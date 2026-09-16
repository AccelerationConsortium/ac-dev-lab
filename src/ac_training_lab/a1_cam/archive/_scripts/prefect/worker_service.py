from prefect.worker.base import BaseWorker

from .device_prefect import A1CamCapture


class A1CamWorker(BaseWorker):
    """
    Custom Prefect worker that maintains a persistent A1CamCapture instance
    for hardware reuse across flow runs. Runs flows in the same process for persistence.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam_capture = A1CamCapture()

    async def run_flow(self, flow_run):
        """
        Run the flow in the same process to maintain hardware persistence.
        """
        flow = flow_run.flow
        # Bind the flow method to the persistent instance
        if hasattr(flow, "__func__"):
            # Unbound method
            bound_method = flow.__func__.__get__(self.cam_capture, A1CamCapture)
            result = await bound_method()
        else:
            # Already bound or other
            result = await flow()
        return result

    def cleanup(self):
        """Clean up the persistent camera instance."""
        if hasattr(self, "cam_capture"):
            self.cam_capture.cleanup()


if __name__ == "__main__":
    import asyncio
    import os

    async def main():
        worker = A1CamWorker(
            work_pool_name=os.environ.get("PREFECT_WORK_POOL", "a1-cam-pool")
        )
        await worker.start()

    asyncio.run(main())
