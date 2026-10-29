"""
PDF Viewer - Vektörel Arka Plan Kutuları Yönetimi (pd_vector_boxes.py)
PDF içerik akışındaki (Content Stream) vektörel çizimlerin (mavi kutular,
zemin şeritleri vb.) tespiti, silinmesi (metni koruyarak) ve düzenlenebilir
annotation nesnesine dönüştürülmesi işlemlerini yönetir.
"""

from datetime import datetime
import customtkinter as ctk
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import messagebox, colorchooser
from pd_annot_sync import hex_from_color, hex_to_rgb_float


def get_page_vector_boxes(page):
    """
    Belirtilen sayfadaki dikdörtgen veya şerit şeklindeki vektörel çizimleri tespit eder.
    Metin içeren veya zemin oluşturan kutuları döndürür.
    """
    if not page:
        return []

    page_rect = page.rect
    drawings = page.get_drawings()
    annot_rects = [fitz.Rect(a.rect) for a in page.annots()]
    boxes = []

    for idx, d in enumerate(drawings):
        r = d.get('rect')
        if not r:
            continue
        rect = fitz.Rect(r)

        # Eğer bu çizim mevcut bir annotation'a aitse atla (zaten etkileşimli yönetiliyor)
        if any(abs(rect.x0 - ar.x0) < 2 and abs(rect.y0 - ar.y0) < 2 and abs(rect.x1 - ar.x1) < 2 and abs(rect.y1 - ar.y1) < 2 for ar in annot_rects):
            continue

        # Çok ince çizgileri filtrele
        if rect.width < 25 or rect.height < 8:
            continue

        # Tüm sayfayı kaplayan dış çerçeve veya sayfa zeminini filtrele
        if rect.width >= page_rect.width * 0.98 and rect.height >= page_rect.height * 0.98:
            continue

        fill = d.get('fill')
        color = d.get('color')
        d_type = d.get('type', '')

        has_fill = (fill is not None) and ('f' in d_type or d_type == 'f' or not d_type)
        has_stroke = (color is not None) and ('s' in d_type or d_type == 's')

        # Dolgu veya çizgi rengi olmayan boş nesneleri atla
        if not has_fill and not has_stroke:
            continue

        # İçerisindeki veya çakışan metni oku
        text_inside = page.get_text("text", clip=rect).strip()

        fill_hex = hex_from_color(fill) if has_fill else None
        stroke_hex = hex_from_color(color) if has_stroke else None
        border_width = float(d.get('width', 1.0) or 1.0) if has_stroke else 0.0

        curves = [it for it in d.get('items', []) if it[0] == 'c']
        if curves and len(curves) >= 4:
            radius_pt = round(min(abs(rect.x1 - curves[0][1].x), abs(rect.y1 - curves[0][1].y)), 1)
            if radius_pt <= 0.1:
                radius_pt = round(abs(rect.x1 - curves[0][1].x), 1)
        else:
            radius_pt = 0.0

        boxes.append({
            'index': idx,
            'rect': [rect.x0, rect.y0, rect.x1, rect.y1],
            'has_fill': has_fill,
            'has_stroke': has_stroke,
            'fill': fill if has_fill else None,
            'stroke': color if has_stroke else None,
            'fill_hex': fill_hex,
            'stroke_hex': stroke_hex,
            'border_width': border_width,
            'radius': radius_pt,
            'text': text_inside,
            'width': round(rect.width, 1),
            'height': round(rect.height, 1)
        })

    return boxes


def find_vector_box_at(page, pdf_x, pdf_y):
    """Verilen PDF koordinatındaki en uygun vektörel kutuyu bulur (yoksa None)"""
    boxes = get_page_vector_boxes(page)
    matched = []
    for b in boxes:
        r = b['rect']
        if r[0] - 2 <= pdf_x <= r[2] + 2 and r[1] - 2 <= pdf_y <= r[3] + 2:
            matched.append(b)

    if not matched:
        return None

    # Birden fazla çakışma varsa en küçük alanlı olanı (en spesifik kutuyu) seç
    matched.sort(key=lambda x: (x['width'] * x['height']))
    return matched[0]


