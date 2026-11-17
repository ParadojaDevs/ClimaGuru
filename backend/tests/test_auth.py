"""Pruebas de autenticacion: /login, cookies httpOnly y acceso con JWT.

Usa la app completa ensamblada en conftest.py (SQLite en tmp, sin MySQL).
"""

import pytest


class TestLogin:
    def test_login_exitoso_devuelve_tokens(self, auth_client, seeded_user, login):
        body = login()
        assert body["token"]
        assert body["refresh_token"]
        assert body["user"]["username"] == "admin"
        # La respuesta nunca debe exponer el hash
        assert "password_hash" not in body["user"]

    def test_login_fija_cookies_httponly(self, auth_client, seeded_user):
        response = auth_client.post(
            "/login", json={"username": "admin", "password": "admin123"}
        )
        cookies = "; ".join(response.headers.getlist("Set-Cookie"))
        assert "climaguru_access_token=" in cookies
        assert "climaguru_refresh_token=" in cookies
        assert "HttpOnly" in cookies

    def test_login_credenciales_invalidas(self, auth_client, seeded_user):
        response = auth_client.post(
            "/login", json={"username": "admin", "password": "malaclave"}
        )
        assert response.status_code == 401
        assert response.get_json()["error"] == "credenciales invalidas"

    def test_login_usuario_inexistente(self, auth_client):
        response = auth_client.post(
            "/login", json={"username": "fantasma", "password": "x"}
        )
        assert response.status_code == 401

    def test_login_campos_faltantes(self, auth_client):
        response = auth_client.post("/login", json={"username": "admin"})
        assert response.status_code == 400

    def test_login_sin_json(self, auth_client):
        response = auth_client.post("/login", data="")
        assert response.status_code == 400


class TestAccesoConToken:
    def test_users_con_token_devuelve_lista(self, auth_client, seeded_user, login):
        token = login()["token"]
        response = auth_client.get(
            "/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        users = response.get_json()
        assert any(u["username"] == "admin" for u in users)
        assert all("password_hash" not in u for u in users)

    def test_token_invalido_422(self, auth_client):
        response = auth_client.get(
            "/users", headers={"Authorization": "Bearer no-es-un-jwt"}
        )
        assert response.status_code in (401, 422)
