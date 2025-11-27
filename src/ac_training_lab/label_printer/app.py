"""
Gradio web app for AprilTag label printing with MQTT integration.

Generates AprilTags and sends print commands via MQTT to a local printer subscriber.
"""

import base64
import json
import os
from io import BytesIO

import gradio as gr
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont

HIVEMQ_HOST = os.environ.get("HIVEMQ_HOST", "")
HIVEMQ_USERNAME = os.environ.get("HIVEMQ_USERNAME", "")
HIVEMQ_PASSWORD = os.environ.get("HIVEMQ_PASSWORD", "")
PORT = 8883
MQTT_TOPIC = "label-printer/apriltag/print"

TAG_FAMILIES = ["tag36h11", "tag25h9", "tag16h5", "tagStandard41h12"]


def generate_apriltag(tag_id: int, tag_family: str, size: int = 300) -> Image.Image:
    """Generate an AprilTag image using pupil_apriltags if available."""
    try:
        from pupil_apriltags import apriltag

        tag_img_array = apriltag(tag_family, tag_id)
        tag_img = Image.fromarray(tag_img_array).convert("RGB")
        tag_img = tag_img.resize((size, size), Image.NEAREST)
    except (ImportError, Exception):
        tag_img = Image.new("RGB", (size, size), color="white")
        draw = ImageDraw.Draw(tag_img)
        draw.rectangle([10, 10, size - 10, size - 10], outline="black", width=3)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24
            )
        except OSError:
            font = ImageFont.load_default()
        draw.text(
            (size // 2, size // 2),
            f"{tag_family}\nID: {tag_id}",
            fill="black",
            font=font,
            anchor="mm",
        )
    return tag_img


def create_label_image(
    device_name: str, tag_id: int, tag_family: str, printed_by: str
) -> Image.Image:
    """Create a label image with AprilTag and device info."""
    label_width = 696  # 62mm label width in pixels at 300dpi
    label_height = 400

    label = Image.new("RGB", (label_width, label_height), color="white")

    tag_img = generate_apriltag(tag_id, tag_family, size=250)
    label.paste(tag_img, (20, 75))

    draw = ImageDraw.Draw(label)
    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text_x = 290
    draw.text((text_x, 80), device_name, fill="black", font=font_large)
    draw.text((text_x, 130), f"Tag ID: {tag_id}", fill="black", font=font_small)
    draw.text((text_x, 160), f"Family: {tag_family}", fill="black", font=font_small)
    if printed_by:
        draw.text((text_x, 200), f"By: {printed_by}", fill="black", font=font_small)

    return label


def preview_label(
    device_name: str, tag_id: int, tag_family: str, printed_by: str
) -> Image.Image:
    """Generate a preview of the label."""
    return create_label_image(device_name, tag_id, tag_family, printed_by)


def send_print_command(
    device_name: str,
    tag_id: int,
    tag_family: str,
    printed_by: str,
    use_custom_broker: bool,
    custom_host: str,
    custom_username: str,
    custom_password: str,
) -> str:
    """Send print command via MQTT."""
    host = custom_host if use_custom_broker else HIVEMQ_HOST
    username = custom_username if use_custom_broker else HIVEMQ_USERNAME
    password = custom_password if use_custom_broker else HIVEMQ_PASSWORD

    if not host:
        return "Error: MQTT broker host not configured"

    label_img = create_label_image(device_name, tag_id, tag_family, printed_by)
    buffer = BytesIO()
    label_img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    command = {
        "device_name": device_name,
        "tag_id": tag_id,
        "tag_family": tag_family,
        "printed_by": printed_by,
        "image_base64": img_base64,
    }

    client = None
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
        client.tls_set()
        client.username_pw_set(username, password)
        client.connect(host, PORT, 60)
        client.publish(MQTT_TOPIC, json.dumps(command), qos=1)
        return f"Print command sent for '{device_name}' (Tag ID: {tag_id})"
    except Exception as e:
        return f"Error sending print command: {e}"
    finally:
        if client:
            client.disconnect()


with gr.Blocks(title="AprilTag Label Printer") as demo:
    gr.Markdown("# AprilTag Label Printer")
    gr.Markdown("Generate and print AprilTag labels for equipment identification.")

    with gr.Row():
        with gr.Column():
            device_name = gr.Textbox(label="Device Name", placeholder="e.g., UR5e-001")
            tag_id = gr.Number(label="Tag ID", value=0, minimum=0, maximum=586)
            tag_family = gr.Dropdown(
                choices=TAG_FAMILIES, value="tag36h11", label="Tag Family"
            )
            printed_by = gr.Textbox(label="Printed By", placeholder="Your name")

            preview_btn = gr.Button("Preview Label")
            print_btn = gr.Button("Print Label", variant="primary")

        with gr.Column():
            preview_img = gr.Image(label="Label Preview", type="pil")
            status = gr.Textbox(label="Status", interactive=False)

    with gr.Accordion("MQTT Configuration", open=False):
        use_custom = gr.Checkbox(label="Use custom broker", value=False)
        custom_host = gr.Textbox(label="Custom Host", placeholder="broker.hivemq.com")
        custom_user = gr.Textbox(label="Custom Username")
        custom_pass = gr.Textbox(label="Custom Password", type="password")

    preview_btn.click(
        preview_label,
        inputs=[device_name, tag_id, tag_family, printed_by],
        outputs=preview_img,
    )

    print_btn.click(
        send_print_command,
        inputs=[
            device_name,
            tag_id,
            tag_family,
            printed_by,
            use_custom,
            custom_host,
            custom_user,
            custom_pass,
        ],
        outputs=status,
    )

demo.launch()
