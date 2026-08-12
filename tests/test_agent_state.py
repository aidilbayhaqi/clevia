from app.agent.state import can_transition
from app.db.models.enums import AgentState


def test_info_can_handoff():
    assert can_transition(AgentState.INFO, AgentState.HANDOFF)


def test_closed_cannot_execute_directly():
    assert not can_transition(AgentState.CLOSED, AgentState.EXECUTING)
