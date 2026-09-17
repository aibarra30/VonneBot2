"""
Loyverse API Connector
Maneja todas las conexiones y consultas a la API de Loyverse POS
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

class LoyverseConnector:
    """
    Conector para la API de Loyverse.
    Maneja inventario, ventas, caja, tickets y reportes.
    """
    
    BASE_URL = "https://api.loyverse.com/v1.0"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.tz = timezone(timedelta(hours=-6))  # CST México
    
    def _request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """
        Realiza una petición a la API de Loyverse
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == "POST":
                resp = requests.post(url, headers=self.headers, json=params, timeout=10)
            else:
                return {"error": f"Método {method} no soportado"}
            
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            return {"error": "Timeout - API de Loyverse tardó demasiado"}
        except requests.exceptions.ConnectionError:
            return {"error": "Error de conexión - Verifica tu conexión a internet"}
        except requests.exceptions.HTTPError as e:
            return {"error": f"Error HTTP: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Error inesperado: {str(e)}"}
    
    # ========== INVENTARIO ==========
    
    def get_items(self, limit: int = 100) -> List[Dict]:
        """Obtiene lista de productos (items) del inventario"""
        response = self._request("GET", "/items", {"limit": limit})
        return response.get("items", [])
    
    def get_item(self, item_id: str) -> Dict:
        """Obtiene detalles de un producto específico"""
        return self._request("GET", f"/items/{item_id}")
    
    def search_item_by_name(self, query: str) -> List[Dict]:
        """Busca productos por nombre/descripción"""
        items = self.get_items(limit=200)
        query_norm = query.lower()
        matches = [
            item for item in items 
            if query_norm in item.get("name", "").lower() or 
               query_norm in item.get("sku", "").lower()
        ]
        return matches
    
    def get_low_stock_items(self, threshold: int = 3) -> List[Dict]:
        """Obtiene productos con stock bajo (< threshold)"""
        items = self.get_items(limit=200)
        low_stock = [
            item for item in items 
            if item.get("quantity_on_hand", 0) < threshold and 
               item.get("quantity_on_hand", 0) > 0
        ]
        return sorted(low_stock, key=lambda x: x.get("quantity_on_hand", 0))
    
    def get_out_of_stock_items(self) -> List[Dict]:
        """Obtiene productos agotados (stock = 0)"""
        items = self.get_items(limit=200)
        return [item for item in items if item.get("quantity_on_hand", 0) == 0]
    
    # ========== VENTAS & RECEIPTS ==========
    
    def get_receipts(self, from_date: datetime = None, to_date: datetime = None, limit: int = 100) -> List[Dict]:
        """Obtiene lista de recibos/tickets de venta"""
        params = {"limit": limit}
        
        if from_date:
            params["from_date"] = from_date.isoformat()
        if to_date:
            params["to_date"] = to_date.isoformat()
        
        response = self._request("GET", "/receipts", params)
        return response.get("receipts", [])
    
    def get_receipt(self, receipt_id: str) -> Dict:
        """Obtiene detalles de un recibo específico"""
        return self._request("GET", f"/receipts/{receipt_id}")
    
    def get_day_sales_summary(self, date: datetime = None) -> Dict:
        """Obtiene resumen de ventas de un día"""
        if date is None:
            date = datetime.now(self.tz)
        
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        receipts = self.get_receipts(from_date=start, to_date=end, limit=500)
        
        total_sales = 0
        total_items = 0
        num_transactions = len(receipts)
        payment_methods = {}
        
        for receipt in receipts:
            # Solo contar recibos completados (no anulados)
            if receipt.get("status") == "closed":
                total_sales += float(receipt.get("total", 0))
                total_items += len(receipt.get("line_items", []))
                
                payment_type = receipt.get("payment_type", "Efectivo")
                if payment_type not in payment_methods:
                    payment_methods[payment_type] = 0
                payment_methods[payment_type] += float(receipt.get("total", 0))
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_sales": total_sales,
            "num_transactions": num_transactions,
            "num_items_sold": total_items,
            "average_ticket": total_sales / num_transactions if num_transactions > 0 else 0,
            "payment_methods": payment_methods
        }
    
    def get_period_sales_summary(self, days: int = 7) -> Dict:
        """Obtiene resumen de ventas de últimos N días"""
        end_date = datetime.now(self.tz)
        start_date = end_date - timedelta(days=days)
        
        receipts = self.get_receipts(from_date=start_date, to_date=end_date, limit=1000)
        
        total_sales = 0
        daily_sales = {}
        
        for receipt in receipts:
            if receipt.get("status") == "closed":
                date_key = receipt.get("created_at", "")[:10]
                amount = float(receipt.get("total", 0))
                total_sales += amount
                
                if date_key not in daily_sales:
                    daily_sales[date_key] = 0
                daily_sales[date_key] += amount
        
        return {
            "period": f"Últimos {days} días",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_sales": total_sales,
            "days_with_sales": len(daily_sales),
            "average_daily_sales": total_sales / max(len(daily_sales), 1),
            "daily_breakdown": daily_sales
        }
    
    def search_receipt_by_number(self, receipt_number: str) -> Optional[Dict]:
        """Busca un recibo por número/folio"""
        receipts = self.get_receipts(limit=500)
        
        for receipt in receipts:
            if str(receipt.get("number", "")) == str(receipt_number):
                return receipt
        
        return None
    
    # ========== CAJA ==========
    
    def get_cash_registers(self) -> List[Dict]:
        """Obtiene lista de cajas registradoras"""
        response = self._request("GET", "/cash_registers")
        return response.get("cash_registers", [])
    
    def get_cash_register_status(self) -> Dict:
        """Obtiene estado actual de la caja"""
        cash_registers = self.get_cash_registers()
        
        if not cash_registers:
            return {"error": "No hay cajas registradas"}
        
        # Asumir que hay una sola caja principal
        cash_register = cash_registers[0]
        
        return {
            "id": cash_register.get("id"),
            "name": cash_register.get("name"),
            "is_open": cash_register.get("is_open", False),
            "opening_balance": float(cash_register.get("opening_balance", 0)),
            "total_cash": float(cash_register.get("total_cash", 0))
        }
    
    # ========== REPORTES ==========
    
    def get_top_sellers(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Obtiene productos más vendidos"""
        end_date = datetime.now(self.tz)
        start_date = end_date - timedelta(days=days)
        
        receipts = self.get_receipts(from_date=start_date, to_date=end_date, limit=1000)
        
        item_sales = {}
        
        for receipt in receipts:
            if receipt.get("status") == "closed":
                for line_item in receipt.get("line_items", []):
                    item_name = line_item.get("name", "Desconocido")
                    quantity = int(line_item.get("quantity", 0))
                    
                    if item_name not in item_sales:
                        item_sales[item_name] = {
                            "quantity": 0,
                            "revenue": 0
                        }
                    
                    item_sales[item_name]["quantity"] += quantity
                    item_sales[item_name]["revenue"] += float(line_item.get("total", 0))
        
        # Ordenar por cantidad vendida
        sorted_items = sorted(
            item_sales.items(),
            key=lambda x: x[1]["quantity"],
            reverse=True
        )
        
        return [
            {
                "name": name,
                "quantity_sold": data["quantity"],
                "revenue": data["revenue"]
            }
            for name, data in sorted_items[:limit]
        ]


# Prueba de conexión
if __name__ == "__main__":
    API_KEY = "1476729ba0b44672914cc3af363f4a77"
    connector = LoyverseConnector(API_KEY)
    
    print("Testing Loyverse Connector...")
    print("\n=== Items ===")
    items = connector.get_items(limit=5)
    print(f"Total items: {len(items)}")
    
    print("\n=== Low Stock ===")
    low_stock = connector.get_low_stock_items(threshold=3)
    print(f"Items with low stock: {len(low_stock)}")
    
    print("\n=== Day Sales ===")
    today_sales = connector.get_day_sales_summary()
    print(f"Today sales: ${today_sales.get('total_sales', 0):.2f} MXN")
    
    print("\n=== Cash Register ===")
    cash = connector.get_cash_register_status()
    print(f"Cash register open: {cash.get('is_open', False)}")
