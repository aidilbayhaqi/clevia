import { useMemo } from "react";
import { Link } from "react-router-dom";
import { crmApi } from "../../api/crmApi";
import { useAsync } from "../../hooks/useAsync";
import { formatDateTime, humanize } from "../../utils/format";
import {
  ErrorState,
  LoadingState,
  PageHeader,
  StatCard,
  StatusBadge,
} from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function DashboardPage() {
  const { data, loading, error } = useAsync(async () => {
    const [leads, clients, appointments, conversations] = await Promise.all([
      crmApi.leads(),
      crmApi.clients(),
      crmApi.appointments(),
      crmApi.conversations(),
    ]);
    return { leads, clients, appointments, conversations };
  }, []);

  const metrics = useMemo(() => {
    if (!data) return null;

    const activeConversations = data.conversations.filter(
      (item) => item.status !== "resolved",
    ).length;

    const requestedAppointments = data.appointments.filter(
      (item) => item.status === "requested",
    ).length;

    const qualifiedLeads = data.leads.filter((item) =>
      ["qualified", "booked", "won"].includes(item.status),
    ).length;

    return { activeConversations, requestedAppointments, qualifiedLeads };
  }, [data]);

  if (loading) return <LoadingState label="Loading clinic overview..." />;
  if (error || !data || !metrics) {
    return <ErrorState message={error || "No dashboard data."} />;
  }

  const pipeline = ["new", "contacted", "qualified", "booked", "won"].map(
    (status) => ({
      status,
      count: data.leads.filter((lead) => lead.status === status).length,
    }),
  );

  const maxPipeline = Math.max(1, ...pipeline.map((item) => item.count));

  const recentLeads = [...data.leads]
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, 5);

  const upcoming = [...data.appointments]
    .filter((item) => !["completed", "cancelled", "no_show"].includes(item.status))
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at))
    .slice(0, 5);

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Today at Clevia"
        title="Good afternoon, Clevia."
        description="Operational snapshot across leads, appointments, and customer conversations."
        actions={
          <Link className="btn btn--gold" to="/admin/conversations">
            Open inbox <Icon name="arrow" />
          </Link>
        }
      />

      <div className="stats-grid stats-grid--responsive">
        <StatCard
          label="Total leads"
          value={data.leads.length}
          hint={`${metrics.qualifiedLeads} qualified or later`}
          icon="leads"
          tone="accent"
        />
        <StatCard
          label="Clients"
          value={data.clients.length}
          hint="Known CRM client records"
          icon="clients"
        />
        <StatCard
          label="Requested appointments"
          value={metrics.requestedAppointments}
          hint="Need staff confirmation"
          icon="calendar"
          tone="warning"
        />
        <StatCard
          label="Active conversations"
          value={metrics.activeConversations}
          hint="AI + human inbox"
          icon="chat"
          tone="good"
        />
      </div>

      <div className="dashboard-grid">
        <section className="panel panel--gold panel--wide">
          <div className="panel__head">
            <div>
              <small>LEAD PIPELINE</small>
              <h2>Conversion movement</h2>
            </div>
            <Link to="/admin/leads">View pipeline</Link>
          </div>

          <div className="pipeline-chart pipeline-chart--gold">
            {pipeline.map((item) => (
              <div key={item.status}>
                <div className="pipeline-chart__bar">
                  <span
                    style={{
                      height: `${Math.max(12, (item.count / maxPipeline) * 100)}%`,
                    }}
                  />
                </div>
                <b>{item.count}</b>
                <small>{humanize(item.status)}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="panel panel--gold">
          <div className="panel__head">
            <div>
              <small>APPOINTMENT PULSE</small>
              <h2>Needs attention</h2>
            </div>
          </div>

          <div className="status-summary">
            {["requested", "confirmed", "checked_in", "completed"].map((status) => (
              <div key={status}>
                <StatusBadge value={status} />
                <b>{data.appointments.filter((item) => item.status === status).length}</b>
              </div>
            ))}
          </div>

          <div className="panel-callout panel-callout--gold">
            <Icon name="calendar" />
            <div>
              <b>{metrics.requestedAppointments} request need confirmation</b>
              <p>Review before they move into the confirmed schedule.</p>
            </div>
          </div>
        </section>
      </div>

      <div className="dashboard-grid dashboard-grid--equal">
        <section className="panel panel--gold">
          <div className="panel__head">
            <div>
              <small>RECENT LEADS</small>
              <h2>Newest opportunities</h2>
            </div>
            <Link to="/admin/leads">All leads</Link>
          </div>

          <div className="mini-list">
            {recentLeads.map((lead) => (
              <Link key={lead.id} to="/admin/leads">
                <span className="mini-avatar">{lead.full_name.slice(0, 1).toUpperCase()}</span>
                <div>
                  <b>{lead.full_name}</b>
                  <small>{lead.interest || lead.phone}</small>
                </div>
                <StatusBadge value={lead.status} />
              </Link>
            ))}
          </div>
        </section>

        <section className="panel panel--gold">
          <div className="panel__head">
            <div>
              <small>UPCOMING</small>
              <h2>Appointment queue</h2>
            </div>
            <Link to="/admin/appointments">All appointments</Link>
          </div>

          <div className="mini-list">
            {upcoming.map((appointment) => (
              <Link key={appointment.id} to="/admin/appointments">
                <span className="mini-date">
                  <b>{new Date(appointment.starts_at).getDate()}</b>
                  <small>
                    {new Intl.DateTimeFormat("en", { month: "short" }).format(
                      new Date(appointment.starts_at),
                    )}
                  </small>
                </span>
                <div>
                  <b>{appointment.client_name}</b>
                  <small>
                    {appointment.service_name} · {formatDateTime(appointment.starts_at)}
                  </small>
                </div>
                <StatusBadge value={appointment.status} />
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
