# PDF Viewer & Düzenleyici — Metod ve Mimari Dokümantasyonu

Bu doküman, PDF Tools projesindeki tüm Python modüllerinin mimarisini, veri modellerini, sınıflarını, metotlarını ve bağımsız fonksiyonlarını detaylandırmaktadır.

## 1. Mimari Genel Bakış
PDF Tools, PyMuPDF (fitz) ve CustomTkinter tabanlı, sayfa içi vektörel kutu ve metin düzenleme (In-Page Editing), damlalık renk örnekleme, font çözümleme, annotasyon yönetimi ve metin seslendirme (TTS) yeteneklerine sahip profesyonel bir PDF araç setidir.

* **Mimari Desen (Mixin Tabanlı Modüler Mimari):**
  Ana pencere sınıfı olan `PDFViewer` (`pdf_view_main.py`), sorumlulukları mantıksal Mixin sınıflarından devralarak monolitik yapıyı modüler bileşenlere böler:
  * `UIComponentsMixin`: Menü, toolbar, sol thumbnail paneli, canvas ve durum çubuğu bileşenlerini inşa eder.
  * `NavigationMixin`: Sayfa geçişleri, dinamik yakınlaştırma (zoom), sayfa döndürme (rotation) ve klavye gezintisini koordine eder.
  * `DisplayMixin`: PyMuPDF render motoru ile sayfaları yüksek çözünürlükte piksel yüzeyine dönüştürür ve canvas çizimlerini yönetir.
  * `AnnotationMixin`: Vurgulama (highlight), serbest çizim, metin notları, damgalar ve etkileşimli annotasyon katmanını yönetir.
  * `SearchMixin`: Büyük/küçük harf duyarsız metin arama, regex eşleştirme ve arama sonuçlarını canvas üzerinde görsel çerçeveleme işlemlerini yürütür.
  * `FileOperationsMixin`: PDF açma, arka planda aşamalı yükleme, annotasyonlarla birlikte güvenli kaydetme ve son dosyalar geçmişini saklar.
  * `TextExtractionMixin`: Sayfadan seçili veya tüm metni yapısal olarak ayıklar.
  * `TextEditorMixin`: PDF metinlerini harici metin düzenleyicide açıp düzenleme süreçlerini koordine eder.
  * `TTSMixin`: `pyttsx3` motorunu kullanarak PDF sayfasındaki metinleri Türkçe veya İngilizce ses profilleriyle sesli okur.
  * `QuickAccessMixin`: F2 kısayolu ile açılan hızlı erişim paneli üzerinden annotasyonlara tek tıklamayla gitmeyi sağlar.

* **Sayfa İçi Vektörel ve Metin Düzenleme (In-Page Editing):**
  * `FontResolver`: Windows Kayıt Defteri, AppData ve PDF `FontDescriptor` nesneleri arasında akıllı font çözümlemesi ve önbelleklemesi sağlar.
  * `InPageTextEngine`: Sayfa içi metin ayıklama, koordinat dönüşümü, piksel renk örnekleme, redaction ve font gömerek metin yerleştirme motorudur.
  * `InPageTextEditor`: Canvas üzerinde fare olayları, metin seçimi, sürükle-bırak ve ok tuşlarıyla (nudge) metin taşıma kontrolcüsüdür.
  * `InPageEditDialog`: Damlalık, font seçimi, arka plan dolgusu ve canlı tipografi modal penceresidir.

* **Vektörel Arka Plan Kutuları & Senkronizasyon:**
  * `VectorBoxManager` & `VectorBoxDialog`: PDF sayfaları üzerine yeniden boyutlandırılabilir, renkli, transparan ve kalıcı olarak gömülebilir (bake) vektörel kutular ekler.
  * `pd_annot_sync.py`: Gömülü PDF annotasyonları ile JSON annotasyon modelleri arasında çift yönlü senkronizasyonu sağlar.

## 2. Klavye Kısayolları ve Etkileşimler
Aşağıdaki tabloda uygulamadaki klavye kısayolları ve fare etkileşimleri listelenmiştir:

| Kısayol / Etkileşim | İşlev |
| :--- | :--- |
| `Ctrl + O` | PDF belgesi açmak için dosya gezginini açar. |
| `Ctrl + S` | Annotasyonlar ve düzenlemelerle birlikte PDF belgesini kaydeder. |
| `Ctrl + E` | Seçili veya tüm metni harici düzenleyiciye aktarır. |
| `Ctrl + F` | PDF içi metin arama çubuğunu odaklar. |
| `Ctrl + T` | Metin seslendirme (TTS - Text-to-Speech) panelini açar/kapatır. |
| `Ctrl + +` / `Ctrl + -` | Sayfayı yakınlaştırır (%10 - %500) veya uzaklaştırır. |
| `Ctrl + 0` | Yakınlaştırmayı sıfırlar (Varsayılan %100 ölçeğe döner). |
| `Ctrl + Mouse Wheel` | İmlecin bulunduğu noktaya doğru akıcı yakınlaştırma/uzaklaştırma yapar. |
| `F2` | Hızlı Erişim ve Annotasyon Yönetim Paneli'ni açar. |
| `Sağ Ok / Page Down` | Bir sonraki sayfaya geçer. |
| `Sol Ok / Page Up` | Bir önceki sayfaya geçer. |
| `Home` / `End` | İlk sayfaya veya son sayfaya gider. |
| `R` | Sayfayı saat yönünde 90 derece döndürür. |
| `H` | Metin vurgulama (Highlight) modunu açar/kapatır. |
| `I` | Sayfa içi metin düzenleme (In-Page Text Edit) aracını açar. |
| `V` | Vektörel arka plan kutusu çizim aracını açar. |
| `Ok Tuşları (In-Page)` | Seçili metin veya vektörel kutuyu 0.5pt hassasiyetle kaydırır (Nudge). |
| `Çift Tıklama (Canvas)` | Seçili metin veya kutunun gelişmiş özellikler diyaloğunu açar. |
| `Sürükle & Bırak` | PDF dosyasını pencereye sürükleyerek anında açma veya metin kutusunu yeni yerine taşıma. |

## 3. Veritabanı ve Şema Yapısı
Uygulama, verilerini yerel dosya sisteminde JSON dosyaları ve Windows Font Kayıt Defteri indeksleri üzerinden yönetir:

* **Yapılandırma Dosyası (`pdf_viewer_settings.json`):**
  * `last_opened_file`: En son açılan PDF belgesinin mutlak dosya yolu.
  * `zoom_level`: Son oturumda kullanılan yakınlaştırma katsayısı (float).
  * `theme`: Arayüz teması tercihi ('dark' veya 'light').
  * `tts_settings`: Ses kimliği (voice), konuşma hızı (speed) ve ses düzeyi ayarları.
  * `recent_files`: En son açılan 10 PDF dosyasının dosya yolları ve erişim zaman damgaları.
  * `annotation_colors`: Kullanıcının en son seçtiği veya özelleştirdiği Hex renk paleti listesi.

* **Annotasyon Veri Modeli (Annotation JSON Schema):**
  * `type`: Annotasyon türü ('highlight', 'note', 'link', 'vector_box', 'drawing').
  * `page`: Sayfa indeksi (0 tabanlı tamsayı).
  * `rect`: `[x0, y0, x1, y1]` koordinat dizisi (nokta cinsinden).
  * `color`: Hex formatında renk kodu (örn: '#FFEB3B').
  * `content`: Not metni, etiket veya köprü URL bağlantısı.
  * `created_at` / `modified_at`: Oluşturulma ve güncellenme zaman damgaları.

* **Font Çözümleme ve Önbellek Modeli (`FontResolver`):**
  * Windows Kayıt Defteri (`HKLM/HKCU`) ve `%LOCALAPPDATA%\Microsoft\Windows\Fonts` dizinlerinden taranan sistem yazı tipi haritası (`family -> {regular, bold, italic, bold_italic}`).

## MODÜL VE YÖNTEM DETAYLARI

### __pdf_tools_grok3.py

**Modül Tanımı:** Deneysel bağımsız PDF düzenleme, tablo ayıklama ve OCR araçları prototip modülü.

#### `PDFEditor` (Sınıf)

PyMuPDF ve Tkinter tabanlı deneysel bağımsız PDF düzenleyici ve araçlar penceresi sınıfıdır.

  * **`__init__(self, root)`**
    * **İşlevi:** Deneysel PDF düzenleyici penceresini ve arayüz bileşenlerini ilklendirir.
    * **Parametreler:**
      * `root`: Tkinter ana (root) pencere nesnesi referansı.

  * **`create_menu(self)`**
    * **İşlevi:** create_menu işlemini gerçekleştirir.

  * **`show_help(self)`**
    * **İşlevi:** show_help işlemini gerçekleştirir.

  * **`open_pdf(self)`**
    * **İşlevi:** open_pdf işlemini gerçekleştirir.

  * **`display_page(self)`**
    * **İşlevi:** display_page işlemini gerçekleştirir.

  * **`prev_page(self)`**
    * **İşlevi:** prev_page işlemini gerçekleştirir.

  * **`next_page(self)`**
    * **İşlevi:** next_page işlemini gerçekleştirir.

  * **`apply_zoom(self)`**
    * **İşlevi:** apply_zoom işlemini gerçekleştirir.

  * **`resize_canvas(self, event)`**
    * **İşlevi:** resize_canvas işlemini gerçekleştirir.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`add_page(self)`**
    * **İşlevi:** add_page işlemini gerçekleştirir.

  * **`delete_page(self)`**
    * **İşlevi:** delete_page işlemini gerçekleştirir.

  * **`rotate_page(self)`**
    * **İşlevi:** rotate_page işlemini gerçekleştirir.

  * **`start_text_insert(self)`**
    * **İşlevi:** start_text_insert işlemini gerçekleştirir.

  * **`add_text(self, point)`**
    * **İşlevi:** add_text işlemini gerçekleştirir.
    * **Parametreler:**
      * `point`: point parametre değeri.

  * **`add_image(self)`**
    * **İşlevi:** add_image işlemini gerçekleştirir.

  * **`toggle_image_move_mode(self)`**
    * **İşlevi:** toggle_image_move_mode işlemini gerçekleştirir.

  * **`handle_canvas_click(self, event)`**
    * **İşlevi:** handle_canvas_click işlemini gerçekleştirir.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`add_annotation(self)`**
    * **İşlevi:** add_annotation işlemini gerçekleştirir.

  * **`edit_metadata(self)`**
    * **İşlevi:** edit_metadata işlemini gerçekleştirir.

  * **`edit_toc(self)`**
    * **İşlevi:** edit_toc işlemini gerçekleştirir.

  * **`extract_table(self)`**
    * **İşlevi:** extract_table işlemini gerçekleştirir.

  * **`apply_ocr(self)`**
    * **İşlevi:** apply_ocr işlemini gerçekleştirir.

  * **`convert_to(self, format_type)`**
    * **İşlevi:** convert_to işlemini gerçekleştirir.
    * **Parametreler:**
      * `format_type`: format_type parametre değeri.

  * **`save_pdf(self)`**
    * **İşlevi:** save_pdf işlemini gerçekleştirir.

