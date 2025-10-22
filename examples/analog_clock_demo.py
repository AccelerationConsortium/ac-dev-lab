"""
Analog Clock Overlay Demo

This script demonstrates how to use the analog clock overlay module
for various video processing scenarios.

Requirements:
- opencv-python (pip install opencv-python)

Usage:
    python examples/analog_clock_demo.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_static_image():
    """Demo 1: Add clock to a static image"""
    import cv2
    import numpy as np
    from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock
    
    print("Demo 1: Creating static image with clock overlay...")
    
    # Create a test image (gradient background)
    img = np.zeros((480, 854, 3), dtype=np.uint8)
    for i in range(480):
        img[i, :] = [50 + i//3, 100 + i//4, 150 + i//5]
    
    # Add title
    cv2.putText(
        img, 
        "Analog Clock Overlay Demo",
        (250, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )
    
    # Add clock in top-right corner
    img = draw_analog_clock(img, position=(770, 70), radius=60)
    
    # Save result
    cv2.imwrite("demo_clock_static.jpg", img)
    print("  ✓ Saved to demo_clock_static.jpg")
    
    return img


def demo_video_processing():
    """Demo 2: Process a video file with clock overlay"""
    import cv2
    from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock
    
    print("\nDemo 2: Video processing (simulated)...")
    print("  Note: This would process an actual video file")
    print("  Example code:")
    print("""
    cap = cv2.VideoCapture('input.mp4')
    out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = draw_analog_clock(frame, position=(730, 70), radius=60)
        out.write(frame)
    
    cap.release()
    out.release()
    """)


def demo_custom_styling():
    """Demo 3: Clock with custom colors and styling"""
    import cv2
    import numpy as np
    from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock
    
    print("\nDemo 3: Creating clocks with custom styling...")
    
    # Create canvas
    img = np.zeros((600, 1200, 3), dtype=np.uint8)
    img[:] = (240, 240, 240)  # Light gray background
    
    # Style 1: Classic colorful
    colors_classic = {
        'background': (255, 255, 255),
        'border': (0, 0, 0),
        'hour_hand': (0, 0, 128),
        'minute_hand': (0, 0, 255),
        'second_hand': (255, 0, 0),
        'markers': (64, 64, 64),
    }
    
    img = draw_analog_clock(
        img, 
        position=(200, 150), 
        radius=100,
        colors=colors_classic
    )
    cv2.putText(img, "Classic Style", (120, 280), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Style 2: Monochrome professional
    colors_mono = {
        'background': (255, 255, 255),
        'border': (0, 0, 0),
        'hour_hand': (0, 0, 0),
        'minute_hand': (64, 64, 64),
        'second_hand': (128, 128, 128),
        'markers': (100, 100, 100),
    }
    
    img = draw_analog_clock(
        img, 
        position=(600, 150), 
        radius=100,
        colors=colors_mono
    )
    cv2.putText(img, "Monochrome", (520, 280), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Style 3: Dark theme
    colors_dark = {
        'background': (40, 40, 40),
        'border': (200, 200, 200),
        'hour_hand': (100, 255, 255),
        'minute_hand': (0, 255, 255),
        'second_hand': (0, 180, 255),
        'markers': (180, 180, 180),
    }
    
    img = draw_analog_clock(
        img, 
        position=(1000, 150), 
        radius=100,
        colors=colors_dark,
        background_alpha=0.9
    )
    cv2.putText(img, "Dark Theme", (920, 280), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Small clocks at bottom
    img = draw_analog_clock(img, position=(300, 450), radius=50)
    cv2.putText(img, "Small (r=50)", (220, 530), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    img = draw_analog_clock(img, position=(600, 450), radius=70)
    cv2.putText(img, "Medium (r=70)", (510, 550), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    img = draw_analog_clock(img, position=(900, 450), radius=90)
    cv2.putText(img, "Large (r=90)", (800, 570), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Save result
    cv2.imwrite("demo_clock_styles.jpg", img)
    print("  ✓ Saved to demo_clock_styles.jpg")
    
    return img


def demo_positions():
    """Demo 4: Clock in different positions"""
    import cv2
    import numpy as np
    from ac_training_lab.video_editing.analog_clock_overlay import draw_analog_clock
    
    print("\nDemo 4: Creating image with clocks in different positions...")
    
    # Create a video-like frame
    img = np.zeros((480, 854, 3), dtype=np.uint8)
    img[:] = (180, 200, 220)
    
    # Add a fake "video content" area
    cv2.rectangle(img, (50, 50), (804, 430), (100, 120, 140), -1)
    cv2.putText(
        img,
        "Video Content Area",
        (280, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (200, 200, 200),
        2
    )
    
    # Add clocks in all four corners
    positions = {
        "top-left": (80, 80),
        "top-right": (774, 80),
        "bottom-left": (80, 400),
        "bottom-right": (774, 400),
    }
    
    for name, pos in positions.items():
        img = draw_analog_clock(img, position=pos, radius=50, background_alpha=0.8)
    
    # Add labels
    cv2.putText(img, "Top-Left", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, "Top-Right", (700, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, "Bottom-Left", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, "Bottom-Right", (680, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Save result
    cv2.imwrite("demo_clock_positions.jpg", img)
    print("  ✓ Saved to demo_clock_positions.jpg")
    
    return img


def main():
    """Run all demos"""
    try:
        import cv2
    except ImportError:
        print("Error: OpenCV (cv2) is not installed.")
        print("Please install it with: pip install opencv-python")
        print("\nFor more information, see: docs/analog_clock_installation.md")
        sys.exit(1)
    
    print("=" * 60)
    print("Analog Clock Overlay Demonstrations")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_static_image()
        demo_video_processing()
        demo_custom_styling()
        demo_positions()
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        print("\nGenerated files:")
        print("  - demo_clock_static.jpg")
        print("  - demo_clock_styles.jpg")
        print("  - demo_clock_positions.jpg")
        print("\nFor more information:")
        print("  - docs/analog_clock_recommendations.md")
        print("  - docs/analog_clock_installation.md")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
