# OT-2 Opentrons Robot

```{include} ../../docs/_snippets/network-setup-note.md
```

This directory contains scripts and configuration files for the Opentrons OT-2 lab automation robot. The OT-2 is a versatile robot that can automate liquid handling tasks in laboratory settings. The scripts enable remote control and monitoring of pipetting operations through MQTT communication, allowing integration with automated laboratory workflows.

## Features

- **MQTT Communication**: Remote control and status updates via MQTT
- **Color Mixing Demo**: Automated mixing of red, yellow, and blue paints
- **Prefect Workflows**: Orchestrated operations using Prefect flows
- **Inventory Management**: Track paint stock levels with evaporation accounting (see [Inventory System](./_scripts/INVENTORY_README.md))

## Inventory Management

The inventory management system helps prevent experiments from running with insufficient paint stock:

- Automatic tracking of red, yellow, and blue paint volumes
- Evaporation compensation over time
- Pre-mixing stock validation
- Manual restock operations via Prefect flows
- Low-stock alerts and monitoring

For detailed documentation, see [_scripts/INVENTORY_README.md](./_scripts/INVENTORY_README.md).

## Related Resources

- Related issue(s):
  - https://github.com/AccelerationConsortium/ac-training-lab/issues/26
  - https://github.com/AccelerationConsortium/ac-training-lab/issues/152
- Wireless Color Sensor: https://accelerationconsortium.github.io/wireless-color-sensor/
