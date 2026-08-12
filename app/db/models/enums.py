from enum import StrEnum


class UserRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    RECEPTIONIST = "receptionist"
    PRACTITIONER = "practitioner"


class StaffType(StrEnum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    THERAPIST = "therapist"
    BEAUTICIAN = "beautician"


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    BOOKED = "booked"
    WON = "won"
    LOST = "lost"


class LeadSource(StrEnum):
    WEBSITE = "website"
    CHATBOT = "chatbot"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    WALK_IN = "walk_in"
    MANUAL = "manual"


class AppointmentStatus(StrEnum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentSource(StrEnum):
    WEBSITE = "website"
    CHATBOT = "chatbot"
    CRM = "crm"
    WALK_IN = "walk_in"


class ConversationStatus(StrEnum):
    AI_ACTIVE = "ai_active"
    WAITING_HUMAN = "waiting_human"
    HUMAN_ACTIVE = "human_active"
    RESOLVED = "resolved"


class AgentState(StrEnum):
    INFO = "INFO"
    COLLECTING = "COLLECTING"
    CONFIRMING = "CONFIRMING"
    EXECUTING = "EXECUTING"
    HANDOFF = "HANDOFF"
    CLOSED = "CLOSED"


class KnowledgeStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"  # legacy compatibility until the next cleanup migration
    APPROVED = "approved"
    ARCHIVED = "archived"


class FeedbackRating(StrEnum):
    GOOD = "good"
    WRONG = "wrong"
    MISSING_KNOWLEDGE = "missing_knowledge"
