"""
Vonne Boutique Bot 2.0
Bot Telegram inteligente para Loyverse POS
Gestiona: Inventario, Ventas, Caja, Tickets, Notificaciones
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from loyverse_connector import LoyverseConnector
from handlers import VonneHandler
from cash_register_monitor import CashRegisterMonitor, CashRegisterScheduler, create_low_stock_report

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Credenciales (deben estar en variables de entorno)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '867837581:AAG_CBVg_Cg1880ICw-BCw6Wh6cvuB2AA')
LOYVERSE_API_KEY = os.getenv('LOYVERSE_API_KEY', '1476729ba0b44672914cc3af363f4a77')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '-5423371582'))

# Variables globales
vonne_handler = None
cash_monitor = None
cash_scheduler = None
app = None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_html(
        "🤖 <b>¡Hola! Soy VonneBot2</b>\n\n"
        "Asistente inteligente para Vonne Boutique\n\n"
        "Escribe tus preguntas sobre:\n"
        "📦 Inventario\n"
        "📊 Ventas\n"
        "💵 Caja\n"
        "🏆 Productos\n"
        "🎫 Tickets\n\n"
        "/help - Más información"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_html(vonne_handler.format_help())


async def handle_message_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper para manejar mensajes"""
    try:
        await vonne_handler.handle_message(update, context)
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {e}")
        await update.message.reply_text(
            "❌ Hubo un error procesando tu solicitud. Intenta de nuevo."
        )


async def on_cash_opened():
    """Callback cuando se abre la caja"""
    logger.info("[EVENT] Caja abierta - Enviando notificación")
    await vonne_handler.notify_cash_opened()


async def on_cash_closed():
    """Callback cuando se cierra la caja"""
    logger.info("[EVENT] Caja cerrada - Enviando notificación")
    await vonne_handler.notify_cash_closed()


async def on_schedule_report():
    """Callback para reporte programado de stock bajo"""
    logger.info("[SCHEDULE] Reporte de stock bajo - Enviando")
    report = create_low_stock_report(vonne_handler.loyverse)
    await vonne_handler.send_to_group(report)


async def init_background_tasks():
    """Inicia tareas en background (monitoreo de caja, scheduler)"""
    global cash_monitor, cash_scheduler
    
    # Monitor de caja (verifica cada 30 segundos)
    cash_monitor = CashRegisterMonitor(
        vonne_handler.loyverse,
        on_opened=on_cash_opened,
        on_closed=on_cash_closed,
        check_interval=30
    )
    
    # Scheduler de reportes (8 PM diario)
    cash_scheduler = CashRegisterScheduler(
        vonne_handler.loyverse,
        on_schedule_report=on_schedule_report,
        report_hour=20,
        report_minute=0
    )
    
    # Iniciar tareas
    monitor_task = asyncio.create_task(cash_monitor.start_monitoring())
    scheduler_task = asyncio.create_task(cash_scheduler.start_scheduler())
    
    logger.info("[BACKGROUND] Tareas iniciadas: Monitor + Scheduler")
    
    return monitor_task, scheduler_task


async def main():
    """Función principal"""
    global vonne_handler, app
    
    logger.info("=" * 70)
    logger.info("🤖 VONNE BOUTIQUE BOT 2.0 - INICIANDO")
    logger.info("=" * 70)
    
    try:
        # Inicializar manejador
        vonne_handler = VonneHandler(
            loyverse_api_key=LOYVERSE_API_KEY,
            telegram_token=TELEGRAM_TOKEN,
            group_chat_id=GROUP_CHAT_ID
        )
        logger.info(f"✅ Manejador inicializado")
        logger.info(f"   Grupo: {GROUP_CHAT_ID}")
        
        # Crear aplicación Telegram
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Agregar handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_wrapper))
        
        logger.info("✅ Handlers de Telegram registrados")
        
        # Iniciar tareas en background
        asyncio.create_task(init_background_tasks())
        
        # Enviar mensaje de inicio al grupo
        try:
            await vonne_handler.send_to_group(
                "🟢 <b>VONNBOT2 ACTIVO</b>\n\n"
                "Monitoreo de caja: ✅\n"
                "Reportes programados: ✅\n\n"
                "🏪 Vonne Boutique Saltillo\n"
                "📍 Plaza La Fragua"
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al grupo al inicio: {e}")
        
        logger.info("=" * 70)
        logger.info("🚀 BOT LISTO - Escuchando mensajes...")
        logger.info("=" * 70)
        
        # Iniciar polling (sin usar Updater)
        async with app:
            await app.start()
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            # Mantener corriendo
            await asyncio.Event().wait()
    
    except Exception as e:
        logger.error(f"❌ Error en main: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️  Bot detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