def delete_vector_box(page, pdf_rect):
    """
    Vektörel kutuyu sayfadan siler.
    PyMuPDF Redaction motoru kullanarak metinlere dokunmadan sadece vektör çizimini temizler.
    """
    try:
        r = fitz.Rect(pdf_rect)
        r.x0 -= 1.0
        r.y0 -= 1.0
        r.x1 += 1.0
        r.y1 += 1.0

        page.add_redact_annot(r)
        success = page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_NONE,
            graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
            text=fitz.PDF_REDACT_TEXT_NONE
        )
        return success
    except Exception as e:
        print(f"DEBUG [pd_vector_boxes]: Vektör silme hatası: {e}")
        return False


def convert_vector_box_to_annotation(page, box_dict, page_num):
    """
    Vektörel kutuyu arka plan akışından siler ve aynı koordinat/renkte
    düzenlenebilir (taşınabilir, boyutlandırılabilir) Square annotation'a çevirir.
    """
    pdf_rect = box_dict['rect']
    has_fill = box_dict.get('has_fill', True)
    has_stroke = box_dict.get('has_stroke', False)

    fill_rgb = box_dict.get('fill') if has_fill else None
    stroke_rgb = box_dict.get('stroke') if has_stroke else None
    border_w = box_dict.get('border_width', 1.5 if has_stroke else 0.0)

    # 1. Sayfa içerik akışındaki statik vektör çizimini sil
    delete_vector_box(page, pdf_rect)

    # 2. Aynı koordinatlara interaktif bir Square annotation yerleştir
    rect = fitz.Rect(pdf_rect)
    annot = page.add_rect_annot(rect)
    annot.set_colors(fill=fill_rgb, stroke=stroke_rgb)
    annot.set_opacity(0.8)
    annot.update()

    ann_dict = {
        'page': page_num,
        'type': 'highlight',
        'annot_type': 'Square',
        'has_fill': has_fill,
        'has_stroke': has_stroke,
        'color': box_dict.get('fill_hex') or '#B0D4EC',
        'stroke_color': box_dict.get('stroke_hex') or '',
        'border_width': border_w,
        'is_vector_origin': True,
        'radius': box_dict.get('radius', 5.0),
        'pdf_rect': [rect.x0, rect.y0, rect.x1, rect.y1],
        'coordinates': {'x1': rect.x0, 'y1': rect.y0, 'x2': rect.x1, 'y2': rect.y1},
        'position': {'x': rect.x0, 'y': rect.y0},
        'xref': annot.xref,
        'is_embedded': True,
        'text': box_dict.get('text', ''),
        'timestamp': datetime.now().isoformat()
    }
    return ann_dict


def bake_annotation_to_vector_box(pdf_document, ann):
    """
    Annotation'ı siler ve yerine PDF içerik akışına (metnin arkasına)
    kalıcı, yuvarlak köşeli veya keskin, çerçeveli/çerçevesiz vektörel çizim olarak yazar.
    """
    page_num = ann.get('page', 0)
    if not pdf_document or page_num < 0 or page_num >= len(pdf_document):
        return False

    page = pdf_document[page_num]
    pdf_rect = ann.get('pdf_rect')
    if not pdf_rect:
        coords = ann.get('coordinates', {})
        pdf_rect = [coords.get('x1', 0), coords.get('y1', 0), coords.get('x2', 100), coords.get('y2', 100)]

    rect = fitz.Rect(pdf_rect)

    # 1. Renkleri ve boyutları hazırla
    has_fill = ann.get('has_fill', True)
    has_stroke = ann.get('has_stroke', bool(ann.get('stroke_color')))

    fill_hex = ann.get('color') if has_fill else None
    stroke_hex = ann.get('stroke_color') if (has_stroke and ann.get('stroke_color')) else None
    border_width = float(ann.get('border_width', 1.0)) if stroke_hex else 0.0

    fill_rgb = hex_to_rgb_float(fill_hex) if fill_hex else None
    stroke_rgb = hex_to_rgb_float(stroke_hex) if stroke_hex else None

    # 2. Varsa mevcut annotation nesnesini PDF'ten sil
    xref = ann.get('xref')
    if xref:
        try:
            for a in list(page.annots()):
                if a.xref == xref:
                    page.delete_annot(a)
                    break
        except Exception as e:
            print(f"DEBUG [bake_to_vector]: Eski annot silme hatası: {e}")

    # 3. PyMuPDF Shape nesnesi ile metnin arkasına (overlay=False) çizim ekle
    try:
        shape = page.new_shape()
        radius_pt = float(ann.get('radius', 0.0))
        min_side = min(rect.width, rect.height)
        if radius_pt > 0 and min_side > 0:
            radius_ratio = min(0.5, radius_pt / min_side)
        else:
            radius_ratio = None

        shape.draw_rect(rect, radius=radius_ratio)
        shape.finish(
            color=stroke_rgb,
            fill=fill_rgb,
            width=border_width if stroke_rgb else 0
        )
        shape.commit(overlay=False)  # Metnin arkasına yaz!
        return True
    except Exception as e:
        print(f"DEBUG [bake_to_vector]: Çizim oluşturma hatası: {e}")
        return False


