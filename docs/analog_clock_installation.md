# Analog Clock Overlay - Installation and Setup

## Prerequisites

To use the analog clock overlay functionality, you need to have OpenCV installed in your Python environment.

## Installation

### Option 1: Install OpenCV with pip

```bash
pip install opencv-python
```

For systems that need GUI support (displaying windows):
```bash
pip install opencv-python-headless  # For servers/headless systems
# OR
pip install opencv-python  # For systems with display
```

### Option 2: Install using conda

```bash
conda install -c conda-forge opencv
```

### Option 3: Add to project dependencies

Add to `setup.cfg` in the appropriate section:

```ini
[options.extras_require]
video_overlay =
    opencv-python>=4.5.0
```

Then install with:
```bash
pip install -e .[video_overlay]
```

## Verification

To verify the installation:

```bash
python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
```

## Usage

Once OpenCV is installed, you can use the analog clock overlay:

```python
import cv2
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

# Create a test frame
frame = cv2.imread('test_image.jpg')

# Add analog clock overlay
frame_with_clock = draw_analog_clock(
    frame,
    position=(100, 100),  # x, y coordinates
    radius=80,
    background_alpha=0.7
)

# Display or save
cv2.imshow('Frame with Clock', frame_with_clock)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

## Integration with Video Streams

### For Live Streaming (picam)

To integrate with the existing picam streaming setup, you would need to:

1. Modify the streaming pipeline to process frames
2. Add the clock overlay to each frame
3. Re-encode and send to ffmpeg

**Note:** This adds processing overhead and may require GPU acceleration for real-time streaming.

### For Post-Processing

To add the clock to existing video files:

```python
import cv2
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

# Open video file
cap = cv2.VideoCapture('input.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))

# Process frames
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Add clock overlay
    frame = draw_analog_clock(frame, position=(width - 90, 90), radius=60)
    
    # Write frame
    out.write(frame)

# Cleanup
cap.release()
out.release()
```

## Troubleshooting

### ImportError: No module named 'cv2'

Install OpenCV as described above.

### Clock not visible

- Check that the position is within frame boundaries
- Adjust `background_alpha` parameter (0.5-0.9 recommended)
- Verify frame is in BGR format (OpenCV's default)

### Performance issues

- Use `opencv-python-headless` for server deployments
- Enable GPU acceleration if available
- Consider processing every Nth frame instead of all frames
- Use hardware encoding/decoding if available

### Display issues on headless systems

If you're running on a system without a display and get errors with `cv2.imshow()`:

```python
# Save to file instead of displaying
cv2.imwrite('output.jpg', frame_with_clock)
```

Or install the headless version:
```bash
pip uninstall opencv-python
pip install opencv-python-headless
```

## Next Steps

1. Install OpenCV using one of the methods above
2. Test the analog clock module with the test script
3. Review `analog_clock_recommendations.md` for usage guidelines
4. Integrate into your video processing pipeline

## Support

For issues or questions:
- Check the [OpenCV documentation](https://docs.opencv.org/)
- Review the module source code: `src/ac_training_lab/video_editing/analog_clock_overlay.py`
- Consult the recommendations document: `docs/analog_clock_recommendations.md`
