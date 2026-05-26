"""
PDF Viewer - Hızlı Erişim Paneli (F2)
Tüm annotation'ları listeler; sayfalara hızlı geçiş ve silme imkanı sağlar.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pdf_view_utils import center_window


class QuickAccessPanel:
    """F2 Hızlı Erişim Paneli — annotation navigasyonu ve yönetimi"""

    def __init__(self, pdf_viewer):
        self.pdf_viewer = pdf_viewer
        self.window = None

    # ── Açma ─────────────────────────────────────────────────────────────

    def open(self):
        """Paneli aç; zaten açıksa öne getir ve yenile."""
        try:
            if self.window and self.window.winfo_exists():
                self.window.lift()
                self.window.focus()
                self.refresh()
                return
        except Exception:
            self.window = None
        self._create_window()

    # ── Pencere oluşturma ─────────────────────────────────────────────────

    def _create_window(self):
        self.window = ctk.CTkToplevel(self.pdf_viewer.root)
        self.window.title("⚡ Hızlı Erişim — Annotation'lar")
        self.window.geometry("780x560")
        center_window(self.window, 780, 560)
        self.window.transient(self.pdf_viewer.root)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        self.window.bind("<F5>", lambda e: self.refresh())

        # ── Başlık ve filtre çubuğu ──────────────────────────────────────
        top = ctk.CTkFrame(self.window)
        top.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            top, text="⚡ Hızlı Erişim",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(side="left", padx=10, pady=8)

        self.filter_var = ctk.StringVar(value="Tümü")
        ctk.CTkComboBox(
            top, width=145,
            values=["Tümü", "🖍️ Vurgulama", "📝 Not", "⭐ İşaret", "🔗 Link"],
            variable=self.filter_var,
            command=lambda _: self.refresh()
        ).pack(side="left", padx=6, pady=8)

        ctk.CTkButton(
            top, text="🔄 Yenile", width=90,
            command=self.refresh
        ).pack(side="left", padx=4, pady=8)

        self.count_label = ctk.CTkLabel(top, text="", text_color="gray")
        self.count_label.pack(side="right", padx=12, pady=8)

        # ── Tablo başlığı ────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self.window, height=32, fg_color="#1a2a40")
        hdr.pack(fill="x", padx=12, pady=(0, 2))
        hdr.pack_propagate(False)

        for label, width, anchor in [
            ("Tür",              95, "center"),
            ("Sayfa",            52, "center"),
            ("İçerik / Önizleme", 330, "w"),
            ("Tarih",            115, "center"),
            ("İşlemler",         110, "center"),
        ]:
            ctk.CTkLabel(
                hdr, text=label, width=width, anchor=anchor,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#7bc0ff"
            ).pack(side="left", padx=3, pady=5)

        # ── Scrollable liste ─────────────────────────────────────────────
        list_container = ctk.CTkFrame(self.window)
        list_container.pack(fill="both", expand=True, padx=12, pady=4)

        self.list_canvas = tk.Canvas(list_container, bg="#1e1e2e", highlightthickness=0)
        self.list_scrollbar = ctk.CTkScrollbar(list_container, command=self.list_canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.list_canvas)

        self.list_canvas.configure(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True)

        self._frame_id = self.list_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(
                scrollregion=self.list_canvas.bbox("all")
            )
        )
        self.list_canvas.bind(
            "<Configure>",
            lambda e: self.list_canvas.itemconfig(self._frame_id, width=e.width)
        )

        def _wheel(evt):
            self.list_canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")

        self.list_canvas.bind("<MouseWheel>", _wheel)
        self.scrollable_frame.bind("<MouseWheel>", _wheel)

        # ── Alt durum çubuğu ─────────────────────────────────────────────
        bot = ctk.CTkFrame(self.window, height=40)
        bot.pack(fill="x", padx=12, pady=(4, 12))
        bot.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            bot, text="F2 aç · F5 yenile · Esc kapat",
            text_color="gray", font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            bot, text="Kapat", width=80,
            command=self.window.destroy
        ).pack(side="right", padx=10, pady=5)

        self.refresh()
        self.window.focus()
        print("DEBUG: Hızlı Erişim paneli açıldı")

    # ── Filtre yardımcısı ─────────────────────────────────────────────────

    def _annotations(self):
        """Ortak annotation listesini döndür (viewer ya da manager üzerinden)."""
        lst = getattr(self.pdf_viewer, 'annotations', None)
        if not lst and hasattr(self.pdf_viewer, 'annotation_manager'):
            lst = getattr(self.pdf_viewer.annotation_manager, 'annotations', [])
        return lst or []

    def _filtered(self):
        f = getattr(self, 'filter_var', None)
        sel = f.get() if f else "Tümü"
        type_map = {
            "🖍️ Vurgulama": "highlight",
            "📝 Not":       "note",
            "⭐ İşaret":    "bookmark",
            "🔗 Link":      "link",
        }
        all_ann = self._annotations()
        if sel in type_map:
            return [(i, a) for i, a in enumerate(all_ann) if a.get("type") == type_map[sel]]
        return list(enumerate(all_ann))

    # ── Yenileme ─────────────────────────────────────────────────────────

    def refresh(self):
        """Listeyi yeniden çiz."""
        try:
            if not self.window or not self.window.winfo_exists():
                return

            for w in list(self.scrollable_frame.winfo_children()):
                try:
                    w.pack_forget()
                except Exception:
                    pass

            items = self._filtered()
            self.count_label.configure(text=f"{len(items)} annotation")

            if not items:
                ctk.CTkLabel(
                    self.scrollable_frame,
                    text="Bu türde annotation bulunamadı.",
                    text_color="gray"
                ).pack(pady=40)
                return

            for orig_idx, ann in items:
                self._build_row(orig_idx, ann)

            self.pdf_viewer.root.after(
                80,
                lambda: self.list_canvas.configure(
                    scrollregion=self.list_canvas.bbox("all")
                )
            )
            print(f"DEBUG: Hızlı Erişim yenilendi — {len(items)} annotation")
        except Exception as e:
            print(f"DEBUG: QuickAccess refresh hatası: {e}")

    # ── Satır oluşturma ────────────────────────────────────────────────────

    def _build_row(self, orig_idx, ann):
        type_icons = {
            "highlight": ("🖍️", "#ffe066"),
            "note":      ("📝", "#7bc0ff"),
            "bookmark":  ("⭐", "#ffa040"),
            "link":      ("🔗", "#66e899"),
        }
        ann_type = ann.get("type", "?")
        icon, color = type_icons.get(ann_type, ("📄", "white"))

        row = ctk.CTkFrame(self.scrollable_frame)
        row.pack(fill="x", padx=4, pady=2)

        # Tür
        ctk.CTkLabel(
            row, text=f"{icon} {ann_type[:9]}",
            width=95, anchor="center", text_color=color
        ).pack(side="left", padx=3, pady=6)

        # Sayfa (1-based)
        ctk.CTkLabel(
            row, text=str(ann.get("page", 0) + 1),
            width=52, anchor="center"
        ).pack(side="left", padx=3, pady=6)

        # İçerik önizleme
        if ann_type == "highlight":
            preview = f"Renk: {ann.get('color', '#FFFF00')}"
        elif ann_type == "link":
            url = ann.get("url", "")
            preview = url[:55] + ("…" if len(url) > 55 else "")
        else:
            txt = ann.get("text", "")
            preview = txt[:60] + ("…" if len(txt) > 60 else "")

        ctk.CTkLabel(
            row, text=preview,
            width=330, anchor="w", text_color="gray"
        ).pack(side="left", padx=3, pady=6)

        # Tarih
        try:
            ts = datetime.fromisoformat(ann["timestamp"]).strftime("%d.%m.%y %H:%M")
        except Exception:
            ts = "—"
        ctk.CTkLabel(
            row, text=ts, width=115, anchor="center",
            text_color="gray", font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=3, pady=6)

        # Butonlar
        btn_box = ctk.CTkFrame(row, fg_color="transparent")
        btn_box.pack(side="right", padx=6, pady=4)

        ctk.CTkButton(
            btn_box, text="Git", width=48, height=26,
            fg_color="#1e5799", hover_color="#2978d6",
            command=lambda a=ann: self._goto(a)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_box, text="Sil", width=48, height=26,
            fg_color="#7a1c1c", hover_color="#c0392b",
            command=lambda idx=orig_idx, a=ann: self._delete(idx, a)
        ).pack(side="left", padx=2)

    # ── Eylemler ──────────────────────────────────────────────────────────

    def _goto(self, ann):
        """Annotation sayfasına git."""
        page = ann.get("page", 0)
        try:
            self.pdf_viewer.current_page = page
            self.pdf_viewer.display_page()
            if hasattr(self.pdf_viewer, 'update_ui'):
                self.pdf_viewer.update_ui()
            self.status_label.configure(text=f"✓ Sayfa {page + 1}'e gidildi")
            print(f"DEBUG: QuickAccess Git — Sayfa {page + 1}")
        except Exception as e:
            print(f"DEBUG: QuickAccess goto hatası: {e}")

    def _delete(self, orig_idx, ann):
        """Onaydan sonra annotation'ı sil."""
        type_names = {
            "highlight": "Vurgulama", "note": "Not",
            "bookmark": "İşaret",    "link": "Link"
        }
        label = type_names.get(ann.get("type", ""), ann.get("type", "annotation"))
        page_no = ann.get("page", 0) + 1

        confirmed = messagebox.askyesno(
            "Silme Onayı",
            f"Sayfa {page_no} — {label} annotation'ı\nsilinecek. Devam edilsin mi?",
            parent=self.window
        )
        if not confirmed:
            print(f"DEBUG: Silme iptal edildi — {label} Sayfa {page_no}")
            return

        try:
            all_ann = self._annotations()
            if 0 <= orig_idx < len(all_ann):
                del all_ann[orig_idx]

                # Sayfa görünümünü yenile
                if hasattr(self.pdf_viewer, 'display_page'):
                    self.pdf_viewer.display_page()

                # Gelişmiş panel açıksa orada da yenile
                mgr = getattr(self.pdf_viewer, 'annotation_manager', None)
                if mgr:
                    try:
                        win = getattr(mgr, 'annotation_window', None)
                        if win and win.winfo_exists():
                            mgr.refresh_annotation_list()
                    except Exception:
                        pass

                self.refresh()
                self.status_label.configure(text=f"✓ {label} (Sayfa {page_no}) silindi")
                print(f"DEBUG: QuickAccess — {label} Sayfa {page_no} silindi")
        except Exception as e:
            print(f"DEBUG: QuickAccess delete hatası: {e}")
            messagebox.showerror("Hata", f"Silme sırasında hata:\n{e}", parent=self.window)
