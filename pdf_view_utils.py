"""
PDF Viewer - Yardımcı Fonksiyonlar ve Genel Araçlar
"""

import traceback
import sys
from datetime import datetime

# Global error handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler - hataları hem terminale hem de dosyaya yaz"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Terminale yazdır
    print(f"\n{'='*50}")
    print(f"HATA YAKALANDI: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print(f"{'='*50}")
    print(error_msg)
    print(f"{'='*50}\n")
    
    # Log dosyasına yaz
    try:
        with open("pdf_viewer_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"HATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n")
            f.write(error_msg)
            f.write(f"{'='*50}\n")
    except:
        pass


def setup_global_exception_handler():
    """Global exception handler'ı ayarla"""
    sys.excepthook = handle_exception


def init_error_log():
    """Error log dosyasını başlat"""
    try:
        with open("pdf_viewer_errors.log", "w", encoding="utf-8") as f:
            f.write(f"PDF Viewer Error Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
    except:
        pass


def center_window(window, width, height):
    """Pencereyi ekranın ortasına yerleştir"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
