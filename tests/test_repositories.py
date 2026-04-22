import pytest
import pytest_asyncio
from fastapi import HTTPException
from app.repositories.fondos_repo import (
    obtener_fondo,
    actualizar_saldo_cliente,
    obtener_transacciones_cliente_fondo,
)


class AsyncIterator:
    """Implementa un iterador async"""
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class FakeCursor:
    """Simula un cursor de MongoDB async que implementa sort()"""
    def __init__(self, items):
        self.items = items

    def sort(self, field, direction):
        """Retorna self para permitir encadenamiento"""
        return self

    def __aiter__(self):
        """Retorna un iterador async"""
        return AsyncIterator(self.items)


class FakeUpdateResult:
    """Simula el resultado de update_one"""
    def __init__(self, matched=1, modified=1):
        self.matched_count = matched
        self.modified_count = modified


class FakeCollection:
    """Simula una colección de MongoDB con soporte para múltiples documentos"""
    def __init__(self):
        self.documents = {}  # {id: documento}

    def insert_document(self, doc):
        """Inserta un documento en la colección fake"""
        doc_id = doc.get("_id")
        if doc_id is not None:
            self.documents[doc_id] = doc

    async def find_one(self, query):
        """Busca un único documento que coincida con la query"""
        id_value = query.get("_id")
        return self.documents.get(id_value)

    async def update_one(self, query, update):
        """Actualiza un documento"""
        id_value = query.get("_id")
        if id_value in self.documents:
            if "$set" in update:
                self.documents[id_value].update(update["$set"])
            return FakeUpdateResult(matched=1, modified=1)
        return FakeUpdateResult(matched=0, modified=0)

    def find(self, query=None):
        """Retorna un cursor con documentos que coincidan"""
        if query is None:
            items = list(self.documents.values())
        else:
            # Filtrar documentos según la query
            items = [doc for doc in self.documents.values() if self._match_query(doc, query)]
        
        return FakeCursor(items)

    def _match_query(self, doc, query):
        """Verifica si un documento coincide con una query"""
        for key, value in query.items():
            if doc.get(key) != value:
                return False
        return True


class FakeDB:
    """Simula el objeto db de MongoDB"""
    def __init__(self):
        self.fondos = FakeCollection()
        self.clientes = FakeCollection()
        self.transacciones = FakeCollection()


@pytest_asyncio.fixture
async def setup_fake_db(monkeypatch):
    """Fixture que configura la base de datos fake"""
    db = FakeDB()
    
    # Insertar datos de prueba
    db.fondos.insert_document({"_id": 1, "nombre": "Fondo 1", "monto_minimo": 50000})
    db.clientes.insert_document({"_id": "c1", "saldo": 500000})
    db.transacciones.insert_document({"id_cliente": "c1", "id_fondo": "1", "tipo": "apertura", "monto": 100000})
    
    # Inyectar el db fake en el módulo
    monkeypatch.setattr("app.repositories.fondos_repo.db", db)
    
    return db


class TestObtenerFondo:
    """Tests para la función obtener_fondo"""

    @pytest.mark.asyncio
    async def test_obtener_fondo_success(self, setup_fake_db):
        """Test: Obtener fondo exitosamente"""
        result = await obtener_fondo("1")
        
        assert result is not None
        assert result["_id"] == 1
        assert result["nombre"] == "Fondo 1"

    @pytest.mark.asyncio
    async def test_obtener_fondo_no_existe(self, setup_fake_db):
        """Test: Fondo no existe retorna None"""
        result = await obtener_fondo("999")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_obtener_fondo_id_invalido(self, setup_fake_db):
        """Test: ID inválido lanza HTTPException 400"""
        with pytest.raises(HTTPException) as exc_info:
            await obtener_fondo("")
        
        assert exc_info.value.status_code == 400


class TestActualizarSaldoCliente:
    """Tests para la función actualizar_saldo_cliente"""

    @pytest.mark.asyncio
    async def test_actualizar_saldo_cliente_success(self, setup_fake_db):
        """Test: Actualizar saldo exitosamente"""
        result = await actualizar_saldo_cliente("c1", 400000)
        
        assert result is not None
        assert result["saldo_nuevo"] == 400000
        assert result["saldo_anterior"] == 500000

    @pytest.mark.asyncio
    async def test_actualizar_saldo_cliente_saldo_negativo(self, setup_fake_db):
        """Test: Saldo negativo lanza HTTPException 400"""
        with pytest.raises(HTTPException) as exc_info:
            await actualizar_saldo_cliente("c1", -100000)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_actualizar_saldo_cliente_no_existe(self, setup_fake_db):
        """Test: Cliente no existe lanza HTTPException 404"""
        with pytest.raises(HTTPException) as exc_info:
            await actualizar_saldo_cliente("c999", 400000)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_actualizar_saldo_cliente_id_invalido(self, setup_fake_db):
        """Test: ID cliente inválido lanza HTTPException 400"""
        with pytest.raises(HTTPException) as exc_info:
            await actualizar_saldo_cliente("", 400000)
        
        assert exc_info.value.status_code == 400


class TestObtenerTransaccionesClienteFondo:
    """Tests para la función obtener_transacciones_cliente_fondo"""

    @pytest.mark.asyncio
    async def test_obtener_transacciones_cliente_fondo_vacio(self, setup_fake_db):
        """Test: Sin transacciones retorna lista vacía"""
        result = await obtener_transacciones_cliente_fondo("c999", "999")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_obtener_transacciones_id_cliente_invalido(self, setup_fake_db):
        """Test: ID cliente inválido lanza HTTPException 400"""
        with pytest.raises(HTTPException) as exc_info:
            await obtener_transacciones_cliente_fondo("", "1")
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_obtener_transacciones_id_fondo_invalido(self, setup_fake_db):
        """Test: ID fondo inválido lanza HTTPException 400"""
        with pytest.raises(HTTPException) as exc_info:
            await obtener_transacciones_cliente_fondo("c1", "")
        
        assert exc_info.value.status_code == 400