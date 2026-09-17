#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from loyverse_connector import LoyverseConnector
from intent_classifier import IntentClassifier
from handlers import VonneHandler

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '867837581:AAG_CBVg_Cg1880ICw-BCw6Wh6cvuB2AA')
LOYVERSE_API_KEY = os.getenv('LOYVERSE_API_KEY', '1476729ba0b44672914cc3af363f4a77')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '-5423371582'))

handler = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🤖 <b>¡Hola! Soy VonneBot2</b>\n\nAsistente de Vonne Boutique\n\nPregunta por:\n📦 Stock\n📊 Ventas\n💵 Caja\n/help - Más info"
    await update.message.reply_html(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(handler.format_help())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    try:
        await handler.handle_message(update, context)
    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            await update.message.reply_text("❌ Error. Intenta de nuevo.")
        except:
            pass

def main():
    global handler
    logger.info("🤖 VONNE BOT 2.0 - INICIANDO")
    
    try:
        handler = VonneHandler(loyverse_api_key=LOYVERSE_API_KEY, telegram_token=TELEGRAM_TOKEN, group_chat_id=GROUP_CHAT_ID)
        logger.info("✅ Handler OK")
        
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        logger.info("✅ App OK")
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        logger.info("✅ Handlers OK")
        
        logger.info("🚀 BOT ACTIVO")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"ERROR: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
