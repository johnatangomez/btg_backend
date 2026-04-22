import pytest
import pytest_asyncio
from fastapi import HTTPException
from app.services.historial_cliente_service import historial_por_cliente

@pytest_asyncio.fixture
async def fake_db_historial_cliente(monkeypatch):
    """Fixture para tests de historial completo del cliente"""
    
    class FakeCursor:
        def __init__(self, data):
            self.data = data

        def sort(self, field, order):
            return self

        def __aiter__(self):
            async def generator():
                for item in self.data:
                    yield item
            return generator()

    class FakeTransacciones:
        def __init__(self):
            self.data = [
                {"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000},
                {"id_cliente": "c1", "id_fondo": "1", "tipo": "cancelación", "monto": 50000},
                {"id_cliente": "c1", "id_fondo": "2", "tipo": "apertura", "monto": 200000}
            ]

        def find(self, query):
            data = [t for t in self.data if t["id_cliente"] == query["id_cliente"]]
            return FakeCursor(data)

    class FakeDB:
        def __init__(self):
            self.transacciones = FakeTransacciones()

    db = FakeDB()
    monkeypatch.setattr("app.services.historial_cliente_service.db", db)

    return db

@pytest.mark.asyncio
async def test_historial_por_cliente_success(fake_db_historial_cliente):
    """Test: Historial completo exitoso"""
    result = await historial_por_cliente("c1")
    
    assert result["total_invertido"] == 250000  # (100000-50000) + 200000
    assert result["cantidad_fondos"] == 2
    assert len(result["fondos"]) == 2
    
    fondos = {f["id_fondo"]: f for f in result["fondos"]}
    assert fondos["1"]["saldo_invertido_actual"] == 50000
    assert fondos["2"]["saldo_invertido_actual"] == 200000

@pytest.mark.asyncio
async def test_historial_por_cliente_sin_transacciones(monkeypatch):
    """Test: Cliente sin transacciones"""
    
    class FakeCursor:
        def sort(self, field, order):
            return self
        def __aiter__(self):
            async def generator():
                return
                yield
            return generator()

    class FakeTransacciones:
        def find(self, query):
            return FakeCursor()

    class FakeDB:
        def __init__(self):
            self.transacciones = FakeTransacciones()

    db = FakeDB()
    monkeypatch.setattr("app.services.historial_cliente_service.db", db)

    with pytest.raises(HTTPException) as exc_info:
        await historial_por_cliente("c999")
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_historial_por_cliente_id_invalido(fake_db_historial_cliente):
    """Test: ID de cliente inválido"""
    with pytest.raises(HTTPException) as exc_info:
        await historial_por_cliente("")
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_historial_por_cliente_calculo_total(fake_db_historial_cliente):
    """Test: Cálculo correcto del total invertido"""
    result = await historial_por_cliente("c1")
    
    # Fondo 1: 100000 - 50000 = 50000
    # Fondo 2: 200000
    # Total: 250000
    assert result["total_invertido"] == 250000