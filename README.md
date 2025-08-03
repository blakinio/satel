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
