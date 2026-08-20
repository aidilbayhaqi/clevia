import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { publicApi } from "../api/publicApi";
import { CHAT_SESSION_KEY } from "../config";
import { Icon } from "./Icon";
import RichMessage from "./RichMessage";

type ChatLine = {
  id: string;
  role: "assistant" | "user";
  content: string;
  intent?: string;
};

type SavedSession = {
  conversationId: string;
  conversationToken: string;
};

const welcome: ChatLine = {
  id: "welcome",
  role: "assistant",
  content:
    "### Halo, aku Clevia AI\nAku bisa bantu kamu mencari informasi klinik dengan lebih rapi.\n\n- Treatment dan estimasi harga\n- Durasi layanan\n- Informasi appointment\n- Profil klinik\n- Arahkan ke staff bila dibutuhkan",
};

function loadSession(): SavedSession | null {
  try {
    const raw = localStorage.getItem(CHAT_SESSION_KEY);
    return raw ? (JSON.parse(raw) as SavedSession) : null;
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
  const endRef = useRef<HTMLDivElement | null>(null);

  const quickPrompts = useMemo(
    () => [
      "Layanan apa saja?",
      "Harga Glow Facial",
      "Berapa lama treatment?",
      "Saya mau booking",
    ],
    [],
  );

  useEffect(() => {
    if (!open) return;
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [lines, busy, open]);

  async function ensureSession(): Promise<SavedSession> {
    if (sessionRef.current) return sessionRef.current;

    const created = await publicApi.createConversation();
    const session = {
      conversationId: created.conversation_id,
      conversationToken: created.conversation_token,
    };

    sessionRef.current = session;
    localStorage.setItem(CHAT_SESSION_KEY, JSON.stringify(session));
    return session;
  }

  async function send(message: string) {
    const clean = message.trim();
    if (!clean || busy) return;

    setLines((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: clean },
    ]);
    setText("");
    setBusy(true);

    try {
      const session = await ensureSession();
      const response = await publicApi.sendMessage(
        session.conversationId,
        session.conversationToken,
        clean,
      );

      setLines((current) => [
        ...current,
        {
          id: response.message_id,
          role: "assistant",
          content: response.message,
          intent: response.intent,
        },
      ]);
    } catch (reason) {
      const messageText =
        reason instanceof Error ? reason.message : "Chat sedang tidak tersedia.";

      setLines((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "### Maaf, chat belum bisa memproses permintaan\n" +
            `${messageText}\n\nSilakan coba lagi atau hubungi staff Clevia bila diperlukan.`,
        },
      ]);

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
        <aside className="chat-panel chat-panel--pro">
          <div className="chat-panel__head">
            <div>
              <span className="ai-dot"><Icon name="sparkle" size={16} /></span>
              <div>
                <b>Clevia AI Concierge</b>
                <small><span className="chat-online-dot" /> Clinic information assistant</small>
              </div>
            </div>
            <button
              className="icon-button"
              aria-label="Close chat"
              onClick={() => setOpen(false)}
            >
              <Icon name="close" />
            </button>
          </div>

          <div className="chat-scope">
            <span>Services</span>
            <span>Pricing</span>
            <span>Appointments</span>
            <span>Clinic info</span>
          </div>

          <div className="chat-panel__messages">
            {lines.map((line) => (
              <div
                key={line.id}
                className={`chat-message-row chat-message-row--${line.role}`}
              >
                {line.role === "assistant" && (
                  <span className="chat-message-avatar">C</span>
                )}

                <div className={`chat-line chat-line--${line.role}`}>
                  {line.role === "assistant" ? (
                    <>
                      <RichMessage content={line.content} compact />
                      {line.intent && line.id !== "welcome" && (
                        <span className="chat-intent">{line.intent.replaceAll("_", " ")}</span>
                      )}
                    </>
                  ) : (
                    <p>{line.content}</p>
                  )}
                </div>
              </div>
            ))}

            {busy && (
              <div className="chat-message-row chat-message-row--assistant">
                <span className="chat-message-avatar">C</span>
                <div className="chat-line chat-line--assistant chat-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}

            <div ref={endRef} />
          </div>

          <div className="chat-panel__quick">
            {quickPrompts.map((prompt) => (
              <button key={prompt} onClick={() => void send(prompt)}>
                {prompt}
              </button>
            ))}
          </div>

          <form className="chat-panel__form" onSubmit={submit}>
            <textarea
              aria-label="Chat message"
              rows={1}
              value={text}
              onChange={(event) => setText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send(text);
                }
              }}
              placeholder="Tanya tentang treatment, harga, atau appointment..."
            />
            <button
              disabled={busy || !text.trim()}
              className="icon-button icon-button--dark"
              aria-label="Send message"
            >
              <Icon name="arrow" />
            </button>
          </form>

          <div className="chat-panel__footer">
            <Icon name="check" size={12} />
            <span>
              AI memberi informasi umum, bukan diagnosis atau keputusan medis personal.
            </span>
          </div>
        </aside>
      )}

      <button
        className="chat-launcher"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="chat-launcher__status" />
        <Icon name={open ? "close" : "chat"} />
        <span>{open ? "Close" : "Ask Clevia AI"}</span>
      </button>
    </>
  );
}
