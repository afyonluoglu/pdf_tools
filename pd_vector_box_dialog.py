"""
PDF Viewer - Vektörel Kutu Özellikleri Dialogu (pd_vector_box_dialog.py)
Kutuların dolgu, çerçeve (kenarlık), çerçeve kalınlığı ve köşe yuvarlatma (radius)
değerlerini canlı önizleme ile düzenlemeyi sağlayan modern iletişim penceresi.
"""

import tkinter as tk
from tkinter import colorchooser, messagebox
import customtkinter as ctk
import fitz


def draw_rounded_rect_on_canvas(canvas, x1, y1, x2, y2, radius=10, **kwargs):
    """Tkinter Canvas üzerinde yuvarlak veya keskin köşeli dikdörtgen çizer"""
    if radius <= 1.0:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
    
    # Radius kutunun boyutlarını aşmasın
    max_r = min((x2 - x1) / 2.0, (y2 - y1) / 2.0)
    r = min(radius, max_r)
    
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class VectorBoxPropertiesDialog(ctk.CTkToplevel):
    """Vektörel kutu ve annotation özelliklerini tek pencereden düzenleme dialogu"""

    def __init__(self, viewer, target, idx=None, page=None):
        super().__init__(viewer.root if hasattr(viewer, 'root') else viewer)

        self.viewer = viewer
        self.target = target  # 'ann' sözlüğü veya 'v_box' sözlüğü
        self.idx = idx
        self.page = page or (viewer.pdf_document[viewer.current_page] if viewer.pdf_document else None)
        self.is_annotation = bool(idx is not None or target.get('type') == 'highlight')

        # Başlangıç değerlerini hazırla
        self.has_fill = bool(target.get('has_fill', True) if 'has_fill' in target else bool(target.get('color')))
        self.fill_color = target.get('color') or target.get('fill_hex') or "#ACD7E6"

        self.has_stroke = bool(target.get('has_stroke', False) if 'has_stroke' in target else bool(target.get('stroke_color')))
        self.stroke_color = target.get('stroke_color') or target.get('stroke_hex') or "#0000FF"
        self.border_width = float(target.get('border_width', 1.5 if self.has_stroke else 1.0))
        if self.border_width <= 0:
            self.border_width = 1.0

        self.radius = float(target.get('radius', 5.0))
        self.has_radius = (self.radius > 0)
        self.preview_text = target.get('text', 'Örnek Metin') or 'Örnek Metin'

        # Pencere ayarları
        self.title("⚙️ Kutu Özellikleri (Renk, Çerçeve, Köşe)")
        self.geometry("460x650")
        self.resizable(False, False)
        self.grab_set()

        # Ekranı ortala
        try:
            self.update_idletasks()
            pw = self.winfo_screenwidth()
            ph = self.winfo_screenheight()
            x = (pw - 460) // 2
            y = (ph - 650) // 2
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        # 1. Canlı Önizleme Kartı
        prev_card = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=10)
        prev_card.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(prev_card, text="👁️ Canlı Önizleme", font=("Segoe UI", 12, "bold"), text_color="#A0A0A0").pack(anchor="w", padx=14, pady=(8, 2))

        self.preview_canvas = tk.Canvas(prev_card, width=410, height=80, bg="#2D2D2D", highlightthickness=1, highlightbackground="#3A3A3A")
        self.preview_canvas.pack(padx=14, pady=(2, 12))

        # 2. Ana Ayarlar Alanı
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=16, pady=4)

        # ── Dolgu Bölümü ──
        fill_card = ctk.CTkFrame(body_frame, fg_color="#232323", corner_radius=8)
        fill_card.pack(fill="x", pady=5)

        fill_header = ctk.CTkFrame(fill_card, fg_color="transparent")
        fill_header.pack(fill="x", padx=12, pady=6)

        self.fill_switch_var = ctk.BooleanVar(value=self.has_fill)
        self.fill_switch = ctk.CTkSwitch(fill_header, text="Dolgu Rengi Kullan", font=("Segoe UI", 12, "bold"),
                                         variable=self.fill_switch_var, command=self._on_fill_toggle)
        self.fill_switch.pack(side="left")

        self.fill_btn_row = ctk.CTkFrame(fill_card, fg_color="transparent")
        self.fill_btn_row.pack(fill="x", padx=12, pady=(0, 8))

        self.fill_chip = tk.Label(self.fill_btn_row, text="   ", bg=self.fill_color, relief="solid", bd=1, width=3)
        self.fill_chip.pack(side="left", padx=(0, 8))

        self.fill_label = ctk.CTkLabel(self.fill_btn_row, text=self.fill_color.upper(), font=("Consolas", 12))
        self.fill_label.pack(side="left", padx=(0, 12))

        self.fill_btn = ctk.CTkButton(self.fill_btn_row, text="🎨 Renk Seç", width=100, height=28, command=self._pick_fill_color)
        self.fill_btn.pack(side="right")

        # ── Çerçeve Bölümü ──
        stroke_card = ctk.CTkFrame(body_frame, fg_color="#232323", corner_radius=8)
        stroke_card.pack(fill="x", pady=5)

        stroke_header = ctk.CTkFrame(stroke_card, fg_color="transparent")
        stroke_header.pack(fill="x", padx=12, pady=6)

        self.stroke_switch_var = ctk.BooleanVar(value=self.has_stroke)
        self.stroke_switch = ctk.CTkSwitch(stroke_header, text="Dış Çerçeve (Kenarlık) Kullan", font=("Segoe UI", 12, "bold"),
                                           variable=self.stroke_switch_var, command=self._on_stroke_toggle)
        self.stroke_switch.pack(side="left")

        self.stroke_btn_row = ctk.CTkFrame(stroke_card, fg_color="transparent")
        self.stroke_btn_row.pack(fill="x", padx=12, pady=(0, 6))

        self.stroke_chip = tk.Label(self.stroke_btn_row, text="   ", bg=self.stroke_color, relief="solid", bd=1, width=3)
        self.stroke_chip.pack(side="left", padx=(0, 8))

        self.stroke_label = ctk.CTkLabel(self.stroke_btn_row, text=self.stroke_color.upper(), font=("Consolas", 12))
        self.stroke_label.pack(side="left", padx=(0, 12))

        self.stroke_btn = ctk.CTkButton(self.stroke_btn_row, text="🔲 Renk Seç", width=100, height=28, command=self._pick_stroke_color)
        self.stroke_btn.pack(side="right")

        # Kalınlık Slider
        self.width_slider_row = ctk.CTkFrame(stroke_card, fg_color="transparent")
        self.width_slider_row.pack(fill="x", padx=12, pady=(0, 8))

        self.width_text_lbl = ctk.CTkLabel(self.width_slider_row, text=f"Kalınlık: {self.border_width:.1f} pt", font=("Segoe UI", 11), width=95, anchor="w")
        self.width_text_lbl.pack(side="left")

        self.width_slider = ctk.CTkSlider(self.width_slider_row, from_=0.5, to=6.0, number_of_steps=11, command=self._on_width_change)
        self.width_slider.set(self.border_width)
        self.width_slider.pack(side="left", fill="x", expand=True, padx=8)

        # ── Köşe Yuvarlatma Bölümü ──
        radius_card = ctk.CTkFrame(body_frame, fg_color="#232323", corner_radius=8)
        radius_card.pack(fill="x", pady=5)

        radius_header = ctk.CTkFrame(radius_card, fg_color="transparent")
        radius_header.pack(fill="x", padx=12, pady=6)

        self.radius_switch_var = ctk.BooleanVar(value=self.has_radius)
        self.radius_switch = ctk.CTkSwitch(radius_header, text="Yuvarlak Köşeli", font=("Segoe UI", 12, "bold"),
                                           variable=self.radius_switch_var, command=self._on_radius_toggle)
        self.radius_switch.pack(side="left")

        self.radius_slider_row = ctk.CTkFrame(radius_card, fg_color="transparent")
        self.radius_slider_row.pack(fill="x", padx=12, pady=(0, 8))

        self.radius_text_lbl = ctk.CTkLabel(self.radius_slider_row, text=f"Yarıçap: {self.radius:.1f} pt", font=("Segoe UI", 11), width=95, anchor="w")
        self.radius_text_lbl.pack(side="left")

        self.radius_slider = ctk.CTkSlider(self.radius_slider_row, from_=1.0, to=20.0, number_of_steps=19, command=self._on_radius_change)
        self.radius_slider.set(self.radius if self.radius > 0 else 5.0)
        self.radius_slider.pack(side="left", fill="x", expand=True, padx=8)

        # 3. Aksiyon Butonları
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=12)

        ctk.CTkButton(
            btn_bar,
            text="📌 Uygula & Vektör Sabitle",
            font=("Segoe UI", 12, "bold"),
            fg_color="#107C41", hover_color="#0B582E",
            height=36,
            command=self._apply_and_bake
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_bar,
            text="✓ Uygula (Düzenlenebilir)",
            font=("Segoe UI", 12),
            height=36,
            command=self._apply_editable
        ).pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(
            btn_bar,
            text="İptal",
            width=70,
            height=36,
            fg_color="#444444", hover_color="#555555",
            command=self.destroy
        ).pack(side="right", padx=(4, 0))

    def _on_fill_toggle(self):
        self.has_fill = self.fill_switch_var.get()
        self._update_preview()

    def _on_stroke_toggle(self):
        self.has_stroke = self.stroke_switch_var.get()
        self._update_preview()

    def _on_radius_toggle(self):
        self.has_radius = self.radius_switch_var.get()
        self.radius = self.radius_slider.get() if self.has_radius else 0.0
        self._update_preview()

    def _on_width_change(self, val):
        self.border_width = float(val)
        self.width_text_lbl.configure(text=f"Kalınlık: {self.border_width:.1f} pt")
        self._update_preview()

    def _on_radius_change(self, val):
        self.radius = float(val)
        self.radius_text_lbl.configure(text=f"Yarıçap: {self.radius:.1f} pt")
        if not self.radius_switch_var.get():
            self.radius_switch_var.set(True)
            self.has_radius = True
        self._update_preview()

    def _pick_fill_color(self):
        color = colorchooser.askcolor(color=self.fill_color, parent=self, title="Dolgu Rengi Seç")[1]
        if color:
            self.fill_color = color
            self.fill_label.configure(text=color.upper())
            self.fill_chip.configure(bg=color)
            if not self.fill_switch_var.get():
                self.fill_switch_var.set(True)
                self.has_fill = True
            self._update_preview()

    def _pick_stroke_color(self):
        color = colorchooser.askcolor(color=self.stroke_color, parent=self, title="Çerçeve Rengi Seç")[1]
        if color:
            self.stroke_color = color
            self.stroke_label.configure(text=color.upper())
            self.stroke_chip.configure(bg=color)
            if not self.stroke_switch_var.get():
                self.stroke_switch_var.set(True)
                self.has_stroke = True
            self._update_preview()

    def _update_preview(self):
        """Canvas üzerindeki canlı kutu önizlemesini çizer"""
        c = self.preview_canvas
        c.delete("all")

        # Kutu koordinatları
        x1, y1 = 20, 15
        x2, y2 = 390, 65

        fill = self.fill_color if self.has_fill else ""
        outline = self.stroke_color if self.has_stroke else ""
        width = int(round(self.border_width)) if self.has_stroke else 0
        rad = self.radius if self.has_radius else 0.0

        draw_rounded_rect_on_canvas(c, x1, y1, x2, y2, radius=rad, fill=fill, outline=outline, width=width)

        # Önizleme metnini kutunun içine çiz
        text_fill = "#FFFFFF" if not self.has_fill else ("#000000" if self._is_light_color(self.fill_color) else "#FFFFFF")
        disp_text = (self.preview_text[:35] + "...") if len(self.preview_text) > 35 else self.preview_text
        c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=disp_text, fill=text_fill, font=("Segoe UI", 12, "bold"))

    @staticmethod
    def _is_light_color(hex_color):
        try:
            h = hex_color.lstrip('#')
            r, g, b = [int(h[i:i+2], 16) for i in (0, 2, 4)]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return lum > 140
        except Exception:
            return True

    def _apply_editable(self):
        """Ayarları interaktif kutuya uygula (düzenlenebilir bırak)"""
        try:
            self._apply_properties_to_target(bake=False)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Uygulama hatası: {e}", parent=self)

    def _apply_and_bake(self):
        """Ayarları uygula ve doğrudan PDF içerik akışına vektörel olarak mühürle"""
        try:
            self._apply_properties_to_target(bake=True)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Sabitleme hatası: {e}", parent=self)

    def _apply_properties_to_target(self, bake=False):
        from pd_vector_boxes import bake_annotation_to_vector_box, convert_vector_box_to_annotation

        ann = None
        if self.is_annotation:
            ann = self.target
        else:
            # Henüz annotation yapılmamış bir ham vektör kutusu
            ann = convert_vector_box_to_annotation(self.page, self.target, self.viewer.current_page)
            self.viewer.annotation_manager.add_annotation(ann)
            self.idx = len(self.viewer.annotation_manager.annotations) - 1

        # Özellikleri güncelle
        ann['has_fill'] = self.has_fill
        ann['color'] = self.fill_color if self.has_fill else "#FFFFFF"
        ann['has_stroke'] = self.has_stroke
        ann['stroke_color'] = self.stroke_color if self.has_stroke else ""
        ann['border_width'] = self.border_width if self.has_stroke else 0.0
        ann['radius'] = self.radius if self.has_radius else 0.0

        if bake:
            success = bake_annotation_to_vector_box(self.viewer.pdf_document, ann)
            if success:
                if self.idx is not None and 0 <= self.idx < len(self.viewer.annotation_manager.annotations):
                    del self.viewer.annotation_manager.annotations[self.idx]
                if hasattr(self.viewer, '_deselect_highlight'):
                    self.viewer._deselect_highlight()
                self.viewer.display_page()
                messagebox.showinfo("Başarılı", "Kutu güncellenen özellikleriyle arka plana sabitlendi!", parent=self.viewer.root)
        else:
            # Sadece ekranda düzenlenebilir olarak güncelle
            self.viewer.display_page()
            if self.idx is not None and hasattr(self.viewer, '_select_highlight'):
                self.viewer._select_highlight(ann, self.idx)
