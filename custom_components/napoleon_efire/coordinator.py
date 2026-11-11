"""The Napoleon eFIRE integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from bonaparte import Fireplace, FireplaceState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONNECTION_ERRORS, DOMAIN, UPDATE_INTERVAL, UPDATE_TIMEOUT

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class NapoleonEfireDataUpdateCoordinator(DataUpdateCoordinator[FireplaceState]):
    """Class to manage the polling of the fireplace API."""

    def __init__(
        self,
        hass: HomeAssistant,
        fireplace: Fireplace,
    ) -> None:
        """Initialize the Coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.device = fireplace
        self.data: FireplaceState

    async def async_config_entry_first_refresh(self) -> None:
        """Get mostly static data on first refresh."""
        # Firmware version queries are two separate calls for BLE FW and MCU FW
        # Because it's pretty much static info we update it only upon initial load
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                await self.device.update_firmware_version()
        except CONNECTION_ERRORS as exception:
            msg = f"Could not read the firmware version: {exception}"
            raise ConfigEntryNotReady(msg) from exception
        return await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> FireplaceState:
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT):
                await self.device.update_state()
        except CONNECTION_ERRORS as exception:
            raise UpdateFailed(exception) from exception
        _LOGGER.debug("Old state: %s", self.data)
        _LOGGER.debug("New state: %s", self.device.state)

        return self.device.state
