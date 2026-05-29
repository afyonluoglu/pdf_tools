"""
PDF Viewer - Dosya İşlemleri Mixin'i
PDF açma, kaydetme, ayarlar yönetimi
"""

import customtkinter as ctk
import fitz  # PyMuPDF
import os
import json
import threading
from datetime import datetime
from tkinter import filedialog, messagebox


class FileOperationsMixin:
    """Dosya işlemleri metodlarını içeren mixin sınıfı"""
    
    def open_pdf(self):
        """PDF dosyası aç"""
        file_path = filedialog.askopenfilename(
            title="PDF Dosyası Seç",
            filetypes=[("PDF dosyaları", "*.pdf"), ("Tüm dosyalar", "*.*")]
        )
        
        if file_path:
            self.load_pdf_with_progress(file_path)
    
    def load_pdf_with_progress(self, file_path):
        """PDF'yi progress bar ile yükle"""
        from pdf_view_utils import center_window
        
        # Progress window
        progress_window = ctk.CTkToplevel(self.root)
        progress_window.title("PDF Yükleniyor...")
        progress_window.geometry("400x150")
        center_window(progress_window, 400, 150)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Progress widgets
        ctk.CTkLabel(progress_window, text="PDF dosyası yükleniyor...", 
                    font=ctk.CTkFont(size=14)).pack(pady=20)
        
        progress_bar = ctk.CTkProgressBar(progress_window, width=300)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        progress_label = ctk.CTkLabel(progress_window, text="Başlıyor...")
        progress_label.pack(pady=5)
        
        def load_pdf_thread():
            try:
                # PDF belgesini aç
                progress_bar.set(0.1)
                progress_label.configure(text="PDF açılıyor...")
                progress_window.update()
                
                self.pdf_document = fitz.open(file_path)
                self.total_pages = len(self.pdf_document)
                self.current_page = 0
                
                progress_bar.set(0.3)
                progress_label.configure(text="Sayfa bilgileri alınıyor...")
                progress_window.update()
                
                # Küçük resimleri oluştur
                self.create_thumbnails(progress_bar, progress_label, progress_window)
                
                progress_bar.set(0.85)
                progress_label.configure(text="Annotation'lar yükleniyor...")
                progress_window.update()
                
                # ÖNCE eski annotation'ları temizle, SONRA sayfayı çiz (hayalet önleme)
                self.clear_previous_annotations()
                
                # Mevcut annotation'ları JSON sidecar'dan yükle
                self.load_existing_annotations()
                
                progress_bar.set(0.95)
                progress_label.configure(text="Görünüm hazırlanıyor...")
                progress_window.update()
                
                # Sayfayı annotation'larla birlikte göster
                self.display_page()
                self.update_ui()
                
                progress_bar.set(1.0)
                progress_label.configure(text="Tamamlandı!")
                progress_window.update()
                
                self.status_label.configure(text=f"Yüklendi: {os.path.basename(file_path)} ({self.total_pages} sayfa)")
                
                # Progress window'u kapat
                self.root.after(500, progress_window.destroy)
                
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Hata", f"PDF yüklenirken hata oluştu:\n{str(e)}")
        
        # Thread'i başlat
        threading.Thread(target=load_pdf_thread, daemon=True).start()
    
    def save_pdf(self):
        """PDF'yi kaydet - kaydetme yöntemini kullanıcıya sorar"""
        if not self.pdf_document:
            messagebox.showwarning("Uyarı", "Kaydetmek için bir PDF dosyası yükleyin.")
            return

        # Annotation varsa kaydetme yöntemi sor
        has_annotations = (
            hasattr(self, 'annotation_manager') and
            bool(self.annotation_manager.annotations)
        )

        if has_annotations:
            save_mode = self._ask_save_mode()
            if save_mode is None:
                return  # Kullanıcı iptal etti
        else:
            save_mode = "json"  # Annotation yoksa varsayılan

        file_path = filedialog.asksaveasfilename(
            title="PDF'yi Kaydet",
            defaultextension=".pdf",
            filetypes=[("PDF dosyaları", "*.pdf")]
        )

        if not file_path:
            return

        if save_mode == "json":
            self._save_with_json_sidecar(file_path)
        else:
            self._save_with_embedded_annotations(file_path)

    def _ask_save_mode(self):
        """Kaydetme yöntemi seçme diyaloğunu göster. 'json', 'embed' veya None döndürür."""
        from pdf_view_utils import center_window
        import tkinter as tk

        result = {"mode": None}

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Annotation Kaydetme Yöntemi")
        dialog.geometry("520x300")
        center_window(dialog, 520, 300)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Başlık
        ctk.CTkLabel(
            dialog,
            text="Annotation'lar nasıl kaydedilsin?",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(20, 10))

        # Seçenek tutucu
        mode_var = tk.StringVar(value="json")

        # Seçenek 1
        frame1 = ctk.CTkFrame(dialog, fg_color="transparent")
        frame1.pack(fill="x", padx=30, pady=4)
        ctk.CTkRadioButton(
            frame1,
            text="Ayrı dosyada sakla  (.ann.json sidecar)",
            variable=mode_var,
            value="json",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame1,
            text="  Annotation'lar PDF'in yanında ayrı bir .ann.json dosyasında tutulur.\n"
                 "  Bu program bu dosyadan okuyarak annotation'ları gösterir.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
            justify="left"
        ).pack(anchor="w", padx=22)

        # Seçenek 2
        frame2 = ctk.CTkFrame(dialog, fg_color="transparent")
        frame2.pack(fill="x", padx=30, pady=4)
        ctk.CTkRadioButton(
            frame2,
            text="PDF içine göm  (diğer programlarda da görünsün)",
            variable=mode_var,
            value="embed",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame2,
            text="  Annotation'lar standart PDF formatında doğrudan dosyaya işlenir.\n"
                 "  Adobe Reader, Foxit, tarayıcılar gibi tüm PDF okuyucularda görünür.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
            justify="left"
        ).pack(anchor="w", padx=22)

        # Butonlar
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=16)

        def on_ok():
            result["mode"] = mode_var.get()
            dialog.destroy()

        def on_cancel():
            result["mode"] = None
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Kaydet", width=110, command=on_ok).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="İptal", width=110, fg_color="gray40",
                      hover_color="gray30", command=on_cancel).pack(side="left", padx=10)

        dialog.wait_window()
        return result["mode"]

    def _save_with_json_sidecar(self, file_path):
        """PDF'yi kaydet; annotation'ları .ann.json sidecar dosyasına yaz."""
        try:
            self.pdf_document.save(file_path, garbage=4, deflate=True)
            print(f"DEBUG [save_pdf/json]: PDF kaydedildi → {os.path.basename(file_path)}")

            if hasattr(self, 'annotation_manager') and self.annotation_manager.annotations:
                base = os.path.splitext(file_path)[0]
                ann_path = base + '.ann.json'
                anns_to_save = [
                    {k: v for k, v in ann.items() if k != 'canvas_id'}
                    for ann in self.annotation_manager.annotations
                ]
                with open(ann_path, 'w', encoding='utf-8') as f:
                    json.dump(anns_to_save, f, indent=2, ensure_ascii=False)
                print(f"DEBUG [save_pdf/json]: {len(anns_to_save)} annotation sidecar'a yazıldı → {os.path.basename(ann_path)}")
                messagebox.showinfo(
                    "Başarılı",
                    f"PDF kaydedildi:\n{file_path}\n\n"
                    f"Annotation'lar ({len(anns_to_save)} adet) ayrı dosyaya kaydedildi:\n"
                    f"{os.path.basename(ann_path)}"
                )
            else:
                messagebox.showinfo("Başarılı", f"PDF başarıyla kaydedildi:\n{file_path}")

        except Exception as e:
            print(f"DEBUG [save_pdf/json]: HATA → {e}")
            messagebox.showerror("Hata", f"PDF kaydedilirken hata oluştu:\n{str(e)}")

    def _save_with_embedded_annotations(self, file_path):
        """Annotation'ları PDF'e standart PDF annotation olarak göm ve kaydet."""
        import fitz
        try:
            # Çalışmak için PDF'in bir kopyasını aç (orijinal doc değişmesin)
            import tempfile, shutil
            tmp_path = file_path + ".tmp_embed.pdf"
            self.pdf_document.save(tmp_path, garbage=4, deflate=True)
            embed_doc = fitz.open(tmp_path)
            print(f"DEBUG [save_pdf/embed]: Geçici PDF oluşturuldu → {os.path.basename(tmp_path)}")

            annotations = self.annotation_manager.annotations if hasattr(self, 'annotation_manager') else []
            embedded_count = 0

            for ann in annotations:
                try:
                    page_num = ann.get('page', 0)
                    if page_num < 0 or page_num >= len(embed_doc):
                        continue

                    page = embed_doc[page_num]
                    ann_type = ann.get('type', '')

                    if ann_type == 'highlight':
                        coords = ann.get('coordinates', {})
                        if not coords:
                            continue
                        # Canvas koordinatlarını PDF koordinatlarına çevir (zoom'u geri al)
                        zoom = getattr(self, 'zoom_level', 1.0)
                        x1 = coords.get('x1', 0) / zoom
                        y1 = coords.get('y1', 0) / zoom
                        x2 = coords.get('x2', 0) / zoom
                        y2 = coords.get('y2', 0) / zoom
                        rect = fitz.Rect(x1, y1, x2, y2)
                        color_hex = ann.get('color', '#FFFF00')
                        rgb = self._hex_to_rgb_float(color_hex)
                        # Dikdörtgen annotation kullan: Highlight tipi metin vurgulama içindir
                        # ve quad tabanlı olduğundan kenarlar kayabilir. Square/Rect tipi
                        # gerçek dikdörtgen verir ve tüm PDF okuyucularda doğru görünür.
                        annot = page.add_rect_annot(rect)
                        # Doldurma rengi = kenarlık rengi (görünmez kenarlık)
                        annot.set_colors(fill=rgb, stroke=rgb)
                        # Yarı saydamlık: dış PDF okuyucularda orijinal görünüme yakın
                        annot.set_opacity(0.4)
                        annot.update()
                        embedded_count += 1
                        print(f"DEBUG [save_pdf/embed]: Highlight (Rect) eklendi → sayfa {page_num+1}, rect={rect}, renk={color_hex}")

                    elif ann_type == 'note':
                        pos = ann.get('position', {'x': 18, 'y': 18})
                        point = fitz.Point(pos['x'], pos['y'])
                        text = ann.get('text', '')
                        annot = page.add_text_annot(point, text, icon="Note")
                        annot.set_info(title="Not")
                        annot.update()
                        embedded_count += 1
                        print(f"DEBUG [save_pdf/embed]: Not eklendi → sayfa {page_num+1}, nokta={point}, metin='{text[:30]}'")

                    elif ann_type == 'bookmark':
                        pos = ann.get('position', {'x': 18, 'y': 18})
                        point = fitz.Point(pos['x'], pos['y'])
                        text = ann.get('text', 'İşaret')
                        annot = page.add_text_annot(point, text, icon="Star")
                        annot.set_info(title="İşaret")
                        annot.update()
                        embedded_count += 1
                        print(f"DEBUG [save_pdf/embed]: İşaret eklendi → sayfa {page_num+1}, nokta={point}")

                    elif ann_type == 'link':
                        pos = ann.get('position', {'x': 18, 'y': 18})
                        url = ann.get('url', '')
                        text = ann.get('text', '')
                        content = f"{text}\nURL: {url}" if url else text
                        point = fitz.Point(pos['x'], pos['y'])
                        annot = page.add_text_annot(point, content, icon="Key")
                        annot.set_info(title="Bağlantı")
                        annot.update()
                        embedded_count += 1
                        print(f"DEBUG [save_pdf/embed]: Bağlantı eklendi → sayfa {page_num+1}, nokta={point}, url='{url[:40]}'")

                except Exception as ann_err:
                    print(f"DEBUG [save_pdf/embed]: Annotation gömme hatası ({ann.get('type','?')}): {ann_err}")

            embed_doc.save(file_path, garbage=4, deflate=True)
            embed_doc.close()
            os.remove(tmp_path)
            print(f"DEBUG [save_pdf/embed]: {embedded_count} annotation gömüldü → {os.path.basename(file_path)}")

            # Eğer aynı isimli .ann.json sidecar varsa sil:
            # PDF içine gömdük; yoksa yeniden açıldığında çift çizim oluşur.
            base = os.path.splitext(file_path)[0]
            ann_sidecar = base + '.ann.json'
            if os.path.exists(ann_sidecar):
                os.remove(ann_sidecar)
                print(f"DEBUG [save_pdf/embed]: Eski sidecar JSON silindi (çift çizim önlendi) → {os.path.basename(ann_sidecar)}")
            messagebox.showinfo(
                "Başarılı",
                f"PDF başarıyla kaydedildi:\n{file_path}\n\n"
                f"{embedded_count} annotation PDF içine gömüldü.\n"
                f"Diğer PDF okuyucularda da görünecektir."
            )

        except Exception as e:
            print(f"DEBUG [save_pdf/embed]: GENEL HATA → {e}")
            # Geçici dosyayı temizle
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            messagebox.showerror("Hata", f"PDF kaydedilirken hata oluştu:\n{str(e)}")

    @staticmethod
    def _hex_to_rgb_float(hex_color):
        """'#RRGGBB' formatındaki rengi (r, g, b) float tuple'ına çevir (0.0-1.0)."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        return (1.0, 1.0, 0.0)  # varsayılan sarı
    
    def load_settings(self):
        """Ayarları yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.highlight_color = settings.get('highlight_color', '#FFFF00')
                    self.zoom_level = settings.get('zoom_level', 1.0)
        except Exception:
            pass
    
    def save_settings(self):
        """Ayarları kaydet"""
        try:
            settings = {
                'highlight_color': self.highlight_color,
                'zoom_level': self.zoom_level,
                'last_opened': datetime.now().isoformat()
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def on_closing(self):
        """Program kapanırken"""
        try:
            # print("Program kapatılıyor...")
            
            # Ayarları kaydet
            self.save_settings()
            
            # Tooltip'i temizle
            if hasattr(self, 'tooltip_window') and self.tooltip_window:
                try:
                    self.tooltip_window.destroy()
                except:
                    pass
            
            # PDF dokümanını kapat
            if self.pdf_document:
                try:
                    self.pdf_document.close()
                except:
                    pass
            
            # Annotation manager'ı temizle
            if hasattr(self, 'annotation_manager'):
                try:
                    if hasattr(self.annotation_manager, 'window') and self.annotation_manager.window.winfo_exists():
                        self.annotation_manager.safe_close_window()
                except:
                    pass
            
            # Ana pencereyi kapat
            self.root.quit()
            self.root.destroy()
            
            # print("Program başarıyla kapatıldı.")
            
        except Exception as e:
            print(f"Program kapatma hatası: {e}")
            # Force close
            try:
                self.root.quit()
            except:
                pass
    
    def load_existing_annotations(self):
        """PDF ile aynı klasördeki JSON sidecar dosyasından annotation'ları yükle"""
        if not self.pdf_document:
            return
            
        try:
            pdf_path = self.pdf_document.name
            if not pdf_path:
                return
            
            base = os.path.splitext(pdf_path)[0]
            ann_path = base + '.ann.json'
            
            if os.path.exists(ann_path):
                with open(ann_path, 'r', encoding='utf-8') as f:
                    annotations = json.load(f)
                
                for ann in annotations:
                    ann.pop('canvas_id', None)  # Eski canvas ID'leri temizle
                    self.annotation_manager.add_annotation(ann)
                
                # print(f"DEBUG: {len(annotations)} annotation JSON'dan yüklendi: {os.path.basename(ann_path)}")
            else:
                # print(f"DEBUG: Sidecar bulunamadı, annotation yok: {os.path.basename(pdf_path)}")
                pass
                
        except Exception as e:
            print(f"Annotation yükleme hatası: {e}")
