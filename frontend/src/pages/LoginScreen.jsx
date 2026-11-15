// Pantalla de login: envuelve el formulario existente y navega al dashboard
// tras autenticar.

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Login from "../../components/Login";
import { login } from "../../services/api";

export default function LoginScreen() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(credentials) {
    try {
      setLoading(true);
      setError("");
      const data = await login(credentials.username, credentials.password);
      localStorage.setItem("username", data.user?.username || "operator");
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen page-enter">
      <div className="login-wrap">
        <Login onLogin={handleLogin} loading={loading} />
        {error && <p className="feedback feedback-error login-error">{error}</p>}
        <nav className="login-backnav">
          <Link className="btn btn-ghost" to="/">
            ← Volver al mapa público
          </Link>
        </nav>
      </div>
    </div>
  );
}