def change_stroke_color_action(viewer, ann, idx):
    """Highlight / Square annotation çerçeve rengini değiştir"""
    from tkinter import colorchooser
    current_stroke = ann.get('stroke_color') or '#0000FF'
    new_color = colorchooser.askcolor(color=current_stroke, parent=viewer.root,
                                      title="Çerçeve Rengi Seç")[1]
    if new_color:
        ann['stroke_color'] = new_color
        cid = ann.get('canvas_id')
        if cid:
            try:
                viewer.canvas.itemconfig(cid, outline=new_color)
            except Exception as e:
                print(f"DEBUG: Çerçeve rengi canvas hatası: {e}")
        xref = ann.get('xref')
        if xref and viewer.pdf_document:
            try:
                page_num = ann.get('page', 0)
                if 0 <= page_num < len(viewer.pdf_document):
                    page = viewer.pdf_document[page_num]
                    for a in page.annots():
                        if a.xref == xref:
                            from pd_annot_sync import hex_to_rgb_float
                            rgb_stroke = hex_to_rgb_float(new_color)
                            rgb_fill = hex_to_rgb_float(ann.get('color', '#B0D4EC'))
                            a.set_colors(stroke=rgb_stroke, fill=rgb_fill)
                            a.update()
                            break
            except Exception as e:
                print(f"DEBUG: Annot stroke renk güncelleme hatası: {e}")


def bake_annotation_action(viewer, ann, idx):
    """Sağ tık menüsünden 'Sabitle / Vektörel Arka Plana Dönüştür' komutu"""
    if not viewer.pdf_document:
        return
    try:
        if not ann.get('pdf_rect'):
            coords = ann.get('coordinates', {})
            from pd_annot_sync import canvas_to_pdf_rect
            ann['pdf_rect'] = canvas_to_pdf_rect(
                coords.get('x1', 0), coords.get('y1', 0),
                coords.get('x2', 100), coords.get('y2', 100),
                getattr(viewer, 'zoom_level', 1.0),
                getattr(viewer, 'rotation', 0)
            )

        success = bake_annotation_to_vector_box(viewer.pdf_document, ann)
        if success:
            if 0 <= idx < len(viewer.annotation_manager.annotations):
                del viewer.annotation_manager.annotations[idx]
            if hasattr(viewer, '_deselect_highlight'):
                viewer._deselect_highlight()
            viewer.display_page()
            if hasattr(viewer, 'status_label'):
                viewer.status_label.configure(text="Kutu orijinal renk ve çerçevesiyle arka plana sabitlendi.")
            messagebox.showinfo(
                "Başarılı",
                "Kutu yeni konumu ve boyutunda, orijinal renk ve çerçevesiyle\n"
                "arka plana başarıyla sabitlendi!",
                parent=viewer.root
            )
    except Exception as e:
        messagebox.showerror("Hata", f"Sabitleme hatası: {e}", parent=viewer.root)


def _convert_vbox(viewer, v_box):
    """Vektörel kutuyu annotation'a dönüştür ve ekranda seç"""
    try:
        page = viewer.pdf_document[viewer.current_page]
        new_ann = convert_vector_box_to_annotation(page, v_box, viewer.current_page)
        viewer.annotation_manager.add_annotation(new_ann)
        viewer.display_page()
        # Yeni eklenen annotation'ı seç
        idx = len(viewer.annotation_manager.annotations) - 1
        if hasattr(viewer, '_select_highlight'):
            viewer._select_highlight(new_ann, idx)
        if hasattr(viewer, 'status_label'):
            viewer.status_label.configure(text="Vektör kutusu düzenlenebilir annotation'a dönüştürüldü.")
    except Exception as e:
        messagebox.showerror("Hata", f"Dönüştürme hatası: {e}", parent=viewer.root)


