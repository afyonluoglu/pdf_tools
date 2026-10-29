"""
PDF Viewer - Gömülü Annotation Senkronizasyonu (pd_annot_sync.py)
PDF içindeki yerel/gömülü annotation'ların (Square, Highlight, vb.) tespiti,
Canvas koordinat dönüşümleri, PyMuPDF ile gerçek zamanlı senkronizasyonu
(taşıma, boyutlandırma, silme, renk değiştirme).
"""

import fitz  # PyMuPDF


def hex_from_color(color_list):
    """PyMuPDF float RGB listesini (#RRGGBB) hex formatına çevirir"""
    if not color_list:
        return "#FFFF00"
    r = int(min(max(color_list[0], 0.0), 1.0) * 255)
    g = int(min(max(color_list[1], 0.0), 1.0) * 255) if len(color_list) > 1 else r
    b = int(min(max(color_list[2], 0.0), 1.0) * 255) if len(color_list) > 2 else r
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb_float(color_hex):
    """Hex renk kodunu ([r, g, b]) 0.0-1.0 float listesine çevirir"""
    try:
        hex_str = color_hex.lstrip('#')
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return [r, g, b]
    except Exception:
        pass
    return [1.0, 1.0, 0.0]


def calculate_canvas_coords(pdf_rect, zoom_level=1.0, rotation=0):
    """PDF rect koordinatlarını (PDF points) mevcut zoom ve rotasyona göre canvas koordinatlarına çevirir"""
    try:
        mat = fitz.Matrix(zoom_level, zoom_level).prerotate(rotation)
        p1 = fitz.Point(pdf_rect[0], pdf_rect[1]) * mat
        p2 = fitz.Point(pdf_rect[2], pdf_rect[3]) * mat
        return min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y)
    except Exception:
        z = zoom_level if zoom_level > 0 else 1.0
        return pdf_rect[0] * z, pdf_rect[1] * z, pdf_rect[2] * z, pdf_rect[3] * z


def canvas_to_pdf_rect(cx1, cy1, cx2, cy2, zoom_level=1.0, rotation=0):
    """Canvas koordinatlarını PDF rect koordinatlarına (PDF points) çevirir"""
    try:
        inv_mat = ~fitz.Matrix(zoom_level, zoom_level).prerotate(rotation)
        p1 = fitz.Point(cx1, cy1) * inv_mat
        p2 = fitz.Point(cx2, cy2) * inv_mat
        return [min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y)]
    except Exception:
        z = zoom_level if zoom_level > 0 else 1.0
        return [cx1 / z, cy1 / z, cx2 / z, cy2 / z]


def load_embedded_annotations(pdf_document):
    """
    PDF belgesindeki gömülü tüm annotation'ları (Square, Highlight, Text vb.)
    okuyup etkileşimli annotation sözlükleri listesi olarak döndürür.
    """
    if not pdf_document:
        return []

    items = []
    for page_num in range(len(pdf_document)):
        try:
            page = pdf_document[page_num]
            for a in page.annots():
                try:
                    type_tuple = a.type
                    type_name = type_tuple[1] if isinstance(type_tuple, tuple) else str(type_tuple)
                    type_id = type_tuple[0] if isinstance(type_tuple, tuple) else 0

                    r = a.rect
                    pdf_rect = [r.x0, r.y0, r.x1, r.y1]

                    colors = a.colors or {}
                    fill_col = colors.get('fill')
                    stroke_col = colors.get('stroke')

                    color_hex = "#FFFF00"
                    stroke_hex = ""
                    if fill_col:
                        color_hex = hex_from_color(fill_col)
                    if stroke_col:
                        stroke_hex = hex_from_color(stroke_col)
                        if not fill_col:
                            color_hex = stroke_hex

                    info = a.info or {}
                    title = info.get('title', '')
                    content = info.get('content', '')

                    # Square, Highlight, Circle, FreeText, Ink -> highlight türünde etkileşimli kutu
                    if type_name in ('Square', 'Highlight', 'Circle', 'FreeText', 'Ink'):
                        generic_type = 'highlight'
                    elif type_name in ('Text',):
                        generic_type = 'note'
                    elif type_name in ('Link',):
                        generic_type = 'link'
                    else:
                        generic_type = 'highlight'

                    ann = {
                        'page': page_num,
                        'type': generic_type,
                        'annot_type': type_name,
                        'type_id': type_id,
                        'color': color_hex,
                        'stroke_color': stroke_hex,
                        'border_width': 1.5 if stroke_hex else 1.0,
                        'pdf_rect': pdf_rect,
                        'coordinates': {'x1': pdf_rect[0], 'y1': pdf_rect[1], 'x2': pdf_rect[2], 'y2': pdf_rect[3]},
                        'position': {'x': pdf_rect[0], 'y': pdf_rect[1]},
                        'xref': a.xref,
                        'is_embedded': True,
                        'text': content or title,
                        'title': title
                    }
                    items.append(ann)
                except Exception as e:
                    print(f"DEBUG [pd_annot_sync]: Sayfa {page_num} annot okuma hatası: {e}")
        except Exception as e:
            print(f"DEBUG [pd_annot_sync]: Sayfa {page_num} okuma hatası: {e}")

    return items


