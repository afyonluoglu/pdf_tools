import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import json
import os

from pdf_view_utils import center_window

class FixedAnnotationManager:
    """CustomTkinter ScrollableFrame bug'ını çözen annotation manager"""
    
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
            print(f"Fixed annotation penceresi açma hatası: {e}")
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
        """Güvenli pencere kapanması - Fixed version"""
        try:
            print("Fixed annotation penceresi kapatılıyor...")
            
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
                    print("Fixed annotation penceresi başarıyla kapatıldı.")
                except:
                    pass
                
        except Exception as e:
            print(f"Fixed pencere kapanma hatası: {e}")
    
    def refresh_annotation_list(self):
        """Annotation listesini yenile - Fixed version"""
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
                    self.create_annotation_item_fixed(original_index, annotation)
                except Exception as e:
                    print(f"Fixed annotation item oluşturma hatası: {e}")
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
            print(f"Fixed refresh annotation list hatası: {e}")
    
    def create_annotation_item_fixed(self, index, annotation):
        """Fixed annotation item oluştur"""
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
            print(f"Fixed annotation item oluşturma hatası: {e}")
    
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
                
                print(f"Annotation silindi: {deleted_annotation.get('type', 'unknown')} - Sayfa {deleted_annotation.get('page', '?')}")
                
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
                        print(f"Canvas'tan silindi: ID {annotation['canvas_id']}")
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
                                    print(f"Pozisyon eşleşmesi ile silindi: {coords}")
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
    
    def setup_color_selection(self):
        """Renk seçimi alanını oluştur"""
        ctk.CTkLabel(self.color_frame, text="Vurgulama Rengi:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        colors_grid = ctk.CTkFrame(self.color_frame)
        colors_grid.pack(pady=5)
        
        # Hazır renkler
        self.highlight_colors = [
            ("#FFFF00", "Sarı"),
            ("#FF9999", "Açık Kırmızı"), 
            ("#99FF99", "Açık Yeşil"),
            ("#99CCFF", "Açık Mavi"),
            ("#FFB366", "Turuncu"),
            ("#FF99FF", "Pembe"),
            ("#CCCCCC", "Gri"),
            ("#FFFFFF", "Beyaz")
        ]
        
        self.selected_color = "#FFFF00"  # Varsayılan sarı
        
        for i, (color, name) in enumerate(self.highlight_colors):
            row = i // 4
            col = i % 4
            
            color_btn = ctk.CTkButton(
                colors_grid,
                text="",
                width=30,
                height=30,
                fg_color=color,
                hover_color=color,
                command=lambda c=color: self.set_highlight_color(c)
            )
            color_btn.grid(row=row, column=col, padx=2, pady=2)
        
        # Özel renk seçimi
        custom_btn = ctk.CTkButton(
            colors_grid,
            text="...",
            width=30,
            height=30,
            command=self.choose_custom_color
        )
        custom_btn.grid(row=1, column=0, padx=2, pady=2)
        
        # Seçili renk göstergesi
        self.color_display = ctk.CTkLabel(self.color_frame, text=f"Seçili: Sarı", 
                                        fg_color=self.selected_color, 
                                        corner_radius=5, width=100, height=30)
        self.color_display.pack(pady=5)
    
    def setup_input_controls(self):
        """Not ve link girişi için kontroller"""
        # Not girişi
        self.note_label = ctk.CTkLabel(self.input_frame, text="📝 Not Metni:", 
                                     font=ctk.CTkFont(size=14, weight="bold"))
        self.note_label.pack(pady=5)
        
        self.note_text = ctk.CTkTextbox(self.input_frame, height=80)
        self.note_text.pack(fill="x", padx=10, pady=5)
        
        # Link girişi
        self.link_label = ctk.CTkLabel(self.input_frame, text="🔗 Link URL:", 
                                     font=ctk.CTkFont(size=14, weight="bold"))
        self.link_label.pack(pady=5)
        
        self.link_entry = ctk.CTkEntry(self.input_frame, placeholder_text="https://example.com")
        self.link_entry.pack(fill="x", padx=10, pady=5)
    
    def setup_control_buttons(self):
        """Alt kontrol butonları"""
        # Manuel annotation ekleme butonları
        add_frame = ctk.CTkFrame(self.control_frame)
        add_frame.pack(side="left", padx=5)
        
        add_note_btn = ctk.CTkButton(add_frame, text="📝 Not Ekle",
                                   command=self.add_manual_note)
        add_note_btn.pack(side="left", padx=2)
        
        add_link_btn = ctk.CTkButton(add_frame, text="🔗 Link Ekle",
                                   command=self.add_manual_link)
        add_link_btn.pack(side="left", padx=2)
        
        add_bookmark_btn = ctk.CTkButton(add_frame, text="⭐ İşaret Ekle",
                                       command=self.add_manual_bookmark)
        add_bookmark_btn.pack(side="left", padx=2)
        
        # İçe/Dışa aktarım
        import_export_frame = ctk.CTkFrame(self.control_frame)
        import_export_frame.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(import_export_frame, text="📤 Dışa Aktar",
                                 command=self.export_annotations)
        export_btn.pack(side="left", padx=2)
        
        import_btn = ctk.CTkButton(import_export_frame, text="📥 İçe Aktar",
                                 command=self.import_annotations)
        import_btn.pack(side="left", padx=2)
        
        # PDF kaydetme
        save_frame = ctk.CTkFrame(self.control_frame)
        save_frame.pack(side="right", padx=5)
        
        save_pdf_btn = ctk.CTkButton(save_frame, text="💾 PDF Olarak Kaydet",
                                   command=self.save_pdf_with_annotations)
        save_pdf_btn.pack(side="left", padx=2)
        
        clear_btn = ctk.CTkButton(save_frame, text="🗑️ Tümünü Temizle",
                                command=self.clear_all_annotations)
        clear_btn.pack(side="left", padx=2)
    
    def on_type_change(self):
        """Annotation türü değiştiğinde UI'ı güncelle"""
        try:
            annotation_type = self.annotation_type_var.get()
            
            # Renk frame'ini göster/gizle
            if annotation_type == "highlight":
                self.color_frame.pack(fill="x", padx=10, pady=5)
                self.note_label.pack_forget()
                self.note_text.pack_forget()
                self.link_label.pack_forget()
                self.link_entry.pack_forget()
            elif annotation_type == "note":
                self.color_frame.pack_forget()
                self.note_label.pack(pady=5)
                self.note_text.pack(fill="x", padx=10, pady=5)
                self.link_label.pack_forget()
                self.link_entry.pack_forget()
            elif annotation_type == "link":
                self.color_frame.pack_forget()
                self.note_label.pack_forget()
                self.note_text.pack_forget()
                self.link_label.pack(pady=5)
                self.link_entry.pack(fill="x", padx=10, pady=5)
            else:  # bookmark
                self.color_frame.pack_forget()
                self.note_label.pack_forget()
                self.note_text.pack_forget()
                self.link_label.pack_forget()
                self.link_entry.pack_forget()
                
        except Exception as e:
            print(f"Type change hatası: {e}")
    
    def set_highlight_color(self, color):
        """Vurgulama rengini ayarla"""
        try:
            self.selected_color = color
            color_names = {
                "#FFFF00": "Sarı",
                "#FF9999": "Açık Kırmızı", 
                "#99FF99": "Açık Yeşil",
                "#99CCFF": "Açık Mavi",
                "#FFB366": "Turuncu",
                "#FF99FF": "Pembe",
                "#CCCCCC": "Gri",
                "#FFFFFF": "Beyaz"
            }
            color_name = color_names.get(color, "Özel")
            
            if hasattr(self, 'color_display'):
                self.color_display.configure(text=f"Seçili: {color_name}", fg_color=color)
                
            # PDF viewer'ın highlight color'ını da güncelle
            if hasattr(self.pdf_viewer, 'highlight_color'):
                self.pdf_viewer.highlight_color = color
                
        except Exception as e:
            print(f"Set highlight color hatası: {e}")
    
    def choose_custom_color(self):
        """Özel renk seçici"""
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Vurgulama Rengi Seç")[1]
            if color:
                self.set_highlight_color(color)
        except Exception as e:
            print(f"Custom color seçme hatası: {e}")
    
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
                print(f"Annotation'lar içe aktarıldı: {len(imported_annotations)} adet")
                
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
                print(f"PDF annotation'larla kaydedildi: {filename}")
                
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
                print("Tüm annotation'lar temizlendi.")
                
        except Exception as e:
            print(f"Clear all annotations hatası: {e}")
    
    def add_manual_note(self):
        """Manuel not ekleme"""
        try:
            # Not text'ini al
            if not hasattr(self, 'note_text') or not self.note_text.winfo_exists():
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Not metni alanı bulunamadı!")
                return
                
            note_content = self.note_text.get("1.0", "end-1c").strip()
            if not note_content:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Lütfen not metnini girin!")
                return
                
            # PDF yüklü mü kontrol et
            if not hasattr(self.pdf_viewer, 'pdf_document') or not self.pdf_viewer.pdf_document:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin!")
                return
                
            # Not annotation'ı oluştur
            current_page = getattr(self.pdf_viewer, 'current_page', 0)
            annotation = self.add_note_annotation(
                current_page, 
                note_content
            )
            
            if annotation:
                # Not text'ini temizle
                self.note_text.delete("1.0", "end")
                
                # Canvas'a not göstergesi ekle
                self.add_note_to_canvas(annotation)
                
                from tkinter import messagebox
                messagebox.showinfo("Başarılı", f"Not eklendi: {note_content[:30]}...")
                
        except Exception as e:
            print(f"Manuel not ekleme hatası: {e}")
    
    def add_manual_link(self):
        """Manuel link ekleme"""
        try:
            # Link URL'ini al
            if not hasattr(self, 'link_entry') or not self.link_entry.winfo_exists():
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Link URL alanı bulunamadı!")
                return
                
            link_url = self.link_entry.get().strip()
            if not link_url:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Lütfen link URL'si girin!")
                return
                
            # URL format kontrolü
            if not (link_url.startswith('http://') or link_url.startswith('https://')):
                link_url = 'https://' + link_url
                
            # PDF yüklü mü kontrol et
            if not hasattr(self.pdf_viewer, 'pdf_document') or not self.pdf_viewer.pdf_document:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin!")
                return
                
            # Link annotation'ı oluştur
            current_page = getattr(self.pdf_viewer, 'current_page', 0)
            annotation = self.add_link_annotation(
                current_page,
                f"Link - Sayfa {current_page + 1}",
                link_url
            )
            
            if annotation:
                # Link entry'yi temizle
                self.link_entry.delete(0, "end")
                
                # Canvas'a link göstergesi ekle
                self.add_link_to_canvas(annotation)
                
                from tkinter import messagebox
                messagebox.showinfo("Başarılı", f"Link eklendi: {link_url[:40]}...")
                
        except Exception as e:
            print(f"Manuel link ekleme hatası: {e}")
    
    def add_manual_bookmark(self):
        """Manuel işaret ekleme"""
        try:
            # PDF yüklü mü kontrol et
            if not hasattr(self.pdf_viewer, 'pdf_document') or not self.pdf_viewer.pdf_document:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin!")
                return
                
            # İşaret annotation'ı oluştur
            current_page = getattr(self.pdf_viewer, 'current_page', 0)
            bookmark_text = f"Sayfa {current_page + 1} İşareti"
            
            annotation = self.add_bookmark_annotation(current_page, bookmark_text)
            
            if annotation:
                # Canvas'a işaret göstergesi ekle
                self.add_bookmark_to_canvas(annotation)
                
                from tkinter import messagebox
                messagebox.showinfo("Başarılı", f"İşaret eklendi: {bookmark_text}")
                
        except Exception as e:
            print(f"Manuel işaret ekleme hatası: {e}")
    
    def add_note_to_canvas(self, annotation):
        """Canvas'a not göstergesi ekle"""
        try:
            if hasattr(self.pdf_viewer, 'canvas') and self.pdf_viewer.canvas:
                canvas = self.pdf_viewer.canvas
                pos = annotation.get('position', {'x': 100, 'y': 100})
                
                # Not ikonu ekle
                note_id = canvas.create_text(
                    pos['x'], pos['y'],
                    text="📝",
                    font=("Arial", 16),
                    fill="blue",
                    tags="annotation"
                )
                
                # Canvas ID'yi annotation'a ekle
                annotation['canvas_id'] = note_id
                
        except Exception as e:
            print(f"Canvas'a not ekleme hatası: {e}")
    
    def add_link_to_canvas(self, annotation):
        """Canvas'a link göstergesi ekle"""
        try:
            if hasattr(self.pdf_viewer, 'canvas') and self.pdf_viewer.canvas:
                canvas = self.pdf_viewer.canvas
                pos = annotation.get('position', {'x': 150, 'y': 150})
                
                # Link ikonu ekle
                link_id = canvas.create_text(
                    pos['x'], pos['y'],
                    text="🔗",
                    font=("Arial", 16),
                    fill="green",
                    tags="annotation"
                )
                
                # Canvas ID'yi annotation'a ekle
                annotation['canvas_id'] = link_id
                
        except Exception as e:
            print(f"Canvas'a link ekleme hatası: {e}")
    
    def add_bookmark_to_canvas(self, annotation):
        """Canvas'a işaret göstergesi ekle"""
        try:
            if hasattr(self.pdf_viewer, 'canvas') and self.pdf_viewer.canvas:
                canvas = self.pdf_viewer.canvas
                pos = annotation.get('position', {'x': 200, 'y': 100})
                
                # İşaret ikonu ekle
                bookmark_id = canvas.create_text(
                    pos['x'], pos['y'],
                    text="⭐",
                    font=("Arial", 16),
                    fill="orange",
                    tags="annotation"
                )
                
                # Canvas ID'yi annotation'a ekle
                annotation['canvas_id'] = bookmark_id
                
        except Exception as e:
            print(f"Canvas'a işaret ekleme hatası: {e}")

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
                    
                    print(f"Renk dönüşümü: {hex_color} -> RGB({r:.3f}, {g:.3f}, {b:.3f})")
                    
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
                    
                    print(f"Highlight koordinat dönüşümü: Canvas({coords.get('x1', 0)}, {coords.get('y1', 0)}, {coords.get('x2', 100)}, {coords.get('y2', 100)}) -> PDF({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
                    
                    rect = fitz.Rect(x1, y1, x2, y2)
                    
                    # Dikdörtgen şekil korumak için Rectangle annotation kullan
                    rect_annot = page.add_rect_annot(rect)
                    
                    # Rengi doğru şekilde ayarla
                    color = hex_to_fitz_color(annotation.get('color', '#FFFF00'))
                    rect_annot.set_colors(fill=color, stroke=color)
                    rect_annot.set_border(width=1)  # İnce çerçeve
                    rect_annot.set_opacity(0.5)  # Yarı şeffaf
                    rect_annot.update()
                    
                    print(f"PDF'e rectangle annotation eklendi: Renk {annotation.get('color', '#FFFF00')} -> {color}")
                    
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


class FixedHighlightTool:
    """Fixed Highlight Tool - Annotation manager ile uyumlu"""
    
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
            print(f"Canvas'ta kullanılan renk: {highlight_color}")
            
            highlight_id = self.pdf_viewer.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=highlight_color, 
                stipple="gray50",
                outline="", 
                tags="highlight"
            )
            
            # PDF koordinatlarına çevir
            pdf_rect = [x1, y1, x2, y2]  # Basit koordinat sistemi
            
            # Fixed Annotation manager'a ekle
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
                print("Canvas annotation'ları temizlendi.")
        except Exception as e:
            print(f"Canvas temizleme hatası: {e}")


def test_fixed_annotation_manager():
    """Fixed annotation manager test"""
    print("Fixed Annotation Manager test başlatılıyor...")
    
    # Mock PDF viewer
    class MockPDFViewer:
        def __init__(self):
            self.root = ctk.CTk()
            self.root.title("Fixed Annotation Manager Test")
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
            
        def center_window(self, window, width, height):
            """Pencereyi ortala"""
            window.geometry(f"{width}x{height}+{100}+{100}")
            
        def go_to_page(self, page_num):
            print(f"Sayfaya git: {page_num}")
    
    # Test GUI
    mock_viewer = MockPDFViewer()
    
    # Ana buton
    test_btn = ctk.CTkButton(mock_viewer.root, 
                           text="Fixed Annotation Manager Aç",
                           command=lambda: FixedAnnotationManager(mock_viewer).create_annotation_window())
    test_btn.pack(pady=50)
    
    mock_viewer.root.mainloop()

if __name__ == "__main__":
    test_fixed_annotation_manager()