def _delete_vbox(viewer, v_box):
    """Vektörel kutuyu sil (yazıyı koru)"""
    txt = v_box.get('text', '').replace('\n', ' ')[:30]
    prompt = f"'{txt}' arkasındaki vektörel zemin kutusu silinecektir.\nİçindeki yazılar korunur. Onaylıyor musunuz?" if txt else "Bu vektörel kutu silinecektir (yazılar korunur). Onaylıyor musunuz?"
    if not messagebox.askyesno("Vektör Kutuyu Sil", prompt, parent=viewer.root):
        return
    try:
        page = viewer.pdf_document[viewer.current_page]
        delete_vector_box(page, v_box['rect'])
        viewer._selected_vector_box = None
        viewer.display_page()
        if hasattr(viewer, 'status_label'):
            viewer.status_label.configure(text="Vektör kutusu silindi (yazı korundu).")
    except Exception as e:
        messagebox.showerror("Hata", f"Silme hatası: {e}", parent=viewer.root)


def _recolor_vbox(viewer, v_box):
    """Vektörel kutunun rengini değiştirerek düzenlenebilir yap"""
    curr = v_box.get('fill_hex', '#B0D4EC')
    new_color = colorchooser.askcolor(color=curr, parent=viewer.root, title="Vektör Kutu Rengi Seç")[1]
    if not new_color:
        return
    v_box['fill_hex'] = new_color
    v_box['fill'] = hex_to_rgb_float(new_color)
    _convert_vbox(viewer, v_box)


def _open_vbox_dialog(viewer, v_box):
    """Vektörel kutu için özellikler penceresini açar"""
    from pd_vector_box_dialog import VectorBoxPropertiesDialog
    page = viewer.pdf_document[viewer.current_page] if viewer.pdf_document else None
    VectorBoxPropertiesDialog(viewer, v_box, page=page)


def show_vector_box_context_menu(viewer, event, v_box):
    """Vektörel arka plan kutusu için sağ-tık bağlam menüsü gösterir"""
    menu = tk.Menu(viewer.root, tearoff=0, background="#333333", foreground="white", activebackground="#1F6AA5")
    txt = v_box.get('text', '').replace('\n', ' ')[:30]
    header = f"🔷 Vektör Kutusu: {txt}" if txt else f"🔷 Vektör Kutusu ({v_box['width']}x{v_box['height']} pt)"
    menu.add_command(label=header, state='disabled')
    menu.add_separator()
    menu.add_command(
        label="⚙️ Kutu Özellikleri (Renk, Çerçeve, Köşe...)",
        command=lambda: _open_vbox_dialog(viewer, v_box)
    )
    menu.add_command(
        label="🔄 Düzenlenebilir Kutuya Dönüştür (Taşı / Boyutlandır)",
        command=lambda: _convert_vbox(viewer, v_box)
    )
    menu.add_command(
        label="🗑️ Bu Vektör Kutuyu Sil (Yazıyı Koru)",
        command=lambda: _delete_vbox(viewer, v_box)
    )
    menu.add_command(
        label="🎨 Rengini Değiştir",
        command=lambda: _recolor_vbox(viewer, v_box)
    )
    menu.add_separator()
    menu.add_command(
        label="📋 Tüm Vektör Kutularını Yönet...",
        command=lambda: VectorBoxManagerDialog(viewer)
    )
    menu.config(font=("Segoe UI", 12))
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


