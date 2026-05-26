"""
PDF Viewer - Annotation Yöneticisi (Ana Sınıf)
Annotation CRUD işlemleri, PDF entegrasyonu, içe/dışa aktarım
"""

import customtkinter as ctk
import json
import os

from pdf_view_ann_window import AnnWindowMixin
from pdf_view_ann_controls import AnnControlsMixin


class AnnotationManager(AnnWindowMixin, AnnControlsMixin):
    """Annotation yöneticisi - tüm annotation işlemlerini koordine eder"""

    def __init__(self, pdf_viewer):
        self.pdf_viewer = pdf_viewer
        # PDF viewer'ın annotations listesini direkt kullan
        self.annotations = getattr(pdf_viewer, 'annotations', [])
        self.current_annotation_type = "highlight"
        self.annotation_window = None

        # PDF viewer methods compatibility
        self.setup_annotation_compatibility()

    def handle_error(self, error, operation="İşlem"):
        """Hataları hem terminale hem GUI'ye yazdır"""
        import traceback
        error_msg = f"{operation} hatası: {error}"
        detailed_error = f"{error_msg}\n{traceback.format_exc()}"

        # Terminale yazdır
        print(detailed_error)

        # GUI'ye göster
        try:
            from tkinter import messagebox
            messagebox.showerror("Hata", error_msg)
        except:
            pass  # GUI hata verirse silent fail

    def setup_annotation_compatibility(self):
        """Ana PDF viewer ile uyumluluk metodları"""
        # Eğer PDF viewer'da annotations yoksa oluştur
        if not hasattr(self.pdf_viewer, 'annotations'):
            self.pdf_viewer.annotations = []

        # Annotations referansını senkronize et
        self.annotations = self.pdf_viewer.annotations

    def add_annotation(self, annotation):
        """Annotation ekleme (genel metod)"""
        try:
            self.annotations.append(annotation)
            self.refresh_annotation_list()
        except Exception as e:
            print(f"Annotation ekleme hatası: {e}")

    def add_bookmark_annotation(self, page, text):
        """İşaret annotation'ı ekleme"""
        try:
            annotation = {
                'page': page,
                'type': 'bookmark',
                'text': text,
                'position': self._next_annotation_position(page),
                'timestamp': self.get_timestamp()
            }
            self.add_annotation(annotation)
            return annotation
        except Exception as e:
            print(f"İşaret annotation ekleme hatası: {e}")
            return None

    def add_link_annotation(self, page, text, url):
        """Link annotation'ı ekleme"""
        try:
            annotation = {
                'page': page,
                'type': 'link',
                'text': text,
                'url': url,
                'position': self._next_annotation_position(page),
                'timestamp': self.get_timestamp()
            }
            self.add_annotation(annotation)
            return annotation
        except Exception as e:
            print(f"Link annotation ekleme hatası: {e}")
            return None

    def add_highlight_annotation(self, x1, y1, x2, y2, color="#FFFF00", text=""):
        """Highlight annotation ekleme"""
        try:
            current_page = getattr(self.pdf_viewer, 'current_page', 0)
            annotation = {
                'page': current_page,
                'type': 'highlight',
                'text': text,
                'color': color,
                'coordinates': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                'timestamp': self.get_timestamp()
            }
            self.add_annotation(annotation)
            return annotation
        except Exception as e:
            print(f"Highlight annotation ekleme hatası: {e}")
            return None

    def add_note_annotation(self, page, text):
        """Not annotation'ı ekleme"""
        try:
            annotation = {
                'page': page,
                'type': 'note',
                'text': text,
                'position': self._next_annotation_position(page),
                'timestamp': self.get_timestamp()
            }
            self.add_annotation(annotation)
            return annotation
        except Exception as e:
            print(f"Not annotation ekleme hatası: {e}")
            return None

    def _next_annotation_position(self, page):
        """Sayfadaki annotation'larla binismeyen bir sonraki ikon konumunu hesapla (PDF koord)"""
        existing = [
            a for a in self.annotations
            if a.get('page') == page and a.get('type') in ('note', 'bookmark', 'link')
        ]
        n = len(existing)
        return {'x': 18, 'y': 18 + n * 30}

    def get_timestamp(self):
        """Timestamp oluştur"""
        from datetime import datetime
        return datetime.now().isoformat()

    def export_annotations(self):
        """Annotation'ları JSON dosyasına aktar"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.annotations, f, ensure_ascii=False, indent=2)
                print(f"Annotation'lar dışa aktarıldı: {filename}")
        except Exception as e:
            print(f"Export annotations hatası: {e}")

    def import_annotations(self):
        """JSON dosyasından annotation'ları içe aktar"""
        try:
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_annotations = json.load(f)

                # Mevcut annotation'lara ekle
                self.annotations.extend(imported_annotations)

                # PDF viewer'ı da güncelle
                if hasattr(self.pdf_viewer, 'annotations'):
                    self.pdf_viewer.annotations = self.annotations

                # Listeyi yenile
                self.refresh_annotation_list()
                # print(f"Annotation'lar içe aktarıldı: {len(imported_annotations)} adet")

        except Exception as e:
            print(f"Import annotations hatası: {e}")

    def save_pdf_with_annotations(self):
        """PDF'i annotation'larla birlikte kaydet"""
        try:
            if not hasattr(self.pdf_viewer, 'pdf_document') or not self.pdf_viewer.pdf_document:
                print("PDF yüklü değil!")
                return

            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )

            if filename:
                # PDF'i annotation'larla birlikte kaydet
                doc = self.pdf_viewer.pdf_document

                # Her annotation'ı PDF'e ekle
                for annotation in self.annotations:
                    page_num = annotation.get('page', 0)
                    if 0 <= page_num < len(doc):
                        page = doc[page_num]

                        if annotation['type'] == 'highlight':
                            # Highlight annotation ekle
                            # Bu kısım PDF viewer'ın highlight metodunu kullanabilir
                            pass
                        elif annotation['type'] == 'note':
                            # Note annotation ekle
                            pass

                doc.save(filename)
                # print(f"PDF annotation'larla kaydedildi: {filename}")

        except Exception as e:
            print(f"Save PDF with annotations hatası: {e}")

    def clear_all_annotations(self):
        """Tüm annotation'ları temizle"""
        try:
            from tkinter import messagebox
            if messagebox.askyesno("Onay", "Tüm annotation'ları silmek istediğinizden emin misiniz?"):
                # Canvas'tan tüm annotation'ları temizle
                if hasattr(self.pdf_viewer, 'canvas') and self.pdf_viewer.canvas:
                    canvas = self.pdf_viewer.canvas

                    # Tüm annotation tag'lerini temizle
                    try:
                        canvas.delete("highlight")
                        canvas.delete("annotation")
                        canvas.delete("temp_highlight")
                    except:
                        pass

                    # Tüm annotation objelerini kontrol et
                    for annotation in self.annotations:
                        if 'canvas_id' in annotation:
                            try:
                                canvas.delete(annotation['canvas_id'])
                            except:
                                pass

                # Annotation listesini temizle
                self.annotations.clear()

                # PDF viewer'ı da güncelle
                if hasattr(self.pdf_viewer, 'annotations'):
                    self.pdf_viewer.annotations = self.annotations

                # Canvas'ı yenile
                if hasattr(self.pdf_viewer, 'display_page'):
                    self.pdf_viewer.display_page()

                # Listeyi yenile
                self.refresh_annotation_list()
                # print("Tüm annotation'lar temizlendi.")

        except Exception as e:
            print(f"Clear all annotations hatası: {e}")

    def add_pdf_annotation(self, annotation):
        """Annotation'ı PDF'e kalıcı olarak ekle"""
        try:
            if not hasattr(self.pdf_viewer, 'pdf_document') or not self.pdf_viewer.pdf_document:
                print("PDF belgesi yüklü değil, annotation PDF'e eklenemiyor.")
                return False

            doc = self.pdf_viewer.pdf_document
            page_num = annotation.get('page', 0)

            if page_num >= len(doc):
                print(f"Geçersiz sayfa numarası: {page_num}")
                return False

            page = doc[page_num]
            annotation_type = annotation.get('type', '')

            # Koordinat dönüşüm sistemi
            def canvas_to_pdf_coords(canvas_x, canvas_y):
                """Canvas koordinatlarını PDF koordinatlarına çevir"""
                try:
                    # PDF sayfasının boyutlarını al
                    page_rect = page.rect
                    pdf_width = page_rect.width
                    pdf_height = page_rect.height

                    # Canvas boyutlarını al
                    canvas_width = getattr(self.pdf_viewer, 'current_page_width', pdf_width)
                    canvas_height = getattr(self.pdf_viewer, 'current_page_height', pdf_height)

                    # Ölçeklendirme faktörlerini hesapla
                    scale_x = pdf_width / canvas_width if canvas_width > 0 else 1
                    scale_y = pdf_height / canvas_height if canvas_height > 0 else 1

                    # PDF koordinatlarına çevir
                    pdf_x = canvas_x * scale_x
                    pdf_y = canvas_y * scale_y

                    return pdf_x, pdf_y
                except:
                    return canvas_x, canvas_y  # Hata durumunda orijinal koordinatları döndür

            def hex_to_fitz_color(hex_color):
                """Hex color'ı PyMuPDF color'ına çevir"""
                try:
                    if not hex_color.startswith('#'):
                        hex_color = '#' + hex_color

                    # RGB değerlerini al
                    r = int(hex_color[1:3], 16) / 255.0
                    g = int(hex_color[3:5], 16) / 255.0
                    b = int(hex_color[5:7], 16) / 255.0

                    # print(f"Renk dönüşümü: {hex_color} -> RGB({r:.3f}, {g:.3f}, {b:.3f})")

                    return [r, g, b]
                except Exception as e:
                    print(f"Renk dönüşüm hatası {hex_color}: {e}")
                    return [1.0, 1.0, 0.0]  # Varsayılan sarı

            if annotation_type == 'highlight':
                # Square annotation ekle (dikdörtgen şekil korumak için)
                coords = annotation.get('coordinates', {})
                if coords:
                    import fitz

                    # Canvas koordinatlarını PDF koordinatlarına çevir
                    x1, y1 = canvas_to_pdf_coords(coords.get('x1', 0), coords.get('y1', 0))
                    x2, y2 = canvas_to_pdf_coords(coords.get('x2', 100), coords.get('y2', 100))

                    # print(f"Highlight koordinat dönüşümü: Canvas({coords.get('x1', 0)}, {coords.get('y1', 0)}, {coords.get('x2', 100)}, {coords.get('y2', 100)}) -> PDF({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")

                    rect = fitz.Rect(x1, y1, x2, y2)

                    # Dikdörtgen şekil korumak için Rectangle annotation kullan
                    rect_annot = page.add_rect_annot(rect)

                    # Rengi doğru şekilde ayarla
                    color = hex_to_fitz_color(annotation.get('color', '#FFFF00'))
                    rect_annot.set_colors(fill=color, stroke=color)
                    rect_annot.set_border(width=1)  # İnce çerçeve
                    rect_annot.set_opacity(0.5)  # Yarı şeffaf
                    rect_annot.update()

                    # print(f"PDF'e rectangle annotation eklendi: Renk {annotation.get('color', '#FFFF00')} -> {color}")

            elif annotation_type == 'note':
                # Not annotation ekle
                pos = annotation.get('position', {'x': 100, 'y': 100})
                import fitz
                point = fitz.Point(pos['x'], pos['y'])
                note = page.add_text_annot(point, annotation.get('text', 'Not'))
                note.update()

            elif annotation_type == 'bookmark':
                # Bookmark (işaret) ekle
                pos = annotation.get('position', {'x': 100, 'y': 100})
                import fitz
                point = fitz.Point(pos['x'], pos['y'])
                bookmark = page.add_text_annot(point, annotation.get('text', 'İşaret'))
                bookmark.set_info(title="İşaret", content=annotation.get('text', 'İşaret'))
                bookmark.update()

            elif annotation_type == 'link':
                # Link annotation ekle
                pos = annotation.get('position', {'x': 100, 'y': 100})
                import fitz
                rect = fitz.Rect(pos['x'], pos['y'], pos['x'] + 100, pos['y'] + 20)
                link = page.add_link_annot(rect, {"uri": annotation.get('url', 'http://example.com')})
                link.update()

            return True

        except Exception as e:
            error_msg = f"PDF annotation ekleme hatası: {e}"
            print(error_msg)  # Terminale yazdır
            return False
