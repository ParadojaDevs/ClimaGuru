export default function UsersList({ users, onEdit, onDelete, loading }) {
  return (
    <section className="panel">
      <h3>Usuarios</h3>
      {users.length === 0 ? (
        <p>No hay usuarios registrados.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Creado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{new Date(user.created_at).toLocaleString()}</td>
                <td className="actions">
                  <button onClick={() => onEdit(user)} disabled={loading}>
                    Editar
                  </button>
                  <button
                    className="danger"
                    onClick={() => onDelete(user.id)}
                    disabled={loading}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
