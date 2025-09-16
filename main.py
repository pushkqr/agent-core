import asyncio
import utils
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost, GrpcWorkerAgentRuntime
from autogen_core import AgentId
from creator import Creator
from agent import Agent
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

async def main():
    logger.info("Starting host and worker")
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()

    logger.info("Registering Creator agent")
    await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")

    await asyncio.sleep(1)

    logger.info("Sending message to Creator to generate Calculator Agent")
    await worker.send_message(utils.Message(content="calculator_agent.py"), creator_id)

    await asyncio.sleep(5)

    logger.info("Stopping worker and host")
    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        logger.exception(e)

if __name__ == "__main__":
    asyncio.run(main())
