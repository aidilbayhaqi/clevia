export const API_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000/api/v1";

export const TOKEN_KEY = "clevia_admin_token";
export const CHAT_SESSION_KEY = "clevia_public_chat_session";
export const WHATSAPP_NUMBER = import.meta.env.VITE_WHATSAPP_NUMBER || "622155502026";
