export type UUID = string;

export type Clinic = {
  id: UUID;
  name: string;
  slug: string;
  tagline: string | null;
  description: string | null;
  timezone: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  instagram: string | null;
  brand_primary: string;
  brand_secondary: string;
  brand_accent: string;
};

export type Service = {
  id: UUID;
  name: string;
  slug: string;
  category: string;
  short_description: string | null;
  description: string | null;
  duration_minutes: number;
  price_from: number | string | null;
  currency: string;
};

export type Staff = {
  id: UUID;
  full_name: string;
  slug: string;
  staff_type: string;
  title: string | null;
  specialty: string | null;
  bio: string | null;
};

export type AvailabilitySlot = {
  staff_id: UUID;
  staff_name: string;
  starts_at: string;
  ends_at: string;
};

export type AuthUser = {
  id: UUID;
  clinic_id?: UUID;
  full_name: string;
  email: string;
  role: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type LeadStatus = "new" | "contacted" | "qualified" | "booked" | "won" | "lost";

export type Lead = {
  id: UUID;
  full_name: string;
  phone: string;
  email: string | null;
  source: string;
  status: LeadStatus;
  interest_service_id: UUID | null;
  assigned_to_user_id: UUID | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  interest?: string;
};

export type Client = {
  id: UUID;
  full_name: string;
  phone: string;
  email: string | null;
  birth_date: string | null;
  tags: string[];
  administrative_notes: string | null;
  created_at: string;
};

export type AppointmentStatus = "requested" | "confirmed" | "checked_in" | "completed" | "cancelled" | "no_show";

export type Appointment = {
  id: UUID;
  client_id: UUID | null;
  lead_id: UUID | null;
  service_id: UUID;
  staff_id: UUID;
  starts_at: string;
  ends_at: string;
  status: AppointmentStatus;
  source: string;
  customer_note: string | null;
  internal_note: string | null;
  created_at: string;
  client_name?: string;
  service_name?: string;
  staff_name?: string;
};

export type ConversationStatus = "ai_active" | "human_active" | "resolved";

export type Conversation = {
  id: UUID;
  clinic_id: UUID;
  lead_id: UUID | null;
  client_id: UUID | null;
  channel: string;
  status: ConversationStatus;
  agent_state: string;
  risk_level: string;
  assigned_user_id: UUID | null;
  handoff_reason: string | null;
  handoff_summary: string | null;
  handoff_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  visitor_name?: string;
  last_message?: string;
};

export type Message = {
  id: UUID;
  conversation_id: UUID;
  role: string;
  sender_type: string;
  content: string;
  model_name: string | null;
  trace_id: string | null;
  created_at: string;
};

export type KnowledgeDocument = {
  id: UUID;
  title: string;
  category: string;
  content: string;
  source_type: string;
  owner: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ConversationCreateResponse = {
  conversation_id: UUID;
  conversation_token: string;
  status: string;
  agent_state: string;
};

export type PublicMessageResponse = {
  message: string;
  message_id: UUID;
  conversation_status: string;
  state: string;
  intent: string;
  tools_used: Array<Record<string, unknown>>;
  sources: Array<Record<string, unknown>>;
  handoff: Record<string, unknown> | null;
  trace_id: string | null;
};
