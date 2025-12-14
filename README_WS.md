Uncaught TypeError: crypto.randomUUID is not a function
    at jcSWP.~utils/extension-store (seed-guardian.ff2dbca9.js:1:1660)
    at f (seed-guardian.ff2dbca9.js:1:705)
    at jcSWP.~utils/extension-store (seed-guardian.ff2dbca9.js:1:1090)
    at seed-guardian.ff2dbca9.js:1:1253
jcSWP.~utils/extension-store @ seed-guardian.ff2dbca9.js:1
f @ seed-guardian.ff2dbca9.js:1
jcSWP.~utils/extension-store @ seed-guardian.ff2dbca9.js:1
(anónimo) @ seed-guardian.ff2dbca9.js:1Entender este error
recepcion.html:85 WebSocket connection to 'ws://localhost:8000/ws/recepcion' failed: 
connectWebSocket @ recepcion.html:85
sendToOdontologo @ recepcion.html:146
onclick @ recepcion.html:66Entender este error
recepcion.html:105 Error en WebSocket: Event {isTrusted: true, type: 'error', target: WebSocket, currentTarget: WebSocket, eventPhase: 2, …}
wsRecepcion.onerror @ recepcion.html:105Entender este error
recepcion.html:99 Conexión WebSocket para Recepción cerrada
recepcion.html:85 WebSocket connection to 'ws://localhost:8000/ws/recepcion' failed: 
connectWebSocket @ recepcion.html:85
sendToOdontologo @ recepcion.html:146
onclick @ recepcion.html:66Entender este error
recepcion.html:105 Error en WebSocket: Event {isTrusted: true, type: 'error', target: WebSocket, currentTarget: WebSocket, eventPhase: 2, …}
wsRecepcion.onerror @ recepcion.html:105Entender este error
recepcion.html:99 Conexión WebSocket para Recepción cerrada
recepcion.html:85 WebSocket connection to 'ws://localhost:8000/ws/recepcion' failed: 
connectWebSocket @ recepcion.html:85
sendToOdontologo @ recepcion.html:146
onclick @ recepcion.html:67Entender este error
recepcion.html:105 Error en WebSocket: Event {isTrusted: true, type: 'error', target: WebSocket, currentTarget: WebSocket, eventPhase: 2, …}
wsRecepcion.onerror @ recepcion.html:105Entender este error
recepcion.html:99 Conexión WebSocket para Recepción cerrada
# WebSocket Communication System - Readme

## Overview

Sistema de comunicación en tiempo real entre Recepción y Odontólogo para el sistema de gestión de consultorio dental. Implementa conexiones WebSocket con timeout automático y mecanismo de almacenamiento de mensajes pendientes.

## Arquitectura

### Componentes
- **Servidor WebSocket**: Se encarga de gestionar todas las conexiones y el enrutamiento de mensajes
- **Panel de Recepción**: Cliente web que permite enviar notificaciones al odontólogo
- **Panel de Odontólogo**: Cliente web con sistema de verificación de notificaciones pendientes

### Stack Tecnológico
- **Backend**: FastAPI con Uvicorn
- **WebSocket**: Implementación nativa de WebSocket en FastAPI
- **Frontend**: HTML/JavaScript vanilla

## Funcionamiento

### 1. Conexiones Temporales
- Cada conexión WebSocket tiene un timeout de 10 segundos sin actividad
- Si no hay interacción durante este periodo, la conexión se cierra automáticamente
- Las conexiones se restablecen solo cuando el usuario interactúa con los botones

### 2. Almacenamiento de Mensajes Pendientes
- El servidor mantiene dos arrays temporales en memoria para almacenar mensajes:
  - `pending_messages["recepcion"]`: Mensajes pendientes para recepción
  - `pending_messages["odontologo"]`: Mensajes pendientes para odontólogo

### 3. Flujo de Comunicación
1. Cuando un panel envía un mensaje:
   - Si el panel destino está conectado, se envía inmediatamente
   - Si el panel destino está desconectado, se almacena en el array correspondiente

2. Cuando un panel se reconecta:
   - Se entregan todos los mensajes pendientes del array correspondiente
   - Se limpia el array de mensajes pendientes

3. El panel de odontólogo tiene un botón "Verificar Notificaciones" para conectarse y recibir mensajes pendientes

### 4. Notificaciones Visuales
- Indicador visual que se muestra cuando hay mensajes pendientes de recepción
- Mensaje de recordatorio al cargar la página

## Endpoints

- `/recepcion.html` - Panel de recepción
- `/odontologo.html` - Panel de odontólogo
- `/ws/{client_type}` - WebSocket endpoint (client_type: "recepcion" o "odontologo")

## Configuración de Timeout

- **Tiempo de conexión activa**: 10 segundos sin actividad
- **Reconexión automática**: Solo se reconecta al interactuar con botones
- **Almacenamiento temporal**: Mientras un panel está desconectado

## Ventajas del Sistema

1. **Eficiencia de Recursos**: No mantiene conexiones innecesarias
2. **Almacenamiento Temporal**: No se pierden mensajes cuando un panel está desconectado
3. **Simplicidad**: Arquitectura ligera sin dependencias externas
4. **Escalabilidad**: Fácilmente adaptable para múltiples consultorios (SaaS)

## Implementación en el Proyecto Principal

### Consideraciones para Integración

1. **Adaptación a Arquitectura Actual**: Integrar con el sistema de autenticación (FastAPI-Users) y multi-tenant
2. **Modelo de Datos**: Crear modelos para almacenar mensajes históricos si se requiere persistencia
3. **Seguridad**: Asegurar que solo usuarios autenticados puedan acceder al WebSocket
4. **Monitorización**: Agregar logging para operaciones de WebSocket

### Posibles Mejoras Futuras

1. **Sistema de Notificaciones Push**: Para alertar sobre mensajes importantes
2. **Historial de Mensajes**: Almacenamiento en base de datos para auditoría
3. **Configuración de Horarios**: Cierre automático fuera de horario comercial
4. **Múltiples Dispositivos**: Soporte para múltiples sesiones del mismo panel

### Scripts de Implementación

1. Crear modelos para mensajes y notificaciones
2. Integrar WebSocket con el sistema de autenticación actual
3. Adaptar la UI para que se integre con el resto del sistema
4. Agregar middlewares de autenticación y control de tenant
5. Implementar sistema de logging de eventos de comunicación

## Comandos de Ejecución

```bash
cd web_comm
uv venv  # Crear entorno virtual con uv
.venv\Scripts\activate  # Activar entorno
uv pip install fastapi uvicorn  # Instalar dependencias
uvicorn main:app --port 8001  # Iniciar servidor en puerto 8001
```

Acceder a:
- `http://localhost:8001/recepcion.html` - Panel de recepción
- `http://localhost:8001/odontologo.html` - Panel de odontólogo

## Despliegue con Docker

```bash
cd web_comm
docker build -t websocket-app .
docker run -p 8001:8001 websocket-app
```

O con docker-compose:
```bash
cd web_comm
docker-compose up -d
```