def sync_update_rect(pdf_document, ann, cx1, cy1, cx2, cy2, zoom_level=1.0, rotation=0):
    """Annotation canvas üzerinde taşındığında veya yeniden boyutlandırıldığında PDF koordinatlarını ve PyMuPDF belgesini günceller"""
    pdf_rect = canvas_to_pdf_rect(cx1, cy1, cx2, cy2, zoom_level, rotation)
    ann['pdf_rect'] = pdf_rect
    ann['coordinates'] = {'x1': cx1, 'y1': cy1, 'x2': cx2, 'y2': cy2}

    xref = ann.get('xref')
    if xref and pdf_document:
        try:
            page_num = ann.get('page', 0)
            if 0 <= page_num < len(pdf_document):
                page = pdf_document[page_num]
                for a in page.annots():
                    if a.xref == xref:
                        if a.type[1] == 'Highlight':
                            col = a.colors.get('stroke') or a.colors.get('fill') or [1.0, 1.0, 0.0]
                            page.delete_annot(a)
                            new_a = page.add_rect_annot(fitz.Rect(pdf_rect))
                            new_a.set_colors(fill=col, stroke=col)
                            new_a.set_opacity(0.4)
                            new_a.update()
                            ann['xref'] = new_a.xref
                            ann['annot_type'] = 'Square'
                        else:
                            a.set_rect(fitz.Rect(pdf_rect))
                            a.update()
                        break
        except Exception as e:
            print(f"DEBUG [pd_annot_sync]: Rect güncelleme hatası: {e}")


def sync_delete_annotation(pdf_document, ann):
    """Annotation silindiğinde PDF belgesindeki karşılık gelen yerel annot'ı siler"""
    xref = ann.get('xref')
    if xref and pdf_document:
        try:
            page_num = ann.get('page', 0)
            if 0 <= page_num < len(pdf_document):
                page = pdf_document[page_num]
                for a in list(page.annots()):
                    if a.xref == xref:
                        page.delete_annot(a)
                        break
        except Exception as e:
            print(f"DEBUG [pd_annot_sync]: Annot silme hatası: {e}")


def sync_update_color(pdf_document, ann, new_color_hex):
    """Annotation rengi değiştiğinde hem veri yapısını hem PDF'teki nesneyi günceller"""
    ann['color'] = new_color_hex
    xref = ann.get('xref')
    if xref and pdf_document:
        try:
            page_num = ann.get('page', 0)
            if 0 <= page_num < len(pdf_document):
                page = pdf_document[page_num]
                for a in page.annots():
                    if a.xref == xref:
                        rgb = hex_to_rgb_float(new_color_hex)
                        a.set_colors(stroke=rgb, fill=rgb)
                        a.update()
                        break
        except Exception as e:
            print(f"DEBUG [pd_annot_sync]: Renk güncelleme hatası: {e}")
