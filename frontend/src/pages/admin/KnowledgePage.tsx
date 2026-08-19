import { useMemo, useState, type FormEvent } from "react";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import { formatDateTime } from "../../utils/format";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function KnowledgePage() {
  const { data, loading, error, setData } = useAsync(() => crmApi.knowledge(), []);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({ title: "", category: "faq", source_type: "operational_faq", owner: "operations", content: "" });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (data || []).filter((item) => !q || item.title.toLowerCase().includes(q) || item.content.toLowerCase().includes(q));
  }, [data, query]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const created = await crmApi.createKnowledge(form);
      setData(data ? [created, ...data] : [created]);
      setForm({ title: "", category: "faq", source_type: "operational_faq", owner: "operations", content: "" });
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  }

  async function approve(id: string) {
    if (!data) return;
    const updated = await crmApi.approveKnowledge(id);
    setData(data.map((item) => item.id === id ? updated : item));
  }

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error || "No knowledge data."} />;

  return (
    <div className="admin-page">
      <PageHeader eyebrow="AI Governance" title="Knowledge base" description="Only approved, current operational knowledge should ground production AI answers." actions={<button className="btn btn--dark" onClick={() => setShowForm((value) => !value)}>{showForm ? "Close form" : "New document"}</button>} />

      {showForm && (
        <form className="panel knowledge-form" onSubmit={submit}>
          <div className="form-grid">
            <label className="field field--full"><span>Title</span><input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
            <label className="field"><span>Category</span><input required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></label>
            <label className="field"><span>Owner</span><input required value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} /></label>
            <label className="field field--full"><span>Content</span><textarea required rows={6} value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} /></label>
          </div>
          <button className="btn btn--dark" disabled={saving}>{saving ? "Saving..." : "Save as draft"}</button>
        </form>
      )}

      <div className="table-toolbar"><label className="search-field search-field--wide"><Icon name="search" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search knowledge..." /></label><span className="count-pill">{data.filter((item) => item.status === "approved").length} approved</span></div>

      <div className="knowledge-grid">
        {filtered.map((document) => (
          <article className="knowledge-card" key={document.id}>
            <div className="knowledge-card__head"><div><span>{document.category}</span><h3>{document.title}</h3></div><StatusBadge value={document.status} /></div>
            <p>{document.content}</p>
            <div className="knowledge-card__meta"><span>Owner: {document.owner}</span><span>{formatDateTime(document.updated_at)}</span></div>
            {document.status === "draft" && <button className="btn btn--soft" onClick={() => void approve(document.id)}>Approve</button>}
          </article>
        ))}
      </div>
    </div>
  );
}
