from datetime import datetime, timezone

import boto3
from libcamera import Transform
from picamera2 import Picamera2
from prefect import flow

from my_secrets import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
)


@flow
def capture_image(picam2: Picamera2, s3: boto3.client) -> str:
    """Capture image and upload to S3, return URI."""
    picam2.autofocus_cycle()
    picam2.capture_file("image.jpeg")

    object_name = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H:%M:%S") + ".jpeg"
    s3.upload_file("image.jpeg", BUCKET_NAME, object_name)

    return f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"


if __name__ == "__main__":
    from prefect import deploy

    # Initialize once at startup
    picam2 = Picamera2()
    picam2.set_controls({"AfMode": "auto"})
    picam2.options["quality"] = 90
    config = picam2.create_still_configuration(transform=Transform(vflip=1))
    picam2.configure(config)
    picam2.start()

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

    deploy(
        capture_image.to_deployment(
            name="capture-image", parameters={"picam2": picam2, "s3": s3}
        ),
    )
