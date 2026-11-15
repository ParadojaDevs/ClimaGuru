// Dashboard autenticado: CRUD de usuarios (experiencia existente, sin cambios
// funcionales). Protegida: sin token redirige a /login.

import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import UserForm from "../../components/UserForm";
import UsersList from "../../components/UsersList";
import {
  getUsers,
  createUser,
  deleteUser,
  updateUser,
  logout as apiLogout,
  clearTokens,
  getAccessToken,
} from "../../services/api";

export default function Dashboard() {
  const token = getAccessToken();
  const navigate = useNavigate();

  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (token) {
      fetchUsers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  async function fetchUsers() {
    try {
      setLoading(true);
      setError("");
      const list = await getUsers(token);
      setUsers(list);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveUser(formData) {
    try {
      setLoading(true);
      setError("");
      setMessage("");

      if (selectedUser) {
        const payload = { username: formData.username };
        if (formData.password) {
          payload.password = formData.password;
        }
        await updateUser(token, selectedUser.id, payload);
        setMessage("Log entry updated");
      } else {
        await createUser(token, formData);
        setMessage("Log entry created");
      }

      setSelectedUser(null);
      await fetchUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteUser(id) {
    const confirmed = window.confirm("Delete this log entry?");
    if (!confirmed) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      await deleteUser(token, id);
      setMessage("Log entry deleted");
      if (selectedUser?.id === id) {
        setSelectedUser(null);
      }
      await fetchUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    apiLogout();
    clearTokens();
    setSelectedUser(null);
    navigate("/login");
  }

  const currentUser = localStorage.getItem("username") || "operator";

  return (
    <main className="container">
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner" />
        </div>
      )}

      <header className="topbar">
        <h1 className="station-id">
          CLIMAGURU <span className="accent">STATION</span>
        </h1>
        <div className="topbar-actions">
          <span className="user-badge">{currentUser}</span>
          <a className="btn btn-ghost" href="/">
            Mapa público
          </a>
          <button className="btn btn-secondary" onClick={logout}>
            Disconnect
          </button>
        </div>
      </header>

      {error && <p className="feedback feedback-error">{error}</p>}
      {message && <p className="feedback feedback-success">{message}</p>}

      <section className="grid">
        <div className="panel panel-enter-left">
          <div className="panel-header">
            <h2 className="panel-title">Control Panel</h2>
            <span className="panel-label">Station Access</span>
          </div>
          <UserForm
            selectedUser={selectedUser}
            onSubmit={handleSaveUser}
            onCancel={() => setSelectedUser(null)}
            loading={loading}
          />
        </div>
        <div className="panel panel-enter-right">
          <div className="panel-header">
            <h2 className="panel-title">Active Readings</h2>
            <span className="panel-label">{users.length} Entries</span>
          </div>
          <UsersList
            users={users}
            onEdit={setSelectedUser}
            onDelete={handleDeleteUser}
            loading={loading}
          />
        </div>
      </section>
    </main>
  );
}
