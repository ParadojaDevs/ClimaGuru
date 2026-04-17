import { useEffect, useState } from "react";

const EMPTY_FORM = { username: "", password: "" };

export default function UserForm({ selectedUser, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState(EMPTY_FORM);

  useEffect(() => {
    if (selectedUser) {
      setForm({ username: selectedUser.username, password: "" });
      return;
    }
    setForm(EMPTY_FORM);
  }, [selectedUser]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h3>{selectedUser ? "Editar usuario" : "Crear usuario"}</h3>
      <label>
        Usuario
        <input
          name="username"
          value={form.username}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Password {selectedUser ? "(opcional)" : ""}
        <input
          type="password"
          name="password"
          value={form.password}
          onChange={handleChange}
          required={!selectedUser}
        />
      </label>
      <div className="actions">
        <button type="submit" disabled={loading}>
          {loading ? "Guardando..." : selectedUser ? "Actualizar" : "Crear"}
        </button>
        {selectedUser && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
