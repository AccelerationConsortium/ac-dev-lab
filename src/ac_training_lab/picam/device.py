import json
import os
import shutil
import subprocess

import requests
from my_secrets import (
    CAM_NAME,
    CAMERA_HFLIP,
    CAMERA_VFLIP,
    LAMBDA_FUNCTION_URL,
    PRIVACY_STATUS,
    WORKFLOW_NAME,
)


def get_camera_command():
    """
    Returns the available camera command: 'rpicam-vid' (trixie) or 'libcamera-vid' (bookworm).
    """
    if shutil.which("rpicam-vid"):
        return "rpicam-vid"
    elif shutil.which("libcamera-vid"):
        return "libcamera-vid"
    else:
        raise RuntimeError(
            "Neither 'rpicam-vid' nor 'libcamera-vid' command found on this system"
        )


def start_stream(ffmpeg_url, stream_key=None):
    """
    Starts the libcamera -> ffmpeg pipeline and returns two Popen objects:
      p1: camera process (rpicam-vid or libcamera-vid)
      p2: ffmpeg process
    """
    camera_cmd = get_camera_command()

    stream_width = int(os.environ.get("PICAM_WIDTH", "640"))
    stream_height = int(os.environ.get("PICAM_HEIGHT", "360"))
    stream_fps = int(os.environ.get("PICAM_FPS", "15"))
    video_bitrate = os.environ.get("PICAM_VIDEO_BITRATE", "1000k")
    video_maxrate = os.environ.get("PICAM_VIDEO_MAXRATE", video_bitrate)
    video_bufsize = os.environ.get("PICAM_VIDEO_BUFSIZE", "2000k")
    x264_preset = os.environ.get("PICAM_X264_PRESET", "ultrafast")
    input_codec = os.environ.get("PICAM_INPUT_CODEC", "raw").lower()
    camera_bitrate = os.environ.get("PICAM_CAMERA_BITRATE", "1200000")
    gop = str(stream_fps * 2)

    libcamera_cmd = [
        camera_cmd,
        "--inline",
        "--nopreview",
        "-t",
        "0",
        "--mode",
        "1280:720",
        "--width",
        str(stream_width),
        "--height",
        str(stream_height),
        "--framerate",
        str(stream_fps),
    ]
    if input_codec == "h264":
        libcamera_cmd.extend(
            [
                "--codec",
                "h264",
                "--profile",
                "baseline",
                "--intra",
                gop,
                "--bitrate",
                str(camera_bitrate),
            ]
        )
    else:
        libcamera_cmd.extend(["--codec", "yuv420"])

    if CAMERA_VFLIP:
        libcamera_cmd.extend(["--vflip"])
    if CAMERA_HFLIP:
        libcamera_cmd.extend(["--hflip"])

    libcamera_cmd.extend(["-o", "-"])

    if input_codec == "h264":
        input_opts = [
            "-f",
            "h264",
            "-r",
            str(stream_fps),
            "-i",
            "pipe:0",
        ]
    else:
        input_opts = [
            "-f",
            "rawvideo",
            "-pix_fmt",
            "yuv420p",
            "-s",
            f"{stream_width}x{stream_height}",
            "-r",
            str(stream_fps),
            "-i",
            "pipe:0",
        ]

    output_url = (
        f"{ffmpeg_url.rstrip('/')}/{stream_key}" if stream_key else ffmpeg_url
    )
    ffmpeg_cmd = (
        [
            "ffmpeg",
            "-thread_queue_size",
            "1024",
            "-use_wallclock_as_timestamps",
            "1",
            "-fflags",
            "+genpts",
            "-analyzeduration",
            "10000000",
            "-probesize",
            "10000000",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
        ]
        + input_opts
        + [
            "-filter:a",
            "aresample=async=1:first_pts=0",
            "-c:v",
            "libx264",
            "-preset",
            x264_preset,
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-g",
            gop,
            "-keyint_min",
            gop,
            "-sc_threshold",
            "0",
            "-b:v",
            video_bitrate,
            "-maxrate",
            video_maxrate,
            "-bufsize",
            video_bufsize,
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "flv",
            output_url,
        ]
    )

    p1 = subprocess.Popen(
        libcamera_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    p2 = subprocess.Popen(ffmpeg_cmd, stdin=p1.stdout, stderr=subprocess.STDOUT)
    p1.stdout.close()
    return p1, p2


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
        stream_key = result["result"].get("stream_key")
        if not stream_key and ffmpeg_url and "/" in ffmpeg_url:
            ffmpeg_url, stream_key = ffmpeg_url.rsplit("/", 1)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise RuntimeError(
            f"Cannot proceed: stream connection details not found or response invalid -> {e}"
        )

    output_url = f"{ffmpeg_url.rstrip('/')}/{stream_key}" if stream_key else ffmpeg_url
    print(f"Streaming to: {output_url}")

    if not shutil.which("rpicam-vid") and not shutil.which("libcamera-vid"):
        print("No Raspberry Pi camera command found; exiting after Lambda dry-run")
        raise SystemExit(0)

    while True:
        print("Starting stream..")
        p1, p2 = start_stream(ffmpeg_url, stream_key)
        print("Stream started")
        interrupted = False
        try:
            p2.wait()
        except KeyboardInterrupt:
            print("Received interrupt signal, exiting...")
            interrupted = True
        except Exception as e:
            print(e)
        finally:
            print("Terminating processes..")
            p1.terminate()
            p2.terminate()
            print("Processes terminated.")
            if interrupted:
                break
            else:
                print("Retrying..")
