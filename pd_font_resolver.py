"""
PDF Viewer - Akıllı Font Çözümleyici ve Yönetici (FontResolver)
Windows Sistem Fontları, Kullanıcı AppData Fontları ve PDF Dahili Font Tanımlayıcıları (FontDescriptor)
arasında çapraz eşleştirme yaparak orijinal fontların kayıpsız korunmasını sağlar.
"""

import os
import re
import winreg
from typing import Optional, Dict, Any, List, Tuple


class FontResolver:
    """PDF fontlarını Windows sistem ve kullanıcı fontlarıyla akıllıca eşleştiren motor"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Tekil (Singleton) desen - Font önbelleği tek bir defa taranır"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        # font_key (küçük harf) -> {"display_name": str, "regular": path, "bold": path, "italic": path, "bold_italic": path}
        self._family_map: Dict[str, Dict[str, Any]] = {}
        # Hızlı dosya arama için font adı -> tam yol
        self._file_lookup: Dict[str, str] = {}
        self._available_families: List[str] = []

        self._scan_fonts()

    def _scan_fonts(self):
        """Windows Kayıt Defteri ve kullanıcı font dizinlerini tarar"""
        windir = os.environ.get("WINDIR", r"C:\Windows")
        sys_fonts_dir = os.path.join(windir, "Fonts")
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        user_fonts_dir = os.path.join(local_appdata, r"Microsoft\Windows\Fonts") if local_appdata else ""

        # 1. Windows Registry (HKLM ve HKCU) Taraması
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
        ]

        for root_hkey, subkey_path in registry_keys:
            try:
                with winreg.OpenKey(root_hkey, subkey_path) as key:
                    count = winreg.QueryInfoKey(key)[1]
                    for i in range(count):
                        val_name, val_data, _ = winreg.EnumValue(key, i)
                        if not val_data:
                            continue
                        # Dosya tam yolu belirle
                        if os.path.isabs(val_data):
                            full_path = val_data
                        else:
                            full_path = os.path.join(sys_fonts_dir, val_data)
                            if not os.path.isfile(full_path) and user_fonts_dir:
                                alt_path = os.path.join(user_fonts_dir, val_data)
                                if os.path.isfile(alt_path):
                                    full_path = alt_path

                        if os.path.isfile(full_path) and full_path.lower().endswith((".ttf", ".otf", ".ttc")):
                            self._register_font_entry(val_name, full_path)
            except Exception:
                pass

        # 2. User AppData Font Klasörü Doğrudan Taraması (Kayıt defterinde yoksa bile yakala)
        if user_fonts_dir and os.path.isdir(user_fonts_dir):
            try:
                for fname in os.listdir(user_fonts_dir):
                    if fname.lower().endswith((".ttf", ".otf")):
                        full_path = os.path.join(user_fonts_dir, fname)
                        base_name = os.path.splitext(fname)[0]
                        self._register_font_entry(base_name, full_path)
            except Exception:
                pass

        # Sıralı font listesi oluştur
        self._available_families = sorted(
            list({data["display_name"] for data in self._family_map.values()}),
            key=lambda s: s.lower()
        )

    def _register_font_entry(self, raw_name: str, file_path: str):
        """Tek bir font kaydını stil ayrıştırması yaparak önbelleğe işler"""
        # (TrueType), (OpenType) gibi uzantıları temizle
        clean = re.sub(r"\s*\((TrueType|OpenType)\)", "", raw_name, flags=re.IGNORECASE).strip()
        lower_clean = clean.lower()

        # Stil tespiti (bold, italic)
        is_bold = "bold" in lower_clean or "kalın" in lower_clean
        is_italic = "italic" in lower_clean or "oblique" in lower_clean or "italik" in lower_clean

        # Aile adını stillerden arındır
        family_clean = re.sub(r"\b(bold|italic|oblique|regular|medium|light|black|semibold|heavy)\b", "", clean, flags=re.IGNORECASE).strip()
        # Çift boşlukları ve tireleri temizle
        family_clean = re.sub(r"[-_\s]+", " ", family_clean).strip()
        if not family_clean:
            family_clean = clean

        fam_key = family_clean.lower()
        if fam_key not in self._family_map:
            self._family_map[fam_key] = {
                "display_name": family_clean,
                "regular": None,
                "bold": None,
                "italic": None,
                "bold_italic": None,
            }

        slot = self._family_map[fam_key]
        if is_bold and is_italic:
            if not slot["bold_italic"]:
                slot["bold_italic"] = file_path
        elif is_bold:
            if not slot["bold"]:
                slot["bold"] = file_path
        elif is_italic:
            if not slot["italic"]:
                slot["italic"] = file_path
        else:
            if not slot["regular"]:
                slot["regular"] = file_path

        # Hızlı tekil arama haritası
        self._file_lookup[lower_clean] = file_path
        self._file_lookup[fam_key] = file_path

    def get_available_font_names(self) -> List[str]:
        """Kullanıcı arayüzü açılır menüsü için sistemde yüklü tüm font ailelerini döndürür"""
        return list(self._available_families)

    def resolve_font_from_pdf(self, doc, page, span_font_name: str) -> Dict[str, Any]:
        """
        PDF sayfasından okunan font ismini (Type3 veya gömülü subset olsa bile)
        FontDescriptor ve sistem fontlarıyla eşleştirir.
        """
        result = {
            "family_name": "Arial",
            "fontfile": None,
            "fontbuffer": None,
            "source": "fallback",
            "is_bold": False,
            "is_italic": False,
            "xref": None
        }

        if not doc or not page:
            return result

        clean_span = (span_font_name or "").strip()
        matched_real_name = None
        matched_xref = None
        matched_ftype = None

        # 1. Sayfadaki Font Nesnelerini (get_fonts) İncele
        page_fonts = page.get_fonts()
        for f in page_fonts:
            xref, ext, ftype, basefont, tag, enc = f
            candidate_name = basefont or ""

            # Type 3 veya BaseFont boş ise FontDescriptor üzerinden gerçek adı çek
            if not candidate_name or ftype == "Type3":
                try:
                    obj_str = doc.xref_object(xref)
                    m = re.search(r"/FontDescriptor\s+(\d+)\s+0\s+R", obj_str)
                    if m:
                        fd_obj = doc.xref_object(int(m.group(1)))
                        m_fam = re.search(r"/FontFamily\s*\((.*?)\)", fd_obj)
                        m_name = re.search(r"/FontName\s*/([^\s/>]+)", fd_obj)
                        if m_fam:
                            candidate_name = m_fam.group(1)
                        elif m_name:
                            candidate_name = m_name.group(1)
                except Exception:
                    pass

            # 6 karakterlik subset önekini temizle (Örn: BAAAAA+SparklyYarn -> SparklyYarn)
            if candidate_name and "+" in candidate_name:
                parts = candidate_name.split("+", 1)
                if len(parts[0]) == 6:
                    candidate_name = parts[1]

            # Eşleştirme Kontrolü
            is_match = False
            # Eğer span adı Unnamed-T3 ise ve bu font Type3 ise eşleşir
            if ("unnamed" in clean_span.lower() or "t3" in clean_span.lower()) and ftype == "Type3":
                is_match = True
            elif clean_span and candidate_name and (clean_span.lower() in candidate_name.lower() or candidate_name.lower() in clean_span.lower()):
                is_match = True

            if is_match:
                matched_real_name = candidate_name
                matched_xref = xref
                matched_ftype = ftype
                break

        # Font adı tespit edilemediyse doğrudan span adını temizle
        target_name = matched_real_name or clean_span
        if "+" in target_name:
            target_name = target_name.split("+", 1)[1]

        # PostScript stil takılarını ayıkla (Örn: ArialMT -> Arial, Consolas-Bold -> Consolas)
        cleaned_family = re.sub(r"MT$", "", target_name, flags=re.IGNORECASE)
        cleaned_family = re.sub(r"-(Bold|Italic|Regular|BoldItalic)", "", cleaned_family, flags=re.IGNORECASE).strip()

        result["family_name"] = cleaned_family or "Arial"
        result["xref"] = matched_xref

        # KADEME 1: Sistem & Kullanıcı Fontlarında Ara (En yüksek kalite TrueType)
        sys_file = self.resolve_file_for_family(cleaned_family)
        if sys_file and os.path.isfile(sys_file):
            result["fontfile"] = sys_file
            result["source"] = "system"
            return result

        # KADEME 2: Sistemde Yoksa ve PDF'e TTF Gömülüyse PDF'ten Çıkar
        if matched_xref:
            try:
                extracted = doc.extract_font(matched_xref)
                # extracted: (name, ext, type, buffer)
                if extracted and len(extracted) >= 4 and extracted[3] and len(extracted[3]) > 0:
                    result["fontbuffer"] = extracted[3]
                    result["source"] = "embedded"
                    return result
            except Exception:
                pass

        # KADEME 3: Varsayılan Sistem Fontuna (Arial) Düş
        windir = os.environ.get("WINDIR", r"C:\Windows")
        arial_path = os.path.join(windir, "Fonts", "arial.ttf")
        if os.path.isfile(arial_path):
            result["fontfile"] = arial_path
        result["source"] = "fallback"
        return result

    def resolve_file_for_family(self, family_name: str, is_bold: bool = False, is_italic: bool = False) -> Optional[str]:
        """Verilen font ailesi ve stil için sistemdeki en uygun .ttf/.otf dosya yolunu bulur"""
        if not family_name:
            return None

        search_key = family_name.lower().strip()
        search_clean = re.sub(r"[-_\s]+", " ", search_key).strip()

        # 1. Tam Eşleşme (_family_map)
        matched_slot = None
        for k, slot in self._family_map.items():
            if k == search_clean or k == search_key:
                matched_slot = slot
                break

        # 2. Kısmi Eşleşme (Örn: "Sparkly Yarn" araması "sparkly yarn regular" ile eşleşsin)
        if not matched_slot:
            for k, slot in self._family_map.items():
                if search_clean in k or k in search_clean:
                    matched_slot = slot
                    break

        if matched_slot:
            # İstenen stile göre dosya seçimi
            if is_bold and is_italic and matched_slot.get("bold_italic"):
                return matched_slot["bold_italic"]
            if is_bold and matched_slot.get("bold"):
                return matched_slot["bold"]
            if is_italic and matched_slot.get("italic"):
                return matched_slot["italic"]
            # Stil yoksa normal (regular) veya mevcut herhangi bir varyant
            for st in ("regular", "bold", "italic", "bold_italic"):
                if matched_slot.get(st):
                    return matched_slot[st]

        # 3. Hızlı doğrudan lookup
        if search_key in self._file_lookup:
            return self._file_lookup[search_key]

        return None


# Global Tekil Nesne
font_resolver = FontResolver()
