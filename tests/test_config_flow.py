"""Tests for the Napoleon eFIRE config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from bleak.exc import BleakError
from bonaparte import Fireplace
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.bluetooth import inject_bluetooth_service_info

from custom_components.napoleon_efire.const import CONF_FEATURES, DOMAIN

from .conftest import ADDRESS, NAME, PASSWORD, make_service_info

ALL_FEATURES_OFF = {
    "aux": False,
    "blower": False,
    "led_lights": False,
    "night_light": False,
    "split_flow": False,
}


async def _inject(hass: HomeAssistant, *infos: BluetoothServiceInfoBleak) -> None:
    for info in infos:
        inject_bluetooth_service_info(hass, info)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("mock_fireplace")
async def test_user_flow(
    hass: HomeAssistant, service_info: BluetoothServiceInfoBleak
) -> None:
    """Pick a fireplace, enter the password, tick features, and get an entry."""
    await _inject(hass, service_info, make_service_info("11:22:33:44:55:66", "Speaker"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    # Only devices advertising as a fireplace controller are offered.
    choices = result["data_schema"].schema[CONF_ADDRESS].container
    assert list(choices) == [ADDRESS]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, CONF_PASSWORD: PASSWORD}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_features"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ALL_FEATURES_OFF, "blower": True, "night_light": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {
        CONF_ADDRESS: ADDRESS,
        CONF_PASSWORD: PASSWORD,
        CONF_FEATURES: ["blower", "night_light"],
    }
    assert result["result"].unique_id == ADDRESS


@pytest.mark.parametrize(
    ("side_effect", "return_value", "error"),
    [
        (None, False, {CONF_PASSWORD: "invalid_auth"}),
        (BleakError("out of range"), True, {"base": "cannot_connect"}),
        (TimeoutError, True, {"base": "cannot_connect"}),
        (RuntimeError("boom"), True, {"base": "unknown"}),
    ],
)
async def test_user_flow_errors(  # noqa: PLR0917
    hass: HomeAssistant,
    mock_fireplace: Fireplace,
    service_info: BluetoothServiceInfoBleak,
    side_effect: Exception | None,
    return_value: bool,
    error: dict[str, str],
) -> None:
    """Show the error, close the connection, and recover once it works."""
    await _inject(hass, service_info)
    mock_fireplace.authenticate = AsyncMock(
        side_effect=side_effect, return_value=return_value
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, CONF_PASSWORD: "bad"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == error
    mock_fireplace.disconnect.assert_awaited()

    mock_fireplace.authenticate = AsyncMock(return_value=True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, CONF_PASSWORD: PASSWORD}
    )
    assert result["step_id"] == "select_features"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ALL_FEATURES_OFF
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_PASSWORD] == PASSWORD


async def test_user_flow_no_devices(hass: HomeAssistant) -> None:
    """Abort when nothing that looks like a fireplace is in range."""
    await _inject(hass, make_service_info("11:22:33:44:55:66", "Speaker"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_unconfigured_devices"


async def test_user_flow_skips_configured_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """A fireplace that is already set up is not offered again."""
    mock_config_entry.add_to_hass(hass)
    await _inject(hass, service_info)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_unconfigured_devices"


@pytest.mark.usefixtures("mock_fireplace")
async def test_user_flow_configured_meanwhile(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Abort if the fireplace was set up by another flow while this one was open."""
    await _inject(hass, service_info)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, CONF_PASSWORD: PASSWORD}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.usefixtures("mock_fireplace")
async def test_bluetooth_discovery(
    hass: HomeAssistant, service_info: BluetoothServiceInfoBleak
) -> None:
    """A discovered fireplace goes straight to the password form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert list(result["data_schema"].schema[CONF_ADDRESS].container) == [ADDRESS]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, CONF_PASSWORD: PASSWORD}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ALL_FEATURES_OFF, "led_lights": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_FEATURES] == ["led_lights"]


async def test_bluetooth_discovery_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """Abort discovery of a fireplace that is already set up."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
