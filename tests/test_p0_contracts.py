from app.agent.router import Intent, route_intent
from app.db.models.conversation import Conversation, Message
from app.db.models.enums import AgentState
from app.schemas.conversation import PublicMessageResponse


def test_agent_state_contract_exists():
    assert AgentState.INFO.value == "INFO"
    assert AgentState.COLLECTING.value == "COLLECTING"
    assert AgentState.HANDOFF.value == "HANDOFF"


def test_conversation_model_contains_p0_state_fields():
    assert hasattr(Conversation, "agent_state")
    assert hasattr(Conversation, "assigned_user_id")
    assert hasattr(Conversation, "handoff_summary")
    assert hasattr(Conversation, "resolved_at")


def test_message_trace_link_exists():
    assert hasattr(Message, "trace_id")


def test_lead_intents_are_separate_from_general_information():
    assert route_intent("Saya tertarik facial acne") == Intent.SERVICE_INTEREST
    assert route_intent("Saya mau booking hari Sabtu") == Intent.BOOKING_INTEREST
    assert route_intent("Berapa harga facial?") == Intent.INFORMATION


def test_public_message_response_supports_trace_and_state():
    fields = PublicMessageResponse.model_fields
    assert "state" in fields
    assert "intent" in fields
    assert "trace_id" in fields
    assert "sources" in fields