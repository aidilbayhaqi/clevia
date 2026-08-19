import { crmApi } from "../../api/crmApi";
import { publicApi } from "../../api/publicApi";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../context/AuthContext";
import { ErrorState, LoadingState, PageHeader } from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function SettingsPage() {
  const { user } = useAuth();
  const { data, loading, error } = useAsync(async () => {
    const [clinic, me] = await Promise.all([publicApi.clinic(), crmApi.me()]);
    return { clinic, me };
  }, []);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error || "No settings data."} />;

  return (
    <div className="admin-page">
      <PageHeader eyebrow="Workspace" title="Settings" description="Read-only operational configuration for this frontend iteration." />
      <div className="settings-grid">
        <section className="panel">
          <div className="settings-section-title"><Icon name="sparkle" /><div><b>Clinic profile</b><span>Public-facing business identity</span></div></div>
          <dl className="settings-list">
            <div><dt>Name</dt><dd>{data.clinic.name}</dd></div><div><dt>Timezone</dt><dd>{data.clinic.timezone}</dd></div><div><dt>Phone</dt><dd>{data.clinic.phone || "—"}</dd></div><div><dt>Email</dt><dd>{data.clinic.email || "—"}</dd></div><div><dt>Instagram</dt><dd>{data.clinic.instagram || "—"}</dd></div><div><dt>Address</dt><dd>{data.clinic.address || "—"}</dd></div>
          </dl>
        </section>
        <section className="panel">
          <div className="settings-section-title"><Icon name="user" /><div><b>Signed-in user</b><span>Current operations session</span></div></div>
          <dl className="settings-list">
            <div><dt>Name</dt><dd>{data.me.full_name}</dd></div><div><dt>Email</dt><dd>{data.me.email}</dd></div><div><dt>Role</dt><dd>{data.me.role}</dd></div><div><dt>Session</dt><dd><span className="system-pill"><span /> authenticated</span></dd></div>
          </dl>
        </section>
        <section className="panel panel--full">
          <div className="settings-section-title"><Icon name="settings" /><div><b>Frontend runtime</b><span>Migration baseline</span></div></div>
          <div className="runtime-grid">
            <div><small>Frontend</small><b>2.1.0</b><span>React + TypeScript</span></div>
            <div><small>Architecture</small><b>Typed API layer</b><span>Public + CRM clients</span></div>
            <div><small>Design</small><b>Unified system</b><span>Public + admin tokens</span></div>
            <div><small>Backend user</small><b>{user?.role || "—"}</b><span>Role-aware session</span></div>
          </div>
        </section>
      </div>
    </div>
  );
}
