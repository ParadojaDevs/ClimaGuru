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
      setMessage(`Sesion iniciada como ${data.user.username}`);
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
        setMessage("Usuario actualizado");
      } else {
        await createUser(token, formData);
        setMessage("Usuario creado");
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
    const confirmed = window.confirm("Deseas eliminar este usuario?");
    if (!confirmed) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      await deleteUser(token, id);
      setMessage("Usuario eliminado");
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
    setMessage("Sesion cerrada");
    setError("");
  }

  return (
    <main className="container">
      <header className="topbar">
        <h1>ClimaGuru - Admin de Usuarios</h1>
        {token && (
          <button className="secondary" onClick={logout}>
            Cerrar sesion
          </button>
        )}
      </header>

      {error && <p className="feedback error">{error}</p>}
      {message && <p className="feedback success">{message}</p>}

      {!token ? (
        <Login onLogin={handleLogin} loading={loading} />
      ) : (
        <section className="grid">
          <UserForm
            selectedUser={selectedUser}
            onSubmit={handleSaveUser}
            onCancel={() => setSelectedUser(null)}
            loading={loading}
          />
          <UsersList
            users={users}
            onEdit={setSelectedUser}
            onDelete={handleDeleteUser}
            loading={loading}
          />
        </section>
      )}
    </main>
  );
}
