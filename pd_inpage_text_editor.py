"""
PDF Viewer - Sayfa İçi Metin Düzenleme Kontrolcüsü (InPageTextEditor)
Canvas fare/klavye olayları, doğrudan sürükle-bırak (drag-drop), yön tuşlarıyla hassas taşıma (nudge),
seçim çerçevesi yönetimi ve düzenleme iletişim kutusu (dialog) entegrasyonunu yönetir.
Arka uç PDF işlemleri pd_inpage_engine.InPageTextEngine üzerinden yürütülür.
"""

import fitz  # PyMuPDF
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Dict, Any, List

from pd_inpage_edit_dialog import InPageEditDialog
from pd_inpage_engine import InPageTextEngine


class InPageTextEditor:
    """PDF ana ekranında metin seçme ve etkileşimli düzenleme kontrolcüsü"""

    def __init__(self, pdf_viewer):
        self.pdf_viewer = pdf_viewer
        self.is_active = False
        self.start_pos = None
        self.current_sel_rect = None
        self._selection_handles = []
        self._active_dialog: Optional[InPageEditDialog] = None
        self.is_eyedropper_active = False
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._is_dragging_box = False
        self._drag_start_canvas = None

        # Arka uç PDF motoru
        self.engine = InPageTextEngine(self.pdf_viewer, on_clear_visuals=self._clear_selection_visuals)

    @property
    def _undo_stack(self) -> List[bytes]:
        """Geri alma yığınına erişim (arka uç motoru ile uyumlu)"""
        return self.engine._undo_stack

    def toggle(self):
        """Metin düzenleme aracını aç/kapa"""
        self.deactivate() if self.is_active else self.activate()

    def activate(self):
        """Metin düzenleme aracını aktif hale getirir"""
        if not self.pdf_viewer.pdf_document:
            messagebox.showwarning("Uyarı", "Lütfen önce bir PDF dosyası açın.")
            return

        # Vurgulama aracı aktifse kapat
        if hasattr(self.pdf_viewer, 'highlight_tool') and getattr(self.pdf_viewer.highlight_tool, 'is_active', False):
            self.pdf_viewer.highlight_tool.deactivate()

        self.is_active = True
        self._bind_canvas_events()
        self.pdf_viewer.canvas.configure(cursor="crosshair")

        # Toolbar buton durumunu güncelle
        if hasattr(self.pdf_viewer, 'inpage_text_edit_btn'):
            self.pdf_viewer.inpage_text_edit_btn.configure(fg_color="#1F6AA5")

        if hasattr(self.pdf_viewer, 'status_label'):
            self.pdf_viewer.status_label.configure(
                text="✏️ Metin Düzenleme Modu: Düzenlemek istediğiniz metni fareyle çerçeve içine alın."
            )

    def deactivate(self):
        """Metin düzenleme aracını kapatır ve varsayılan canvas kontrollerini geri yükler"""
        self.is_active = False
        self.start_pos = None
        self._clear_selection_visuals()

        # Canvas varsayılan dinleyicilerini geri yükle
        if hasattr(self.pdf_viewer, 'on_canvas_click'):
            self.pdf_viewer.canvas.bind("<Button-1>", self.pdf_viewer.on_canvas_click)
        if hasattr(self.pdf_viewer, 'on_canvas_drag'):
            self.pdf_viewer.canvas.bind("<B1-Motion>", self.pdf_viewer.on_canvas_drag)
        if hasattr(self.pdf_viewer, 'on_canvas_release'):
            self.pdf_viewer.canvas.bind("<ButtonRelease-1>", self.pdf_viewer.on_canvas_release)

        for key in ("<Up>", "<Down>", "<Left>", "<Right>", "<Shift-Up>", "<Shift-Down>", "<Shift-Left>", "<Shift-Right>", "<Return>"):
            self.pdf_viewer.canvas.unbind(key)

        self.pdf_viewer.canvas.configure(cursor="")

        # Toolbar buton rengini sıfırla
        if hasattr(self.pdf_viewer, 'inpage_text_edit_btn'):
            self.pdf_viewer.inpage_text_edit_btn.configure(fg_color=["#3a7ebf", "#1f538d"])

        if hasattr(self.pdf_viewer, 'status_label'):
            self.pdf_viewer.status_label.configure(text="Hazır")

    def _bind_canvas_events(self):
        """Canvas fare ve klavye olaylarını metin düzenleyiciye bağlar"""
        self.pdf_viewer.canvas.bind("<Button-1>", self._on_mouse_down)
        self.pdf_viewer.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.pdf_viewer.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        # Klavye yön tuşları ile taşıma (Nudge)
        nudge_map = {
            "<Up>": (0, -1), "<Down>": (0, 1), "<Left>": (-1, 0), "<Right>": (1, 0),
            "<Shift-Up>": (0, -5), "<Shift-Down>": (0, 5), "<Shift-Left>": (-5, 0), "<Shift-Right>": (5, 0)
        }
        for k, (dx, dy) in nudge_map.items():
            self.pdf_viewer.canvas.bind(k, lambda e, x=dx, y=dy: self.nudge(x, y))
        self.pdf_viewer.canvas.bind("<Return>", lambda e: self._on_enter_key())

    def _on_mouse_down(self, event):
        """Fare tıklama olayı"""
        if self.is_eyedropper_active:
            self._handle_eyedropper_click(event)
            return

        if not self.is_active:
            return

        cx = self.pdf_viewer.canvas.canvasx(event.x)
        cy = self.pdf_viewer.canvas.canvasy(event.y)

        # Tıklanan yer mevcut seçim kutusu veya tutamacı mı?
        current_items = self.pdf_viewer.canvas.find_withtag("current")
        for item in current_items:
            tags = self.pdf_viewer.canvas.gettags(item)
            if "inpage_active_box" in tags or "inpage_handle" in tags:
                self._is_dragging_box = True
                self._drag_start_canvas = (event.x, event.y)
                self.pdf_viewer.canvas.focus_set()
                return

        # Dışarıya tıklandıysa ve açık bir dialog varsa kapat
        if self._active_dialog:
            try:
                self._active_dialog.destroy()
            except Exception:
                pass
            self._active_dialog = None

        self._clear_selection_visuals()
        self.start_pos = (cx, cy)

    def _on_mouse_drag(self, event):
        """Fare sürükleme olayı (seçim kutusunu çizer veya mevcut kutuyu taşır)"""
        if self.is_eyedropper_active or not self.is_active:
            return

        if getattr(self, "_is_dragging_box", False) and self._drag_start_canvas:
            cdx = event.x - self._drag_start_canvas[0]
            cdy = event.y - self._drag_start_canvas[1]
            self._drag_start_canvas = (event.x, event.y)

            self.pdf_viewer.canvas.move("inpage_active_box", cdx, cdy)
            self.pdf_viewer.canvas.move("inpage_handle", cdx, cdy)

            zoom = getattr(self.pdf_viewer, 'zoom_level', 1.0)
            rotation = getattr(self.pdf_viewer, 'rotation', 0)
            mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
            inv_mat = ~mat
            p_delta = fitz.Point(cdx, cdy) * inv_mat - fitz.Point(0, 0) * inv_mat

            self.offset_x += p_delta.x
            self.offset_y += p_delta.y

            if self._active_dialog and hasattr(self._active_dialog, "update_offset_display"):
                self._active_dialog.update_offset_display(self.offset_x, self.offset_y)
            return

        if not self.start_pos:
            return

        cx = self.pdf_viewer.canvas.canvasx(event.x)
        cy = self.pdf_viewer.canvas.canvasy(event.y)

        # Mevcut geçici kutuyu sil
        if self.current_sel_rect:
            self.pdf_viewer.canvas.delete(self.current_sel_rect)

        # Yeni seçim kutusunu çiz (mavi kesikli çizgi)
        self.current_sel_rect = self.pdf_viewer.canvas.create_rectangle(
            self.start_pos[0], self.start_pos[1], cx, cy,
            outline="#0099ff", width=2, dash=(4, 2), tags="inpage_sel_box"
        )

    def _on_mouse_up(self, event):
        """Fare bırakma olayı"""
        if self.is_eyedropper_active or not self.is_active:
            return

        if getattr(self, "_is_dragging_box", False):
            self._is_dragging_box = False
            # Taşıma bittiğinde metni hemen yeni yerine konumlandır
            if abs(self.offset_x) > 0.5 or abs(self.offset_y) > 0.5:
                self._apply_direct_move()
            return

        if not self.start_pos:
            return

        end_x = self.pdf_viewer.canvas.canvasx(event.x)
        end_y = self.pdf_viewer.canvas.canvasy(event.y)
        start_x, start_y = self.start_pos
        self.start_pos = None

        x1, x2 = min(start_x, end_x), max(start_x, end_x)
        y1, y2 = min(start_y, end_y), max(start_y, end_y)

        # Tek tık yapıldıysa kelime/satır bul
        if (x2 - x1) < 6 and (y2 - y1) < 6:
            expanded = self._find_word_at_click(x1, y1)
            if expanded:
                x1, y1, x2, y2 = expanded
            else:
                self._clear_selection_visuals()
                return

        pdf_rect = self._canvas_to_pdf_rect(x1, y1, x2, y2)
        if not pdf_rect or pdf_rect.is_empty:
            self._clear_selection_visuals()
            return

        extracted_info = self._extract_text_and_styles(pdf_rect)
        if not extracted_info.get("text"):
            if hasattr(self.pdf_viewer, 'status_label'):
                self.pdf_viewer.status_label.configure(
                    text="ℹ️ Seçilen alanda metin bulunamadı. Lütfen metin içeren bir alanı seçin."
                )
            self._clear_selection_visuals()
            return

        exact_bbox = extracted_info.get("exact_bbox", pdf_rect)
        self.current_exact_bbox = exact_bbox
        self.current_extracted_info = extracted_info
        self.offset_x = 0.0
        self.offset_y = 0.0

        snap = self._pdf_to_canvas_rect(exact_bbox)
        self._draw_selection_box_with_handles(*snap)

        if hasattr(self.pdf_viewer, 'status_label'):
            self.pdf_viewer.status_label.configure(
                text="✨ Metin seçildi. Sürükleyip bırakarak taşıyabilirsiniz. Düzenlemek için kutuya çift tıklayın."
            )

    def _canvas_to_pdf_rect(self, cx1: float, cy1: float, cx2: float, cy2: float) -> fitz.Rect:
        """Canvas koordinatlarını mevcut Zoom ve Rotation matrisine göre PDF Rect'ine çevirir"""
        return self.engine.canvas_to_pdf_rect(cx1, cy1, cx2, cy2)

    def _pdf_to_canvas_rect(self, pdf_rect: fitz.Rect) -> tuple:
        """PDF Rect koordinatlarını Canvas koordinatlarına çevirir"""
        return self.engine.pdf_to_canvas_rect(pdf_rect)

    def _find_word_at_click(self, cx: float, cy: float) -> Optional[tuple]:
        """Kullanıcı sadece tek tık yaptıysa, tıklanan noktadaki satır veya kelimenin koordinatlarını döndürür"""
        return self.engine.find_word_at_click(cx, cy)

    def _extract_text_and_styles(self, pdf_rect: fitz.Rect) -> Dict[str, Any]:
        """Seçilen PDF dikdörtgenindeki metni, fontunu, boyutunu ve rengini ayıklar"""
        return self.engine.extract_text_and_styles(pdf_rect)

    def _draw_selection_box_with_handles(self, x1: float, y1: float, x2: float, y2: float):
        """Canvas üzerinde seçilen metin kutusunu ve köşe tutamaçlarını çizer"""
        self._clear_selection_visuals()

        # Saydam mavi dolgulu ve belirgin kenarlı kutu
        box = self.pdf_viewer.canvas.create_rectangle(
            x1, y1, x2, y2, outline="#0099ff", width=2, fill="#0099ff",
            stipple="gray25", tags="inpage_active_box"
        )
        self._selection_handles.append(box)

        # 4 köşeye tutamaç ekle
        handle_size = 4
        for hx, hy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            h = self.pdf_viewer.canvas.create_rectangle(
                hx - handle_size, hy - handle_size, hx + handle_size, hy + handle_size,
                fill="#ffffff", outline="#0099ff", width=1, tags="inpage_handle"
            )
            self._selection_handles.append(h)

        # Taşıma imleci ve çift tıklama ile düzenleme penceresini açma
        for tag in ("inpage_active_box", "inpage_handle"):
            self.pdf_viewer.canvas.tag_bind(tag, "<Enter>", lambda e: self.pdf_viewer.canvas.configure(cursor="fleur"))
            self.pdf_viewer.canvas.tag_bind(tag, "<Leave>", lambda e: self.pdf_viewer.canvas.configure(cursor="crosshair"))
            self.pdf_viewer.canvas.tag_bind(tag, "<Double-Button-1>", self._on_box_double_click)

    def _on_box_double_click(self, event):
        """Kutuya çift tıklandığında metin düzenleme penceresini açar"""
        if hasattr(self, "current_exact_bbox") and hasattr(self, "current_extracted_info"):
            self._open_edit_dialog(self.current_exact_bbox, self.current_extracted_info)

    def _on_enter_key(self):
        """Enter tuşuna basıldığında yön tuşlarıyla yapılan taşımayı kaydeder"""
        if abs(self.offset_x) > 0.1 or abs(self.offset_y) > 0.1:
            self._apply_direct_move()

    def _apply_direct_move(self):
        """Kutunun yeni yerine bırakılmasıyla metni hemen PDF'e taşır"""
        if not hasattr(self, "current_exact_bbox") or not hasattr(self, "current_extracted_info"):
            return

        info, exact_rect = self.current_extracted_info, self.current_exact_bbox
        bg_col = info.get("bg_color")
        payload = {
            "text": info.get("text", ""),
            "fontfile": info.get("fontfile"),
            "fontbuffer": info.get("fontbuffer"),
            "fontname": info.get("resolved_font_name") or info.get("font", "Arial"),
            "fontsize": info.get("size", 11.0),
            "is_bold": info.get("is_bold", False),
            "is_italic": info.get("is_italic", False),
            "color": info.get("color", "#000000"),
            "bg_color": bg_col,
            "align": 0,
            "auto_fit": False,
            "lines_info": info.get("lines_info", []),
            "origin": info.get("origin"),
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }
        ox, oy = self.offset_x, self.offset_y
        new_bbox = fitz.Rect(exact_rect.x0 + ox, exact_rect.y0 + oy, exact_rect.x1 + ox, exact_rect.y1 + oy)
        updated_lines = []
        for li in info.get("lines_info", []):
            b, orig = fitz.Rect(li["bbox"]), li.get("origin")
            new_b = fitz.Rect(b.x0 + ox, b.y0 + oy, b.x1 + ox, b.y1 + oy)
            new_orig = (orig[0] + ox, orig[1] + oy) if orig else None
            updated_lines.append({"text": li["text"], "bbox": new_b, "origin": new_orig, "y0": new_b.y0, "x0": new_b.x0})

        new_origin = (info["origin"][0] + ox, info["origin"][1] + oy) if info.get("origin") else None
        self.apply_text_edit([exact_rect.x0, exact_rect.y0, exact_rect.x1, exact_rect.y1], payload)

        self.current_exact_bbox = new_bbox
        self.current_extracted_info = {
            **info,
            "exact_bbox": new_bbox,
            "origin": new_origin,
            "lines_info": updated_lines,
            "bg_color": bg_col
        }
        self.offset_x = 0.0
        self.offset_y = 0.0
        snap = self._pdf_to_canvas_rect(new_bbox)
        self._draw_selection_box_with_handles(*snap)
        if hasattr(self.pdf_viewer, 'status_label'):
            self.pdf_viewer.status_label.configure(
                text="✓ Metin yeni konumuna taşındı. (Tekrar sürükleyebilir veya düzenlemek için çift tıklayabilirsiniz)"
            )

    def _clear_selection_visuals(self):
        """Canvas üzerindeki geçici seçim çizgilerini ve tutamaçları temizler"""
        self.pdf_viewer.canvas.delete("inpage_sel_box")
        self.pdf_viewer.canvas.delete("inpage_active_box")
        self.pdf_viewer.canvas.delete("inpage_handle")
        self.current_sel_rect = None
        self._selection_handles.clear()
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._is_dragging_box = False
        self._drag_start_canvas = None

    def nudge(self, dx_pt: float, dy_pt: float):
        """Klavye yön tuşları veya dialog butonları ile seçili metin kutusunu PDF puanı kadar kaydırır"""
        if not self._selection_handles:
            return

        zoom = getattr(self.pdf_viewer, 'zoom_level', 1.0)
        rotation = getattr(self.pdf_viewer, 'rotation', 0)
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        p_delta = fitz.Point(dx_pt, dy_pt) * mat - fitz.Point(0, 0) * mat

        self.pdf_viewer.canvas.move("inpage_active_box", p_delta.x, p_delta.y)
        self.pdf_viewer.canvas.move("inpage_handle", p_delta.x, p_delta.y)

        self.offset_x += dx_pt
        self.offset_y += dy_pt

        if self._active_dialog and hasattr(self._active_dialog, "update_offset_display"):
            self._active_dialog.update_offset_display(self.offset_x, self.offset_y)

    def reset_offset(self):
        """Ofseti sıfırlayıp kutuyu orijinal yerine geri döndürür"""
        if self.offset_x == 0.0 and self.offset_y == 0.0:
            return
        self.nudge(-self.offset_x, -self.offset_y)
        self.offset_x = 0.0
        self.offset_y = 0.0

    def _open_edit_dialog(self, pdf_rect: fitz.Rect, extracted_info: Dict[str, Any]):
        """Düzenleme dialogunu açar"""
        coords = [pdf_rect.x0, pdf_rect.y0, pdf_rect.x1, pdf_rect.y1]
        def _on_apply(rects, payload):
            if hasattr(self, "current_extracted_info") and self.current_extracted_info:
                self.current_extracted_info["bg_color"] = payload.get("bg_color")
                self.current_extracted_info["text"] = payload.get("text", "")
                self.current_extracted_info["color"] = payload.get("color", "#000000")
                self.current_extracted_info["fontfile"] = payload.get("fontfile")
                self.current_extracted_info["fontbuffer"] = payload.get("fontbuffer")
                self.current_extracted_info["resolved_font_name"] = payload.get("fontname")
            self.apply_text_edit(rects, payload)

        self._active_dialog = InPageEditDialog(
            parent=self.pdf_viewer,
            page_num=self.pdf_viewer.current_page,
            rect_coords=coords,
            initial_text=extracted_info["text"],
            style_info=extracted_info,
            on_apply=_on_apply,
            on_pick_color_request=self.start_eyedropper
        )

    def start_eyedropper(self, dialog: InPageEditDialog):
        """Canvas üzerinden renk seçme (Damlalık) modunu başlatır"""
        self.is_eyedropper_active = True
        self._active_dialog = dialog
        self.pdf_viewer.canvas.configure(cursor="tcross")
        if hasattr(self.pdf_viewer, 'status_label'):
            self.pdf_viewer.status_label.configure(
                text="🖌 Damlalık Modu: Arka plan rengini almak istediğiniz yere canvas üzerinde tıklayın."
            )

    def _handle_eyedropper_click(self, event):
        """Damlalık ile canvas'a tıklandığında altındaki pikselin rengini alır"""
        cx = int(self.pdf_viewer.canvas.canvasx(event.x))
        cy = int(self.pdf_viewer.canvas.canvasy(event.y))
        hex_color = self.engine.sample_pixel_color(cx, cy)
        self.is_eyedropper_active = False
        self.pdf_viewer.canvas.configure(cursor="crosshair")
        if self._active_dialog:
            self._active_dialog.set_sampled_bg_color(hex_color)

    def apply_text_edit(self, rect_coords: list, payload: Dict[str, Any]):
        """PyMuPDF Redaction ve Metin Yazma motorunu çalıştırır"""
        return self.engine.apply_text_edit(rect_coords, payload)

    def undo(self):
        """Son yapılan metin düzenlemesini geri alır"""
        return self.engine.undo()
