import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import Logo from "../../components/Logo";
import { useAuth } from "../../context/AuthContext";
import { Icon } from "../../components/Icon";

type LocationState = { from?: { pathname?: string } };

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("owner@clevia.id");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/admin" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      const state = location.state as LocationState | null;
      navigate(state?.from?.pathname || "/admin", { replace: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Login gagal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-screen__visual">
        <Logo />
        <div>
          <span className="eyebrow eyebrow--light">Clevia Operations</span>
          <h1>A refined workspace for clinic operations.</h1>
          <p>Lead pipeline, appointments, conversations, and AI knowledge—organized in one clear operational view.</p>
        </div>
        <div className="login-screen__signals">
          <span><i /> AI + human handoff</span>
          <span><i /> Tenant-aware CRM</span>
          <span><i /> Appointment controls</span>
        </div>
      </div>

      <div className="login-screen__form-wrap">
        <form className="login-form" onSubmit={submit}>
          <span className="login-form__icon"><Icon name="user" /></span>
          <small>ADMIN PORTAL</small>
          <h2>Welcome back.</h2>
          <p>Sign in with your Clevia operations account.</p>
          {error && <div className="form-error">{error}</div>}
          <label className="field"><span>Email</span><input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label className="field"><span>Password</span><input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button className="btn btn--dark btn--wide btn--large" disabled={loading}>{loading ? "Signing in..." : "Sign in"} <Icon name="arrow" /></button>
          <div className="login-form__hint">Local development account is prefilled. Change credentials before real deployment.</div>
        </form>
      </div>
    </div>
  );
}
