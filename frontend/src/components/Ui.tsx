import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";
import { humanize } from "../utils/format";

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </div>
  );
}

export function StatusBadge({ value }: { value: string }) {
  return <span className={`status-badge status-badge--${value.toLowerCase().replaceAll(" ", "_")}`}><span />{humanize(value)}</span>;
}

export function LoadingState({ label = "Memuat data..." }: { label?: string }) {
  return <div className="state-card"><span className="loader" /><p>{label}</p></div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="state-card state-card--error"><b>Data belum bisa dimuat.</b><p>{message}</p></div>;
}

export function StatCard({ label, value, hint, icon, tone = "neutral" }: {
  label: string;
  value: string | number;
  hint: string;
  icon: IconName;
  tone?: "neutral" | "accent" | "good" | "warning";
}) {
  return (
    <article className={`stat-card stat-card--${tone}`}>
      <div className="stat-card__icon"><Icon name={icon} /></div>
      <div><span>{label}</span><strong>{value}</strong><small>{hint}</small></div>
    </article>
  );
}
