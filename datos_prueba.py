from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno (donde guardas tu URI)
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

# Conectar al cluster
client = MongoClient(MONGO_URI)

# Seleccionar la base de datos
client.drop_database("BTG")  # Eliminar la base de datos si ya existe para evitar duplicados
db = client["BTG"]

# Datos de prueba
clientes = [
    {"_id": "c1", "nombre": "Juan", "apellidos": "Pérez", "ciudad": "Medellín"},
    {"_id": "c2", "nombre": "Ana", "apellidos": "Gómez", "ciudad": "Bogotá"}
]

sucursales = [
    {"_id": "s1", "nombre": "Sucursal Centro", "ciudad": "Bogotá"},
    {"_id": "s2", "nombre": "Sucursal Norte", "ciudad": "Medellín"}
]

productos = [
    {"_id": "p1", "nombre": "Laptop", "tipoProducto": "Electrónica"},
    {"_id": "p2", "nombre": "Libro", "tipoProducto": "Educación"}
]

inscripciones = [
    {"_id": "i1", "idProducto": "p1", "idCliente": "c1"},
    {"_id": "i2", "idProducto": "p2", "idCliente": "c2"}
]

disponibilidades = [
    {"_id": "d1", "idSucursal": "s1", "idProducto": "p1"},
    {"_id": "d2", "idSucursal": "s2", "idProducto": "p2"}
]

visitas = [
    {"_id": "v1", "idSucursal": "s1", "idCliente": "c1", "fechaVisita": "2026-04-15"},
    {"_id": "v2", "idSucursal": "s2", "idCliente": "c2", "fechaVisita": "2026-04-16"}
]

fondos = [
    {"_id": 1, "nombre": "FPV_BTG_PACTUAL_RECAUDADORA", "monto_minimo": 75000, "categoria": "FPV", "moneda": "COP"},
    {"_id": 2, "nombre": "FPV_BTG_PACTUAL_ECOPETROL", "monto_minimo": 125000, "categoria": "FPV", "moneda": "COP"},
    {"_id": 3, "nombre": "DEUDAPRIVADA", "monto_minimo": 50000, "categoria": "FIC", "moneda": "COP"},
    {"_id": 4, "nombre": "FDO-ACCIONES", "monto_minimo": 250000, "categoria": "FIC", "moneda": "COP"},
    {"_id": 5, "nombre": "FPV_BTG_PACTUAL_DINAMICA", "monto_minimo": 100000, "categoria": "FPV", "moneda": "COP"}
]

# Insertar documentos en cada colección (plural y minúsculas)
db.clientes.insert_many(clientes)
db.sucursales.insert_many(sucursales)
db.productos.insert_many(productos)
db.inscripciones.insert_many(inscripciones)
db.disponibilidades.insert_many(disponibilidades)
db.visitas.insert_many(visitas)
db.fondos.insert_many(fondos)

print("Colecciones y datos de prueba creados correctamente en MongoDB Atlas")

