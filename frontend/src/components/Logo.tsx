import { Link } from "react-router-dom";

export default function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link className={`brand ${compact ? "brand--compact" : ""}`} to="/">
      <span className="brand__mark">C</span>
      <span className="brand__text">
        <b>CLEVIA</b>
        {!compact && <small>BEAUTY CLINIC</small>}
      </span>
    </Link>
  );
}
