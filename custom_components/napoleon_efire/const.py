"""Constants for the Napoleon eFIRE integration."""

from datetime import timedelta

from bleak.exc import BleakError
from bonaparte.exceptions import EfireException

DOMAIN = "napoleon_efire"

# Config Flow constants
CONF_FEATURES = "features"
LOCAL_NAME_PREFIX = "NAP_FPC_"

# List of features supported by the bonaparte library but not by this component
# - The controller's timer feature is not supported and probably should not be implemented
#   This feature can be achieved using automations from within Home Assistant instead
UNSUPPORTED_FEATURES = ["timer"]

# Coordinator constants
UPDATE_INTERVAL = timedelta(seconds=30)
UPDATE_TIMEOUT = 15  # seconds

# Entity keys that were part of the legacy `<ble_name>_<key>` unique ID scheme.
# This list is deliberately frozen: it exists only to recognise IDs written before
# the switch to `<address>_<key>`, so keys added later never belong in it.
LEGACY_UNIQUE_ID_KEYS = (
    "aux",
    "blower",
    "continuous_pilot",
    "flame",
    "led_lights",
    "night_light",
    "split_flow",
)

# Errors that mean the fireplace could not be reached or did not answer properly.
# BleakError covers the Bluetooth stack, EfireException covers bonaparte (a dropped
# connection, a missing characteristic, a rejected command) and the rest are what
# bleak-retry-connector gives up with once its retries run out.
CONNECTION_ERRORS = (
    BleakError,
    ConnectionError,
    EOFError,
    EfireException,
    TimeoutError,
)
