# Satel Alarm Integration

Integration with Satel alarm systems for Home Assistant.

## Installation

1. Copy the `custom_components/satel` directory to your Home Assistant `config/custom_components` folder.
2. Alternatively, use [HACS](https://hacs.xyz) and add this repository as a custom repository.
3. Restart Home Assistant to load the integration.

## Configuration

Configuration is handled through the Home Assistant UI:

1. Navigate to **Settings → Devices & Services**.
2. Click **Add Integration** and search for **Satel Alarm**.
3. Enter your Satel controller details and complete the setup wizard.

## Supported Features

- Binary sensors for zones and partitions
- Sensor entities for device status and diagnostics
- Switch entities for arming and disarming
- Configuration flow for guided setup

## Troubleshooting

- Ensure the Satel controller is reachable on the network.
- Check the Home Assistant logs for detailed error messages.
- Remove and re-add the integration if entities are missing.
