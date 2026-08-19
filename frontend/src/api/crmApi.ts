import { request } from "./client";
import { TOKEN_KEY } from "../config";
import type { Appointment, AppointmentStatus, AuthUser, Client, Conversation, KnowledgeDocument, Lead, LeadStatus, LoginResponse, Message, Service, Staff, UUID } from "../types";

export const crmApi = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const data = await request<LoginResponse>("/auth/login", { method: "POST", body: { email, password } });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    return data;
  },
  me: () => request<AuthUser>("/auth/me", { auth: true }),
  async leads(): Promise<Lead[]> {
    const [rows, services] = await Promise.all([
      request<Lead[]>("/crm/leads", { auth: true }),
      request<Service[]>("/public/services"),
    ]);
    const serviceMap = new Map(services.map((item) => [item.id, item.name]));
    return rows.map((lead) => ({
      ...lead,
      interest: lead.interest_service_id ? serviceMap.get(lead.interest_service_id) || "Unknown service" : "—",
    }));
  },
  updateLead: (leadId: UUID, payload: Partial<{
    full_name: string;
    phone: string;
    email: string | null;
    status: LeadStatus;
    interest_service_id: UUID | null;
    assigned_to_user_id: UUID | null;
    notes: string | null;
  }>) => request<Lead>(`/crm/leads/${leadId}`, { method: "PATCH", auth: true, body: payload }),
  clients: () => request<Client[]>("/crm/clients", { auth: true }),
  async appointments(): Promise<Appointment[]> {
    const [appointments, services, staff, clients, leads] = await Promise.all([
      request<Appointment[]>("/appointments", { auth: true }),
      request<Service[]>("/public/services"),
      request<Staff[]>("/public/staff"),
      request<Client[]>("/crm/clients", { auth: true }),
      request<Lead[]>("/crm/leads", { auth: true }),
    ]);
    const serviceMap = new Map(services.map((item) => [item.id, item.name]));
    const staffMap = new Map(staff.map((item) => [item.id, item.full_name]));
    const clientMap = new Map(clients.map((item) => [item.id, item.full_name]));
    const leadMap = new Map(leads.map((item) => [item.id, item.full_name]));
    return appointments.map((appointment) => ({
      ...appointment,
      service_name: serviceMap.get(appointment.service_id) || "Unknown service",
      staff_name: staffMap.get(appointment.staff_id) || "Unknown staff",
      client_name:
        (appointment.client_id && clientMap.get(appointment.client_id)) ||
        (appointment.lead_id && leadMap.get(appointment.lead_id)) ||
        "Unlinked client",
    }));
  },
  updateAppointment: (appointmentId: UUID, payload: Partial<{ status: AppointmentStatus; internal_note: string | null }>) =>
    request<Appointment>(`/appointments/${appointmentId}`, { method: "PATCH", auth: true, body: payload }),
  async conversations(): Promise<Conversation[]> {
    const [rows, clients, leads] = await Promise.all([
      request<Conversation[]>("/conversations", { auth: true }),
      request<Client[]>("/crm/clients", { auth: true }),
      request<Lead[]>("/crm/leads", { auth: true }),
    ]);
    const clientMap = new Map(clients.map((item) => [item.id, item.full_name]));
    const leadMap = new Map(leads.map((item) => [item.id, item.full_name]));
    return rows.map((conversation) => ({
      ...conversation,
      visitor_name:
        (conversation.client_id && clientMap.get(conversation.client_id)) ||
        (conversation.lead_id && leadMap.get(conversation.lead_id)) ||
        `Visitor ${conversation.id.slice(0, 6)}`,
      last_message: conversation.handoff_summary || "Open conversation",
    }));
  },
  transcript: (id: UUID) => request<Message[]>(`/conversations/${id}/messages`, { auth: true }),
  takeover: (id: UUID) => request<{ status: string; agent_state: string }>(`/conversations/${id}/takeover`, { method: "POST", auth: true }),
  release: (id: UUID) => request<{ status: string; agent_state: string }>(`/conversations/${id}/release`, { method: "POST", auth: true }),
  resolve: (id: UUID) => request<{ status: string; agent_state: string }>(`/conversations/${id}/resolve`, { method: "POST", auth: true }),
  reply: (id: UUID, message: string) => request<Message>(`/conversations/${id}/messages`, { method: "POST", auth: true, body: { message } }),
  knowledge: () => request<KnowledgeDocument[]>("/knowledge", { auth: true }),
  createKnowledge: (payload: { title: string; category: string; content: string; source_type: string; owner: string }) =>
    request<KnowledgeDocument>("/knowledge", { method: "POST", auth: true, body: payload }),
  approveKnowledge: (id: UUID) => request<KnowledgeDocument>(`/knowledge/${id}/approve`, { method: "POST", auth: true }),
};
