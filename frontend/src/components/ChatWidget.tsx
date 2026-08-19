import { useMemo, useRef, useState, type FormEvent } from "react";
import { publicApi } from "../api/publicApi";
import { CHAT_SESSION_KEY } from "../config";
import { Icon } from "./Icon";

type ChatLine = { id: string; role: "assistant" | "user"; content: string };
type SavedSession = { conversationId: string; conversationToken: string };

const welcome: ChatLine = {
  id: "welcome",
  role: "assistant",
  content: "Hi, aku Clevia AI. Aku bisa bantu cek treatment, harga, jadwal, kebijakan appointment, atau mengarahkan ke tim klinik.",
};

function loadSession(): SavedSession | null {
  try {
    const raw = localStorage.getItem(CHAT_SESSION_KEY);
    return raw ? JSON.parse(raw) as SavedSession : null;
  } catch {
    return null;
  }
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [lines, setLines] = useState<ChatLine[]>([welcome]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const sessionRef = useRef<SavedSession | null>(loadSession());
  const quickPrompts = useMemo(() => ["Layanan apa saja?", "Harga Glow Facial", "Mau booking"], []);

  async function ensureSession(): Promise<SavedSession> {
    if (sessionRef.current) return sessionRef.current;
    const created = await publicApi.createConversation();
    const session = { conversationId: created.conversation_id, conversationToken: created.conversation_token };
    sessionRef.current = session;
    localStorage.setItem(CHAT_SESSION_KEY, JSON.stringify(session));
    return session;
  }

  async function send(message: string) {
    const clean = message.trim();
    if (!clean || busy) return;
    setLines((current) => [...current, { id: crypto.randomUUID(), role: "user", content: clean }]);
    setText("");
    setBusy(true);
    try {
      const session = await ensureSession();
      const response = await publicApi.sendMessage(session.conversationId, session.conversationToken, clean);
      setLines((current) => [...current, { id: response.message_id, role: "assistant", content: response.message }]);
    } catch (reason) {
      const messageText = reason instanceof Error ? reason.message : "Chat sedang tidak tersedia.";
      setLines((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: `Maaf, ${messageText}` }]);
      if (messageText.toLowerCase().includes("conversation")) {
        localStorage.removeItem(CHAT_SESSION_KEY);
        sessionRef.current = null;
      }
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void send(text);
  }

  return (
    <>
      {open && (
        <aside className="chat-panel">
          <div className="chat-panel__head">
            <div><span className="ai-dot" /><div><b>Clevia AI</b><small>Clinic information assistant</small></div></div>
            <button className="icon-button" onClick={() => setOpen(false)}><Icon name="close" /></button>
          </div>
          <div className="chat-panel__messages">
            {lines.map((line) => <div key={line.id} className={`chat-line chat-line--${line.role}`}>{line.content}</div>)}
            {busy && <div className="chat-line chat-line--assistant chat-typing"><span /><span /><span /></div>}
          </div>
          <div className="chat-panel__quick">
            {quickPrompts.map((prompt) => <button key={prompt} onClick={() => void send(prompt)}>{prompt}</button>)}
          </div>
          <form className="chat-panel__form" onSubmit={submit}>
            <input aria-label="Chat message" value={text} onChange={(event) => setText(event.target.value)} placeholder="Tanya tentang Clevia..." />
            <button disabled={busy || !text.trim()} className="icon-button icon-button--dark"><Icon name="arrow" /></button>
          </form>
          <small className="chat-panel__notice">AI tidak memberikan diagnosis. Informasi personal dapat diarahkan ke tim klinik.</small>
        </aside>
      )}
      <button className="chat-launcher" onClick={() => setOpen((value) => !value)}>
        <span className="chat-launcher__status" /><Icon name={open ? "close" : "chat"} /><span>{open ? "Close" : "Ask Clevia AI"}</span>
      </button>
    </>
  );
}
