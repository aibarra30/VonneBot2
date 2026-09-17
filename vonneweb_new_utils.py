"""
Utilidades y funciones auxiliares
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List


def format_currency(value: float, currency: str = "MXN") -> str:
    """Formatea un valor como moneda"""
    return f"${value:,.2f} {currency}"


def format_datetime(dt: datetime, format_str: str = "%d/%m/%Y %H:%M:%S") -> str:
    """Formatea una fecha"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=-6)))
    return dt.strftime(format_str)


def format_percentage(value: float, decimals: int = 1) -> str:
    """Formatea un porcentaje"""
    return f"{value:.{decimals}f}%"


def truncate_string(s: str, max_length: int = 50) -> str:
    """Trunca una cadena a máximo length caracteres"""
    if len(s) > max_length:
        return s[:max_length-3] + "..."
    return s


def group_by(items: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """Agrupa items por una clave"""
    grouped = {}
    for item in items:
        k = item.get(key, "Otro")
        if k not in grouped:
            grouped[k] = []
        grouped[k].append(item)
    return grouped


def sort_by_key(items: List[Dict], key: str, reverse: bool = False) -> List[Dict]:
    """Ordena items por una clave"""
    return sorted(items, key=lambda x: x.get(key, 0), reverse=reverse)


def get_timezone_mex():
    """Obtiene timezone de México CST"""
    return timezone(timedelta(hours=-6))


def get_now_mex():
    """Obtiene hora actual en México"""
    return datetime.now(get_timezone_mex())


def human_readable_duration(seconds: int) -> str:
    """Convierte segundos a formato legible (ej: 1h 30m)"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def escape_html(text: str) -> str:
    """Escapa caracteres HTML"""
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


# Pruebas
if __name__ == "__main__":
    print(f"Hora actual (MX): {format_datetime(get_now_mex())}")
    print(f"Moneda: {format_currency(1500.50)}")
    print(f"Porcentaje: {format_percentage(45.678)}")
    print(f"Duración: {human_readable_duration(5465)}")
