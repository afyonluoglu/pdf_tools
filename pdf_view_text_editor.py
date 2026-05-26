"""
PDF Viewer - Profesyonel Metin Editörü
PDF'den çıkarılan metni düzenleme, kaydetme ve seslendirme
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re

EDITOR_FONT_SIZE = 14

class ProfessionalTextEditor:
    """Profesyonel metin editörü - PDF'den çıkarılan metni düzenleme ve kaydetme"""
    
    def __init__(self, parent, pdf_viewer, text, start_page, end_page):
        self.parent = parent
        self.pdf_viewer = pdf_viewer
        self.original_text = text
        self.start_page = start_page
        self.end_page = end_page
        self.undo_stack = []
        self.redo_stack = []
        self.find_results = []
        self.current_find_index = 0
        self.filename = None
        
        # TTS Manager
        self.tts_manager = None
        
        # Ana pencere
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Metin Editörü - Sayfa {start_page}-{end_page}")
        self.window.geometry("1150x750")
        
        from pdf_view_utils import center_window
        center_window(self.window, 1150, 750)
        self.window.transient(parent)
        
        self.setup_ui()
        self.setup_keybindings()
        
        # Metni ekle
        self.text_widget.insert("1.0", text)
        self.update_status()
        
        # TTS'i başlat
        self.init_tts()
        
        # print(f"DEBUG: Metin editörü açıldı - {len(text)} karakter yüklendi")
    
    def init_tts(self):
        """TTS manager'ı başlat"""
        try:
            from pdf_view_tts import TTSManager
            self.tts_manager = TTSManager(self.window)
            # print("DEBUG: TTS manager başlatıldı")
        except Exception as e:
            print(f"DEBUG: TTS başlatma hatası: {e}")
            self.tts_manager = None
    
    def _remove_page_separators(self, text):
        """Metindeki sayfa ayraçlarını temizle (=== SAYFA X ===)"""
        # "=== SAYFA 2 ===============" veya benzeri formatları temizle
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Sayfa ayracı formatını kontrol et
            stripped = line.strip()
            if stripped.startswith('=') and 'SAYFA' in stripped:
                # Bu bir sayfa ayracı, atla
                print(f"DEBUG: Sayfa ayracı kaldırıldı: {stripped[:50]}")
                continue
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        # Ardışık boş satırları tek satıra indir
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')
        return result.strip()
    
    def setup_ui(self):
        """Editör arayüzünü oluştur"""
        # Ana menü çubuğu
        self.menu_frame = ctk.CTkFrame(self.window, height=40)
        self.menu_frame.pack(fill="x", padx=5, pady=5)
        self.menu_frame.pack_propagate(False)
        
        # Dosya işlemleri
        ctk.CTkButton(self.menu_frame, text="� Aç", width=70, 
                     command=self.open_text_file).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="�💾 Kaydet", width=90, 
                     command=self.save_text).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="📋 Panoya Kopyala", width=120, 
                     command=self.copy_all).pack(side="left", padx=3, pady=5)
        
        # Ayırıcı
        ctk.CTkFrame(self.menu_frame, width=2, height=30, fg_color="gray").pack(side="left", padx=8, pady=5)
        
        # Düzenleme işlemleri
        ctk.CTkButton(self.menu_frame, text="↩️ Geri Al", width=80, 
                     command=self.undo).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="↪️ Yinele", width=80, 
                     command=self.redo).pack(side="left", padx=3, pady=5)
        
        # Ayırıcı
        ctk.CTkFrame(self.menu_frame, width=2, height=30, fg_color="gray").pack(side="left", padx=8, pady=5)
        
        # Metin işlemleri
        ctk.CTkButton(self.menu_frame, text="🔤 BÜYÜK", width=80, 
                     command=self.to_uppercase).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="🔡 küçük", width=80, 
                     command=self.to_lowercase).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="📏 Satır Temizle", width=100, 
                     command=self.remove_empty_lines).pack(side="left", padx=3, pady=5)
        
        # Ayırıcı
        ctk.CTkFrame(self.menu_frame, width=2, height=30, fg_color="gray").pack(side="left", padx=8, pady=5)
        
        # Seslendirme butonları
        ctk.CTkButton(self.menu_frame, text="🔊 Seslendir", width=100, 
                     fg_color="#28a745", hover_color="#218838",
                     command=self.speak_text).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="⏹️ Durdur", width=80, 
                     fg_color="#dc3545", hover_color="#c82333",
                     command=self.stop_speech).pack(side="left", padx=3, pady=5)
        ctk.CTkButton(self.menu_frame, text="💾 MP3 Kaydet", width=100, 
                     fg_color="#17a2b8", hover_color="#138496",
                     command=self.save_as_mp3).pack(side="left", padx=3, pady=5)
        
        # Araç çubuğu 2
        self.toolbar2 = ctk.CTkFrame(self.window, height=45)
        self.toolbar2.pack(fill="x", padx=5, pady=(0, 5))
        self.toolbar2.pack_propagate(False)
        
        # Bul ve değiştir
        ctk.CTkLabel(self.toolbar2, text="Bul:").pack(side="left", padx=5, pady=8)
        self.find_entry = ctk.CTkEntry(self.toolbar2, width=150, placeholder_text="Aranacak metin...")
        self.find_entry.pack(side="left", padx=3, pady=8)
        self.find_entry.bind("<Return>", lambda e: self.find_text())
        
        ctk.CTkButton(self.toolbar2, text="🔍", width=40, 
                     command=self.find_text).pack(side="left", padx=2, pady=8)
        ctk.CTkButton(self.toolbar2, text="▼", width=30, 
                     command=self.find_next).pack(side="left", padx=2, pady=8)
        ctk.CTkButton(self.toolbar2, text="▲", width=30, 
                     command=self.find_prev).pack(side="left", padx=2, pady=8)
        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar2, width=2, height=30, fg_color="gray").pack(side="left", padx=8, pady=8)
        
        # Değiştir
        ctk.CTkLabel(self.toolbar2, text="Değiştir:").pack(side="left", padx=5, pady=8)
        self.replace_entry = ctk.CTkEntry(self.toolbar2, width=150, placeholder_text="Yeni metin...")
        self.replace_entry.pack(side="left", padx=3, pady=8)
        
        ctk.CTkButton(self.toolbar2, text="Değiştir", width=70, 
                     command=self.replace_current).pack(side="left", padx=3, pady=8)
        ctk.CTkButton(self.toolbar2, text="Tümünü", width=70, 
                     command=self.replace_all).pack(side="left", padx=3, pady=8)
        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar2, width=2, height=30, fg_color="gray").pack(side="left", padx=8, pady=8)
        
        # TTS Ses seçimi
        ctk.CTkLabel(self.toolbar2, text="Ses:").pack(side="left", padx=5, pady=8)
        self.voice_var = ctk.StringVar(value="Emel (Kadın)")
        self.voice_combo = ctk.CTkComboBox(
            self.toolbar2, 
            width=130,
            values=["Emel (Kadın)", "Ahmet (Erkek)"],
            variable=self.voice_var
        )
        self.voice_combo.pack(side="left", padx=3, pady=8)
        
        # Hız
        ctk.CTkLabel(self.toolbar2, text="Hız:").pack(side="left", padx=5, pady=8)
        self.speed_var = ctk.StringVar(value="Normal")
        self.speed_combo = ctk.CTkComboBox(
            self.toolbar2, 
            width=100,
            values=["Yavaş", "Normal", "Hızlı"],
            variable=self.speed_var
        )
        self.speed_combo.pack(side="left", padx=3, pady=8)
        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar2, width=2, height=30, fg_color="gray").pack(side="left", padx=8, pady=8)
        
        # Font boyutu
        ctk.CTkLabel(self.toolbar2, text="Font:").pack(side="left", padx=5, pady=8)
        self.font_size_var = ctk.StringVar(value=str(EDITOR_FONT_SIZE))
        self.font_size_combo = ctk.CTkComboBox(
            self.toolbar2, 
            width=70,
            values=["9", "10", "11", "12", "14", "16", "18", "20", "24", "28"],
            variable=self.font_size_var,
            command=self.change_font_size
        )
        self.font_size_combo.pack(side="left", padx=3, pady=8)
        
        # Metin alanı - Frame ile sarmalanmış
        text_frame = ctk.CTkFrame(self.window)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Satır numaraları için canvas
        self.line_numbers = tk.Canvas(text_frame, width=50, bg='#2b2b2b', highlightthickness=0)
        self.line_numbers.pack(side="left", fill="y")
        
        # Ana metin widget'ı
        text_container = ctk.CTkFrame(text_frame)
        text_container.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(text_container)
        scrollbar.pack(side="right", fill="y")
        
        # Textbox - CustomTkinter yerine tkinter.Text (daha fazla kontrol için)
        self.text_widget = tk.Text(
            text_container,
            wrap="word",
            font=("Consolas", EDITOR_FONT_SIZE),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#3d5a80",
            selectforeground="#ffffff",
            undo=True,
            maxundo=50,
            padx=10,
            pady=10
        )
        self.text_widget.pack(side="left", fill="both", expand=True)
        
        # Scrollbar bağla
        self.text_widget.config(yscrollcommand=self._on_text_scroll)
        scrollbar.configure(command=self.text_widget.yview)
        
        # Metin değişikliği olayları
        self.text_widget.bind("<<Modified>>", self.on_text_modified)
        self.text_widget.bind("<KeyRelease>", self.update_line_numbers)
        self.text_widget.bind("<MouseWheel>", self.update_line_numbers)
        
        # Durum çubuğu
        self.status_frame = ctk.CTkFrame(self.window, height=35)
        self.status_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Hazır", 
                                        font=ctk.CTkFont(size=11))
        self.status_label.pack(side="left", padx=10, pady=8)
        
        # TTS durum göstergesi
        self.tts_status_label = ctk.CTkLabel(self.status_frame, text="", 
                                            font=ctk.CTkFont(size=11),
                                            text_color="#28a745")
        self.tts_status_label.pack(side="left", padx=10, pady=8)
        
        self.char_count_label = ctk.CTkLabel(self.status_frame, text="0 karakter", 
                                            font=ctk.CTkFont(size=11))
        self.char_count_label.pack(side="right", padx=10, pady=8)
        
        self.word_count_label = ctk.CTkLabel(self.status_frame, text="0 kelime", 
                                            font=ctk.CTkFont(size=11))
        self.word_count_label.pack(side="right", padx=10, pady=8)
        
        self.line_count_label = ctk.CTkLabel(self.status_frame, text="0 satır", 
                                            font=ctk.CTkFont(size=11))
        self.line_count_label.pack(side="right", padx=10, pady=8)
        
        # İlk satır numaralarını çiz
        self.window.after(100, self.update_line_numbers)
    
    def _on_text_scroll(self, *args):
        """Metin kaydırma olayı"""
        scrollbar = None
        for widget in self.text_widget.master.winfo_children():
            if isinstance(widget, ctk.CTkScrollbar):
                scrollbar = widget
                break
        if scrollbar:
            scrollbar.set(*args)
        self.update_line_numbers()
    
    def setup_keybindings(self):
        """Klavye kısayolları"""
        self.text_widget.bind("<Control-s>", lambda e: self.save_text())
        self.text_widget.bind("<Control-z>", lambda e: self.undo())
        self.text_widget.bind("<Control-y>", lambda e: self.redo())
        self.text_widget.bind("<Control-f>", lambda e: self.find_entry.focus())
        self.text_widget.bind("<Control-h>", lambda e: self.replace_entry.focus())
        self.text_widget.bind("<Control-a>", lambda e: self.select_all())
        self.window.bind("<F3>", lambda e: self.find_next())
        self.window.bind("<Shift-F3>", lambda e: self.find_prev())
        self.window.bind("<F5>", lambda e: self.speak_text())  # F5 ile seslendir
        self.window.bind("<Escape>", lambda e: self.stop_speech())  # ESC ile durdur
    
    def update_line_numbers(self, event=None):
        """Satır numaralarını güncelle"""
        self.line_numbers.delete("all")
        
        # Görünür satırları hesapla
        first_visible = self.text_widget.index("@0,0")
        last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
        
        first_line = int(first_visible.split(".")[0])
        last_line = int(last_visible.split(".")[0])
        
        # Her satır için numara çiz
        for i in range(first_line, last_line + 1):
            y = self.text_widget.dlineinfo(f"{i}.0")
            if y:
                self.line_numbers.create_text(
                    45, y[1] + 12,
                    text=str(i),
                    fill="#888888",
                    font=("Consolas", EDITOR_FONT_SIZE),
                    anchor="e"
                )
    
    def on_text_modified(self, event=None):
        """Metin değiştiğinde"""
        if self.text_widget.edit_modified():
            self.update_status()
            self.text_widget.edit_modified(False)
    
    def update_status(self):
        """Durum çubuğunu güncelle"""
        text = self.text_widget.get("1.0", "end-1c")
        
        # Karakter sayısı
        char_count = len(text)
        self.char_count_label.configure(text=f"{char_count:,} karakter")
        
        # Kelime sayısı
        words = text.split()
        word_count = len(words)
        self.word_count_label.configure(text=f"{word_count:,} kelime")
        
        # Satır sayısı
        lines = text.split("\n")
        line_count = len(lines)
        self.line_count_label.configure(text=f"{line_count:,} satır")
    
    # ==================== SESLENDİRME FONKSİYONLARI ====================
    
    def speak_text(self):
        """Seçili metni veya tüm metni seslendir"""
        if not self.tts_manager:
            messagebox.showerror("Hata", "Seslendirme modülü yüklenemedi.\nedge-tts paketini yükleyin: pip install edge-tts")
            return
        
        # Seçili metin var mı kontrol et
        try:
            text = self.text_widget.get("sel.first", "sel.last")
            self.status_label.configure(text="🔊 Seçili metin seslendiriliyor...")
        except tk.TclError:
            # Seçim yoksa tüm metni al
            text = self.text_widget.get("1.0", "end-1c")
            self.status_label.configure(text="🔊 Tüm metin seslendiriliyor...")
        
        if not text.strip():
            messagebox.showwarning("Uyarı", "Seslendirilecek metin bulunamadı.")
            return
        
        # Ses ve hız ayarlarını al
        voice = self.voice_var.get()
        speed = self.speed_var.get()
        
        # Seslendirmeyi başlat
        self.tts_status_label.configure(text="🔊 Seslendirme hazırlanıyor...")
        self.tts_manager.speak(text, voice, speed, self.on_tts_status_update)
    
    def stop_speech(self):
        """Seslendirmeyi durdur"""
        if self.tts_manager:
            self.tts_manager.stop()
            self.tts_status_label.configure(text="⏹️ Durduruldu")
            self.status_label.configure(text="Hazır")
            # print("DEBUG: Seslendirme durduruldu")
    
    def save_as_mp3(self):
        """Seçili metni veya tüm metni MP3 olarak kaydet"""
        if not self.tts_manager:
            messagebox.showerror("Hata", "TTS modülü yüklenemedi.\nedge-tts paketini yükleyin: pip install edge-tts")
            return
        
        # Seçili metin var mı kontrol et
        try:
            text = self.text_widget.get("sel.first", "sel.last")
        except tk.TclError:
            text = self.text_widget.get("1.0", "end-1c")
        
        if not text.strip():
            messagebox.showwarning("Uyarı", "Kaydedilecek metin bulunamadı.")
            return
        
        # Sayfa ayraçlarını (=== SAYFA X ===) temizle
        text = self._remove_page_separators(text)
        
        # Dosya kaydetme dialogu
        file_path = filedialog.asksaveasfilename(
            title="MP3 Olarak Kaydet",
            defaultextension=".mp3",
            filetypes=[("MP3 Dosyası", "*.mp3")],
            initialfile=f"seslendirme_sayfa_{self.start_page}-{self.end_page}.mp3"
        )
        
        if file_path:
            voice = self.voice_var.get()
            speed = self.speed_var.get()
            
            self.tts_status_label.configure(text="💾 MP3 oluşturuluyor...")
            self.status_label.configure(text="MP3 kaydediliyor...")
            
            self.tts_manager.save_as_mp3(text, voice, speed, file_path, self.on_mp3_save_status)
    
    def on_mp3_save_status(self, status):
        """MP3 kaydetme durum güncellemesi"""
        self.tts_status_label.configure(text=status)
        if "kaydedildi" in status.lower():
            self.status_label.configure(text="Hazır")
            messagebox.showinfo("Başarılı", status)
        elif "hata" in status.lower():
            self.status_label.configure(text="Hazır")
    
    def change_font_size(self, size=None):
        """Metin font boyutunu değiştir"""
        try:
            new_size = int(self.font_size_var.get())
            self.text_widget.configure(font=("Consolas", new_size))
            self.status_label.configure(text=f"Font boyutu: {new_size}")
            self.update_line_numbers()
            # print(f"DEBUG: Font boyutu değiştirildi: {new_size}")
        except ValueError:
            pass
    
    def on_tts_status_update(self, status):
        """TTS durum güncellemesi callback'i"""
        self.tts_status_label.configure(text=status)
        if "Tamamlandı" in status or "Hata" in status:
            self.status_label.configure(text="Hazır")
    
    # ==================== DOSYA İŞLEMLERİ ====================
    
    def open_text_file(self):
        """TXT dosyası aç ve editöre yükle"""
        file_path = filedialog.askopenfilename(
            title="Metin Dosyası Aç",
            defaultextension=".txt",
            filetypes=[
                ("Metin Dosyası", "*.txt"),
                ("Tüm Dosyalar", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Editörü temizle ve yeni içeriği ekle
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", content)
                
                # Pencere başlığını güncelle
                self.filename = os.path.basename(file_path)
                self.window.title(f"Metin Editörü - {self.filename}")
                
                self.status_label.configure(text=f"✓ Açıldı: {self.filename}")
                self.update_status()
                self.update_line_numbers()
                # print(f"DEBUG: Metin dosyası açıldı: {file_path}")
                
            except Exception as e:
                print(f"DEBUG: Dosya açma hatası: {e}")
                messagebox.showerror("Hata", f"Dosya açılırken hata oluştu:\n{str(e)}")
    
    def save_text(self):
        """Metni dosyaya kaydet"""
        if self.filename == None:
            file_path = filedialog.asksaveasfilename(
                title="Metni Kaydet",
                defaultextension=".txt",
                filetypes=[
                    ("Metin Dosyası", "*.txt"),
                    ("Tüm Dosyalar", "*.*")
                ],
                initialfile=f"{self.filename}"
            )
        else:
            file_path = self.filename
            # print(f"DEBUG: Dosya {file_path} ismiyle saklanacak")

        if file_path:
            try:
                text = self.text_widget.get("1.0", "end-1c")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                self.status_label.configure(text=f"✓ Kaydedildi: {os.path.basename(file_path)}")
                # print(f"DEBUG: Metin dosyası kaydedildi: {file_path}")
                self.filename = os.path.basename(file_path)
                self.window.title(f"Metin Editörü - {self.filename}")
                messagebox.showinfo("Başarılı", f"Metin başarıyla kaydedildi:\n{file_path}")
                
            except Exception as e:
                print(f"DEBUG: Kaydetme hatası: {e}")
                messagebox.showerror("Hata", f"Dosya kaydedilirken hata oluştu:\n{str(e)}")
    
    def copy_all(self):
        """Tüm metni panoya kopyala"""
        text = self.text_widget.get("1.0", "end-1c")
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        self.status_label.configure(text="✓ Metin panoya kopyalandı")
        # print("DEBUG: Metin panoya kopyalandı")
    
    def select_all(self):
        """Tüm metni seç"""
        self.text_widget.tag_add("sel", "1.0", "end-1c")
        return "break"
    
    def undo(self):
        """Geri al"""
        try:
            self.text_widget.edit_undo()
            self.status_label.configure(text="↩️ Geri alındı")
        except tk.TclError:
            self.status_label.configure(text="Geri alınacak işlem yok")
        return "break"
    
    def redo(self):
        """Yinele"""
        try:
            self.text_widget.edit_redo()
            self.status_label.configure(text="↪️ Yinelendi")
        except tk.TclError:
            self.status_label.configure(text="Yinelenecek işlem yok")
        return "break"
    
    def to_uppercase(self):
        """Seçili metni büyük harfe çevir"""
        try:
            selection = self.text_widget.get("sel.first", "sel.last")
            self.text_widget.delete("sel.first", "sel.last")
            self.text_widget.insert("insert", selection.upper())
            self.status_label.configure(text="🔤 Büyük harfe çevrildi")
        except tk.TclError:
            # Seçim yoksa tüm metni çevir
            text = self.text_widget.get("1.0", "end-1c")
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", text.upper())
            self.status_label.configure(text="🔤 Tüm metin büyük harfe çevrildi")
    
    def to_lowercase(self):
        """Seçili metni küçük harfe çevir"""
        try:
            selection = self.text_widget.get("sel.first", "sel.last")
            self.text_widget.delete("sel.first", "sel.last")
            self.text_widget.insert("insert", selection.lower())
            self.status_label.configure(text="🔡 Küçük harfe çevrildi")
        except tk.TclError:
            text = self.text_widget.get("1.0", "end-1c")
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", text.lower())
            self.status_label.configure(text="🔡 Tüm metin küçük harfe çevrildi")
    
    def remove_empty_lines(self):
        """Boş satırları temizle"""
        text = self.text_widget.get("1.0", "end-1c")
        lines = text.split("\n")
        # Ardışık boş satırları tek satıra indir
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", "\n".join(cleaned_lines))
        self.status_label.configure(text="📏 Boş satırlar temizlendi")
        self.update_status()
    
    # ==================== ARAMA FONKSİYONLARI ====================
    
    def find_text(self):
        """Metinde ara"""
        search_term = self.find_entry.get()
        if not search_term:
            return
        
        # Önceki vurgulamaları temizle
        self.text_widget.tag_remove("search", "1.0", "end")
        
        # Tüm eşleşmeleri bul
        self.find_results = []
        start = "1.0"
        while True:
            pos = self.text_widget.search(search_term, start, "end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(search_term)}c"
            self.find_results.append((pos, end))
            self.text_widget.tag_add("search", pos, end)
            start = end
        
        # Vurgulama rengi
        self.text_widget.tag_config("search", background="#3d5a80", foreground="#ffffff")
        
        if self.find_results:
            self.current_find_index = 0
            self.highlight_current_find()
            self.status_label.configure(text=f"🔍 {len(self.find_results)} sonuç bulundu")
            # print(f"DEBUG: '{search_term}' için {len(self.find_results)} sonuç bulundu")
        else:
            self.status_label.configure(text=f"🔍 '{search_term}' bulunamadı")
    
    def highlight_current_find(self):
        """Mevcut arama sonucunu vurgula"""
        if not self.find_results:
            return
        
        # Önceki aktif vurgulamayı kaldır
        self.text_widget.tag_remove("current_find", "1.0", "end")
        
        # Mevcut sonuca git ve vurgula
        pos, end = self.find_results[self.current_find_index]
        self.text_widget.tag_add("current_find", pos, end)
        self.text_widget.tag_config("current_find", background="#ff6b6b", foreground="#ffffff")
        self.text_widget.see(pos)
        
        self.status_label.configure(
            text=f"🔍 {self.current_find_index + 1} / {len(self.find_results)}"
        )
    
    def find_next(self):
        """Sonraki sonuca git"""
        if self.find_results and self.current_find_index < len(self.find_results) - 1:
            self.current_find_index += 1
            self.highlight_current_find()
    
    def find_prev(self):
        """Önceki sonuca git"""
        if self.find_results and self.current_find_index > 0:
            self.current_find_index -= 1
            self.highlight_current_find()
    
    def replace_current(self):
        """Mevcut eşleşmeyi değiştir"""
        if not self.find_results:
            self.find_text()
            return
        
        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()
        
        if not search_term:
            return
        
        # Mevcut eşleşmeyi değiştir
        pos, end = self.find_results[self.current_find_index]
        self.text_widget.delete(pos, end)
        self.text_widget.insert(pos, replace_term)
        
        self.status_label.configure(text="✓ Değiştirildi")
        
        # Aramayı yenile
        self.find_text()
    
    def replace_all(self):
        """Tüm eşleşmeleri değiştir"""
        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()
        
        if not search_term:
            return
        
        text = self.text_widget.get("1.0", "end-1c")
        count = text.lower().count(search_term.lower())
        
        # Case-insensitive replace
        new_text = re.sub(re.escape(search_term), replace_term, text, flags=re.IGNORECASE)
        
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", new_text)
        
        self.status_label.configure(text=f"✓ {count} adet değiştirildi")
        self.find_results = []
        self.update_status()
        # print(f"DEBUG: {count} adet '{search_term}' -> '{replace_term}' değiştirildi")
