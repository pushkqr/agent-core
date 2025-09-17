import asyncio
import utils
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost, GrpcWorkerAgentRuntime
from autogen_core import AgentId
from creator import Creator
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")


async def main():
    spec = {
        "filename": "agents/calculator_agent.py",
        "agent_name": "calculator_agent",
        "description": "An agent that evaluates basic arithmetic expressions like 'Add 3 + 5'.",
        "system_message": "You are a calculator agent. You can evaluate basic math expressions."
    }

    logger.info("Starting host and worker")
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")

    try:
        host.start()
        await worker.start()

        logger.info("Registering Creator agent")
        await Creator.register(worker, "Creator", lambda: Creator("Creator"))
        creator_id = AgentId("Creator", "default")

        await asyncio.sleep(1)

        logger.info("Sending message to Creator to generate Calculator Agent")
        await worker.send_message(utils.Message(content=json.dumps(spec)), creator_id)

        await asyncio.sleep(5)

    finally:
        logger.info("Stopping worker and host cleanly")
        await worker.stop()
        await host.stop()


if __name__ == "__main__":
    asyncio.run(main())
