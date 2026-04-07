"""
Agent module for LLM-powered deal analysis.

All agents are database-driven via the DynamicAgent class.
Use get_agent(slug) or get_agent_by_id(id) to resolve agents.
"""
import logging

logger = logging.getLogger(__name__)

_DynamicAgent = None
_BaseAgent = None


def _import_dynamic_agent():
    global _DynamicAgent, _BaseAgent
    if _DynamicAgent is None:
        from .dynamic_agent import DynamicAgent
        _DynamicAgent = DynamicAgent
    if _BaseAgent is None:
        from .base_agent import BaseAgent
        _BaseAgent = BaseAgent


def get_agent(agent_slug: str):
    """
    Get the specialist agent for a given agent slug.
    Resolves from the database (Agent model) and returns a DynamicAgent.
    """
    _import_dynamic_agent()

    from apps.scanners.models import Agent as AgentModel
    try:
        agent_record = AgentModel.objects.get(slug=agent_slug, enabled=True)
    except AgentModel.DoesNotExist:
        raise ValueError(
            f"No enabled agent found with slug '{agent_slug}'. "
            f"Create an agent via the UI first."
        )

    logger.debug(f"Resolved agent '{agent_slug}' from database")
    return _DynamicAgent(agent_record)


def get_agent_by_id(agent_id: int):
    _import_dynamic_agent()
    from apps.scanners.models import Agent as AgentModel
    agent_record = AgentModel.objects.get(id=agent_id, enabled=True)
    return _DynamicAgent(agent_record)


def __getattr__(name):
    _import_dynamic_agent()
    mapping = {'DynamicAgent': '_DynamicAgent', 'BaseAgent': '_BaseAgent'}
    if name in mapping:
        return globals()[mapping[name]]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ['DynamicAgent', 'BaseAgent', 'get_agent', 'get_agent_by_id']
