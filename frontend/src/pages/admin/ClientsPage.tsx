import { useMemo, useState } from "react";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import { formatDate, humanize } from "../../utils/format";
import { ErrorState, LoadingState, PageHeader } from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function ClientsPage() {
  const { data, loading, error } = useAsync(() => crmApi.clients(), []);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    return (data || []).filter((client) => !q || client.full_name.toLowerCase().includes(q) || client.phone.toLowerCase().includes(q) || (client.email || "").toLowerCase().includes(q));
  }, [data, query]);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error || "No client data."} />;

  return (
    <div className="admin-page">
      <PageHeader eyebrow="CRM" title="Client directory" description="A clean operational directory for known clinic clients." />
      <div className="table-toolbar"><label className="search-field search-field--wide"><Icon name="search" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search clients..." /></label><span className="count-pill">{filtered.length} clients</span></div>
      <div className="client-card-grid">
        {filtered.map((client) => (
          <article className="client-card" key={client.id}>
            <div className="client-card__head"><span className="mini-avatar mini-avatar--large">{client.full_name.slice(0, 1).toUpperCase()}</span><div><h3>{client.full_name}</h3><span>Client since {formatDate(client.created_at)}</span></div></div>
            <div className="client-card__details"><div><small>Phone</small><b>{client.phone}</b></div><div><small>Email</small><b>{client.email || "—"}</b></div><div><small>Birthday</small><b>{formatDate(client.birth_date)}</b></div></div>
            <div className="tag-row">{client.tags?.length ? client.tags.map((tag) => <span key={tag}>{humanize(tag)}</span>) : <span>No tags</span>}</div>
          </article>
        ))}
      </div>
    </div>
  );
}
