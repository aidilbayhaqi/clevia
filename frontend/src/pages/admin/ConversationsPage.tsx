import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import type { Conversation, Message } from "../../types";
import { formatDateTime, humanize } from "../../utils/format";
import {
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from "../../components/Ui";
import { Icon } from "../../components/Icon";
import RichMessage from "../../components/RichMessage";

type Filter = "all" | "ai_active" | "human_active" | "resolved";
type OwnershipAction = "takeover" | "release" | "resolve";

export default function ConversationsPage() {
  const { data, loading, error, setData } = useAsync(
    () => crmApi.conversations(),
    [],
  );

  const [selectedId, setSelectedId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageLoading, setMessageLoading] = useState(false);
  const [messageError, setMessageError] = useState("");
  const [reply, setReply] = useState("");
  const [busyAction, setBusyAction] = useState<OwnershipAction | "reply" | "">("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [focusComposerAfterTakeover, setFocusComposerAfterTakeover] = useState(false);

  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const previousSelectedRef = useRef("");

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();

    return (data || []).filter((conversation) => {
      const statusMatch = filter === "all" || conversation.status === filter;
      const searchMatch =
        !needle ||
        (conversation.visitor_name || "").toLowerCase().includes(needle) ||
        (conversation.last_message || "").toLowerCase().includes(needle) ||
        conversation.id.toLowerCase().includes(needle);

      return statusMatch && searchMatch;
    });
  }, [data, filter, query]);

  const selected = useMemo(
    () => (data || []).find((item) => item.id === selectedId) || null,
    [data, selectedId],
  );

  const isAdminHandling = selected?.status === "human_active";
  const isAiHandling = selected?.status === "ai_active";
  const isResolved = selected?.status === "resolved";
  const isBusy = Boolean(busyAction);

  useEffect(() => {
    if (!selectedId && filtered[0]) setSelectedId(filtered[0].id);
  }, [filtered, selectedId]);

  useEffect(() => {
    if (!selectedId) return;

    let active = true;
    setMessageLoading(true);
    setMessageError("");

    crmApi
      .transcript(selectedId)
      .then((result) => {
        if (active) setMessages(result);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setMessages([]);
        setMessageError(
          reason instanceof Error ? reason.message : "Transcript gagal dimuat.",
        );
      })
      .finally(() => {
        if (active) setMessageLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedId]);

  // When switching conversations, land on the newest message.
  useEffect(() => {
    if (!selectedId || messageLoading) return;

    if (previousSelectedRef.current !== selectedId) {
      previousSelectedRef.current = selectedId;
      requestAnimationFrame(() => scrollTranscriptToBottom(false));
    }
  }, [messageLoading, selectedId]);

  // Keep the newest reply visible without making the whole page scroll.
  useEffect(() => {
    if (!messages.length || messageLoading) return;
    requestAnimationFrame(() => scrollTranscriptToBottom(true));
  }, [messages.length, messageLoading]);

  // A successful takeover immediately brings the admin to the reply field.
  useEffect(() => {
    if (!focusComposerAfterTakeover || !isAdminHandling) return;

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      scrollTranscriptToBottom(true);
      setFocusComposerAfterTakeover(false);
    });
  }, [focusComposerAfterTakeover, isAdminHandling]);

  function scrollTranscriptToBottom(smooth: boolean) {
    const element = transcriptRef.current;
    if (!element) return;

    element.scrollTo({
      top: element.scrollHeight,
      behavior: smooth ? "smooth" : "auto",
    });
  }

  async function refreshConversations() {
    const refreshed = await crmApi.conversations();
    setData(refreshed);
    return refreshed;
  }

  async function action(kind: OwnershipAction) {
    if (!selected || isBusy) return;

    setBusyAction(kind);

    try {
      await crmApi[kind](selected.id);
      await refreshConversations();

      if (kind === "takeover") {
        setFocusComposerAfterTakeover(true);
      }

      if (kind === "release") {
        setReply("");
      }
    } catch (reason) {
      alert(
        reason instanceof Error
          ? reason.message
          : "Conversation action failed.",
      );
    } finally {
      setBusyAction("");
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();

    if (!selected || !reply.trim() || !isAdminHandling || isBusy) return;

    setBusyAction("reply");

    try {
      const created = await crmApi.reply(selected.id, reply.trim());
      setMessages((current) => [...current, created]);
      setReply("");
      await refreshConversations();

      requestAnimationFrame(() => {
        textareaRef.current?.focus();
        scrollTranscriptToBottom(true);
      });
    } catch (reason) {
      alert(reason instanceof Error ? reason.message : "Reply failed.");
    } finally {
      setBusyAction("");
    }
  }

  function selectConversation(conversation: Conversation) {
    setSelectedId(conversation.id);
    setReply("");
  }

  if (loading) {
    return <LoadingState label="Loading conversation workspace..." />;
  }

  if (error || !data) {
    return <ErrorState message={error || "No conversation data."} />;
  }

  const activeCount = data.filter((item) => item.status !== "resolved").length;
  const humanCount = data.filter((item) => item.status === "human_active").length;

  return (
    <div className="admin-page admin-page--conversation">
      <PageHeader
        eyebrow="Customer inbox"
        title="Conversations"
        description="AI handles routine chat until staff takes ownership. The reply composer stays anchored at the bottom."
        actions={
          <div className="conversation-summary-pills">
            <span><i /> {activeCount} active</span>
            <span>{humanCount} admin-owned</span>
          </div>
        }
      />

      <div className={`conversation-workspace ${selected ? "has-selection" : ""}`}>
        <aside className="conversation-list-pane">
          <div className="conversation-list-pane__toolbar">
            <label className="conversation-search">
              <Icon name="search" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search conversation..."
              />
            </label>

            <div className="conversation-filters">
              {(["all", "ai_active", "human_active", "resolved"] as Filter[]).map(
                (item) => (
                  <button
                    key={item}
                    className={filter === item ? "is-active" : ""}
                    onClick={() => setFilter(item)}
                  >
                    {item === "all" ? "All" : humanize(item)}
                  </button>
                ),
              )}
            </div>
          </div>

          <div className="conversation-list-pane__meta">
            <b>{filtered.length} conversations</b>
            <span>sorted by recent activity</span>
          </div>

          <div className="conversation-list">
            {filtered.map((conversation) => (
              <button
                key={conversation.id}
                className={selectedId === conversation.id ? "is-active" : ""}
                onClick={() => selectConversation(conversation)}
              >
                <div className="conversation-list__top">
                  <span className="mini-avatar">
                    {conversation.visitor_name?.slice(0, 1).toUpperCase() || "V"}
                  </span>

                  <div>
                    <b>{conversation.visitor_name || "Website visitor"}</b>
                    <small>{humanize(conversation.channel)}</small>
                  </div>

                  <time>{formatDateTime(conversation.updated_at)}</time>
                </div>

                <p>{conversation.last_message || "Open conversation"}</p>

                <div className="conversation-list__footer">
                  <StatusBadge value={conversation.status} />
                  <span>{humanize(conversation.agent_state)}</span>
                </div>
              </button>
            ))}

            {!filtered.length && (
              <div className="conversation-empty">
                <Icon name="chat" />
                <b>No conversations found.</b>
                <span>Try another search or status filter.</span>
              </div>
            )}
          </div>
        </aside>

        <section className="conversation-thread-pane">
          {selected ? (
            <>
              <div className="conversation-thread-pane__head">
                <button
                  className="conversation-mobile-back"
                  onClick={() => setSelectedId("")}
                >
                  ← Inbox
                </button>

                <div className="conversation-person">
                  <span className="mini-avatar mini-avatar--large">
                    {selected.visitor_name?.slice(0, 1).toUpperCase() || "V"}
                  </span>

                  <div>
                    <h2>{selected.visitor_name || "Website visitor"}</h2>
                    <span>
                      {humanize(selected.channel)} · updated{" "}
                      {formatDateTime(selected.updated_at)}
                    </span>
                  </div>
                </div>

                <div
                  className={`conversation-owner-control ${
                    isAdminHandling
                      ? "is-admin"
                      : isResolved
                        ? "is-resolved"
                        : "is-ai"
                  }`}
                >
                  <div className="conversation-owner-control__state">
                    <span className="conversation-owner-control__dot" />
                    <div>
                      <small>CHAT OWNER</small>
                      <b>
                        {isAdminHandling
                          ? "Admin handling"
                          : isResolved
                            ? "Conversation closed"
                            : "Clevia AI handling"}
                      </b>
                    </div>
                  </div>

                  {isAiHandling && (
                    <button
                      disabled={isBusy}
                      className="btn btn--gold"
                      onClick={() => void action("takeover")}
                    >
                      {busyAction === "takeover" ? "Taking over..." : "Take over"}
                    </button>
                  )}

                  {isAdminHandling && (
                    <button
                      disabled={isBusy}
                      className="btn btn--light-gold"
                      onClick={() => void action("release")}
                    >
                      {busyAction === "release" ? "Releasing..." : "Return to AI"}
                    </button>
                  )}
                </div>

                {!isResolved && (
                  <button
                    disabled={isBusy}
                    className="conversation-resolve-button"
                    onClick={() => void action("resolve")}
                  >
                    <Icon name="check" size={14} />
                    {busyAction === "resolve" ? "Resolving..." : "Resolve"}
                  </button>
                )}
              </div>

              <div className="conversation-state-bar">
                <StatusBadge value={selected.status} />
                <span>
                  Agent state: <b>{humanize(selected.agent_state)}</b>
                </span>
                <span>
                  Risk: <b>{humanize(selected.risk_level)}</b>
                </span>
                {selected.handoff_reason && (
                  <span>
                    Handoff: <b>{humanize(selected.handoff_reason)}</b>
                  </span>
                )}
              </div>

              <div className="conversation-transcript" ref={transcriptRef}>
                {messageLoading && (
                  <LoadingState label="Loading transcript..." />
                )}

                {messageError && <ErrorState message={messageError} />}

                {!messageLoading &&
                  !messageError &&
                  messages.map((message) => {
                    const isVisitor = message.sender_type === "visitor";
                    const isStaff = message.sender_type === "staff";
                    const author = isVisitor
                      ? selected.visitor_name || "Visitor"
                      : isStaff
                        ? "Clevia Staff"
                        : "Clevia AI";

                    return (
                      <article
                        key={message.id}
                        className={`transcript-message transcript-message--${message.sender_type}`}
                      >
                        <div className="transcript-message__meta">
                          <span className="transcript-author">
                            {!isVisitor && (
                              <i className={isStaff ? "is-staff" : "is-ai"}>
                                {isStaff ? "S" : "C"}
                              </i>
                            )}
                            <b>{author}</b>
                          </span>

                          <time>{formatDateTime(message.created_at)}</time>
                        </div>

                        <div className="transcript-message__bubble">
                          {isVisitor ? (
                            <p>{message.content}</p>
                          ) : (
                            <RichMessage content={message.content} />
                          )}
                        </div>

                        {message.trace_id && (
                          <span className="trace-chip">
                            trace {message.trace_id.slice(0, 12)}
                          </span>
                        )}
                      </article>
                    );
                  })}

                {!messageLoading && !messageError && !messages.length && (
                  <div className="conversation-empty conversation-empty--thread">
                    <Icon name="chat" />
                    <b>No transcript yet.</b>
                  </div>
                )}
              </div>

              <div className="conversation-composer-shell">
                {isAdminHandling && (
                  <form className="conversation-composer conversation-composer--active" onSubmit={submit}>
                    <div className="conversation-composer__field">
                      <div className="conversation-composer__identity">
                        <span className="admin-live-dot" />
                        <b>Replying as Clevia Staff</b>
                        <small>AI is paused for this conversation.</small>
                      </div>

                      <textarea
                        ref={textareaRef}
                        rows={2}
                        placeholder="Write a reply to the customer..."
                        value={reply}
                        onChange={(event) => setReply(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" && !event.shiftKey) {
                            event.preventDefault();

                            if (reply.trim() && !isBusy) {
                              event.currentTarget.form?.requestSubmit();
                            }
                          }
                        }}
                      />

                      <small className="conversation-composer__hint">
                        Enter to send · Shift+Enter for a new line
                      </small>
                    </div>

                    <button
                      className="btn btn--gold conversation-send-button"
                      disabled={isBusy || !reply.trim()}
                    >
                      {busyAction === "reply" ? "Sending..." : "Send"}
                      <Icon name="arrow" />
                    </button>
                  </form>
                )}

                {isAiHandling && (
                  <div className="conversation-handoff-cta">
                    <div className="conversation-handoff-cta__icon">
                      <Icon name="sparkle" />
                    </div>

                    <div className="conversation-handoff-cta__copy">
                      <small>AI IS CURRENTLY HANDLING THIS CHAT</small>
                      <b>Need to reply personally?</b>
                      <p>
                        Take over once. The composer will unlock immediately and
                        Clevia AI will stop replying until you return control.
                      </p>
                    </div>

                    <button
                      disabled={isBusy}
                      className="btn btn--gold"
                      onClick={() => void action("takeover")}
                    >
                      {busyAction === "takeover"
                        ? "Taking over..."
                        : "Take over & reply"}
                      <Icon name="arrow" />
                    </button>
                  </div>
                )}

                {isResolved && (
                  <div className="conversation-closed-composer">
                    <span><Icon name="check" /></span>
                    <div>
                      <b>Conversation resolved</b>
                      <small>This thread is closed and cannot receive a staff reply.</small>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="conversation-select-empty">
              <span><Icon name="chat" size={24} /></span>
              <h2>Select a conversation</h2>
              <p>Choose a customer from the inbox to review the transcript.</p>
            </div>
          )}
        </section>

        <aside className="conversation-context-pane">
          {selected ? (
            <>
              <div className="context-card context-card--identity">
                <span className="context-card__label">
                  CONVERSATION CONTEXT
                </span>
                <h3>{selected.visitor_name || "Website visitor"}</h3>
                <p>{selected.last_message || "No summary available."}</p>
              </div>

              <div className="context-card">
                <span className="context-card__label">STATE</span>
                <dl>
                  <div>
                    <dt>Owner</dt>
                    <dd>
                      {isAdminHandling
                        ? "Admin"
                        : isResolved
                          ? "Closed"
                          : "Clevia AI"}
                    </dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd><StatusBadge value={selected.status} /></dd>
                  </div>
                  <div>
                    <dt>Agent state</dt>
                    <dd>{humanize(selected.agent_state)}</dd>
                  </div>
                  <div>
                    <dt>Channel</dt>
                    <dd>{humanize(selected.channel)}</dd>
                  </div>
                  <div>
                    <dt>Risk level</dt>
                    <dd>{humanize(selected.risk_level)}</dd>
                  </div>
                </dl>
              </div>

              {(selected.handoff_summary || selected.handoff_reason) && (
                <div className="context-card context-card--handoff">
                  <span className="context-card__label">HANDOFF</span>
                  {selected.handoff_reason && (
                    <b>{humanize(selected.handoff_reason)}</b>
                  )}
                  {selected.handoff_summary && (
                    <p>{selected.handoff_summary}</p>
                  )}
                </div>
              )}

              <div className="context-card">
                <span className="context-card__label">LINKED RECORDS</span>
                <dl>
                  <div>
                    <dt>Lead</dt>
                    <dd>
                      {selected.lead_id
                        ? selected.lead_id.slice(0, 8)
                        : "Not linked"}
                    </dd>
                  </div>
                  <div>
                    <dt>Client</dt>
                    <dd>
                      {selected.client_id
                        ? selected.client_id.slice(0, 8)
                        : "Not linked"}
                    </dd>
                  </div>
                  <div>
                    <dt>Assigned user</dt>
                    <dd>
                      {selected.assigned_user_id
                        ? selected.assigned_user_id.slice(0, 8)
                        : "AI / unassigned"}
                    </dd>
                  </div>
                </dl>
              </div>

              <div className="context-card context-card--timeline">
                <span className="context-card__label">TIMELINE</span>

                <div>
                  <i />
                  <span>
                    <b>Created</b>
                    {formatDateTime(selected.created_at)}
                  </span>
                </div>

                {selected.handoff_at && (
                  <div>
                    <i />
                    <span>
                      <b>Handoff</b>
                      {formatDateTime(selected.handoff_at)}
                    </span>
                  </div>
                )}

                {selected.resolved_at && (
                  <div>
                    <i />
                    <span>
                      <b>Resolved</b>
                      {formatDateTime(selected.resolved_at)}
                    </span>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="context-card">
              <p>Conversation details will appear here.</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
