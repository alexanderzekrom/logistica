# Sistema de Logística y Envíos

Backend Python (FastAPI) + Frontend React con TypeScript.

## Requisitos

- Python 3.12+
- Node.js 22+
- MySQL 8.0+ (o MariaDB compatible)
- Docker y Docker Compose (opcional)

## Estructura del Proyecto

```
prueba/
├── backend/                 # Backend Python (FastAPI)
│   ├── config/             # Configuración
│   │   ├── database.py     # Conexión a base de datos
│   │   └── security.py     # Seguridad y JWT
│   ├── models/             # Modelos de datos
│   │   ├── database_models.py  # Modelos SQLAlchemy
│   │   └── schemas.py      # Esquemas Pydantic
│   ├── routes/             # Rutas de la API
│   │   ├── auth.py         # Autenticación
│   │   ├── clientes.py     # Endpoints de clientes
│   │   ├── conductores.py  # Endpoints de conductores
│   │   ├── vehiculos.py    # Endpoints de vehículos
│   │   └── pedidos.py      # Endpoints de pedidos
│   ├── main.py             # Punto de entrada de la aplicación
│   └── Dockerfile
├── frontend-react/         # Frontend React + TypeScript
│   ├── src/                # Código fuente
│   │   ├── components/     # Componentes React
│   │   ├── pages/          # Páginas
│   │   ├── api.ts          # Cliente API
│   │   └── types.ts        # Tipos TypeScript
│   ├── package.json        # Dependencias Node
│   ├── vite.config.ts      # Configuración Vite
│   └── Dockerfile
├── data/                   # Datos y scripts SQL
│   └── baseDatos_corregido-v2.sql
├── docs/                   # Documentación
├── .env.example            # Variables de entorno ejemplo
├── docker-compose.yml      # Configuración Docker
├── requirements.txt        # Dependencias Python
└── README.md              # Este archivo
```

## Instalación con Docker (Recomendado)

### 1. Copiar archivo de entorno

```bash
cp .env.example .env
```

### 2. Levantar servicios

```bash
docker-compose up -d
```

Los servicios estarán disponibles en:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8001`
- Base de datos: `localhost:3307`

## Instalación Manual

### Backend

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos MySQL
mysql -u root -p
```

```sql
CREATE DATABASE logistica_db;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON logistica_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

```bash
# Ejecutar script de base de datos
mysql -u app_user -p logistica_db < data/baseDatos_corregido-v2.sql

# Ejecutar backend
cd backend
python main.py
```

### Frontend React

```bash
cd frontend-react

# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build para producción
npm run build
```

## API Endpoints

### Autenticación
- `POST /login` - Login simple
- `POST /api/token` - Login con token JWT

### Clientes
- `GET /clientes` - Listar todos
- `POST /clientes` - Crear cliente
- `PUT /clientes/{id}` - Actualizar cliente
- `DELETE /clientes/{id}` - Eliminar cliente

### Conductores
- `GET /conductores` - Listar todos
- `POST /conductores` - Crear conductor
- `PUT /conductores/{id}` - Actualizar conductor
- `DELETE /conductores/{id}` - Eliminar conductor

### Vehículos
- `GET /vehiculos` - Listar todos
- `POST /vehiculos` - Crear vehículo
- `PUT /vehiculos/{id}` - Actualizar vehículo
- `DELETE /vehiculos/{id}` - Eliminar vehículo

### Pedidos
- `GET /pedidos` - Listar todos
- `GET /api/pedidos` - Listar con filtros por rol
- `POST /pedidos` - Crear pedido
- `PUT /pedidos/{id}` - Actualizar pedido completo
- `PUT /pedidos/{id}/estado` - Actualizar estado
- `DELETE /pedidos/{id}` - Eliminar pedido

## Usuarios de Prueba

- **admin** / `123` (Rol: ADMIN)
- **conductor1** / `123` (Rol: CONDUCTOR)
- **cliente1** / `123` (Rol: CLIENTE)

## Dependencias

- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- sqlalchemy==2.0.25
- pymysql==1.1.0
- pydantic==2.5.3
- pydantic-settings==2.1.0
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4
- python-multipart==0.0.6
- python-dateutil==2.8.2

## Notas

- Los passwords se almacenan en texto plano (sin encriptación) para desarrollo
- CORS está habilitado para todos los orígenes (solo para desarrollo)
- La base de datos MySQL debe estar ejecutándose antes de iniciar el backend
