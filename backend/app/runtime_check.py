import os

def is_vercel_environment() -> bool:
    """Проверяет, выполняется ли код в среде Vercel"""
    return bool(os.environ.get('VERCEL_ENV'))