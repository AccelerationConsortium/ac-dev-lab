# Brother QL-810W Label Printer Automation with AprilTags

This module provides automation for the Brother QL-810W label printer to print AprilTags for equipment identification in the lab.

## Hardware

- **Printer**: Brother QL-810W (wireless label printer)
- **Labels**: DK-2251 (black/red on white) or DK-4205 (removable, black on white)

## Setup

### 1. Install brother_ql

```bash
pip install brother_ql Pillow
```

### 2. Find printer

For USB connection:
```bash
brother_ql discover
```

For network connection, use the printer's IP address:
```
tcp://192.168.1.XXX:9100
```

### 3. Disable Editor Lite mode

If your printer has "Editor Lite" mode enabled, disable it by holding the button until the LED turns off. This is required for USB printing.

### 4. Test print

```bash
export BROTHER_QL_PRINTER=tcp://192.168.1.XXX:9100
export BROTHER_QL_MODEL=QL-810W
brother_ql print -l 62 test_image.png
```

## Files

- `mwe_print.py` - Minimal working example for sending a print command
- `app.py` - Gradio web app for AprilTag printing with MQTT integration

## Usage

### MWE (Minimum Working Example)

Configure environment variables and run:
```bash
export BROTHER_QL_PRINTER=tcp://192.168.1.XXX:9100
export BROTHER_QL_MODEL=QL-810W
export BROTHER_QL_LABEL=62
python mwe_print.py
```

### Gradio App

Configure MQTT credentials and run:
```bash
export HIVEMQ_HOST=your-broker.hivemq.cloud
export HIVEMQ_USERNAME=your-username
export HIVEMQ_PASSWORD=your-password
python app.py
```

The Gradio app provides:
- AprilTag generation with configurable tag family and ID
- Print preview before sending to printer
- MQTT integration for remote printing via HiveMQ

## Troubleshooting

### Raspberry Pi Setup

The brother_ql library communicates directly with the printer, bypassing CUPS drivers. This is especially useful on Raspberry Pi where Brother's official i386 drivers are incompatible with ARM architecture.

For USB on Linux, ensure proper permissions:
```bash
sudo usermod -a -G lp $USER
```

Or set up udev rules for the printer.

### Backend Options

- `pyusb` - Cross-platform USB (requires libusb)
- `network` - TCP/IP for WiFi-enabled printers
- `linux_kernel` - Uses /dev/usb/lp0 on Linux

## Related Issues

- [ac-dev-lab #70](https://github.com/AccelerationConsortium/ac-dev-lab/issues/70) - Set up QL810WC label printer automation with AprilTags
- [echem-cell #4](https://github.com/AccelerationConsortium/echem-cell/issues/4) - Electrocatalyst experiment equipment
- [brother_ql #162](https://github.com/pklaus/brother_ql/issues/162) - Brother QL-810W Printer Not Printing on Raspberry Pi

## References

- [brother_ql documentation](https://github.com/pklaus/brother_ql)
- [Brother QL-810W manual](https://support.brother.com/g/b/manualtop.aspx?c=ca&lang=en&prod=lpql810weus)
