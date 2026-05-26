# PDF Viewer Modüller Dokümantasyonu

Bu dosya, `professional_pdf_viewer.py` dosyasının modüler parçalara ayrılmış yapısını açıklar.

## Modül Yapısı

```
PDF Tools/
├── pdf_view_main.py          # Ana giriş noktası
├── pdf_view_utils.py         # Yardımcı fonksiyonlar
├── pdf_view_ui_setup.py      # UI kurulum mixin
├── pdf_view_navigation.py    # Sayfa navigasyonu mixin
├── pdf_view_display.py       # Sayfa görüntüleme mixin
├── pdf_view_annotations.py   # Annotasyon işlemleri mixin
├── pdf_view_search.py        # Metin arama mixin
├── pdf_view_file_ops.py      # Dosya işlemleri mixin
├── pdf_view_text_extraction.py # Metin çıkarma mixin
├── pdf_view_text_editor.py   # Profesyonel metin editörü
├── pdf_view_tts.py           # Türkçe TTS modülü
└── PDF_viewer_modules.md     # Bu dosya
```

---

## 1. pdf_view_main.py (Ana Giriş)

**Amaç:** Tüm mixin sınıfları birleştirerek `PDFViewer` sınıfını oluşturur.

**Sınıflar:**
- `PDFViewer` - Ana uygulama sınıfı (tüm mixin'leri miras alır)
- `AdvancedAnnotationWindow` - Gelişmiş annotation penceresi

**Fonksiyonlar:**
- `main()` - Program giriş noktası

**Kullanım:**
```python
python pdf_view_main.py
```

---

## 2. pdf_view_utils.py (Yardımcı Fonksiyonlar)

**Amaç:** Global yardımcı fonksiyonlar ve hata yönetimi.

**Fonksiyonlar:**
| Fonksiyon | Açıklama |
|-----------|----------|
| `handle_exception(exc_type, exc_value, exc_traceback)` | Global exception handler |
| `setup_global_exception_handler()` | Exception handler'ı sisteme kaydet |
| `init_error_log()` | Hata log dosyasını başlat |
| `center_window(window, width, height)` | Pencereyi ekran ortasına yerleştir |

---

## 3. pdf_view_ui_setup.py (UI Kurulum)

**Amaç:** Kullanıcı arayüzü elemanlarının kurulumu.

**Sınıf:** `UISetupMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `setup_ui()` | Ana UI yapısını kurulu |
| `setup_toolbar()` | Araç çubuğunu oluştur |
| `setup_canvas()` | PDF canvas ve scroll bölgesini oluştur |
| `setup_canvas_tooltips()` | Canvas tooltip event'lerini bağla |
| `setup_keybindings()` | Klavye kısayollarını tanımla |
| `update_ui()` | UI elemanlarını güncelle |

---

## 4. pdf_view_navigation.py (Sayfa Navigasyonu)

**Amaç:** PDF sayfaları arasında gezinme ve zoom işlemleri.

**Sınıf:** `NavigationMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `previous_page()` | Önceki sayfaya git |
| `next_page()` | Sonraki sayfaya git |
| `goto_page(event=None)` | Belirli sayfaya git |
| `zoom_in()` | Yakınlaştır (+25%) |
| `zoom_out()` | Uzaklaştır (-25%) |
| `reset_zoom()` | Zoom'u sıfırla (100%) |
| `rotate_page()` | Sayfayı 90° döndür |

**Klavye Kısayolları:**
- `Left/Up Arrow` veya `Page Up`: Önceki sayfa
- `Right/Down Arrow` veya `Page Down`: Sonraki sayfa
- `Ctrl++`: Yakınlaştır
- `Ctrl+-`: Uzaklaştır
- `Ctrl+0`: Zoom sıfırla

---

## 5. pdf_view_display.py (Sayfa Görüntüleme)

**Amaç:** PDF sayfalarını ve thumbnail'leri görüntüleme.

**Sınıf:** `DisplayMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `create_thumbnails()` | Sol panelde sayfa thumbnail'leri oluştur |
| `display_page()` | Mevcut sayfayı canvas'ta göster |
| `show_highlights()` | Arama sonuçlarını vurgula |
| `load_pdf_annotations()` | PDF'deki native annotation'ları yükle |
| `clear_previous_annotations()` | Mevcut annotation görsellerini temizle |

---

## 6. pdf_view_annotations.py (Annotasyon İşlemleri)

**Amaç:** Tooltip, not ekleme, yer imi ve link işlemleri.

**Sınıf:** `AnnotationMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `on_canvas_motion(event)` | Mouse hareket event handler |
| `show_tooltip(text, x, y)` | Tooltip göster |
| `hide_tooltip()` | Tooltip gizle |
| `on_canvas_double_click(event)` | Çift tıklama ile link açma |
| `toggle_highlight_mode()` | Vurgulama modunu aç/kapat |
| `on_highlight_start(event)` | Vurgulama başla |
| `on_highlight_drag(event)` | Vurgulama sürükle |
| `on_highlight_end(event)` | Vurgulama bitir |
| `show_color_picker()` | Renk seçici dialog |
| `add_bookmark()` | Mevcut sayfaya yer imi ekle |
| `show_bookmarks()` | Yer imleri penceresini aç |
| `goto_bookmark(page_num)` | Yer imine git |
| `show_advanced_annotations()` | Gelişmiş annotation penceresini aç |

---

## 7. pdf_view_search.py (Metin Arama)

**Amaç:** PDF içinde metin arama ve sonuçlar arasında gezinme.

**Sınıf:** `SearchMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `search_text()` | Arama başlat, sonuçları topla |
| `search_next()` | Sonraki arama sonucuna git |
| `show_search_result()` | Mevcut arama sonucunu göster ve vurgula |

**Klavye Kısayolları:**
- `Ctrl+F`: Arama kutusuna odaklan
- `Enter` (arama kutusunda): Aramayı başlat
- `F3`: Sonraki sonuç

---

## 8. pdf_view_file_ops.py (Dosya İşlemleri)

**Amaç:** PDF açma/kaydetme ve uygulama ayarları yönetimi.

**Sınıf:** `FileOperationsMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `open_pdf()` | Dosya seçici ile PDF aç |
| `load_pdf_with_progress(file_path)` | Progress bar ile PDF yükle |
| `save_pdf()` | PDF'yi kaydet (annotation'larla birlikte) |
| `load_settings()` | Uygulama ayarlarını yükle |
| `save_settings()` | Uygulama ayarlarını kaydet |
| `on_closing()` | Uygulama kapanırken temizlik |
| `load_existing_annotations()` | Kaydedilmiş annotation'ları yükle |

