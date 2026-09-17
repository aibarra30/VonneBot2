"""
Vonne Boutique Bot 2.0
Bot Telegram inteligente para Loyverse POS
Versión simplificada - python-telegram-bot 20.7
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from loyverse_connector import LoyverseConnector
from handlers import VonneHandler

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
        try:
            await update.message.reply_text(
                "❌ Hubo un error procesando tu solicitud. Intenta de nuevo."
            )
        except:
            pass


def main():
    """Función principal - versión simplificada"""
    
    logger.info("=" * 70)
    logger.info("🤖 VONNE BOUTIQUE BOT 2.0 - INICIANDO")
    logger.info("=" * 70)
    
    global vonne_handler
    
    try:
        # Inicializar manejador
        vonne_handler = VonneHandler(
            loyverse_api_key=LOYVERSE_API_KEY,
            telegram_token=TELEGRAM_TOKEN,
            group_chat_id=GROUP_CHAT_ID
        )
        logger.info(f"✅ Manejador inicializado")
        logger.info(f"   Token: ✓")
        logger.info(f"   API Key: ✓")
        logger.info(f"   Grupo: {GROUP_CHAT_ID}")
        
        # Crear aplicación Telegram
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Agregar handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_wrapper))
        
        logger.info("✅ Handlers registrados")
        
        logger.info("=" * 70)
        logger.info("🚀 BOT LISTO - Polling iniciado...")
        logger.info("=" * 70)
        
        # Ejecutar bot
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️  Bot detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
