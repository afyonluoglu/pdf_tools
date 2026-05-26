"""
PDF Viewer - Metin Çıkarma Mixin'i
PDF'den metin çıkarma işlemleri
"""

import customtkinter as ctk
import threading
from tkinter import messagebox


class TextExtractionMixin:
    """Metin çıkarma metodlarını içeren mixin sınıfı"""
    
    def extract_text_to_file(self):
        """PDF'den metin çıkarma işlemini başlat"""
        if not self.pdf_document:
            messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin.")
            return
        
        # Tek sayfa ise direkt çıkar
        if self.total_pages == 1:
            self.start_text_extraction(1, 1)
        else:
            # Sayfa aralığı seçme penceresi göster
            self.show_page_range_dialog()
    
    def show_page_range_dialog(self):
        """Sayfa aralığı seçme penceresi"""
        from pdf_view_utils import center_window
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Sayfa Aralığı Seç")
        dialog.geometry("400x280")
        center_window(dialog, 400, 280)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Başlık
        ctk.CTkLabel(dialog, text="📄 Metne Çevrilecek Sayfaları Seçin", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        
        # Bilgi
        info_text = f"PDF toplam {self.total_pages} sayfa içermektedir."
        ctk.CTkLabel(dialog, text=info_text, font=ctk.CTkFont(size=12)).pack(pady=5)
        
        # Seçim tipi
        selection_type = ctk.StringVar(value="all")
        
        type_frame = ctk.CTkFrame(dialog)
        type_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkRadioButton(type_frame, text="Tüm sayfaları çevir", 
                          variable=selection_type, value="all").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(type_frame, text="Sayfa aralığı belirt", 
                          variable=selection_type, value="range").pack(anchor="w", pady=5)
        
        # Sayfa aralığı giriş alanları
        range_frame = ctk.CTkFrame(dialog)
        range_frame.pack(fill="x", padx=30, pady=5)
        
        # Entry'lere odaklanınca veya değer girilince radiobutton'u seç
        def on_entry_focus_or_change(event=None):
            selection_type.set("range")
        
        ctk.CTkLabel(range_frame, text="Başlangıç:").grid(row=0, column=0, padx=5, pady=5)
        start_entry = ctk.CTkEntry(range_frame, width=80, placeholder_text="1")
        start_entry.grid(row=0, column=1, padx=5, pady=5)
        start_entry.insert(0, "1")
        start_entry.bind("<FocusIn>", on_entry_focus_or_change)
        start_entry.bind("<KeyRelease>", on_entry_focus_or_change)
        
        ctk.CTkLabel(range_frame, text="Bitiş:").grid(row=0, column=2, padx=5, pady=5)
        end_entry = ctk.CTkEntry(range_frame, width=80, placeholder_text=str(self.total_pages))
        end_entry.grid(row=0, column=3, padx=5, pady=5)
        end_entry.insert(0, str(self.total_pages))
        end_entry.bind("<FocusIn>", on_entry_focus_or_change)
        end_entry.bind("<KeyRelease>", on_entry_focus_or_change)
        
        def on_confirm():
            try:
                if selection_type.get() == "all":
                    start_page = 1
                    end_page = self.total_pages
                else:
                    start_page = int(start_entry.get())
                    end_page = int(end_entry.get())
                
                # Doğrulama
                if start_page < 1 or end_page > self.total_pages:
                    messagebox.showerror("Hata", f"Sayfa numaraları 1-{self.total_pages} arasında olmalıdır.")
                    return
                if start_page > end_page:
                    messagebox.showerror("Hata", "Başlangıç sayfası bitiş sayfasından büyük olamaz.")
                    return
                
                dialog.destroy()
                self.start_text_extraction(start_page, end_page)
                
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli sayfa numaraları girin.")
        
        # Butonlar
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkButton(btn_frame, text="İptal", width=100, 
                     fg_color="gray", command=dialog.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Metne Çevir", width=120, 
                     command=on_confirm).pack(side="right", padx=10)
    
    def start_text_extraction(self, start_page, end_page):
        """Metin çıkarma işlemini başlat"""
        from pdf_view_utils import center_window
        
        # Progress penceresi
        progress_window = ctk.CTkToplevel(self.root)
        progress_window.title("Metin Çıkarılıyor...")
        progress_window.geometry("450x180")
        center_window(progress_window, 450, 180)
        progress_window.transient(self.root)
        progress_window.grab_set()
        progress_window.resizable(False, False)
        
        # Progress widgets
        ctk.CTkLabel(progress_window, text="📄 PDF'den metin çıkarılıyor...", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        progress_bar = ctk.CTkProgressBar(progress_window, width=350)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        progress_label = ctk.CTkLabel(progress_window, text="Hazırlanıyor...")
        progress_label.pack(pady=5)
        
        page_label = ctk.CTkLabel(progress_window, text="")
        page_label.pack(pady=5)
        
        extracted_text = []
        
        def extract_thread():
            try:
                total_to_extract = end_page - start_page + 1
                
                for i, page_num in enumerate(range(start_page - 1, end_page)):
                    # İlerleme güncelle
                    progress = (i + 1) / total_to_extract
                    progress_bar.set(progress)
                    progress_label.configure(text=f"Sayfa {page_num + 1} işleniyor...")
                    page_label.configure(text=f"{i + 1} / {total_to_extract} sayfa tamamlandı")
                    progress_window.update()
                    
                    # Sayfadan metin çıkar
                    page = self.pdf_document[page_num]
                    
                    # Türkçe karakterler için UTF-8 text extraction
                    text = page.get_text("text")
                    
                    if text.strip():
                        # Satır sonlarını akıllıca temizle (paragrafları koru)
                        text = self._clean_line_breaks(text)
                        
                        # Sayfa başlığı ekle
                        extracted_text.append(f"\n === SAYFA {page_num + 1} {'='*60}")
                        # extracted_text.append(f"SAYFA {page_num + 1}")
                        # extracted_text.append(f"{'='*60}\n")
                        extracted_text.append(text)
                    
                    print(f"DEBUG: Sayfa {page_num + 1}: metin çıkarıldı ({len(text)} karakter)")
                
                progress_bar.set(1.0)
                progress_label.configure(text="Tamamlandı!")
                progress_window.update()
                
                # Metin editörünü aç
                self.root.after(300, lambda: self.open_text_editor("\n".join(extracted_text), start_page, end_page))
                self.root.after(500, progress_window.destroy)
                
                print(f"DEBUG: Toplam {total_to_extract} sayfa metin çıkarma işlemi tamamlandı")
                
            except Exception as e:
                print(f"DEBUG: Metin çıkarma hatası: {e}")
                progress_window.destroy()
                messagebox.showerror("Hata", f"Metin çıkarılırken hata oluştu:\n{str(e)}")
        
        # Thread'i başlat
        threading.Thread(target=extract_thread, daemon=True).start()
    
    def _clean_line_breaks(self, text):
        """
        PDF'den çıkarılan metindeki gereksiz satır sonlarını temizle.
        Paragraf yapısını koruyarak satır içi kırılmaları birleştir.
        Ayrıca hece bölünmelerini (satır sonundaki "- ") temizle.
        """
        import re
        
        # Önce satır sonundaki hece bölünmelerini temizle
        # "kelime-\n devam" -> "kelimedevam"
        # Satır sonunda tire ve ardından satır başı boşluklar varsa birleştir
        
        # print(f"EDIT: ###{text}###")
        text = re.sub(r'-\s*\n\s*', '', text)

        lines = text.split('\n')
        cleaned_lines = []
        current_paragraph = []
        
        for line in lines:
            stripped = line.strip()
            
            # Boş satır = paragraf sonu
            if not stripped:
                if current_paragraph:
                    cleaned_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                cleaned_lines.append('')  # Paragraf ayırıcı boş satır
                continue
            
            # Satır bir cümle/paragraf sonuyla bitiyorsa (., !, ?, :) ayrı tut
            # veya başlık gibi kısa satırlar (tamamen büyük harf veya sayı ile başlıyor)
            is_sentence_end = stripped.endswith(('.', '!', '?', ':', ';'))
            is_title_like = len(stripped) < 60 and (stripped.isupper() or re.match(r'^\d+\.', stripped) or '=' in stripped)
            
            if is_sentence_end or is_title_like:
                current_paragraph.append(stripped)
                cleaned_lines.append(' '.join(current_paragraph))
                current_paragraph = []
            else:
                # Devam eden satır - bir sonraki ile birleştir
                current_paragraph.append(stripped)
        
        # Son paragrafı ekle
        if current_paragraph:
            cleaned_lines.append(' '.join(current_paragraph))
        
        # Ardışık boş satırları tek satıra indir
        result = []
        prev_empty = False
        for line in cleaned_lines:
            if line == '':
                if not prev_empty:
                    result.append(line)
                prev_empty = True
            else:
                result.append(line)
                prev_empty = False
        
        return '\n'.join(result)
    
    def open_text_editor(self, text, start_page, end_page):
        """Profesyonel metin editörü penceresini aç"""
        from pdf_view_text_editor import ProfessionalTextEditor
        editor = ProfessionalTextEditor(self.root, self, text, start_page, end_page)
