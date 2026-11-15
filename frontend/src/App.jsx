import { useEffect, useState } from "react";
import Login from "../components/Login";
import UserForm from "../components/UserForm";
import UsersList from "../components/UsersList";
import { createUser, deleteUser, getUsers, login, updateUser } from "../services/api";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setUsers([]);
      return;
    }
    fetchUsers();
  }, [token]);

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

  async function handleLogin(credentials) {
    try {
      setLoading(true);
      setError("");
      const data = await login(credentials.username, credentials.password);
      localStorage.setItem("token", data.token);
      setToken(data.token);
      setMessage(`Station access granted: ${data.user.username}`);
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
    localStorage.removeItem("token");
    setToken("");
    setSelectedUser(null);
    setMessage("Station access revoked");
    setError("");
  }

  const currentUser = localStorage.getItem("username") || "operator";

  return (
    <div className="page-enter">
      {loading && <div className="loading-overlay"><div className="loading-spinner" /></div>}

      {!token ? (
        <div className="login-screen">
          <Login onLogin={handleLogin} loading={loading} />
        </div>
      ) : (
        <main className="container">
          <header className="topbar">
            <h1 className="station-id">CLIMAGURU <span className="accent">STATION</span></h1>
            <div className="topbar-actions">
              <span className="user-badge">{currentUser}</span>
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
      )}
    </div>
  );
}