# AWS Lambda Function URL - Required for YouTube streaming
# This URL is obtained by deploying the streamingLambda service to AWS.
# See: https://github.com/AccelerationConsortium/streamingLambda
# The Lambda function handles YouTube API calls to create and manage live streams.
LAMBDA_FUNCTION_URL = "your_Lambda_function_url"

# Camera Name - Used for identifying this specific camera device
# This appears in the YouTube broadcast title alongside the workflow name and timestamp.
# Examples: "PiCam-01", "LabCam-A", "MainCamera"
CAM_NAME = "your_camera_name"

# Workflow Name - Used for organizing streams into playlists
# IMPORTANT: This must be UNIQUE across all devices to avoid conflicts.
# The workflow name is used to:
# - Create/find YouTube playlists
# - End streams for this specific workflow
# - Organize videos by experimental setup or location
# Keep it short (YouTube has character limits) and descriptive.
# Examples: "SDLT-Toronto-001", "MyLab-Setup-A", "AC-Synthesis-Bench"
# Related issue: https://github.com/AccelerationConsortium/ac-dev-lab/issues/290
WORKFLOW_NAME = "your_workflow_name"

# YouTube Privacy Status - Controls who can view the live stream
# Options: "private" (only you), "public" (anyone), "unlisted" (anyone with link)
# For lab monitoring, "unlisted" is often preferred for controlled sharing.
PRIVACY_STATUS = "private"  # "private", "public", or "unlisted"

# Camera orientation settings
# Set to True to flip the camera image vertically (rotate 180° around horizontal axis)
CAMERA_VFLIP = True
# Set to True to flip the camera image horizontally (mirror image)
CAMERA_HFLIP = True
