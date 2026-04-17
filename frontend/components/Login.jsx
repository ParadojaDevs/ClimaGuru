import { useState } from "react";

export default function Login({ onLogin, loading }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");

  function handleSubmit(event) {
    event.preventDefault();
    onLogin({ username, password });
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>Iniciar sesion</h2>
      <label>
        Usuario
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="usuario"
          required
        />
      </label>
      <label>
        Password
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="password"
          required
        />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? "Ingresando..." : "Entrar"}
      </button>
    </form>
  );
}
