import pytest
import pytest_asyncio
from fastapi import HTTPException
from app.services.historial_cliente_fondo_service import historial_cliente_fondo

@pytest_asyncio.fixture
async def fake_db_historial_fondo(monkeypatch):
    """Fixture para tests de historial cliente-fondo"""
    cliente = {"_id": "c1", "saldo": 500000}
    transacciones = [
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000},
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "cancelación", "monto": 50000}
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente if id_cliente == "c1" else None

    async def fake_obtener_transacciones_cliente_fondo(id_cliente, id_fondo):
        if not transacciones:
            return []
        return transacciones

    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_cliente_fondo)

    return {"cliente": cliente, "transacciones": transacciones}

@pytest.mark.asyncio
async def test_historial_cliente_fondo_success(fake_db_historial_fondo):
    """Test: Historial exitoso"""
    result = await historial_cliente_fondo("c1", "1")
    
    assert result["saldo_invertido_actual"] == 50000  # 100000 - 50000
    assert result["saldo_actual_cliente"] == 500000
    assert result["aperturas_totales"] == 100000
    assert result["cancelaciones_totales"] == 50000
    assert len(result["historial"]) == 2

@pytest.mark.asyncio
async def test_historial_cliente_fondo_cliente_no_existe(fake_db_historial_fondo, monkeypatch):
    """Test: Cliente no existe"""
    async def fake_obtener_cliente_none(id_cliente):
        return None

    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_cliente", fake_obtener_cliente_none)

    with pytest.raises(HTTPException) as exc_info:
        await historial_cliente_fondo("c999", "1")
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_historial_cliente_fondo_sin_transacciones(monkeypatch):
    """Test: Sin transacciones"""
    cliente = {"_id": "c1", "saldo": 500000}

    async def fake_obtener_cliente(id_cliente):
        return cliente

    async def fake_obtener_transacciones_vacio(id_cliente, id_fondo):
        return []

    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones_vacio)

    with pytest.raises(HTTPException) as exc_info:
        await historial_cliente_fondo("c1", "1")
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_historial_cliente_fondo_id_cliente_invalido(fake_db_historial_fondo):
    """Test: ID de cliente inválido"""
    with pytest.raises(HTTPException) as exc_info:
        await historial_cliente_fondo("", "1")
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_historial_cliente_fondo_id_fondo_invalido(fake_db_historial_fondo):
    """Test: ID de fondo inválido"""
    with pytest.raises(HTTPException) as exc_info:
        await historial_cliente_fondo("c1", "")
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_historial_cliente_fondo_saldo_negativo(monkeypatch):
    """Test: Detectar saldo invertido negativo (warning)"""
    cliente = {"_id": "c1", "saldo": 500000}
    transacciones = [
        {"id_cliente": "c1", "id_fondo": "1", "tipo": "cancelación", "monto": 100000}
    ]

    async def fake_obtener_cliente(id_cliente):
        return cliente

    async def fake_obtener_transacciones(id_cliente, id_fondo):
        return transacciones

    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_cliente", fake_obtener_cliente)
    monkeypatch.setattr("app.services.historial_cliente_fondo_service.obtener_transacciones_cliente_fondo", fake_obtener_transacciones)

    result = await historial_cliente_fondo("c1", "1")
    assert result["saldo_invertido_actual"] == -100000