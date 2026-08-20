import { useMemo, useState } from "react";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import type { LeadStatus } from "../../types";
import { formatDateTime, humanize } from "../../utils/format";
import {
  ErrorState,
  LoadingState,
  PageHeader,
} from "../../components/Ui";
import { Icon } from "../../components/Icon";

const statuses: Array<"all" | LeadStatus> = [
  "all",
  "new",
  "contacted",
  "qualified",
  "booked",
  "won",
  "lost",
];

export default function LeadsPage() {
  const { data, loading, error, setData } = useAsync(() => crmApi.leads(), []);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | LeadStatus>("all");
  const [saving, setSaving] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();

    return (data || []).filter((lead) => {
      const statusMatch = status === "all" || lead.status === status;
      const searchMatch =
        !q ||
        lead.full_name.toLowerCase().includes(q) ||
        lead.phone.toLowerCase().includes(q) ||
        (lead.interest || "").toLowerCase().includes(q);

      return statusMatch && searchMatch;
    });
  }, [data, query, status]);

  async function updateStatus(id: string, nextStatus: LeadStatus) {
    if (!data) return;

    setSaving(id);
    try {
      const updated = await crmApi.updateLead(id, { status: nextStatus });
      setData(
        data.map((lead) =>
          lead.id === id
            ? { ...lead, ...updated, interest: lead.interest }
            : lead,
        ),
      );
    } finally {
      setSaving("");
    }
  }

  if (loading) return <LoadingState />;
  if (error || !data) {
    return <ErrorState message={error || "No lead data."} />;
  }

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="CRM"
        title="Lead pipeline"
        description="Track customer intent, treatment interest, source, and the next operational status."
      />

      <div className="table-toolbar table-toolbar--responsive">
        <label className="search-field search-field--wide">
          <Icon name="search" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search name, phone, treatment..."
          />
        </label>

        <div className="filter-pills filter-pills--admin">
          {statuses.map((item) => (
            <button
              key={item}
              className={status === item ? "is-active" : ""}
              onClick={() => setStatus(item)}
            >
              {humanize(item)}
            </button>
          ))}
        </div>
      </div>

      <div className="data-table-wrap data-table-wrap--responsive">
        <table className="data-table data-table--responsive">
          <thead>
            <tr>
              <th>Lead</th>
              <th>Interest</th>
              <th>Source</th>
              <th>Status</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((lead) => (
              <tr key={lead.id}>
                <td data-label="Lead">
                  <div className="person-cell">
                    <span className="mini-avatar">
                      {lead.full_name.slice(0, 1).toUpperCase()}
                    </span>
                    <div>
                      <b>{lead.full_name}</b>
                      <small>
                        {lead.phone}
                        {lead.email ? ` · ${lead.email}` : ""}
                      </small>
                    </div>
                  </div>
                </td>
                <td data-label="Interest">{lead.interest || "—"}</td>
                <td data-label="Source">
                  <span className="soft-label">{humanize(lead.source)}</span>
                </td>
                <td data-label="Status">
                  <select
                    className="status-select"
                    disabled={saving === lead.id}
                    value={lead.status}
                    onChange={(event) =>
                      void updateStatus(lead.id, event.target.value as LeadStatus)
                    }
                  >
                    {statuses
                      .filter((item): item is LeadStatus => item !== "all")
                      .map((item) => (
                        <option key={item} value={item}>
                          {humanize(item)}
                        </option>
                      ))}
                  </select>
                </td>
                <td data-label="Updated">{formatDateTime(lead.updated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {!filtered.length && (
          <div className="admin-empty-state">
            <Icon name="leads" />
            <b>No matching leads.</b>
            <span>Try another search or pipeline status.</span>
          </div>
        )}
      </div>

      <div className="table-footer">
        <span>{filtered.length} of {data.length} leads</span>
      </div>
    </div>
  );
}
