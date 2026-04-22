# BTG Backend

Este proyecto es un backend desarrollado en **Python** usando **FastAPI**, diseñado para gestionar suscripciones de clientes a fondos y enviar notificaciones mediante diferentes estrategias (correo electrónico vía SMTP y SMS vía Twilio).  
Además, incluye consultas SQL sobre una base de datos relacional llamada **BTG**, como parte de la prueba técnica.

---

## Características principales
- API REST con FastAPI.
- Patrón Strategy para notificaciones (Email y SMS).
- Plantillas HTML para correos electrónicos.
- Integración con **SMTP (Outlook/Gmail)** y **Twilio**.
- Manejo de excepciones y logging.
- Pruebas unitarias con `pytest`.
- Consultas SQL sobre la base de datos **BTG**.

---

## Estructura del proyecto
btg_backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Aplicación FastAPI principal
│   ├── config.py                    # Variables de configuración
│   ├── database.py                  # Conexión a MongoDB
│   ├── logger.py                    # Sistema de logging
│   ├── security.py                  # Autenticación JWT
│   ├── models.py                    # Modelos Pydantic
│   ├── crud.py                      # Operaciones de BD (Create, Read, Update, Delete)
│   ├── utils.py                     # Funciones utilitarias
│   │
│   ├── repositories/
│   │   └── fondos_repo.py           # Repositorio de fondos
│   │
│   ├── services/
│   │   ├── suscribir_service.py     # Lógica de suscripción
│   │   ├── cancelar_service.py      # Lógica de cancelación
│   │   ├── historial_cliente_service.py         # Historial completo
│   │   └── historial_cliente_fondo_service.py   # Historial por fondo
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── fondos.py                # Endpoints de fondos
│   │
│   ├── notifications/
│   │   ├── base.py                  # Clase base de notificaciones
│   │   ├── context.py               # Context pattern
│   │   ├── email_strategy.py        # Estrategia de email
│   │   ├── sms_strategy.py          # Estrategia de SMS
│   │   └── templates/
│   │       └── respuesta.html       # Template de email
│   │
│   └── logs/                        # Logs de la aplicación
│       └── app.log
│
├── tests/
│   ├── __init__.py
│   ├── test_suscribir_service.py    # Tests de suscripción
│   ├── test_cancelar_service.py     # Tests de cancelación
│   ├── test_historial_*.py          # Tests de historial
│   ├── test_models.py               # Tests de validación Pydantic
│   ├── test_repositories.py         # Tests de repositorio
│   ├── test_endpoints.py            # Tests de endpoints
│   └── test_fondos.py               # Tests de integración
│
├── .env                             # Variables de entorno (no committed)
├── .gitignore                       # Archivos a ignorar en Git
├── .env.example                     # Ejemplo de .env
├── requirements.txt                 # Dependencias del proyecto
├── README.md                        # Este archivo
├── pytest.ini                       # Configuración de pytest
└── consultas_sql/                   # Consultas SQL
    └── consulta.sql                 # Consulta a BD BTG relacional

---
## Instalación paso a paso

- python3 -m venv venv_btg
- source venv_btg/bin/activate   # Linux/Mac
- venv_btg\Scripts\activate      # Windows

- pip install -r requirements.txt
- Crear un archivo .env con las variables de entorno (revisar .env.example)

---
## Levantar aplicación
- uvicorn app.main:app --reload
- La aplicación estara disponible en http://localhost:8000

se puede visualizar la documentación en:
- http://localhost:8000/docs
---

## Ejecutar Test

- pytest