"""
PDF Viewer - UI Kurulum Mixin'i
Toolbar, canvas ve temel UI bileşenlerini oluşturur
"""

import customtkinter as ctk
import tkinter as tk


class UISetupMixin:
    """UI kurulum metodlarını içeren mixin sınıfı"""
    
    def setup_ui(self):
        """Ana kullanıcı arayüzünü oluştur"""
        # Ana toolbar
        self.toolbar = ctk.CTkFrame(self.root, height=50)
        self.toolbar.pack(fill="x", padx=5, pady=0)
        self.toolbar.pack_propagate(False)

        self.toolbar2 = ctk.CTkFrame(self.root, height=50)
        self.toolbar2.pack(fill="x", padx=5, pady=0)
        self.toolbar2.pack_propagate(False)        

        # Toolbar butonları
        self.setup_toolbar()
        
        # Ana içerik alanı
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Sol panel (küçük resim görünümü)
        self.sidebar = ctk.CTkFrame(self.main_frame, width=200)
        self.sidebar.pack(side="left", fill="y", padx=(5, 2), pady=5)
        self.sidebar.pack_propagate(False)
        
        # Küçük resim başlığı
        ctk.CTkLabel(self.sidebar, text="Sayfa Küçük Resimleri", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # Küçük resim scroll alanı - Fixed version (Normal Canvas + Scrollbar)
        thumbnail_container = ctk.CTkFrame(self.sidebar)
        thumbnail_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Thumbnail canvas ve scrollbar
        self.thumbnail_canvas = tk.Canvas(thumbnail_container, bg='gray17', highlightthickness=0)
        self.thumbnail_scrollbar = ctk.CTkScrollbar(thumbnail_container, command=self.thumbnail_canvas.yview)
        self.thumbnail_frame = ctk.CTkFrame(self.thumbnail_canvas)
        
        # Scrollbar konfigürasyonu
        self.thumbnail_canvas.configure(yscrollcommand=self.thumbnail_scrollbar.set)
        
        # Pack layout
        self.thumbnail_scrollbar.pack(side="right", fill="y")
        self.thumbnail_canvas.pack(side="left", fill="both", expand=True)
        
        # Canvas içindeki frame
        self.thumbnail_canvas_frame_id = self.thumbnail_canvas.create_window((0, 0), 
                                                                            window=self.thumbnail_frame, 
                                                                            anchor="nw")
        
        # Thumbnail mouse wheel binding
        def _on_thumbnail_mousewheel(event):
            self.thumbnail_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.thumbnail_canvas.bind("<MouseWheel>", _on_thumbnail_mousewheel)
        self.thumbnail_frame.bind("<MouseWheel>", _on_thumbnail_mousewheel)
        
        # Frame boyutları ayarla
        self.thumbnail_frame.bind('<Configure>', self._configure_thumbnail_scroll_region)
        self.thumbnail_canvas.bind('<Configure>', self._configure_thumbnail_canvas_width)
        
        # Sağ panel (ana PDF görünümü)
        self.viewer_frame = ctk.CTkFrame(self.main_frame)
        self.viewer_frame.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)
        
        # PDF canvas için scroll alanı
        self.canvas_frame = ctk.CTkFrame(self.viewer_frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canvas ve scrollbar'lar
        self.setup_canvas()
        
        # Canvas tooltip desteği
        self.setup_canvas_tooltips()
        
        # Alt durum çubuğu
        self.status_bar = ctk.CTkFrame(self.root, height=30)
        self.status_bar.pack(fill="x", padx=5, pady=(0, 5))
        self.status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="PDF dosyası yükleyin")
        self.status_label.pack(side="left", padx=10, pady=5)
        
    def setup_toolbar(self):
        """Toolbar butonlarını oluştur"""

        CONST_PADY = 0
        # Dosya işlemleri
        ctk.CTkButton(self.toolbar, text="📁 Aç", width=80, 
                     command=self.open_pdf).pack(side="left", padx=5, pady=CONST_PADY)
        
        ctk.CTkButton(self.toolbar, text="💾 Kaydet", width=80,
                     command=self.save_pdf).pack(side="left", padx=5, pady=CONST_PADY)
        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar, width=2, height=50, fg_color="gray").pack(side="left", padx=10, pady=CONST_PADY)
        
        # Navigasyon
        ctk.CTkButton(self.toolbar, text="⬅️", width=40,
                     command=self.previous_page).pack(side="left", padx=2, pady=CONST_PADY)
        
        self.page_entry = ctk.CTkEntry(self.toolbar, width=60, placeholder_text="1")
        self.page_entry.pack(side="left", padx=5, pady=CONST_PADY)
        self.page_entry.bind("<Return>", self.goto_page)
        
        self.page_label = ctk.CTkLabel(self.toolbar, text="/ 0")
        self.page_label.pack(side="left", padx=5, pady=CONST_PADY)
        
        ctk.CTkButton(self.toolbar, text="➡️", width=40,
                     command=self.next_page).pack(side="left", padx=2, pady=CONST_PADY)
        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar, width=2, height=50, fg_color="gray").pack(side="left", padx=10, pady=CONST_PADY)
        
        # Zoom kontrolleri
        ctk.CTkButton(self.toolbar, text="🔍-", width=40,
                     command=self.zoom_out).pack(side="left", padx=2, pady=CONST_PADY)
        
        self.zoom_label = ctk.CTkLabel(self.toolbar, text="100%", width=60)
        self.zoom_label.pack(side="left", padx=5, pady=CONST_PADY)
        
        ctk.CTkButton(self.toolbar, text="🔍+", width=40,
                     command=self.zoom_in).pack(side="left", padx=2, pady=CONST_PADY)
        
        ctk.CTkButton(self.toolbar, text="↻", width=40,
                     command=self.rotate_page).pack(side="left", padx=5, pady=CONST_PADY)
        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar, width=2, height=50, fg_color="gray").pack(side="left", padx=10, pady=CONST_PADY)
        
        # Arama
        self.search_entry = ctk.CTkEntry(self.toolbar, width=110, placeholder_text="Metin ara...")
        self.search_entry.pack(side="left", padx=5, pady=CONST_PADY)
        self.search_entry.bind("<Return>", self.search_text)
        
        ctk.CTkButton(self.toolbar, text="🔍", width=40,
                     command=self.search_text).pack(side="left", padx=2, pady=CONST_PADY)

        ctk.CTkButton(self.toolbar, text="Next", width=40,
                     command=self.search_next).pack(side="left", padx=2, pady=CONST_PADY)

        
        # Ayırıcı
        ctk.CTkFrame(self.toolbar, width=2, height=50, fg_color="gray").pack(side="left", padx=10, pady=CONST_PADY)
        
        # Annotation araçları
        ctk.CTkButton(self.toolbar2, text="🖍️ Vurgula", width=100,
                     command=self.toggle_highlight_mode).pack(side="left", padx=5, pady=CONST_PADY)
        
        ctk.CTkButton(self.toolbar2, text="🎨 Renk", width=80,
                     command=self.choose_highlight_color).pack(side="left", padx=5, pady=CONST_PADY)
        
        # ctk.CTkFrame(self.toolbar, width=2, height=40, fg_color="gray").pack(side="left", padx=6, pady=CONST_PADY)

        ctk.CTkButton(self.toolbar2, text="📝 Not", width=80,
                     command=self.quick_add_note).pack(side="left", padx=4, pady=CONST_PADY)

        # ctk.CTkButton(self.toolbar2, text="⭐ İşaret", width=90,
        #              command=self.quick_add_bookmark).pack(side="left", padx=4, pady=CONST_PADY)

        ctk.CTkButton(self.toolbar2, text="🔗 Link", width=80,
                     command=self.quick_add_link).pack(side="left", padx=4, pady=CONST_PADY)

        ctk.CTkButton(self.toolbar2, text="⚡ Hızlı Erişim Paneli", width=90,
                     command=self.open_quick_access).pack(side="left", padx=4, pady=CONST_PADY)

        ctk.CTkButton(self.toolbar2, text="📝 Gelişmiş", width=100,
                     command=self.open_advanced_annotations).pack(side="left", padx=5, pady=CONST_PADY)

        # Ayırıcı
        # ctk.CTkFrame(self.toolbar, width=2, height=50, fg_color="gray").pack(side="left", padx=10, pady=CONST_PADY)

        # Metne çevirme
        ctk.CTkButton(self.toolbar, text="📄 Metne Çevir & Seslendir", width=120,
                     command=self.extract_text_to_file).pack(side="left", padx=5, pady=CONST_PADY)
        
    def setup_canvas(self):
        """PDF görüntüleme canvas'ını oluştur"""
        # Ana canvas frame
        canvas_container = ctk.CTkFrame(self.canvas_frame)
        canvas_container.pack(fill="both", expand=True)
        
        # Tkinter canvas (scroll özelliği için)
        self.canvas = tk.Canvas(canvas_container, bg="#2b2b2b", highlightthickness=0)
        
        # Scrollbar'lar
        v_scrollbar = ctk.CTkScrollbar(canvas_container, orientation="vertical", command=self.canvas.yview)
        h_scrollbar = ctk.CTkScrollbar(canvas_container, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack işlemleri
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mouse_wheel)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        
    def setup_canvas_tooltips(self):
        """Canvas tooltip desteği"""
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.tooltip_window = None
    
    def setup_keybindings(self):
        """Klavye kısayollarını ayarla"""
        self.root.bind("<Control-o>", lambda e: self.open_pdf())
        self.root.bind("<Control-s>", lambda e: self.save_pdf())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_zoom())
        self.root.bind("<Left>", lambda e: self.previous_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<Prior>", lambda e: self.previous_page())  # Page Up
        self.root.bind("<Next>", lambda e: self.next_page())  # Page Down
        self.root.bind("<F1>", lambda e: self.open_help())    # Yardım
        self.root.bind("<F2>", lambda e: self.open_quick_access())  # Hızlı Erişim

    def open_help(self):
        """F1 - Yardım dosyasını varsayılan tarayıcıda aç"""
        import webbrowser
        import os
        help_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_viewer_help.html")
        if os.path.exists(help_file):
            webbrowser.open(f"file:///{help_file.replace(os.sep, '/')}")
            # print(f"DEBUG: Yardım dosyası açıldı: {help_file}")
        else:
            from tkinter import messagebox
            messagebox.showwarning("Yardım", "Yardım dosyası bulunamadı: pdf_viewer_help.html")
            # print(f"DEBUG: Yardım dosyası bulunamadı: {help_file}")
    
    def _configure_thumbnail_scroll_region(self, event):
        """Thumbnail canvas scroll region'ını güncelle"""
        try:
            self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
        except Exception as e:
            print(f"Thumbnail scroll region güncelleme hatası: {e}")
    
    def _configure_thumbnail_canvas_width(self, event):
        """Thumbnail canvas width'ini ayarla"""
        try:
            canvas_width = event.width
            self.thumbnail_canvas.itemconfig(self.thumbnail_canvas_frame_id, width=canvas_width)
        except Exception as e:
            print(f"Thumbnail canvas width ayarlama hatası: {e}")
    
    def update_ui(self):
        """UI elementlerini güncelle"""
        if self.pdf_document:
            self.page_entry.delete(0, "end")
            self.page_entry.insert(0, str(self.current_page + 1))
            self.page_label.configure(text=f"/ {self.total_pages}")
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
