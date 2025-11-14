import json
import logging
import socket
import time
from multiprocessing import Process

import cv2
import requests
from libcamera import Transform
from my_secrets import (
    CAM_NAME,
    CAMERA_HFLIP,
    CAMERA_VFLIP,
    LAMBDA_FUNCTION_URL,
    PRIVACY_STATUS,
    WORKFLOW_NAME,
)
from picamera2 import MappedArray, Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput


def start_stream(ffmpeg_url):
    picam2 = Picamera2()

    picam2.configure(
        picam2.create_video_configuration(
            main={"size": (1280, 720)}, transform=Transform(hflip=CAMERA_HFLIP, vflip=CAMERA_VFLIP)
        )
    )

    # Configure timestamp
    bg_colour = (0, 0, 0)
    colour = (255, 255, 255)
    origin = (0, 30)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    thickness = 2
    # Precompute text size for timestamp format (fixed width)
    sample_timestamp = "2024-06-01 12:34:56"  # Matches "%Y-%m-%d %X"
    text_size, _ = cv2.getTextSize(sample_timestamp, font, scale, thickness)
    text_w, text_h = text_size

    def apply_timestamp(request):
        timestamp = time.strftime("%Y-%m-%d %X")
        with MappedArray(request, "main") as m:
            x, y = origin
            cv2.rectangle(m.array, (0, 0), (x + text_w, y + text_h), bg_colour, -1)
            cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)
    # Create the ffmpeg command for streaming
    ffmpeg_cmd = [
        # Most options such as wallclock_for_timestamps, thread_queue_size, and audio are handled by Picamera2 https://github.com/raspberrypi/picamera2/blob/main/picamera2/outputs/ffmpegoutput.py
        # FLV is the livestream output file format
        "-f",
        "flv",
        ffmpeg_url,
    ]

    ffmpeg_cmd = " ".join(ffmpeg_cmd)

    # Initialize FfmpegOutput to handle streaming
    # Audio is required for youtube streaming. Since the rpi and rpi cameras don't have mics, the audio signal is blank
    ffmpeg_output = FfmpegOutput(ffmpeg_cmd, audio=True)
    YOUTUBE_720P_BITRATE = 1000000
    h264_encoder = H264Encoder(bitrate=YOUTUBE_720P_BITRATE)

    picam2.start_recording(encoder=h264_encoder, output=ffmpeg_output)

    return picam2


def call_lambda(action, CAM_NAME, WORKFLOW_NAME, privacy_status="private"):
    payload = {
        "action": action,
        "cam_name": CAM_NAME,
        "workflow_name": WORKFLOW_NAME,
        "privacy_status": privacy_status,
    }
    print(f"Sending to Lambda: {payload}")
    try:

        response = requests.post(LAMBDA_FUNCTION_URL, json=payload)
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        response.raise_for_status()
        # Try to decode JSON, otherwise fall back to raw text
        try:
            result = response.json()
            if isinstance(result, dict) and "statusCode" in result and "body" in result:
                body = result["body"]
            else:
                body = result
        except ValueError:
            body = response.text

        print(f"Lambda '{action}' succeeded: {body}")
        return body

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error occurred: {e} - Response: {response.text}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to decode Lambda response: {e}")


if __name__ == "__main__":
    # End previous broadcast and start a new one via Lambda
    call_lambda("end", CAM_NAME, WORKFLOW_NAME)
    raw_body = call_lambda(
        "create", CAM_NAME, WORKFLOW_NAME, privacy_status=PRIVACY_STATUS
    )
    try:
        result = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        ffmpeg_url = result["result"]["ffmpeg_url"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise RuntimeError(
            f"Cannot proceed: ffmpeg_url not found or response invalid → {e}"
        )

    print(f"Streaming to: {ffmpeg_url}")

    # Gracefully terminate picamera2 on keyboard interrupt or on error.
    # Reattempt if terminated due to error.
    run = True
    while run:
        picam2 = None
        try:
            print("Starting stream...")
            picam2 = start_stream(ffmpeg_url)
            print("Stream started")

            # Spin and wait for error.
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            run = False

        except Exception as e:
            print(f"Stream crashed {e}")
        finally:
            if picam2:
                try:
                    print("Stopping stream")
                    picam2.stop_recording()
                    print("Stream stopped")
                except Exception as e:
                    print(f"Error stopping stream {e}")

            if run:
                print("Retrying in 3 seconds")
                time.sleep(3)