def handle_vector_box_click(viewer, cx, cy):
    """Kullanıcı canvas'ta boş yere tıkladığında vektörel kutu var mı kontrol eder ve seçer"""
    try:
        viewer.canvas.delete("sel_vector_box")
    except Exception:
        pass
    viewer._selected_vector_box = None

    if not viewer.pdf_document or not hasattr(viewer, 'current_page'):
        return

    try:
        page = viewer.pdf_document[viewer.current_page]
        mat = fitz.Matrix(viewer.zoom_level, viewer.zoom_level).prerotate(viewer.rotation)
        pdf_pt = fitz.Point(cx, cy) * ~mat
        v_box = find_vector_box_at(page, pdf_pt.x, pdf_pt.y)
        if v_box:
            viewer._selected_vector_box = v_box
            from pd_annot_sync import calculate_canvas_coords
            x1, y1, x2, y2 = calculate_canvas_coords(v_box['rect'], viewer.zoom_level, viewer.rotation)
            viewer.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='#0078D4', width=2, dash=(6, 3),
                tags=('sel_vector_box', 'sel_highlight')
            )
            txt = v_box.get('text', '').replace('\n', ' ')[:25]
            info = f"'{txt}'" if txt else f"{v_box['width']}x{v_box['height']} pt"
            if hasattr(viewer, 'status_label'):
                viewer.status_label.configure(text=f"🔷 Vektör kutusu seçildi: {info} (Sil: Delete | İşlemler: Sağ Tık)")
    except Exception as e:
        print(f"DEBUG [handle_vector_box_click]: {e}")


