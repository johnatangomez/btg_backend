import pytest
from pydantic import ValidationError
from app.models import Transaccion, Cliente, Fondo, TipoTransaccion
from datetime import UTC, datetime

class TestTransaccion:
    """Tests de validación del modelo Transaccion"""
    
    def test_transaccion_valida(self):
        """Test: Transacción válida"""
        t = Transaccion(
            id="tx1",
            id_cliente="c1",
            id_fondo="1",
            tipo=TipoTransaccion.apertura,
            monto=100000
        )
        assert t.id == "tx1"
        assert t.monto == 100000

    def test_transaccion_monto_minimo_global(self):
        """Test: Monto < MONTO_MINIMO_PERMITIDO (1000)"""
        with pytest.raises(ValidationError) as exc_info:
            Transaccion(
                id="tx1",
                id_cliente="c1",
                id_fondo="1",
                tipo=TipoTransaccion.apertura,
                monto=500
            )
        assert "Monto mínimo permitido" in str(exc_info.value)

    def test_transaccion_monto_maximo_global(self):
        """Test: Monto > MONTO_MAXIMO_PERMITIDO (500000)"""
        with pytest.raises(ValidationError) as exc_info:
            Transaccion(
                id="tx1",
                id_cliente="c1",
                id_fondo="1",
                tipo=TipoTransaccion.apertura,
                monto=600000
            )
        assert "Monto máximo permitido" in str(exc_info.value)

    def test_transaccion_monto_cero(self):
        """Test: Monto = 0"""
        with pytest.raises(ValidationError):
            Transaccion(
                id="tx1",
                id_cliente="c1",
                id_fondo="1",
                tipo=TipoTransaccion.apertura,
                monto=0
            )

    def test_transaccion_id_cliente_vacio(self):
        """Test: ID cliente vacío"""
        with pytest.raises(ValidationError):
            Transaccion(
                id="tx1",
                id_cliente="",
                id_fondo="1",
                tipo=TipoTransaccion.apertura,
                monto=100000
            )

    def test_transaccion_id_fondo_vacio(self):
        """Test: ID fondo vacío"""
        with pytest.raises(ValidationError):
            Transaccion(
                id="tx1",
                id_cliente="c1",
                id_fondo="",
                tipo=TipoTransaccion.apertura,
                monto=100000
            )

class TestCliente:
    """Tests de validación del modelo Cliente"""
    
    def test_cliente_valido(self):
        """Test: Cliente válido"""
        c = Cliente(
            id="c1",
            nombre="Juan Pérez",
            saldo=500000,
            preferencia_notificacion="email",
            contacto="juan@example.com"
        )
        assert c.nombre == "Juan Pérez"
        assert c.saldo == 500000

    def test_cliente_nombre_vacio(self):
        """Test: Nombre vacío"""
        with pytest.raises(ValidationError):
            Cliente(
                id="c1",
                nombre="",
                saldo=500000,
                preferencia_notificacion="email",
                contacto="juan@example.com"
            )

    def test_cliente_email_invalido(self):
        """Test: Email inválido"""
        with pytest.raises(ValidationError):
            Cliente(
                id="c1",
                nombre="Juan",
                saldo=500000,
                preferencia_notificacion="email",
                contacto="invalid-email"
            )

    def test_cliente_telefono_invalido(self):
        """Test: Teléfono inválido"""
        with pytest.raises(ValidationError):
            Cliente(
                id="c1",
                nombre="Juan",
                saldo=500000,
                preferencia_notificacion="sms",
                contacto="invalid-phone"
            )

    def test_cliente_telefono_valido(self):
        """Test: Teléfono válido"""
        c = Cliente(
            id="c1",
            nombre="Juan",
            saldo=500000,
            preferencia_notificacion="sms",
            contacto="+573105551234"
        )
        assert c.contacto == "+573105551234"

class TestFondo:
    """Tests de validación del modelo Fondo"""
    
    def test_fondo_valido(self):
        """Test: Fondo válido"""
        f = Fondo(
            id="1",
            nombre="Fondo Seguro",
            monto_minimo=50000,
            categoria="Renta Fija"
        )
        assert f.nombre == "Fondo Seguro"
        assert f.monto_minimo == 50000

    def test_fondo_monto_minimo_cero(self):
        """Test: Monto mínimo = 0"""
        with pytest.raises(ValidationError):
            Fondo(
                id="1",
                nombre="Fondo Seguro",
                monto_minimo=0,
                categoria="Renta Fija"
            )

    def test_fondo_nombre_vacio(self):
        """Test: Nombre vacío"""
        with pytest.raises(ValidationError):
            Fondo(
                id="1",
                nombre="",
                monto_minimo=50000,
                categoria="Renta Fija"
            )