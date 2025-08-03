 codex/add-unit-tests-for-satelhub-integration
# Satel Alarm Home Assistant Integration

This custom component provides a simple integration with Satel alarm systems.

## Configuration

### UI setup

1. In Home Assistant navigate to **Settings → Devices & Services**.
2. Click **Add Integration** and search for **Satel**.
3. Enter the host and port of your Satel interface and finish the flow.

### YAML configuration

The integration can also be configured in `configuration.yaml`:

```yaml
satel:
  host: 192.168.1.2
  port: 7094
```

After adding the configuration, restart Home Assistant.
=======
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
 main
