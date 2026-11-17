"""Pruebas del CRUD de usuarios que alimenta el dashboard (/users).

En este backend (Backend A) no hay rutas de consultas meteorologicas
privadas (viven en app_pkg, fase posterior); este archivo cubre el CRUD
de la zona autenticada. SQLite en tmp, sin MySQL.
"""

import pytest


@pytest.fixture()
def auth_headers(auth_client, seeded_user, login):
    token = login()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestCrear:
    def test_create_201(self, auth_client, auth_headers):
        response = auth_client.post(
            "/users",
            json={"username": "operario1", "password": "clave123"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.get_json()
        assert body["username"] == "operario1"
        assert "id" in body

    def test_create_duplicado_409(self, auth_client, auth_headers, seeded_user):
        response = auth_client.post(
            "/users",
            json={"username": "admin", "password": "otra"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_create_sin_password_400(self, auth_client, auth_headers):
        response = auth_client.post(
            "/users", json={"username": "x"}, headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_nuevo_usuario_puede_loguearse(self, auth_client, auth_headers, login):
        auth_client.post(
            "/users",
            json={"username": "temporal", "password": "clave123"},
            headers=auth_headers,
        )
        body = login("temporal", "clave123")
        assert body["user"]["username"] == "temporal"


class TestListar:
    def test_lista_incluye_creados(self, auth_client, auth_headers, seeded_user):
        auth_client.post(
            "/users",
            json={"username": "segundo", "password": "clave123"},
            headers=auth_headers,
        )
        response = auth_client.get("/users", headers=auth_headers)
        usernames = [u["username"] for u in response.get_json()]
        assert "admin" in usernames
        assert "segundo" in usernames


class TestActualizar:
    def test_update_username_200(self, auth_client, auth_headers, seeded_user):
        response = auth_client.put(
            f"/users/{seeded_user['id']}",
            json={"username": "admin_renombrado"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["username"] == "admin_renombrado"

    def test_update_password_permite_login_nuevo(
        self, auth_client, auth_headers, seeded_user
    ):
        response = auth_client.put(
            f"/users/{seeded_user['id']}",
            json={"password": "nuevaclave"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        # la clave vieja ya no sirve, la nueva si
        assert auth_client.post(
            "/login", json={"username": "admin", "password": "admin123"}
        ).status_code == 401
        assert (
            auth_client.post(
                "/login", json={"username": "admin", "password": "nuevaclave"}
            ).status_code
            == 200
        )

    def test_update_username_vacio_400(self, auth_client, auth_headers, seeded_user):
        response = auth_client.put(
            f"/users/{seeded_user['id']}", json={"username": "   "}, headers=auth_headers
        )
        assert response.status_code == 400

    def test_update_username_en_uso_409(self, auth_client, auth_headers, seeded_user):
        auth_client.post(
            "/users",
            json={"username": "otro", "password": "clave123"},
            headers=auth_headers,
        )
        response = auth_client.put(
            f"/users/{seeded_user['id']}", json={"username": "otro"}, headers=auth_headers
        )
        assert response.status_code == 409

    def test_update_inexistente_404(self, auth_client, auth_headers):
        response = auth_client.put(
            "/users/99999", json={"username": "x"}, headers=auth_headers
        )
        assert response.status_code == 404


class TestEliminar:
    def test_delete_200_y_desaparece(self, auth_client, auth_headers, seeded_user):
        response = auth_client.delete(
            f"/users/{seeded_user['id']}", headers=auth_headers
        )
        assert response.status_code == 200
        usernames = [u["username"] for u in auth_client.get("/users", headers=auth_headers).get_json()]
        assert "admin" not in usernames

    def test_delete_inexistente_404(self, auth_client, auth_headers):
        response = auth_client.delete("/users/99999", headers=auth_headers)
        assert response.status_code == 404
