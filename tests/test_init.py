"""Tests for setting up and unloading Napoleon eFIRE."""

from __future__ import annotations

from unittest.mock import AsyncMock

from bleak.exc import BleakError
from bonaparte import Fireplace
from bonaparte.exceptions import DisconnectedException
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.bluetooth import inject_bluetooth_service_info

from custom_components.napoleon_efire.const import DOMAIN

from .conftest import ADDRESS, NAME


async def _setup(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    service_info: BluetoothServiceInfoBleak | None,
) -> None:
    if service_info is not None:
        inject_bluetooth_service_info(hass, service_info)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_and_unload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fireplace: Fireplace,
    service_info: BluetoothServiceInfoBleak,
    entity_registry: er.EntityRegistry,
) -> None:
    """Set up the configured features, then disconnect on unload."""
    await _setup(hass, mock_config_entry, service_info)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data.device is mock_fireplace

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert sorted(entry.unique_id for entry in entities) == [
        f"{ADDRESS}_blower",
        f"{ADDRESS}_continuous_pilot",
        f"{ADDRESS}_flame",
        f"{ADDRESS}_night_light",
    ]

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    mock_fireplace.disconnect.assert_awaited()


@pytest.mark.usefixtures("mock_fireplace")
async def test_setup_retry_when_not_in_range(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Retry later when no adapter or proxy can see the fireplace."""
    await _setup(hass, mock_config_entry, None)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize(
    "error", [BleakError("gone"), TimeoutError, DisconnectedException("gone")]
)
async def test_setup_retry_when_authenticate_fails(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fireplace: Fireplace,
    service_info: BluetoothServiceInfoBleak,
    error: Exception,
) -> None:
    """Retry later, and let go of the connection, when the controller drops out."""
    mock_fireplace.authenticate = AsyncMock(side_effect=error)
    await _setup(hass, mock_config_entry, service_info)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    mock_fireplace.disconnect.assert_awaited()


async def test_setup_rejected_password(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fireplace: Fireplace,
    service_info: BluetoothServiceInfoBleak,
) -> None:
    """A rejected password fails setup instead of retrying forever."""
    mock_fireplace.authenticate = AsyncMock(return_value=False)
    await _setup(hass, mock_config_entry, service_info)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    mock_fireplace.disconnect.assert_awaited()


@pytest.mark.parametrize("method", ["update_firmware_version", "update_state"])
async def test_setup_retry_when_first_read_fails(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_fireplace: Fireplace,
    service_info: BluetoothServiceInfoBleak,
    method: str,
) -> None:
    """Retry later when the first read of the fireplace fails."""
    setattr(mock_fireplace, method, AsyncMock(side_effect=BleakError("gone")))
    await _setup(hass, mock_config_entry, service_info)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    mock_fireplace.disconnect.assert_awaited()


@pytest.mark.usefixtures("mock_fireplace")
async def test_legacy_unique_ids_migrated(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    service_info: BluetoothServiceInfoBleak,
    entity_registry: er.EntityRegistry,
) -> None:
    """Re-key unique IDs based on the advertised name onto the address."""
    mock_config_entry.add_to_hass(hass)
    old_blower = entity_registry.async_get_or_create(
        Platform.FAN, DOMAIN, f"{NAME}_blower", config_entry=mock_config_entry
    )

    await _setup(hass, mock_config_entry, service_info)

    blower = entity_registry.async_get(old_blower.entity_id)
    assert blower is not None
    assert blower.unique_id == f"{ADDRESS}_blower"
