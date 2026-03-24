import json
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

TOKEN_CACHE_PATH = Path.home() / ".config" / "ac-picam" / "token.json"


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

    libcamera_cmd = [
        camera_cmd,
        "--inline",
        "--nopreview",
        "-t",
        "0",
        "--mode",
        "1536:864",
        "--width",
        "854",
        "--height",
        "480",
        "--framerate",
        "15",
        "--codec",
        "h264",
        "--bitrate",
        "1000000",
    ]

    if CAMERA_VFLIP:
        libcamera_cmd.extend(["--vflip"])
    if CAMERA_HFLIP:
        libcamera_cmd.extend(["--hflip"])

    libcamera_cmd.extend(["-o", "-"])

    ffmpeg_cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-thread_queue_size",
        "1024",
        "-use_wallclock_as_timestamps",
        "1",
        "-i",
        "pipe:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-preset",
        "fast",
        "-strict",
        "experimental",
        "-f",
        "flv",
        f"{ffmpeg_url.rstrip('/')}/{stream_key}",
    ]

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


def call_lambda(action, cam_name, workflow_name, privacy_status="private"):
    payload = {
        "action": action,
        "cam_name": cam_name,
        "workflow_name": workflow_name,
        "privacy_status": privacy_status,
    }
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
    try:
        call_lambda("end", CAM_NAME, WORKFLOW_NAME)
    except RuntimeError as e:
        message = str(e)
        if "no active stream" not in message and "Invalid transition" not in message:
            raise
        print("No endable active stream found; continuing")

    raw_body = call_lambda(
        "create", CAM_NAME, WORKFLOW_NAME, privacy_status=PRIVACY_STATUS
    )
    try:
        result = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        ffmpeg_url = result["result"]["ffmpeg_url"]
        stream_key = result["result"]["stream_key"]
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
        p1, p2 = start_stream(ffmpeg_url)
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
