"""
PDF Viewer - Annotation Mixin'i
Tooltip, not, işaret ve link işlemleri
"""

import customtkinter as ctk
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import messagebox, colorchooser


class AnnotationMixin:
    """Annotation işlemleri metodlarını içeren mixin sınıfı"""
    
    def on_canvas_motion(self, event):
        """Canvas üzerinde mouse hareketi"""
        # Tooltip gösterme (basit versiyon)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Mouse altındaki annotation'ları kontrol et
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            tags = self.canvas.gettags(item)
            if "custom_note" in tags or "note_annotation" in tags:
                # Note için tooltip
                note_content = self.get_note_content_at_position(x, y)
                if note_content:
                    self.show_tooltip(event.x_root, event.y_root, f"Not: {note_content[:50]}...")
                else:
                    self.show_tooltip(event.x_root, event.y_root, "Not - Çift tıklayın detayları görmek için")
                return
            elif "custom_bookmark" in tags:
                self.show_tooltip(event.x_root, event.y_root, "İşaret - Çift tıklayın detayları görmek için")
                return
            elif "custom_link" in tags:
                link_url = self.get_link_url_at_position(x, y)
                if link_url:
                    self.show_tooltip(event.x_root, event.y_root, f"Link: {link_url}")
                else:
                    self.show_tooltip(event.x_root, event.y_root, "Link - Çift tıklayın açmak için")
                return
                
        # Tooltip'i gizle
        self.hide_tooltip()
        
    def show_tooltip(self, x, y, text):
        """Tooltip göster"""
        try:
            if self.tooltip_window:
                self.tooltip_window.destroy()
                
            self.tooltip_window = tk.Toplevel(self.root)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x+10}+{y+10}")
            
            label = tk.Label(self.tooltip_window, text=text, 
                            background="lightyellow", relief="solid", borderwidth=1,
                            font=("Arial", 12))
            label.pack()
            
            # Otomatik gizleme
            self.root.after(3000, self.hide_tooltip)
            
        except Exception as e:
            print(f"Tooltip gösterme hatası: {e}")
        
    def hide_tooltip(self):
        """Tooltip'i gizle"""
        try:
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None
        except Exception as e:
            print(f"Tooltip gizleme hatası: {e}")
            
    def _annotation_at_canvas_pos(self, cx, cy):
        """Canvas koordinatında annotation varsa (ann, idx) döndür, yoksa (None, -1)"""
        items = self.canvas.find_overlapping(cx - 15, cy - 15, cx + 15, cy + 15)
        for item in items:
            for tag in self.canvas.gettags(item):
                if tag.startswith("ann_idx_"):
                    try:
                        idx = int(tag[8:])
                        anns = self.annotation_manager.annotations
                        if 0 <= idx < len(anns):
                            return anns[idx], idx
                    except (ValueError, IndexError):
                        pass
        return None, -1

    def on_canvas_double_click(self, event):
        """Canvas çift tıklama: annotation varsa aç/göster"""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        ann, idx = self._annotation_at_canvas_pos(cx, cy)
        if ann is None:
            return
        ann_type = ann.get('type', '')
        page_no = ann.get('page', 0) + 1
        if ann_type == 'note':
            text = ann.get('text', '(boş not)')
            messagebox.showinfo(f"📝 Not — Sayfa {page_no}", text, parent=self.root)
            # print(f"DEBUG: Not çift tık gösterildi — idx={idx}, sayfa={page_no}")
        elif ann_type == 'link':
            url = ann.get('url', '')
            if url:
                import webbrowser
                webbrowser.open(url)
                # print(f"DEBUG: Link tarayıcıda açıldı — {url}")
            else:
                messagebox.showinfo("🔗 Link", "URL bulunamadı.", parent=self.root)
        elif ann_type == 'bookmark':
            label = ann.get('text', '')
            msg = f"Sayfa {page_no}" + (f": {label}" if label else "")
            messagebox.showinfo("⭐ İşaret", msg, parent=self.root)
            # print(f"DEBUG: Bookmark çift tık gösterildi — sayfa={page_no}")
                
    def get_note_content_at_position(self, x, y):
        """Belirtilen pozisyondaki not içeriğini al"""
        if not hasattr(self, 'annotation_manager'):
            return None
            
        # Canvas koordinatlarını PDF koordinatlarına çevir
        mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
        inv_mat = ~mat
        pdf_point = fitz.Point(x, y) * inv_mat
        
        for annotation in self.annotation_manager.annotations:
            if annotation["page"] == self.current_page and annotation["type"] == "note":
                pos = annotation["position"]
                # Yakınlık kontrolü (20 piksel tolerans)
                if abs(pdf_point.x - pos["x"]) < 20 and abs(pdf_point.y - pos["y"]) < 20:
                    return annotation["text"]
        return None
        
    def get_link_url_at_position(self, x, y):
        """Belirtilen pozisyondaki link URL'sini al"""
        if not hasattr(self, 'annotation_manager'):
            return None
            
        mat = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
        inv_mat = ~mat
        pdf_point = fitz.Point(x, y) * inv_mat
        
        for annotation in self.annotation_manager.annotations:
            if annotation["page"] == self.current_page and annotation["type"] == "link":
                pos = annotation["position"]
                if abs(pdf_point.x - pos["x"]) < 20 and abs(pdf_point.y - pos["y"]) < 20:
                    return annotation["url"]
        return None
        
    def show_note_details(self, x, y):
        """Not detaylarını göster"""
        from pdf_view_utils import center_window
        
        note_content = self.get_note_content_at_position(x, y)
        if note_content:
            # Detay penceresi oluştur
            detail_window = ctk.CTkToplevel(self.root)
            detail_window.title("Not Detayları")
            detail_window.geometry("400x300")
            center_window(detail_window, 400, 300)
            detail_window.transient(self.root)
            
            # Not içeriği
            ctk.CTkLabel(detail_window, text="📝 Not İçeriği", 
                        font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
            
            text_widget = ctk.CTkTextbox(detail_window, height=150)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", note_content)
            text_widget.configure(state="disabled")
            
            ctk.CTkButton(detail_window, text="Kapat", 
                         command=detail_window.destroy).pack(pady=10)
        else:
            messagebox.showinfo("Bilgi", "Bu pozisyonda not bulunamadı.")
            
    def show_bookmark_details(self, x, y):
        """İşaret detaylarını göster"""
        messagebox.showinfo("İşaret", f"Sayfa {self.current_page + 1} işareti\nBu sayfayı işaretlediniz.")
        
    def open_link(self, x, y):
        """Link'i aç"""
        link_url = self.get_link_url_at_position(x, y)
        if link_url:
            try:
                import webbrowser
                webbrowser.open(link_url)
                messagebox.showinfo("Link Açıldı", f"Link tarayıcıda açıldı:\n{link_url}")
            except Exception as e:
                messagebox.showerror("Hata", f"Link açılamadı:\n{str(e)}")
        else:
            messagebox.showinfo("Bilgi", "Bu pozisyonda link bulunamadı.")
    
    def toggle_highlight_mode(self):
        """Vurgulama modunu aç/kapat"""
        if hasattr(self.highlight_tool, 'is_active') and self.highlight_tool.is_active:
            self.highlight_tool.deactivate()
            self.status_label.configure(text="Vurgulama modu kapalı")
        else:
            self.highlight_tool.activate()
            self.status_label.configure(text="Vurgulama modu açık - Fare ile dikdörtgen çizin")
    
    def open_advanced_annotations(self):
        """Gelişmiş annotation penceresini aç"""
        self.annotation_manager.create_annotation_window()
    
    def choose_highlight_color(self):
        """Vurgulama rengi seç"""
        color = colorchooser.askcolor(color=self.highlight_color)[1]
        if color:
            self.highlight_color = color

    # ── Hızlı Annotation Araçları ─────────────────────────────────────────

    def quick_add_note(self):
        """Hızlı not ekleme — küçük popup diyalog."""
        if not getattr(self, 'pdf_document', None):
            messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin.")
            return

        from pdf_view_utils import center_window

        dlg = ctk.CTkToplevel(self.root)
        dlg.title("📝 Hızlı Not Ekle")
        dlg.geometry("360x230")
        center_window(dlg, 360, 230)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(
            dlg, text=f"📝 Not Ekle — Sayfa {self.current_page + 1}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(14, 4))

        text_box = ctk.CTkTextbox(dlg, height=100, width=320)
        text_box.pack(padx=18, pady=4)
        text_box.focus()

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=10)

        def _confirm():
            note = text_box.get("1.0", "end-1c").strip()
            if not note:
                return
            self.annotation_manager.add_note_annotation(self.current_page, note)
            self.display_page()
            self.status_label.configure(
                text=f"📝 Not eklendi — Sayfa {self.current_page + 1}"
            )
            # print(f"DEBUG: Hızlı not eklendi — Sayfa {self.current_page + 1}: {note[:40]}")
            dlg.destroy()

        ctk.CTkButton(
            btn_row, text="İptal", width=90, fg_color="gray",
            command=dlg.destroy
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="✓ Ekle", width=110, command=_confirm
        ).pack(side="left", padx=8)

        dlg.bind("<Control-Return>", lambda e: _confirm())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def quick_add_bookmark(self):
        """Hızlı işaret ekleme — mevcut sayfaya anında ekler, diyalog açmaz."""
        if not getattr(self, 'pdf_document', None):
            messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin.")
            return

        text = f"Sayfa {self.current_page + 1} İşareti"
        self.annotation_manager.add_bookmark_annotation(self.current_page, text)
        self.display_page()
        self.status_label.configure(
            text=f"⭐ İşaret eklendi — Sayfa {self.current_page + 1}"
        )
        # print(f"DEBUG: Hızlı işaret eklendi — Sayfa {self.current_page + 1}")

    def quick_add_link(self):
        """Hızlı link ekleme — küçük popup diyalog."""
        if not getattr(self, 'pdf_document', None):
            messagebox.showwarning("Uyarı", "Önce bir PDF dosyası yükleyin.")
            return

        from pdf_view_utils import center_window

        dlg = ctk.CTkToplevel(self.root)
        dlg.title("🔗 Hızlı Link Ekle")
        dlg.geometry("380x210")
        center_window(dlg, 380, 210)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(
            dlg, text=f"🔗 Link Ekle — Sayfa {self.current_page + 1}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(14, 4))

        ctk.CTkLabel(dlg, text="URL:", anchor="w").pack(padx=18, fill="x")
        url_entry = ctk.CTkEntry(dlg, width=340, placeholder_text="https://example.com")
        url_entry.pack(padx=18, pady=(2, 6))
        url_entry.focus()

        ctk.CTkLabel(dlg, text="Etiket (opsiyonel):", anchor="w").pack(padx=18, fill="x")
        label_entry = ctk.CTkEntry(dlg, width=340, placeholder_text="Link açıklaması")
        label_entry.pack(padx=18, pady=(2, 4))

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=10)

        def _confirm():
            url = url_entry.get().strip()
            if not url:
                return
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            lbl = label_entry.get().strip() or f"Link — Sayfa {self.current_page + 1}"
            self.annotation_manager.add_link_annotation(self.current_page, lbl, url)
            self.display_page()
            self.status_label.configure(
                text=f"🔗 Link eklendi — Sayfa {self.current_page + 1}"
            )
            # print(f"DEBUG: Hızlı link eklendi — Sayfa {self.current_page + 1}: {url}")
            dlg.destroy()

        ctk.CTkButton(
            btn_row, text="İptal", width=90, fg_color="gray",
            command=dlg.destroy
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="✓ Ekle", width=110, command=_confirm
        ).pack(side="left", padx=8)

        dlg.bind("<Return>", lambda e: _confirm())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def on_canvas_right_click(self, event):
        """Sağ tık: annotation varsa bağlam menüsü göster"""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        ann, idx = self._annotation_at_canvas_pos(cx, cy)
        if ann is not None:
            self._show_annotation_context_menu(event, ann, idx)

    def _show_annotation_context_menu(self, event, ann, idx):
        """Annotation için sağ-tık bağlam menüsü"""

        menu = tk.Menu(self.root, tearoff=0,
                       background="#333333", 
                        foreground="white", 
                        activebackground="#1F6AA5"
                       )
        ann_type = ann.get('type', '')
        type_labels = {'note': '📝 Not', 'bookmark': '⭐ İşaret', 'link': '🔗 Link'}
        menu.add_command(
            label=type_labels.get(ann_type, 'Annotation'),
            state='disabled'
        )
        menu.add_separator()
        if ann_type in ('note', 'link'):
            menu.add_command(
                label="✏️ İçeriği Değiştir",
                command=lambda: self._edit_annotation(ann, idx)
            )
        menu.add_command(
            label="🗑️ Bu annotation'ı Sil",
            command=lambda: self._delete_annotation_at(idx)
        )

        list_font = ("Segoe UI", 13) 
        menu.config(font=list_font)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        # print(f"DEBUG: Bağlam menüsü — idx={idx}, tür={ann_type}")

    def _edit_annotation(self, ann, idx):
        """Not veya link annotation'ını düzenle"""
        from pdf_view_utils import center_window
        ann_type = ann.get('type', '')
        if ann_type == 'note':
            dlg = ctk.CTkToplevel(self.root)
            dlg.title("📝 Notu Düzenle")
            dlg.geometry("360x230")
            center_window(dlg, 360, 230)
            dlg.transient(self.root)
            dlg.grab_set()
            ctk.CTkLabel(dlg, text="📝 Notu Düzenle",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(14, 4))
            text_box = ctk.CTkTextbox(dlg, height=100, width=320)
            text_box.pack(padx=18, pady=4)
            text_box.insert("1.0", ann.get('text', ''))
            text_box.focus()
            btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
            btn_row.pack(pady=10)
            def _save():
                new_text = text_box.get("1.0", "end-1c").strip()
                if new_text:
                    self.annotation_manager.annotations[idx]['text'] = new_text
                    self.display_page()
                    # print(f"DEBUG: Not düzenlendi — idx={idx}")
                dlg.destroy()
            ctk.CTkButton(btn_row, text="İptal", width=90, fg_color="gray",
                          command=dlg.destroy).pack(side="left", padx=8)
            ctk.CTkButton(btn_row, text="✓ Kaydet", width=110,
                          command=_save).pack(side="left", padx=8)
            dlg.bind("<Control-Return>", lambda e: _save())
            dlg.bind("<Escape>", lambda e: dlg.destroy())
        elif ann_type == 'link':
            dlg = ctk.CTkToplevel(self.root)
            dlg.title("🔗 Linki Düzenle")
            dlg.geometry("380x200")
            center_window(dlg, 380, 200)
            dlg.transient(self.root)
            dlg.grab_set()
            ctk.CTkLabel(dlg, text="🔗 URL Düzenle",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(14, 4))
            ctk.CTkLabel(dlg, text="URL:", anchor="w").pack(padx=18, fill="x")
            url_entry = ctk.CTkEntry(dlg, width=340)
            url_entry.pack(padx=18, pady=(2, 8))
            url_entry.insert(0, ann.get('url', ''))
            url_entry.focus()
            btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
            btn_row.pack(pady=8)
            def _save_link():
                new_url = url_entry.get().strip()
                if new_url:
                    if not (new_url.startswith("http://") or new_url.startswith("https://")):
                        new_url = "https://" + new_url
                    self.annotation_manager.annotations[idx]['url'] = new_url
                    self.display_page()
                    # print(f"DEBUG: Link düzenlendi — idx={idx}, url={new_url}")
                dlg.destroy()
            ctk.CTkButton(btn_row, text="İptal", width=90, fg_color="gray",
                          command=dlg.destroy).pack(side="left", padx=8)
            ctk.CTkButton(btn_row, text="✓ Kaydet", width=110,
                          command=_save_link).pack(side="left", padx=8)
            dlg.bind("<Return>", lambda e: _save_link())
            dlg.bind("<Escape>", lambda e: dlg.destroy())

    def _delete_annotation_at(self, idx):
        """Belirtilen indexteki annotation'ı sil ve sayfayı yenile"""
        try:
            ann = self.annotation_manager.annotations[idx]
            ann_type = ann.get('type', '')
            if not messagebox.askyesno("Annotation Sil",
                    f"Bu {ann_type} annotation'ını silmek istediğinizden emin misiniz?",
                    parent=self.root):
                return
            del self.annotation_manager.annotations[idx]
            self.display_page()
            self.status_label.configure(text=f"Annotation silindi.")
            # print(f"DEBUG: Annotation silindi — idx={idx}, tür={ann_type}")
        except (IndexError, Exception) as e:
            print(f"DEBUG: Annotation silme hatası — {e}")

    def open_quick_access(self):
        """F2 — Hızlı Erişim panelini aç."""
        if not hasattr(self, '_quick_access_panel') or self._quick_access_panel is None:
            from pdf_view_quick_access import QuickAccessPanel
            self._quick_access_panel = QuickAccessPanel(self)
        self._quick_access_panel.open()
        # print("DEBUG: Hızlı Erişim paneli çağrıldı (F2)")

    def on_canvas_click(self, event):
        """Canvas tıklama olayını işle"""
        if hasattr(self, 'highlight_mode') and self.highlight_mode:
            # Vurgulama modunda ise, tıklanan konumu işaretle
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            # Basit vurgulama (gerçek PDF annotation'ı için daha karmaşık kod gerekir)
            self.canvas.create_oval(
                x-5, y-5, x+5, y+5,
                fill=self.highlight_color, outline="",
                tags="manual_highlight"
            )
