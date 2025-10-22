# Analog Clock Overlay Recommendations for Time-Lapse Videos

## Overview

This document provides recommendations for using analog clock overlays in place of timestamp overlays for time-lapse videos, particularly those sped up by 32x or more.

## Why Analog Clocks Work Well for Time-Lapse

Analog clocks are superior to digital timestamps for time-lapse videos because:

1. **Visual Continuity**: The smooth movement of clock hands provides a clear visual indication of time passage
2. **Speed Visibility**: At 32x speedup, the second hand completes a full rotation in ~2 seconds, making the acceleration obvious
3. **Intuitive Reading**: Viewers can instantly gauge approximate time without needing to read numbers
4. **Less Eye Strain**: Moving hands are easier to track than rapidly changing digits
5. **Professional Appearance**: Analog clocks have a classic, sophisticated look suitable for scientific videos

## Implementation Options

### Option 1: Python/OpenCV Integration (Recommended)

**Pros:**
- Full control over clock appearance
- Can be integrated directly into existing Python-based video pipelines
- No additional external dependencies beyond OpenCV
- Easy to customize colors, size, and position

**Implementation:**
The provided `analog_clock_overlay.py` module offers a complete solution:

```python
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

# In your video processing loop:
frame_with_clock = draw_analog_clock(
    frame, 
    position=(730, 70),  # top-right corner
    radius=60,
    background_alpha=0.7
)
```

**Integration with existing picam/device.py pipeline:**

The clock can be integrated into the streaming pipeline by processing frames before they're sent to ffmpeg. However, this requires modifying the pipeline to decode, process, and re-encode frames, which adds computational overhead.

### Option 2: FFmpeg Complex Filters

**Pros:**
- No Python processing required
- Lower CPU overhead
- Real-time performance

**Cons:**
- FFmpeg cannot draw analog clocks natively
- Would require pre-generating clock overlay video or images

**Implementation approach:**
1. Generate transparent PNG sequence of clock images (one per second/minute)
2. Use ffmpeg's `overlay` filter to composite the clock onto the video

### Option 3: Pre-rendered Clock Overlay

**Pros:**
- Minimal processing overhead
- Can use any graphics tool to create the clock
- Simple to implement

**Cons:**
- Clock must be synchronized with video timing
- Requires pre-generation of clock frames

## Recommended Clock Design for 32x Time-Lapse

For optimal visibility at 32x speedup:

### Size
- **Radius**: 60-80 pixels for 854x480 video (7-9% of frame height)
- **Position**: Top-right or bottom-right corner with 20-30px margin

### Visual Elements
- **Hour markers**: Bold lines at 12, 3, 6, 9 o'clock positions
- **Minute markers**: Thinner lines or dots at other hour positions
- **Hand widths**: 
  - Hour hand: 6px (thickest)
  - Minute hand: 4px
  - Second hand: 2px (thinnest)
- **Background**: Semi-transparent white/light gray (70-80% opacity)
- **Border**: 2px black circle for definition

### Color Scheme
Two recommended color schemes:

**Classic (High Contrast):**
- Background: Light gray (#F5F5F5)
- Hour hand: Dark blue (#000080)
- Minute hand: Red (#FF0000)
- Second hand: Bright blue (#0000FF)
- Markers: Dark gray (#404040)

**Professional (Monochrome):**
- Background: White (#FFFFFF)
- All hands: Black (#000000) with varying thickness
- Markers: Medium gray (#808080)

## Example Use Cases

### 1. Live Camera Streaming

Integrate the clock overlay into the camera streaming pipeline:

```python
# In picam/device.py, modify the pipeline to include frame processing
# This would require capturing frames, adding overlay, and re-encoding
```

### 2. Post-Processing Time-Lapse

Apply the clock to downloaded videos:

```python
import cv2
from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock

cap = cv2.VideoCapture('input_timelapse.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output_with_clock.mp4', fourcc, 30.0, (854, 480))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = draw_analog_clock(frame, position=(730, 70), radius=60)
    out.write(frame)

cap.release()
out.release()
```

### 3. Testing the Clock

To test the analog clock overlay:

```bash
cd /home/runner/work/ac-dev-lab/ac-dev-lab
python src/ac_training_lab/video_editing/analog_clock_overlay.py
```

This will display a test frame with analog clocks in different positions.

## Performance Considerations

### CPU Impact
- Drawing the clock on each frame adds ~5-10ms per frame on typical hardware
- For 15fps video, this represents 7-15% CPU overhead
- Consider implementing frame skipping (update clock every N frames) if needed

### GPU Acceleration
- OpenCV can use GPU acceleration for drawing operations
- Enable with `cv2.cuda` if available
- Significant speedup possible on systems with NVIDIA GPUs

### Memory Usage
- Minimal additional memory required (~1-2 MB for overlay buffer)
- No significant impact on streaming pipelines

## Alternative Tools and Libraries

If the provided solution doesn't meet your needs, consider:

### 1. MoviePy
```python
from moviepy.editor import VideoFileClip
from moviepy.video.fx import speedx
# Add custom drawing function
```

### 2. Manim (Mathematical Animation Engine)
- Excellent for precise, animated graphics
- Overkill for simple clock overlay
- Good for creating professional video overlays

### 3. Processing/p5.js
- Create animated clock as separate video layer
- Composite with main video using ffmpeg

### 4. After Effects / Premiere Pro
- Manual approach for one-off videos
- Time-consuming but maximum control

## Recommendations Summary

**For immediate use:**
1. Use the provided `analog_clock_overlay.py` module
2. Place clock in top-right corner with 60px radius
3. Use high-contrast color scheme for visibility
4. Test with actual 32x time-lapse footage to verify readability

**For production deployment:**
1. Profile CPU usage with actual streaming setup
2. Consider GPU acceleration if available
3. Implement caching/optimization if frame rate drops
4. Test with various lighting conditions and video content

**Next steps:**
1. Integrate with existing video pipeline
2. Add configuration options to device settings
3. Create example videos showing clock at various speedup rates
4. Document integration process for other devices

## References

- [OpenCV Drawing Functions](https://docs.opencv.org/4.x/dc/da5/tutorial_py_drawing_functions.html)
- [FFmpeg Overlay Filter](https://ffmpeg.org/ffmpeg-filters.html#overlay-1)
- [Time-Lapse Best Practices](https://www.cincopa.com/learn/creating-time-lapse-videos-with-ffmpeg)
- Example implementations on GitHub:
  - [inkymello/Analog-clock-using-OpenCV](https://github.com/inkymello/Analog-clock-using-OpenCV)
  - [hasnimughal/clock_using_opencv_python](https://github.com/hasnimughal/clock_using_opencv_python)
