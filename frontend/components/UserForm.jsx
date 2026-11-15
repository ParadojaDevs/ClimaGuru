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
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="username">
          Callsign
          {selectedUser && <span className="optional">[EDIT]</span>}
        </label>
        <input
          id="username"
          name="username"
          type="text"
          className="form-input"
          value={form.username}
          onChange={handleChange}
          required
          disabled={loading}
          autoComplete="username"
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="password">
          Access Code
          {selectedUser ? <span className="optional">(optional)</span> : null}
        </label>
        <input
          id="password"
          name="password"
          type="password"
          className="form-input"
          value={form.password}
          onChange={handleChange}
          required={!selectedUser}
          disabled={loading}
          autoComplete={selectedUser ? "new-password" : "current-password"}
          placeholder={selectedUser ? "Leave blank to keep current" : "Set access code"}
        />
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Transmitting..." : selectedUser ? "Update Entry" : "Create Entry"}
        </button>
        {selectedUser && (
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
            Abort
          </button>
        )}
      </div>
    </form>
  );
}