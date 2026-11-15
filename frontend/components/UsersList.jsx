export default function UsersList({ users, onEdit, onDelete, loading }) {
  return (
    <div className="table-wrapper">
      {users.length === 0 ? (
        <div className="empty-state">
          <div className="icon">□</div>
          <p>No active readings</p>
          <p style={{ fontSize: "var(--scale-small)", marginTop: "var(--spacing-xs)", color: "var(--pressure-line)" }}>
            Create first log entry via Control Panel
          </p>
        </div>
      ) : (
        <table className="readings-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Callsign</th>
              <th>Logged</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td className="data-value">{user.id}</td>
                <td>{user.username}</td>
                <td className="data-value">{new Date(user.created_at).toLocaleString()}</td>
                <td className="actions-cell">
                  <button
                    className="btn btn-ghost"
                    onClick={() => onEdit(user)}
                    disabled={loading}
                    style={{ padding: "var(--spacing-xs) var(--spacing-sm)", fontSize: "var(--scale-small)" }}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={() => onDelete(user.id)}
                    disabled={loading}
                    style={{ padding: "var(--spacing-xs) var(--spacing-sm)", fontSize: "var(--scale-small)" }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}