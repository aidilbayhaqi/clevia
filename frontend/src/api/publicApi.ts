import { request } from "./client";
import type { Appointment, AvailabilitySlot, Clinic, ConversationCreateResponse, PublicMessageResponse, Service, Staff, UUID } from "../types";

export const publicApi = {
  clinic: () => request<Clinic>("/public/clinic"),
  services: () => request<Service[]>("/public/services"),
  staff: () => request<Staff[]>("/public/staff"),
  availability: (serviceId: UUID, date: string, staffId?: UUID) => {
    const params = new URLSearchParams({ service_id: serviceId, date });
    if (staffId) params.set("staff_id", staffId);
    return request<AvailabilitySlot[]>(`/public/availability?${params.toString()}`);
  },
  requestAppointment: (payload: {
    full_name: string;
    phone: string;
    email?: string | null;
    service_id: UUID;
    staff_id: UUID;
    starts_at: string;
    note?: string | null;
  }) => request<Appointment>("/public/appointment-requests", { method: "POST", body: payload }),
  createConversation: () => request<ConversationCreateResponse>("/public/conversations", { method: "POST" }),
  sendMessage: (conversationId: UUID, conversationToken: string, message: string) =>
    request<PublicMessageResponse>(`/public/conversations/${conversationId}/messages`, {
      method: "POST",
      body: { conversation_token: conversationToken, message },
    }),
};
