# TravelPath — Sistema de Gestión de Itinerarios de Viaje

**Equipo:** Sebastián Carvajal, Brissa Mahecha  
**Arquitectura:** Hexagonal (Ports & Adapters)  
**Stack:** Python · Flask · SQLAlchemy · MySQL · JWT · Plotly

---

## Requisitos previos

- Python 3.11+
- MySQL 8.0 (o Docker)
- pip

---

## Ejecución con Docker (recomendado)

```bash
docker-compose up --build
```

La app estará disponible en http://localhost:5000

---

## Ejecución local (sin Docker)

```bash
# 1. Entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# Edita .env con tus credenciales de MySQL

# 4. Base de datos
mysql -u root -p < database/migrations/001_create_tables.sql
mysql -u root -p < database/migrations/002_indexes.sql
mysql -u root -p < database/migrations/003_seed_data.sql   # opcional (aeropuertos iniciales)

# 5. Ejecutar
python app.py
```

---

## Endpoints principales

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/register` | Registro de usuario |
| POST | `/auth/login` | Login (retorna JWT) |
| POST | `/auth/logout` | Cierre de sesión |
| POST | `/auth/refresh` | Renovar token |
| GET  | `/auth/me` | Perfil del usuario autenticado |

### Itinerarios *(requieren JWT)*
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/itinerarios` | Listar todos del usuario |
| POST | `/api/itinerarios` | Crear nuevo |
| GET | `/api/itinerarios/<id>` | Detalle |
| PUT | `/api/itinerarios/<id>` | Modificar |
| DELETE | `/api/itinerarios/<id>` | Borrado lógico |
| GET | `/api/itinerarios/historial` | Agrupado por año |

### Aeropuertos *(requieren JWT)*
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/aeropuertos?nombre=bog` | Búsqueda por nombre |
| GET | `/api/aeropuertos/<iata>` | Búsqueda por código IATA |
| GET | `/api/aeropuertos/mapa` | Datos para mapa Plotly |

---

## Ejecutar tests

```bash
# Tests unitarios
pytest tests/unit/ -v

# Tests de integración
pytest tests/integration/ -v

# Todos
pytest tests/ -v
```

---

## Estructura del proyecto

```
travelpath/
├── src/
│   ├── domain/          # Núcleo — entidades, puertos, excepciones
│   ├── application/     # Casos de uso — servicios y DTOs
│   ├── infrastructure/  # Adaptadores — DB, API externa, controladores
│   └── presentation/    # Frontend — HTML, CSS, JS
├── database/
│   ├── migrations/      # SQL puro: DDL, índices, seed
│   └── models/          # Modelos ORM SQLAlchemy
├── tests/
│   ├── unit/            # Tests de dominio y servicios
│   └── integration/     # Tests de API HTTP
├── app.py               # Entry point
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Requerimientos implementados

| ID | Descripción | Estado |
|----|-------------|--------|
| RF-01 | Registro de usuarios | ✅ |
| RF-02 | Inicio de sesión con JWT | ✅ |
| RF-03 | Cierre de sesión (blacklist) | ✅ |
| RF-04 | Recuperación de contraseña (simulada) | ✅ |
| RF-05 | Crear itinerario con validación de aeropuertos | ✅ |
| RF-06 | Consultar itinerarios paginados | ✅ |
| RF-07 | Ver detalle con mapa Plotly | ✅ |
| RF-08 | Modificar itinerario | ✅ |
| RF-09 | Eliminar (borrado lógico) | ✅ |
| RF-10 | Validar fechas no pasadas | ✅ |
| RF-11 | Validar superposición de fechas | ✅ |
| RF-12 | Calcular duración automáticamente | ✅ |
| RF-13 | Restricción modificación itinerario pasado | ✅ |
| RF-14 | Buscar aeropuerto por nombre | ✅ |
| RF-15 | Buscar aeropuerto por código IATA | ✅ |
| RF-16 | Autocompletado en formulario | ✅ |
| RF-18 | Mapa interactivo (Plotly scatter geo) | ✅ |
| RF-19 | Historial agrupado por año | ✅ |
