import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.security import verificar_token, validar_acceso_cliente

# ============================================================================
# FIXTURE DE AUTENTICACIÓN - Override de dependencias de seguridad
# ============================================================================

@pytest.fixture(autouse=True)
def mock_auth():
    """Override de seguridad para todos los tests de este archivo"""
    async def override_verify_token():
        return "c1"  # cliente_id fijo para pruebas
    
    async def override_validar_acceso_cliente(cliente_id, current_user):
        return True  # siempre permitir
    
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[verificar_token] = override_verify_token
    app.dependency_overrides[validar_acceso_cliente] = override_validar_acceso_cliente
    
    yield
    
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


client = TestClient(app)

# ============================================================================
# FIXTURE DE MOCKS DE SERVICIOS
# ============================================================================

@pytest_asyncio.fixture
async def fake_repo_endpoints(monkeypatch):
    """Fixture con mocks completos para tests de endpoints"""
    cliente = {"_id": "c1", "saldo": 200000, "preferencia_notificacion": "email", "contacto": "test@example.com"}
    fondo = {"_id": 1, "nombre": "Fondo Prueba", "monto_minimo": 50000}
    transacciones = [
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000}
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente if id_cliente == "c1" else None

    async def fake_obtener_fondo(id_fondo):
        return fondo if int(id_fondo) == 1 else None

    async def fake_actualizar_saldo_cliente(cliente_id, nuevo_saldo):
        cliente["saldo"] = nuevo_saldo
        return {"cliente_id": cliente_id, "saldo_nuevo": nuevo_saldo}

    async def fake_obtener_transacciones_cliente_fondo(id_cliente, id_fondo):
        return transacciones

    async def fake_crear_transaccion(transaccion):
        transacciones.append(transaccion.model_dump())
        return True

    async def fake_notify(destinatario, mensaje, datos=None):
        return {"status": "sent", "destinatario": destinatario}

    monkeypatch.setattr("app.services.suscribir_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.suscribir_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.suscribir_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.suscribir_service.crear_transaccion", fake_crear_transaccion)
    monkeypatch.setattr("app.notifications.context.NotificationContext.notify", fake_notify)

    monkeypatch.setattr("app.services.cancelar_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.cancelar_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_cliente_fondo)
    monkeypatch.setattr("app.services.cancelar_service.crear_transaccion", fake_crear_transaccion)

    return {"cliente": cliente, "fondo": fondo, "transacciones": transacciones}


# ============================================================================
# TESTS: SUSCRIBIR ENDPOINT
# ============================================================================

class TestSuscribirEndpoint:
    def test_suscribir_endpoint_success(self, fake_repo_endpoints):
        response = client.post("/fondos/suscribir", json={
            "id": "tx1", "id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000
        })
        assert response.status_code == 200
        data = response.json()
        assert "Suscripción exitosa" in data["mensaje"]

    def test_suscribir_endpoint_cliente_no_existe(self, fake_repo_endpoints):
        response = client.post("/fondos/suscribir", json={
            "id": "tx2", "id_cliente": "c999", "id_fondo": "1", "tipo": "apertura", "monto": 100000
        })
        assert response.status_code in [403, 404], f"Status: {response.status_code}, Response: {response.json()}"


    def test_suscribir_endpoint_fondo_no_existe(self, fake_repo_endpoints):
        response = client.post("/fondos/suscribir", json={
            "id": "tx3", "id_cliente": "c1", "id_fondo": "999", "tipo": "apertura", "monto": 100000
        })
        assert response.status_code == 404

    def test_suscribir_endpoint_saldo_insuficiente(self, fake_repo_endpoints):
        response = client.post("/fondos/suscribir", json={
            "id": "tx4", "id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 300000
        })
        assert response.status_code == 400

    def test_suscribir_endpoint_monto_minimo_fondo(self, fake_repo_endpoints):
        response = client.post("/fondos/suscribir", json={
            "id": "tx5", "id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 40000
        })
        assert response.status_code == 400


# ============================================================================
# TESTS: CANCELAR ENDPOINT
# ============================================================================

class TestCancelarEndpoint:
    def test_cancelar_endpoint_success(self, fake_repo_endpoints):
        response = client.post("/fondos/cancelar?cliente_id=c1&fondo_id=1", json={
            "id": "tx6", "tipo": "cancelación", "monto": 0
        })
        assert response.status_code == 200

    def test_cancelar_endpoint_cliente_no_existe(self, fake_repo_endpoints):
        response = client.post("/fondos/cancelar?cliente_id=c999&fondo_id=1", json={
        "id": "tx7", "tipo": "cancelación", "monto": 0
        })
        assert response.status_code in [403, 404], f"Status: {response.status_code}, Response: {response.json()}"

    def test_cancelar_endpoint_fondo_no_existe(self, fake_repo_endpoints):
        response = client.post("/fondos/cancelar?cliente_id=c1&fondo_id=999", json={
            "id": "tx8", "tipo": "cancelación", "monto": 0
        })
        assert response.status_code == 404

    def test_cancelar_endpoint_sin_saldo_invertido(self, fake_repo_endpoints):
        fake_repo_endpoints["transacciones"].append({
            "id_cliente": "c1", "id_fondo": "1", "tipo": "cancelación", "monto": 100000
        })
        response = client.post("/fondos/cancelar?cliente_id=c1&fondo_id=1", json={
            "id": "tx9", "tipo": "cancelación", "monto": 0
        })
        assert response.status_code == 400
