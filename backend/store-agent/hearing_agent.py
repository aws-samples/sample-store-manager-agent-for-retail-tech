from strands import Agent
from bedrock_model import get_bedrock_model
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from prompt_loader import PromptLoader
import os
from config import config

REGION = config.REGION


def _load_system_prompt(filename: str) -> str:
    loader = PromptLoader()
    return loader.load_prompt(filename)


def create_hearing_agent(session_id=None, actor_id=None) -> Agent:
    bedrock_model = get_bedrock_model()

    system_prompt = _load_system_prompt("hearing_system_prompt.txt")

    memory_id = config.HEARING_AGENTCORE_MEMORY_ID

    memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id, session_id=session_id, actor_id=actor_id
    )

    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=memory_config, region_name=REGION
    )

    agent = Agent(
        model=bedrock_model,
        system_prompt=system_prompt,
        session_manager=session_manager,
        tools=[],
    )

    return agent
