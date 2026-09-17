"""
Telegram Message Handlers
Procesa mensajes y envía respuestas formateadas
"""

from telegram import Update, Bot
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from datetime import datetime, timedelta, timezone
from typing import Optional

from loyverse_connector import LoyverseConnector
from intent_classifier import IntentClassifier


class VonneHandler:
    """
    Manejador principal de mensajes del bot Vonne
    """
    
    def __init__(self, loyverse_api_key: str, telegram_token: str, group_chat_id: int):
        self.loyverse = LoyverseConnector(loyverse_api_key)
        self.classifier = IntentClassifier()
        self.telegram_token = telegram_token
        self.group_chat_id = group_chat_id
        self.bot = Bot(token=telegram_token)
        self.tz = timezone(timedelta(hours=-6))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensaje del usuario"""
        user_text = update.message.text
        chat_id = update.message.chat_id
        
        print(f"[MSG] {update.message.from_user.username}: {user_text}")
        
        # Clasificar intención
        intent, confidence, extracted = self.classifier.classify(user_text)
        
        print(f"[INTENT] {intent} (conf: {confidence:.2f})")
        
        # Procesar según intención
        if intent == "stock_bajo":
            response = await self.handle_low_stock(extracted)
        
        elif intent == "agotados":
            response = await self.handle_out_of_stock(extracted)
        
        elif intent == "ventas":
            response = await self.handle_sales_query(extracted)
        
        elif intent == "inventario":
            response = await self.handle_inventory_query(extracted)
        
        elif intent == "caja":
            response = await self.handle_cash_register()
        
        elif intent == "top_vendidas":
            response = await self.handle_top_sellers()
        
        elif intent == "costo_margen":
            response = await self.handle_cost_margin(extracted)
        
        elif intent == "ticket":
            response = await self.handle_ticket_search(extracted)
        
        else:
            response = self.format_help()
        
        # Enviar respuesta
        await context.bot.send_message(chat_id=chat_id, text=response, parse_mode="HTML")
    
    # ========== HANDLERS ==========
    
    async def handle_low_stock(self, extracted: dict) -> str:
        """Maneja consultas de stock bajo"""
        prenda = extracted.get("prenda", "")
        
        low_stock = self.loyverse.get_low_stock_items(threshold=3)
        
        if prenda:
            # Filtrar por prenda específica
            low_stock = [
                item for item in low_stock 
                if prenda.lower() in item.get("name", "").lower()
            ]
        
        if not low_stock:
            return "✅ <b>Buen Inventario</b>\nNo hay prendas con stock bajo. Todos los productos tienen suficiente cantidad en stock."
        
        response_lines = [
            "⚠️ <b>CONTROL DE INVENTARIO - STOCK BAJO</b>\n"
            "🏪 Vonne Boutique Saltillo\n"
        ]
        
        for item in low_stock[:15]:
            qty = item.get("quantity_on_hand", 0)
            name = item.get("name", "Desconocido")
            response_lines.append(f"• {name}: {qty} pzas")
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    async def handle_out_of_stock(self, extracted: dict) -> str:
        """Maneja consultas de productos agotados"""
        prenda = extracted.get("prenda", "")
        
        agotados = self.loyverse.get_out_of_stock_items()
        
        if prenda:
            agotados = [
                item for item in agotados 
                if prenda.lower() in item.get("name", "").lower()
            ]
        
        if not agotados:
            return "✅ <b>Todos en Stock</b>\nNo hay productos agotados en este momento."
        
        response_lines = [
            "🔴 <b>PRODUCTOS AGOTADOS</b>\n"
            "🏪 Vonne Boutique Saltillo\n"
        ]
        
        for item in agotados[:15]:
            name = item.get("name", "Desconocido")
            response_lines.append(f"• {name}")
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    async def handle_sales_query(self, extracted: dict) -> str:
        """Maneja consultas de ventas"""
        period = extracted.get("period", "today")
        
        if period == "yesterday":
            yesterday = datetime.now(self.tz) - timedelta(days=1)
            sales = self.loyverse.get_day_sales_summary(yesterday)
            title = f"VENTAS DE AYER - {sales['date']}"
        elif period == "week":
            sales = self.loyverse.get_period_sales_summary(7)
            title = "VENTAS - ÚLTIMOS 7 DÍAS"
        elif period == "month":
            sales = self.loyverse.get_period_sales_summary(30)
            title = "VENTAS - ÚLTIMOS 30 DÍAS"
        else:  # today
            sales = self.loyverse.get_day_sales_summary()
            title = f"VENTAS DE HOY - {sales['date']}"
        
        if "error" in sales:
            return f"❌ Error: {sales['error']}"
        
        response_lines = [
            f"📊 <b>{title}</b>\n"
            f"🏪 Vonne Boutique Saltillo\n",
            f"💰 <b>Ventas Totales:</b> ${sales['total_sales']:,.2f} MXN",
            f"🎫 <b>Tickets:</b> {sales['num_transactions']}",
            f"📦 <b>Prendas Vendidas:</b> {sales['num_items_sold']}",
        ]
        
        if sales['num_transactions'] > 0:
            response_lines.append(f"📈 <b>Ticket Promedio:</b> ${sales['average_ticket']:,.2f} MXN")
        
        if sales.get("payment_methods"):
            response_lines.append("\n💳 <b>FORMAS DE PAGO:</b>")
            for method, amount in sales['payment_methods'].items():
                response_lines.append(f"• {method}: ${amount:,.2f} MXN")
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    async def handle_inventory_query(self, extracted: dict) -> str:
        """Maneja consultas de inventario"""
        prenda = extracted.get("prenda", "")
        talla = extracted.get("talla", "")
        
        if not prenda:
            # Resumen general
            items = self.loyverse.get_items(limit=200)
            total_qty = sum(item.get("quantity_on_hand", 0) for item in items)
            total_items = len(items)
            
            return (
                f"📦 <b>RESUMEN DE INVENTARIO</b>\n"
                f"🏪 Vonne Boutique Saltillo\n\n"
                f"👗 Prendas Registradas: {total_items}\n"
                f"📦 Cantidad Total: {total_qty} piezas\n\n"
                f"📍 <i>Plaza La Fragua, Saltillo</i>"
            )
        
        matches = self.loyverse.search_item_by_name(prenda)
        
        if not matches:
            return f"❌ No encontré '{prenda}'. Intenta con el nombre exacto o más corto."
        
        response_lines = [
            f"📦 <b>INVENTARIO EN TIENDA</b>\n"
            f"🏪 Vonne Boutique Saltillo\n"
            f"🔎 Búsqueda: {prenda}\n"
        ]
        
        for item in matches[:5]:
            name = item.get("name", "")
            qty = item.get("quantity_on_hand", 0)
            sku = item.get("sku", "")
            
            response_lines.append(f"\n• <b>{name}</b> ({sku})")
            response_lines.append(f"  📦 Stock: {qty} pzas")
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    async def handle_cash_register(self) -> str:
        """Maneja consultas de caja"""
        cash = self.loyverse.get_cash_register_status()
        
        if "error" in cash:
            return f"❌ Error: {cash['error']}"
        
        status = "🟢 ABIERTA" if cash['is_open'] else "🔴 CERRADA"
        
        return (
            f"💵 <b>ESTADO DE CAJA</b>\n"
            f"🏪 Vonne Boutique Saltillo\n\n"
            f"Estado: {status}\n"
            f"Saldo Inicial: ${cash['opening_balance']:,.2f} MXN\n"
            f"Total Actual: ${cash['total_cash']:,.2f} MXN\n\n"
            f"📍 <i>Plaza La Fragua, Saltillo</i>"
        )
    
    async def handle_top_sellers(self) -> str:
        """Maneja consultas de productos más vendidos"""
        top = self.loyverse.get_top_sellers(days=30, limit=10)
        
        if not top:
            return "❌ No hay datos de ventas"
        
        response_lines = [
            "🏆 <b>PRODUCTOS MÁS VENDIDOS - ÚLTIMOS 30 DÍAS</b>\n"
            "🏪 Vonne Boutique Saltillo\n"
        ]
        
        for i, item in enumerate(top, 1):
            response_lines.append(
                f"\n{i}. <b>{item['name']}</b>\n"
                f"   • Vendidas: {item['quantity_sold']} pzas\n"
                f"   • Ingresos: ${item['revenue']:,.2f} MXN"
            )
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    async def handle_cost_margin(self, extracted: dict) -> str:
        """Maneja consultas de costo y margen"""
        prenda = extracted.get("prenda", "")
        
        if not prenda:
            return "❌ Especifica qué prenda deseas analizar"
        
        matches = self.loyverse.search_item_by_name(prenda)
        
        if not matches:
            return f"❌ No encontré '{prenda}'"
        
        response_lines = [
            "💰 <b>ANÁLISIS DE COSTO Y MARGEN</b>\n"
            "🏪 Vonne Boutique Saltillo\n"
        ]
        
        for item in matches[:3]:
            name = item.get("name", "")
            # Nota: Loyverse API puede no exponer costo directamente
            # Aquí asumimos que está en los datos
            response_lines.append(f"\n• <b>{name}</b>")
            response_lines.append(f"  Precio Venta: ${item.get('price', 0):,.2f} MXN")
            response_lines.append(f"  [Costo no disponible en API]")
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    async def handle_ticket_search(self, extracted: dict) -> str:
        """Maneja búsqueda de tickets"""
        ticket_num = extracted.get("ticket_number", "")
        
        if not ticket_num:
            return "❌ Especifica el número del ticket (ej: #1234)"
        
        receipt = self.loyverse.search_receipt_by_number(ticket_num)
        
        if not receipt:
            return f"❌ No encontré el ticket #{ticket_num}"
        
        response_lines = [
            f"🎫 <b>DETALLES DEL TICKET #{receipt.get('number', ticket_num)}</b>\n"
            f"🏪 Vonne Boutique Saltillo\n"
        ]
        
        response_lines.append(f"Fecha: {receipt.get('created_at', 'N/A')[:10]}")
        response_lines.append(f"Total: ${receipt.get('total', 0):,.2f} MXN")
        response_lines.append(f"\n📦 <b>Prendas:</b>")
        
        for line_item in receipt.get('line_items', [])[:10]:
            name = line_item.get('name', 'Desconocido')
            qty = line_item.get('quantity', 0)
            total = line_item.get('total', 0)
            response_lines.append(f"• {name} x{qty}: ${total:,.2f} MXN")
        
        response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
        
        return "\n".join(response_lines)
    
    def format_help(self) -> str:
        """Menú de ayuda"""
        return (
            "🤖 <b>Asistente Vonne Boutique</b>\n\n"
            "Entiendo preguntas sobre:\n\n"
            "📦 <b>Inventario:</b> 'Stock bajo', 'Qué falta resurtir', 'Agotados'\n"
            "📊 <b>Ventas:</b> 'Cuánto vendimos hoy', 'Ventas de ayer'\n"
            "💵 <b>Caja:</b> 'Cómo está la caja', 'Estado de caja'\n"
            "🏆 <b>Top:</b> 'Prendas más vendidas', 'Bestsellers'\n"
            "💰 <b>Costos:</b> 'Cuánto costó este vestido'\n"
            "🎫 <b>Tickets:</b> 'Detalle del ticket 1234'\n\n"
            "📍 <i>Plaza La Fragua, Saltillo</i>"
        )
    
    async def send_to_group(self, message: str):
        """Envía mensaje al grupo"""
        try:
            await self.bot.send_message(
                chat_id=self.group_chat_id,
                text=message,
                parse_mode="HTML"
            )
        except TelegramError as e:
            print(f"[ERROR] No se pudo enviar al grupo: {e}")
    
    async def notify_cash_opened(self):
        """Notifica apertura de caja"""
        cash = self.loyverse.get_cash_register_status()
        
        message = (
            "🟢 <b>CAJA ABIERTA</b>\n"
            "🏪 Vonne Boutique Saltillo\n\n"
            f"Saldo Inicial: ${cash.get('opening_balance', 0):,.2f} MXN\n"
            f"Hora: {datetime.now(self.tz).strftime('%H:%M:%S')}\n\n"
            "¡Listos para vender! 💰"
        )
        
        await self.send_to_group(message)
    
    async def notify_cash_closed(self):
        """Notifica cierre de caja"""
        cash = self.loyverse.get_cash_register_status()
        today_sales = self.loyverse.get_day_sales_summary()
        
        message = (
            "🔴 <b>CAJA CERRADA</b>\n"
            "🏪 Vonne Boutique Saltillo\n\n"
            f"Total Caja: ${cash.get('total_cash', 0):,.2f} MXN\n"
            f"Ventas Hoy: ${today_sales['total_sales']:,.2f} MXN\n"
            f"Tickets: {today_sales['num_transactions']}\n"
            f"Hora: {datetime.now(self.tz).strftime('%H:%M:%S')}\n\n"
            "¡Buen día de ventas!"
        )
        
        await self.send_to_group(message)
