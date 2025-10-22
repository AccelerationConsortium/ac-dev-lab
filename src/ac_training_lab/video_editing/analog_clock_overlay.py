"""
Analog Clock Overlay for Video Streams

This module provides functionality to create an analog clock overlay suitable
for time-lapse videos. The clock is designed to be clearly visible even when
videos are sped up significantly (e.g., 32x speedup).

The implementation uses OpenCV to draw a classic analog clock with:
- Hour, minute, and second hands
- Hour markers (thick lines at 12, 3, 6, 9 positions)
- Semi-transparent background for better visibility
- Configurable size, position, and styling

Usage:
    from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock
    
    # In a video processing loop:
    frame_with_clock = draw_analog_clock(frame, position=(50, 50), radius=80)

For integration with ffmpeg streaming pipelines, this can be used as a
frame processor before encoding.
"""

import cv2
import numpy as np
from datetime import datetime
import math


def draw_analog_clock(
    frame,
    position=(50, 50),
    radius=80,
    background_alpha=0.7,
    colors=None,
    show_digital=False,
):
    """
    Draw an analog clock overlay on a video frame.
    
    Args:
        frame: numpy array representing the video frame (BGR format)
        position: tuple (x, y) for the center of the clock
        radius: int, radius of the clock in pixels
        background_alpha: float (0-1), transparency of the clock background
        colors: dict with color specifications (optional), e.g.:
                {
                    'background': (255, 255, 255),  # white
                    'border': (0, 0, 0),             # black
                    'hour_hand': (0, 0, 128),        # dark blue
                    'minute_hand': (0, 0, 255),      # red
                    'second_hand': (255, 0, 0),      # blue
                    'markers': (64, 64, 64),         # dark gray
                }
        show_digital: bool, whether to show digital time below the clock
    
    Returns:
        frame with analog clock overlay
    """
    # Default colors (BGR format for OpenCV)
    if colors is None:
        colors = {
            'background': (245, 245, 245),  # light gray
            'border': (0, 0, 0),             # black
            'hour_hand': (0, 0, 128),        # dark blue
            'minute_hand': (0, 0, 255),      # red
            'second_hand': (255, 0, 0),      # blue
            'markers': (64, 64, 64),         # dark gray
            'digital_text': (0, 0, 0),       # black
        }
    
    # Create a copy of the frame to work with
    overlay = frame.copy()
    
    # Get current time
    now = datetime.now()
    hour = now.hour % 12
    minute = now.minute
    second = now.second
    
    center = position
    
    # Draw clock background (semi-transparent circle)
    cv2.circle(overlay, center, radius, colors['background'], -1)
    
    # Apply transparency
    frame = cv2.addWeighted(overlay, background_alpha, frame, 1 - background_alpha, 0)
    
    # Draw clock border
    cv2.circle(frame, center, radius, colors['border'], 2)
    
    # Draw hour markers (thicker lines at 12, 3, 6, 9)
    for i in range(12):
        angle = math.radians(i * 30 - 90)  # -90 to start from top
        
        if i % 3 == 0:
            # Major markers (thicker)
            start_ratio = 0.75
            thickness = 3
        else:
            # Minor markers
            start_ratio = 0.85
            thickness = 2
        
        start_x = int(center[0] + radius * start_ratio * math.cos(angle))
        start_y = int(center[1] + radius * start_ratio * math.sin(angle))
        end_x = int(center[0] + radius * 0.95 * math.cos(angle))
        end_y = int(center[1] + radius * 0.95 * math.sin(angle))
        
        cv2.line(frame, (start_x, start_y), (end_x, end_y), colors['markers'], thickness)
    
    # Calculate angles for hands (-90 degrees to start from top)
    second_angle = math.radians(second * 6 - 90)
    minute_angle = math.radians(minute * 6 + second * 0.1 - 90)
    hour_angle = math.radians(hour * 30 + minute * 0.5 - 90)
    
    # Draw hour hand (shortest, thickest)
    hour_length = radius * 0.5
    hour_x = int(center[0] + hour_length * math.cos(hour_angle))
    hour_y = int(center[1] + hour_length * math.sin(hour_angle))
    cv2.line(frame, center, (hour_x, hour_y), colors['hour_hand'], 6)
    
    # Draw minute hand (medium length)
    minute_length = radius * 0.7
    minute_x = int(center[0] + minute_length * math.cos(minute_angle))
    minute_y = int(center[1] + minute_length * math.sin(minute_angle))
    cv2.line(frame, center, (minute_x, minute_y), colors['minute_hand'], 4)
    
    # Draw second hand (longest, thinnest)
    second_length = radius * 0.85
    second_x = int(center[0] + second_length * math.cos(second_angle))
    second_y = int(center[1] + second_length * math.sin(second_angle))
    cv2.line(frame, center, (second_x, second_y), colors['second_hand'], 2)
    
    # Draw center dot
    cv2.circle(frame, center, 5, colors['border'], -1)
    
    # Optionally show digital time
    if show_digital:
        time_str = now.strftime("%H:%M:%S")
        text_size = cv2.getTextSize(time_str, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = center[0] - text_size[0] // 2
        text_y = center[1] + radius + 20
        cv2.putText(
            frame,
            time_str,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            colors['digital_text'],
            1,
            cv2.LINE_AA
        )
    
    return frame


def create_clock_overlay_for_stream(
    frame_width=854,
    frame_height=480,
    clock_position="top-right",
    clock_radius=60,
    **kwargs
):
    """
    Helper function to calculate clock position for video streams.
    
    Args:
        frame_width: width of the video frame
        frame_height: height of the video frame
        clock_position: string, one of: "top-left", "top-right", "bottom-left", "bottom-right"
        clock_radius: radius of the clock
        **kwargs: additional arguments to pass to draw_analog_clock
    
    Returns:
        A function that takes a frame and returns it with the clock overlay
    """
    # Calculate position based on frame size and desired location
    margin = clock_radius + 20
    
    positions = {
        "top-left": (margin, margin),
        "top-right": (frame_width - margin, margin),
        "bottom-left": (margin, frame_height - margin),
        "bottom-right": (frame_width - margin, frame_height - margin),
    }
    
    if clock_position not in positions:
        raise ValueError(f"clock_position must be one of {list(positions.keys())}")
    
    position = positions[clock_position]
    
    def overlay_func(frame):
        return draw_analog_clock(frame, position=position, radius=clock_radius, **kwargs)
    
    return overlay_func


# Example usage and testing
if __name__ == "__main__":
    # Create a test frame
    test_frame = np.zeros((480, 854, 3), dtype=np.uint8)
    test_frame[:] = (200, 200, 200)  # Light gray background
    
    # Add text to show this is a test
    cv2.putText(
        test_frame,
        "Test Frame - Analog Clock Overlay",
        (50, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 0),
        2
    )
    
    # Draw clock in different positions
    positions = [
        ("top-right", (730, 70)),
        ("bottom-right", (730, 410)),
    ]
    
    for name, pos in positions:
        test_frame = draw_analog_clock(test_frame, position=pos, radius=60)
    
    # Display the test frame
    cv2.imshow("Analog Clock Overlay Test", test_frame)
    print("Press any key to close the window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
