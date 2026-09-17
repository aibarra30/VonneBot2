#!/usr/bin/env python3
"""
Vonne Boutique Bot 2.0 - VERSIÓN SIMPLIFICADA
Bot Telegram para Loyverse POS
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from loyverse_connector import LoyverseConnector
from intent_classifier import IntentClassifier
from handlers import VonneHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '867837581:AAG_CBVg_Cg1880ICw-BCw6Wh6cvuB2AA')
LOYVERSE_API_KEY = os.getenv('LOYVERSE_API_KEY', '1476729ba0b44672914cc3af363f4a77')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '-5423371582'))

# Global handler
handler = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    text = (
        "🤖 <b>¡Hola! Soy VonneBot2</b>\n\n"
        "Asistente de Vonne Boutique\n\n"
        "Pregunta por:\n"
        "📦 Stock\n"
        "📊 Ventas\n"
        "💵 Caja\n"
        "🏆 Top productos\n"
        "🎫 Tickets\n\n"
        "/help - Más info"
    )
    await update.message.reply_html(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_html(handler.format_help())


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes normales"""
    if not update.message or not update.message.text:
        return
    
    try:
        await handler.handle_message(update, context)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        try:
            await update.message.reply_text("❌ Error procesando tu mensaje. Intenta de nuevo.")
        except:
            pass


def main():
    """Main function"""
    global handler
    
    logger.info("=" * 70)
    logger.info("🤖 VONNE BOUTIQUE BOT 2.0 - INICIANDO")
    logger.info("=" * 70)
    
    try:
        # Crear handler
        handler = VonneHandler(
            loyverse_api_key=LOYVERSE_API_KEY,
            telegram_token=TELEGRAM_TOKEN,
            group_chat_id=GROUP_CHAT_ID
        )
        logger.info("✅ Handler inicializado")
        
        # Crear aplicación
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        logger.info("✅ Aplicación Telegram creada")
        
        # Agregar handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        logger.info("✅ Handlers registrados")
        
        logger.info("=" * 70)
        logger.info("🚀 BOT ACTIVO - Escuchando mensajes...")
        logger.info("=" * 70)
        
        # Run
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except Exception as e:
        logger.error(f"ERROR FATAL: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
