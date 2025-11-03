# orchestrator.py - Script to submit jobs to work queues
"""
This script demonstrates how to submit jobs to different work queues
with prioritization. It runs the deployments created earlier.
"""

from prefect.deployments import run_deployment


def submit_color_mixing_job():
    """
    Submit a high-priority color mixing job.
    This will be picked up by workers assigned to the 'high-priority' queue.
    """
    print("Submitting high-priority color mixing job...")
    run_deployment(
        name="mix-color/mix-color",
        parameters={"R": 120, "Y": 50, "B": 80, "mix_well": "B2"},
    )
    print("Color mixing job submitted to high-priority queue")


def submit_measurement_job():
    """
    Submit a standard priority measurement job.
    This will be picked up by workers assigned to the 'standard' queue.
    """
    print("Submitting standard priority measurement job...")
    run_deployment(
        name="move-sensor-to-measurement-position/move-sensor-to-measurement-position",
        parameters={"mix_well": "B2"},
    )
    print("Measurement job submitted to standard queue")


def submit_reset_job():
    """
    Submit a low-priority reset job.
    This will be picked up by workers assigned to the 'low-priority' queue.
    """
    print("Submitting low-priority reset job...")
    run_deployment(name="move-sensor-back/move-sensor-back")
    print("Reset job submitted to low-priority queue")


def run_full_experiment():
    """
    Run a complete experiment workflow with proper job prioritization.
    High-priority jobs (color mixing) run first, followed by measurements,
    and finally cleanup/reset operations.
    """
    print("Starting full experiment workflow...")

    # Step 1: Mix colors (high priority)
    submit_color_mixing_job()

    # Step 2: Position sensor for measurement (standard priority)
    submit_measurement_job()

    # Step 3: Reset sensor (low priority)
    submit_reset_job()

    print(
        "Full experiment workflow submitted. Jobs will be processed by available workers."
    )


if __name__ == "__main__":
    # Example: Run full experiment
    run_full_experiment()

    # Alternative: Submit individual jobs
    # submit_color_mixing_job()
    # submit_measurement_job()
    # submit_reset_job()
