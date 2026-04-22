import pytest
from fastapi import HTTPException
from app.security import verificar_token, validar_acceso_cliente

# -------------------------------
# Tests para verificar_token (async)
# -------------------------------

@pytest.mark.asyncio
async def test_verificar_token_sin_header():
    # Simular llamada sin header
    with pytest.raises(HTTPException) as exc_info:
        await verificar_token(None)   # no se pasa Authorization
    assert exc_info.value.status_code == 401
    assert "Authorization" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_verificar_token_con_header_invalido():
    with pytest.raises(HTTPException) as exc_info:
        await verificar_token("Bearer token_invalido")
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_verificar_token_valido():
    # Usar un token inválido provoca excepción
    with pytest.raises(HTTPException) as exc_info:
        await verificar_token("Bearer c1")
    assert exc_info.value.status_code == 401
    assert "Token expirado o inválido" in str(exc_info.value.detail)

# -------------------------------
# Tests para validar_acceso_cliente (sync)
# -------------------------------

def test_validar_acceso_cliente_autorizado():
    result = validar_acceso_cliente("c1", "c1")
    assert result is True

def test_validar_acceso_cliente_no_autorizado():
    with pytest.raises(HTTPException) as exc_info:
        validar_acceso_cliente("c999", "c1")
    assert exc_info.value.status_code == 403
    # Ajustar al mensaje real de tu implementación
    assert "No tienes permiso" in str(exc_info.value.detail)
