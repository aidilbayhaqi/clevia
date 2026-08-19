import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Logo from "./Logo";
import { Icon, type IconName } from "./Icon";

const navigation: Array<[string, string, IconName]> = [
  ["Overview", "/admin", "home"],
  ["Leads", "/admin/leads", "leads"],
  ["Clients", "/admin/clients", "clients"],
  ["Appointments", "/admin/appointments", "calendar"],
  ["Conversations", "/admin/conversations", "chat"],
  ["Knowledge", "/admin/knowledge", "book"],
  ["Settings", "/admin/settings", "settings"],
];

const titles: Record<string, string> = {
  "/admin": "Clinic overview",
  "/admin/leads": "Lead pipeline",
  "/admin/clients": "Client directory",
  "/admin/appointments": "Appointments",
  "/admin/conversations": "Conversations",
  "/admin/knowledge": "AI knowledge",
  "/admin/settings": "Workspace settings",
};

export default function AdminLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function signOut() {
    logout();
    navigate("/admin/login", { replace: true });
  }

  return (
    <div className="admin-shell admin-shell--gold">
      <aside className={`admin-sidebar admin-sidebar--gold ${mobileOpen ? "is-open" : ""}`}>
        <div className="admin-sidebar__brand">
          <Logo compact />
          <button
            className="icon-button mobile-only"
            onClick={() => setMobileOpen(false)}
          >
            <Icon name="close" />
          </button>
        </div>

        <div className="admin-sidebar__label">Operations</div>

        <nav className="admin-nav">
          {navigation.map(([label, href, icon]) => (
            <NavLink
              end={href === "/admin"}
              key={href}
              to={href}
              onClick={() => setMobileOpen(false)}
            >
              <Icon name={icon} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="admin-sidebar__user">
          <div className="avatar">{(user?.full_name || "C").slice(0, 1).toUpperCase()}</div>
          <div>
            <b>{user?.full_name || "Clevia Owner"}</b>
            <small>{user?.role || "owner"}</small>
          </div>
          <button className="icon-button" title="Sign out" onClick={signOut}>
            <Icon name="logout" />
          </button>
        </div>
      </aside>

      <div className="admin-main">
        <header className="admin-topbar admin-topbar--gold">
          <button
            className="icon-button mobile-only"
            onClick={() => setMobileOpen(true)}
          >
            <Icon name="menu" />
          </button>

          <div>
            <span className="admin-topbar__eyebrow">CLEVIA OPERATIONS</span>
            <b>{titles[location.pathname] || "Workspace"}</b>
          </div>

          <div className="admin-topbar__right">
            <span className="system-pill system-pill--gold">
              <span /> API connected
            </span>
            <span>
              {new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date())}
            </span>
          </div>
        </header>

        <main className="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
