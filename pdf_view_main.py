"""
Professional PDF Viewer - Ana Giriş Modülü
Geliştirme        : Mart - 2026
Yazan             : Dr. Mustafa Afyonluoğlu
"""

import customtkinter as ctk
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import messagebox
import os
from datetime import datetime

# Tema ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Modül importları
from pdf_view_utils import setup_global_exception_handler, init_error_log, center_window
from pdf_view_ui_setup import UISetupMixin
from pdf_view_navigation import NavigationMixin
from pdf_view_display import DisplayMixin
from pdf_view_annotations import AnnotationMixin
from pdf_view_search import SearchMixin
from pdf_view_file_ops import FileOperationsMixin
from pdf_view_text_extraction import TextExtractionMixin

# Annotation manager importları
from annotation_manager_fixed import FixedAnnotationManager, FixedHighlightTool

# Global exception handler'ı ayarla
setup_global_exception_handler()


class PDFViewer(
    UISetupMixin,
    NavigationMixin,
    DisplayMixin,
    AnnotationMixin,
    SearchMixin,
    FileOperationsMixin,
    TextExtractionMixin
):
    """
    Professional PDF Viewer - Ana sınıf
    
    Tüm fonksiyonelliği mixin sınıflarından miras alır:
    - UISetupMixin: Kullanıcı arayüzü kurulumu
    - NavigationMixin: Sayfa navigasyonu ve zoom
    - DisplayMixin: Sayfa görüntüleme ve thumbnail
    - AnnotationMixin: Annotasyon işlemleri
    - SearchMixin: Metin arama
    - FileOperationsMixin: Dosya açma/kaydetme/ayarlar
    - TextExtractionMixin: PDF'den metin çıkarma
    """
    
    def __init__(self):
        # Error log dosyasını başlat
        init_error_log()
        
        # Ana pencere
        self.root = ctk.CTk()
        self.root.title("Professional PDF Viewer 2026 by M.Afyonluoglu")
        self.root.geometry("1150x800")
        
        # Pencereyi ekranın ortasına yerleştir
        center_window(self.root, 1150, 800)
        
        # PDF döküman değişkenleri
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.rotation = 0
        self.search_results = []
        self.current_search_index = 0
        self.annotations = []
        self.highlight_color = "#FFFF00"  # Sarı
        
        # Ayarlar dosyası
        settings_file="pdf_viewer_settings.json"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(current_dir, settings_file)
        print(f"Ayarlar dosyası yolu: {self.settings_file}")

        # self.settings_file = "pdf_viewer_settings.json"
        self.load_settings()
        
        # Fixed annotation manager - ScrollableFrame bug'ını çözen versiyon
        self.annotation_manager = FixedAnnotationManager(self)
        # HighlightTool'u da fixed annotation manager ile uyumlu hale getir
        self.highlight_tool = FixedHighlightTool(self)
        
        # UI ve keybinding'leri kur (mixin'lerden)
        self.setup_ui()
        self.setup_keybindings()
        
        print("DEBUG: PDFViewer başlatıldı")
    
    def run(self):
        """Uygulamayı çalıştır"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


class AdvancedAnnotationWindow:
    """Gelişmiş annotation penceresi"""
    
    def __init__(self, parent, pdf_viewer):
        self.parent = parent
        self.pdf_viewer = pdf_viewer
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Gelişmiş Annotation Araçları")
        self.window.geometry("400x500")
        center_window(self.window, 400, 500)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Annotation araçları UI'ını oluştur"""
        # Başlık
        ctk.CTkLabel(self.window, text="Annotation Araçları", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Highlight renk seçenekleri
        colors_frame = ctk.CTkFrame(self.window)
        colors_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(colors_frame, text="Vurgulama Renkleri:").pack(pady=5)
        
        color_buttons_frame = ctk.CTkFrame(colors_frame)
        color_buttons_frame.pack(pady=5)
        
        colors = ["#FFFF00", "#00FF00", "#FF0000", "#0000FF", "#FF00FF", "#00FFFF"]
        color_names = ["Sarı", "Yeşil", "Kırmızı", "Mavi", "Magenta", "Cyan"]
        
        for i, (color, name) in enumerate(zip(colors, color_names)):
            btn = ctk.CTkButton(
                color_buttons_frame, 
                text=name, 
                fg_color=color,
                text_color="black" if color in ["#FFFF00", "#00FFFF"] else "white",
                width=60,
                command=lambda c=color: self.set_highlight_color(c)
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)
        
        # Not ekleme
        notes_frame = ctk.CTkFrame(self.window)
        notes_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(notes_frame, text="Not Ekle:").pack(pady=5)
        
        self.note_text = ctk.CTkTextbox(notes_frame, height=100)
        self.note_text.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(notes_frame, text="Not Ekle", 
                     command=self.add_note).pack(pady=5)
        
        # Info label
        info_label = ctk.CTkLabel(self.window, 
                                text="Fixed Annotation Manager kullanılıyor.\nAna menüden 'Annotation Yönetimi' butonunu kullanın.")
        info_label.pack(pady=20)
    
    def set_highlight_color(self, color):
        """Vurgulama rengini ayarla"""
        self.pdf_viewer.highlight_color = color
        
    def add_note(self):
        """Not ekle"""
        note_text = self.note_text.get("1.0", "end-1c").strip()
        if note_text:
            messagebox.showinfo("Not", f"Not eklendi: {note_text[:50]}...")
            self.note_text.delete("1.0", "end")
    
    def refresh_annotation_list(self):
        """Annotation listesini yenile"""
        # Mevcut annotation'ları temizle
        for widget in self.annotation_list.winfo_children():
            widget.destroy()
        
        # Dummy annotation'lar
        dummy_annotations = [
            "Sayfa 1: Sarı vurgulama",
            "Sayfa 2: Not - Önemli bölüm",
            "Sayfa 3: Kırmızı vurgulama"
        ]
        
        for i, annotation in enumerate(dummy_annotations):
            frame = ctk.CTkFrame(self.annotation_list)
            frame.pack(fill="x", pady=2)
            
            label = ctk.CTkLabel(frame, text=annotation)
            label.pack(side="left", padx=10, pady=5)
            
            delete_btn = ctk.CTkButton(frame, text="Sil", width=50,
                                     command=lambda idx=i: self.delete_annotation(idx))
            delete_btn.pack(side="right", padx=10, pady=5)
    
    def delete_annotation(self, index):
        """Annotation'ı sil"""
        messagebox.showinfo("Silindi", f"Annotation {index + 1} silindi")
        self.refresh_annotation_list()


def main():
    """Ana program"""
    try:
        print("DEBUG: PDF Viewer başlatılıyor...")
        app = PDFViewer()
        app.run()
    except Exception as e:
        import traceback
        error_msg = f"Program hatası: {e}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            messagebox.showerror("Program Hatası", str(e))
        except:
            pass


if __name__ == "__main__":
    main()
