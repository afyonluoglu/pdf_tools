"""
PDF Viewer - Sayfa İçi Metin Düzenleme Arka Uç Motoru (InPageTextEngine)
PyMuPDF Redaction, metin yazma, font gömme, otomatik sığdırma (auto-fit),
koordinat dönüşümleri ve geri alma (undo) işlemlerini yönetir.
"""

import os
import fitz  # PyMuPDF
from tkinter import messagebox
from typing import Optional, Dict, Any, List, Callable


class InPageTextEngine:
    """PDF sayfa içi metin çıkarma, koordinat dönüşümü, redaction ve yazma motoru"""

    def __init__(self, pdf_viewer, on_clear_visuals: Optional[Callable] = None):
        self.pdf_viewer = pdf_viewer
        self.on_clear_visuals = on_clear_visuals
        self._undo_stack: List[bytes] = []

    def canvas_to_pdf_rect(self, cx1: float, cy1: float, cx2: float, cy2: float) -> fitz.Rect:
        """Canvas koordinatlarını mevcut Zoom ve Rotation matrisine göre PDF Rect'ine çevirir"""
        zoom = getattr(self.pdf_viewer, 'zoom_level', 1.0)
        rotation = getattr(self.pdf_viewer, 'rotation', 0)
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        p1, p2 = fitz.Point(cx1, cy1) * ~mat, fitz.Point(cx2, cy2) * ~mat
        return fitz.Rect(min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y))

    def pdf_to_canvas_rect(self, pdf_rect: fitz.Rect) -> tuple:
        """PDF Rect koordinatlarını Canvas koordinatlarına çevirir"""
        zoom = getattr(self.pdf_viewer, 'zoom_level', 1.0)
        rotation = getattr(self.pdf_viewer, 'rotation', 0)
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        p1, p2 = fitz.Point(pdf_rect.x0, pdf_rect.y0) * mat, fitz.Point(pdf_rect.x1, pdf_rect.y1) * mat
        return (min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y))

    def find_word_at_click(self, cx: float, cy: float) -> Optional[tuple]:
        """Kullanıcı sadece tek tık yaptıysa, tıklanan noktadaki satır veya kelimenin koordinatlarını döndürür"""
        try:
            page = self.pdf_viewer.pdf_document[self.pdf_viewer.current_page]
            zoom, rotation = getattr(self.pdf_viewer, 'zoom_level', 1.0), getattr(self.pdf_viewer, 'rotation', 0)
            mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
            pdf_pt = fitz.Point(cx, cy) * ~mat
            for b in page.get_text("dict").get("blocks", []):
                if b.get("type") == 0:
                    for l in b.get("lines", []):
                        r = fitz.Rect(l.get("bbox"))
                        if (r.x0 - 4 <= pdf_pt.x <= r.x1 + 4 and r.y0 - 4 <= pdf_pt.y <= r.y1 + 4):
                            return self.pdf_to_canvas_rect(r)
            for w in page.get_text("words"):
                if fitz.Rect(w[:4]).contains(pdf_pt):
                    return self.pdf_to_canvas_rect(fitz.Rect(w[:4]))
        except Exception:
            pass
        return None

    def extract_text_and_styles(self, pdf_rect: fitz.Rect) -> Dict[str, Any]:
        """Seçilen PDF dikdörtgenindeki metni, fontunu, boyutunu ve rengini ayıklar"""
        page = self.pdf_viewer.pdf_document[self.pdf_viewer.current_page]
        dict_data = page.get_text("dict", clip=pdf_rect, sort=True)

        raw_items = []
        fonts = []
        sizes = []
        colors = []
        flags = []
        span_bboxes = []
        first_origin = None

        for block in dict_data.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    line_spans_text = []
                    line_span_bboxes = []
                    line_origin = None
                    for span in line.get("spans", []):
                        t = span.get("text", "")
                        if not t:
                            continue
                        line_spans_text.append(t)
                        if t.strip():
                            fonts.append(span.get("font", "Arial"))
                            sizes.append(span.get("size", 11.0))
                            colors.append(span.get("color", 0))
                            flags.append(span.get("flags", 0))
                            sb = fitz.Rect(span.get("bbox"))
                            span_bboxes.append(sb)
                            line_span_bboxes.append(sb)
                            if first_origin is None and "origin" in span:
                                first_origin = span.get("origin")
                            if line_origin is None and "origin" in span:
                                line_origin = span.get("origin")
                    if line_span_bboxes:
                        box = fitz.Rect(line_span_bboxes[0])
                        for b in line_span_bboxes[1:]:
                            box |= b
                        raw_items.append({
                            "text": "".join(line_spans_text),
                            "bbox": box,
                            "origin": line_origin or (box.x0, box.y1),
                        })

        # Satırları dikey görsel sıraya (origin y, sonra x0) göre sırala
        def sort_key(item):
            oy = item["origin"][1] if item["origin"] else item["bbox"].y0
            ox = item["origin"][0] if item["origin"] else item["bbox"].x0
            return (round(oy, 1), round(ox, 1))

        raw_items.sort(key=sort_key)

        # Aynı taban çizgisine / satıra denk gelen parçaları birleştir
        lines_info = []
        for item in raw_items:
            if not lines_info:
                lines_info.append(item)
                continue
            last = lines_info[-1]
            same_line = False
            if last["origin"] and item["origin"]:
                if abs(last["origin"][1] - item["origin"][1]) < 3.0:
                    same_line = True
            else:
                v_overlap = min(last["bbox"].y1, item["bbox"].y1) - max(last["bbox"].y0, item["bbox"].y0)
                min_h = min(last["bbox"].height, item["bbox"].height)
                if v_overlap > 0.5 * min_h:
                    same_line = True

            if same_line:
                sep = ""
                if not last["text"].endswith(" ") and not item["text"].startswith(" "):
                    sep = " "
                last["text"] = last["text"] + sep + item["text"]
                last["bbox"] |= item["bbox"]
                if item["origin"][0] < last["origin"][0]:
                    last["origin"] = item["origin"]
            else:
                lines_info.append(item)

        # Metinleri temizle ve geçerli satırları ayıkla
        cleaned_lines = []
        valid_lines_info = []
        for li in lines_info:
            txt = li["text"].strip()
            if txt:
                li["text"] = txt
                cleaned_lines.append(txt)
                valid_lines_info.append(li)

        full_text = "\n".join(cleaned_lines)

        # Gerçek metin sınırlayıcı kutusu (kullanıcının fareyle çektiği gevşek kutu yerine metnin tam kutusu)
        exact_bbox = pdf_rect
        if span_bboxes:
            exact_bbox = fitz.Rect(span_bboxes[0])
            for b in span_bboxes[1:]:
                exact_bbox |= b

        # En sık geçen font, boyut, renk ve stiller
        dominant_font = max(set(fonts), key=fonts.count) if fonts else "Arial"
        dominant_size = sum(sizes) / len(sizes) if sizes else 11.0
        hex_color = "#000000"
        if colors:
            dom_col = max(set(colors), key=colors.count)
            if dom_col != 0:
                hex_color = f"#{(dom_col >> 16) & 255:02x}{(dom_col >> 8) & 255:02x}{dom_col & 255:02x}"
            else:
                # Type 3 veya rengi 0 raporlanan fontlarda piksel haritasından gerçek rengi örnekle
                try:
                    pix = page.get_pixmap()
                    non_white = []
                    sample_boxes = span_bboxes[:3] if span_bboxes else [exact_bbox]
                    for sb in sample_boxes:
                        x0 = max(0, int(sb.x0))
                        y0 = max(0, int(sb.y0))
                        x1 = min(pix.width, int(sb.x1))
                        y1 = min(pix.height, int(sb.y1))
                        for sy in range(y0, y1, 2):
                            for sx in range(x0, x1, 2):
                                p = pix.pixel(sx, sy)
                                if p[0] < 240 or p[1] < 240 or p[2] < 240:
                                    non_white.append(p)
                    if non_white:
                        from collections import Counter
                        top_p = Counter(non_white).most_common(1)[0][0]
                        hex_color = f"#{top_p[0]:02x}{top_p[1]:02x}{top_p[2]:02x}"
                except Exception:
                    hex_color = "#000000"
        is_bold = any((f & 2 != 0 or f & 16 != 0 or "bold" in dominant_font.lower()) for f in flags)
        is_italic = any((f & 1 != 0 or "italic" in dominant_font.lower() or "oblique" in dominant_font.lower()) for f in flags)

        # Varsa önceden eklenmiş InPageBG veya Highlight arka planını tespit et
        detected_bg = None
        for a in page.annots():
            if a.rect.intersects(exact_bbox):
                if a.info.get("title") == "InPageBG" or a.type[1] in ("Highlight", "Square"):
                    col = a.colors.get("stroke") or a.colors.get("fill")
                    if col and len(col) >= 3:
                        detected_bg = f"#{int(col[0]*255):02x}{int(col[1]*255):02x}{int(col[2]*255):02x}"
                        break

        # Akıllı Font Çözümleyici ile font adı, dosyası ve bellekteki gömülü fontu tespit et
        from pd_font_resolver import font_resolver
        resolved_font = font_resolver.resolve_font_from_pdf(self.pdf_viewer.pdf_document, page, dominant_font)
        resolved_family = resolved_font.get("family_name") or dominant_font
        font_file_path = resolved_font.get("fontfile")
        font_buffer_data = resolved_font.get("fontbuffer")
        font_source = resolved_font.get("source", "fallback")

        return {
            "text": full_text, "font": dominant_font, "resolved_font_name": resolved_family,
            "fontfile": font_file_path, "fontbuffer": font_buffer_data, "font_source": font_source,
            "size": dominant_size, "color": hex_color,
            "bg_color": detected_bg, "is_bold": is_bold, "is_italic": is_italic,
            "exact_bbox": exact_bbox, "origin": first_origin, "lines_info": valid_lines_info,
        }

    def sample_pixel_color(self, cx: int, cy: int) -> str:
        """Canvas koordinatındaki pikselin rengini hex (#RRGGBB) olarak döndürür"""
        hex_color = "#FFFFFF"
        try:
            if hasattr(self.pdf_viewer, 'pdf_document') and self.pdf_viewer.pdf_document:
                page = self.pdf_viewer.pdf_document[self.pdf_viewer.current_page]
                mat = fitz.Matrix(
                    getattr(self.pdf_viewer, 'zoom_level', 1.0),
                    getattr(self.pdf_viewer, 'zoom_level', 1.0)
                ).prerotate(getattr(self.pdf_viewer, 'rotation', 0))
                pix = page.get_pixmap(matrix=mat)
                if 0 <= cx < pix.width and 0 <= cy < pix.height:
                    p = pix.pixel(cx, cy)
                    hex_color = f"#{p[0]:02x}{p[1]:02x}{p[2]:02x}"
        except Exception as e:
            print(f"Eyedropper hatası: {e}")
        return hex_color

    def apply_text_edit(self, rect_coords: list, payload: Dict[str, Any]):
        """PyMuPDF Redaction ve Metin Yazma motorunu çalıştırır"""
        if not self.pdf_viewer.pdf_document:
            return

        # Geri Alma (Undo) için mevcut PDF durumunun yedeğini al
        try:
            doc_snapshot = self.pdf_viewer.pdf_document.tobytes()
            self._undo_stack.append(doc_snapshot)
            if len(self._undo_stack) > 15:
                self._undo_stack.pop(0)
        except Exception as e:
            print(f"Undo snapshot hatası: {e}")

        try:
            page = self.pdf_viewer.pdf_document[self.pdf_viewer.current_page]
            exact_rect = fitz.Rect(rect_coords[0], rect_coords[1], rect_coords[2], rect_coords[3])

            new_text = payload.get("text", "")
            fontfile = payload.get("fontfile")
            fontbuffer = payload.get("fontbuffer")
            fontname = payload.get("fontname", "Arial")
            is_bold = payload.get("is_bold", False)
            is_italic = payload.get("is_italic", False)

            # Eğer bold veya italic istenmişse veya fontfile geçerli değilse, font_resolver'dan tam stil dosyasını iste
            if is_bold or is_italic or not fontfile or not os.path.isfile(fontfile):
                from pd_font_resolver import font_resolver
                resolved_file = font_resolver.resolve_file_for_family(fontname, is_bold=is_bold, is_italic=is_italic)
                if resolved_file and os.path.isfile(resolved_file):
                    fontfile = resolved_file
                    fontbuffer = None  # Stil dosyasını kullandığımız için eski buffer'ı temizle
                elif not fontfile or not os.path.isfile(fontfile):
                    windir = os.environ.get("WINDIR", r"C:\Windows")
                    sys_arial = os.path.join(windir, "Fonts", "arial.ttf")
                    if os.path.isfile(sys_arial):
                        fontfile = sys_arial

            fontsize = payload.get("fontsize", 11.0)
            align = payload.get("align", 0)
            auto_fit = payload.get("auto_fit", True)
            lines_info = payload.get("lines_info", [])

            def hex_to_rgb_tuple(h):
                if not h or not h.startswith("#"):
                    return (0.0, 0.0, 0.0)
                h = h.lstrip("#")
                return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

            text_color = hex_to_rgb_tuple(payload.get("color", "#000000"))
            bg_color_hex = payload.get("bg_color")
            bg_color = hex_to_rgb_tuple(bg_color_hex) if bg_color_hex else None

            # Eski metnin özel bir arka planı var mıydı?
            old_bg_hex = payload.get("old_bg_color")
            old_had_bg = bool(old_bg_hex)

            offset_x = payload.get("offset_x", 0.0)
            offset_y = payload.get("offset_y", 0.0)

            # 1. ESKİ KONUMDAKİ InPageBG ANNOTATION'LARINI TEMİZLE
            for a in list(page.annots()):
                if (a.info.get("title") == "InPageBG" or a.type[1] in ("Highlight", "Square")) and a.rect.intersects(exact_rect):
                    page.delete_annot(a)
                    old_had_bg = True

            # 2. ESKİ METNİ SİL (Redaction)
            redact_boxes = [li["bbox"] for li in lines_info] if len(lines_info) > 1 else [exact_rect]
            for b in redact_boxes:
                fb = fitz.Rect(b)
                r_rect = fitz.Rect(fb.x0 - 0.5, fb.y0 - 0.5, fb.x1 + 0.5, fb.y1 + 0.5)
                if payload.get("page_bg_color"):
                    page.add_redact_annot(r_rect, fill=hex_to_rgb_tuple(payload["page_bg_color"]))
                elif old_had_bg:
                    # Yalnızca önceden özel arka plan rengi olan metinler için eski yeri temiz zeminle ört
                    page.add_redact_annot(r_rect, fill=(1.0, 1.0, 1.0))
                else:
                    # Saydam / doğal metinler (örn: mavi kutudaki tarih): dolgusuz silinir, alttaki şekil bozulmaz!
                    page.add_redact_annot(r_rect)

            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE
            )

            # 3. YENİ KONUMDA ARKA PLAN DOLGUSU OLUŞTUR (Saydam değilse)
            if bg_color:
                target_bg_rect = fitz.Rect(
                    exact_rect.x0 + offset_x - 1.0, exact_rect.y0 + offset_y - 1.0,
                    exact_rect.x1 + offset_x + 1.0, exact_rect.y1 + offset_y + 1.0
                )
                annot = page.add_highlight_annot(target_bg_rect)
                annot.set_colors(stroke=bg_color)
                annot.set_info(title="InPageBG")
                annot.update()

            # 3. YENİ METNİ YERLEŞTİR (Taban çizgisi kilitli ve ofset uygulanmış olarak)
            if new_text.strip():
                page_rect = page.rect
                new_lines = new_text.split("\n") if len(lines_info) > 1 else [new_text]
                for idx, line_str in enumerate(new_lines):
                    line_clean = line_str.rstrip("\r")
                    if not line_clean.strip():
                        continue

                    if len(lines_info) > 1:
                        if idx < len(lines_info):
                            orig_box = fitz.Rect(lines_info[idx]["bbox"])
                            orig_origin = lines_info[idx].get("origin")
                        else:
                            last_box = fitz.Rect(lines_info[-1]["bbox"])
                            last_origin = lines_info[-1].get("origin")
                            line_spacing = max(fontsize * 1.35, 14.0)
                            extra_dy = (idx - len(lines_info) + 1) * line_spacing
                            orig_box = fitz.Rect(last_box.x0, last_box.y0 + extra_dy, last_box.x1, last_box.y1 + extra_dy)
                            orig_origin = (last_origin[0], last_origin[1] + extra_dy) if last_origin else None
                    else:
                        orig_box = exact_rect
                        orig_origin = payload.get("origin")

                    # Fontun ascender oranını dinamik öğren (Arial: ~0.905, Sparkly Yarn: ~1.215 vb.)
                    # MuPDF insert_textbox baseline'ı: target_rect.y0 + (ascender * fs)
                    # Orijinal baseline'a tam kilitlemek için: base_y0 = target_baseline_y - (ascender * fs)
                    ascender = 0.905
                    try:
                        if fontfile and os.path.isfile(fontfile):
                            ascender = fitz.Font(fontfile=fontfile).ascender
                        elif fontbuffer:
                            ascender = fitz.Font(fontbuffer=fontbuffer).ascender
                    except Exception:
                        ascender = 0.905

                    if orig_origin:
                        target_baseline_y = orig_origin[1] + offset_y
                        base_y0 = target_baseline_y - (ascender * fontsize)
                        base_x0 = orig_origin[0] + offset_x
                    else:
                        base_y0 = orig_box.y0 + offset_y
                        base_x0 = orig_box.x0 + offset_x

                    max_w = max(orig_box.width * 2, page_rect.width - base_x0 - 20)
                    max_h = max(orig_box.height * 2, 50.0 if len(lines_info) > 1 else 200.0)

                    if align == 1:  # Center
                        cx = base_x0 + orig_box.width / 2
                        half_w = max(orig_box.width / 2, 150.0)
                        target_rect = fitz.Rect(cx - half_w, base_y0, cx + half_w, base_y0 + max_h)
                    elif align == 2:  # Right
                        target_rect = fitz.Rect(base_x0 + orig_box.width - max_w, base_y0, base_x0 + orig_box.width, base_y0 + max_h)
                    else:  # Left
                        target_rect = fitz.Rect(base_x0, base_y0, base_x0 + max_w, base_y0 + max_h)

                    self._insert_single_line(page, target_rect, line_clean, fontsize, fontfile, fontbuffer, text_color, align, auto_fit)

            # Belgeyi değiştirildi olarak işaretle
            self.pdf_viewer.is_modified = True

            # Canvas görsel seçimlerini temizle
            if self.on_clear_visuals:
                self.on_clear_visuals()

            # Sayfayı yeniden render et
            self.pdf_viewer.display_page()

            if hasattr(self.pdf_viewer, 'status_label'):
                self.pdf_viewer.status_label.configure(
                    text="✓ Metin başarıyla güncellendi. (Geri almak için Ctrl+Z)"
                )

        except Exception as e:
            messagebox.showerror("Hata", f"Metin güncellenirken hata oluştu:\n{str(e)}")

    def _insert_single_line(self, page, target_rect, text, fontsize, fontfile, fontbuffer, color, align, auto_fit):
        """Tek bir satırı otomatik sığdırma ve font kontrolleriyle PDF sayfasına yerleştirir"""
        custom_fontname = None
        if fontfile and os.path.isfile(fontfile):
            custom_fontname = "F_InPage"
            try:
                page.insert_font(fontname=custom_fontname, fontfile=fontfile)
            except Exception:
                custom_fontname = None
        elif fontbuffer:
            custom_fontname = "F_InPageBuf"
            try:
                page.insert_font(fontname=custom_fontname, fontbuffer=fontbuffer)
            except Exception:
                custom_fontname = None

        line_fs = fontsize
        if auto_fit:
            test_fs = fontsize
            while test_fs >= 5.0:
                test_doc = fitz.open()
                test_page = test_doc.new_page(width=target_rect.width + 100, height=target_rect.height + 100)
                dummy_rect = fitz.Rect(0, 0, target_rect.width, target_rect.height)
                if custom_fontname == "F_InPage" and fontfile:
                    test_page.insert_font(fontname="F_Test", fontfile=fontfile)
                    rc = test_page.insert_textbox(dummy_rect, text, fontsize=test_fs, fontname="F_Test", align=align)
                elif custom_fontname == "F_InPageBuf" and fontbuffer:
                    test_page.insert_font(fontname="F_Test", fontbuffer=fontbuffer)
                    rc = test_page.insert_textbox(dummy_rect, text, fontsize=test_fs, fontname="F_Test", align=align)
                else:
                    rc = test_page.insert_textbox(dummy_rect, text, fontsize=test_fs, fontname="helv", align=align)
                test_doc.close()
                if rc >= 0:
                    break
                test_fs -= 0.5
            line_fs = max(test_fs, 5.0)

        if custom_fontname:
            page.insert_textbox(target_rect, text, fontsize=line_fs, fontname=custom_fontname, color=color, align=align)
        else:
            page.insert_textbox(target_rect, text, fontsize=line_fs, fontname="helv", color=color, align=align)

    def undo(self):
        """Son yapılan metin düzenlemesini geri alır"""
        if not self._undo_stack:
            messagebox.showinfo("Bilgi", "Geri alınacak bir metin düzenleme işlemi yok.")
            return

        try:
            prev_bytes = self._undo_stack.pop()
            current_p = self.pdf_viewer.current_page
            new_doc = fitz.open(stream=prev_bytes, filetype="pdf")
            self.pdf_viewer.pdf_document = new_doc
            self.pdf_viewer.current_page = min(current_p, len(new_doc) - 1)

            if self.on_clear_visuals:
                self.on_clear_visuals()

            self.pdf_viewer.display_page()

            if hasattr(self.pdf_viewer, 'status_label'):
                self.pdf_viewer.status_label.configure(text="✓ Son metin düzenlemesi geri alındı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Geri alma hatası: {str(e)}")
