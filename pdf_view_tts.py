"""
PDF Viewer - Türkçe Metin Seslendirme (TTS) Modülü
Microsoft Edge TTS kullanarak yüksek kaliteli Türkçe seslendirme
"""

import asyncio
import threading
import tempfile
import os
from typing import Optional, Callable


class TTSManager:
    """Türkçe metin seslendirme yöneticisi - edge-tts kullanır"""
    
    # Microsoft Türkçe sesleri
    VOICES = {
        "Emel (Kadın)": "tr-TR-EmelNeural",
        "Ahmet (Erkek)": "tr-TR-AhmetNeural"
    }
    
    # Hız ayarları (rate parametresi)
    SPEEDS = {
        "Yavaş": "-20%",
        "Normal": "+0%",
        "Hızlı": "+25%"
    }
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.is_playing = False
        self.stop_requested = False
        self.player_process = None
        self.temp_file = None
        self._playback_thread = None
        self._pygame_initialized = False
        self._lock = threading.Lock()
        
        # edge-tts modülünü kontrol et
        self._check_edge_tts()
        
        # print("DEBUG: TTS Manager oluşturuldu")
    
    def _check_edge_tts(self):
        """edge-tts modülünün yüklü olup olmadığını kontrol et"""
        try:
            import edge_tts
            self.edge_tts_available = True
            # print("DEBUG: edge-tts modülü mevcut")
        except ImportError:
            self.edge_tts_available = False
            print("DEBUG: edge-tts modülü bulunamadı - pip install edge-tts gerekli")
    
    def speak(self, text: str, voice: str, speed: str, callback: Optional[Callable] = None):
        """
        Metni Türkçe olarak seslendir
        
        Args:
            text: Seslendirilecek metin
            voice: Ses seçimi ("Emel (Kadın)" veya "Ahmet (Erkek)")
            speed: Hız ayarı ("Yavaş", "Normal", "Hızlı")
            callback: Durum güncellemesi için callback fonksiyonu
        """
        if not self.edge_tts_available:
            if callback:
                callback("Hata: edge-tts yüklü değil")
            return
        
        if self.is_playing:
            self.stop()
        
        self.stop_requested = False
        self.is_playing = True
        
        # Arka planda seslendirme başlat
        thread = threading.Thread(
            target=self._speak_async,
            args=(text, voice, speed, callback),
            daemon=True
        )
        thread.start()
        self._playback_thread = thread
        
        # print(f"DEBUG: Seslendirme başlatıldı - Ses: {voice}, Hız: {speed}")
    
    def _speak_async(self, text: str, voice: str, speed: str, callback: Optional[Callable]):
        """Asenkron seslendirme işlemi"""
        try:
            # Yeni event loop oluştur
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._generate_and_play(text, voice, speed, callback))
            finally:
                loop.close()
                
        except Exception as e:
            print(f"DEBUG: TTS async hatası: {e}")
            if callback:
                self._safe_callback(callback, f"Hata: {str(e)}")
        finally:
            self.is_playing = False
    
    async def _generate_and_play(self, text: str, voice: str, speed: str, callback: Optional[Callable]):
        """Ses dosyası oluştur ve oynat"""
        import edge_tts
        
        # Ses ve hız ayarlarını al
        voice_id = self.VOICES.get(voice, "tr-TR-EmelNeural")
        rate = self.SPEEDS.get(speed, "+0%")
        
        if callback:
            self._safe_callback(callback, "🔊 Ses oluşturuluyor...")
        
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            self.temp_file = f.name
        
        try:
            # edge-tts ile ses oluştur
            communicate = edge_tts.Communicate(text, voice_id, rate=rate)
            await communicate.save(self.temp_file)
            
            if self.stop_requested:
                self._cleanup_temp()
                if callback:
                    self._safe_callback(callback, "⏹️ Durduruldu")
                return
            
            if callback:
                self._safe_callback(callback, "🔊 Oynatılıyor...")
            
            # Ses dosyasını oynat
            await self._play_audio()
            
            if callback:
                if self.stop_requested:
                    self._safe_callback(callback, "⏹️ Durduruldu")
                else:
                    self._safe_callback(callback, "✓ Tamamlandı")
                    
        except Exception as e:
            print(f"DEBUG: TTS oluşturma hatası: {e}")
            if callback:
                self._safe_callback(callback, f"Hata: {str(e)}")
        finally:
            self._cleanup_temp()
    
    async def _play_audio(self):
        """Ses dosyasını oynat"""
        import subprocess
        import sys
        
        if not os.path.exists(self.temp_file):
            print("DEBUG: Geçici ses dosyası bulunamadı")
            return
        
        try:
            # Windows'ta pygame veya playsound kullan
            if sys.platform == 'win32':
                await self._play_with_pygame()
            else:
                # Linux/Mac için
                await self._play_with_subprocess()
                
        except Exception as e:
            print(f"DEBUG: Ses oynatma hatası: {e}")
            # Alternatif: winsound ile dene (sadece .wav destekler)
            raise
    
    async def _play_with_pygame(self):
        """Pygame ile oynat - thread-safe"""
        try:
            import pygame
            
            with self._lock:
                if self.stop_requested:
                    return
                
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self._pygame_initialized = True
                pygame.mixer.music.load(self.temp_file)
                pygame.mixer.music.play()
            
            # Çalma bitene kadar veya durdurulana kadar bekle
            while not self.stop_requested:
                try:
                    if not pygame.mixer.get_init() or not pygame.mixer.music.get_busy():
                        break
                except:
                    break
                await asyncio.sleep(0.1)
            
            # Güvenli temizlik
            with self._lock:
                try:
                    if pygame.mixer.get_init():
                        pygame.mixer.music.stop()
                        pygame.mixer.quit()
                    self._pygame_initialized = False
                except:
                    pass
            
            # print("DEBUG: Pygame ile seslendirme tamamlandı")
            
        except ImportError:
            print("DEBUG: pygame bulunamadı, playsound deneniyor...")
            await self._play_with_playsound()
    
    async def _play_with_playsound(self):
        """Playsound ile oynat"""
        try:
            from playsound import playsound
            
            # playsound senkron çalıştığı için thread'de çalıştır
            def play():
                if not self.stop_requested:
                    try:
                        playsound(self.temp_file)
                    except Exception as e:
                        print(f"DEBUG: playsound hatası: {e}")
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, play)
            
            # print("DEBUG: playsound ile seslendirme tamamlandı")
            
        except ImportError:
            print("DEBUG: playsound bulunamadı, Windows Media Player ile deneniyor...")
            await self._play_with_subprocess()
    
    async def _play_with_subprocess(self):
        """Sistem oynatıcısı ile oynat"""
        import subprocess
        import sys
        
        try:
            if sys.platform == 'win32':
                # Windows'ta varsayılan uygulama ile aç
                self.player_process = subprocess.Popen(
                    ['cmd', '/c', 'start', '/wait', '', self.temp_file],
                    shell=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux/Mac
                self.player_process = subprocess.Popen(
                    ['ffplay', '-nodisp', '-autoexit', self.temp_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Çalma bitene kadar bekle
            while self.player_process.poll() is None:
                if self.stop_requested:
                    self.player_process.terminate()
                    break
                await asyncio.sleep(0.1)
            
            # print("DEBUG: Subprocess ile seslendirme tamamlandı")
            
        except Exception as e:
            print(f"DEBUG: Subprocess oynatma hatası: {e}")
            raise
    
    def stop(self):
        """Seslendirmeyi durdur - thread-safe"""
        with self._lock:
            self.stop_requested = True
            
            # pygame durdurmayı dene - thread-safe
            try:
                import pygame
                if self._pygame_initialized and pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    # quit() çağırmıyoruz - kilitleme sorununa neden olabilir
                    # Bunun yerine sadece müziği durduruyoruz
                    self._pygame_initialized = False
            except Exception as e:
                print(f"DEBUG: Pygame durdurma hatası (yoksayıldı): {e}")
            
            # Subprocess'i durdur
            if self.player_process:
                try:
                    self.player_process.terminate()
                except:
                    pass
                self.player_process = None
            
            self.is_playing = False
        
        # cleanup'ı lock dışında yap
        # NOT: Temp dosyayı hemen silmiyoruz, oynatma thread'i kullanıyor olabilir
        # Thread bitince silinecek
        
        # print("DEBUG: TTS durduruldu")
    
    def _safe_callback(self, callback: Callable, message: str):
        """GUI thread'inde callback çağır"""
        try:
            self.parent_window.after(0, lambda: callback(message))
        except:
            pass
    
    def _cleanup_temp(self):
        """Geçici dosyayı temizle"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                # print(f"DEBUG: Geçici dosya silindi: {self.temp_file}")
            except Exception as e:
                print(f"DEBUG: Geçici dosya silinemedi: {e}")
        self.temp_file = None
    
    def _split_text_into_chunks(self, text: str, max_chars: int = 12000) -> list:
        """
        Metni belirli karakter sayısına göre cümle sonlarından böler.
        
        Args:
            text: Bölünecek metin
            max_chars: Maksimum karakter sayısı (varsayılan 12000)
            
        Returns:
            Metin parçaları listesi
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            # Maksimum karaktere kadar al
            end_pos = current_pos + max_chars
            
            if end_pos >= len(text):
                # Son parça
                chunks.append(text[current_pos:])
                break
            
            # Cümle sonu bul (., !, ?, :) - max_chars sonrasındaki ilk cümle sonu
            chunk_text = text[current_pos:end_pos]
            
            # Son cümle sonunu bul
            sentence_end = -1
            for i in range(len(chunk_text) - 1, max(0, len(chunk_text) - 500), -1):
                if chunk_text[i] in '.!?':
                    # Sonraki karakter boşluk veya satır sonu olmalı
                    if i + 1 >= len(chunk_text) or chunk_text[i + 1] in ' \n\t':
                        sentence_end = i + 1
                        break
            
            if sentence_end == -1:
                # Cümle sonu bulunamazsa, max_chars sonrasında cümle sonu ara
                extended_text = text[current_pos:min(len(text), end_pos + 500)]
                for i in range(max_chars, len(extended_text)):
                    if extended_text[i] in '.!?':
                        if i + 1 >= len(extended_text) or extended_text[i + 1] in ' \n\t':
                            sentence_end = i + 1
                            break
                
                if sentence_end == -1:
                    # Hala bulunamazsa, satır sonunda kes
                    for i in range(max_chars, len(extended_text)):
                        if extended_text[i] in '\n':
                            sentence_end = i + 1
                            break
                    
                    if sentence_end == -1:
                        # Son çare: max_chars'ta kes
                        sentence_end = max_chars
            
            chunks.append(text[current_pos:current_pos + sentence_end].strip())
            current_pos = current_pos + sentence_end
            
            # Boşlukları atla
            while current_pos < len(text) and text[current_pos] in ' \n\t':
                current_pos += 1
        
        # print(f"DEBUG: Metin {len(chunks)} parçaya bölündü")
        # for i, chunk in enumerate(chunks):
        #     print(f"DEBUG: Parça {i+1}: {len(chunk)} karakter")
        
        return chunks
    
    def save_as_mp3(self, text: str, voice: str, speed: str, output_path: str, callback: Optional[Callable] = None):
        """
        Metni MP3 dosyası olarak kaydet. 12.000 karakterden uzun metinler parçalara bölünür.
        
        Args:
            text: Seslendirilecek metin
            voice: Ses seçimi ("Emel (Kadın)" veya "Ahmet (Erkek)")
            speed: Hız ayarı ("Yavaş", "Normal", "Hızlı")
            output_path: Kaydedilecek MP3 dosya yolu
            callback: Durum güncellemesi için callback fonksiyonu
        """
        if not self.edge_tts_available:
            if callback:
                callback("Hata: edge-tts yüklü değil")
            return
        
        # Arka planda kaydetme başlat
        thread = threading.Thread(
            target=self._save_mp3_async,
            args=(text, voice, speed, output_path, callback),
            daemon=True
        )
        thread.start()
        
        # print(f"DEBUG: MP3 kaydetme başlatıldı - {output_path}")
    
    def _save_mp3_async(self, text: str, voice: str, speed: str, output_path: str, callback: Optional[Callable]):
        """Asenkron MP3 kaydetme işlemi - parçalama desteği ile"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Metni parçalara böl (12.000 karakter)
                chunks = self._split_text_into_chunks(text, 12000)
                
                if len(chunks) == 1:
                    # Tek parça - normal kaydet
                    loop.run_until_complete(self._generate_mp3(chunks[0], voice, speed, output_path, callback))
                else:
                    # Çoklu parça - numaralı dosyalar oluştur
                    base_path = output_path.rsplit('.', 1)[0]  # Uzantıyı kaldır
                    extension = output_path.rsplit('.', 1)[1] if '.' in output_path else 'mp3'
                    
                    for i, chunk in enumerate(chunks):
                        part_path = f"{base_path}-{i+1:02d}.{extension}"
                        if callback:
                            self._safe_callback(callback, f"🔊 Parça {i+1}/{len(chunks)} oluşturuluyor...")
                        loop.run_until_complete(self._generate_mp3_chunk(chunk, voice, speed, part_path))
                        # print(f"DEBUG: Parça {i+1} kaydedildi: {part_path}")
                    
                    if callback:
                        self._safe_callback(callback, f"✓ {len(chunks)} MP3 dosyası kaydedildi")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"DEBUG: MP3 kaydetme hatası: {e}")
            if callback:
                self._safe_callback(callback, f"Hata: {str(e)}")
    
    async def _generate_mp3_chunk(self, text: str, voice: str, speed: str, output_path: str):
        """Tek bir MP3 parçası oluştur (callback olmadan)"""
        import edge_tts
        
        voice_id = self.VOICES.get(voice, "tr-TR-EmelNeural")
        rate = self.SPEEDS.get(speed, "+0%")
        
        communicate = edge_tts.Communicate(text, voice_id, rate=rate)
        await communicate.save(output_path)
    
    async def _generate_mp3(self, text: str, voice: str, speed: str, output_path: str, callback: Optional[Callable]):
        """MP3 dosyası oluştur ve kaydet"""
        import edge_tts
        
        voice_id = self.VOICES.get(voice, "tr-TR-EmelNeural")
        rate = self.SPEEDS.get(speed, "+0%")
        
        if callback:
            self._safe_callback(callback, "🔊 MP3 oluşturuluyor...")
        
        try:
            communicate = edge_tts.Communicate(text, voice_id, rate=rate)
            await communicate.save(output_path)
            
            if callback:
                self._safe_callback(callback, f"✓ MP3 kaydedildi: {os.path.basename(output_path)}")
            
            # print(f"DEBUG: MP3 başarıyla kaydedildi: {output_path}")
            
        except Exception as e:
            print(f"DEBUG: MP3 oluşturma hatası: {e}")
            if callback:
                self._safe_callback(callback, f"Hata: {str(e)}")
    
    def __del__(self):
        """Yıkıcı - kaynakları temizle"""
        self.stop()
        self._cleanup_temp()


# Test fonksiyonu
if __name__ == "__main__":
    import tkinter as tk
    
    print("TTS Manager Test")
    print("=" * 50)
    
    # edge-tts kontrolü
    try:
        import edge_tts
        print("✓ edge-tts modülü yüklü")
    except ImportError:
        print("✗ edge-tts modülü bulunamadı")
        print("  Yüklemek için: pip install edge-tts")
    
    # pygame kontrolü
    try:
        import pygame
        print("✓ pygame modülü yüklü")
    except ImportError:
        print("✗ pygame modülü bulunamadı")
        print("  Yüklemek için: pip install pygame")
    
    print("\nKullanılabilir Türkçe sesler:")
    for name, voice_id in TTSManager.VOICES.items():
        print(f"  - {name}: {voice_id}")
