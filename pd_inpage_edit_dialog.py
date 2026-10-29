"""
PDF Viewer - Sayfa İçi Metin Düzenleme Dialogu
Font ailesi, stil, boyut, renk, damlalık ve hizalama kontrollerini içeren modal pencere.
"""

import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any


class InPageEditDialog(ctk.CTkToplevel):
    """PDF üzerindeki seçili metni düzenlemek için gelişmiş modal pencere"""

    # Windows standart sistem fontları haritası (normal, bold, italic, bold_italic)
    SYSTEM_FONTS = {
        "Arial": {
            "regular": "arial.ttf", "bold": "arialbd.ttf",
            "italic": "ariali.ttf", "bold_italic": "arialbi.ttf"
        },
        "Calibri": {
            "regular": "calibri.ttf", "bold": "calibrib.ttf",
            "italic": "calibrii.ttf", "bold_italic": "calibriz.ttf"
        },
        "Times New Roman": {
            "regular": "times.ttf", "bold": "timesbd.ttf",
            "italic": "timesi.ttf", "bold_italic": "timesbi.ttf"
        },
        "Segoe UI": {
            "regular": "segoeui.ttf", "bold": "segoeuib.ttf",
            "italic": "segoeuii.ttf", "bold_italic": "segoeuiz.ttf"
        },
        "Tahoma": {
            "regular": "tahoma.ttf", "bold": "tahomabd.ttf",
            "italic": "tahoma.ttf", "bold_italic": "tahomabd.ttf"
        },
        "Verdana": {
            "regular": "verdana.ttf", "bold": "verdanab.ttf",
            "italic": "verdanai.ttf", "bold_italic": "verdanaz.ttf"
        },
        "Georgia": {
            "regular": "georgia.ttf", "bold": "georgiab.ttf",
            "italic": "georgiai.ttf", "bold_italic": "georgiaz.ttf"
        },
        "Consolas": {
            "regular": "consola.ttf", "bold": "consolab.ttf",
            "italic": "consolai.ttf", "bold_italic": "consolaz.ttf"
        },
    }

    def __init__(self, parent, page_num: int, rect_coords: list,
                 initial_text: str, style_info: Dict[str, Any],
                 on_apply: Callable, on_pick_color_request: Optional[Callable] = None):
        super().__init__(parent.root if hasattr(parent, 'root') else parent)
        
        self.editor_manager = parent
        self.page_num = page_num
        self.rect_coords = rect_coords
        self.initial_text = initial_text
        self.style_info = style_info or {}
        self.on_apply = on_apply
        self.on_pick_color_request = on_pick_color_request
        
        # State variables
        self.text_color = self.style_info.get("color", "#000000")
        has_bg = bool(self.style_info.get("bg_color"))
        self.bg_color = self.style_info.get("bg_color") or "#FFFFFF"
        self.is_transparent_bg = tk.BooleanVar(value=not has_bg)
        self.auto_fit_var = tk.BooleanVar(value=True)
        self.is_bold_var = tk.BooleanVar(value=self.style_info.get("is_bold", False))
        self.is_italic_var = tk.BooleanVar(value=self.style_info.get("is_italic", False))
        self.alignment_var = tk.StringVar(value="left")
        self.custom_font_path = None
        self.preview_override_bg = None
        self._preview_click_timer = None
        
        # Windows Fonts directory
        windir = os.environ.get("WINDIR", r"C:\Windows")
        self.fonts_dir = os.path.join(windir, "Fonts")

        self._setup_window()
        self._build_ui()
        self._update_preview()

    def _setup_window(self):
        """Pencere genel ayarları"""
        self.title(f"✏️ Metin Düzenleyici — Sayfa {self.page_num + 1}")
        self.geometry("640x780")
        self.minsize(580, 700)
        self.transient(self.master)

        # Ekranın ortasına konumlandır
        try:
            from pdf_view_utils import center_window
            center_window(self, 640, 780)
        except Exception:
            pass

    def _build_ui(self):
        """Tüm arayüz bileşenlerini oluşturur"""
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # 1. Orijinal Metin Bilgisi (Referans)
        orig_card = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"), corner_radius=8)
        orig_card.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(orig_card, text="Orijinal Metin (Referans):",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
        
        orig_display = self.initial_text if self.initial_text.strip() else "(Seçilen alanda tespit edilen metin boş)"
        ctk.CTkLabel(orig_card, text=orig_display,
                      text_color=("gray40", "gray65"),
                      wraplength=580, justify="left", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(0, 8))

        # 2. Yeni Metin Giriş Alanı
        ctk.CTkLabel(main_frame, text="Yeni Metin:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=2, pady=(0, 2))
        self.text_editor = ctk.CTkTextbox(main_frame, height=90, font=ctk.CTkFont(size=13))
        self.text_editor.pack(fill="x", pady=(0, 6), padx=2)
        self.text_editor.insert("1.0", self.initial_text)
        self.text_editor.bind("<<Modified>>", lambda e: self._on_text_modified())
        self.text_editor.bind("<KeyRelease>", lambda e: self._update_preview())
        if hasattr(self.text_editor, "_textbox"):
            self.text_editor._textbox.bind("<KeyRelease>", lambda e: self._update_preview())
            self.text_editor._textbox.bind("<<Modified>>", lambda e: self._on_text_modified())

        # Hızlı Metin Dönüştürme Araçları
        tools_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        tools_row.pack(fill="x", pady=(0, 12), padx=2)
        
        ctk.CTkButton(tools_row, text="AA BÜYÜK", width=80, height=26, font=ctk.CTkFont(size=11),
                      fg_color="gray30", hover_color="gray40", command=self._case_upper).pack(side="left", padx=(0, 6))
        ctk.CTkButton(tools_row, text="aa küçük", width=80, height=26, font=ctk.CTkFont(size=11),
                      fg_color="gray30", hover_color="gray40", command=self._case_lower).pack(side="left", padx=6)
        ctk.CTkButton(tools_row, text="Aa Baş Harfler", width=95, height=26, font=ctk.CTkFont(size=11),
                      fg_color="gray30", hover_color="gray40", command=self._case_title).pack(side="left", padx=6)

        # 3. Tipografi & Font Seçimi Bölümü
        font_box = ctk.CTkFrame(main_frame, corner_radius=8)
        font_box.pack(fill="x", pady=(0, 12), padx=2)

        ctk.CTkLabel(font_box, text="Tipografi & Font Seçimi (PDF'e Gömülür):",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        f_row1 = ctk.CTkFrame(font_box, fg_color="transparent")
        f_row1.pack(fill="x", padx=10, pady=4)

        # Sistem ve kullanıcı fontları açılır listesi
        from pd_font_resolver import font_resolver
        all_sys = font_resolver.get_available_font_names()
        default_font = self._match_initial_font()

        priority_fonts = ["Arial", "Calibri", "Segoe UI", "Times New Roman", "Tahoma", "Verdana", "Georgia", "Consolas"]
        if default_font and default_font not in priority_fonts:
            priority_fonts.insert(0, default_font)

        other_fonts = [f for f in all_sys if f not in priority_fonts]
        self.font_names = priority_fonts + other_fonts
        self.font_var = tk.StringVar(value=default_font)

        self.font_dropdown = ctk.CTkOptionMenu(
            f_row1, values=self.font_names, variable=self.font_var,
            width=200, command=lambda v: self._on_font_changed()
        )
        self.font_dropdown.pack(side="left", padx=(0, 8))

        # Harici font seçme butonu
        ctk.CTkButton(f_row1, text="📂 Harici Font Seç (.ttf)...", width=160,
                      command=self._pick_custom_font).pack(side="left", padx=4)

        # Harici font bilgisi
        self.font_info_label = ctk.CTkLabel(
            font_box,
            text="ℹ️ Seçilen font Türkçe karakterlerle birlikte PDF dosyasına otomatik gömülecektir.",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray70")
        )
        self.font_info_label.pack(anchor="w", padx=10, pady=(2, 8))

        # 4. Boyut, Stil ve Hizalama
        f_row2 = ctk.CTkFrame(font_box, fg_color="transparent")
        f_row2.pack(fill="x", padx=10, pady=(0, 8))

        # Punto boyutu
        ctk.CTkLabel(f_row2, text="Punto:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        initial_size = str(int(round(self.style_info.get("size", 11.0))))
        self.size_var = tk.StringVar(value=initial_size if initial_size != "0" else "11")
        preset_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]
        
        self.size_menu = ctk.CTkComboBox(
            f_row2, values=preset_sizes, variable=self.size_var,
            width=70, command=lambda v: self._update_preview()
        )
        self.size_menu.pack(side="left", padx=(0, 12))

        # Stil (Bold / Italic)
        self.bold_btn = ctk.CTkCheckBox(
            f_row2, text="Kalın (B)", variable=self.is_bold_var,
            font=ctk.CTkFont(weight="bold"), command=self._update_preview
        )
        self.bold_btn.pack(side="left", padx=(0, 10))

        self.italic_btn = ctk.CTkCheckBox(
            f_row2, text="İtalik (I)", variable=self.is_italic_var,
            font=ctk.CTkFont(slant="italic"), command=self._update_preview
        )
        self.italic_btn.pack(side="left", padx=(0, 10))

        # Hizalama
        f_row3 = ctk.CTkFrame(font_box, fg_color="transparent")
        f_row3.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(f_row3, text="Hizalama:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        self.align_seg = ctk.CTkSegmentedButton(
            f_row3, values=["Sola", "Ortala", "Sağa", "İki Yana"],
            command=self._on_align_changed
        )
        self.align_seg.set("Sola")
        self.align_seg.pack(side="left", padx=(0, 15))

        # Otomatik Sığdırma Onayı
        ctk.CTkCheckBox(
            f_row3, text="Kutuya Sığdır (Auto-fit)", variable=self.auto_fit_var,
            command=self._update_preview
        ).pack(side="left")

        # 5. Renk Ayarları (Yazı ve Arka Plan)
        color_box = ctk.CTkFrame(main_frame, corner_radius=8)
        color_box.pack(fill="x", pady=(0, 12), padx=2)

        ctk.CTkLabel(color_box, text="Renk Ayarları & Damlalık:",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        c_row = ctk.CTkFrame(color_box, fg_color="transparent")
        c_row.pack(fill="x", padx=10, pady=(0, 8))

        # Yazı rengi
        ctk.CTkLabel(c_row, text="Yazı Rengi:").pack(side="left", padx=(0, 4))
        self.text_color_preview = ctk.CTkButton(
            c_row, text="", width=28, height=26, fg_color=self.text_color,
            hover_color=self.text_color, corner_radius=4, command=self._pick_text_color
        )
        self.text_color_preview.pack(side="left", padx=(0, 15))

        # Arka plan dolgusu
        ctk.CTkLabel(c_row, text="Arka Plan Dolgusu:").pack(side="left", padx=(0, 4))
        self.bg_color_preview = ctk.CTkButton(
            c_row, text="", width=28, height=26, fg_color=self.bg_color,
            hover_color=self.bg_color, corner_radius=4, command=self._pick_bg_color
        )
        self.bg_color_preview.pack(side="left", padx=(0, 8))

        # Damlalık butonu
        ctk.CTkButton(
            c_row, text="🖌 Sayfadan Renk Al", width=130, height=26,
            fg_color="#3d5a80", hover_color="#2b3e55", command=self._trigger_eyedropper
        ).pack(side="left", padx=4)

        ctk.CTkCheckBox(
            c_row, text="Saydam (Dolgu Yok)", variable=self.is_transparent_bg,
            command=self._update_preview
        ).pack(side="left", padx=(10, 0))

        # 6. Konum & İnce Ayar (Taşıma / Nudge)
        pos_box = ctk.CTkFrame(main_frame, corner_radius=8)
        pos_box.pack(fill="x", pady=(0, 12), padx=2)

        ctk.CTkLabel(pos_box, text="📍 Konum & İnce Ayar (Sayfada Sürükleyebilir veya Ok Tuşlarıyla Kaydırabilirsiniz):",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))

        pos_row = ctk.CTkFrame(pos_box, fg_color="transparent")
        pos_row.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(pos_row, text="Yatay (X):").pack(side="left", padx=(0, 4))
        ctk.CTkButton(pos_row, text="◀ -1", width=42, height=26, fg_color="gray30", hover_color="gray40",
                      command=lambda: self._nudge(-1, 0)).pack(side="left", padx=2)
        ctk.CTkButton(pos_row, text="+1 ▶", width=42, height=26, fg_color="gray30", hover_color="gray40",
                      command=lambda: self._nudge(1, 0)).pack(side="left", padx=(2, 10))

        ctk.CTkLabel(pos_row, text="Dikey (Y):").pack(side="left", padx=(0, 4))
        ctk.CTkButton(pos_row, text="▲ -1", width=42, height=26, fg_color="gray30", hover_color="gray40",
                      command=lambda: self._nudge(0, -1)).pack(side="left", padx=2)
        ctk.CTkButton(pos_row, text="+1 ▼", width=42, height=26, fg_color="gray30", hover_color="gray40",
                      command=lambda: self._nudge(0, 1)).pack(side="left", padx=(2, 12))

        self.offset_label = ctk.CTkLabel(
            pos_row, text="X: 0.0 pt  |  Y: 0.0 pt",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=("#1f538d", "#64b5f6")
        )
        self.offset_label.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            pos_row, text="↺ Sıfırla", width=65, height=26,
            fg_color="gray35", hover_color="gray45", command=self._reset_offset
        ).pack(side="right")

        # 7. Canlı Önizleme Alanı
        ctk.CTkLabel(main_frame, text="Canlı Önizleme (Tıkla: Beyaz/Siyah | Çift Tıkla: Renk Seç):",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=2, pady=(0, 2))
        self.preview_frame = ctk.CTkFrame(
            main_frame, height=65, corner_radius=6, cursor="hand2",
            border_width=1, border_color=("gray70", "gray40")
        )
        self.preview_frame.pack(fill="x", pady=(0, 15), padx=2)
        self.preview_frame.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="", cursor="hand2")
        self.preview_label.pack(fill="both", expand=True, padx=8, pady=4)

        # Hem CTkFrame/CTkLabel hem de altındaki gerçek Tkinter _canvas ve _label bileşenlerini bağla
        widgets_to_bind = [self.preview_frame, self.preview_label]
        for w in (self.preview_frame, self.preview_label):
            if hasattr(w, "_canvas") and w._canvas:
                widgets_to_bind.append(w._canvas)
                try:
                    w._canvas.configure(cursor="hand2")
                except Exception:
                    pass
            if hasattr(w, "_label") and w._label:
                widgets_to_bind.append(w._label)
                try:
                    w._label.configure(cursor="hand2")
                except Exception:
                    pass

        for widget in set(widgets_to_bind):
            widget.bind("<Button-1>", self._on_preview_click)
            widget.bind("<Double-Button-1>", self._on_preview_double_click)

        # 8. Alt Butonlar
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15), side="bottom")

        ctk.CTkButton(
            btn_row, text="İptal", width=110, fg_color="gray40",
            hover_color="gray30", command=self._cancel
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row, text="✔ Değişikliği Uygula", width=160,
            fg_color="#2a9d8f", hover_color="#21867a", font=ctk.CTkFont(weight="bold"),
            command=self._apply
        ).pack(side="right")

    def _match_initial_font(self) -> str:
        """PDF'den okunan orijinal font ismini mevcut sistem fontlarıyla eşleştirir"""
        if self.style_info.get("resolved_font_name"):
            return self.style_info["resolved_font_name"]
        orig_name = str(self.style_info.get("font", "")).lower()
        if "times" in orig_name:
            return "Times New Roman"
        if "calibri" in orig_name:
            return "Calibri"
        if "segoe" in orig_name:
            return "Segoe UI"
        if "tahoma" in orig_name:
            return "Tahoma"
        if "verdana" in orig_name:
            return "Verdana"
        if "georgia" in orig_name:
            return "Georgia"
        if "consolas" in orig_name or "courier" in orig_name:
            return "Consolas"
        return "Arial"

    def _on_font_changed(self):
        self.custom_font_path = None
        self.font_info_label.configure(
            text=f"ℹ️ {self.font_var.get()} sistem fontu PDF'e gömülecektir."
        )
        self._update_preview()

    def _pick_custom_font(self):
        """Harici bir .ttf / .otf dosyası seçtirir"""
        path = filedialog.askopenfilename(
            parent=self, title="Özel Font Dosyası Seç",
            filetypes=[("Font Dosyaları", "*.ttf;*.otf"), ("TrueType", "*.ttf"), ("OpenType", "*.otf")]
        )
        if path:
            self.custom_font_path = path
            fname = os.path.basename(path)
            self.font_var.set(f"Özel: {fname}")
            self.font_info_label.configure(
                text=f"✓ Seçilen font ({fname}) PDF'e doğrudan gömülecektir."
            )
            self._update_preview()

    def _pick_text_color(self):
        color = colorchooser.askcolor(parent=self, title="Yazı Rengi Seç", initialcolor=self.text_color)
        if color and color[1]:
            self.text_color = color[1]
            self.text_color_preview.configure(fg_color=self.text_color, hover_color=self.text_color)
            self._update_preview()

    def _pick_bg_color(self):
        color = colorchooser.askcolor(parent=self, title="Arka Plan Dolgu Rengi Seç", initialcolor=self.bg_color)
        if color and color[1]:
            self.bg_color = color[1]
            self.is_transparent_bg.set(False)
            self.bg_color_preview.configure(fg_color=self.bg_color, hover_color=self.bg_color)
            self._update_preview()

    def set_sampled_bg_color(self, hex_color: str):
        """Damlalık tarafından örneklenen rengi uygular"""
        self.bg_color = hex_color
        self.is_transparent_bg.set(False)
        self.bg_color_preview.configure(fg_color=self.bg_color, hover_color=self.bg_color)
        self._update_preview()
        self.deiconify()
        self.lift()

    def _trigger_eyedropper(self):
        """Kullanıcının canvas üzerinden renk seçmesi için damlalık modunu başlatır"""
        if self.on_pick_color_request:
            self.withdraw()  # Kullanıcı sayfayı rahat görsün diye pencereyi gizle
            self.on_pick_color_request(self)

    def _on_align_changed(self, value):
        self.alignment_var.set(value)
        self._update_preview()

    def _on_text_modified(self):
        self.text_editor.edit_modified(False)
        self._update_preview()

    def _on_preview_click(self, event=None):
        """Önizleme kutusuna tek tıklandığında (250ms gecikmeyle) beyaz/siyah geçişi yapar"""
        if self._preview_click_timer:
            self.after_cancel(self._preview_click_timer)
            self._preview_click_timer = None
        self._preview_click_timer = self.after(250, self._toggle_preview_bg)
        return "break"

    def _toggle_preview_bg(self):
        """Önizleme kutusu arka planını beyaz ve siyah arasında değiştirir"""
        self._preview_click_timer = None
        if self.preview_override_bg and str(self.preview_override_bg).upper() == "#FFFFFF":
            self.preview_override_bg = "#000000"
        else:
            self.preview_override_bg = "#FFFFFF"
        self._update_preview()

    def _on_preview_double_click(self, event=None):
        """Önizleme kutusuna çift tıklandığında özel renk seçme penceresini açar"""
        if self._preview_click_timer:
            self.after_cancel(self._preview_click_timer)
            self._preview_click_timer = None

        current = self.preview_override_bg or "#FFFFFF"
        color = colorchooser.askcolor(parent=self, title="Önizleme Arka Plan Rengi Seç", initialcolor=current)
        if color and color[1]:
            self.preview_override_bg = color[1]
            self._update_preview()
        return "break"

    def _case_upper(self):
        text = self.text_editor.get("1.0", "end-1c")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text.upper())
        self._update_preview()

    def _case_lower(self):
        text = self.text_editor.get("1.0", "end-1c")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text.lower())
        self._update_preview()

    def _case_title(self):
        text = self.text_editor.get("1.0", "end-1c")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", text.title())
        self._update_preview()

    def _resolve_font_file(self) -> Optional[str]:
        """Kullanılan fontun fiziksel disk yolunu döndürür"""
        if self.custom_font_path and os.path.isfile(self.custom_font_path):
            return self.custom_font_path

        from pd_font_resolver import font_resolver
        font_name = self.font_var.get()
        is_bold = self.is_bold_var.get()
        is_italic = self.is_italic_var.get()

        orig_bold = self.style_info.get("is_bold", False)
        orig_italic = self.style_info.get("is_italic", False)

        # Eğer font ve stil (bold/italic) orijinaliyle tamamen aynıysa ve fontfile varsa onu kullan
        if (font_name == self.style_info.get("resolved_font_name") and
            is_bold == orig_bold and is_italic == orig_italic and
            self.style_info.get("fontfile")):
            if os.path.isfile(self.style_info["fontfile"]):
                return self.style_info["fontfile"]

        resolved = font_resolver.resolve_file_for_family(font_name, is_bold=is_bold, is_italic=is_italic)
        if resolved and os.path.isfile(resolved):
            return resolved

        # Standart Windows Arial fallback
        windir = os.environ.get("WINDIR", r"C:\Windows")
        arial_path = os.path.join(windir, "Fonts", "arial.ttf")
        return arial_path if os.path.isfile(arial_path) else None

    def _update_preview(self):
        """Dialog içindeki canlı önizleme alanını günceller"""
        try:
            new_text = self.text_editor.get("1.0", "end-1c").strip()
            display_text = new_text if new_text else "(Metin boş)"

            try:
                size_pt = int(float(self.size_var.get()))
                preview_size = max(10, min(size_pt, 22))  # dialog içine sığacak ölçek
            except (ValueError, TypeError):
                preview_size = 12

            weight = "bold" if self.is_bold_var.get() else "normal"
            slant = "italic" if self.is_italic_var.get() else "roman"

            # Arka plan rengi (Kullanıcının tek/çift tıkla seçtiği önizleme rengi önceliklidir)
            if self.preview_override_bg:
                bg_col = self.preview_override_bg
            else:
                bg_col = "transparent" if self.is_transparent_bg.get() else self.bg_color

            self.preview_frame.configure(fg_color=bg_col if bg_col != "transparent" else ("gray85", "gray25"))

            # Hizalama
            align_map = {"Sola": "left", "Ortala": "center", "Sağa": "right", "İki Yana": "left"}
            justify = align_map.get(self.alignment_var.get(), "left")

            font_family = self.font_var.get()
            if font_family.startswith("Özel:"):
                font_family = "Arial"

            try:
                preview_font = ctk.CTkFont(family=font_family, size=preview_size, weight=weight, slant=slant)
            except Exception:
                preview_font = ctk.CTkFont(family="Arial", size=preview_size, weight=weight, slant=slant)

            self.preview_label.configure(
                text=display_text,
                text_color=self.text_color,
                justify=justify,
                font=preview_font,
                wraplength=520
            )
        except Exception as e:
            print(f"Canlı önizleme hatası: {e}")

    def _apply(self):
        """Kullanıcının girdiği değişiklikleri doğrular ve onaylar"""
        new_text = self.text_editor.get("1.0", "end-1c")
        if not new_text.strip():
            if not messagebox.askyesno("Metin Boş", "Yeni metin boş bırakıldı. Seçilen metin tamamen silinsin mi?", parent=self):
                return

        try:
            fontsize = float(self.size_var.get())
        except ValueError:
            fontsize = 11.0

        align_code_map = {"Sola": 0, "Ortala": 1, "Sağa": 2, "İki Yana": 3}
        align_code = align_code_map.get(self.alignment_var.get(), 0)

        offset_x = 0.0
        offset_y = 0.0
        if hasattr(self.editor_manager, "inpage_text_editor"):
            offset_x = getattr(self.editor_manager.inpage_text_editor, "offset_x", 0.0)
            offset_y = getattr(self.editor_manager.inpage_text_editor, "offset_y", 0.0)

        orig_bold = self.style_info.get("is_bold", False)
        orig_italic = self.style_info.get("is_italic", False)
        style_changed = (self.is_bold_var.get() != orig_bold or self.is_italic_var.get() != orig_italic)

        fontbuffer = None
        if not style_changed and self.font_var.get() == self.style_info.get("resolved_font_name"):
            fontbuffer = self.style_info.get("fontbuffer")

        result_payload = {
            "text": new_text,
            "fontfile": self._resolve_font_file(),
            "fontbuffer": fontbuffer,
            "fontname": self.font_var.get(),
            "fontsize": fontsize,
            "color": self.text_color,
            "bg_color": None if self.is_transparent_bg.get() else self.bg_color,
            "old_bg_color": self.style_info.get("bg_color"),
            "align": align_code,
            "auto_fit": self.auto_fit_var.get(),
            "is_bold": self.is_bold_var.get(),
            "is_italic": self.is_italic_var.get(),
            "lines_info": self.style_info.get("lines_info", []),
            "origin": self.style_info.get("origin"),
            "offset_x": offset_x,
            "offset_y": offset_y,
        }

        self.destroy()
        if self.on_apply:
            self.on_apply(self.rect_coords, result_payload)

    def _nudge(self, dx: float, dy: float):
        if hasattr(self.editor_manager, "inpage_text_editor"):
            self.editor_manager.inpage_text_editor.nudge(dx, dy)

    def _reset_offset(self):
        if hasattr(self.editor_manager, "inpage_text_editor"):
            self.editor_manager.inpage_text_editor.reset_offset()

    def update_offset_display(self, ox: float, oy: float):
        """Tuvalden veya butonlardan gelen ofset bilgisini etiketlerde günceller"""
        try:
            sign_x = "+" if ox > 0 else ""
            sign_y = "+" if oy > 0 else ""
            self.offset_label.configure(text=f"X: {sign_x}{ox:.1f} pt  |  Y: {sign_y}{oy:.1f} pt")
        except Exception:
            pass

    def _cancel(self):
        """İptal edildiğinde seçim çizgilerini temizler ve pencereyi kapatır"""
        if hasattr(self.editor_manager, "inpage_text_editor"):
            self.editor_manager.inpage_text_editor._clear_selection_visuals()
        self.destroy()

    def destroy(self):
        if hasattr(self.editor_manager, "inpage_text_editor"):
            editor = self.editor_manager.inpage_text_editor
            if getattr(editor, "_active_dialog", None) == self:
                editor._active_dialog = None
        super().destroy()
