import asyncio
import utils
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost, GrpcWorkerAgentRuntime
from autogen_core import AgentId
from creator import Creator
import logging
from utils import setup_logging
import yaml
from end import End
from workflow_state import workflow_state

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")


async def main() -> None:

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
        await worker.send_message(utils.Message(content=content, sender="Host"), creator_id)
        
        try:
            success, result = await asyncio.wait_for(
                workflow_state.wait_for_completion(), 
                timeout=300
            )
        except asyncio.TimeoutError:
            print("❌ Workflow timed out after 5 minutes")
            success, result = False, "Workflow timed out"
        
        if success:
            print(f"✅ Workflow completed successfully!")
            print(f"Result: {result}")
        else:
            print(f"❌ Workflow failed: {result}")
            
    except Exception as e:
        logger.error(f"Main process error: {e}")

    finally:
        logger.info("Stopping worker and host cleanly")
        try:
            await worker.stop()
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")
        
        try:
            await host.stop()
        except Exception as e:
            logger.error(f"Error stopping host: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Main process completed")
