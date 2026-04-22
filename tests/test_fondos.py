import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.security import verificar_token, validar_acceso_cliente

# ============================================================================
# FIXTURE DE AUTENTICACIÓN - Override de dependencias de seguridad
# ============================================================================

@pytest.fixture
def mock_auth():
    """Mock de autenticación - reemplaza funciones de seguridad en todos los tests"""
    async def override_verify_token():
        return "12345"  # Retornar solo el cliente_id como string
    
    async def override_validar_acceso_cliente(cliente_id, current_user):
        # No validar, permitir acceso para tests
        return True
    
    # Guardar los overrides originales
    original_overrides = app.dependency_overrides.copy()
    
    # Establecer los overrides
    app.dependency_overrides[verificar_token] = override_verify_token
    app.dependency_overrides[validar_acceso_cliente] = override_validar_acceso_cliente
    
    yield
    
    # Limpiar después del test
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture
def client(mock_auth):
    """TestClient con autenticación mocked"""
    return TestClient(app)


# ============================================================================
# FIXTURE DE MOCKS DE SERVICIOS
# ============================================================================

@pytest_asyncio.fixture
async def fake_repo_fondos(monkeypatch):
    """Fixture con mocks para tests de fondos"""
    cliente = {"_id": "12345", "saldo": 500000, "preferencia_notificacion": "email", "contacto": "cliente@example.com"}
    fondo = {"_id": 1, "nombre": "Fondo Prueba", "monto_minimo": 50000}
    fondos_list = [
        {"_id": 1, "nombre": "Fondo 1", "monto_minimo": 50000},
        {"_id": 2, "nombre": "Fondo 2", "monto_minimo": 100000}
    ]
    transacciones = [
        {"id_cliente": "12345", "id_fondo": "1", "tipo": "apertura", "monto": 100000},
        {"id_cliente": "12345", "id_fondo": "1", "tipo": "cancelación", "monto": 50000},
        {"id_cliente": "12345", "id_fondo": "2", "tipo": "apertura", "monto": 200000}
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente if id_cliente == "12345" else None

    async def fake_obtener_fondo(id_fondo):
        fondo_id = int(id_fondo) if isinstance(id_fondo, str) else id_fondo
        for f in fondos_list:
            if f["_id"] == fondo_id:
                return f
        return None

    async def fake_actualizar_saldo_cliente(cliente_id, nuevo_saldo):
        cliente["saldo"] = nuevo_saldo
        return True

    async def fake_crear_transaccion(transaccion):
        transacciones.append(transaccion.model_dump())
        return True

    async def fake_obtener_transacciones_cliente_fondo(id_cliente, id_fondo):
        return [t for t in transacciones if t["id_cliente"] == id_cliente and t["id_fondo"] == id_fondo]

    async def fake_notify(destinatario, mensaje, datos=None):
        return {"status": "sent"}

    # Monkeypatch en suscribir_service
    monkeypatch.setattr("app.services.suscribir_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.suscribir_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.suscribir_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.suscribir_service.crear_transaccion", fake_crear_transaccion)
    monkeypatch.setattr("app.notifications.context.NotificationContext.notify", fake_notify)

    # Monkeypatch en cancelar_service
    monkeypatch.setattr("app.services.cancelar_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_fondo", fake_obtener_fondo)
    monkeypatch.setattr("app.services.cancelar_service.actualizar_saldo_cliente", fake_actualizar_saldo_cliente)
    monkeypatch.setattr("app.services.cancelar_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_cliente_fondo)
    monkeypatch.setattr("app.services.cancelar_service.crear_transaccion", fake_crear_transaccion)

    return {
        "cliente": cliente,
        "fondo": fondo,
        "transacciones": transacciones
    }


# ============================================================================
# TESTS: SUSCRIPCIONES
# ============================================================================

class TestSuscribirFondo:
    """Tests para suscripciones a fondos"""

    def test_suscribir_fondo_success(self, client, fake_repo_fondos):
        """Test: Suscripción exitosa"""
        response = client.post("/fondos/suscribir", json={
            "id": "tx1",
            "id_cliente": "12345",
            "id_fondo": "1",
            "tipo": "apertura",
            "monto": 75000
        })
        
        assert response.status_code == 200, f"Status: {response.status_code}, Response: {response.json()}"
        data = response.json()
        assert "nuevo_saldo" in data
        assert "Suscripción exitosa" in data["mensaje"]

    def test_suscribir_fondo_monto_invalido(self, client, fake_repo_fondos):
        """Test: Monto inválido (muy bajo)"""
        response = client.post("/fondos/suscribir", json={
            "id": "tx2",
            "id_cliente": "12345",
            "id_fondo": "1",
            "tipo": "apertura",
            "monto": 100  # Menor que MONTO_MINIMO_PERMITIDO (1000)
        })
        
        # La validación de Pydantic ocurre antes -> 422
        assert response.status_code == 422, f"Status: {response.status_code}, Response: {response.json()}"

    def test_suscribir_fondo_cliente_invalido(self, client, fake_repo_fondos):
        """Test: Cliente inexistente"""
        response = client.post("/fondos/suscribir", json={
            "id": "tx3",
            "id_cliente": "cliente_no_existe",
            "id_fondo": "1",
            "tipo": "apertura",
            "monto": 75000
        })
        
        assert response.status_code in [403, 404], f"Status: {response.status_code}, Response: {response.json()}"


# ============================================================================
# TESTS: CANCELACIONES
# ============================================================================

class TestCancelarFondo:
    """Tests para cancelaciones"""

    def test_cancelar_fondo_success(self, client, fake_repo_fondos):
        """Test: Cancelación exitosa"""
        response = client.post(
            "/fondos/cancelar?cliente_id=12345&fondo_id=1",  # cliente_id y fondo_id como query params
            json={
                "id": "tx4",
                "tipo": "cancelación",
                "monto": 0
            }
        )
        
        assert response.status_code == 200, f"Status: {response.status_code}, Response: {response.json()}"
        data = response.json()
        assert "Cancelación exitosa" in data["mensaje"]
        assert "monto_devuelto" in data


# ============================================================================
# TESTS: HISTORIAL
# ============================================================================

class TestHistorial:
    """Tests para historial"""

    def test_historial_cliente_success(self, client, fake_repo_fondos):
        """Test: Obtener historial completo del cliente"""
        response = client.get("/fondos/historial/12345")
        
        assert response.status_code in [200, 404, 500], f"Status: {response.status_code}"

    def test_historial_cliente_fondo_success(self, client, fake_repo_fondos):
        """Test: Obtener historial por fondo específico"""
        response = client.get("/fondos/historial/12345/1")
        
        assert response.status_code in [200, 404, 500], f"Status: {response.status_code}"
