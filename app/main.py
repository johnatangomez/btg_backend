from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import routers
from app.logger import logger

app = FastAPI(title="BTG Fondos API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Endpoint para verificar salud de la API"""
    logger.info("Health check")
    return {"status": "ok"}

# Registrar todos los routers
for r in routers:
    app.include_router(r)

logger.info("Aplicación BTG Fondos API inicializada")