# OpenFlexure Microscope

```{include} ../../docs/_snippets/network-setup-note.md
```

OpenFlexure Microscope is a low-cost, open-source microscope designed for educational and research purposes. It is built using 3D-printed parts, off-the-shelf components, and open-source software. The microscope is designed to be easy to assemble, use, and modify, making it an ideal tool for teaching microscopy and conducting research in various fields. Here, we set it up with remote access via MQTT.

Related issue(s):
- https://github.com/AccelerationConsortium/ac-training-lab/issues/81
- https://github.com/AccelerationConsortium/ac-training-lab/issues/58
- https://github.com/AccelerationConsortium/ac-training-lab/issues/37
- https://github.com/AccelerationConsortium/ac-training-lab/issues/173
- https://github.com/AccelerationConsortium/ac-training-lab/issues/142

## Video Recording Functionality

The OpenFlexure microscope now supports video recording to capture time-lapse footage during experiments like vibration testing. This functionality captures sequential frames from the microscope camera and saves them as animated GIF files.

### Features

- **Continuous Recording**: Start and stop recording manually for flexible duration control
- **Fixed Duration Recording**: Record for a specific time period automatically
- **Configurable Frame Rate**: Adjust FPS (1-10 recommended) based on experiment needs
- **Timestamped Output**: Automatic filename generation with timestamps
- **Error Handling**: Graceful handling of connection issues during recording

### Usage Examples

#### Basic Recording

```python
from microscope_demo_client import MicroscopeDemo

# Connect to microscope
microscope = MicroscopeDemo(
    host="your_mqtt_broker",
    port=8883,
    username="microscope2clientuser", 
    password="your_access_key",
    microscope="microscope2"
)

# Record for 30 seconds at 2 FPS
video_path = microscope.record_video_for_duration(
    duration_seconds=30,
    fps=2,
    output_filename="vibration_test.gif"
)

print(f"Video saved: {video_path}")
microscope.end_connection()
```

#### Manual Control Recording

```python
# Start recording
microscope.start_video_recording(fps=3, output_dir="./experiment_videos")

# Do your experiment (vibration testing, etc.)
# ...

# Stop and save recording
video_path = microscope.stop_video_recording("experiment_results.gif")
```

#### Command Line Recording

Use the standalone video recorder script for quick recordings:

```bash
python video_recorder.py --microscope microscope2 --duration 60 --fps 2 --access-key YOUR_KEY --output vibration_test.gif
```

### Parameters

- **fps**: Frames per second (1-10 recommended, default: 2)
- **duration_seconds**: Recording duration in seconds
- **output_filename**: Custom filename for the video (optional)
- **output_dir**: Directory to save recordings (default: "./recordings")

### File Format

Videos are saved as animated GIF files for universal compatibility and easy viewing. The files are automatically compressed and optimized for reasonable file sizes while maintaining visual quality for analysis.

### GUI Integration

The Streamlit GUI (`gui_control.py`) includes video recording controls:

- **Start Recording**: Begin continuous recording
- **Stop Recording**: End recording and save video
- **Record for Duration**: Automated recording for specified time
- **FPS Control**: Adjustable frame rate settings

### Tips for Vibration Testing

1. **Frame Rate**: Use 2-5 FPS for most vibration tests to capture movement while keeping file size manageable
2. **Duration**: Record 30-120 seconds to capture full vibration cycles
3. **Positioning**: Ensure stable microscope positioning before starting recording
4. **Lighting**: Verify adequate lighting for clear frame capture
5. **Storage**: Check available disk space for longer recordings

### Troubleshooting

- **No frames captured**: Check microscope connection and access credentials
- **Recording fails**: Verify MQTT broker connectivity and permissions
- **Large file sizes**: Reduce FPS or recording duration
- **Blurry images**: Check microscope focus before starting recording
