const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

function buildHeaders(token, hasBody = false) {
  const headers = {};
  if (hasBody) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function request(path, { method = "GET", body, token } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: buildHeaders(token, body !== undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.error || "Error de servidor";
    throw new Error(message);
  }

  return payload;
}

export function login(username, password) {
  return request("/login", {
    method: "POST",
    body: { username, password },
  });
}

export function getUsers(token) {
  return request("/users", { token });
}

export function createUser(token, data) {
  return request("/users", {
    method: "POST",
    token,
    body: data,
  });
}

export function updateUser(token, id, data) {
  return request(`/users/${id}`, {
    method: "PUT",
    token,
    body: data,
  });
}

export function deleteUser(token, id) {
  return request(`/users/${id}`, {
    method: "DELETE",
    token,
  });
}
