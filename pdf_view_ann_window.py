"""
PDF Viewer - Annotation Pencere ve Liste Yönetimi (Mixin)
Pencere oluşturma, liste görüntüleme, scroll, silme/gitme işlemleri
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime

from pdf_view_utils import center_window


class AnnWindowMixin:
    """Annotation penceresi ve liste yönetimi metodlarını içeren mixin sınıfı"""

    def create_annotation_window(self):
        """Annotation araçları penceresini oluştur - ScrollableFrame olmadan"""
        try:
            # Zaten açık mı kontrol et
            if hasattr(self, 'annotation_window') and self.annotation_window:
                try:
                    if self.annotation_window.winfo_exists():
                        self.annotation_window.lift()
                        self.annotation_window.focus()
                        return
                except:
                    self.annotation_window = None

            # Yeni pencere oluştur
            self.annotation_window = ctk.CTkToplevel(self.pdf_viewer.root)
            self.annotation_window.title("Gelişmiş Annotation Yönetimi")
            self.annotation_window.geometry("1080x900+100+50")

            self.annotation_window.bind('<Escape>', lambda e: self.annotation_window.destroy())

            # Ana pencereye göre ortalama
            self.annotation_window.transient(self.pdf_viewer.root)
            center_window(self.annotation_window, 1080, 900)

            # Pencere kapanma kontrolü
            self.annotation_window.protocol("WM_DELETE_WINDOW", self.safe_close_window)

            # Ana başlık
            title_frame = ctk.CTkFrame(self.annotation_window)
            title_frame.pack(fill="x", padx=10, pady=10)

            title_label = ctk.CTkLabel(title_frame,
                                     text="📝 Gelişmiş Annotation Araçları",
                                     font=ctk.CTkFont(size=20, weight="bold"))
            title_label.pack(pady=10)

            # Annotation türü seçimi
            type_frame = ctk.CTkFrame(self.annotation_window)
            type_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(type_frame, text="Annotation Türü:",
                        font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

            self.annotation_type_var = ctk.StringVar(value="highlight")
            type_options = [
                ("🖍️ Vurgulama", "highlight"),
                ("📝 Not", "note"),
                ("⭐ İşaret", "bookmark"),
                ("🔗 Link", "link")
            ]

            button_frame = ctk.CTkFrame(type_frame)
            button_frame.pack(pady=5)

            for text, value in type_options:
                ctk.CTkRadioButton(button_frame, text=text, variable=self.annotation_type_var,
                                  value=value, command=self.on_type_change).pack(side="left", padx=15, pady=5)

            # Renk seçimi frame
            self.color_frame = ctk.CTkFrame(self.annotation_window)
            self.color_frame.pack(fill="x", padx=10, pady=5)
            self.setup_color_selection()

            # Not/Link ekleme frame
            self.input_frame = ctk.CTkFrame(self.annotation_window)
            self.input_frame.pack(fill="x", padx=10, pady=5)
            self.setup_input_controls()

            # Arama ve filtre bölümü
            filter_frame = ctk.CTkFrame(self.annotation_window)
            filter_frame.pack(fill="x", padx=10, pady=5)

            search_label = ctk.CTkLabel(filter_frame, text="🔍 Arama:")
            search_label.pack(side="left", padx=(10, 5), pady=10)

            self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Annotation'larda ara...")
            self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
            self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_change())

            # İstatistik gösterimi
            self.count_label = ctk.CTkLabel(filter_frame, text="")
            self.count_label.pack(side="right", padx=10, pady=10)

            # **SABIT ÇÖZÜM: Normal Frame + Scrollbar kullan**
            list_frame = ctk.CTkFrame(self.annotation_window)
            list_frame.pack(fill="both", expand=True, padx=10, pady=5)

            # Liste başlığı
            list_header = ctk.CTkLabel(list_frame, text="Mevcut Annotation'lar:",
                                     font=ctk.CTkFont(size=14, weight="bold"))
            list_header.pack(pady=5)

            # Canvas ve scrollbar
            self.canvas = tk.Canvas(list_frame, bg='gray17', highlightthickness=0)
            self.scrollbar = ctk.CTkScrollbar(list_frame, command=self.canvas.yview)
            self.scrollable_frame = ctk.CTkFrame(self.canvas)

            # Scrollbar konfigürasyonu
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            # Pack layout
            self.scrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)

            # Canvas içindeki frame
            self.canvas_frame_id = self.canvas.create_window((0, 0),
                                                           window=self.scrollable_frame,
                                                           anchor="nw")

            # Mouse wheel binding
            self.bind_mousewheel()

            # Frame boyutları ayarla
            self.scrollable_frame.bind('<Configure>', self.configure_scroll_region)
            self.canvas.bind('<Configure>', self.configure_canvas_width)

            # Annotation listesi container
            self.annotation_list = ctk.CTkFrame(self.scrollable_frame)
            self.annotation_list.pack(fill="both", expand=True, padx=10, pady=10)

            # Alt kontrol butonları
            self.control_frame = ctk.CTkFrame(self.annotation_window)
            self.control_frame.pack(fill="x", padx=10, pady=10)
            self.setup_control_buttons()

            # Pencere göster
            self.annotation_window.focus()

            # Listeyi yenile
            self.refresh_annotation_list()

            # İlk değerleri ayarla
            self.on_type_change()

            self.annotation_window.focus()

        except Exception as e:
            print(f"Annotation penceresi açma hatası: {e}")
            self.annotation_window = None

    def bind_mousewheel(self):
        """Mouse wheel scrolling"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind mouse wheel to canvas
        self.canvas.bind("<MouseWheel>", _on_mousewheel)

        # Bind to scrollable frame too
        self.scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    def configure_scroll_region(self, event):
        """Canvas scroll region'ını güncelle"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configure_canvas_width(self, event):
        """Canvas width'ini ayarla"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_id, width=canvas_width)

    def safe_close_window(self):
        """Güvenli pencere kapanması"""
        try:
            # print("Annotation penceresi kapatılıyor...")

            # Widget'ları temizle
            if hasattr(self, 'annotation_list'):
                try:
                    if self.annotation_list.winfo_exists():
                        # Normal widget cleanup - hiç destroy etme
                        for child in list(self.annotation_list.winfo_children()):
                            try:
                                child.pack_forget()
                            except:
                                pass
                except:
                    pass

            # Canvas cleanup
            if hasattr(self, 'canvas'):
                try:
                    self.canvas.delete("all")
                except:
                    pass

            # Ana pencereyi kapat
            if hasattr(self, 'annotation_window'):
                try:
                    self.annotation_window.destroy()
                    # print("Annotation penceresi başarıyla kapatıldı.")
                except:
                    pass

        except Exception as e:
            print(f"Pencere kapanma hatası: {e}")

    def refresh_annotation_list(self):
        """Annotation listesini yenile"""
        try:
            # Widget varlığı kontrolü
            if not hasattr(self, 'annotation_list') or not self.annotation_list.winfo_exists():
                return

            # Mevcut widget'ları SADECE forget et (destroy etme!)
            for child in list(self.annotation_list.winfo_children()):
                try:
                    child.pack_forget()
                except:
                    pass

            # UI güncelleme
            self.pdf_viewer.root.update_idletasks()

            # Annotation sayısını güncelle
            try:
                if hasattr(self, 'count_label') and self.count_label.winfo_exists():
                    annotation_count = len(self.annotations)
                    self.count_label.configure(text=f"Toplam: {annotation_count} annotation")
            except:
                pass

            # Arama filtresi
            search_term = ""
            if hasattr(self, 'search_entry'):
                try:
                    if self.search_entry.winfo_exists():
                        search_term = self.search_entry.get().lower()
                except:
                    search_term = ""

            # Filtered annotations
            filtered_annotations = []
            for i, annotation in enumerate(self.annotations):
                if not search_term or search_term in annotation.get("text", "").lower():
                    filtered_annotations.append((i, annotation))

            # Annotation items oluştur
            for original_index, annotation in filtered_annotations:
                try:
                    self.create_annotation_item(original_index, annotation)
                except Exception as e:
                    print(f"Annotation item oluşturma hatası: {e}")
                    continue

            # Boş liste mesajı
            if not filtered_annotations:
                try:
                    empty_label = ctk.CTkLabel(self.annotation_list,
                                             text="Annotation bulunamadı" if search_term else "Henüz annotation eklenmedi")
                    empty_label.pack(pady=20)
                except:
                    pass

            # Scroll region güncelle
            self.pdf_viewer.root.after(100, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        except Exception as e:
            print(f"Refresh annotation list hatası: {e}")

    def create_annotation_item(self, index, annotation):
        """Annotation item oluştur"""
        try:
            item_frame = ctk.CTkFrame(self.annotation_list)
            item_frame.pack(fill="x", pady=2)

            # Ana bilgiler
            info_frame = ctk.CTkFrame(item_frame)
            info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)

            # Tür ikonu ve sayfa
            type_icons = {"highlight": "🖍️", "note": "📝", "bookmark": "⭐", "link": "🔗"}
            icon = type_icons.get(annotation["type"], "📄")

            header_text = f"{icon} Sayfa {annotation['page'] + 1} - {annotation['type'].title()}"

            header_label = ctk.CTkLabel(info_frame, text=header_text, font=ctk.CTkFont(weight="bold"))
            header_label.pack(anchor="w")

            # İçerik
            if annotation["type"] == "note":
                content = annotation.get("text", "")[:50]
                if len(annotation.get("text", "")) > 50:
                    content += "..."
                content_label = ctk.CTkLabel(info_frame, text=content, text_color="gray")
                content_label.pack(anchor="w")
            elif annotation["type"] == "highlight":
                color_text = f"Renk: {annotation.get('color', '#FFFF00')}"
                color_label = ctk.CTkLabel(info_frame, text=color_text, text_color="gray")
                color_label.pack(anchor="w")
            elif annotation["type"] == "link":
                url_text = f"URL: {annotation.get('url', '')[:30]}..."
                url_label = ctk.CTkLabel(info_frame, text=url_text, text_color="gray")
                url_label.pack(anchor="w")

            # Zaman damgası
            try:
                timestamp = datetime.fromisoformat(annotation["timestamp"]).strftime("%d.%m.%Y %H:%M")
                time_label = ctk.CTkLabel(info_frame, text=timestamp, text_color="gray",
                                        font=ctk.CTkFont(size=10))
                time_label.pack(anchor="w")
            except:
                pass

            # Kontrol butonları
            button_frame = ctk.CTkFrame(item_frame)
            button_frame.pack(side="right", padx=5, pady=5)

            goto_btn = ctk.CTkButton(button_frame, text="Git", width=50,
                                   command=lambda: self.safe_goto_annotation(annotation))
            goto_btn.pack(pady=1)

            delete_btn = ctk.CTkButton(button_frame, text="Sil", width=50,
                                     command=lambda idx=index: self.safe_delete_annotation(idx))
            delete_btn.pack(pady=1)

        except Exception as e:
            print(f"Annotation item oluşturma hatası: {e}")

    def safe_goto_annotation(self, annotation):
        """Annotation'a güvenli git"""
        try:
            page_num = annotation["page"]
            if hasattr(self.pdf_viewer, 'go_to_page'):
                self.pdf_viewer.go_to_page(page_num + 1)  # 1-indexed
            elif hasattr(self.pdf_viewer, 'current_page'):
                self.pdf_viewer.current_page = page_num
                self.pdf_viewer.display_page()
        except Exception as e:
            print(f"Goto annotation hatası: {e}")

    def safe_delete_annotation(self, index):
        """Annotation'ı güvenli sil"""
        try:
            if 0 <= index < len(self.annotations):
                # Annotation'ı sil
                deleted_annotation = self.annotations[index]
                del self.annotations[index]

                # Canvas'tan temizle
                self.clear_annotation_from_canvas(deleted_annotation)

                # PDF viewer'da display'i yenile
                if hasattr(self.pdf_viewer, 'display_page'):
                    self.pdf_viewer.display_page()

                # Liste'yi yenile
                self.refresh_annotation_list()

                # print(f"Annotation silindi: {deleted_annotation.get('type', 'unknown')} - Sayfa {deleted_annotation.get('page', '?')}")

        except Exception as e:
            print(f"Delete annotation hatası: {e}")

    def clear_annotation_from_canvas(self, annotation):
        """Canvas'tan annotation'ı temizle - Geliştirilmiş versiyon"""
        try:
            if hasattr(self.pdf_viewer, 'canvas') and self.pdf_viewer.canvas:
                canvas = self.pdf_viewer.canvas

                # Canvas ID varsa direkt sil
                if 'canvas_id' in annotation:
                    try:
                        canvas.delete(annotation['canvas_id'])
                        # print(f"Canvas'tan silindi: ID {annotation['canvas_id']}")
                    except:
                        pass

                # Annotation türüne göre temizlik
                if annotation['type'] == 'highlight':
                    # Highlight'ları temizle
                    highlight_items = canvas.find_withtag("highlight")
                    for item in highlight_items:
                        try:
                            canvas.delete(item)
                        except:
                            pass

                elif annotation['type'] in ['note', 'link', 'bookmark']:
                    # Text annotation'ları temizle
                    annotation_items = canvas.find_withtag("annotation")
                    for item in annotation_items:
                        try:
                            # Pozisyon eşleşmesi kontrol et
                            coords = canvas.coords(item)
                            if coords:
                                pos = annotation.get('position', {})
                                if (abs(coords[0] - pos.get('x', 0)) < 30 and
                                    abs(coords[1] - pos.get('y', 0)) < 30):
                                    canvas.delete(item)
                                    # print(f"Pozisyon eşleşmesi ile silindi: {coords}")
                                    break
                        except:
                            pass

                # Genel temizlik - tüm annotation tag'leri
                try:
                    canvas.delete("temp_highlight")
                except:
                    pass

        except Exception as e:
            print(f"Clear annotation from canvas hatası: {e}")

    def on_search_change(self):
        """Arama değişikliği"""
        try:
            self.refresh_annotation_list()
        except Exception as e:
            print(f"Search change hatası: {e}")
