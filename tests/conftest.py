"""Shared fixtures for the Napoleon eFIRE tests."""

from __future__ import annotations

from collections.abc import Generator
import time
from unittest.mock import AsyncMock, PropertyMock, patch

from bonaparte import Fireplace
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS, CONF_PASSWORD
import pytest
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.bluetooth import (
    generate_advertisement_data,
    generate_ble_device,
)

from custom_components.napoleon_efire.const import CONF_FEATURES, DOMAIN

ADDRESS = "AA:BB:CC:DD:EE:FF"
NAME = "NAP_FPC_1E13"
PASSWORD = "1234"


def make_service_info(address: str, name: str) -> BluetoothServiceInfoBleak:
    """Build a connectable advertisement as the Bluetooth integration reports it."""
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
        device=generate_ble_device(address, name),
        advertisement=generate_advertisement_data(local_name=name),
        connectable=True,
        time=time.monotonic(),
        tx_power=-127,
    )


@pytest.fixture(autouse=True, scope="session")
def mock_bluez_history() -> Generator[None]:
    """Report no BlueZ advertisement history.

    The shared fixtures pretend to be Linux, but dbus-fast leaves its unpacker unset
    on other systems, so reading BlueZ history crashes when the tests run on macOS.
    """
    with patch(
        "bluetooth_adapters.systems.linux.LinuxAdapters.history",
        new_callable=PropertyMock,
        return_value={},
    ):
        yield


@pytest.fixture(autouse=True)
def auto_enable_bluetooth(enable_bluetooth: None) -> None:
    """Run every test with the Bluetooth integration mocked and loaded."""


@pytest.fixture
def service_info() -> BluetoothServiceInfoBleak:
    """Return the fireplace's advertisement."""
    return make_service_info(ADDRESS, NAME)


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry for one fireplace with a blower and night light."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        unique_id=ADDRESS,
        data={
            CONF_ADDRESS: ADDRESS,
            CONF_PASSWORD: PASSWORD,
            CONF_FEATURES: ["blower", "night_light"],
        },
    )


@pytest.fixture
def mock_fireplace() -> Generator[Fireplace]:
    """Return a real Fireplace object whose Bluetooth I/O is mocked out.

    Using the real class keeps the state and feature handling genuine, so only the
    calls that would talk to the controller are replaced.
    """
    fireplace = Fireplace(generate_ble_device(ADDRESS, NAME), compatibility_mode=False)
    fireplace.authenticate = AsyncMock(return_value=True)
    fireplace.update_state = AsyncMock()
    fireplace.update_firmware_version = AsyncMock()
    fireplace.disconnect = AsyncMock()

    with (
        patch(
            "custom_components.napoleon_efire.Fireplace",
            return_value=fireplace,
        ),
        patch(
            "custom_components.napoleon_efire.config_flow.Fireplace",
            return_value=fireplace,
        ),
    ):
        yield fireplace
