from app.db.models.enums import AgentState


ALLOWED_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.INFO: {
        AgentState.INFO,
        AgentState.COLLECTING,
        AgentState.HANDOFF,
        AgentState.CLOSED,
    },
    AgentState.COLLECTING: {
        AgentState.CONFIRMING,
        AgentState.HANDOFF,
        AgentState.CLOSED,
    },
    AgentState.CONFIRMING: {
        AgentState.EXECUTING,
        AgentState.COLLECTING,
        AgentState.HANDOFF,
        AgentState.CLOSED,
    },
    AgentState.EXECUTING: {AgentState.CLOSED, AgentState.HANDOFF},
    AgentState.HANDOFF: {AgentState.INFO, AgentState.CLOSED},
    AgentState.CLOSED: {AgentState.INFO},
}


def can_transition(current: AgentState, target: AgentState) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
