"""
PDF Viewer - Navigasyon Mixin'i
Sayfa geçişi ve zoom işlemleri
"""

from tkinter import messagebox


class NavigationMixin:
    """Sayfa navigasyonu metodlarını içeren mixin sınıfı"""
    
    def previous_page(self):
        """Önceki sayfaya git"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            self.update_ui()
    
    def next_page(self):
        """Sonraki sayfaya git"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()
            self.update_ui()
    
    def goto_page(self, event=None):
        """Belirtilen sayfaya git"""
        try:
            page_num = int(self.page_entry.get()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.display_page()
                self.update_ui()
            else:
                messagebox.showwarning("Uyarı", f"Sayfa numarası 1-{self.total_pages} arasında olmalıdır.")
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir sayfa numarası girin.")
    
    def goto_page_direct(self, page_num):
        """Doğrudan belirtilen sayfaya git (küçük resim tıklaması için)"""
        self.current_page = page_num
        self.display_page()
        self.update_ui()
    
    def zoom_in(self):
        """Yakınlaştır"""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.display_page()
        self.update_ui()
    
    def zoom_out(self):
        """Uzaklaştır"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self.display_page()
        self.update_ui()
    
    def reset_zoom(self):
        """Zoom'u sıfırla"""
        self.zoom_level = 1.0
        self.display_page()
        self.update_ui()
    
    def rotate_page(self):
        """Sayfayı 90 derece döndür"""
        self.rotation = (self.rotation + 90) % 360
        self.display_page()
    
    def on_mouse_wheel(self, event):
        """Mouse wheel ile kaydırma"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_ctrl_mouse_wheel(self, event):
        """Ctrl + Mouse wheel ile zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
