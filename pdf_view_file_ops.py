"""
PDF Viewer - Dosya İşlemleri Mixin'i
PDF açma, kaydetme, ayarlar yönetimi
"""

import customtkinter as ctk
import fitz  # PyMuPDF
import os
import json
import threading
from datetime import datetime
from tkinter import filedialog, messagebox


class FileOperationsMixin:
    """Dosya işlemleri metodlarını içeren mixin sınıfı"""
    
    def open_pdf(self):
        """PDF dosyası aç"""
        file_path = filedialog.askopenfilename(
            title="PDF Dosyası Seç",
            filetypes=[("PDF dosyaları", "*.pdf"), ("Tüm dosyalar", "*.*")]
        )
        
        if file_path:
            self.load_pdf_with_progress(file_path)
    
    def load_pdf_with_progress(self, file_path):
        """PDF'yi progress bar ile yükle"""
        from pdf_view_utils import center_window
        
        # Progress window
        progress_window = ctk.CTkToplevel(self.root)
        progress_window.title("PDF Yükleniyor...")
        progress_window.geometry("400x150")
        center_window(progress_window, 400, 150)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Progress widgets
        ctk.CTkLabel(progress_window, text="PDF dosyası yükleniyor...", 
                    font=ctk.CTkFont(size=14)).pack(pady=20)
        
        progress_bar = ctk.CTkProgressBar(progress_window, width=300)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        progress_label = ctk.CTkLabel(progress_window, text="Başlıyor...")
        progress_label.pack(pady=5)
        
        def load_pdf_thread():
            try:
                # PDF belgesini aç
                progress_bar.set(0.1)
                progress_label.configure(text="PDF açılıyor...")
                progress_window.update()
                
                self.pdf_document = fitz.open(file_path)
                self.total_pages = len(self.pdf_document)
                self.current_page = 0
                
                progress_bar.set(0.3)
                progress_label.configure(text="Sayfa bilgileri alınıyor...")
                progress_window.update()
                
                # Küçük resimleri oluştur
                self.create_thumbnails(progress_bar, progress_label, progress_window)
                
                progress_bar.set(0.85)
                progress_label.configure(text="Annotation'lar yükleniyor...")
                progress_window.update()
                
                # ÖNCE eski annotation'ları temizle, SONRA sayfayı çiz (hayalet önleme)
                self.clear_previous_annotations()
                
                # Mevcut annotation'ları JSON sidecar'dan yükle
                self.load_existing_annotations()
                
                progress_bar.set(0.95)
                progress_label.configure(text="Görünüm hazırlanıyor...")
                progress_window.update()
                
                # Sayfayı annotation'larla birlikte göster
                self.display_page()
                self.update_ui()
                
                progress_bar.set(1.0)
                progress_label.configure(text="Tamamlandı!")
                progress_window.update()
                
                self.status_label.configure(text=f"Yüklendi: {os.path.basename(file_path)} ({self.total_pages} sayfa)")
                
                # Progress window'u kapat
                self.root.after(500, progress_window.destroy)
                
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Hata", f"PDF yüklenirken hata oluştu:\n{str(e)}")
        
        # Thread'i başlat
        threading.Thread(target=load_pdf_thread, daemon=True).start()
    
    def save_pdf(self):
        """PDF'yi kaydet (annotation'lar JSON sidecar'a ayrı kaydedilir)"""
        if not self.pdf_document:
            messagebox.showwarning("Uyarı", "Kaydetmek için bir PDF dosyası yükleyin.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="PDF'yi Kaydet",
            defaultextension=".pdf",
            filetypes=[("PDF dosyaları", "*.pdf")]
        )
        
        if file_path:
            try:
                # PDF'yi kaydet (annotation'lar fitz'e gömülmeden)
                self.pdf_document.save(file_path, garbage=4, deflate=True)
                
                # Annotation'ları JSON sidecar'a kaydet (aynı klasör, aynı isim + .ann.json)
                if hasattr(self, 'annotation_manager') and self.annotation_manager.annotations:
                    base = os.path.splitext(file_path)[0]
                    ann_path = base + '.ann.json'
                    anns_to_save = [
                        {k: v for k, v in ann.items() if k != 'canvas_id'}
                        for ann in self.annotation_manager.annotations
                    ]
                    with open(ann_path, 'w', encoding='utf-8') as f:
                        json.dump(anns_to_save, f, indent=2, ensure_ascii=False)
                    print(f"DEBUG: {len(anns_to_save)} annotation JSON sidecar'a kaydedildi: {os.path.basename(ann_path)}")
                
                messagebox.showinfo("Başarılı", f"PDF başarıyla kaydedildi:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Hata", f"PDF kaydedilirken hata oluştu:\n{str(e)}")
    
    def load_settings(self):
        """Ayarları yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.highlight_color = settings.get('highlight_color', '#FFFF00')
                    self.zoom_level = settings.get('zoom_level', 1.0)
        except Exception:
            pass
    
    def save_settings(self):
        """Ayarları kaydet"""
        try:
            settings = {
                'highlight_color': self.highlight_color,
                'zoom_level': self.zoom_level,
                'last_opened': datetime.now().isoformat()
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def on_closing(self):
        """Program kapanırken"""
        try:
            print("Program kapatılıyor...")
            
            # Ayarları kaydet
            self.save_settings()
            
            # Tooltip'i temizle
            if hasattr(self, 'tooltip_window') and self.tooltip_window:
                try:
                    self.tooltip_window.destroy()
                except:
                    pass
            
            # PDF dokümanını kapat
            if self.pdf_document:
                try:
                    self.pdf_document.close()
                except:
                    pass
            
            # Annotation manager'ı temizle
            if hasattr(self, 'annotation_manager'):
                try:
                    if hasattr(self.annotation_manager, 'window') and self.annotation_manager.window.winfo_exists():
                        self.annotation_manager.safe_close_window()
                except:
                    pass
            
            # Ana pencereyi kapat
            self.root.quit()
            self.root.destroy()
            
            print("Program başarıyla kapatıldı.")
            
        except Exception as e:
            print(f"Program kapatma hatası: {e}")
            # Force close
            try:
                self.root.quit()
            except:
                pass
    
    def load_existing_annotations(self):
        """PDF ile aynı klasördeki JSON sidecar dosyasından annotation'ları yükle"""
        if not self.pdf_document:
            return
            
        try:
            pdf_path = self.pdf_document.name
            if not pdf_path:
                return
            
            base = os.path.splitext(pdf_path)[0]
            ann_path = base + '.ann.json'
            
            if os.path.exists(ann_path):
                with open(ann_path, 'r', encoding='utf-8') as f:
                    annotations = json.load(f)
                
                for ann in annotations:
                    ann.pop('canvas_id', None)  # Eski canvas ID'leri temizle
                    self.annotation_manager.add_annotation(ann)
                
                print(f"DEBUG: {len(annotations)} annotation JSON'dan yüklendi: {os.path.basename(ann_path)}")
            else:
                print(f"DEBUG: Sidecar bulunamadı, annotation yok: {os.path.basename(pdf_path)}")
                
        except Exception as e:
            print(f"Annotation yükleme hatası: {e}")
