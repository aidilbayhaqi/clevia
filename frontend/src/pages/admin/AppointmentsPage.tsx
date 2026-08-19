import { useMemo, useState } from "react";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import type { AppointmentStatus } from "../../types";
import { formatDateTime, humanize } from "../../utils/format";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "../../components/Ui";
import { Icon } from "../../components/Icon";

const statusOptions: Array<"all" | AppointmentStatus> = ["all", "requested", "confirmed", "checked_in", "completed", "cancelled", "no_show"];

export default function AppointmentsPage() {
  const { data, loading, error, setData } = useAsync(() => crmApi.appointments(), []);
  const [status, setStatus] = useState<"all" | AppointmentStatus>("all");
  const [saving, setSaving] = useState("");

  const filtered = useMemo(() => (data || []).filter((item) => status === "all" || item.status === status), [data, status]);

  async function transition(id: string, next: AppointmentStatus) {
    if (!data) return;
    setSaving(id);
    try {
      const updated = await crmApi.updateAppointment(id, { status: next });
      setData(data.map((item) => item.id === id ? { ...item, ...updated } : item));
    } catch (reason) {
      alert(reason instanceof Error ? reason.message : "Status update failed.");
    } finally {
      setSaving("");
    }
  }

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error || "No appointment data."} />;

  return (
    <div className="admin-page">
      <PageHeader eyebrow="Schedule" title="Appointments" description="Review requests and move appointments only through allowed clinic transitions." />
      <div className="filter-pills filter-pills--admin appointment-tabs">
        {statusOptions.map((item) => <button key={item} className={status === item ? "is-active" : ""} onClick={() => setStatus(item)}>{humanize(item)}{item !== "all" && <span>{data.filter((row) => row.status === item).length}</span>}</button>)}
      </div>
      <div className="appointment-grid">
        {filtered.map((appointment) => (
          <article className="appointment-card" key={appointment.id}>
            <div className="appointment-card__top"><div className="appointment-card__time"><Icon name="calendar" /><div><b>{formatDateTime(appointment.starts_at)}</b><small>{appointment.staff_name}</small></div></div><StatusBadge value={appointment.status} /></div>
            <div className="appointment-card__body"><span>CLIENT</span><h3>{appointment.client_name}</h3><p>{appointment.service_name}</p><small>Source: {humanize(appointment.source)}</small></div>
            <div className="appointment-card__actions">
              {appointment.status === "requested" && <><button disabled={saving === appointment.id} className="btn btn--dark" onClick={() => void transition(appointment.id, "confirmed")}>Confirm</button><button disabled={saving === appointment.id} className="btn btn--soft" onClick={() => void transition(appointment.id, "cancelled")}>Cancel</button></>}
              {appointment.status === "confirmed" && <><button disabled={saving === appointment.id} className="btn btn--dark" onClick={() => void transition(appointment.id, "checked_in")}>Check in</button><button disabled={saving === appointment.id} className="btn btn--soft" onClick={() => void transition(appointment.id, "no_show")}>No show</button></>}
              {appointment.status === "checked_in" && <button disabled={saving === appointment.id} className="btn btn--dark" onClick={() => void transition(appointment.id, "completed")}>Complete</button>}
              {!["requested", "confirmed", "checked_in"].includes(appointment.status) && <span className="appointment-card__closed">No further transitions</span>}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
