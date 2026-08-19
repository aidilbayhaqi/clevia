import { useEffect, useMemo, useState, type FormEvent } from "react";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import type { Message } from "../../types";
import { formatDateTime } from "../../utils/format";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function ConversationsPage() {
  const { data, loading, error, setData } = useAsync(() => crmApi.conversations(), []);
  const [selectedId, setSelectedId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageLoading, setMessageLoading] = useState(false);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  const selected = useMemo(() => (data || []).find((item) => item.id === selectedId) || null, [data, selectedId]);

  useEffect(() => {
    if (!selectedId && data?.[0]) setSelectedId(data[0].id);
  }, [data, selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    setMessageLoading(true);
    crmApi.transcript(selectedId).then(setMessages).finally(() => setMessageLoading(false));
  }, [selectedId]);

  async function action(kind: "takeover" | "release" | "resolve") {
    if (!selected || !data) return;
    setBusy(true);
    try {
      await crmApi[kind](selected.id);
      setData(await crmApi.conversations());
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selected || !reply.trim()) return;
    setBusy(true);
    try {
      const created = await crmApi.reply(selected.id, reply.trim());
      setMessages((current) => [...current, created]);
      setReply("");
    } catch (reason) {
      alert(reason instanceof Error ? reason.message : "Reply failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error || "No conversation data."} />;

  return (
    <div className="admin-page">
      <PageHeader eyebrow="Inbox" title="Conversations" description="See AI context, take over when necessary, and return control safely." />
      <div className="inbox-shell">
        <aside className="inbox-list">
          <div className="inbox-list__head"><b>Inbox</b><span>{data.filter((item) => item.status !== "resolved").length} active</span></div>
          {data.map((conversation) => (
            <button key={conversation.id} className={selectedId === conversation.id ? "is-active" : ""} onClick={() => setSelectedId(conversation.id)}>
              <div><span className="mini-avatar">{conversation.visitor_name?.slice(0, 1) || "V"}</span><div><b>{conversation.visitor_name}</b><small>{conversation.last_message}</small></div></div>
              <span>{formatDateTime(conversation.updated_at)}</span>
            </button>
          ))}
        </aside>

        <section className="inbox-thread">
          {selected ? (
            <>
              <div className="inbox-thread__head">
                <div><h2>{selected.visitor_name}</h2><div><StatusBadge value={selected.status} /><span>State: {selected.agent_state}</span></div></div>
                <div className="thread-actions">
                  {selected.status === "ai_active" && <button disabled={busy} className="btn btn--dark" onClick={() => void action("takeover")}>Take over</button>}
                  {selected.status === "human_active" && <button disabled={busy} className="btn btn--soft" onClick={() => void action("release")}>Release to AI</button>}
                  {selected.status !== "resolved" && <button disabled={busy} className="btn btn--ghost" onClick={() => void action("resolve")}>Resolve</button>}
                </div>
              </div>

              <div className="inbox-thread__messages">
                {messageLoading ? <LoadingState label="Loading transcript..." /> : messages.map((message) => (
                  <div key={message.id} className={`thread-message thread-message--${message.sender_type}`}>
                    <div><span>{message.sender_type === "visitor" ? selected.visitor_name : message.sender_type === "staff" ? "Clevia Staff" : "Clevia AI"}</span><small>{formatDateTime(message.created_at)}</small></div>
                    <p>{message.content}</p>
                    {message.trace_id && <code>{message.trace_id.slice(0, 12)}</code>}
                  </div>
                ))}
              </div>

              <form className="thread-composer" onSubmit={submit}>
                <textarea rows={2} disabled={selected.status !== "human_active"} placeholder={selected.status === "human_active" ? "Reply as clinic staff..." : "Take over the conversation before replying."} value={reply} onChange={(e) => setReply(e.target.value)} />
                <button className="btn btn--dark" disabled={busy || selected.status !== "human_active" || !reply.trim()}>Send <Icon name="arrow" /></button>
              </form>
            </>
          ) : <div className="state-card"><b>Select a conversation.</b></div>}
        </section>
      </div>
    </div>
  );
}
