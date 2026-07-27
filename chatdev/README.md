# ChatDev Web Interface

Frontend React + Vite para ChatDev Assistant.

## Instalación

```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build
npm run build

# Preview
npm run preview
```

## Estructura

```
src/
├── components/      # Componentes React
├── stores/          # Estado global (Zustand)
├── utils/           # Servicios (WebSocket, etc.)
├── App.jsx          # Componente raíz
├── main.jsx         # Punto de entrada
└── index.css        # Estilos globales
```

## Características

- ✅ Autenticación JWT
- ✅ WebSocket Secure (WSS)
- ✅ Chat en tiempo real
- ✅ Indicadores de fase [PLANEAMIENTO]/[EJECUCIÓN]
- ✅ Información de modelo y rol
- ✅ Exportar conversaciones
- ✅ Modo oscuro/claro
- ✅ Historial de chats

## Conectar con Backend

El servidor FastAPI debe estar en `http://localhost:8000` con:
- `POST /auth/login` - Obtener token JWT
- `WebSocket /ws?token=...` - Conexión WebSocket autenticada

## Requisitos

- Node.js 16+
- npm o yarn
