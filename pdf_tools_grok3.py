import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
import json
import xml.etree.ElementTree as ET
from io import BytesIO
import tabula  # Tablo algılama için
import pytesseract  # OCR için
try:
    from pdf2image import convert_from_path  # PDF'den görüntü için
except ImportError:
    convert_from_path = None

class PDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Gelişmiş PDF Düzenleyici")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f4f8")

        # Variables
        self.pdf_path = tk.StringVar()
        self.doc = None
        self.current_page = 0
        self.page_count = 0
        self.zoom = 1.0
        self.annotation_text = tk.StringVar()
        self.meta_data = {}
        self.annotation_type = tk.StringVar(value="text")  # text, line, rect, highlight
        self.toc = []
        self.selected_image = None
        self.image_move_mode = False
        self.text_insert_mode = False
        self.inserted_images = {}  # Eklenen resimler: {page: [(rect, image_data), ...]}

        # Modern UI
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Helvetica", 10), padding=5)
        self.style.configure("TLabel", font=("Helvetica", 10), background="#f0f4f8")
        self.style.configure("TCheckbutton", font=("Helvetica", 10), background="#f0f4f8")

        # Menu Bar
        self.create_menu()

        # Main Frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Toolbar
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill="x", pady=5)
        ttk.Button(self.toolbar, text="PDF Aç", command=self.open_pdf).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Kaydet", command=self.save_pdf).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Önceki Sayfa", command=self.prev_page).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Sonraki Sayfa", command=self.next_page).pack(side="left", padx=5)
        ttk.Label(self.toolbar, text="Zoom:").pack(side="left", padx=5)
        self.zoom_entry = ttk.Entry(self.toolbar, width=5, textvariable=tk.StringVar(value="1.0"))
        self.zoom_entry.pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Uygula", command=self.apply_zoom).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Tablo Çıkar", command=self.extract_table).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="OCR Uygula", command=self.apply_ocr).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Resim Seç", command=self.toggle_image_move_mode).pack(side="left", padx=5)

        # PDF Display
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.resize_canvas)
        self.canvas.bind("<Button-1>", self.handle_canvas_click)

        # Status Bar
        self.status = ttk.Label(self.main_frame, text="Sayfa: 0/0")
        self.status.pack(pady=5)

        # Annotation and Text Input
        self.annotation_frame = ttk.Frame(self.main_frame)
        self.annotation_frame.pack(fill="x", pady=5)
        ttk.Label(self.annotation_frame, text="Anotasyon/Metin:").pack(side="left", padx=5)
        ttk.Entry(self.annotation_frame, textvariable=self.annotation_text).pack(side="left", padx=5)
        ttk.Button(self.annotation_frame, text="Metin Ekle", command=self.start_text_insert).pack(side="left", padx=5)
        ttk.OptionMenu(self.annotation_frame, self.annotation_type, "text", "text", "line", "rect", "highlight").pack(side="left", padx=5)
        ttk.Button(self.annotation_frame, text="Anotasyon Ekle", command=self.add_annotation).pack(side="left", padx=5)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="PDF Aç", command=self.open_pdf, accelerator="Ctrl+O")
        file_menu.add_command(label="Kaydet", command=self.save_pdf, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit, accelerator="Ctrl+Q")

        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Düzenle", menu=edit_menu)
        edit_menu.add_command(label="Sayfa Ekle", command=self.add_page, accelerator="Ctrl+N")
        edit_menu.add_command(label="Sayfa Sil", command=self.delete_page, accelerator="Ctrl+D")
        edit_menu.add_command(label="Sayfa Döndür", command=self.rotate_page, accelerator="Ctrl+R")
        edit_menu.add_command(label="Metin Ekle", command=self.start_text_insert, accelerator="Ctrl+T")
        edit_menu.add_command(label="Resim Ekle", command=self.add_image, accelerator="Ctrl+I")
        edit_menu.add_command(label="Anotasyon Ekle", command=self.add_annotation, accelerator="Ctrl+A")
        edit_menu.add_command(label="Meta Veri Düzenle", command=self.edit_metadata, accelerator="Ctrl+M")
        edit_menu.add_command(label="TOC Düzenle", command=self.edit_toc, accelerator="Ctrl+E")
        edit_menu.add_command(label="Resim Taşı", command=self.toggle_image_move_mode, accelerator="Ctrl+Shift+M")

        # Convert Menu
        convert_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dönüştür", menu=convert_menu)
        convert_menu.add_command(label="TXT'ye Dönüştür", command=lambda: self.convert_to("text"), accelerator="Ctrl+Shift+T")
        convert_menu.add_command(label="HTML'ye Dönüştür", command=lambda: self.convert_to("html"), accelerator="Ctrl+Shift+H")
        convert_menu.add_command(label="JSON'a Dönüştür", command=lambda: self.convert_to("json"), accelerator="Ctrl+Shift+J")
        convert_menu.add_command(label="XML'e Dönüştür", command=lambda: self.convert_to("xml"), accelerator="Ctrl+Shift+X")
        convert_menu.add_command(label="PNG'ye Dönüştür", command=lambda: self.convert_to("png"), accelerator="Ctrl+Shift+P")

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Araçlar", menu=tools_menu)
        tools_menu.add_command(label="Tablo Çıkar", command=self.extract_table, accelerator="Ctrl+Shift+B")
        tools_menu.add_command(label="OCR Uygula", command=self.apply_ocr, accelerator="Ctrl+Shift+O")

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Kullanım Kılavuzu", command=self.show_help)

        # Key Bindings
        self.root.bind("<Control-o>", lambda e: self.open_pdf())
        self.root.bind("<Control-s>", lambda e: self.save_pdf())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-n>", lambda e: self.add_page())
        self.root.bind("<Control-d>", lambda e: self.delete_page())
        self.root.bind("<Control-r>", lambda e: self.rotate_page())
        self.root.bind("<Control-t>", lambda e: self.start_text_insert())
        self.root.bind("<Control-i>", lambda e: self.add_image())
        self.root.bind("<Control-a>", lambda e: self.add_annotation())
        self.root.bind("<Control-m>", lambda e: self.edit_metadata())
        self.root.bind("<Control-e>", lambda e: self.edit_toc())
        self.root.bind("<Control-Shift-T>", lambda e: self.convert_to("text"))
        self.root.bind("<Control-Shift-H>", lambda e: self.convert_to("html"))
        self.root.bind("<Control-Shift-J>", lambda e: self.convert_to("json"))
        self.root.bind("<Control-Shift-X>", lambda e: self.convert_to("xml"))
        self.root.bind("<Control-Shift-P>", lambda e: self.convert_to("png"))
        self.root.bind("<Control-Shift-B>", lambda e: self.extract_table())
        self.root.bind("<Control-Shift-O>", lambda e: self.apply_ocr())
        self.root.bind("<Control-Shift-M>", lambda e: self.toggle_image_move_mode())

    def show_help(self):
        help_text = """
        Gelişmiş PDF Düzenleyici - Kullanım Kılavuzu

        Bu program, PDF dosyalarını açar, düzenler, dönüştürür ve ek araçlar sunar.

        Özellikler:
        - PDF dosyasını açıp görüntüleme.
        - Sayfa ekleme, silme, döndürme.
        - Metin, resim ve gelişmiş anotasyonlar (çizgi, dikdörtgen, vurgulama) ekleme.
        - Resim seçip yerini değiştirme.
        - Meta veri ve TOC (İçindekiler) düzenleme.
        - Tablo çıkarma (tabula-py) ve OCR (pytesseract) desteği.
        - PDF'yi TXT, HTML, JSON, XML, PNG formatlarına dönüştürme.
        - Düzenlenen PDF'yi kaydetme.

        Metin Ekleme Adımları:
        1. "Anotasyon/Metin" kutusuna metni yazın.
        2. "Metin Ekle" (Ctrl+T) butonuna basın.
        3. Canvas üzerinde metni yerleştirmek istediğiniz konuma tıklayın.

        Resim Taşıma Adımları:
        1. "Resim Seç" (Ctrl+Shift+M) butonuna basın.
        2. Taşımak istediğiniz resme tıklayın.
        3. Yeni konuma tıklayın.

        Zoom Kullanımı:
        1. Zoom kutusuna bir değer (0.1-5.0) girin.
        2. "Uygula" butonuna basın.

        Kısayollar:
        - Ctrl+O: PDF Aç
        - Ctrl+S: Kaydet
        - Ctrl+Q: Çıkış
        - Ctrl+N: Sayfa Ekle
        - Ctrl+D: Sayfa Sil
        - Ctrl+R: Sayfa Döndür
        - Ctrl+T: Metin Ekle
        - Ctrl+I: Resim Ekle
        - Ctrl+A: Anotasyon Ekle
        - Ctrl+M: Meta Veri Düzenle
        - Ctrl+E: TOC Düzenle
        - Ctrl+Shift+M: Resim Taşı
        - Ctrl+Shift+T: TXT'ye Dönüştür
        - Ctrl+Shift+H: HTML'ye Dönüştür
        - Ctrl+Shift+J: JSON'a Dönüştür
        - Ctrl+Shift+X: XML'e Dönüştür
        - Ctrl+Shift+P: PNG'ye Dönüştür
        - Ctrl+Shift+B: Tablo Çıkar
        - Ctrl+Shift+O: OCR Uygula
        """
        messagebox.showinfo("Yardım", help_text)

    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.pdf_path.set(file_path)
            self.doc = fitz.open(file_path)
            self.page_count = self.doc.page_count
            self.current_page = 0
            self.toc = self.doc.get_toc()
            self.inserted_images = {}  # Yeni PDF için resimleri sıfırla
            self.display_page()
            self.status.config(text=f"Sayfa: {self.current_page + 1}/{self.page_count}")
            self.meta_data = self.doc.metadata

    def display_page(self):
        if not self.doc:
            return
        page = self.doc[self.current_page]
        # Zoom faktörüne göre DPI hesapla (temel DPI 72, zoom ile ölçeklendir)
        dpi = int(72 * self.zoom)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(BytesIO(pix.tobytes()))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.status.config(text=f"Sayfa: {self.current_page + 1}/{self.page_count}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self):
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.display_page()

    def apply_zoom(self):
        try:
            new_zoom = float(self.zoom_entry.get())
            if new_zoom < 0.1 or new_zoom > 5.0:
                raise ValueError("Zoom 0.1 ile 5.0 arasında olmalı!")
            self.zoom = new_zoom
            self.display_page()
        except ValueError as e:
            messagebox.showerror("Hata", str(e))

    def resize_canvas(self, event):
        self.display_page()

    def add_page(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        self.doc.insert_page(self.current_page)
        self.page_count += 1
        self.display_page()

    def delete_page(self):
        if not self.doc or self.page_count <= 1:
            messagebox.showerror("Hata", "Silinecek sayfa yok!")
            return
        self.doc.delete_page(self.current_page)
        self.page_count -= 1
        if self.current_page >= self.page_count:
            self.current_page = self.page_count - 1
        self.display_page()

    def rotate_page(self):
        if not self.doc:
            return
        self.doc[self.current_page].set_rotation((self.doc[self.current_page].rotation + 90) % 360)
        self.display_page()

    def start_text_insert(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        text = self.annotation_text.get()
        if not text:
            messagebox.showerror("Hata", "Lütfen eklemek için bir metin girin!")
            return
        self.text_insert_mode = True
        self.image_move_mode = False
        self.canvas.config(cursor="cross")

    def add_text(self, point):
        page = self.doc[self.current_page]
        page.insert_text(point, self.annotation_text.get(), fontname="Helvetica", fontsize=12)
        self.text_insert_mode = False
        self.canvas.config(cursor="")
        self.display_page()

    def add_image(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        img_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if img_path:
            page = self.doc[self.current_page]
            img_data = open(img_path, "rb").read()
            rect = fitz.Rect(50, 50, 200, 200)
            page.insert_image(rect, stream=img_data)
            # Eklenen resmi kaydet
            if self.current_page not in self.inserted_images:
                self.inserted_images[self.current_page] = []
            self.inserted_images[self.current_page].append((rect, img_data))
            self.display_page()

    def toggle_image_move_mode(self):
        self.image_move_mode = not self.image_move_mode
        self.text_insert_mode = False
        self.canvas.config(cursor="hand2" if self.image_move_mode else "")
        self.selected_image = None
        if self.image_move_mode:
            messagebox.showinfo("Bilgi", "Resim seçmek için bir resme, ardından yeni konuma tıklayın.")

    def handle_canvas_click(self, event):
        if not self.doc:
            return
        # Zoom faktörüne göre koordinatları ölçeklendir
        point = fitz.Point(event.x / self.zoom, event.y / self.zoom)

        if self.text_insert_mode:
            self.add_text(point)
        elif self.image_move_mode:
            if not self.selected_image:
                # Resim seç
                page = self.doc[self.current_page]
                images = page.get_image_info()
                # Orijinal resimleri kontrol et
                for img in images:
                    rect = fitz.Rect(img["bbox"])
                    if rect.contains(point):
                        # Orijinal resim için ham veriyi al
                        xref = img.get("xref")
                        if xref:
                            img_data = self.doc.extract_image(xref)
                            if img_data:
                                self.selected_image = {"bbox": rect, "image": img_data["image"], "xref": xref}
                                messagebox.showinfo("Bilgi", "Resim seçildi, şimdi yeni konuma tıklayın.")
                                break
                # Eklenen resimleri kontrol et
                if not self.selected_image and self.current_page in self.inserted_images:
                    for rect, img_data in self.inserted_images[self.current_page]:
                        if rect.contains(point):
                            self.selected_image = {"bbox": rect, "image": img_data}
                            messagebox.showinfo("Bilgi", "Eklenen resim seçildi, şimdi yeni konuma tıklayın.")
                            break
                if not self.selected_image:
                    messagebox.showerror("Hata", "Seçilen konumda resim bulunamadı!")
            else:
                # Resmi taşı
                page = self.doc[self.current_page]
                new_rect = fitz.Rect(point.x, point.y, point.x + 150, point.y + 150)
                if self.selected_image["image"]:  # Resim verisi varsa
                    page.insert_image(new_rect, stream=self.selected_image["image"])
                    # Eski resmi kaldır
                    if "xref" in self.selected_image and self.selected_image["xref"]:
                        page.delete_image(self.selected_image["xref"])
                    if self.current_page in self.inserted_images:
                        self.inserted_images[self.current_page] = [
                            (r, img) for r, img in self.inserted_images[self.current_page]
                            if r != fitz.Rect(self.selected_image["bbox"])
                        ]
                    # Yeni resmi kaydet
                    if self.current_page not in self.inserted_images:
                        self.inserted_images[self.current_page] = []
                    self.inserted_images[self.current_page].append((new_rect, self.selected_image["image"]))
                    self.selected_image = None
                    self.image_move_mode = False
                    self.canvas.config(cursor="")
                    self.display_page()
                else:
                    messagebox.showerror("Hata", "Resim verisi geçersiz!")
        else:
            annot_type = self.annotation_type.get()
            page = self.doc[self.current_page]
            if annot_type == "text":
                text = self.annotation_text.get()
                if text:
                    page.add_text_annot(point, text)
            elif annot_type == "line":
                page.add_line_annot(point, fitz.Point(point.x + 50, point.y + 50))
            elif annot_type == "rect":
                page.add_rect_annot(fitz.Rect(point, point + (50, 50)))
            elif annot_type == "highlight":
                rect = fitz.Rect(point, point + (100, 20))
                page.add_highlight_annot(rect)
            self.display_page()

    def add_annotation(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        self.canvas.config(cursor="cross")

    def edit_metadata(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        meta_window = tk.Toplevel(self.root)
        meta_window.title("Meta Veri Düzenle")
        meta_window.geometry("400x300")
        
        fields = ["title", "author", "subject", "keywords"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(meta_window, text=field.capitalize()).grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(meta_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, self.meta_data.get(field, ""))
            entries[field] = entry

        def save_metadata():
            for field, entry in entries.items():
                self.meta_data[field] = entry.get()
            self.doc.set_metadata(self.meta_data)
            messagebox.showinfo("Başarılı", "Meta veri güncellendi!")
            meta_window.destroy()

        ttk.Button(meta_window, text="Kaydet", command=save_metadata).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def edit_toc(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        toc_window = tk.Toplevel(self.root)
        toc_window.title("TOC Düzenle")
        toc_window.geometry("600x400")

        toc_text = scrolledtext.ScrolledText(toc_window, height=15)
        toc_text.pack(padx=5, pady=5, fill="both", expand=True)
        toc_text.insert(tk.END, "\n".join([f"{level} | {title} | {page}" for level, title, page in self.toc]))

        def save_toc():
            new_toc = []
            for line in toc_text.get(1.0, tk.END).splitlines():
                try:
                    level, title, page = line.split(" | ")
                    new_toc.append([int(level), title, int(page)])
                except:
                    continue
            self.toc = new_toc
            self.doc.set_toc(new_toc)
            messagebox.showinfo("Başarılı", "TOC güncellendi!")
            toc_window.destroy()

        ttk.Button(toc_window, text="Kaydet", command=save_toc).pack(pady=5)

    def extract_table(self):
        if not self.pdf_path.get():
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        try:
            tables = tabula.read_pdf(self.pdf_path.get(), pages=self.current_page + 1, multiple_tables=True)
            if not tables:
                messagebox.showinfo("Bilgi", "Bu sayfada tablo bulunamadı!")
                return
            output_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if output_path:
                for i, table in enumerate(tables):
                    table.to_csv(f"{output_path[:-4]}_table_{i+1}.csv")
                messagebox.showinfo("Başarılı", "Tablolar CSV olarak kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Tablo çıkarma başarısız: {str(e)}")

    def apply_ocr(self):
        if not self.doc or not convert_from_path:
            messagebox.showerror("Hata", "PDF dosyası açık olmalı ve pdf2image yüklü olmalı!")
            return
        try:
            images = convert_from_path(self.pdf_path.get(), first_page=self.current_page + 1, last_page=self.current_page + 1)
            text = pytesseract.image_to_string(images[0], lang="tur")
            output_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text)
                messagebox.showinfo("Başarılı", "OCR metni kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"OCR işlemi başarısız: {str(e)}")

    def convert_to(self, format_type):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        output_path = filedialog.asksaveasfilename(defaultextension=f".{format_type}", filetypes=[(f"{format_type.upper()} Files", f"*.{format_type}")])
        if output_path:
            if format_type == "text":
                with open(output_path, "w", encoding="utf-8") as f:
                    for page in self.doc:
                        f.write(page.get_text("text") + "\n")
            elif format_type == "html":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(self.doc.get_text("html"))
            elif format_type == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump([page.get_text("dict") for page in self.doc], f, ensure_ascii=False)
            elif format_type == "xml":
                root = ET.Element("pdf")
                for page in self.doc:
                    page_elem = ET.SubElement(root, "page")
                    page_elem.text = page.get_text("text")
                ET.ElementTree(root).write(output_path, encoding="unicode")
            elif format_type == "png":
                for i, page in enumerate(self.doc):
                    pix = page.get_pixmap()
                    pix.save(f"{output_path[:-4]}_page_{i+1}.png")
            messagebox.showinfo("Başarılı", f"Dosya {format_type.upper()} olarak kaydedildi!")

    def save_pdf(self):
        if not self.doc:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası açın!")
            return
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if output_path:
            self.doc.save(output_path)
            messagebox.showinfo("Başarılı", "PDF kaydedildi!")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFEditor(root)
    root.mainloop()