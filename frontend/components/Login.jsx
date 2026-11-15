import { useState } from "react";

export default function Login({ onLogin, loading }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");

  function handleSubmit(event) {
    event.preventDefault();
    onLogin({ username, password });
  }

  return (
    <form className="panel login-panel login-form" onSubmit={handleSubmit}>
      <div className="login-header">
        <h1 className="login-station-id">CLIMAGURU <span className="accent">STATION</span></h1>
        <p className="login-subtitle">Station Access Protocol</p>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="username">Callsign</label>
        <input
          id="username"
          type="text"
          className="form-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter callsign"
          required
          autoComplete="username"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="password">Access Code</label>
        <input
          id="password"
          type="password"
          className="form-input"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter access code"
          required
          autoComplete="current-password"
          disabled={loading}
        />
      </div>

      <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={loading}>
        {loading ? "Authenticating..." : "Establish Link"}
      </button>
    </form>
  );
}