# 🤖 Vonne Boutique Bot 2.0

Bot inteligente de Telegram para Loyverse POS

Gestiona inventario, ventas, caja, tickets y notificaciones automáticas de apertura/cierre.

---

## 🚀 Características

✅ **Consultas de Inventario**
- Stock disponible
- Prendas con stock bajo (< 3 pzas)
- Productos agotados
- Búsqueda por prenda/talla

✅ **Resumen de Ventas**
- Ventas de hoy
- Ventas de ayer
- Últimos 7/30 días
- Desglose por forma de pago
- Ticket promedio

✅ **Estado de Caja**
- Apertura/cierre automático
- Saldo actual
- Notificaciones en tiempo real

✅ **Productos Más Vendidos**
- Ranking de últimos 30 días
- Cantidad vendida e ingresos

✅ **Análisis de Costos**
- Precio de venta
- Costo de adquisición
- Margen de ganancia

✅ **Búsqueda de Tickets**
- Detalles de recibos específicos
- Prendas y totales

✅ **Reportes Automáticos**
- Notificación de apertura de caja
- Notificación de cierre de caja
- Reporte diario de stock bajo (8 PM)

---

## 📋 Estructura del Proyecto

```
vonneweb-bot-2.0/
├── main.py                      # Entrada del bot
├── loyverse_connector.py        # Conexión a API Loyverse
├── intent_classifier.py         # Clasificación semántica de intenciones
├── handlers.py                  # Manejadores de Telegram
├── cash_register_monitor.py     # Monitor de apertura/cierre de caja
├── utils.py                     # Funciones auxiliares
├── requirements.txt             # Dependencias Python
└── README.md                    # Este archivo
```

---

## 🔧 Instalación Local

### Requisitos
- Python 3.8+
- pip

### Pasos

1. **Clona o descarga el proyecto**
   ```bash
   cd vonneweb-bot-2.0
   ```

2. **Instala dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura variables de entorno** (crear archivo `.env`)
   ```
   TELEGRAM_TOKEN=867837581:AAG_CBVg_Cg1880ICw-BCw6Wh6cvuB2AA
   LOYVERSE_API_KEY=1476729ba0b44672914cc3af363f4a77
   GROUP_CHAT_ID=-5423371582
   ```

4. **Ejecuta el bot**
   ```bash
   python main.py
   ```

---

## 🌐 Despliegue en Render

### Paso 1: Prepara el Repositorio

1. Sube los archivos a un repositorio de GitHub

2. Crea un archivo `.env.example` (SIN valores reales)
   ```
   TELEGRAM_TOKEN=<tu_token>
   LOYVERSE_API_KEY=<tu_api_key>
   GROUP_CHAT_ID=<tu_group_id>
   ```

### Paso 2: Crea un Servicio en Render

1. Ve a https://dashboard.render.com
2. Click en **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Configura:
   - **Name:** `vonneweb-bot-2`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Region:** Cualquiera (recomendado: Oregón USA)

### Paso 3: Agrega Variables de Entorno

1. En Render, ve a tu servicio → **Environment**
2. Agrega:
   - **TELEGRAM_TOKEN** → `867837581:AAG_CBVg_Cg1880ICw-BCw6Wh6cvuB2AA`
   - **LOYVERSE_API_KEY** → `1476729ba0b44672914cc3af363f4a77`
   - **GROUP_CHAT_ID** → `-5423371582`

### Paso 4: Deploy

1. Click en **"Create Web Service"**
2. Espera a que termine el despliegue (~3 minutos)
3. Verifica que diga ✅ "Live"

---

## 💬 Comandos del Bot

### Comandos Registrados
- `/start` - Inicia el bot
- `/help` - Muestra ayuda

### Ejemplos de Consultas Naturales

**Inventario:**
- "que tenemos en stock bajo?"
- "prendas agotadas"
- "inventario de blazer en talla XXL"

**Ventas:**
- "cuánto vendimos hoy?"
- "ventas de ayer"
- "ventas de los últimos 7 días"

**Caja:**
- "cómo está la caja?"
- "estado de caja"

**Productos:**
- "top de más vendidas"
- "prendas bestseller"

**Tickets:**
- "detalle del ticket 1234"
- "recibo #567"

**Costos:**
- "cuánto costó el vestido?"
- "margen del blazer"

---

## 📊 Notificaciones Automáticas

### Apertura de Caja
Se envía al grupo cuando Loyverse detecta apertura:
```
🟢 CAJA ABIERTA
Saldo Inicial: $XXX MXN
¡Listos para vender! 💰
```

### Cierre de Caja
Se envía al grupo cuando se cierra la caja:
```
🔴 CAJA CERRADA
Total Caja: $XXX MXN
Ventas Hoy: $XXX MXN
Tickets: N
```

### Reporte de Stock Bajo (8 PM diario)
```
📦 REPORTE DE INVENTARIO
⚠️ PRENDAS CON STOCK BAJO:
• Blazer Rosa: 2 pzas
• Vestido Mini: 1 pza
...
```

---

## 🔑 Credenciales Requeridas

### Loyverse API Key
- Obtener en: https://loyverse.com/api
- Referencia: `1476729ba0b44672914cc3af363f4a77`

### Token de Bot Telegram
- Crear en: @BotFather en Telegram
- Bot actual: `VonneBot2_Bot`
- Token: `867837581:AAG_CBVg_Cg1880ICw-BCw6Wh6cvuB2AA`

### Group Chat ID
- Obtener en: @userinfobot en el grupo
- Grupo Vonne: `-5423371582`

---

## 🛠️ Troubleshooting

### Bot no responde
1. Verifica que Render esté en ✅ "Live"
2. Verifica que el TELEGRAM_TOKEN sea correcto
3. Comprueba los logs en Render

### No se envían notificaciones de caja
1. Verifica GROUP_CHAT_ID
2. Asegúrate que el bot esté agregado al grupo
3. Revisa los logs de monitoreo

### API Loyverse lenta
- Loyverse puede tardar 10+ segundos en responder
- El bot tiene timeout de 10 segundos
- Si falla, intenta de nuevo

---

## 📝 Logs

El bot escribe logs en consola con formato:
```
[2026-09-17 15:30:45] INFO - Mensaje recibido: "que tenemos en stock bajo?"
[2026-09-17 15:30:46] INFO - Intención: stock_bajo (conf: 0.95)
[2026-09-17 15:30:47] INFO - Respuesta enviada
```

Para ver logs en Render:
https://dashboard.render.com → VonneWeb → Logs

---

## 🔄 Actualizaciones

Para actualizar el bot:

1. Haz cambios en tu código local
2. Sube a GitHub
3. Render redeploy automático (~3 minutos)

---

## 📞 Soporte

Para problemas:
1. Revisa los logs
2. Verifica credenciales en Render Environment
3. Comprueba que el grupo existe y el bot está agregado

---

**Versión:** 2.0  
**Última actualización:** 17 de Septiembre, 2026  
**Bot:** VonneBot2_Bot  
**Grupo:** Vonne Boutique  
**Ubicación:** Plaza La Fragua, Saltillo
