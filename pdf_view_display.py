"""
PDF Viewer - Görüntüleme Mixin'i
Sayfa görüntüleme, küçük resimler ve highlight gösterimi
"""

import customtkinter as ctk
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
from tkinter import messagebox


class DisplayMixin:
    """Sayfa görüntüleme metodlarını içeren mixin sınıfı"""
    
    def create_thumbnails(self, progress_bar, progress_label, progress_window):
        """Sayfa küçük resimlerini oluştur"""
        try:
            # Mevcut küçük resimleri FORGET ile güvenli şekilde temizle (destroy değil!)
            children_to_forget = []
            try:
                children_to_forget = list(self.thumbnail_frame.winfo_children())
            except:
                pass
                
            for widget in children_to_forget:
                try:
                    if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                        # Widget'ı destroy değil pack_forget ile temizle
                        if hasattr(widget, 'pack_forget'):
                            widget.pack_forget()
                        if hasattr(widget, 'grid_forget'):
                            widget.grid_forget()
                        if hasattr(widget, 'place_forget'):
                            widget.place_forget()
                except Exception as e:
                    print(f"Thumbnail widget temizleme hatası: {e}")
                    continue
            
            # Update tasks'ları tamamla
            self.root.update_idletasks()
            
            for page_num in range(self.total_pages):
                try:
                    progress = 0.3 + (page_num / self.total_pages) * 0.5
                    progress_bar.set(progress)
                    progress_label.configure(text=f"Küçük resimler oluşturuluyor... ({page_num + 1}/{self.total_pages})")
                    progress_window.update()
                    
                    # Küçük resim oluştur
                    page = self.pdf_document[page_num]
                    mat = fitz.Matrix(0.2, 0.2)  # Küçük boyut için
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("ppm")
                    
                    # PIL Image'e çevir
                    img = Image.open(io.BytesIO(img_data))
                    
                    # CTkImage kullan (HighDPI desteği için)
                    ctk_image = ctk.CTkImage(light_image=img, dark_image=img, 
                                           size=(150, int(150 * img.height / img.width)))
                    
                    # Küçük resim frame'i
                    thumb_frame = ctk.CTkFrame(self.thumbnail_frame)
                    thumb_frame.pack(fill="x", padx=5, pady=2)
                    
                    # Sayfa numarası
                    page_label = ctk.CTkLabel(thumb_frame, text=f"Sayfa {page_num + 1}")
                    page_label.pack(pady=2)
                    
                    # Küçük resim butonu
                    thumb_btn = ctk.CTkButton(
                        thumb_frame, 
                        text="",
                        image=ctk_image,
                        width=150,
                        height=int(150 * img.height / img.width),
                        command=lambda p=page_num: self.goto_page_direct(p)
                    )
                    thumb_btn.pack(pady=2)
                    
                    # Resmi sakla (garbage collection'dan korunması için)
                    thumb_btn.image = ctk_image
                    
                except Exception as e:
                    print(f"Sayfa {page_num + 1} küçük resmi oluşturma hatası: {e}")
                    continue
                    
            # Thumbnail oluşturma sonunda scroll region'ı güncelle
            self.root.after(100, lambda: self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all")))
                    
        except Exception as e:
            print(f"Küçük resim oluşturma genel hatası: {e}")
    
    def display_page(self):
        """Mevcut sayfayı görüntüle"""
        if not self.pdf_document:
            return
        
        try:
            page = self.pdf_document[self.current_page]
            
            # Zoom ve rotasyon matrisi
            mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
            pix = page.get_pixmap(matrix=mat)
            
            # Canvas boyutlarını kaydet (koordinat dönüşümü için)
            self.current_page_width = pix.width
            self.current_page_height = pix.height
            
            # PIL Image'e çevir
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            self.current_image = ImageTk.PhotoImage(img)
            
            # Canvas'ı temizle ve yeni resmi ekle
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.current_image)
            
            # Canvas scroll bölgesini güncelle
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Annotation'ları PDF'den yükle ve göster
            try:
                self.load_pdf_annotations()
                self.show_highlights()
            except Exception as e:
                print(f"Annotation gösterme hatası: {e}")
            
        except Exception as e:
            print(f"Sayfa görüntülenirken hata oluştu: {e}")
            messagebox.showerror("Hata", f"Sayfa görüntülenirken hata oluştu:\n{str(e)}")
    
    def show_highlights(self):
        """Mevcut sayfadaki annotation_manager annotation'larını göster.
        Fitz native annotation'lar load_pdf_annotations() tarafından ayrıca yüklenir."""
        if not self.pdf_document:
            return
        
        try:
            # Kendi annotation manager'daki annotation'ları göster
            if hasattr(self, 'annotation_manager'):
                for i, annotation in enumerate(self.annotation_manager.annotations):
                    if annotation["page"] == self.current_page:
                        idx_tag = f"ann_idx_{i}"
                        if annotation["type"] == "highlight":
                            coords = annotation.get("coordinates", {})
                            if coords:
                                x1, y1 = coords.get('x1', 0), coords.get('y1', 0)
                                x2, y2 = coords.get('x2', 100), coords.get('y2', 100)
                                color = annotation.get('color', '#FFFF00')
                                cid = self.canvas.create_rectangle(
                                    x1, y1, x2, y2,
                                    fill=color,
                                    stipple="gray50",
                                    outline="",
                                    tags=("annotation_display", idx_tag)
                                )
                                annotation['canvas_id'] = cid
                        elif annotation["type"] == "note":
                            pos = annotation["position"]
                            mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
                            point = fitz.Point(pos["x"], pos["y"]) * mat
                            cid = self.canvas.create_text(
                                point.x, point.y,
                                text="📝",
                                font=("Arial", 16),
                                fill="green",
                                tags=("custom_note", idx_tag)
                            )
                            annotation['canvas_id'] = cid
                        elif annotation["type"] == "bookmark":
                            pos = annotation.get("position", {"x": 18, "y": 18})
                            mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
                            point = fitz.Point(pos["x"], pos["y"]) * mat
                            cid = self.canvas.create_text(
                                point.x, point.y,
                                text="⭐",
                                font=("Arial", 16),
                                fill="orange",
                                tags=("custom_bookmark", idx_tag)
                            )
                            annotation['canvas_id'] = cid
                        elif annotation["type"] == "link":
                            pos = annotation["position"]
                            mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
                            point = fitz.Point(pos["x"], pos["y"]) * mat
                            cid = self.canvas.create_text(
                                point.x, point.y,
                                text="🔗",
                                font=("Arial", 16),
                                fill="#0099ff",
                                tags=("custom_link", idx_tag)
                            )
                            annotation['canvas_id'] = cid
        
        except Exception as e:
            print(f"Highlight gösterme hatası: {e}")
            
        # Eğer not toolbox'ı açıksa, mevcut notları göster
        if hasattr(self, 'note_manager') and self.note_manager.notes_visible:
            self.note_manager.display_notes_for_page(self.current_page)
    
    def load_pdf_annotations(self):
        """PDF'deki annotation'ları yükle ve canvas'ta göster"""
        try:
            if not self.pdf_document:
                return
                
            page = self.pdf_document[self.current_page]
            
            # PDF koordinatlarını Canvas koordinatlarına çevir
            def pdf_to_canvas_coords(pdf_x, pdf_y):
                """PDF koordinatlarını Canvas koordinatlarına çevir"""
                try:
                    # PDF sayfasının boyutlarını al
                    page_rect = page.rect
                    pdf_width = page_rect.width
                    pdf_height = page_rect.height
                    
                    # Canvas boyutlarını al
                    canvas_width = getattr(self, 'current_page_width', pdf_width)
                    canvas_height = getattr(self, 'current_page_height', pdf_height)
                    
                    # Ölçeklendirme faktörlerini hesapla
                    scale_x = canvas_width / pdf_width if pdf_width > 0 else 1
                    scale_y = canvas_height / pdf_height if pdf_height > 0 else 1
                    
                    # Canvas koordinatlarına çevir
                    canvas_x = pdf_x * scale_x
                    canvas_y = pdf_y * scale_y
                    
                    return canvas_x, canvas_y
                except:
                    return pdf_x, pdf_y
            
            # PDF'deki annotation'ları al
            for annot in page.annots():
                try:
                    annot_type = annot.type[1]  # Annotation tipi
                    rect = annot.rect

                    if annot_type in ['Highlight', 'Square']:
                        # PDF koordinatlarını Canvas koordinatlarına çevir
                        x1, y1 = pdf_to_canvas_coords(rect.x0, rect.y0)
                        x2, y2 = pdf_to_canvas_coords(rect.x1, rect.y1)

                        # Rengi al — önce fill, yoksa stroke (Highlight için stroke'ta tutulur)
                        colors = annot.colors
                        hex_color = "#FFFF00"  # varsayılan
                        if colors:
                            fill = colors.get('fill')
                            stroke = colors.get('stroke')
                            if fill:
                                hex_color = f"#{int(fill[0]*255):02x}{int(fill[1]*255):02x}{int(fill[2]*255):02x}"
                            elif stroke:
                                hex_color = f"#{int(stroke[0]*255):02x}{int(stroke[1]*255):02x}{int(stroke[2]*255):02x}"

                        # Tüm vurgulama tipleri aynı şekilde çizilir:
                        # stipple="gray50" → yarı saydamlık, outline="" → kenarlık yok
                        # Bu, show_highlights() ile çizilen orijinal görünümle birebir eşleşir.
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2,
                            fill=hex_color,
                            stipple="gray50",
                            outline="",
                            tags="pdf_annotation"
                        )
                        # print(f"DEBUG [load_pdf_annots]: {annot_type} yüklendi → "
                        #       f"canvas({x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}) renk:{hex_color}")

                    elif annot_type == 'Text':
                        # Not / İşaret / Bağlantı (Text annotation) — ikon olarak göster
                        x1, y1 = pdf_to_canvas_coords(rect.x0, rect.y0)
                        title = annot.info.get('title', '')
                        content = annot.info.get('content', '')
                        icon = annot.info.get('icon', 'Note')
                        if icon == 'Star':
                            symbol, color = "⭐", "orange"
                        elif icon == 'Key':
                            symbol, color = "🔗", "#0099ff"
                        else:
                            symbol, color = "📝", "green"
                        self.canvas.create_text(
                            x1, y1,
                            text=symbol,
                            font=("Arial", 16),
                            fill=color,
                            tags="pdf_annotation"
                        )
                        # print(f"DEBUG [load_pdf_annots]: Text({icon}) yüklendi → canvas({x1:.1f},{y1:.1f})")

                except Exception as e:
                    print(f"Annotation işleme hatası: {e}")
                    
        except Exception as e:
            print(f"PDF annotation yükleme hatası: {e}")

    def clear_previous_annotations(self):
        """Önceki PDF'in annotation'larını temizle"""
        try:
            # Canvas'tan tüm annotation'ları temizle
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.delete("highlight")
                self.canvas.delete("annotation") 
                self.canvas.delete("temp_highlight")
                self.canvas.delete("note_icon")
                self.canvas.delete("link_icon")
                self.canvas.delete("bookmark_icon")
                self.canvas.delete("pdf_annotation")  # PDF'den yüklenen annotation'lar
            
            # Annotation manager'daki annotation'ları temizle
            if hasattr(self, 'annotation_manager') and self.annotation_manager:
                self.annotation_manager.annotations.clear()
                # Annotation listesini yenile
                if hasattr(self.annotation_manager, 'refresh_annotation_list'):
                    self.annotation_manager.refresh_annotation_list()
            
            # Highlight selection'ları temizle
            if hasattr(self, 'highlight_selections'):
                self.highlight_selections.clear()
                
            # print("Önceki annotation'lar temizlendi.")
            
        except Exception as e:
            print(f"Önceki annotation'ları temizleme hatası: {e}")
