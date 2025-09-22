import asyncio
import utils
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost, GrpcWorkerAgentRuntime
from autogen_core import AgentId
from creator import Creator
import logging
from utils import setup_logging
import yaml
from end import End

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")


async def main():

    logger.info("Starting host and worker")
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")

    try:
        host.start()
        await worker.start()

        logger.info("Registering Creator agent")
        await Creator.register(worker, "Creator", lambda: Creator("Creator"))
        creator_id = AgentId("Creator", "default")

        logger.info("Registering End agent")
        await End.register(worker, "End", lambda: End("End"))
        end_id = AgentId("End", "default")

        with open("agents.yaml", "r") as f:
            spec = yaml.safe_load(f)

        content = yaml.safe_dump(spec)

        await asyncio.sleep(1)

        logger.info("Sending message to Creator")
        await worker.send_message(utils.Message(content=content), creator_id)

        await asyncio.sleep(5)

    finally:
        logger.info("Stopping worker and host cleanly")
        await worker.stop()
        await host.stop()


if __name__ == "__main__":
    asyncio.run(main())
