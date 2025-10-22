# Examples Directory

This directory contains example scripts and demonstrations for various features of the AC Training Lab codebase.

## Analog Clock Overlay Demo

### Overview

The `analog_clock_demo.py` script demonstrates the analog clock overlay functionality, which is particularly useful for time-lapse videos and live streams.

### Requirements

```bash
pip install opencv-python
```

See [docs/analog_clock_installation.md](../docs/analog_clock_installation.md) for detailed installation instructions.

### Running the Demo

```bash
cd /path/to/ac-dev-lab
python examples/analog_clock_demo.py
```

### What the Demo Does

The script generates three demonstration images:

1. **demo_clock_static.jpg** - Basic clock overlay on a gradient background
2. **demo_clock_styles.jpg** - Various clock styles (classic, monochrome, dark theme) and sizes
3. **demo_clock_positions.jpg** - Clock placement in different corners of a video frame

### Demo Output Examples

The demonstrations show:

- **Different styles**: Classic colorful, monochrome professional, and dark theme
- **Different sizes**: Small (r=50), medium (r=70), and large (r=90) clocks
- **Different positions**: Top-left, top-right, bottom-left, bottom-right corners
- **Custom colors**: Configurable colors for all clock elements

### Use Cases

The analog clock overlay is designed for:

1. **Time-lapse videos**: Especially those sped up 32x or more
2. **Live camera streams**: Real-time overlay on streaming video
3. **Laboratory recordings**: Clear time indication in research videos
4. **Post-processing**: Adding clocks to existing video files

### Key Features

- **Smooth animation**: Continuous hand movement (not just ticks)
- **Highly customizable**: Colors, size, position, transparency
- **Efficient**: Minimal computational overhead
- **Standard format**: Works with OpenCV BGR format
- **Easy integration**: Simple function call to add to any frame

### Integration Examples

#### Basic Usage

```python
import cv2
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

# Load a frame
frame = cv2.imread('frame.jpg')

# Add clock
frame_with_clock = draw_analog_clock(
    frame,
    position=(730, 70),  # top-right corner
    radius=60
)

# Save or display
cv2.imwrite('output.jpg', frame_with_clock)
```

#### Video Processing

```python
import cv2
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

# Open video
cap = cv2.VideoCapture('input.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))

# Process frames
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = draw_analog_clock(frame, position=(width-90, 90), radius=60)
    out.write(frame)

cap.release()
out.release()
```

#### Custom Styling

```python
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

# Define custom colors (BGR format)
custom_colors = {
    'background': (255, 255, 255),  # white
    'border': (0, 0, 0),             # black
    'hour_hand': (0, 0, 128),        # dark blue
    'minute_hand': (0, 0, 255),      # red
    'second_hand': (255, 0, 0),      # blue
    'markers': (64, 64, 64),         # dark gray
}

frame = draw_analog_clock(
    frame,
    position=(100, 100),
    radius=80,
    background_alpha=0.7,
    colors=custom_colors,
    show_digital=True  # Also show digital time
)
```

### Performance Notes

- Adds approximately 5-10ms per frame on typical hardware
- For real-time streaming at 15fps, represents 7-15% CPU overhead
- GPU acceleration available through OpenCV CUDA support
- Consider frame skipping for very high frame rates

### Further Documentation

- [Analog Clock Recommendations](../docs/analog_clock_recommendations.md) - Detailed recommendations for design and usage
- [Installation Guide](../docs/analog_clock_installation.md) - How to install OpenCV and dependencies
- [Module Source](../src/ac_training_lab/video_editing/analog_clock_overlay.py) - The implementation

### Troubleshooting

If the demo fails to run:

1. **Check OpenCV installation**:
   ```bash
   python -c "import cv2; print(cv2.__version__)"
   ```

2. **Install if missing**:
   ```bash
   pip install opencv-python
   ```

3. **On headless systems**, use opencv-python-headless:
   ```bash
   pip uninstall opencv-python
   pip install opencv-python-headless
   ```

4. **Display issues**: If you can't display images, the demo still saves them to files

For more help, see the [installation guide](../docs/analog_clock_installation.md).

## Contributing

To add new examples:

1. Create a well-documented script in this directory
2. Update this README with usage instructions
3. Include example outputs or screenshots
4. Add appropriate .gitignore rules for generated files
5. Update CHANGELOG.md

## License

All examples are part of the AC Training Lab project and are subject to the same license as the main repository.
