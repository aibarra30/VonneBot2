"""
Intent Classifier
Clasifica semánticamente las intenciones del usuario sin palabras clave literales
"""

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

class IntentClassifier:
    """
    Clasifica intenciones del usuario interpretando variaciones, sinónimos y modismos.
    
    Categorías:
    - stock_bajo: Prendas con poco stock (< 3 piezas)
    - agotados: Prendas sin stock (0 piezas)
    - ventas: Resumen de ventas (hoy, ayer, período, fecha específica)
    - inventario: Stock disponible de prenda específica
    - caja: Estado de caja registradora
    - top_vendidas: Ranking de prendas más vendidas
    - costo_margen: Análisis de costo y ganancia
    - ticket: Búsqueda de recibo específico
    - otra: Cualquier otra cosa
    """
    
    def __init__(self):
        self.tz = timezone(timedelta(hours=-6))  # CST México
    
    def normalize(self, text: str) -> str:
        """Normaliza texto para comparación"""
        if not text:
            return ""
        t = text.lower()
        t = unicodedata.normalize('NFD', t)
        t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
        return t.strip()
    
    def classify(self, user_text: str) -> Tuple[str, float, Dict]:
        """
        Clasifica la intención del usuario.
        
        Returns:
            (intent, confidence, extracted_data)
        """
        
        norm = self.normalize(user_text)
        
        # 1. STOCK BAJO
        if any(w in norm for w in ["stock bajo", "bajo stock", "qué se acaba", 
                                    "qué falta resurtir", "falta resurtir", "prendas por agotarse",
                                    "poco stock", "stock bajo", "inventario bajo"]):
            prenda = self._extract_garment_name(user_text)
            return "stock_bajo", 0.95, {"prenda": prenda}
        
        # 2. AGOTADOS
        if any(w in norm for w in ["agotad", "no hay", "en ceros", "se termino", 
                                    "ya no tengo", "ya no hay", "acabado", "sin stock"]):
            prenda = self._extract_garment_name(user_text)
            return "agotados", 0.90, {"prenda": prenda}
        
        # 3. CAJA
        if any(w in norm for w in ["caja", "efectivo", "dinero", "fondo", 
                                    "estado de caja", "corte de caja", "apertura", "cierre"]):
            return "caja", 0.90, {}
        
        # 4. TOP VENDIDAS
        if any(w in norm for w in ["top", "vendido", "ranking", "bestseller", 
                                    "más vendido", "prendas estrella", "más se vende"]):
            return "top_vendidas", 0.85, {}
        
        # 5. COSTO/MARGEN
        if any(w in norm for w in ["costo", "precio", "margen", "ganancia", 
                                    "cuánto costó", "precio de compra", "cuánto sacamos"]):
            prenda = self._extract_garment_name(user_text)
            return "costo_margen", 0.85, {"prenda": prenda}
        
        # 6. TICKET/RECIBO
        if any(w in norm for w in ["ticket", "recibo", "factura", "folio", "#"]):
            ticket_num = self._extract_ticket_number(user_text)
            return "ticket", 0.90, {"ticket_number": ticket_num}
        
        # 7. VENTAS
        if any(w in norm for w in ["venta", "vendim", "corte", "ingreso", "total", 
                                    "cómo va", "hoy", "ayer", "semana", "mes"]):
            date_context = self._extract_date_context(user_text)
            return "ventas", 0.85, date_context
        
        # 8. INVENTARIO
        if any(w in norm for w in ["inventario", "cuánto hay", "stock", "disponible", 
                                    "hay de", "existe"]):
            prenda = self._extract_garment_name(user_text)
            talla = self._extract_size(user_text)
            return "inventario", 0.80, {"prenda": prenda, "talla": talla}
        
        return "otra", 0.3, {}
    
    def _extract_garment_name(self, text: str) -> str:
        """Extrae nombre de prenda de la consulta"""
        garment_types = [
            "blazer", "vestido", "pantalón", "short", "blusa", "falda",
            "traje de baño", "camiseta", "camisa", "chaleco", "chaqueta",
            "abrigo", "sweater", "cardigan", "leggings", "jeans"
        ]
        
        norm = self.normalize(text)
        
        for garment in garment_types:
            if garment in norm:
                # Intenta extraer más detalles
                match = re.search(rf'({garment}[^,\.]*)', text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                return garment
        
        return ""
    
    def _extract_size(self, text: str) -> str:
        """Extrae talla de la consulta"""
        sizes = ["ch", "m", "g", "xl", "xxl"]
        norm = self.normalize(text)
        
        for size in sizes:
            if f"talla {size}" in norm or f"tamaño {size}" in norm or f" {size} " in norm:
                return size.upper()
        
        return ""
    
    def _extract_date_context(self, text: str) -> Dict:
        """Extrae contexto de fecha"""
        norm = self.normalize(text)
        
        # Períodos predefinidos
        if "hoy" in norm:
            return {"period": "today", "type": "predefined"}
        elif "ayer" in norm:
            return {"period": "yesterday", "type": "predefined"}
        elif "semana" in norm:
            return {"period": "week", "type": "predefined"}
        elif "mes" in norm:
            return {"period": "month", "type": "predefined"}
        elif "últimos" in norm and "7" in norm:
            return {"period": "last_7_days", "type": "predefined"}
        elif "últimos" in norm and "30" in norm:
            return {"period": "last_30_days", "type": "predefined"}
        
        return {"period": "today", "type": "default"}
    
    def _extract_ticket_number(self, text: str) -> str:
        """Extrae número de ticket/folio"""
        # Busca patrones como: #123, ticket 123, folio 123, etc.
        match = re.search(r'(?:#|ticket|folio|recibo)\s*(\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Si no encontró, busca cualquier número de 1-5 dígitos
        match = re.search(r'\b(\d{1,5})\b', text)
        if match:
            return match.group(1)
        
        return ""


# Pruebas
if __name__ == "__main__":
    classifier = IntentClassifier()
    
    test_queries = [
        "que tenemos en stock bajo?",
        "qué prendas se están acabando?",
        "agotados",
        "cuánto vendimos hoy?",
        "ventas de ayer",
        "cuánto costó el blazer?",
        "cómo está la caja?",
        "top de prendas más vendidas",
        "detalle del ticket 1234",
        "saber inventario de blazer en talla XXL"
    ]
    
    print("=" * 70)
    print("PRUEBAS DE CLASIFICACIÓN DE INTENCIONES")
    print("=" * 70)
    
    for query in test_queries:
        intent, confidence, extracted = classifier.classify(query)
        print(f"\n📝 '{query}'")
        print(f"   └─ Intención: {intent} (conf: {confidence:.2f})")
        if extracted:
            print(f"   └─ Datos: {extracted}")
