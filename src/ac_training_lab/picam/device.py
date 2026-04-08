import json
import os
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path

import requests
from my_secrets import (
    CAM_NAME,
    CAMERA_HFLIP,
    CAMERA_VFLIP,
    LAMBDA_FUNCTION_URL,
    PRIVACY_STATUS,
    WORKFLOW_NAME,
)

try:
    from my_secrets import AUTH_BASE_URL
except ImportError:
    AUTH_BASE_URL = "http://localhost:5000"

try:
    from my_secrets import AUTH_TAILSCALE_IP
except ImportError:
    AUTH_TAILSCALE_IP = ""

try:
    from my_secrets import LAMBDA_TOKEN
except ImportError:
    LAMBDA_TOKEN = ""

try:
    from my_secrets import FORCE_NEW
except ImportError:
    FORCE_NEW = False

TOKEN_CACHE_PATH = Path.home() / ".config" / "ac-picam" / "token.json"
STREAM_STATE_PATH = Path.home() / ".config" / "ac-picam" / "stream.json"


def load_cached_token():
    if LAMBDA_TOKEN:
        return LAMBDA_TOKEN
    if not TOKEN_CACHE_PATH.exists():
        return None
    try:
        data = json.loads(TOKEN_CACHE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("token")


def save_cached_token(token):
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(json.dumps({"token": token}) + "\n")


def load_cached_stream_id():
    if not STREAM_STATE_PATH.exists():
        return None
    try:
        data = json.loads(STREAM_STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("stream_id")


def save_cached_stream_id(stream_id):
    if not stream_id:
        return
    STREAM_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STREAM_STATE_PATH.write_text(json.dumps({"stream_id": stream_id}) + "\n")


def login_for_lambda_token():
    params = {}
    if AUTH_TAILSCALE_IP:
        params["tailscale_ip"] = AUTH_TAILSCALE_IP

    start = requests.get(
        f"{AUTH_BASE_URL.rstrip('/')}/device/start",
        params=params or None,
        timeout=15,
    )
    start.raise_for_status()
    payload = start.json()

    login_url = payload["login_url"]
    device_code = payload["device_code"]
    poll_interval = payload.get("poll_interval", 2)

    print("Log in with GitHub here:")
    print(login_url)
    try:
        webbrowser.open(login_url)
    except Exception:
        pass

    while True:
        poll = requests.get(
            f"{AUTH_BASE_URL.rstrip('/')}/device/poll",
            params={"device_code": device_code},
            timeout=15,
        )
        poll.raise_for_status()
        result = poll.json()
        if result.get("status") == "approved" and result.get("token"):
            token = result["token"]
            save_cached_token(token)
            return token
        time.sleep(poll_interval)


def get_lambda_token(force_refresh=False):
    if not force_refresh:
        cached = load_cached_token()
        if cached:
            return cached
    return login_for_lambda_token()


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


def start_stream(ffmpeg_url, stream_key):
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
            "-af",
            "aresample=async=1:first_pts=0",
        ]
        + input_opts
        + [
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
            f"{ffmpeg_url.rstrip('/')}/{stream_key}",
        ]
    )

    p1 = subprocess.Popen(
        libcamera_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    p2 = subprocess.Popen(ffmpeg_cmd, stdin=p1.stdout, stderr=subprocess.STDOUT)
    p1.stdout.close()
    return p1, p2


def _post_lambda(payload, token):
    return requests.post(
        LAMBDA_FUNCTION_URL,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )


def call_lambda(
    action, cam_name, workflow_name, privacy_status="private", stream_id=None
):
    payload = {
        "action": action,
        "cam_name": cam_name,
        "workflow_name": workflow_name,
        "privacy_status": privacy_status,
    }
    if action == "create":
        payload["force_new"] = FORCE_NEW
    if stream_id:
        payload["stream_id"] = stream_id
    print(f"Sending to Lambda: {payload}")

    token = get_lambda_token()

    try:
        response = _post_lambda(payload, token)
        if response.status_code == 401:
            print("Lambda token missing or expired; starting GitHub login flow")
            token = get_lambda_token(force_refresh=True)
            response = _post_lambda(payload, token)

        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        response.raise_for_status()
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
    cached_stream_id = load_cached_stream_id()
    if cached_stream_id:
        try:
            call_lambda("end", CAM_NAME, WORKFLOW_NAME, stream_id=cached_stream_id)
        except RuntimeError as e:
            message = str(e)
            if (
                "no active stream" not in message
                and "Invalid transition" not in message
                and "Redundant transition" not in message
            ):
                raise
            print("No endable active stream found; continuing")
    else:
        print("No cached stream_id found; skipping end step.")

    raw_body = call_lambda(
        "create", CAM_NAME, WORKFLOW_NAME, privacy_status=PRIVACY_STATUS
    )
    try:
        result = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        ffmpeg_url = result["result"]["ffmpeg_url"]
        stream_key = result["result"].get("stream_key")
        if not stream_key and ffmpeg_url and "/" in ffmpeg_url:
            ffmpeg_url, stream_key = ffmpeg_url.rsplit("/", 1)
        stream_id = result["result"].get("stream_id")
        if stream_id:
            save_cached_stream_id(stream_id)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise RuntimeError(
            f"Cannot proceed: stream connection details not found or response invalid -> {e}"
        )

    print(f"Streaming to: {ffmpeg_url}/{stream_key}")

    if not shutil.which("rpicam-vid") and not shutil.which("libcamera-vid"):
        print("No Raspberry Pi camera command found; exiting after Lambda dry-run")
        raise SystemExit(0)

    while True:
        print("Starting stream..")
        p1, p2 = start_stream(ffmpeg_url, stream_key)
        print("Stream started")
        time.sleep(8)
        if stream_id:
            life_cycle = None
            for attempt in range(6):
                try:
                    status_body = call_lambda(
                        "status", CAM_NAME, WORKFLOW_NAME, stream_id=stream_id
                    )
                    status = (
                        status_body.get("result")
                        if isinstance(status_body, dict)
                        else None
                    )
                    life_cycle = ((status or {}).get("status") or {}).get(
                        "lifeCycleStatus"
                    )
                    if life_cycle in ("ready", "testing", "live"):
                        break
                except RuntimeError as e:
                    print(f"Status check failed: {e}")
                time.sleep(5)

            for action in ("testing", "live"):
                if life_cycle == "live":
                    break
                if action == "testing" and life_cycle == "testing":
                    continue
                for attempt in range(3):
                    try:
                        call_lambda(
                            action, CAM_NAME, WORKFLOW_NAME, stream_id=stream_id
                        )
                        break
                    except RuntimeError as e:
                        message = str(e)
                        if "Invalid transition" in message and action == "testing":
                            break
                        print(
                            f"{action} transition failed (attempt {attempt + 1}): {e}"
                        )
                        time.sleep(5)
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
