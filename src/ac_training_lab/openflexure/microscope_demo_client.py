# generate a jwt
# hive mq api to add this jwt to the list of tokens
# expire this token after a given timeframe with api

# mqtt to the microscope commands with attached credentials
# recieve returned mqtt/stored images

# recieve the payload
# execute the command
# return the images/store them etc

import base64
import json
import time
from io import BytesIO
from queue import Queue
import threading
import datetime
import os

import paho.mqtt.client as mqtt
from PIL import Image

# microscope1
# microscope2
# deltastagereflection
# deltastagetransmission


class MicroscopeDemo:
    def __init__(self, host, port, username, password, microscope):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.microscope = microscope

        self.client = mqtt.Client()
        self.client.tls_set()
        self.client.username_pw_set(self.username, self.password)

        self.receiveq = Queue()
        
        # Video recording attributes
        self._recording = False
        self._recording_thread = None
        self._frames = []
        self._recording_start_time = None

        def on_message(client, userdata, message):
            received = json.loads(message.payload.decode("utf-8"))
            self.receiveq.put(received)
            if len(json.dumps(received)) <= 300:
                print(received)
            else:
                try:
                    print(json.dumps(received)[:300] + "...")
                except Exception as e:
                    print(f"Command printing error (program will continue): {e}")

        self.client.on_message = on_message

        self.client.connect(self.host, port=self.port, keepalive=60, bind_address="")

        self.client.loop_start()

        self.client.subscribe(self.microscope + "/return", qos=2)

    def scan_and_stitch(self, c1, c2, ov=1200, foc=0):  # WIP
        command = json.dumps(
            {"command": "scan_and_stitch", "c1": c1, "c2": c2, "ov": ov, "foc": foc}
        )
        self.client.publish(
            self.microscope + "/command", payload=command, qos=2, retain=False
        )
        while self.receiveq.empty():
            time.sleep(0.05)
        image = self.receiveq.get()
        image_string = image["image"]
        image_bytes = base64.b64decode(image_string)
        image_object = Image.open(BytesIO(image_bytes))
        return image_object

    def move(self, x, y, z=False, relative=False):
        """moves to given coordinates x, y (and z if it is set to any integer
        value, if it is set to False the z value wont change). If relative is
        True, then it will move relative to the current position instead of
        moving to the absolute coordinates"""
        command = json.dumps(
            {"command": "move", "x": x, "y": y, "z": z, "relative": relative}
        )
        self.client.publish(
            self.microscope + "/command", payload=command, qos=2, retain=False
        )
        while self.receiveq.empty():
            time.sleep(0.05)
        return self.receiveq.get()

    def scan(self, c1, c2, ov=1200, foc=0):
        """returns a list of image objects. Takes images to scan an entire area
        specified by two corners. you can input the corner coordinates as "x1
        y1", "x2, y2" or [x1, y1], [x2, y2]. ov refers to the overlap between
        the images (useful for stitching) and foc refers to how much the
        microscope should focus between images (0 to disable)"""
        command = json.dumps(
            {"command": "scan", "c1": c1, "c2": c2, "ov": ov, "foc": foc}
        )
        self.client.publish(
            self.microscope + "/command", payload=command, qos=2, retain=False
        )
        while self.receiveq.empty():
            time.sleep(0.05)
        image_l = self.receiveq.get()
        image_list = image_l["images"]
        for i in range(len(image_list)):
            image = image_list[i]
            image_bytes = base64.b64decode(image)
            image_object = Image.open(BytesIO(image_bytes))
            image_list[i] = image_object
        return image_list

    def focus(
        self, amount="fast"
    ):  # focuses by different amounts: huge, fast, medium, fine, or any integer value
        command = json.dumps({"command": "focus", "amount": amount})
        self.client.publish(
            self.microscope + "/command", payload=command, qos=2, retain=False
        )
        while self.receiveq.empty():
            time.sleep(0.05)
        return self.receiveq.get()

    def get_pos(
        self,
    ):  # returns a dictionary with x, y, and z coordinates eg. {'x':1,'y':2,'z':3}
        command = json.dumps({"command": "get_pos"})
        self.client.publish(
            self.microscope + "/command", payload=command, qos=2, retain=False
        )
        while self.receiveq.empty():
            time.sleep(0.05)
        pos = self.receiveq.get()
        return pos["pos"]

    def take_image(self):  # returns an image object
        command = json.dumps({"command": "take_image"})
        self.client.publish(
            self.microscope + "/command", payload=command, qos=2, retain=False
        )
        while self.receiveq.empty():
            time.sleep(0.05)
        image = self.receiveq.get()
        image_string = image["image"]
        image_bytes = base64.b64decode(image_string)
        image_object = Image.open(BytesIO(image_bytes))
        return image_object

    def end_connection(self):  # ends the connection
        # Stop recording if active
        if self._recording:
            self.stop_video_recording()
        self.client.loop_stop()
        self.client.disconnect()

    def start_video_recording(self, fps=2, output_dir="./recordings"):
        """
        Start recording video by continuously capturing frames.
        
        Args:
            fps (int): Frames per second for video recording (default: 2)
            output_dir (str): Directory to save recorded videos
        """
        if self._recording:
            print("Video recording is already in progress")
            return
            
        self._recording = True
        self._frames = []
        self._recording_start_time = datetime.datetime.now()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        def capture_frames():
            """Continuously capture frames while recording is active"""
            frame_interval = 1.0 / fps
            
            print(f"Starting video recording at {fps} fps...")
            while self._recording:
                try:
                    # Capture frame using existing take_image method
                    frame = self.take_image()
                    if frame:
                        timestamp = datetime.datetime.now()
                        self._frames.append((frame, timestamp))
                        print(f"Captured frame {len(self._frames)} at {timestamp.strftime('%H:%M:%S.%f')[:-3]}")
                    
                    time.sleep(frame_interval)
                except Exception as e:
                    print(f"Error capturing frame: {e}")
                    if not self._recording:  # Exit if recording was stopped due to error
                        break
                    time.sleep(frame_interval)
        
        self._recording_thread = threading.Thread(target=capture_frames, daemon=True)
        self._recording_thread.start()
        
        return True

    def stop_video_recording(self, output_filename=None):
        """
        Stop video recording and save frames to disk.
        
        Args:
            output_filename (str): Custom filename for the output. If None, generates timestamped filename.
            
        Returns:
            str: Path to the saved video file
        """
        if not self._recording:
            print("No video recording in progress")
            return None
            
        self._recording = False
        
        # Wait for recording thread to finish
        if self._recording_thread:
            self._recording_thread.join(timeout=5.0)
        
        if not self._frames:
            print("No frames captured during recording")
            return None
            
        # Generate filename if not provided
        if output_filename is None:
            timestamp = self._recording_start_time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"microscope_recording_{timestamp}.gif"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filename) or "./recordings"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, os.path.basename(output_filename))
        
        try:
            # Save as animated GIF for simplicity (can be extended to MP4 later)
            images = [frame[0] for frame in self._frames]
            
            # Calculate duration based on actual frame timestamps
            if len(self._frames) > 1:
                total_duration = (self._frames[-1][1] - self._frames[0][1]).total_seconds() * 1000
                frame_duration = int(total_duration / len(self._frames))
            else:
                frame_duration = 500  # Default 500ms per frame
                
            print(f"Saving {len(images)} frames to {full_path}...")
            images[0].save(
                full_path,
                save_all=True,
                append_images=images[1:],
                duration=frame_duration,
                loop=0
            )
            
            print(f"Video recording saved: {full_path}")
            print(f"Recording duration: {len(self._frames)} frames over {(self._frames[-1][1] - self._frames[0][1]).total_seconds():.2f} seconds")
            
            # Clear frames after saving
            self._frames = []
            
            return full_path
            
        except Exception as e:
            print(f"Error saving video recording: {e}")
            return None

    def record_video_for_duration(self, duration_seconds=30, fps=2, output_filename=None):
        """
        Record video for a specific duration.
        
        Args:
            duration_seconds (int): How long to record in seconds
            fps (int): Frames per second
            output_filename (str): Custom output filename
            
        Returns:
            str: Path to saved video file
        """
        print(f"Starting {duration_seconds}-second video recording...")
        
        self.start_video_recording(fps=fps)
        
        if not self._recording:
            return None
            
        # Wait for specified duration
        time.sleep(duration_seconds)
        
        return self.stop_video_recording(output_filename)