---

### annotation_manager_fixed.py

**Modül Tanımı:** Geriye dönük uyumluluk shim modülü. Eski importları yönlendirir.

---

---

---

---

### pd_annot_sync.py

**Modül Tanımı:** PDF Viewer - Gömülü Annotation Senkronizasyonu (pd_annot_sync.py).

#### Bağımsız Fonksiyonlar

* **`hex_from_color(color_list)`**
  * **İşlevi:** PyMuPDF float RGB listesini (#RRGGBB) hex formatına çevirir.
  * **Parametreler:**
    * `color_list`: color_list parametre değeri.

* **`hex_to_rgb_float(color_hex)`**
  * **İşlevi:** Hex renk kodunu ([r, g, b]) 0.0-1.0 float listesine çevirir.
  * **Parametreler:**
    * `color_hex`: Onaltılık (Hex) renk kodu dizesi.

* **`calculate_canvas_coords(pdf_rect, zoom_level, rotation)`**
  * **İşlevi:** PDF rect koordinatlarını (PDF points) mevcut zoom ve rotasyona göre canvas koordinatlarına çevirir.
  * **Parametreler:**
    * `pdf_rect`: pdf_rect parametre değeri.
    * `zoom_level`: zoom_level parametre değeri.
    * `rotation`: rotation parametre değeri.

* **`canvas_to_pdf_rect(cx1, cy1, cx2, cy2, zoom_level, rotation)`**
  * **İşlevi:** Canvas koordinatlarını PDF rect koordinatlarına (PDF points) çevirir.
  * **Parametreler:**
    * `cx1`: cx1 parametre değeri.
    * `cy1`: cy1 parametre değeri.
    * `cx2`: cx2 parametre değeri.
    * `cy2`: cy2 parametre değeri.
    * `zoom_level`: zoom_level parametre değeri.
    * `rotation`: rotation parametre değeri.

* **`load_embedded_annotations(pdf_document)`**
  * **İşlevi:** PDF belgesindeki gömülü tüm annotation'ları (Square, Highlight, Text vb.).
  * **Parametreler:**
    * `pdf_document`: Yüklü PDF belge nesnesi.

* **`sync_update_rect(pdf_document, ann, cx1, cy1, cx2, cy2, zoom_level, rotation)`**
  * **İşlevi:** Annotation canvas üzerinde taşındığında veya yeniden boyutlandırıldığında PDF koordinatlarını ve PyMuPDF belgesini günceller.
  * **Parametreler:**
    * `pdf_document`: Yüklü PDF belge nesnesi.
    * `ann`: ann parametre değeri.
    * `cx1`: cx1 parametre değeri.
    * `cy1`: cy1 parametre değeri.
    * `cx2`: cx2 parametre değeri.
    * `cy2`: cy2 parametre değeri.
    * `zoom_level`: zoom_level parametre değeri.
    * `rotation`: rotation parametre değeri.

* **`sync_delete_annotation(pdf_document, ann)`**
  * **İşlevi:** Annotation silindiğinde PDF belgesindeki karşılık gelen yerel annot'ı siler.
  * **Parametreler:**
    * `pdf_document`: Yüklü PDF belge nesnesi.
    * `ann`: ann parametre değeri.

* **`sync_update_color(pdf_document, ann, new_color_hex)`**
  * **İşlevi:** Annotation rengi değiştiğinde hem veri yapısını hem PDF'teki nesneyi günceller.
  * **Parametreler:**
    * `pdf_document`: Yüklü PDF belge nesnesi.
    * `ann`: ann parametre değeri.
    * `new_color_hex`: new_color_hex parametre değeri.

---

### pd_font_resolver.py

**Modül Tanımı:** Windows Registry, AppData ve PDF FontDescriptor nesneleri arasında akıllı font eşleştirme motoru modülü.

#### `FontResolver` (Sınıf)

Windows Registry, AppData ve PDF FontDescriptor nesneleri arasında akıllı font çözümlemesi ve önbelleklemesi sağlayan çekirdek motor sınıfıdır.

  * **`__new__(cls, *args, **kwargs)`**
    * **İşlevi:** Tekil (Singleton) desen - Font önbelleği tek bir defa taranır.
    * **Parametreler:**
      * `args`: Fonksiyona aktarılan ek konfigürasyon argümanları demeti.
      * `kwargs`: Üst sınıfa veya alt bileşene aktarılacak ek anahtar-değer parametreleri.

  * **`__init__(self)`**
    * **İşlevi:** Tekil (Singleton) desende font önbelleğini ve Registry indeksini başlatır.

  * **`_scan_fonts(self)`**
    * **İşlevi:** Windows Kayıt Defteri ve kullanıcı font dizinlerini tarar.

  * **`_register_font_entry(self, raw_name, file_path)`**
    * **İşlevi:** Tek bir font kaydını stil ayrıştırması yaparak önbelleğe işler.
    * **Parametreler:**
      * `raw_name`: raw_name parametre değeri.
      * `file_path`: İşlem yapılacak veya açılacak dosyanın mutlak dosya yolu.

  * **`get_available_font_names(self)`**
    * **İşlevi:** Kullanıcı arayüzü açılır menüsü için sistemde yüklü tüm font ailelerini döndürür.

  * **`resolve_font_from_pdf(self, doc, page, span_font_name)`**
    * **İşlevi:** PDF sayfasından okunan font ismini (Type3 veya gömülü subset olsa bile).
    * **Parametreler:**
      * `doc`: PyMuPDF fitz.Document belge örneği referansı.
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `span_font_name`: span_font_name parametre değeri.

  * **`resolve_file_for_family(self, family_name, is_bold, is_italic)`**
    * **İşlevi:** Verilen font ailesi ve stil için sistemdeki en uygun .ttf/.otf dosya yolunu bulur.
    * **Parametreler:**
      * `family_name`: family_name parametre değeri.
      * `is_bold`: is_bold parametre değeri.
      * `is_italic`: is_italic parametre değeri.

---

### pd_inpage_edit_dialog.py

**Modül Tanımı:** Damlalık, font seçimi ve tipografi modal diyalog modülü.

#### `InPageEditDialog` (Sınıf)

Gelişmiş metin düzenleme, tipografi, font seçimi, damlalık ve canlı önizleme modal pencere sınıfıdır.

  * **`__init__(self, parent, page_num, rect_coords, initial_text, style_info, on_apply, on_pick_color_request)`**
    * **İşlevi:** Tipografi ve font düzenleme modal penceresini ve damlalık araçlarını ilklendirir.
    * **Parametreler:**
      * `parent`: Üst pencere veya taşıyıcı arayüz bileşeni referansı.
      * `page_num`: İşlem yapılan sayfanın numarası veya indeksi.
      * `rect_coords`: rect_coords parametre değeri.
      * `initial_text`: initial_text parametre değeri.
      * `style_info`: style_info parametre değeri.
      * `on_apply`: on_apply parametre değeri.
      * `on_pick_color_request`: on_pick_color_request parametre değeri.

  * **`_setup_window(self)`**
    * **İşlevi:** Pencere genel ayarları.

  * **`_build_ui(self)`**
    * **İşlevi:** Tüm arayüz bileşenlerini oluşturur.

  * **`_match_initial_font(self)`**
    * **İşlevi:** PDF'den okunan orijinal font ismini mevcut sistem fontlarıyla eşleştirir.

  * **`_on_font_changed(self)`**
    * **İşlevi:** _on_font_changed işlemini gerçekleştirir.

  * **`_pick_custom_font(self)`**
    * **İşlevi:** Harici bir .ttf / .otf dosyası seçtirir.

  * **`_pick_text_color(self)`**
    * **İşlevi:** _pick_text_color işlemini gerçekleştirir.

  * **`_pick_bg_color(self)`**
    * **İşlevi:** _pick_bg_color işlemini gerçekleştirir.

  * **`set_sampled_bg_color(self, hex_color)`**
    * **İşlevi:** Damlalık tarafından örneklenen rengi uygular.
    * **Parametreler:**
      * `hex_color`: Atanacak veya seçilen Hex renk kodu.

  * **`_trigger_eyedropper(self)`**
    * **İşlevi:** Kullanıcının canvas üzerinden renk seçmesi için damlalık modunu başlatır.

  * **`_on_align_changed(self, value)`**
    * **İşlevi:** _on_align_changed işlemini gerçekleştirir.
    * **Parametreler:**
      * `value`: Atanacak veya güncellenecek özellik değeri.

  * **`_on_text_modified(self)`**
    * **İşlevi:** _on_text_modified işlemini gerçekleştirir.

  * **`_on_preview_click(self, event)`**
    * **İşlevi:** Önizleme kutusuna tek tıklandığında (250ms gecikmeyle) beyaz/siyah geçişi yapar.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_toggle_preview_bg(self)`**
    * **İşlevi:** Önizleme kutusu arka planını beyaz ve siyah arasında değiştirir.

  * **`_on_preview_double_click(self, event)`**
    * **İşlevi:** Önizleme kutusuna çift tıklandığında özel renk seçme penceresini açar.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_case_upper(self)`**
    * **İşlevi:** _case_upper işlemini gerçekleştirir.

  * **`_case_lower(self)`**
    * **İşlevi:** _case_lower işlemini gerçekleştirir.

  * **`_case_title(self)`**
    * **İşlevi:** _case_title işlemini gerçekleştirir.

  * **`_resolve_font_file(self)`**
    * **İşlevi:** Kullanılan fontun fiziksel disk yolunu döndürür.

  * **`_update_preview(self)`**
    * **İşlevi:** Dialog içindeki canlı önizleme alanını günceller.

  * **`_apply(self)`**
    * **İşlevi:** Kullanıcının girdiği değişiklikleri doğrular ve onaylar.

  * **`_nudge(self, dx, dy)`**
    * **İşlevi:** _nudge işlemini gerçekleştirir.
    * **Parametreler:**
      * `dx`: dx parametre değeri.
      * `dy`: dy parametre değeri.

  * **`_reset_offset(self)`**
    * **İşlevi:** _reset_offset işlemini gerçekleştirir.

  * **`update_offset_display(self, ox, oy)`**
    * **İşlevi:** Tuvalden veya butonlardan gelen ofset bilgisini etiketlerde günceller.
    * **Parametreler:**
      * `ox`: ox parametre değeri.
      * `oy`: oy parametre değeri.

  * **`_cancel(self)`**
    * **İşlevi:** İptal edildiğinde seçim çizgilerini temizler ve pencereyi kapatır.

  * **`destroy(self)`**
    * **İşlevi:** destroy işlemini gerçekleştirir.

---

### pd_inpage_engine.py

**Modül Tanımı:** Sayfa içi redaction, koordinat dönüşümü ve taban çizgisi kilitli metin yazma motoru modülü.

#### `InPageTextEngine` (Sınıf)

Sayfa içi metin ayıklama, koordinat dönüşümü, piksel renk örnekleme, redaction ve font gömerek metin yerleştirme motor sınıfıdır.

  * **`__init__(self, pdf_viewer, on_clear_visuals)`**
    * **İşlevi:** Sayfa içi metin ayıklama, koordinat dönüşümü ve redaction motorunu ilklendirir.
    * **Parametreler:**
      * `pdf_viewer`: pdf_viewer parametre değeri.
      * `on_clear_visuals`: on_clear_visuals parametre değeri.

  * **`canvas_to_pdf_rect(self, cx1, cy1, cx2, cy2)`**
    * **İşlevi:** Canvas koordinatlarını mevcut Zoom ve Rotation matrisine göre PDF Rect'ine çevirir.
    * **Parametreler:**
      * `cx1`: cx1 parametre değeri.
      * `cy1`: cy1 parametre değeri.
      * `cx2`: cx2 parametre değeri.
      * `cy2`: cy2 parametre değeri.

  * **`pdf_to_canvas_rect(self, pdf_rect)`**
    * **İşlevi:** PDF Rect koordinatlarını Canvas koordinatlarına çevirir.
    * **Parametreler:**
      * `pdf_rect`: pdf_rect parametre değeri.

  * **`find_word_at_click(self, cx, cy)`**
    * **İşlevi:** Kullanıcı sadece tek tık yaptıysa, tıklanan noktadaki satır veya kelimenin koordinatlarını döndürür.
    * **Parametreler:**
      * `cx`: Canvas üzerindeki X piksel koordinatı.
      * `cy`: Canvas üzerindeki Y piksel koordinatı.

  * **`extract_text_and_styles(self, pdf_rect)`**
    * **İşlevi:** Seçilen PDF dikdörtgenindeki metni, fontunu, boyutunu ve rengini ayıklar.
    * **Parametreler:**
      * `pdf_rect`: pdf_rect parametre değeri.

  * **`sample_pixel_color(self, cx, cy)`**
    * **İşlevi:** Canvas koordinatındaki pikselin rengini hex (#RRGGBB) olarak döndürür.
    * **Parametreler:**
      * `cx`: Canvas üzerindeki X piksel koordinatı.
      * `cy`: Canvas üzerindeki Y piksel koordinatı.

  * **`apply_text_edit(self, rect_coords, payload)`**
    * **İşlevi:** PyMuPDF Redaction ve Metin Yazma motorunu çalıştırır.
    * **Parametreler:**
      * `rect_coords`: rect_coords parametre değeri.
      * `payload`: payload parametre değeri.

  * **`_insert_single_line(self, page, target_rect, text, fontsize, fontfile, fontbuffer, color, align, auto_fit)`**
    * **İşlevi:** Tek bir satırı otomatik sığdırma ve font kontrolleriyle PDF sayfasına yerleştirir.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `target_rect`: target_rect parametre değeri.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `fontsize`: Yazı tipi punto boyutu (pt cinsinden değer).
      * `fontfile`: fontfile parametre değeri.
      * `fontbuffer`: fontbuffer parametre değeri.
      * `color`: Hex veya RGB formatında renk kodu (örn: "#FFCC00").
      * `align`: align parametre değeri.
      * `auto_fit`: auto_fit parametre değeri.

  * **`undo(self)`**
    * **İşlevi:** Son yapılan metin düzenlemesini geri alır.

---

### pd_inpage_text_editor.py

**Modül Tanımı:** Canvas üzerinde fare ile metin seçme, sürükleme ve ok tuşlarıyla (nudge) taşıma kontrolcüsü modülü.

#### `InPageTextEditor` (Sınıf)

Canvas üzerinde fare olayları, metin seçimi, sürükle-bırak ve ok tuşlarıyla (nudge) metin taşıma kontrolcü sınıfıdır.

  * **`__init__(self, pdf_viewer)`**
    * **İşlevi:** Sayfa içi metin düzenleme kontrolcüsünü ve InPageTextEngine motorunu başlatır.
    * **Parametreler:**
      * `pdf_viewer`: pdf_viewer parametre değeri.

  * **`_undo_stack(self)`**
    * **İşlevi:** Geri alma yığınına erişim (arka uç motoru ile uyumlu).

  * **`toggle(self)`**
    * **İşlevi:** Metin düzenleme aracını aç/kapa.

  * **`activate(self)`**
    * **İşlevi:** Metin düzenleme aracını aktif hale getirir.

  * **`deactivate(self)`**
    * **İşlevi:** Metin düzenleme aracını kapatır ve varsayılan canvas kontrollerini geri yükler.

  * **`_bind_canvas_events(self)`**
    * **İşlevi:** Canvas fare ve klavye olaylarını metin düzenleyiciye bağlar.

  * **`_on_mouse_down(self, event)`**
    * **İşlevi:** Fare tıklama olayı.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_on_mouse_drag(self, event)`**
    * **İşlevi:** Fare sürükleme olayı (seçim kutusunu çizer veya mevcut kutuyu taşır).
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_on_mouse_up(self, event)`**
    * **İşlevi:** Fare bırakma olayı.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_canvas_to_pdf_rect(self, cx1, cy1, cx2, cy2)`**
    * **İşlevi:** Canvas koordinatlarını mevcut Zoom ve Rotation matrisine göre PDF Rect'ine çevirir.
    * **Parametreler:**
      * `cx1`: cx1 parametre değeri.
      * `cy1`: cy1 parametre değeri.
      * `cx2`: cx2 parametre değeri.
      * `cy2`: cy2 parametre değeri.

  * **`_pdf_to_canvas_rect(self, pdf_rect)`**
    * **İşlevi:** PDF Rect koordinatlarını Canvas koordinatlarına çevirir.
    * **Parametreler:**
      * `pdf_rect`: pdf_rect parametre değeri.

  * **`_find_word_at_click(self, cx, cy)`**
    * **İşlevi:** Kullanıcı sadece tek tık yaptıysa, tıklanan noktadaki satır veya kelimenin koordinatlarını döndürür.
    * **Parametreler:**
      * `cx`: Canvas üzerindeki X piksel koordinatı.
      * `cy`: Canvas üzerindeki Y piksel koordinatı.

  * **`_extract_text_and_styles(self, pdf_rect)`**
    * **İşlevi:** Seçilen PDF dikdörtgenindeki metni, fontunu, boyutunu ve rengini ayıklar.
    * **Parametreler:**
      * `pdf_rect`: pdf_rect parametre değeri.

  * **`_draw_selection_box_with_handles(self, x1, y1, x2, y2)`**
    * **İşlevi:** Canvas üzerinde seçilen metin kutusunu ve köşe tutamaçlarını çizer.
    * **Parametreler:**
      * `x1`: Seçim alanının sol kenar koordinatı.
      * `y1`: Seçim alanının üst kenar koordinatı.
      * `x2`: Seçim alanının sağ kenar koordinatı.
      * `y2`: Seçim alanının alt kenar koordinatı.

  * **`_on_box_double_click(self, event)`**
    * **İşlevi:** Kutuya çift tıklandığında metin düzenleme penceresini açar.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_on_enter_key(self)`**
    * **İşlevi:** Enter tuşuna basıldığında yön tuşlarıyla yapılan taşımayı kaydeder.

  * **`_apply_direct_move(self)`**
    * **İşlevi:** Kutunun yeni yerine bırakılmasıyla metni hemen PDF'e taşır.

  * **`_clear_selection_visuals(self)`**
    * **İşlevi:** Canvas üzerindeki geçici seçim çizgilerini ve tutamaçları temizler.

  * **`nudge(self, dx_pt, dy_pt)`**
    * **İşlevi:** Klavye yön tuşları veya dialog butonları ile seçili metin kutusunu PDF puanı kadar kaydırır.
    * **Parametreler:**
      * `dx_pt`: dx_pt parametre değeri.
      * `dy_pt`: dy_pt parametre değeri.

  * **`reset_offset(self)`**
    * **İşlevi:** Ofseti sıfırlayıp kutuyu orijinal yerine geri döndürür.

  * **`_open_edit_dialog(self, pdf_rect, extracted_info)`**
    * **İşlevi:** Düzenleme dialogunu açar.
    * **Parametreler:**
      * `pdf_rect`: pdf_rect parametre değeri.
      * `extracted_info`: extracted_info parametre değeri.

  * **`start_eyedropper(self, dialog)`**
    * **İşlevi:** Canvas üzerinden renk seçme (Damlalık) modunu başlatır.
    * **Parametreler:**
      * `dialog`: Açılan modal pencere veya ayarlar diyalog referansı.

  * **`_handle_eyedropper_click(self, event)`**
    * **İşlevi:** Damlalık ile canvas'a tıklandığında altındaki pikselin rengini alır.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`apply_text_edit(self, rect_coords, payload)`**
    * **İşlevi:** PyMuPDF Redaction ve Metin Yazma motorunu çalıştırır.
    * **Parametreler:**
      * `rect_coords`: rect_coords parametre değeri.
      * `payload`: payload parametre değeri.

  * **`undo(self)`**
    * **İşlevi:** Son yapılan metin düzenlemesini geri alır.

---

### pd_vector_box_dialog.py

**Modül Tanımı:** Vektörel kutu renk, kenarlık ve saydamlık ayarları diyalog modülü.

#### `VectorBoxPropertiesDialog` (Sınıf)

Vektörel kutu ve annotation özelliklerini tek pencereden düzenleme dialogu.

  * **`__init__(self, viewer, target, idx, page)`**
    * **İşlevi:** VectorBoxPropertiesDialog sınıfını ve gerekli bileşenlerini ilklendirir.
    * **Parametreler:**
      * `viewer`: viewer parametre değeri.
      * `target`: target parametre değeri.
      * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.

  * **`_build_ui(self)`**
    * **İşlevi:** _build_ui işlemini gerçekleştirir.

  * **`_on_fill_toggle(self)`**
    * **İşlevi:** _on_fill_toggle işlemini gerçekleştirir.

  * **`_on_stroke_toggle(self)`**
    * **İşlevi:** _on_stroke_toggle işlemini gerçekleştirir.

  * **`_on_radius_toggle(self)`**
    * **İşlevi:** _on_radius_toggle işlemini gerçekleştirir.

  * **`_on_width_change(self, val)`**
    * **İşlevi:** _on_width_change işlemini gerçekleştirir.
    * **Parametreler:**
      * `val`: Atanacak sayısal veya metinsel değer.

  * **`_on_radius_change(self, val)`**
    * **İşlevi:** _on_radius_change işlemini gerçekleştirir.
    * **Parametreler:**
      * `val`: Atanacak sayısal veya metinsel değer.

  * **`_pick_fill_color(self)`**
    * **İşlevi:** _pick_fill_color işlemini gerçekleştirir.

  * **`_pick_stroke_color(self)`**
    * **İşlevi:** _pick_stroke_color işlemini gerçekleştirir.

  * **`_update_preview(self)`**
    * **İşlevi:** Canvas üzerindeki canlı kutu önizlemesini çizer.

  * **`_is_light_color(hex_color)`**
    * **İşlevi:** _is_light_color işlemini gerçekleştirir.
    * **Parametreler:**
      * `hex_color`: Atanacak veya seçilen Hex renk kodu.

  * **`_apply_editable(self)`**
    * **İşlevi:** Ayarları interaktif kutuya uygula (düzenlenebilir bırak).

  * **`_apply_and_bake(self)`**
    * **İşlevi:** Ayarları uygula ve doğrudan PDF içerik akışına vektörel olarak mühürle.

  * **`_apply_properties_to_target(self, bake)`**
    * **İşlevi:** _apply_properties_to_target işlemini gerçekleştirir.
    * **Parametreler:**
      * `bake`: bake parametre değeri.

#### Bağımsız Fonksiyonlar

* **`draw_rounded_rect_on_canvas(canvas, x1, y1, x2, y2, radius, **kwargs)`**
  * **İşlevi:** Tkinter Canvas üzerinde yuvarlak veya keskin köşeli dikdörtgen çizer.
  * **Parametreler:**
    * `canvas`: Çizim ve render işlemlerinin yapıldığı Canvas bileşeni.
    * `x1`: Seçim alanının sol kenar koordinatı.
    * `y1`: Seçim alanının üst kenar koordinatı.
    * `x2`: Seçim alanının sağ kenar koordinatı.
    * `y2`: Seçim alanının alt kenar koordinatı.
    * `radius`: radius parametre değeri.
    * `kwargs`: Üst sınıfa veya alt bileşene aktarılacak ek anahtar-değer parametreleri.

---

### pd_vector_boxes.py

**Modül Tanımı:** Vektörel arka plan kutuları oluşturma, taşıma ve PDF içine kalıcı gömme motoru modülü.

#### `VectorBoxManagerDialog` (Sınıf)

Mevcut sayfadaki vektörel kutuları listeleyen ve toplu/tekil yönetim sağlayan diyalog.

  * **`__init__(self, pdf_viewer)`**
    * **İşlevi:** VectorBoxManagerDialog sınıfını ve gerekli bileşenlerini ilklendirir.
    * **Parametreler:**
      * `pdf_viewer`: pdf_viewer parametre değeri.

  * **`_setup_ui(self)`**
    * **İşlevi:** _setup_ui işlemini gerçekleştirir.

  * **`_load_boxes(self)`**
    * **İşlevi:** _load_boxes işlemini gerçekleştirir.

  * **`_edit_box(self, box)`**
    * **İşlevi:** _edit_box işlemini gerçekleştirir.
    * **Parametreler:**
      * `box`: box parametre değeri.

  * **`_convert_box(self, box)`**
    * **İşlevi:** _convert_box işlemini gerçekleştirir.
    * **Parametreler:**
      * `box`: box parametre değeri.

  * **`_delete_box(self, box)`**
    * **İşlevi:** _delete_box işlemini gerçekleştirir.
    * **Parametreler:**
      * `box`: box parametre değeri.

  * **`_convert_all(self)`**
    * **İşlevi:** _convert_all işlemini gerçekleştirir.

  * **`_delete_all(self)`**
    * **İşlevi:** _delete_all işlemini gerçekleştirir.

#### Bağımsız Fonksiyonlar

* **`get_page_vector_boxes(page)`**
  * **İşlevi:** Belirtilen sayfadaki dikdörtgen veya şerit şeklindeki vektörel çizimleri tespit eder.
  * **Parametreler:**
    * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.

* **`find_vector_box_at(page, pdf_x, pdf_y)`**
  * **İşlevi:** Verilen PDF koordinatındaki en uygun vektörel kutuyu bulur (yoksa None).
  * **Parametreler:**
    * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
    * `pdf_x`: pdf_x parametre değeri.
    * `pdf_y`: pdf_y parametre değeri.

* **`delete_vector_box(page, pdf_rect)`**
  * **İşlevi:** Vektörel kutuyu sayfadan siler.
  * **Parametreler:**
    * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
    * `pdf_rect`: pdf_rect parametre değeri.

* **`convert_vector_box_to_annotation(page, box_dict, page_num)`**
  * **İşlevi:** Vektörel kutuyu arka plan akışından siler ve aynı koordinat/renkte.
  * **Parametreler:**
    * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
    * `box_dict`: box_dict parametre değeri.
    * `page_num`: İşlem yapılan sayfanın numarası veya indeksi.

* **`bake_annotation_to_vector_box(pdf_document, ann)`**
  * **İşlevi:** Annotation'ı siler ve yerine PDF içerik akışına (metnin arkasına).
  * **Parametreler:**
    * `pdf_document`: Yüklü PDF belge nesnesi.
    * `ann`: ann parametre değeri.

* **`change_stroke_color_action(viewer, ann, idx)`**
  * **İşlevi:** Highlight / Square annotation çerçeve rengini değiştir.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `ann`: ann parametre değeri.
    * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

* **`bake_annotation_action(viewer, ann, idx)`**
  * **İşlevi:** Sağ tık menüsünden 'Sabitle / Vektörel Arka Plana Dönüştür' komutu.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `ann`: ann parametre değeri.
    * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

* **`_convert_vbox(viewer, v_box)`**
  * **İşlevi:** Vektörel kutuyu annotation'a dönüştür ve ekranda seç.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `v_box`: v_box parametre değeri.

* **`_delete_vbox(viewer, v_box)`**
  * **İşlevi:** Vektörel kutuyu sil (yazıyı koru).
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `v_box`: v_box parametre değeri.

* **`_recolor_vbox(viewer, v_box)`**
  * **İşlevi:** Vektörel kutunun rengini değiştirerek düzenlenebilir yap.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `v_box`: v_box parametre değeri.

* **`_open_vbox_dialog(viewer, v_box)`**
  * **İşlevi:** Vektörel kutu için özellikler penceresini açar.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `v_box`: v_box parametre değeri.

* **`show_vector_box_context_menu(viewer, event, v_box)`**
  * **İşlevi:** Vektörel arka plan kutusu için sağ-tık bağlam menüsü gösterir.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `event`: Tkinter fare veya klavye olay nesnesi (Event).
    * `v_box`: v_box parametre değeri.

* **`handle_vector_box_click(viewer, cx, cy)`**
  * **İşlevi:** Kullanıcı canvas'ta boş yere tıkladığında vektörel kutu var mı kontrol eder ve seçer.
  * **Parametreler:**
    * `viewer`: viewer parametre değeri.
    * `cx`: Canvas üzerindeki X piksel koordinatı.
    * `cy`: Canvas üzerindeki Y piksel koordinatı.

---

### pdf_view_ann_controls.py

**Modül Tanımı:** Annotation penceresinin renk seçimi, manuel ekleme ve buton kontrollerini yöneten Mixin modülü.

#### `AnnControlsMixin` (Sınıf)

Annotation yönetim penceresinin renk seçimi, manuel ekleme, butonlar ve girdi alanlarını oluşturan kontrol Mixin sınıfıdır.

  * **`setup_color_selection(self)`**
    * **İşlevi:** Renk seçimi alanını oluştur.

  * **`setup_input_controls(self)`**
    * **İşlevi:** Not ve link girişi için kontroller.

  * **`setup_control_buttons(self)`**
    * **İşlevi:** Alt kontrol butonları.

  * **`on_type_change(self)`**
    * **İşlevi:** Annotation türü değiştiğinde UI'ı güncelle.

  * **`set_highlight_color(self, color)`**
    * **İşlevi:** Vurgulama rengini ayarla.
    * **Parametreler:**
      * `color`: Hex veya RGB formatında renk kodu (örn: "#FFCC00").

  * **`choose_custom_color(self)`**
    * **İşlevi:** Özel renk seçici.

  * **`add_manual_note(self)`**
    * **İşlevi:** Manuel not ekleme.

  * **`add_manual_link(self)`**
    * **İşlevi:** Manuel link ekleme.

  * **`add_manual_bookmark(self)`**
    * **İşlevi:** Manuel işaret ekleme.

  * **`add_note_to_canvas(self, annotation)`**
    * **İşlevi:** Canvas'a not göstergesi ekle.
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

  * **`add_link_to_canvas(self, annotation)`**
    * **İşlevi:** Canvas'a link göstergesi ekle.
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

  * **`add_bookmark_to_canvas(self, annotation)`**
    * **İşlevi:** Canvas'a işaret göstergesi ekle.
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

---

### pdf_view_ann_core.py

**Modül Tanımı:** Annotasyonların bellekte tutulması, silinmesi ve PDF sayfasına işlenmesini sağlayan çekirdek yönetici modülü.

#### `AnnotationManager` (Sınıf)

Annotasyonların oluşturulması, bellekte saklanması, düzenlenmesi ve PDF sayfasına işlenmesini koordine eden çekirdek yönetici sınıfıdır.

  * **`__init__(self, pdf_viewer)`**
    * **İşlevi:** Annotasyon yöneticisini, çizim katmanını ve renk paletlerini ilklendirir.
    * **Parametreler:**
      * `pdf_viewer`: pdf_viewer parametre değeri.

  * **`handle_error(self, error, operation)`**
    * **İşlevi:** Hataları hem terminale hem GUI'ye yazdır.
    * **Parametreler:**
      * `error`: error parametre değeri.
      * `operation`: operation parametre değeri.

  * **`setup_annotation_compatibility(self)`**
    * **İşlevi:** Ana PDF viewer ile uyumluluk metodları.

  * **`add_annotation(self, annotation)`**
    * **İşlevi:** Annotation ekleme (genel metod).
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

  * **`add_bookmark_annotation(self, page, text)`**
    * **İşlevi:** İşaret annotation'ı ekleme.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`add_link_annotation(self, page, text, url)`**
    * **İşlevi:** Link annotation'ı ekleme.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `url`: url parametre değeri.

  * **`add_highlight_annotation(self, x1, y1, x2, y2, color, text)`**
    * **İşlevi:** Highlight annotation ekleme.
    * **Parametreler:**
      * `x1`: Seçim alanının sol kenar koordinatı.
      * `y1`: Seçim alanının üst kenar koordinatı.
      * `x2`: Seçim alanının sağ kenar koordinatı.
      * `y2`: Seçim alanının alt kenar koordinatı.
      * `color`: Hex veya RGB formatında renk kodu (örn: "#FFCC00").
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`add_note_annotation(self, page, text)`**
    * **İşlevi:** Not annotation'ı ekleme.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`_next_annotation_position(self, page)`**
    * **İşlevi:** Sayfadaki annotation'larla binismeyen bir sonraki ikon konumunu hesapla (PDF koord).
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.

  * **`get_timestamp(self)`**
    * **İşlevi:** Timestamp oluştur.

  * **`export_annotations(self)`**
    * **İşlevi:** Annotation'ları JSON dosyasına aktar.

  * **`import_annotations(self)`**
    * **İşlevi:** JSON dosyasından annotation'ları içe aktar.

  * **`save_pdf_with_annotations(self)`**
    * **İşlevi:** PDF'i annotation'larla birlikte kaydet.

  * **`clear_all_annotations(self)`**
    * **İşlevi:** Tüm annotation'ları temizle.

  * **`add_pdf_annotation(self, annotation)`**
    * **İşlevi:** Annotation'ı PDF'e kalıcı olarak ekle.
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

---

### pdf_view_ann_highlight.py

**Modül Tanımı:** Canvas üzerinde fareyle serbest dikdörtgen çizerek vurgulama (highlight) yapılmasını sağlayan modül.

#### `HighlightTool` (Sınıf)

Canvas üzerinde fare ile serbest dikdörtgen çizerek metin ve alan vurgulaması (highlight) yapılmasını sağlayan etkileşimli çizim aracıdır.

  * **`__init__(self, pdf_viewer)`**
    * **İşlevi:** Vurgulama aracını, fare olay dinleyicilerini ve seçim çerçevesini ilklendirir.
    * **Parametreler:**
      * `pdf_viewer`: pdf_viewer parametre değeri.

  * **`activate(self)`**
    * **İşlevi:** Vurgulama aracını aktifleştir.

  * **`deactivate(self)`**
    * **İşlevi:** Vurgulama aracını deaktifleştir.

  * **`start_highlight(self, event)`**
    * **İşlevi:** Vurgulama başlat.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`update_highlight(self, event)`**
    * **İşlevi:** Vurgulama güncelle.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`finish_highlight(self, event)`**
    * **İşlevi:** Vurgulama tamamla.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`add_highlight_rect(self, start_pos, end_pos)`**
    * **İşlevi:** Vurgulama dikdörtgeni ekle.
    * **Parametreler:**
      * `start_pos`: start_pos parametre değeri.
      * `end_pos`: end_pos parametre değeri.

  * **`add_annotation(self, annotation)`**
    * **İşlevi:** Annotation ekleme (genel metod).
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

  * **`add_bookmark_annotation(self, page, text)`**
    * **İşlevi:** İşaret annotation'ı ekleme.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`add_link_annotation(self, page, text, url)`**
    * **İşlevi:** Link annotation'ı ekleme.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `url`: url parametre değeri.

  * **`add_highlight_annotation(self, x1, y1, x2, y2, color, text)`**
    * **İşlevi:** Highlight annotation ekleme.
    * **Parametreler:**
      * `x1`: Seçim alanının sol kenar koordinatı.
      * `y1`: Seçim alanının üst kenar koordinatı.
      * `x2`: Seçim alanının sağ kenar koordinatı.
      * `y2`: Seçim alanının alt kenar koordinatı.
      * `color`: Hex veya RGB formatında renk kodu (örn: "#FFCC00").
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`add_note_annotation(self, page, text)`**
    * **İşlevi:** Not annotation'ı ekleme.
    * **Parametreler:**
      * `page`: PyMuPDF fitz.Page sayfa nesnesi referansı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`clear_all_canvas_annotations(self)`**
    * **İşlevi:** Canvas'tan tüm annotation'ları temizle.

#### Bağımsız Fonksiyonlar

* **`test_annotation_manager()`**
  * **İşlevi:** Annotation manager test.

---

### pdf_view_ann_window.py

**Modül Tanımı:** Annotasyonların listelendiği, filtrelendiği ve düzenlendiği gelişmiş yönetim penceresi modülü.

#### `AnnWindowMixin` (Sınıf)

Annotation penceresi ve liste yönetimi metodlarını içeren mixin sınıfı.

  * **`create_annotation_window(self)`**
    * **İşlevi:** Annotation araçları penceresini oluştur - ScrollableFrame olmadan.

  * **`bind_mousewheel(self)`**
    * **İşlevi:** Mouse wheel scrolling.

  * **`configure_scroll_region(self, event)`**
    * **İşlevi:** Canvas scroll region'ını güncelle.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`configure_canvas_width(self, event)`**
    * **İşlevi:** Canvas width'ini ayarla.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`safe_close_window(self)`**
    * **İşlevi:** Güvenli pencere kapanması.

  * **`refresh_annotation_list(self)`**
    * **İşlevi:** Annotation listesini yenile.

  * **`create_annotation_item(self, index, annotation)`**
    * **İşlevi:** Annotation item oluştur.
    * **Parametreler:**
      * `index`: İşlem yapılacak öğenin dizin indeksi (int).
      * `annotation`: annotation parametre değeri.

  * **`safe_goto_annotation(self, annotation)`**
    * **İşlevi:** Annotation'a güvenli git.
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

  * **`safe_delete_annotation(self, index)`**
    * **İşlevi:** Annotation'ı güvenli sil.
    * **Parametreler:**
      * `index`: İşlem yapılacak öğenin dizin indeksi (int).

  * **`clear_annotation_from_canvas(self, annotation)`**
    * **İşlevi:** Canvas'tan annotation'ı temizle - Geliştirilmiş versiyon.
    * **Parametreler:**
      * `annotation`: annotation parametre değeri.

  * **`on_search_change(self)`**
    * **İşlevi:** Arama değişikliği.

---

### pdf_view_annotations.py

**Modül Tanımı:** Vurgulama, notlar, damgalar ve annotasyon katmanı etkileşimlerini yöneten Mixin modülü.

#### `AnnotationMixin` (Sınıf)

PDF üzerinde tooltip notları, işaretlemeler, damgalar ve etkileşimli annotasyon katmanını yöneten Mixin sınıfıdır.

  * **`on_canvas_motion(self, event)`**
    * **İşlevi:** Canvas üzerinde mouse hareketi.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`show_tooltip(self, x, y, text)`**
    * **İşlevi:** Tooltip göster.
    * **Parametreler:**
      * `x`: Yatay eksendeki piksel veya nokta koordinatı.
      * `y`: Düşey eksendeki piksel veya nokta koordinatı.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`hide_tooltip(self)`**
    * **İşlevi:** Tooltip'i gizle.

  * **`_annotation_at_canvas_pos(self, cx, cy)`**
    * **İşlevi:** Canvas koordinatında annotation varsa (ann, idx) döndür, yoksa (None, -1).
    * **Parametreler:**
      * `cx`: Canvas üzerindeki X piksel koordinatı.
      * `cy`: Canvas üzerindeki Y piksel koordinatı.

  * **`on_canvas_double_click(self, event)`**
    * **İşlevi:** Canvas çift tıklama: annotation varsa aç/göster.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`get_note_content_at_position(self, x, y)`**
    * **İşlevi:** Belirtilen pozisyondaki not içeriğini al.
    * **Parametreler:**
      * `x`: Yatay eksendeki piksel veya nokta koordinatı.
      * `y`: Düşey eksendeki piksel veya nokta koordinatı.

  * **`get_link_url_at_position(self, x, y)`**
    * **İşlevi:** Belirtilen pozisyondaki link URL'sini al.
    * **Parametreler:**
      * `x`: Yatay eksendeki piksel veya nokta koordinatı.
      * `y`: Düşey eksendeki piksel veya nokta koordinatı.

  * **`show_note_details(self, x, y)`**
    * **İşlevi:** Not detaylarını göster.
    * **Parametreler:**
      * `x`: Yatay eksendeki piksel veya nokta koordinatı.
      * `y`: Düşey eksendeki piksel veya nokta koordinatı.

  * **`show_bookmark_details(self, x, y)`**
    * **İşlevi:** İşaret detaylarını göster.
    * **Parametreler:**
      * `x`: Yatay eksendeki piksel veya nokta koordinatı.
      * `y`: Düşey eksendeki piksel veya nokta koordinatı.

  * **`open_link(self, x, y)`**
    * **İşlevi:** Link'i aç.
    * **Parametreler:**
      * `x`: Yatay eksendeki piksel veya nokta koordinatı.
      * `y`: Düşey eksendeki piksel veya nokta koordinatı.

  * **`toggle_highlight_mode(self)`**
    * **İşlevi:** Vurgulama modunu aç/kapat.

  * **`open_advanced_annotations(self)`**
    * **İşlevi:** Gelişmiş annotation penceresini aç.

  * **`choose_highlight_color(self)`**
    * **İşlevi:** Vurgulama rengi seç.

  * **`quick_add_note(self)`**
    * **İşlevi:** Hızlı not ekleme — küçük popup diyalog.

  * **`quick_add_bookmark(self)`**
    * **İşlevi:** Hızlı işaret ekleme — mevcut sayfaya anında ekler, diyalog açmaz.

  * **`quick_add_link(self)`**
    * **İşlevi:** Hızlı link ekleme — küçük popup diyalog.

  * **`on_canvas_right_click(self, event)`**
    * **İşlevi:** Sağ tık: annotation varsa onun bağlam menüsünü, yoksa vektör kutu bağlam menüsünü göster.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_show_annotation_context_menu(self, event, ann, idx)`**
    * **İşlevi:** Annotation için sağ-tık bağlam menüsü.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).
      * `ann`: ann parametre değeri.
      * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

  * **`_change_highlight_color(self, ann, idx)`**
    * **İşlevi:** Highlight annotation rengini değiştir.
    * **Parametreler:**
      * `ann`: ann parametre değeri.
      * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

  * **`_edit_annotation(self, ann, idx)`**
    * **İşlevi:** Not veya link annotation'ını düzenle.
    * **Parametreler:**
      * `ann`: ann parametre değeri.
      * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

  * **`_delete_annotation_at(self, idx)`**
    * **İşlevi:** Belirtilen indexteki annotation'ı sil ve sayfayı yenile.
    * **Parametreler:**
      * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

  * **`open_quick_access(self)`**
    * **İşlevi:** F2 — Hızlı Erişim panelini aç.

  * **`on_canvas_click(self, event)`**
    * **İşlevi:** Canvas tıklama olayını işle.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`on_canvas_drag(self, event)`**
    * **İşlevi:** Canvas drag olayı — highlight taşıma/boyutlandırma.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`on_canvas_release(self, event)`**
    * **İşlevi:** Canvas button release — drag/resize işlemini tamamla.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_find_highlight_at(self, cx, cy)`**
    * **İşlevi:** Canvas koordinatında highlight annotation varsa (ann, idx) döndür.
    * **Parametreler:**
      * `cx`: Canvas üzerindeki X piksel koordinatı.
      * `cy`: Canvas üzerindeki Y piksel koordinatı.

  * **`_get_resize_handle_at(self, cx, cy)`**
    * **İşlevi:** Verilen koordinatta resize handle var mı kontrol et; handle adı döndür ya da None.
    * **Parametreler:**
      * `cx`: Canvas üzerindeki X piksel koordinatı.
      * `cy`: Canvas üzerindeki Y piksel koordinatı.

  * **`_select_highlight(self, ann, idx)`**
    * **İşlevi:** Highlight annotation'ı seç, seçim göstergelerini çiz.
    * **Parametreler:**
      * `ann`: ann parametre değeri.
      * `idx`: Öğenin veya sayfanın liste içerisindeki sıra indeksi (int).

  * **`_draw_selection_handles_coords(self, x1, y1, x2, y2)`**
    * **İşlevi:** Seçim kenarlığı ve köşe handle'larını çiz.
    * **Parametreler:**
      * `x1`: Seçim alanının sol kenar koordinatı.
      * `y1`: Seçim alanının üst kenar koordinatı.
      * `x2`: Seçim alanının sağ kenar koordinatı.
      * `y2`: Seçim alanının alt kenar koordinatı.

  * **`_deselect_highlight(self)`**
    * **İşlevi:** Seçili highlight veya vektör kutu seçimini kaldır, göstergeleri sil.

---

### pdf_view_display.py

**Modül Tanımı:** PyMuPDF motoruyla PDF render, canvas çizimleri ve sayfa görselleştirmesini yöneten Mixin modülü.

#### `DisplayMixin` (Sınıf)

PyMuPDF motoru ile PDF sayfalarını yüksek çözünürlüklü piksellere render eden, canvas üzerine çizen ve thumbnail önizlemelerini üreten Mixin sınıfıdır.

  * **`create_thumbnails(self, progress_bar, progress_label, progress_window)`**
    * **İşlevi:** Sayfa küçük resimlerini oluştur.
    * **Parametreler:**
      * `progress_bar`: progress_bar parametre değeri.
      * `progress_label`: progress_label parametre değeri.
      * `progress_window`: progress_window parametre değeri.

  * **`display_page(self)`**
    * **İşlevi:** Mevcut sayfayı görüntüle.

  * **`show_highlights(self)`**
    * **İşlevi:** Mevcut sayfadaki annotation_manager annotation'larını göster.

  * **`load_pdf_annotations(self)`**
    * **İşlevi:** PDF'deki annotation'ları yükle ve canvas'ta göster.

  * **`clear_previous_annotations(self)`**
    * **İşlevi:** Önceki PDF'in annotation'larını temizle.

---

### pdf_view_file_ops.py

**Modül Tanımı:** PDF açma, kaydetme, dışa aktarma ve dosya geçmişini yöneten Mixin modülü.

#### `FileOperationsMixin` (Sınıf)

PDF dosyalarını açma, arka planda yükleme, annotasyonlarla birlikte kaydetme ve son dosyalar listesini yöneten Mixin sınıfıdır.

  * **`open_pdf(self)`**
    * **İşlevi:** PDF dosyası aç.

  * **`load_pdf_with_progress(self, file_path)`**
    * **İşlevi:** PDF'yi progress bar ile yükle.
    * **Parametreler:**
      * `file_path`: İşlem yapılacak veya açılacak dosyanın mutlak dosya yolu.

  * **`save_pdf(self)`**
    * **İşlevi:** PDF'yi kaydet - kaydetme yöntemini kullanıcıya sorar.

  * **`_is_same_file(path1, path2)`**
    * **İşlevi:** İki dosya yolunun aynı fiziksel dosyayı gösterip göstermediğini kontrol eder.
    * **Parametreler:**
      * `path1`: path1 parametre değeri.
      * `path2`: path2 parametre değeri.

  * **`_ask_save_mode(self)`**
    * **İşlevi:** Kaydetme yöntemi seçme diyaloğunu göster. 'json', 'embed' veya None döndürür.

  * **`_save_with_json_sidecar(self, file_path)`**
    * **İşlevi:** PDF'yi kaydet; annotation'ları .ann.json sidecar dosyasına yaz.
    * **Parametreler:**
      * `file_path`: İşlem yapılacak veya açılacak dosyanın mutlak dosya yolu.

  * **`_save_with_embedded_annotations(self, file_path)`**
    * **İşlevi:** Annotation'ları PDF'e standart PDF annotation olarak göm ve kaydet.
    * **Parametreler:**
      * `file_path`: İşlem yapılacak veya açılacak dosyanın mutlak dosya yolu.

  * **`_hex_to_rgb_float(hex_color)`**
    * **İşlevi:** '#RRGGBB' formatındaki rengi (r, g, b) float tuple'ına çevir (0.0-1.0).
    * **Parametreler:**
      * `hex_color`: Atanacak veya seçilen Hex renk kodu.

  * **`load_settings(self)`**
    * **İşlevi:** Ayarları yükle.

  * **`save_settings(self)`**
    * **İşlevi:** Ayarları kaydet.

  * **`on_closing(self)`**
    * **İşlevi:** Program kapanırken.

  * **`load_existing_annotations(self)`**
    * **İşlevi:** PDF ile aynı klasördeki JSON sidecar dosyasından veya doğrudan PDF'ten gömülü annotation'ları yükle.

---

### pdf_view_main.py

**Modül Tanımı:** Ana uygulama giriş noktası ve tüm Mixin bileşenlerini birleştiren ana pencere modülü.

#### `PDFViewer` (Sınıf)

Tüm Mixin bileşenlerini birleştirerek PDF görüntüleme, render, arama ve navigasyon işlemlerini koordine eden ana uygulama sınıfıdır.

  * **`__init__(self)`**
    * **İşlevi:** Ana pencereyi, Mixin arayüzlerini, durum çubuğunu ve PyMuPDF belge motorunu ilklendirir.

  * **`toggle_inpage_text_edit_mode(self)`**
    * **İşlevi:** Sayfa içi metin düzenleme modunu aç/kapat.

  * **`undo_inpage_text_edit(self)`**
    * **İşlevi:** Son yapılan metin düzenlemesini geri al (Ctrl+Z).

  * **`run(self)`**
    * **İşlevi:** Uygulamayı çalıştır.

#### `AdvancedAnnotationWindow` (Sınıf)

PDF üzerindeki tüm vurgulama, not, çizim ve link annotasyonlarını listeleyen, filtreleyen ve yöneten gelişmiş annotasyon penceresidir.

  * **`__init__(self, parent, pdf_viewer)`**
    * **İşlevi:** Gelişmiş annotasyon yönetim modal penceresini ve liste bileşenlerini ilklendirir.
    * **Parametreler:**
      * `parent`: Üst pencere veya taşıyıcı arayüz bileşeni referansı.
      * `pdf_viewer`: pdf_viewer parametre değeri.

  * **`setup_ui(self)`**
    * **İşlevi:** Annotation araçları UI'ını oluştur.

  * **`set_highlight_color(self, color)`**
    * **İşlevi:** Vurgulama rengini ayarla.
    * **Parametreler:**
      * `color`: Hex veya RGB formatında renk kodu (örn: "#FFCC00").

  * **`add_note(self)`**
    * **İşlevi:** Not ekle.

  * **`refresh_annotation_list(self)`**
    * **İşlevi:** Annotation listesini yenile.

  * **`delete_annotation(self, index)`**
    * **İşlevi:** Annotation'ı sil.
    * **Parametreler:**
      * `index`: İşlem yapılacak öğenin dizin indeksi (int).

#### Bağımsız Fonksiyonlar

* **`main()`**
  * **İşlevi:** Ana program.

---

### pdf_view_navigation.py

**Modül Tanımı:** Sayfa geçişleri, yakınlaştırma (zoom), sayfa döndürme ve klavye gezintisini yöneten Mixin modülü.

#### `NavigationMixin` (Sınıf)

Önceki/sonraki sayfa geçişleri, direkt sayfa atlama, yakınlaştırma (zoom), sayfa döndürme ve klavye gezintisini yöneten Mixin sınıfıdır.

  * **`previous_page(self)`**
    * **İşlevi:** Önceki sayfaya git.

  * **`next_page(self)`**
    * **İşlevi:** Sonraki sayfaya git.

  * **`goto_page(self, event)`**
    * **İşlevi:** Belirtilen sayfaya git.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`goto_page_direct(self, page_num)`**
    * **İşlevi:** Doğrudan belirtilen sayfaya git (küçük resim tıklaması için).
    * **Parametreler:**
      * `page_num`: İşlem yapılan sayfanın numarası veya indeksi.

  * **`zoom_in(self)`**
    * **İşlevi:** Yakınlaştır.

  * **`zoom_out(self)`**
    * **İşlevi:** Uzaklaştır.

  * **`reset_zoom(self)`**
    * **İşlevi:** Zoom'u sıfırla.

  * **`rotate_page(self)`**
    * **İşlevi:** Sayfayı 90 derece döndür.

  * **`on_mouse_wheel(self, event)`**
    * **İşlevi:** Mouse wheel ile kaydırma.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`on_ctrl_mouse_wheel(self, event)`**
    * **İşlevi:** Ctrl + Mouse wheel ile zoom.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

---

### pdf_view_quick_access.py

**Modül Tanımı:** F2 hızlı erişim paneli ve annotasyon gezgini Mixin modülü.

#### `QuickAccessPanel` (Sınıf)

F2 Hızlı Erişim Paneli — annotation navigasyonu ve yönetimi.

  * **`__init__(self, pdf_viewer)`**
    * **İşlevi:** QuickAccessPanel sınıfını ve gerekli bileşenlerini ilklendirir.
    * **Parametreler:**
      * `pdf_viewer`: pdf_viewer parametre değeri.

  * **`open(self)`**
    * **İşlevi:** Paneli aç; zaten açıksa öne getir ve yenile.

  * **`_create_window(self)`**
    * **İşlevi:** _create_window işlemini gerçekleştirir.

  * **`_annotations(self)`**
    * **İşlevi:** Ortak annotation listesini döndür (viewer ya da manager üzerinden).

  * **`_filtered(self)`**
    * **İşlevi:** _filtered işlemini gerçekleştirir.

  * **`refresh(self)`**
    * **İşlevi:** Listeyi yeniden çiz.

  * **`_build_row(self, orig_idx, ann)`**
    * **İşlevi:** _build_row işlemini gerçekleştirir.
    * **Parametreler:**
      * `orig_idx`: orig_idx parametre değeri.
      * `ann`: ann parametre değeri.

  * **`_goto(self, ann)`**
    * **İşlevi:** Annotation sayfasına git.
    * **Parametreler:**
      * `ann`: ann parametre değeri.

  * **`_delete(self, orig_idx, ann)`**
    * **İşlevi:** Onaydan sonra annotation'ı sil.
    * **Parametreler:**
      * `orig_idx`: orig_idx parametre değeri.
      * `ann`: ann parametre değeri.

---

### pdf_view_search.py

**Modül Tanımı:** PDF içinde metin arama, regex eşleştirme ve arama sonuçlarını vurgulama Mixin modülü.

#### `SearchMixin` (Sınıf)

PDF belgesi içerisinde büyük/küçük harf duyarsız metin arama, çoklu sonuç bulma ve sonuçları sarı/kırmızı çerçeveyle vurgulama Mixin sınıfıdır.

  * **`search_text(self, event)`**
    * **İşlevi:** PDF'de metin ara.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`search_next(self, event)`**
    * **İşlevi:** Sonraki arama sonucuna git.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`show_search_result(self)`**
    * **İşlevi:** Mevcut arama sonucunu göster.

---

### pdf_view_text_editor.py

**Modül Tanımı:** PDF metinlerini harici metin düzenleyicide açıp işlemeyi sağlayan Mixin modülü.

#### `ProfessionalTextEditor` (Sınıf)

Profesyonel metin editörü - PDF'den çıkarılan metni düzenleme ve kaydetme.

  * **`__init__(self, parent, pdf_viewer, text, start_page, end_page)`**
    * **İşlevi:** ProfessionalTextEditor sınıfını ve gerekli bileşenlerini ilklendirir.
    * **Parametreler:**
      * `parent`: Üst pencere veya taşıyıcı arayüz bileşeni referansı.
      * `pdf_viewer`: pdf_viewer parametre değeri.
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `start_page`: start_page parametre değeri.
      * `end_page`: end_page parametre değeri.

  * **`init_tts(self)`**
    * **İşlevi:** TTS manager'ı başlat.

  * **`_remove_page_separators(self, text)`**
    * **İşlevi:** Metindeki sayfa ayraçlarını temizle (=== SAYFA X ===).
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`setup_ui(self)`**
    * **İşlevi:** Editör arayüzünü oluştur.

  * **`_on_text_scroll(self, *args)`**
    * **İşlevi:** Metin kaydırma olayı.
    * **Parametreler:**
      * `args`: Fonksiyona aktarılan ek konfigürasyon argümanları demeti.

  * **`setup_keybindings(self)`**
    * **İşlevi:** Klavye kısayolları.

  * **`update_line_numbers(self, event)`**
    * **İşlevi:** Satır numaralarını güncelle.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`on_text_modified(self, event)`**
    * **İşlevi:** Metin değiştiğinde.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`update_status(self)`**
    * **İşlevi:** Durum çubuğunu güncelle.

  * **`speak_text(self)`**
    * **İşlevi:** Seçili metni veya tüm metni seslendir.

  * **`stop_speech(self)`**
    * **İşlevi:** Seslendirmeyi durdur.

  * **`save_as_mp3(self)`**
    * **İşlevi:** Seçili metni veya tüm metni MP3 olarak kaydet.

  * **`on_mp3_save_status(self, status)`**
    * **İşlevi:** MP3 kaydetme durum güncellemesi.
    * **Parametreler:**
      * `status`: İşlem veya araç aktiflik durumu.

  * **`change_font_size(self, size)`**
    * **İşlevi:** Metin font boyutunu değiştir.
    * **Parametreler:**
      * `size`: Boyut, punto veya piksel büyüklüğü değeri.

  * **`on_tts_status_update(self, status)`**
    * **İşlevi:** TTS durum güncellemesi callback'i.
    * **Parametreler:**
      * `status`: İşlem veya araç aktiflik durumu.

  * **`open_text_file(self)`**
    * **İşlevi:** TXT dosyası aç ve editöre yükle.

  * **`save_text(self)`**
    * **İşlevi:** Metni dosyaya kaydet.

  * **`copy_all(self)`**
    * **İşlevi:** Tüm metni panoya kopyala.

  * **`select_all(self)`**
    * **İşlevi:** Tüm metni seç.

  * **`undo(self)`**
    * **İşlevi:** Geri al.

  * **`redo(self)`**
    * **İşlevi:** Yinele.

  * **`to_uppercase(self)`**
    * **İşlevi:** Seçili metni büyük harfe çevir.

  * **`to_lowercase(self)`**
    * **İşlevi:** Seçili metni küçük harfe çevir.

  * **`remove_empty_lines(self)`**
    * **İşlevi:** Boş satırları temizle.

  * **`find_text(self)`**
    * **İşlevi:** Metinde ara.

  * **`highlight_current_find(self)`**
    * **İşlevi:** Mevcut arama sonucunu vurgula.

  * **`find_next(self)`**
    * **İşlevi:** Sonraki sonuca git.

  * **`find_prev(self)`**
    * **İşlevi:** Önceki sonuca git.

  * **`replace_current(self)`**
    * **İşlevi:** Mevcut eşleşmeyi değiştir.

  * **`replace_all(self)`**
    * **İşlevi:** Tüm eşleşmeleri değiştir.

---

### pdf_view_text_extraction.py

**Modül Tanımı:** PDF sayfasından seçili veya tüm metni ayıklayan Mixin modülü.

#### `TextExtractionMixin` (Sınıf)

Seçili alandaki veya tüm PDF sayfasındaki metin içeriğini biçimlendirilmiş olarak ayıklayan Mixin sınıfıdır.

  * **`extract_text_to_file(self)`**
    * **İşlevi:** PDF'den metin çıkarma işlemini başlat.

  * **`show_page_range_dialog(self)`**
    * **İşlevi:** Sayfa aralığı seçme penceresi.

  * **`start_text_extraction(self, start_page, end_page)`**
    * **İşlevi:** Metin çıkarma işlemini başlat.
    * **Parametreler:**
      * `start_page`: start_page parametre değeri.
      * `end_page`: end_page parametre değeri.

  * **`_clean_line_breaks(self, text)`**
    * **İşlevi:** PDF'den çıkarılan metindeki gereksiz satır sonlarını temizle.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.

  * **`open_text_editor(self, text, start_page, end_page)`**
    * **İşlevi:** Profesyonel metin editörü penceresini aç.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `start_page`: start_page parametre değeri.
      * `end_page`: end_page parametre değeri.

---

### pdf_view_tts.py

**Modül Tanımı:** pyttsx3 tabanlı Türkçe ve İngilizce metin okuma motorunu yöneten Mixin modülü.

#### `TTSManager` (Sınıf)

Türkçe metin seslendirme yöneticisi - edge-tts kullanır.

  * **`__init__(self, parent_window)`**
    * **İşlevi:** TTSManager sınıfını ve gerekli bileşenlerini ilklendirir.
    * **Parametreler:**
      * `parent_window`: parent_window parametre değeri.

  * **`_check_edge_tts(self)`**
    * **İşlevi:** edge-tts modülünün yüklü olup olmadığını kontrol et.

  * **`speak(self, text, voice, speed, callback)`**
    * **İşlevi:** Metni Türkçe olarak seslendir.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.

  * **`_speak_async(self, text, voice, speed, callback)`**
    * **İşlevi:** Asenkron seslendirme işlemi.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.

  * **`_generate_and_play(self, text, voice, speed, callback)`**
    * **İşlevi:** Ses dosyası oluştur ve oynat.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.

  * **`_play_audio(self)`**
    * **İşlevi:** Ses dosyasını oynat.

  * **`_play_with_pygame(self)`**
    * **İşlevi:** Pygame ile oynat - thread-safe.

  * **`_play_with_playsound(self)`**
    * **İşlevi:** Playsound ile oynat.

  * **`_play_with_subprocess(self)`**
    * **İşlevi:** Sistem oynatıcısı ile oynat.

  * **`stop(self)`**
    * **İşlevi:** Seslendirmeyi durdur - thread-safe.

  * **`_safe_callback(self, callback, message)`**
    * **İşlevi:** GUI thread'inde callback çağır.
    * **Parametreler:**
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.
      * `message`: Kullanıcıya gösterilecek durum veya bildirim iletisi.

  * **`_cleanup_temp(self)`**
    * **İşlevi:** Geçici dosyayı temizle.

  * **`_split_text_into_chunks(self, text, max_chars)`**
    * **İşlevi:** Metni belirli karakter sayısına göre cümle sonlarından böler.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `max_chars`: max_chars parametre değeri.

  * **`save_as_mp3(self, text, voice, speed, output_path, callback)`**
    * **İşlevi:** Metni MP3 dosyası olarak kaydet. 12.000 karakterden uzun metinler parçalara bölünür.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `output_path`: Oluşturulacak veya kaydedilecek hedef dosyanın tam yolu.
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.

  * **`_save_mp3_async(self, text, voice, speed, output_path, callback)`**
    * **İşlevi:** Asenkron MP3 kaydetme işlemi - parçalama desteği ile.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `output_path`: Oluşturulacak veya kaydedilecek hedef dosyanın tam yolu.
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.

  * **`_generate_mp3_chunk(self, text, voice, speed, output_path)`**
    * **İşlevi:** Tek bir MP3 parçası oluştur (callback olmadan).
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `output_path`: Oluşturulacak veya kaydedilecek hedef dosyanın tam yolu.

  * **`_generate_mp3(self, text, voice, speed, output_path, callback)`**
    * **İşlevi:** MP3 dosyası oluştur ve kaydet.
    * **Parametreler:**
      * `text`: İşlenecek, gösterilecek veya aranacak metin içeriği.
      * `voice`: voice parametre değeri.
      * `speed`: speed parametre değeri.
      * `output_path`: Oluşturulacak veya kaydedilecek hedef dosyanın tam yolu.
      * `callback`: İşlem tamamlandığında tetiklenecek geri çağırım fonksiyonu.

  * **`__del__(self)`**
    * **İşlevi:** Yıkıcı - kaynakları temizle.

---

### pdf_view_ui_setup.py

**Modül Tanımı:** Toolbar, canvas, sol thumbnail paneli ve durum çubuğu arayüz bileşenlerini inşa eden Mixin modülü.

#### `UISetupMixin` (Sınıf)

UI kurulum metodlarını içeren mixin sınıfı.

  * **`setup_ui(self)`**
    * **İşlevi:** Ana kullanıcı arayüzünü oluştur.

  * **`setup_toolbar(self)`**
    * **İşlevi:** Toolbar butonlarını oluştur.

  * **`setup_canvas(self)`**
    * **İşlevi:** PDF görüntüleme canvas'ını oluştur.

  * **`setup_canvas_tooltips(self)`**
    * **İşlevi:** Canvas tooltip desteği.

  * **`setup_keybindings(self)`**
    * **İşlevi:** Klavye kısayollarını ayarla.

  * **`delete_selected_annotation(self)`**
    * **İşlevi:** Seçili annotation veya vektörel kutu varsa sil (Delete tuşu kısayolu).

  * **`open_vector_box_manager(self)`**
    * **İşlevi:** Vektörel arka plan kutuları yönetim penceresini aç.

  * **`open_help(self)`**
    * **İşlevi:** F1 - Yardım dosyasını varsayılan tarayıcıda aç.

  * **`_configure_thumbnail_scroll_region(self, event)`**
    * **İşlevi:** Thumbnail canvas scroll region'ını güncelle.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`_configure_thumbnail_canvas_width(self, event)`**
    * **İşlevi:** Thumbnail canvas width'ini ayarla.
    * **Parametreler:**
      * `event`: Tkinter fare veya klavye olay nesnesi (Event).

  * **`update_ui(self)`**
    * **İşlevi:** UI elementlerini güncelle.

---

### pdf_view_utils.py

**Modül Tanımı:** PDF Viewer - Yardımcı Fonksiyonlar ve Genel Araçlar.

#### Bağımsız Fonksiyonlar

* **`handle_exception(exc_type, exc_value, exc_traceback)`**
  * **İşlevi:** Global exception handler - hataları hem terminale hem de dosyaya yaz.
  * **Parametreler:**
    * `exc_type`: exc_type parametre değeri.
    * `exc_value`: exc_value parametre değeri.
    * `exc_traceback`: exc_traceback parametre değeri.

* **`setup_global_exception_handler()`**
  * **İşlevi:** Global exception handler'ı ayarla.

* **`init_error_log()`**
  * **İşlevi:** Error log dosyasını başlat.

* **`center_window(window, width, height)`**
  * **İşlevi:** Pencereyi ekranın ortasına yerleştir.
  * **Parametreler:**
    * `window`: Açık olan pencere veya Toplevel diyalog nesnesi.
    * `width`: Bileşenin piksel cinsinden genişlik değeri.
    * `height`: Bileşenin piksel cinsinden yükseklik değeri.

---
