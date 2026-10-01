"""
Voice Engine for Hitasha: Hybrid Online/Offline Indian Voice & Speech Recognition.
- Online: Ultra-natural Indian Female voice (edge-tts: en-IN-NeerjaNeural) played via pygame.
- Offline: Automatic fallback to local Windows SAPI5 (pyttsx3).
- Non-blocking background worker queues for smooth 60fps desktop experience.
"""

import os
import sys
import time
import queue
import asyncio
import tempfile
import threading
import winsound
from PyQt6.QtCore import QObject, pyqtSignal

# Edge-TTS & PyGame for natural Indian Girl online voice
try:
    import edge_tts
    import pygame
    _EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    pygame = None
    _EDGE_TTS_AVAILABLE = False

# Offline Windows SAPI5 fallback
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

# Microphone STT
try:
    import speech_recognition as sr
except ImportError:
    sr = None


class VoiceEngine(QObject):
    """
    Manages non-blocking TTS and STT with seamless Online/Offline switching.
    """
    speech_started = pyqtSignal(str)
    speech_finished = pyqtSignal()
    listening_started = pyqtSignal()
    listening_finished = pyqtSignal()
    speech_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    INDIAN_VOICES = {
        "neerja": "en-IN-NeerjaNeural",     # Warm, expressive Indian female (Default)
        "kavya": "en-IN-KavyaNeural",       # Young, bubbly Indian female
        "ananya": "en-IN-AnanyaNeural",     # Friendly Indian female
    }

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = False
        self.stop_requested = False
        self._tts_thread = None
        self._stt_thread = None

        # Initialize pygame mixer once for low-latency audio playback
        if pygame:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception as e:
                print(f"[VoiceEngine] pygame.mixer init warning: {e}")

        # Start TTS background worker
        self._init_tts_worker()

    def _init_tts_worker(self):
        self._tts_thread = threading.Thread(target=self._tts_worker_loop, daemon=True)
        self._tts_thread.start()

    def _tts_worker_loop(self):
        """Worker thread executing speech synthesis without locking UI."""
        offline_engine = None
        if pyttsx3:
            try:
                offline_engine = pyttsx3.init()
            except Exception as e:
                print(f"[VoiceEngine] pyttsx3 offline init warning: {e}")

        while not self.stop_requested:
            try:
                item = self.speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if item is None:
                break

            text = item
            if not self.config.get("voice_enabled", True) or not text.strip():
                self.speech_queue.task_done()
                continue

            self.is_speaking = True
            self.speech_started.emit(text)

            spoken_successfully = False

            # 1. Attempt Online Natural Indian Girl Voice (Edge-TTS)
            if _EDGE_TTS_AVAILABLE and self.config.get("online_voice", True):
                try:
                    spoken_successfully = self._speak_online_edge(text)
                except Exception as e:
                    print(f"[VoiceEngine] Edge-TTS error, switching to offline fallback: {e}")
                    spoken_successfully = False

            # 2. Offline Fallback (pyttsx3) if Edge-TTS failed or offline mode forced
            if not spoken_successfully and offline_engine:
                try:
                    rate = self.config.get("voice_rate", 185)
                    volume = self.config.get("voice_volume", 1.0)
                    voice_id = self.config.get("voice_id", "")

                    offline_engine.setProperty("rate", rate)
                    offline_engine.setProperty("volume", volume)
                    if voice_id:
                        try:
                            offline_engine.setProperty("voice", voice_id)
                        except Exception:
                            pass
                    offline_engine.say(text)
                    offline_engine.runAndWait()
                    spoken_successfully = True
                except Exception as e:
                    print(f"[VoiceEngine] pyttsx3 offline error: {e}")

            self.is_speaking = False
            self.speech_finished.emit()
            self.speech_queue.task_done()

    def _speak_online_edge(self, text: str) -> bool:
        """Synthesize natural Indian female voice via edge-tts and play via pygame."""
        voice_key = self.config.get("indian_voice", "neerja")
        voice_name = self.INDIAN_VOICES.get(voice_key, "en-IN-NeerjaNeural")

        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        async def _gen():
            comm = edge_tts.Communicate(text, voice=voice_name, rate="+4%", pitch="+1Hz")
            await comm.save(temp_path)

        # Run async generation inside worker thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.wait_for(_gen(), timeout=8.0))
        finally:
            loop.close()

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return False

        # Play audio using pygame.mixer
        try:
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self.stop_requested and self.is_speaking:
                time.sleep(0.05)
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

        return True

    def speak(self, text: str):
        """Queue text to be spoken asynchronously."""
        if not self.config.get("voice_enabled", True):
            return
        # Clean markdown/HTML brackets for clean speech
        clean_text = text.replace("*", "").replace("#", "").replace("`", "")
        self.speech_queue.put(clean_text)

    def stop_speaking(self):
        """Immediately stop currently playing audio and clear queue."""
        self.is_speaking = False
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
        if pygame and pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.speech_finished.emit()

    def listen_once(self):
        """Trigger one-shot voice listening in background thread."""
        if self.is_listening or not sr:
            return

        self._stt_thread = threading.Thread(target=self._stt_worker, daemon=True)
        self._stt_thread.start()

    def _stt_worker(self):
        """Worker thread for microphone listening and recognition."""
        self.is_listening = True
        self.listening_started.emit()

        if self.config.get("sound_effects", True):
            try:
                winsound.Beep(1200, 100)
            except Exception:
                pass

        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            # Recognize with Google STT (standard free endpoint)
            text = recognizer.recognize_google(audio)
            if text:
                if self.config.get("sound_effects", True):
                    try:
                        winsound.Beep(1600, 80)
                    except Exception:
                        pass
                self.speech_recognized.emit(text)
        except sr.WaitTimeoutError:
            self.error_occurred.emit("Didn't hear anything, bestie! Try speaking a bit louder.")
        except sr.UnknownValueError:
            self.error_occurred.emit("Aree, couldn't catch that clearly! Mind saying it again?")
        except Exception as e:
            self.error_occurred.emit(f"Mic note: {str(e)[:40]}")
        finally:
            self.is_listening = False
            self.listening_finished.emit()

    def play_sound(self, sound_type: str = "pop"):
        """Play quick synthesized audio cue."""
        if not self.config.get("sound_effects", True):
            return

        def _sound():
            try:
                if sound_type == "pop":
                    winsound.Beep(1000, 60)
                elif sound_type == "chime":
                    winsound.Beep(800, 80)
                    winsound.Beep(1200, 100)
                elif sound_type == "ding":
                    winsound.Beep(1500, 150)
                elif sound_type == "roast":
                    winsound.Beep(600, 120)
                    winsound.Beep(450, 160)
                elif sound_type == "victory":
                    for freq in [523, 659, 784, 1046]:
                        winsound.Beep(freq, 90)
            except Exception:
                pass

        threading.Thread(target=_sound, daemon=True).start()

    @staticmethod
    def get_available_voices():
        """Retrieve list of available local SAPI5 voices for offline settings."""
        voices_list = []
        if not pyttsx3:
            return voices_list
        try:
            e = pyttsx3.init()
            voices = e.getProperty("voices")
            for v in voices:
                voices_list.append({"id": v.id, "name": v.name})
        except Exception:
            pass
        return voices_list
