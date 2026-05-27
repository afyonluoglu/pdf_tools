# Professional PDF Viewer

Python ile geliştirilmiş, modern CustomTkinter arayüzlü, kapsamlı bir PDF görüntüleyici ve düzenleyici uygulaması.

> **Geliştirici:** Dr. Mustafa Afyonluoğlu | **Tarih:** Mart - 2026  
> **Detaylı yardım için:** `F1` tuşuna basın

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Proje Mimarisi](#-proje-mimarisi)
- [Kurulum](#-kurulum)
- [Kullanım Kılavuzu](#-kullanım-kılavuzu)
- [Klavye Kısayolları](#️-klavye-kısayolları)
- [Teknik Detaylar](#-teknik-detaylar)

---

## ✨ Özellikler

### 📄 PDF Görüntüleme
- **Yüksek kaliteli rendering**: PyMuPDF (fitz) motoru ile piksel-mükemmel sayfa görüntüleme
- **Esnek zoom**: %10'dan %500'e kadar yakınlaştırma/uzaklaştırma
  - Toolbar butonları (🔍+ / 🔍-)
  - `Ctrl + Mouse Wheel` ile sürükleyerek zoom
  - `Ctrl+0` ile %100'e sıfırlama
- **Sayfa döndürme**: Her tıklamada 90° döndürme (↻ butonu)
- **Küçük resim paneli**: Sol sidebar'da tüm sayfaların scrollable thumbnail görünümü; thumbnail'e tıklayarak o sayfaya anında erişim
- **Çift scrollbar**: Dikey ve yatay kaydırma desteği büyük sayfalarda tam görüntü sağlar

### 🗂️ Sayfa Navigasyonu
- **Önceki/Sonraki sayfa**: Üst toolbarda ⬅️ ➡️ butonları veya klavye Page Up-Down tuşları
- **Direkt sayfa atlama**: Sayfa numarası kutusuna numara yazıp Enter tuşuna basarak sayfaya geçiş
- **Thumbnail tıklama**: Sol panelden herhangi bir sayfaya tek tıkla gitme

### 🔍 Gelişmiş Metin Arama
- Tüm sayfalarda anlık metin tarama
- Bulunan eşleşmeler kırmızı çerçeve ile vurgulanır
- **"Next" tuşu** ile sonraki eşleşmeye sıralı geçiş
- `Ctrl+F` ile arama kutusuna odaklanma

### 🖍️ Annotation (İşaretleme) Araçları
- **Vurgulama modu**: "🖍️ İşaretle" butonuyla etkinleştirme; fare ile dikdörtgen çizerek metin vurgulama
(Aynı tuşa tekrar tıklanarak vurgulama modundan çıkılır)
- **Renk seçici**: "🎨 Renk" butonu ile vurgulama renginin seçilebilmesi
- **Gelişmiş İşaretleme Yönetimi** (📝 Gelişmiş butonu):
  - Dört annotation türü: **Vurgulama**, **Not**, **İşaret (Bookmark)**, **Link**
  - Tüm annotation'ları listeleyen kaydırılabilir panel
  - Annotation'larda metin arama ve filtreleme
  - Mevcut annotaion'ları tek tek silme desteği
- **Tooltip desteği**: Not ve link annotation'larının üzerine gelindiğinde otomatik açıklama balonu
- **Bağlantıya Geçiş**: Link annotation'una çift tıklayarak internet gezgininde bu bağlantıyı açma
- **Hızlı Annotation Araç Çubuğu** (İkinci toolbar):
  - **📝 Not**: Not ekleme penceresi (mevcut sayfaya)
  - **⭐ İşaret**: Mevcut sayfayı anında işaretle 
  - **🔗 Link**: URL + opsiyonel açıklama ile link ekleme penceresi

- **F2 — Hızlı Erişim Paneli**: Tüm annotation'ları tek ekranda listeler; tür filtreleme, Gör/Sil butonları
- **PDF üzerinde Çift tıklama İşlevleri**:
  - 📝 Not → Not metnini mesaj kutusunda gösterir
  - 🔗 Link → URL'yi varsayılan tarayıcıda açar
  - ⭐ İşaret → Sayfa bilgisini gösterir
- **Sağ tıklama**: Annotation üzerinde bağlam menüsü açar — **Değiştir** (not/link için) ve **Sil** seçenekleri

### 📄 PDF'den Metin Çıkarma
- "📄 Metne Çevir" butonu ile PDF sayfalarından metin aktarımı
- **Sayfa aralığı seçimi**: Tüm sayfalar veya belirli aralık (örn. 3-15. sayfalar)
- **Akıllı satır birleştirme**: PDF'den çıkarılan metindeki gereksiz satır kırılmalarını ve hece bölünmelerini otomatik temizler
- Progress bar ile işlem takibi
- Çıkarılan metin **Profesyonel Metin Editörü**'nde açılır

### ✏️ Profesyonel Metin Editörü
Metin çıkarma işlemi sonrasında açılan tam özellikli metin editörü:

| Özellik | Detay |
|---|---|
| **Metin Düzenleme** | Tam undo/redo desteği (50 adım), büyük/küçük harf dönüşümü |
| **Bul & Değiştir** | Bul, Sonraki/Önceki bul, Şimdikini değiştir, Tümünü değiştir |
| **Dosya İşlemleri** | .txt / .md kaydetme, var olan dosya açma, panoya kopyalama |
| **Satır Numaraları** | Sol kenarda canlı satır numarası gösterimi |
| **Font Boyutu** | 9–28pt arası seçilebilir font boyutu |
| **Boş Satır Temizleme** | Gereksiz boş satırları tek komutla kaldırma |
| **İstatistik çubuğu** | Anlık karakter, kelime ve satır sayısı |
| **Sayfa Ayraçlarını Kaldırma** | Metne gömülü `=== SAYFA X ===` ayraçlarını temizleme |

### 🔊 Metin Seslendirme (TTS)
Metin Editörü içinde entegre Microsoft Edge TTS ile Türkçe seslendirme:

- **İki Türkçe ses**: Emel (Kadın) — `tr-TR-EmelNeural` / Ahmet (Erkek) — `tr-TR-AhmetNeural`
- **Üç hız seçeneği**: Yavaş (-20%), Normal (+0%), Hızlı (+25%)
- **Durdur** butonu ile anlık seslendirmeyi sonlandırma
- **MP3 olarak kaydetme**: Seslendirilen metni .mp3 dosyası olarak dışa aktarma
- Arka planda (thread) çalışarak arayüzü bloklamaz

### 💾 Dosya İşlemleri
- **PDF açma**: Dosya seçici diyaloğu; `.pdf` formatı
- **Progress bar ile yükleme**: Büyük dosyalarda sayfalı yükleme, ilerleme göstergesi
- **Annotation'larla kaydetme**: Tüm vurgulamalar ve notlar PDF'te tekrar açıldığında gösterilebilecek şekilde kaydedilir
- **Ayarlar kalıcılığı**: Son zoom seviyesi ve highlight rengi gibi ayarlar `pdf_viewer_settings.json` dosyasına otomatik kaydedilir

### 🛠️ Hata Yönetimi
- Global exception handler: Tüm beklenmedik hatalar `pdf_viewer_errors.log` dosyasına tarih-damgalı olarak kaydedilir
- Yükleme/kaydetme hatalarında kullanıcıya bilgilendirici hata mesajı

---

## 🏗️ Proje Mimarisi

Proje, `Mixin` tabanlı modüler mimariye sahiptir. Ana sınıf `PDFViewer` hiçbir iş mantığı içermez; tüm fonksiyonellik ayrı Mixin sınıflarından miras alınır.

```
PDF Tools/
├── pdf_view_main.py          # Ana giriş: PDFViewer sınıfı, uygulama başlatma
├── pdf_view_ui_setup.py      # UISetupMixin: Toolbar, canvas, sidebar, keybinding'ler
├── pdf_view_navigation.py    # NavigationMixin: Sayfa geçişi, zoom, döndürme
├── pdf_view_display.py       # DisplayMixin: Sayfa render, thumbnail oluşturma
├── pdf_view_search.py        # SearchMixin: Metin arama, sonuç vurgulama
├── pdf_view_annotations.py   # AnnotationMixin: Tooltip, not/bookmark/link işlemleri
├── pdf_view_file_ops.py      # FileOperationsMixin: Açma, kaydetme, ayarlar
├── pdf_view_text_extraction.py # TextExtractionMixin: PDF→metin, sayfa aralığı
├── pdf_view_text_editor.py   # ProfessionalTextEditor: Metin editörü penceresi
├── pdf_view_tts.py           # TTSManager: Microsoft Edge TTS seslendirme
├── pdf_view_utils.py         # Yardımcı fonk.: exception handler, pencere merkezleme
├── pdf_view_ann_core.py      # AnnotationManager: CRUD, PDF entegrasyonu, içe/dışa aktarım
├── pdf_view_ann_window.py    # AnnWindowMixin: Pencere, liste, scroll, silme/gitme işlemleri
├── pdf_view_ann_controls.py  # AnnControlsMixin: Renk/tip kontrolleri, manuel ekleme, canvas
├── pdf_view_ann_highlight.py # HighlightTool: Fareyle vurgulama aracı + test fonksiyonu
├── annotation_manager_fixed.py # Geriye dönük uyumluluk shim'i (eski importlar için)
├── pdf_viewer_settings.json  # Kullanıcı ayarları (otomatik oluşturulur)
├── pdf_viewer_errors.log     # Hata günlüğü (otomatik oluşturulur)
├── requirements.txt          # Python bağımlılıkları
└── start_pdf_viewer.bat      # Windows hızlı başlatma betiği
```

### Mixin Sınıf Hiyerarşisi

```
PDFViewer
├── UISetupMixin        → setup_ui(), setup_toolbar(), setup_canvas(), setup_keybindings()
├── NavigationMixin     → previous_page(), next_page(), goto_page(), zoom_in/out(), rotate_page()
├── DisplayMixin        → display_page(), create_thumbnails(), update_ui()
├── AnnotationMixin     → toggle_highlight_mode(), on_canvas_click/motion/double_click(), tooltip
├── SearchMixin         → search_text(), search_next(), show_search_result()
├── FileOperationsMixin → open_pdf(), save_pdf(), load/save_settings(), on_closing()
└── TextExtractionMixin → extract_text_to_file(), show_page_range_dialog(), start_text_extraction()

AnnotationManager (pdf_view_ann_core.py)
├── AnnWindowMixin      → create_annotation_window(), refresh_annotation_list(), create_annotation_item()
└── AnnControlsMixin    → setup_color_selection(), add_manual_note/link/bookmark(), canvas gösterimi

HighlightTool (pdf_view_ann_highlight.py)
└── Fareyle vurgulama: activate(), start/update/finish_highlight(), add_highlight_rect()
```

---

## 🚀 Kurulum

### Gereksinimler

```bash
pip install customtkinter>=5.2.0 PyMuPDF>=1.23.0 Pillow>=10.0.0
```

**TTS özelliği için (isteğe bağlı):**

```bash
pip install edge-tts pygame
```

Veya requirements.txt ile tümünü yükleyin:

```bash
pip install -r requirements.txt
```

### Çalıştırma

```bash
python pdf_view_main.py
```

Windows'ta `start_pdf_viewer.bat` dosyasına çift tıklayarak da başlatılabilir.

---

## 📖 Kullanım Kılavuzu

### PDF Açma
1. Toolbar'daki **"📁 Aç"** butonuna tıklayın veya `Ctrl+O` tuşlayın
2. Dosya seçici diyaloğundan `.pdf` dosyasını seçin
3. Yükleme progress bar'ı ile takip edin

### Sayfa Navigasyonu
| Eylem | Yöntem |
|---|---|
| Sonraki sayfa | ➡️ butonu, Page Down |
| Önceki sayfa | ⬅️ butonu, Page Up |
| Belirli sayfaya git | Sayfa numarası kutusuna yaz + Enter |
| Thumbnail ile git | Sol paneldeki küçük resme tıkla |

### Zoom İşlemleri
| Eylem | Yöntem |
|---|---|
| Yakınlaştır | 🔍+ butonu veya `Ctrl+` |
| Uzaklaştır | 🔍- butonu veya `Ctrl-` |
| Fare ile zoom | `Ctrl + Mouse Wheel` |
| %100'e sıfırla | `Ctrl+0` |

### Metin Arama
1. Toolbar'daki arama kutusuna metni yazın (veya `Ctrl+F` ile odaklanın)
2. `Enter` veya 🔍 butonuna basın — bulunan tüm sonuçlar kırmızı çerçeve içerisinde gösterilir
3. **"Next"** butonuyla sonraki eşleşmeye geçin

### Metin Vurgulama
1. **"🎨 Renk"** butonu ile vurgulama rengini seçin (veya Gelişmiş panelden 6 renk arasından seçin)
2. **"🖍️ İşaretle"** butonuna tıklayın — mod etkinleşir
3. PDF üzerinde dikdörtgen çizerek metni vurgulayın
4. Modu kapatmak için tekrar "🖍️ İşaretle" butonuna basın

### Hızlı Annotation Ekleme
| Araç | Yöntem |
|---|---|
| 📝 Not | Toolbar'daki **"📝 Not"** butonu → açılan pencereye notu yaz → ✓ Ekle veya Ctrl+Enter |
| ⭐ İşaret | Toolbar'daki **"⭐ İşaret"** butonu → sayfaya anında eklenir |
| 🔗 Link | Toolbar'daki **"🔗 Link"** butonu → URL ve açıklama gir → ✓ Ekle veya Enter |
| Tüm İşaretleme Listesi | **"🗂️ Erişim"** butonu veya **`F2`** → Hızlı Erişim Paneli |

### Annotation ile Etkileşim
| Eylem | Sonuç |
|---|---|
| Canvas'ta 📝 nota **çift tıkla** | Not metnini gösterir |
| Canvas'ta 🔗 linke **çift tıkla** | URL'yi tarayıcıda açar |
| Canvas'ta ⭐ işarete **çift tıkla** | Sayfa bilgisini gösterir |
| Canvas'ta herhangi annotation'a **sağ tıkla** | **Sil** ve (not/link için) **Değiştir** bağlam menüsü |

### Not / Bookmark / Link Ekleme (Gelişmiş)
1. **"📝 Gelişmiş"** butonuna tıklayın
2. Annotation türünü seçin (Vurgulama / Not / İşaret / Link)
3. İlgili alanları doldurun ve PDF üzerinde konumu belirtin
4. Annotation listesinden mevcut işaretleri yönetin veya silin

### PDF'den Metin Çıkarma
1. **"📄 Metne Çevir"** butonuna tıklayın
2. Sayfa aralığını seçin (Tümü veya belirli aralık)
3. Progress bar ile işlemi takip edin
4. Sonuç, **Profesyonel Metin Editörü**'nde otomatik açılır

### Metin Editörü Seslendirme
1. Editörde seslendirmek istediğiniz metni seçin (seçim yoksa tüm metin)
2. Ses (Emel/Ahmet) ve hız (Yavaş/Normal/Hızlı) seçin
3. **"🔊 Seslendir"** butonuna tıklayın
4. Durdurmak için **"⏹️ Durdur"**
5. MP3 olarak kaydetmek için **"💾 MP3 Kaydet"**

### PDF Kaydetme
1. **"💾 Kaydet"** butonuna veya `Ctrl+S` tuşlayın
2. Kayıt konumunu seçin
3. Tüm annotation'lar PDF ile senkronize şekilde kaydedilir

---

## ⌨️ Klavye Kısayolları

### Ana Pencere

| Kısayol | İşlev |
|---|---|
| `Ctrl+O` | PDF dosyası aç |
| `Ctrl+S` | PDF kaydet |
| `Ctrl+F` | Arama kutusuna odaklan |
| `Ctrl+` veya `Ctrl+=` | Yakınlaştır |
| `Ctrl+-` | Uzaklaştır |
| `Ctrl+0` | Zoom'u %100'e sıfırla |
| `←` Sol Ok | Önceki sayfa |
| `→` Sağ Ok | Sonraki sayfa |
| `Page Up` | Önceki sayfa |
| `Page Down` | Sonraki sayfa |
| `F1` | Yardım dosyasını aç |
| `F2` | Hızlı Erişim Paneli'ni aç (tüm annotation'lar) |

### Metin Editörü

| Kısayol | İşlev |
|---|---|
| `Ctrl+Z` | Geri al |
| `Ctrl+Y` | Yinele |
| `Ctrl+A` | Tümünü seç |
| `Ctrl+C` | Kopyala |
| `Ctrl+V` | Yapıştır |
| `Ctrl+S` | Kaydet |
| `Ctrl+F` | Bul |
| `F3` | Sonraki bul |

---

## 🔧 Teknik Detaylar

### Kullanılan Kütüphaneler

| Kütüphane | Versiyon | Kullanım Amacı |
|---|---|---|
| CustomTkinter | ≥5.2.0 | Modern karanlık tema UI framework |
| PyMuPDF (fitz) | ≥1.23.0 | PDF okuma, rendering, annotation |
| Pillow (PIL) | ≥10.0.0 | Görüntü işleme, thumbnail oluşturma |
| Tkinter | Built-in | Canvas, scroll, temel widget'lar |
| threading | Built-in | Arka plan yükleme ve TTS işlemleri |
| edge-tts | Opsiyonel | Microsoft Edge TTS Türkçe seslendirme |
| pygame | Opsiyonel | MP3 dosyası oynatma |

### Performans Notları
- **Thread desteği**: PDF yükleme ve TTS işlemleri arka plan thread'lerinde çalışır; arayüz donmaz
- **Lazy thumbnail**: Küçük resimler yükleme sırasında kademeli olarak oluşturulur
- **Bellek yönetimi**: PDF dokümanı kapatma sırasında düzgün serbest bırakılır
- **JSON ayarları**: Zoom ve renk tercihleri oturum dışında da kalıcıdır
- **Hata günlükleme**: Tüm hatalar `pdf_viewer_errors.log` dosyasına tarihli olarak kaydedilir

---

## 📝 Lisans

Bu proje CC BY-NC-SA 4.0 lisans şartlarında sunulmaktadır.

---

## 👤 İletişim

**Geliştirici:** Dr. Mustafa Afyonluoğlu  
**Geliştirme Yılı:** 2026
