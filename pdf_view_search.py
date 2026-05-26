"""
PDF Viewer - Arama Mixin'i
PDF içinde metin arama işlemleri
"""

import fitz  # PyMuPDF
from tkinter import messagebox


class SearchMixin:
    """Arama metodlarını içeren mixin sınıfı"""
    
    def search_text(self, event=None):
        """PDF'de metin ara"""
        if not self.pdf_document:
            messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin.")
            return
        
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Uyarı", "Arama metni girin.")
            return
        
        self.search_results = []
        
        # Tüm sayfalarda ara
        for page_num in range(self.total_pages):
            page = self.pdf_document[page_num]
            text_instances = page.search_for(search_term)
            
            for inst in text_instances:
                self.search_results.append((page_num, inst))
        
        if self.search_results:
            for i in range(0, len(self.search_results)):
                self.current_search_index = i
                print(f"🚩Sonuç {i+1}: Sayfa {self.search_results[i][0] + 1}, Konum: {self.search_results[i][1]}")

            self.current_search_index = 0
            self.show_search_result()

            messagebox.showinfo("Arama Sonucu", f"'{search_term}' için {len(self.search_results)} sonuç bulundu.")
        else:
            messagebox.showinfo("Arama Sonucu", f"'{search_term}' bulunamadı.")
    
    def search_next(self, event=None):
        """Sonraki arama sonucuna git"""
        print(f"🔎 Toplam sonuç: {len(self.search_results)}, Şu anki indeks: {self.current_search_index}")
        if self.current_search_index < len(self.search_results)-1:
            self.current_search_index += 1
            self.show_search_result()

    def show_search_result(self):
        """Mevcut arama sonucunu göster"""
        if not self.search_results:
            return
        
        page_num, rect = self.search_results[self.current_search_index]
        
        # İlgili sayfaya git
        self.current_page = page_num
        self.display_page()
        self.update_ui()
        
        # Sonucu vurgula
        mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
        rect = rect * mat
        
        self.canvas.create_rectangle(
            rect.x0, rect.y0, rect.x1, rect.y1,
            outline="red", width=2, tags="search_highlight"
        )