**Ayarlar:**
- Son açılan dosya yolu
- Son sayfa konumu
- Zoom seviyesi
- Yer imleri

---

## 9. pdf_view_text_extraction.py (Metin Çıkarma)

**Amaç:** PDF'den metin çıkarma ve editöre aktarma.

**Sınıf:** `TextExtractionMixin`

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `extract_text_to_file()` | Sayfa aralığı dialog'unu göster |
| `show_page_range_dialog()` | Sayfa aralığı seçim penceresi |
| `start_text_extraction(start_page, end_page, dialog)` | Metin çıkarmayı başlat |
| `open_text_editor(text, start_page, end_page)` | Profesyonel text editörü aç |

---

## 10. pdf_view_text_editor.py (Profesyonel Metin Editörü)

**Amaç:** PDF'den çıkarılan metni düzenleme, kaydetme ve seslendirme.

**Sınıf:** `ProfessionalTextEditor`

**Özellikler:**
- Satır numaraları
- Bul/Değiştir
- Geri Al/Yinele (undo/redo)
- Büyük/küçük harf dönüştürme
- Boş satır temizleme
- Türkçe seslendirme (TTS)

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `setup_ui()` | Editör arayüzünü oluştur |
| `setup_keybindings()` | Klavye kısayolları |
| `update_line_numbers()` | Satır numaralarını güncelle |
| `update_status()` | Karakter/kelime/satır sayısı |
| `speak_text()` | Seçili veya tüm metni seslendir |
| `stop_speech()` | Seslendirmeyi durdur |
| `save_text()` | Dosyaya kaydet |
| `copy_all()` | Panoya kopyala |
| `undo()` / `redo()` | Geri al / Yinele |
| `to_uppercase()` / `to_lowercase()` | Harf dönüştürme |
| `remove_empty_lines()` | Boş satırları temizle |
| `find_text()` | Metinde ara |
| `find_next()` / `find_prev()` | Sonraki/önceki sonuç |
| `replace_current()` / `replace_all()` | Değiştir |

**Klavye Kısayolları:**
- `Ctrl+S`: Kaydet
- `Ctrl+Z`: Geri al
- `Ctrl+Y`: Yinele
- `Ctrl+F`: Bul
- `Ctrl+H`: Değiştir
- `Ctrl+A`: Tümünü seç
- `F3`: Sonraki sonuç
- `F5`: Seslendir
- `Escape`: Seslendirmeyi durdur

---

## 11. pdf_view_tts.py (Türkçe TTS Modülü)

**Amaç:** Türkçe metin seslendirme (Text-to-Speech).

**Sınıf:** `TTSManager`

**Gerekli Paketler:**
```bash
pip install edge-tts pygame
```

**Türkçe Sesler:**
| Ses Adı | Voice ID |
|---------|----------|
| Emel (Kadın) | tr-TR-EmelNeural |
| Ahmet (Erkek) | tr-TR-AhmetNeural |

**Hız Ayarları:**
| Ayar | Rate |
|------|------|
| Yavaş | -20% |
| Normal | +0% |
| Hızlı | +25% |

**Metodlar:**
| Metod | Açıklama |
|-------|----------|
| `speak(text, voice, speed, callback)` | Metni seslendir |
| `stop()` | Seslendirmeyi durdur |
| `_generate_and_play()` | Ses dosyası oluştur ve oynat |
| `_play_with_pygame()` | Pygame ile oynat |
| `_play_with_playsound()` | Playsound ile oynat |
| `_cleanup_temp()` | Geçici dosyaları temizle |

---

## Bağımlılıklar

**Temel:**
```bash
pip install customtkinter PyMuPDF Pillow
```

**TTS için (opsiyonel):**
```bash
pip install edge-tts pygame
```

---

## Mixin Mimarisi

Proje, Python'un çoklu kalıtım (multiple inheritance) özelliğini kullanarak Mixin pattern'i uygular:

```python
class PDFViewer(
    UISetupMixin,
    NavigationMixin,
    DisplayMixin,
    AnnotationMixin,
    SearchMixin,
    FileOperationsMixin,
    TextExtractionMixin
):
    pass
```

Her mixin sınıfı belirli bir işlevselliği kapsüller ve `PDFViewer` sınıfı bunların tamamını miras alır.

---

## Oluşturulma Tarihi

Bu modüler yapı, 2025 yılında büyüyen `professional_pdf_viewer.py` dosyasını (~1931 satır) yönetilebilir parçalara ayırmak için oluşturulmuştur.