class VectorBoxManagerDialog(ctk.CTkToplevel):
    """Mevcut sayfadaki vektörel kutuları listeleyen ve toplu/tekil yönetim sağlayan diyalog"""

    def __init__(self, pdf_viewer):
        super().__init__(pdf_viewer.root)
        self.viewer = pdf_viewer
        self.title("🔷 Vektörel Arka Plan Kutuları Yönetimi")
        self.geometry("640x500")
        self.transient(pdf_viewer.root)
        self.grab_set()

        from pdf_view_utils import center_window
        center_window(self, 640, 500)

        self.page_num = self.viewer.current_page
        self.page = self.viewer.pdf_document[self.page_num] if self.viewer.pdf_document else None

        self._setup_ui()
        self._load_boxes()

    def _setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))

        title_lbl = ctk.CTkLabel(
            header,
            text=f"Sayfa {self.page_num + 1} Vektörel Arka Plan Kutuları",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_lbl.pack(side="left")

        desc_lbl = ctk.CTkLabel(
            self,
            text="Bu sayfadaki grafik çizimler (mavi başlık zeminleri vb.) aşağıda listelenmiştir.\n"
                 "Düzenlenebilir yaparak fareyle taşıyabilir/boyutlandırabilir veya metni koruyarak silebilirsiniz.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            justify="left"
        )
        desc_lbl.pack(fill="x", padx=16, pady=(0, 8))

        # Toplu İşlem Butonları
        batch_frame = ctk.CTkFrame(self, fg_color="transparent")
        batch_frame.pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            batch_frame,
            text="🔄 Tümünü Düzenlenebilir Yap",
            fg_color="#1F6AA5",
            hover_color="#144f7a",
            command=self._convert_all
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            batch_frame,
            text="🗑️ Tümünü Sil (Yazıları Koru)",
            fg_color="#D83B01",
            hover_color="#a82e00",
            command=self._delete_all
        ).pack(side="left", padx=8)

        # Liste Container
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=280)
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Alt Buton
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkButton(footer, text="Kapat", width=100, command=self.destroy).pack(side="right")

    def _load_boxes(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.page:
            ctk.CTkLabel(self.scroll_frame, text="Sayfa yüklenemedi.").pack(pady=20)
            return

        boxes = get_page_vector_boxes(self.page)
        if not boxes:
            ctk.CTkLabel(
                self.scroll_frame,
                text="Bu sayfada yönetilebilir vektörel kutu bulunamadı.",
                font=ctk.CTkFont(size=13),
                text_color="gray60"
            ).pack(pady=30)
            return

        for idx, b in enumerate(boxes):
            item_card = ctk.CTkFrame(self.scroll_frame, fg_color="#333333")
            item_card.pack(fill="x", padx=4, pady=4)

            # Renk kutucuğu (çerçeve ve dolgu)
            bg_col = b.get('fill_hex') or "#333333"
            bd_col = b.get('stroke_hex') or ("#0000FF" if b.get('has_stroke') else "#555555")
            swatch = tk.Canvas(item_card, width=24, height=24, bg=bg_col, highlightthickness=1, highlightbackground=bd_col)
            swatch.pack(side="left", padx=(10, 8), pady=8)

            # Bilgi etiketi
            txt = b['text'].replace('\n', ' ')[:35] if b['text'] else "(Metinsiz Kutu)"
            stroke_desc = "Çerçeveli" if b.get('has_stroke') else "Çerçevesiz"
            rad_desc = f", r={b['radius']}pt" if b.get('radius') else ""
            info_text = f"Kutu #{idx+1} — {b['width']} x {b['height']} pt ({stroke_desc}{rad_desc})\nMetin: {txt}"
            lbl = ctk.CTkLabel(item_card, text=info_text, font=ctk.CTkFont(size=12), justify="left")
            lbl.pack(side="left", padx=4, fill="x", expand=True)

            # Butonlar
            btn_box = ctk.CTkFrame(item_card, fg_color="transparent")
            btn_box.pack(side="right", padx=8)

            ctk.CTkButton(
                btn_box,
                text="⚙️ Özellikler",
                width=80,
                command=lambda box=b: self._edit_box(box)
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                btn_box,
                text="🔄 Düzenle",
                width=75,
                command=lambda box=b: self._convert_box(box)
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                btn_box,
                text="🗑️ Sil",
                width=55,
                fg_color="#D83B01",
                hover_color="#a82e00",
                command=lambda box=b: self._delete_box(box)
            ).pack(side="left", padx=3)

    def _edit_box(self, box):
        from pd_vector_box_dialog import VectorBoxPropertiesDialog
        VectorBoxPropertiesDialog(self.viewer, box, page=self.page)

    def _convert_box(self, box):
        try:
            new_ann = convert_vector_box_to_annotation(self.page, box, self.page_num)
            self.viewer.annotation_manager.add_annotation(new_ann)
            self.viewer.display_page()
            self._load_boxes()
            messagebox.showinfo("Başarılı", "Vektör kutusu düzenlenebilir annotation'a dönüştürüldü!", parent=self)
        except Exception as e:
            messagebox.showerror("Hata", f"Dönüştürme hatası: {e}", parent=self)

    def _delete_box(self, box):
        if not messagebox.askyesno(
                "Kutuyu Sil",
                "Bu vektörel arka plan kutusu silinecektir. İçindeki metinler korunacaktır.\nOnaylıyor musunuz?",
                parent=self):
            return
        try:
            delete_vector_box(self.page, box['rect'])
            self.viewer.display_page()
            self._load_boxes()
            messagebox.showinfo("Başarılı", "Vektör kutusu silindi!", parent=self)
        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatası: {e}", parent=self)

    def _convert_all(self):
        boxes = get_page_vector_boxes(self.page)
        if not boxes:
            return
        if not messagebox.askyesno(
                "Tümünü Dönüştür",
                f"Bu sayfadaki {len(boxes)} adet vektörel kutunun tümü düzenlenebilir annotation'a dönüştürülecektir.\nOnaylıyor musunuz?",
                parent=self):
            return
        count = 0
        for b in boxes:
            try:
                new_ann = convert_vector_box_to_annotation(self.page, b, self.page_num)
                self.viewer.annotation_manager.add_annotation(new_ann)
                count += 1
            except Exception as e:
                print(f"DEBUG: Toplu dönüştürme hatası: {e}")
        self.viewer.display_page()
        self._load_boxes()
        messagebox.showinfo("Başarılı", f"{count} adet vektör kutusu düzenlenebilir yapıldı!", parent=self)

    def _delete_all(self):
        boxes = get_page_vector_boxes(self.page)
        if not boxes:
            return
        if not messagebox.askyesno(
                "Tümünü Sil",
                f"Bu sayfadaki {len(boxes)} adet vektörel kutunun tümü silinecektir (yazılar korunur).\nOnaylıyor musunuz?",
                parent=self):
            return
        count = 0
        for b in boxes:
            try:
                delete_vector_box(self.page, b['rect'])
                count += 1
            except Exception as e:
                print(f"DEBUG: Toplu silme hatası: {e}")
        self.viewer.display_page()
        self._load_boxes()
        messagebox.showinfo("Başarılı", f"{count} adet vektör kutusu silindi!", parent=self)
