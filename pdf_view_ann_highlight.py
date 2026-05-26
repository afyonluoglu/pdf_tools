"""
PDF Viewer - Vurgulama (Highlight) Aracı
Canvas üzerinde fareyle vurgulama çizme işlemleri
"""

import customtkinter as ctk
from datetime import datetime


class HighlightTool:
    """Highlight Tool - Annotation manager ile uyumlu"""

    def __init__(self, pdf_viewer):
        self.pdf_viewer = pdf_viewer
        self.is_active = False
        self.start_pos = None
        self.current_rect = None

    def activate(self):
        """Vurgulama aracını aktifleştir"""
        self.is_active = True
        self.pdf_viewer.canvas.bind("<Button-1>", self.start_highlight)
        self.pdf_viewer.canvas.bind("<B1-Motion>", self.update_highlight)
        self.pdf_viewer.canvas.bind("<ButtonRelease-1>", self.finish_highlight)
        self.pdf_viewer.canvas.configure(cursor="crosshair")

    def deactivate(self):
        """Vurgulama aracını deaktifleştir"""
        self.is_active = False
        if hasattr(self.pdf_viewer, 'on_canvas_click'):
            self.pdf_viewer.canvas.bind("<Button-1>", self.pdf_viewer.on_canvas_click)
        self.pdf_viewer.canvas.unbind("<B1-Motion>")
        self.pdf_viewer.canvas.unbind("<ButtonRelease-1>")
        self.pdf_viewer.canvas.configure(cursor="")

    def start_highlight(self, event):
        """Vurgulama başlat"""
        if not self.is_active:
            return

        self.start_pos = (self.pdf_viewer.canvas.canvasx(event.x),
                         self.pdf_viewer.canvas.canvasy(event.y))

    def update_highlight(self, event):
        """Vurgulama güncelle"""
        if not self.is_active or not self.start_pos:
            return

        current_pos = (self.pdf_viewer.canvas.canvasx(event.x),
                      self.pdf_viewer.canvas.canvasy(event.y))

        # Mevcut geçici dikdörtgeni sil
        if self.current_rect:
            self.pdf_viewer.canvas.delete(self.current_rect)

        # Yeni geçici dikdörtgen çiz
        self.current_rect = self.pdf_viewer.canvas.create_rectangle(
            self.start_pos[0], self.start_pos[1],
            current_pos[0], current_pos[1],
            outline="red", width=2, tags="temp_highlight"
        )

    def finish_highlight(self, event):
        """Vurgulama tamamla"""
        if not self.is_active or not self.start_pos:
            return

        end_pos = (self.pdf_viewer.canvas.canvasx(event.x),
                  self.pdf_viewer.canvas.canvasy(event.y))

        # Geçici dikdörtgeni sil
        if self.current_rect:
            self.pdf_viewer.canvas.delete(self.current_rect)

        # Vurgulama dikdörtgenini ekle
        self.add_highlight_rect(self.start_pos, end_pos)

        # Pozisyonları sıfırla
        self.start_pos = None
        self.current_rect = None

    def add_highlight_rect(self, start_pos, end_pos):
        """Vurgulama dikdörtgeni ekle"""
        try:
            # Koordinatları düzenle
            x1, y1 = min(start_pos[0], end_pos[0]), min(start_pos[1], end_pos[1])
            x2, y2 = max(start_pos[0], end_pos[0]), max(start_pos[1], end_pos[1])

            # Çok küçük dikdörtgenleri görmezden gel
            if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
                return

            # Canvas'ta vurgulama göster
            highlight_color = getattr(self.pdf_viewer, 'highlight_color', '#FFFF00')
            # print(f"Canvas'ta kullanılan renk: {highlight_color}")

            highlight_id = self.pdf_viewer.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=highlight_color,
                stipple="gray50",
                outline="",
                tags="highlight"
            )

            # PDF koordinatlarına çevir
            pdf_rect = [x1, y1, x2, y2]  # Basit koordinat sistemi

            # Annotation manager'a ekle
            if hasattr(self.pdf_viewer, 'annotation_manager'):
                annotation = self.pdf_viewer.annotation_manager.add_highlight_annotation(
                    x1, y1, x2, y2, highlight_color
                )

                # Canvas ID'yi annotation'a ekle
                if annotation:
                    annotation['canvas_id'] = highlight_id

        except Exception as e:
            print(f"Add highlight rect hatası: {e}")

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

    def clear_all_canvas_annotations(self):
        """Canvas'tan tüm annotation'ları temizle"""
        try:
            if hasattr(self.pdf_viewer, 'canvas') and self.pdf_viewer.canvas:
                canvas = self.pdf_viewer.canvas
                # Tüm annotation tag'lerini sil
                canvas.delete("highlight")
                canvas.delete("annotation")
                canvas.delete("temp_highlight")
                canvas.delete("note_icon")
                canvas.delete("link_icon")
                canvas.delete("bookmark_icon")
                # print("Canvas annotation'ları temizlendi.")
        except Exception as e:
            print(f"Canvas temizleme hatası: {e}")


def test_annotation_manager():
    """Annotation manager test"""
    # print("Annotation Manager test başlatılıyor...")

    from pdf_view_ann_core import AnnotationManager

    # Mock PDF viewer
    class MockPDFViewer:
        def __init__(self):
            self.root = ctk.CTk()
            self.root.title("Annotation Manager Test")
            self.root.geometry("400x300")
            self.annotations = [
                {
                    "type": "highlight",
                    "page": 0,
                    "color": "#FFFF00",
                    "timestamp": datetime.now().isoformat(),
                    "text": "Test highlight"
                },
                {
                    "type": "note",
                    "page": 1,
                    "text": "Bu bir test notu",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "bookmark",
                    "page": 2,
                    "text": "Test bookmark",
                    "timestamp": datetime.now().isoformat()
                }
            ]


    # Test GUI
    mock_viewer = MockPDFViewer()

    # Ana buton
    test_btn = ctk.CTkButton(mock_viewer.root,
                           text="Annotation Manager Aç",
                           command=lambda: AnnotationManager(mock_viewer).create_annotation_window())
    test_btn.pack(pady=50)

    mock_viewer.root.mainloop()


if __name__ == "__main__":
    test_annotation_manager()
