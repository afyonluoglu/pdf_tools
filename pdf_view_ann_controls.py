"""
PDF Viewer - Annotation Kontroller ve Manuel Ekleme (Mixin)
Renk seçimi, tip kontrolleri, manuel annotation ekleme ve canvas gösterimi
"""

import customtkinter as ctk
import tkinter as tk


class AnnControlsMixin:
    """Annotation kontrolleri ve manuel ekleme metodlarını içeren mixin sınıfı"""

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
