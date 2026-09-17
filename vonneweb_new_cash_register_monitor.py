"""
Cash Register Monitor
Monitorea el estado de la caja y envía notificaciones de apertura/cierre
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

class CashRegisterMonitor:
    """
    Monitorea el estado de la caja registradora.
    Detecta cambios de estado (abierta/cerrada) y envía notificaciones.
    """
    
    def __init__(self, loyverse_connector, on_opened: Optional[Callable] = None, 
                 on_closed: Optional[Callable] = None, check_interval: int = 30):
        """
        Args:
            loyverse_connector: Instancia de LoyverseConnector
            on_opened: Callback cuando se abre la caja (async function)
            on_closed: Callback cuando se cierra la caja (async function)
            check_interval: Segundos entre checks (por defecto 30)
        """
        self.loyverse = loyverse_connector
        self.on_opened = on_opened
        self.on_closed = on_closed
        self.check_interval = check_interval
        
        self.last_state = None
        self.is_running = False
        self.tz = timezone(timedelta(hours=-6))
    
    async def start_monitoring(self):
        """Inicia el monitoreo continuo"""
        self.is_running = True
        print("[MONITOR] Iniciando monitoreo de caja...")
        
        while self.is_running:
            try:
                await self._check_status()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
                await asyncio.sleep(self.check_interval)
    
    async def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_running = False
        print("[MONITOR] Monitoreo detenido")
    
    async def _check_status(self):
        """Verifica el estado actual de la caja"""
        try:
            cash = self.loyverse.get_cash_register_status()
            
            if "error" in cash:
                print(f"[MONITOR] Error al obtener estado: {cash['error']}")
                return
            
            current_state = cash.get('is_open')
            
            # Detectar cambio de estado
            if self.last_state is None:
                # Primera vez - solo guardar estado
                self.last_state = current_state
                print(f"[MONITOR] Estado inicial: {'ABIERTA' if current_state else 'CERRADA'}")
            
            elif self.last_state != current_state:
                # Cambio detectado
                if current_state:
                    # Caja se ABRIÓ
                    print("[MONITOR] ¡CAJA ABIERTA!")
                    if self.on_opened:
                        await self.on_opened()
                else:
                    # Caja se CERRÓ
                    print("[MONITOR] ¡CAJA CERRADA!")
                    if self.on_closed:
                        await self.on_closed()
                
                self.last_state = current_state
        
        except Exception as e:
            print(f"[MONITOR CHECK ERROR] {e}")


class CashRegisterScheduler:
    """
    Programador de reportes de caja a hora fija
    """
    
    def __init__(self, loyverse_connector, on_schedule_report: Optional[Callable] = None, 
                 report_hour: int = 20, report_minute: int = 0):
        """
        Args:
            loyverse_connector: Instancia de LoyverseConnector
            on_schedule_report: Callback para reporte programado (async function)
            report_hour: Hora del día para enviar reporte (0-23)
            report_minute: Minuto de la hora (0-59)
        """
        self.loyverse = loyverse_connector
        self.on_schedule_report = on_schedule_report
        self.report_hour = report_hour
        self.report_minute = report_minute
        
        self.is_running = False
        self.tz = timezone(timedelta(hours=-6))
        self.last_report_date = None
    
    async def start_scheduler(self):
        """Inicia el scheduler de reportes"""
        self.is_running = True
        print(f"[SCHEDULER] Iniciando scheduler de reportes ({self.report_hour:02d}:{self.report_minute:02d})...")
        
        while self.is_running:
            try:
                await self._check_schedule()
                # Verificar cada minuto
                await asyncio.sleep(60)
            except Exception as e:
                print(f"[SCHEDULER ERROR] {e}")
                await asyncio.sleep(60)
    
    async def stop_scheduler(self):
        """Detiene el scheduler"""
        self.is_running = False
        print("[SCHEDULER] Scheduler detenido")
    
    async def _check_schedule(self):
        """Verifica si es hora de enviar el reporte"""
        now = datetime.now(self.tz)
        
        # Verificar si es la hora programada
        if now.hour == self.report_hour and now.minute == self.report_minute:
            # Verificar que no se haya enviado hoy
            today = now.date()
            
            if self.last_report_date != today:
                print("[SCHEDULER] ¡Es hora del reporte!")
                
                if self.on_schedule_report:
                    await self.on_schedule_report()
                
                self.last_report_date = today


def create_low_stock_report(loyverse_connector) -> str:
    """
    Crea un reporte de prendas con stock bajo
    """
    low_stock = loyverse_connector.get_low_stock_items(threshold=3)
    out_of_stock = loyverse_connector.get_out_of_stock_items()
    
    now = datetime.now(timezone(timedelta(hours=-6)))
    
    response_lines = [
        f"📦 <b>REPORTE DE INVENTARIO</b>\n"
        f"🏪 Vonne Boutique Saltillo\n"
        f"📅 {now.strftime('%A %d de %B de %Y')}\n"
        f"🕐 {now.strftime('%H:%M:%S')}\n"
    ]
    
    # Stock bajo
    if low_stock:
        response_lines.append(f"\n⚠️ <b>PRENDAS CON STOCK BAJO (< 3 pzas):</b>")
        for item in low_stock[:15]:
            qty = item.get("quantity_on_hand", 0)
            name = item.get("name", "")
            response_lines.append(f"• {name}: {qty} pzas")
    else:
        response_lines.append(f"\n✅ <b>No hay prendas con stock bajo</b>")
    
    # Agotados
    if out_of_stock:
        response_lines.append(f"\n🔴 <b>PRENDAS AGOTADAS:</b>")
        for item in out_of_stock[:15]:
            name = item.get("name", "")
            response_lines.append(f"• {name}")
    else:
        response_lines.append(f"\n✅ <b>No hay prendas agotadas</b>")
    
    response_lines.append(f"\n📍 <i>Plaza La Fragua, Saltillo</i>")
    
    return "\n".join(response_lines)


# Pruebas
if __name__ == "__main__":
    print("CashRegisterMonitor y CashRegisterScheduler están listos para usar")
