# Napoleon eFIRE Integration

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

Control a Napoleon fireplace with the eFIRE Bluetooth controller from Home Assistant. Works best with an [ESPHome Bluetooth proxy](https://esphome.github.io/bluetooth-proxies/) near the fireplace.

This is a personal fork of [kaechele/napoleon-efire](https://github.com/kaechele/napoleon-efire) by Felix Kaechele, which did all the protocol work through the [bonaparte](https://github.com/kaechele/bonaparte) library. The fork models the flame as a heater instead of a light, adds an options flow for the feature set, and meets the Bronze tier of the Home Assistant integration quality scale. Versions are date-based (for example `2026.11.0`) so they never collide with upstream's releases.

## Platforms

<!-- prettier-ignore -->
| Platform | Description |
| --- | --- |
| `climate` | The flame: on or off, and the flame height as presets 1 to 6. |
| `fan` | The optional 6-speed blower. |
| `light` | The optional night light and the optional LED light kit. |
| `switch` | Continuous pilot, plus the optional AUX relay and split flow valve. |

## Features and controls

1. **Flame** (climate entity)

   Heat turns the burner on and Off turns it off. The presets 1 to 6 set the flame height. Turning the flame on without picking a height starts it at height 1, the lowest.

   The flame is a climate entity rather than a light on purpose. A light answers area-wide commands like "turn on the living room lights", from a voice assistant or a script, and for this device that would ignite gas. Climate entities aren't part of those commands.

   Home Assistant shows a temperature range on the entity because every climate entity needs a unit. The fireplace has no thermostat, so nothing uses it.

1. **Blower** (fan entity, _optional_)

   The fan that spreads the hot air from the fireplace into the room. It has 6 speeds.

1. **Night light** (light entity, _optional_)

   A lamp at the top of the firebox, if your fireplace has one. It has 6 dimming levels.

1. **LED lights** (light entity, _optional_)

   The LED light kit, if one is fitted. You can set its color and brightness, and pick one of these effects: Hold (a steady color), Cycle and Ember Bed.

1. **Continuous pilot** (switch entity)

   When on, the pilot light burns all the time (continuous pilot, CPI). By default the pilot works in intermittent mode (IPI) and is lit just before the main burner.

   Leave it in IPI mode unless you need what CPI gives you: quicker ignition in extreme cold, less condensation on the glass, and working during a power outage once the backup batteries are flat. The cost is burning a small amount of gas all the time, which also affects air quality.

1. **Split flow** (switch entity, _optional_)

   Controls an optional valve that sends gas to a second burner, for example on fireplaces with a front and a back burner. Turning it on lights both.

1. **AUX** (switch entity, _optional_)

   A high voltage relay on the IFC (Integrated Fireplace Controller), fed from its line voltage, that can switch small electric loads. See the IFC manual for details.

The controller's timer isn't supported on purpose. An automation in Home Assistant does the same job.

## Limitations

Many of these come from the Napoleon Bluetooth controller or the ProFlame 2 IFC, which this integration can't change.

1. **The RF remote overrides Bluetooth control (IFC limitation).**

   Once the RF remote is used, the controller can no longer send commands to the IFC or read its state. That also means you can't turn off a fireplace that was turned on with the remote. The eFIRE app has a lock screen that is supposed to show while the remote is in control, but on the original author's controller the command behind it never answers, so it isn't implemented here either.

   **Ideally, Home Assistant is the only thing controlling the fireplace.**

1. **The Bluetooth controller is off when the switch on the RF receiver / battery backup inside the fireplace is set to Off (IFC limitation).**

   To disable the RF remote, take its batteries out instead.

1. **Setting a flame height or blower speed while the fireplace is off first turns it on at the highest setting, then lowers it (Bluetooth controller limitation).**

1. **The eFIRE app can't connect while Home Assistant is connected.**

   The integration keeps a permanent connection to the controller, and while something is connected the controller isn't discoverable by the app. Connecting only when polling (every 30 seconds) would work around that, but Home Assistant and the app would still conflict with each other.

1. **Changes are found by polling, every 30 seconds.**

   The controller doesn't send its state in Bluetooth advertisements, so Home Assistant has to ask for it. A change made outside Home Assistant can take up to 30 seconds to show.

1. **Features are not detected.**

   The controller can't tell which accessories are fitted, so you pick them during setup. A feature you tick that isn't there gives you an entity that accepts commands and does nothing. You can change the selection later, see [Configuration](#configuration).

## Installation

### Through the Marketplace (or HACS)

1. In Home Assistant, go to **Settings** > **Marketplace** and select **Add from link**. On Home Assistant 2026.10 or older, add it as a custom repository in HACS instead.
1. Enter `vemboy200/napoleon-efire` and add it.
1. Install **Napoleon eFIRE** and restart Home Assistant.

Requires Home Assistant 2026.11 or newer.

If you're switching from upstream, the Marketplace makes you remove the existing setup before uninstalling the old version, so you set the fireplace up again afterwards. Your entity IDs come back the same, but their history and area are lost.

### Manual installation

1. Open the folder that holds your Home Assistant configuration (where `configuration.yaml` is).
1. If there's no `custom_components` folder there, create it.
1. Inside it, create a folder called `napoleon_efire`.
1. Copy _all_ the files from `custom_components/napoleon_efire/` in this repository into that folder.
1. Restart Home Assistant.

## Configuration

Your fireplace should show up under **Settings** > **Devices & services** as discovered. Otherwise, select **Add integration** and search for **Napoleon eFIRE**.

1. **Device:** pick your fireplace. The controller advertises a name that starts with `NAP_FPC_`.
1. **Password:** the password set in the eFIRE app. Unless someone changed it, it's `0000`.
1. **Features:** tick the accessories your fireplace has: blower, LED lights, night light, AUX relay and split flow.

To change the features later, go to the integration's entry and select **Configure**. The integration reloads and adds or removes the matching entities.

## Removing the integration

This integration follows standard integration removal. No extra steps are required.

1. Go to **Settings** > **Devices & services** and select **Napoleon eFIRE**.
1. Next to the fireplace's entry, select the three-dot menu and then **Delete**.
1. If you won't set it up again, uninstall **Napoleon eFIRE** in the Marketplace (or HACS) and restart Home Assistant.

Removing the entry closes the Bluetooth connection, so the eFIRE app can find the fireplace again. It doesn't change anything on the fireplace itself: the password and the features you set up stay as they were.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[license-shield]: https://img.shields.io/github/license/vemboy200/napoleon-efire.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/vemboy200/napoleon-efire.svg?style=for-the-badge
[releases]: https://github.com/vemboy200/napoleon-efire/releases
