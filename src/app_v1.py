"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VOICE STUDIO  PRO  —  v1.0                               ║
║          Speech ↔ Text · Waveform Visualizer · Cross-Platform               ║
║                     Author: Abhishek Srivastava                             ║
║              Refactored & Enhanced by Voice Studio Pro Team                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

INSTALL:
    pip install SpeechRecognition pyttsx3 gTTS pyaudio pydub pygame

Linux extras:
    sudo apt install portaudio19-dev python3-tk espeak

macOS extras:
    brew install portaudio

KEYBOARD SHORTCUTS:
    Ctrl+R    → Start/Stop Recording
    Ctrl+T    → Speak/Stop Text
    Ctrl+S    → Save current output
    Ctrl+C    → Copy all (in STT tab)
    Ctrl+L    → Clear current tab
    Ctrl+,    → Open Settings
    Ctrl+H    → Show History
    F1        → Toggle tab (STT ↔ TTS)

FIXES IN THIS VERSION:
    - _tkinter.TclError on ttk.Scrollbar custom style (Python 3.12 + Windows)
    - All ttk styles registered AFTER theme_use() and before widget creation
    - Scrollbar style fallback: uses tk.Scrollbar on style failure
    - Safe engine probe: no pyttsx3 zombie threads
    - Queue poll runs on after() not threads to avoid Tcl re-entrancy
    - All widget .after() calls guarded against TclError on destroy
    - Settings dialog fully modal with grab_set / grab_release
    - Toast fade uses winfo_exists() guard
    - HistoryEntry uses __slots__ correctly
    - File-drop handler works on Windows (TkinterDnD not required — graceful)
    - pyttsx3 engine always del'd after use; no lingering COM references
    - Pygame mixer init failure is fully silent
    - All Path operations wrapped with specific exceptions
    - Font probing: falls back safely on every platform
"""

# ── Suppress noisy warnings BEFORE any imports ──────────────────────────────
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources.*")

# ── stdlib ───────────────────────────────────────────────────────────────────
import os
import sys
import io
import re
import math
import threading
import queue
import time
import json
import random
import tempfile
import datetime
import traceback
import subprocess
from pathlib import Path
from typing import Optional, Callable, List, Tuple

# ── Suppress pygame / tkinter init banners ───────────────────────────────────
_stderr_real, _stdout_real = sys.stderr, sys.stdout
sys.stderr = sys.stdout = io.StringIO()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

sys.stderr, sys.stdout = _stderr_real, _stdout_real

# ── Optional dependencies — graceful degradation ─────────────────────────────
def _try_import(name: str):
    try:
        return __import__(name), True
    except ImportError:
        return None, False

_sr_mod,   HAS_SR      = _try_import("speech_recognition")
_p3_mod,   HAS_PYTTSX3 = _try_import("pyttsx3")
_gtts_mod, HAS_GTTS    = _try_import("gtts")
_pydub_mod,HAS_PYDUB   = _try_import("pydub")

if HAS_SR:
    import speech_recognition as sr
if HAS_PYTTSX3:
    import pyttsx3
if HAS_GTTS:
    from gtts import gTTS
if HAS_PYDUB:
    from pydub import AudioSegment
    try:
        from pydub.playback import play as _pydub_play
        HAS_PYDUB_PLAY = True
    except Exception:
        HAS_PYDUB_PLAY = False

# ── Pygame (audio playback) ──────────────────────────────────────────────────
HAS_PYGAME = False
sys.stderr = sys.stdout = io.StringIO()
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_PYGAME = True
except Exception:
    pass
finally:
    sys.stderr, sys.stdout = _stderr_real, _stdout_real


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE     = "Voice Studio Pro"
APP_VERSION   = "1.0"
SAVE_DIR      = Path.home() / "VoiceStudio"
SETTINGS_FILE = SAVE_DIR / ".settings_v1.json"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette ───────────────────────────────────────────────────────────
C = {
    "bg":         "#050810",
    "bg2":        "#080c18",
    "surface":    "#0c1020",
    "surf1":      "#101525",
    "surf2":      "#141b2e",
    "surf3":      "#1a2238",
    "surf4":      "#202840",
    "surf5":      "#263048",
    "border":     "#1e2d4a",
    "border2":    "#263650",
    "border3":    "#304060",
    "blue":       "#3b82f6",
    "blue_dim":   "#1e40af",
    "blue_glow":  "#60a5fa",
    "cyan":       "#06b6d4",
    "cyan_dim":   "#0e7490",
    "green":      "#10b981",
    "green_dim":  "#065f46",
    "red":        "#ef4444",
    "red_dim":    "#7f1d1d",
    "orange":     "#f59e0b",
    "orange_dim": "#78350f",
    "purple":     "#8b5cf6",
    "purple_dim": "#4c1d95",
    "pink":       "#ec4899",
    "text":       "#e2e8f0",
    "text2":      "#94a3b8",
    "text3":      "#64748b",
    "text4":      "#475569",
    "white":      "#f8fafc",
    "success":    "#10b981",
    "warn":       "#f59e0b",
    "err":        "#ef4444",
    "info":       "#3b82f6",
    "glass":      "#ffffff08",
    "glass2":     "#ffffff12",
    "shimmer":    "#ffffff20",
}

TEXT_FILETYPES  = [("Text",     "*.txt"), ("Markdown", "*.md"),
                   ("Log",      "*.log"), ("All",      "*.*")]
AUDIO_FILETYPES = [("WAV",      "*.wav"), ("MP3",      "*.mp3"),
                   ("All",      "*.*")]

QUICK_SNIPPETS = [
    "Hello, world!",
    "Testing 1 2 3.",
    "Good morning!",
    "Thank you very much.",
    "The quick brown fox jumps over the lazy dog.",
    "How may I help you today?",
]

SUPPORTED_LANGS = [
    ("en",    "English"),    ("hi",    "Hindi"),
    ("es",    "Spanish"),    ("fr",    "French"),
    ("de",    "German"),     ("it",    "Italian"),
    ("pt",    "Portuguese"), ("ru",    "Russian"),
    ("zh-cn", "Chinese"),    ("ja",    "Japanese"),
    ("ko",    "Korean"),     ("ar",    "Arabic"),
    ("tr",    "Turkish"),    ("nl",    "Dutch"),
    ("pl",    "Polish"),     ("sv",    "Swedish"),
]

# ── Platform fonts (safe fallbacks) ─────────────────────────────────────────
def _resolve_font(candidates: List[str], fallback: str) -> str:
    """Return the first available font from candidates, else fallback."""
    try:
        available = set(tkfont.families())
        for f in candidates:
            if f in available:
                return f
    except Exception:
        pass
    return fallback

# Resolved at startup after Tk root exists
FONT_UI   = "TkDefaultFont"
FONT_MONO = "TkFixedFont"


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class Settings:
    """Thread-safe JSON-backed persistent settings."""

    DEFAULTS: dict = {
        "tts_engine":    "pyttsx3",
        "tts_rate":      175,
        "tts_volume":    1.0,
        "tts_voice_idx": 0,
        "tts_lang":      "en",
        "stt_energy":    300,
        "stt_pause":     0.8,
        "stt_timeout":   10,
        "stt_phrase":    30,
        "stt_mic_idx":   0,
        "save_dir":      str(SAVE_DIR),
        "auto_save":     False,
        "font_size":     11,
        "theme":         "dark",
        "show_waveform": True,
        "notifications": True,
        "append_mode":   True,
        "word_wrap":     True,
        "zoom":          100,
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._d    = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                with self._lock:
                    self._d.update(
                        {k: v for k, v in data.items() if k in self.DEFAULTS}
                    )
        except Exception:
            pass

    def save(self):
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            with self._lock:
                snapshot = dict(self._d)
            SETTINGS_FILE.write_text(
                json.dumps(snapshot, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def get(self, key, default=None):
        with self._lock:
            return self._d.get(
                key,
                default if default is not None else self.DEFAULTS.get(key)
            )

    def set(self, key, value):
        with self._lock:
            self._d[key] = value
        self.save()

    def __getattr__(self, k):
        if k.startswith("_"):
            raise AttributeError(k)
        return self.get(k)

    def __setattr__(self, k, v):
        if k.startswith("_"):
            object.__setattr__(self, k, v)
        else:
            self.set(k, v)

    def update_many(self, **kwargs):
        with self._lock:
            self._d.update(kwargs)
        self.save()


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _emit(cb: Optional[Callable], value):
    if cb is not None:
        try:
            cb(value)
        except Exception:
            pass

def _format_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"

def _word_count(text: str) -> Tuple[int, int]:
    clean = text.strip()
    words = len(clean.split()) if clean else 0
    return words, len(text)

def _ts_filename(prefix: str, ext: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"

def _readable_size(path: Path) -> str:
    try:
        b = path.stat().st_size
        if b < 1024:
            return f"{b} B"
        elif b < 1_048_576:
            return f"{b // 1024} KB"
        else:
            return f"{b / 1_048_576:.1f} MB"
    except Exception:
        return ""

def _safe_after(widget, ms: int, fn: Callable):
    """Schedule widget.after() only if the widget still exists."""
    try:
        if widget.winfo_exists():
            widget.after(ms, fn)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  TTS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class TTSEngine:
    """
    Production-grade TTS engine.

    DESIGN NOTES:
    - pyttsx3: A fresh engine is created per speak call; pyttsx3 cannot be
      safely reused across threads after runAndWait() returns.
    - gTTS: Temp-file → pygame → pydub → OS player fallback chain.
    - stop() is fully thread-safe via Event + engine reference under a lock.
    """

    def __init__(self, cfg: Settings):
        self.cfg         = cfg
        self._call_lock  = threading.Lock()
        self._eng_lock   = threading.Lock()
        self._active_eng = None
        self._stop_evt   = threading.Event()
        self._voices: list = []
        self._probe_voices()

    # ── Voice enumeration ────────────────────────────────────────────────────

    def _probe_voices(self):
        if not HAS_PYTTSX3:
            return
        try:
            eng = pyttsx3.init()
            self._voices = list(eng.getProperty("voices") or [])
            try:
                eng.stop()
            except Exception:
                pass
            del eng
        except Exception:
            self._voices = []

    @property
    def voices(self) -> list:
        return self._voices

    @property
    def voice_names(self) -> List[str]:
        return [f"{i}: {v.name}" for i, v in enumerate(self._voices)]

    # ── Engine factory ───────────────────────────────────────────────────────

    def _build_engine(self):
        eng = pyttsx3.init()
        rate   = max(50, min(400, int(self.cfg.tts_rate)))
        volume = max(0.0, min(1.0, float(self.cfg.tts_volume)))
        eng.setProperty("rate",   rate)
        eng.setProperty("volume", volume)
        if self._voices:
            idx = max(0, min(int(self.cfg.tts_voice_idx), len(self._voices) - 1))
            eng.setProperty("voice", self._voices[idx].id)
        return eng

    # ── Public API ───────────────────────────────────────────────────────────

    def speak_async(self, text: str,
                    on_start: Optional[Callable] = None,
                    on_done:  Optional[Callable] = None,
                    on_error: Optional[Callable] = None) -> threading.Thread:
        self._stop_evt.clear()
        t = threading.Thread(
            target=self._speak_worker,
            args=(text.strip(), on_start, on_done, on_error),
            daemon=True, name="TTS-speak")
        t.start()
        return t

    def save_async(self, text: str, path: str,
                   on_done:  Optional[Callable] = None,
                   on_error: Optional[Callable] = None) -> threading.Thread:
        self._stop_evt.clear()
        t = threading.Thread(
            target=self._save_worker,
            args=(text.strip(), path, on_done, on_error),
            daemon=True, name="TTS-save")
        t.start()
        return t

    def stop(self):
        self._stop_evt.set()
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        with self._eng_lock:
            eng = self._active_eng
        if eng is not None:
            try:
                eng.stop()
            except Exception:
                pass

    # ── Workers ──────────────────────────────────────────────────────────────

    def _speak_worker(self, text, on_start, on_done, on_error):
        with self._call_lock:
            try:
                if not text:
                    raise ValueError("No text provided to speak.")
                if on_start:
                    on_start()
                if self.cfg.tts_engine == "gtts" and HAS_GTTS:
                    self._gtts_speak(text)
                elif HAS_PYTTSX3:
                    self._pyttsx3_speak(text)
                else:
                    raise RuntimeError(
                        "No TTS engine available.\n"
                        "Install pyttsx3:  pip install pyttsx3\n"
                        "Or gTTS:          pip install gTTS"
                    )
                if not self._stop_evt.is_set() and on_done:
                    on_done()
            except Exception as exc:
                with self._eng_lock:
                    self._active_eng = None
                if not self._stop_evt.is_set() and on_error:
                    on_error(_format_error(exc))

    def _save_worker(self, text, path, on_done, on_error):
        with self._call_lock:
            try:
                if not text:
                    raise ValueError("No text provided to save.")
                p = Path(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                if self.cfg.tts_engine == "gtts" and HAS_GTTS:
                    out = p.with_suffix(".mp3")
                    gTTS(text=text, lang=self.cfg.tts_lang, slow=False).save(str(out))
                    if on_done:
                        on_done(str(out))
                elif HAS_PYTTSX3:
                    out = p.with_suffix(".wav")
                    eng = self._build_engine()
                    eng.save_to_file(text, str(out))
                    eng.runAndWait()
                    try:
                        eng.stop()
                    except Exception:
                        pass
                    del eng
                    if on_done:
                        on_done(str(out))
                else:
                    raise RuntimeError("No TTS engine available.")
            except Exception as exc:
                if on_error:
                    on_error(_format_error(exc))

    def _pyttsx3_speak(self, text: str):
        eng = self._build_engine()
        with self._eng_lock:
            self._active_eng = eng
        try:
            if not self._stop_evt.is_set():
                eng.say(text)
                eng.runAndWait()
        finally:
            with self._eng_lock:
                self._active_eng = None
            try:
                eng.stop()
            except Exception:
                pass
            del eng

    def _gtts_speak(self, text: str):
        fd, tmp = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            gTTS(text=text, lang=self.cfg.tts_lang, slow=False).save(tmp)
            if not self._stop_evt.is_set():
                self._play_file(tmp)
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

    def _play_file(self, path: str):
        if self._stop_evt.is_set():
            return
        if HAS_PYGAME:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if self._stop_evt.is_set():
                        pygame.mixer.music.stop()
                        return
                    time.sleep(0.05)
                return
            except Exception:
                pass
        if HAS_PYDUB and HAS_PYDUB_PLAY:
            try:
                _pydub_play(AudioSegment.from_file(path))
                return
            except Exception:
                pass
        # OS fallback
        try:
            if sys.platform == "win32":
                os.startfile(path)
                time.sleep(3)
            elif sys.platform == "darwin":
                subprocess.run(["afplay", path], check=True, capture_output=True)
            else:
                for player in ["mpg123", "mpg321", "ffplay", "aplay"]:
                    try:
                        subprocess.run([player, path], check=True,
                                       capture_output=True, timeout=60)
                        return
                    except (subprocess.CalledProcessError,
                            FileNotFoundError,
                            subprocess.TimeoutExpired):
                        continue
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  STT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class STTEngine:
    """Google Speech Recognition — microphone and file transcription."""

    def __init__(self, cfg: Settings):
        if not HAS_SR:
            raise RuntimeError(
                "SpeechRecognition is not installed.\n"
                "Run:  pip install SpeechRecognition pyaudio\n\n"
                "On Linux also:  sudo apt install portaudio19-dev"
            )
        self.cfg   = cfg
        self.rec   = sr.Recognizer()
        self._stop = threading.Event()
        self._refresh_params()

    def _refresh_params(self):
        self.rec.energy_threshold         = max(50, int(self.cfg.stt_energy))
        self.rec.pause_threshold          = max(0.1, float(self.cfg.stt_pause))
        self.rec.dynamic_energy_threshold = True

    @property
    def mic_available(self) -> bool:
        try:
            return len(sr.Microphone.list_microphone_names()) > 0
        except Exception:
            return False

    def list_mics(self) -> List[str]:
        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def transcribe_mic(self,
                       on_status: Optional[Callable] = None,
                       on_result: Optional[Callable] = None,
                       on_error:  Optional[Callable] = None) -> threading.Thread:
        self._stop.clear()
        self._refresh_params()
        t = threading.Thread(
            target=self._mic_worker,
            args=(on_status, on_result, on_error),
            daemon=True, name="STT-mic")
        t.start()
        return t

    def transcribe_file(self, path: str,
                        on_status: Optional[Callable] = None,
                        on_result: Optional[Callable] = None,
                        on_error:  Optional[Callable] = None) -> threading.Thread:
        self._stop.clear()
        t = threading.Thread(
            target=self._file_worker,
            args=(path, on_status, on_result, on_error),
            daemon=True, name="STT-file")
        t.start()
        return t

    def stop(self):
        self._stop.set()

    def _mic_worker(self, on_status, on_result, on_error):
        try:
            mic_idx    = int(self.cfg.stt_mic_idx)
            mics       = self.list_mics()
            mic_kwargs = ({"device_index": mic_idx}
                          if 0 <= mic_idx < len(mics) else {})
            with sr.Microphone(**mic_kwargs) as src:
                _emit(on_status, "Calibrating microphone…")
                self.rec.adjust_for_ambient_noise(src, duration=1.0)
                if self._stop.is_set():
                    return
                _emit(on_status, "🎙  Listening — speak now…")
                audio = self.rec.listen(
                    src,
                    timeout=max(1, int(self.cfg.stt_timeout)),
                    phrase_time_limit=max(5, int(self.cfg.stt_phrase))
                )
            if self._stop.is_set():
                return
            _emit(on_status, "⚙  Processing with Google Speech…")
            text = self.rec.recognize_google(audio)
            _emit(on_result, text)
        except sr.WaitTimeoutError:
            _emit(on_error,
                  "No speech detected within the timeout window.\n\n"
                  "Tips:\n"
                  "• Ensure your microphone is connected and unmuted\n"
                  "• Increase 'Listen Timeout' in Settings → STT\n"
                  "• Reduce ambient noise")
        except sr.UnknownValueError:
            _emit(on_error,
                  "Speech was unclear — could not transcribe.\n\n"
                  "Tips:\n"
                  "• Speak more clearly at normal volume\n"
                  "• Move closer to the microphone\n"
                  "• Reduce background noise")
        except sr.RequestError as e:
            _emit(on_error,
                  f"Google Speech API error:\n{e}\n\n"
                  "Check your internet connection.")
        except OSError as e:
            _emit(on_error,
                  f"Microphone access failed:\n{e}\n\n"
                  "Check OS microphone permissions.")
        except Exception as e:
            _emit(on_error, f"Unexpected error:\n{_format_error(e)}")

    def _file_worker(self, path, on_status, on_result, on_error):
        try:
            p = Path(path)
            if not p.exists():
                raise FileNotFoundError(f"File not found:\n{path}")
            if p.stat().st_size == 0:
                raise ValueError("Audio file is empty.")
            _emit(on_status, f"Loading  {p.name}…")
            with sr.AudioFile(str(p)) as src:
                audio = self.rec.record(src)
            if self._stop.is_set():
                return
            _emit(on_status, "⚙  Transcribing…")
            text = self.rec.recognize_google(audio)
            _emit(on_result, text)
        except (FileNotFoundError, ValueError) as e:
            _emit(on_error, str(e))
        except sr.UnknownValueError:
            _emit(on_error,
                  "Could not understand the audio file.\n\n"
                  "Ensure the file contains clear speech (WAV recommended).")
        except sr.RequestError as e:
            _emit(on_error, f"Google Speech API error:\n{e}")
        except Exception as e:
            _emit(on_error, f"File transcription error:\n{_format_error(e)}")


# ══════════════════════════════════════════════════════════════════════════════
#  TTK STYLE MANAGER
# ══════════════════════════════════════════════════════════════════════════════

# Sentinel: populated once styles are successfully registered
_SCROLLBAR_STYLE  = ""   # "V.TScrollbar" if registered, else ""
_NOTEBOOK_STYLE   = "clam"  # theme name
_NOTEBOOK_TAB_STYLE   = "Main.TNotebook"
_DLG_NOTEBOOK_STYLE   = "Dlg.TNotebook"

def _register_styles(root: tk.Tk) -> None:
    """
    Register all ttk styles in one place, AFTER the root Tk() is created.
    Falls back gracefully if any style registration fails.

    FIX: The original code tried to use ttk style names before calling
    theme_use(), and also used element names that don't exist in the 'clam'
    theme on Python 3.12/Windows, triggering _tkinter.TclError.
    """
    global _SCROLLBAR_STYLE, _NOTEBOOK_TAB_STYLE, _DLG_NOTEBOOK_STYLE

    s = ttk.Style(root)

    # Always set theme first
    try:
        s.theme_use("clam")
    except tk.TclError:
        try:
            s.theme_use("default")
        except tk.TclError:
            pass

    # ── Notebook (main window) ───────────────────────────────────────────────
    try:
        s.configure("Main.TNotebook",
                    background=C["bg"], borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("Main.TNotebook.Tab",
                    background=C["surf2"], foreground=C["text3"],
                    padding=[24, 12], font=(FONT_UI, 10, "bold"),
                    borderwidth=0)
        s.map("Main.TNotebook.Tab",
              background=[("selected", C["surf3"])],
              foreground=[("selected", C["blue_glow"])])
        _NOTEBOOK_TAB_STYLE = "Main.TNotebook"
    except tk.TclError:
        _NOTEBOOK_TAB_STYLE = "TNotebook"

    # ── Notebook (settings dialog) ───────────────────────────────────────────
    try:
        s.configure("Dlg.TNotebook",
                    background=C["bg"], borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("Dlg.TNotebook.Tab",
                    background=C["surf2"], foreground=C["text3"],
                    padding=[16, 8], font=(FONT_UI, 9, "bold"),
                    borderwidth=0)
        s.map("Dlg.TNotebook.Tab",
              background=[("selected", C["surf3"])],
              foreground=[("selected", C["blue"])])
        _DLG_NOTEBOOK_STYLE = "Dlg.TNotebook"
    except tk.TclError:
        _DLG_NOTEBOOK_STYLE = "TNotebook"

    # ── Scrollbar ────────────────────────────────────────────────────────────
    # FIX: The original "V.TScrollbar" style fails on Python 3.12 + Windows
    # because the element configuration is missing. We detect this and fall
    # back to the plain tk.Scrollbar approach instead.
    try:
        s.configure("V.TScrollbar",
                    background=C["surf3"],
                    troughcolor=C["surface"],
                    arrowcolor=C["text4"],
                    borderwidth=0,
                    relief="flat",
                    width=6)
        s.map("V.TScrollbar",
              background=[("active", C["border2"])])
        # Validate the style actually works by checking element presence
        # (this is the call that fails on 3.12 if elements aren't registered)
        s.layout("V.TScrollbar")   # raises TclError if broken
        _SCROLLBAR_STYLE = "V.TScrollbar"
    except tk.TclError:
        _SCROLLBAR_STYLE = ""  # will use tk.Scrollbar fallback

    # ── Combobox ─────────────────────────────────────────────────────────────
    try:
        s.configure("TCombobox",
                    fieldbackground=C["surf3"], background=C["surf3"],
                    foreground=C["text"], arrowcolor=C["blue"],
                    selectbackground=C["surf3"],
                    selectforeground=C["text"])
        s.map("TCombobox",
              fieldbackground=[("readonly", C["surf3"])])
        s.configure("D.TCombobox",
                    fieldbackground=C["surf3"], background=C["surf3"],
                    foreground=C["text"], arrowcolor=C["blue"],
                    selectbackground=C["surf3"],
                    selectforeground=C["text"])
        s.map("D.TCombobox",
              fieldbackground=[("readonly", C["surf3"])])
    except tk.TclError:
        pass


def _make_scrollbar(parent: tk.Widget, orient: str = "vertical",
                    command: Optional[Callable] = None) -> tk.Widget:
    """
    Create a scrollbar, using ttk.Scrollbar with our custom style when
    available, and falling back to a styled tk.Scrollbar otherwise.

    FIX: This factory is the key fix for the TclError crash. All scrollbars
    in the application must be created through this function.
    """
    if _SCROLLBAR_STYLE:
        sb = ttk.Scrollbar(parent, orient=orient, style=_SCROLLBAR_STYLE)
    else:
        sb = tk.Scrollbar(
            parent, orient=orient,
            bg=C["surf3"], troughcolor=C["surface"],
            activebackground=C["border2"],
            relief="flat", bd=0, width=8,
            elementborderwidth=0)
    if command is not None:
        sb.configure(command=command)
    return sb


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class AnimatedDot(tk.Canvas):
    """Pulsing animated indicator dot."""

    def __init__(self, parent, color_on: str, color_off: str = C["text4"],
                 size: int = 12, **kw):
        bg = kw.pop("bg", C["surf2"])
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0, bg=bg, **kw)
        self._c_on  = color_on
        self._c_off = color_off
        self._s     = size
        self._on    = False
        self._phase = 0
        self._job   = None
        self._draw(False)

    def _draw(self, bright: bool):
        self.delete("all")
        c   = self._s // 2
        r   = c - 2
        col = self._c_on if bright else self._c_off
        if bright:
            self.create_oval(c - r - 2, c - r - 2, c + r + 2, c + r + 2,
                             fill="", outline=col + "40", width=2)
        self.create_oval(c - r, c - r, c + r, c + r, fill=col, outline="")

    def start(self):
        self._on    = True
        self._phase = 0
        self._tick()

    def stop(self):
        self._on = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        try:
            self._draw(False)
        except tk.TclError:
            pass

    def _tick(self):
        if not self._on:
            return
        try:
            if not self.winfo_exists():
                return
            self._phase = (self._phase + 1) % 8
            self._draw(self._phase < 4)
            self._job = self.after(180, self._tick)
        except tk.TclError:
            self._on = False


class WaveformCanvas(tk.Canvas):
    """
    Animated waveform visualizer.
    Draws animated sine-wave bars during active speech/recording.
    """

    def __init__(self, parent, bars: int = 32, **kw):
        self._bg = kw.pop("bg", C["surf2"])
        super().__init__(parent, highlightthickness=0, bd=0,
                         bg=self._bg, **kw)
        self._bars   = bars
        self._active = False
        self._phase  = 0.0
        self._amps   = [0.0] * bars
        self._color  = C["blue"]
        self._job    = None
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def _redraw(self):
        try:
            if not self.winfo_exists():
                return
            self.delete("all")
            w = self.winfo_width()
            h = self.winfo_height()
            if w < 2 or h < 2:
                return
            bar_w  = w / self._bars
            center = h / 2
            max_a  = center * 0.85
            for i, amp in enumerate(self._amps):
                x1 = i * bar_w + 1
                x2 = x1 + bar_w - 2
                bh = max(2, amp * max_a)
                self.create_rectangle(x1, center - bh, x2, center + bh,
                                      fill=self._color, outline="", tags="bar")
                if amp > 0.05:
                    self.create_rectangle(x1, center - bh, x2, center - bh + 2,
                                          fill=C["white"], outline="", tags="cap")
        except tk.TclError:
            pass

    def start(self, color: str = C["blue"]):
        self._active = True
        self._color  = color
        self._animate()

    def stop(self):
        self._active = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self._decay()

    def _animate(self):
        if not self._active:
            return
        try:
            if not self.winfo_exists():
                return
            self._phase += 0.18
            for i in range(self._bars):
                t   = self._phase + i * 0.4
                amp = (0.4 * math.sin(t) +
                       0.3 * math.sin(t * 1.7 + 1.2) +
                       0.2 * math.sin(t * 2.9 + 0.5) +
                       0.1 * random.random())
                self._amps[i] = max(0.0, min(1.0, abs(amp)))
            self._redraw()
            self._job = self.after(40, self._animate)
        except tk.TclError:
            self._active = False

    def _decay(self):
        try:
            if not self.winfo_exists():
                return
            still = False
            for i in range(self._bars):
                self._amps[i] *= 0.82
                if self._amps[i] > 0.01:
                    still = True
            self._redraw()
            if still:
                self._job = self.after(40, self._decay)
        except tk.TclError:
            pass


class ToastNotification:
    """Non-blocking toast notification overlay."""

    def __init__(self, root: tk.Tk):
        self._root    = root
        self._queue   = []
        self._showing = False

    def show(self, message: str, kind: str = "info", duration: int = 2800):
        colors = {
            "info":    (C["blue"],   "ℹ"),
            "success": (C["green"],  "✓"),
            "warn":    (C["orange"], "⚠"),
            "error":   (C["red"],    "✕"),
        }
        color, icon = colors.get(kind, colors["info"])
        self._queue.append((f"{icon}  {message}", color, duration))
        if not self._showing:
            self._next()

    def _next(self):
        if not self._queue:
            self._showing = False
            return
        self._showing = True
        msg, color, duration = self._queue.pop(0)
        self._render(msg, color, duration)

    def _render(self, msg: str, color: str, duration: int):
        try:
            if not self._root.winfo_exists():
                return
            rx = self._root.winfo_rootx()
            ry = self._root.winfo_rooty()
            rw = self._root.winfo_width()
            rh = self._root.winfo_height()
        except tk.TclError:
            self._next()
            return

        try:
            win = tk.Toplevel(self._root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            try:
                win.attributes("-alpha", 0.0)
            except Exception:
                pass
            win.configure(bg=C["surf3"])

            frame = tk.Frame(win, bg=color, padx=0, pady=0)
            frame.pack(fill="both", expand=True)
            inner = tk.Frame(frame, bg=C["surf3"], padx=18, pady=10)
            inner.pack(fill="both", expand=True, padx=2, pady=2)
            tk.Label(inner, text=msg, bg=C["surf3"], fg=C["text"],
                     font=(FONT_UI, 9, "bold"), wraplength=340,
                     justify="left").pack()

            win.update_idletasks()
            w = max(win.winfo_reqwidth(), 260)
            h = win.winfo_reqheight()
            x = rx + rw - w - 20
            y = ry + rh - h - 50
            win.geometry(f"{w}x{h}+{x}+{y}")

            def _after_fade_in():
                try:
                    if win.winfo_exists():
                        win.after(duration, _start_fade_out)
                except tk.TclError:
                    pass

            def _start_fade_out():
                self._fade(win, 0.95, 0.0, 10, 15, _done)

            def _done():
                try:
                    if win.winfo_exists():
                        win.destroy()
                except tk.TclError:
                    pass
                self._next()

            self._fade(win, 0.0, 0.95, 10, 15, _after_fade_in)
        except tk.TclError:
            self._next()

    def _fade(self, win, frm, to, steps, delay, done=None):
        step  = (to - frm) / max(steps, 1)
        alpha = [frm]

        def _tick():
            alpha[0] = round(alpha[0] + step, 3)
            clamp = max(0.0, min(1.0, alpha[0]))
            try:
                if not win.winfo_exists():
                    if done:
                        done()
                    return
                win.attributes("-alpha", clamp)
            except tk.TclError:
                if done:
                    done()
                return

            remaining = abs((to - alpha[0]) / step) if step != 0 else 0
            if remaining > 1:
                try:
                    win.after(delay, _tick)
                except tk.TclError:
                    if done:
                        done()
            else:
                try:
                    win.attributes("-alpha", to)
                except tk.TclError:
                    pass
                if done:
                    done()

        _tick()


class RoundedButton(tk.Frame):
    """Flat button with hover animation."""

    def __init__(self, parent, text: str, command,
                 bg: str = C["surf3"], fg: str = C["text2"],
                 hover_bg: str = C["blue"], hover_fg: str = C["white"],
                 font_size: int = 9, bold: bool = True,
                 padx: int = 14, pady: int = 8, **kw):
        super().__init__(parent, bg=parent.cget("bg"), **kw)
        style = "bold" if bold else ""
        self._lbl = tk.Label(
            self, text=text, bg=bg, fg=fg,
            font=(FONT_UI, font_size, style),
            padx=padx, pady=pady, cursor="hand2")
        self._lbl.pack(fill="both", expand=True)
        self._bg, self._fg     = bg, fg
        self._hbg, self._hfg  = hover_bg, hover_fg
        self._cmd              = command
        for w in (self, self._lbl):
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def config_text(self, text: str, bg: str = None, fg: str = None):
        kw = {"text": text}
        if bg:
            kw["bg"]  = bg
            self._bg  = bg
        if fg:
            kw["fg"]  = fg
            self._fg  = fg
        try:
            self._lbl.config(**kw)
        except tk.TclError:
            pass

    def _on_enter(self, _e=None):
        try:
            self._lbl.config(bg=self._hbg, fg=self._hfg)
        except tk.TclError:
            pass

    def _on_leave(self, _e=None):
        try:
            self._lbl.config(bg=self._bg, fg=self._fg)
        except tk.TclError:
            pass

    def _on_click(self, _e=None):
        if self._cmd:
            try:
                self._cmd()
            except Exception:
                pass


class StatusBar(tk.Frame):
    """Animated bottom status bar with real-time clock."""

    def __init__(self, parent):
        super().__init__(parent, bg=C["surface"], height=30)
        self.pack_propagate(False)

        self._dot = AnimatedDot(self, C["green"], bg=C["surface"], size=10)
        self._dot.pack(side="left", padx=(14, 0), pady=10)

        self._msg = tk.Label(self, text="Initializing…",
                             bg=C["surface"], fg=C["text3"],
                             font=(FONT_UI, 9), anchor="w", padx=8)
        self._msg.pack(side="left", fill="x", expand=True)

        self._stats = tk.Label(self, text="",
                               bg=C["surface"], fg=C["text4"],
                               font=(FONT_MONO, 8), padx=14)
        self._stats.pack(side="right")

        self._clk = tk.Label(self, text="",
                             bg=C["surface"], fg=C["text3"],
                             font=(FONT_UI, 8), padx=14)
        self._clk.pack(side="right")
        self._tick()

    def set(self, text: str, color: str = C["text3"]):
        try:
            self._msg.config(text=text, fg=color)
            self._dot._c_on = color
            self._dot._draw(True)
        except tk.TclError:
            pass

    def set_stats(self, text: str):
        try:
            self._stats.config(text=text)
        except tk.TclError:
            pass

    def _tick(self):
        try:
            if self.winfo_exists():
                self._clk.config(
                    text=datetime.datetime.now().strftime("%H:%M:%S"))
                self.after(1000, self._tick)
        except tk.TclError:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class SettingsDialog(tk.Toplevel):

    def __init__(self, root, cfg: Settings,
                 tts: Optional[TTSEngine],
                 stt: Optional[STTEngine]):
        super().__init__(root)
        self.cfg, self.tts, self.stt = cfg, tts, stt
        self.title("Settings — Voice Studio Pro")
        self.geometry("560x580")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.transient(root)
        self.grab_set()
        self._build()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    # ── Layout helpers ───────────────────────────────────────────────────────

    def _section(self, parent, title: str) -> tk.Frame:
        lf = tk.LabelFrame(parent, text=f"  {title}  ",
                           bg=C["surf1"], fg=C["blue"],
                           font=(FONT_UI, 9, "bold"),
                           bd=1, relief="flat", labelanchor="nw",
                           padx=12, pady=8)
        lf.pack(fill="x", padx=16, pady=5)
        return lf

    def _row(self, parent, label: str) -> tk.Frame:
        r = tk.Frame(parent, bg=C["surf1"])
        r.pack(fill="x", pady=3)
        tk.Label(r, text=label, width=22, anchor="w",
                 bg=C["surf1"], fg=C["text2"],
                 font=(FONT_UI, 9)).pack(side="left")
        return r

    def _scale(self, parent, var, lo, hi, res=1) -> tk.Scale:
        return tk.Scale(
            parent, variable=var, from_=lo, to=hi, resolution=res,
            orient="horizontal", bg=C["surf1"], fg=C["text2"],
            troughcolor=C["border"], activebackground=C["blue"],
            highlightthickness=0, bd=0, sliderrelief="flat", length=200)

    def _combo(self, parent, var, values, width=28) -> ttk.Combobox:
        return ttk.Combobox(parent, textvariable=var, values=values,
                            state="readonly", width=width, style="D.TCombobox")

    # ── Build ────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = tk.Frame(self, bg=C["surf1"], height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  Settings",
                 bg=C["surf1"], fg=C["text"],
                 font=(FONT_UI, 13, "bold")).pack(
                     side="left", padx=18, pady=14)
        tk.Label(hdr, text="Voice Studio Pro",
                 bg=C["surf1"], fg=C["text4"],
                 font=(FONT_UI, 9)).pack(side="right", padx=18)
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        nb = ttk.Notebook(self, style=_DLG_NOTEBOOK_STYLE)
        nb.pack(fill="both", expand=True)

        for label, builder in [
            ("  🔊  TTS  ",     self._tab_tts),
            ("  🎙  STT  ",     self._tab_stt),
            ("  🎨  General  ", self._tab_general),
        ]:
            f = tk.Frame(nb, bg=C["surf1"])
            nb.add(f, text=label)
            builder(f)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        bf = tk.Frame(self, bg=C["bg"], pady=10)
        bf.pack(fill="x", padx=16)
        RoundedButton(bf, "✓  Save & Apply", self._save,
                      hover_bg=C["green"]).pack(side="right", padx=4)
        RoundedButton(bf, "✕  Cancel", self._close,
                      hover_bg=C["red"]).pack(side="right", padx=4)
        RoundedButton(bf, "↺  Reset Defaults", self._reset,
                      hover_bg=C["orange"]).pack(side="left", padx=4)

    def _tab_tts(self, tab):
        sec1 = self._section(tab, "Engine")
        r1   = self._row(sec1, "TTS Engine:")
        opts = ["pyttsx3  (offline)"]
        if HAS_GTTS:
            opts.append("gTTS  (online / Google)")
        self._v_eng = tk.StringVar(value=(
            "gTTS  (online / Google)"
            if self.cfg.tts_engine == "gtts" else "pyttsx3  (offline)"))
        self._combo(r1, self._v_eng, opts).pack(side="left")

        sec2  = self._section(tab, "Voice  (pyttsx3 only)")
        r2    = self._row(sec2, "Voice:")
        names = (self.tts.voice_names if self.tts else []) or ["(none detected)"]
        idx   = min(max(0, int(self.cfg.tts_voice_idx)), len(names) - 1)
        self._v_voice = tk.StringVar(value=names[idx])
        self._combo(r2, self._v_voice, names).pack(side="left")

        sec3 = self._section(tab, "Speech Parameters")
        r3   = self._row(sec3, "Rate (wpm):")
        self._v_rate = tk.IntVar(value=int(self.cfg.tts_rate))
        self._scale(r3, self._v_rate, 50, 400).pack(side="left")
        tk.Label(r3, textvariable=self._v_rate,
                 bg=C["surf1"], fg=C["blue"],
                 font=(FONT_MONO, 9), width=4).pack(side="left", padx=4)

        r4 = self._row(sec3, "Volume:")
        self._v_vol = tk.DoubleVar(value=float(self.cfg.tts_volume))
        self._scale(r4, self._v_vol, 0.0, 1.0, res=0.05).pack(side="left")

        sec4 = self._section(tab, "gTTS Language  (online only)")
        r5   = self._row(sec4, "Language:")
        lang_opts = [f"{code}  —  {name}" for code, name in SUPPORTED_LANGS]
        cur_lang  = self.cfg.tts_lang
        cur_str   = next((f"{c}  —  {n}" for c, n in SUPPORTED_LANGS
                          if c == cur_lang), lang_opts[0])
        self._v_lang = tk.StringVar(value=cur_str)
        self._combo(r5, self._v_lang, lang_opts, width=22).pack(side="left")

    def _tab_stt(self, tab):
        sec1 = self._section(tab, "Microphone Device")
        r1   = self._row(sec1, "Device:")
        mics = ([f"{i}: {m}" for i, m in
                 enumerate(self.stt.list_mics() if self.stt else [])]
                or ["(none detected)"])
        self._v_mic = tk.StringVar(value=mics[0])
        self._combo(r1, self._v_mic, mics).pack(side="left")

        sec2 = self._section(tab, "Recognition Parameters")
        params = [
            ("Energy threshold:",    "stt_energy",  50,  4000, 10),
            ("Pause threshold (s):", "stt_pause",   0.3, 3.0,  0.1),
            ("Listen timeout (s):",  "stt_timeout", 2,   120,  1),
            ("Phrase limit (s):",    "stt_phrase",  3,   180,  1),
        ]
        self._stt_vars = {}
        for label, key, lo, hi, res in params:
            r   = self._row(sec2, label)
            typ = tk.DoubleVar if isinstance(res, float) else tk.IntVar
            val = (float(getattr(self.cfg, key)) if isinstance(res, float)
                   else int(getattr(self.cfg, key)))
            var = typ(value=val)
            self._stt_vars[key] = var
            self._scale(r, var, lo, hi, res).pack(side="left")
            tk.Label(r, textvariable=var,
                     bg=C["surf1"], fg=C["blue"],
                     font=(FONT_MONO, 9), width=6).pack(side="left", padx=4)

    def _tab_general(self, tab):
        sec1 = self._section(tab, "Behaviour")
        self._v_auto   = tk.BooleanVar(value=bool(self.cfg.auto_save))
        self._v_notify = tk.BooleanVar(value=bool(self.cfg.notifications))
        self._v_wrap   = tk.BooleanVar(value=bool(self.cfg.word_wrap))
        for text, var in [
            ("Auto-save each transcription to ~/VoiceStudio/", self._v_auto),
            ("Show toast notifications",                        self._v_notify),
            ("Word wrap in editors",                            self._v_wrap),
        ]:
            tk.Checkbutton(sec1, text=text, variable=var,
                           bg=C["surf1"], fg=C["text2"],
                           activebackground=C["surf1"],
                           selectcolor=C["blue"],
                           font=(FONT_UI, 9),
                           cursor="hand2").pack(anchor="w", pady=2)

        sec2 = self._section(tab, "Display")
        rf   = self._row(sec2, "Editor font size:")
        self._v_font = tk.IntVar(value=int(self.cfg.font_size))
        self._scale(rf, self._v_font, 8, 24).pack(side="left")
        tk.Label(rf, textvariable=self._v_font,
                 bg=C["surf1"], fg=C["blue"],
                 font=(FONT_MONO, 9), width=4).pack(side="left", padx=4)

        sec3 = self._section(tab, "Save Directory")
        rf2  = tk.Frame(sec3, bg=C["surf1"])
        rf2.pack(fill="x", pady=4)
        self._v_savedir = tk.StringVar(value=self.cfg.save_dir)
        tk.Entry(rf2, textvariable=self._v_savedir,
                 bg=C["surf3"], fg=C["text2"],
                 insertbackground=C["text"], relief="flat",
                 font=(FONT_MONO, 8),
                 highlightthickness=1,
                 highlightbackground=C["border"]).pack(
                     side="left", fill="x", expand=True, ipady=4, padx=(0, 6))
        RoundedButton(rf2, "Browse…", self._browse_dir,
                      hover_bg=C["blue"], pady=4).pack(side="left")

    def _browse_dir(self):
        p = filedialog.askdirectory(
            title="Choose Save Directory",
            initialdir=self._v_savedir.get(),
            parent=self)
        if p:
            self._v_savedir.set(p)

    def _save(self):
        eng_raw = self._v_eng.get()
        self.cfg.tts_engine = "gtts" if "gTTS" in eng_raw else "pyttsx3"
        try:
            self.cfg.tts_voice_idx = int(self._v_voice.get().split(":")[0])
        except Exception:
            self.cfg.tts_voice_idx = 0
        self.cfg.tts_rate   = int(self._v_rate.get())
        self.cfg.tts_volume = round(float(self._v_vol.get()), 2)
        lang_raw = self._v_lang.get().split("  —  ")[0].strip()
        self.cfg.tts_lang   = lang_raw
        for key, var in self._stt_vars.items():
            self.cfg.set(key, round(var.get(), 3))
        self.cfg.auto_save     = bool(self._v_auto.get())
        self.cfg.notifications = bool(self._v_notify.get())
        self.cfg.word_wrap     = bool(self._v_wrap.get())
        self.cfg.font_size     = int(self._v_font.get())
        save_dir = self._v_savedir.get().strip()
        if save_dir:
            self.cfg.save_dir = save_dir
        self.cfg.save()
        self._close()

    def _reset(self):
        if messagebox.askyesno("Reset Settings",
                               "Reset all settings to defaults?",
                               parent=self):
            self.cfg.update_many(**Settings.DEFAULTS)
            self._close()


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION HISTORY
# ══════════════════════════════════════════════════════════════════════════════

class HistoryEntry:
    __slots__ = ("kind", "text", "ts")

    def __init__(self, kind: str, text: str):
        self.kind = kind
        self.text = text
        self.ts   = datetime.datetime.now()

    def fmt_time(self) -> str:
        return self.ts.strftime("%H:%M:%S")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class VoiceStudioPro(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.geometry("1040x720")
        self.minsize(860, 620)
        self.configure(bg=C["bg"])
        self._set_icon()

        # Resolve fonts now that Tk exists
        global FONT_UI, FONT_MONO
        if sys.platform == "win32":
            FONT_UI   = _resolve_font(["Segoe UI", "Tahoma", "Arial"], "TkDefaultFont")
            FONT_MONO = _resolve_font(["Cascadia Code", "Consolas", "Courier New"], "TkFixedFont")
        elif sys.platform == "darwin":
            FONT_UI   = _resolve_font(["SF Pro Display", "Helvetica Neue", "Helvetica"], "TkDefaultFont")
            FONT_MONO = _resolve_font(["Menlo", "Monaco", "Courier"], "TkFixedFont")
        else:
            FONT_UI   = _resolve_font(["Ubuntu", "DejaVu Sans", "Liberation Sans"], "TkDefaultFont")
            FONT_MONO = _resolve_font(["Ubuntu Mono", "DejaVu Sans Mono", "Liberation Mono"], "TkFixedFont")

        # Register all TTK styles (must be after Tk() + font resolution)
        _register_styles(self)

        # ── Core state ──────────────────────────────────────────────────────
        self.cfg  = Settings()
        self._q   = queue.Queue()
        self._log: List[HistoryEntry] = []

        self._rec_active = False
        self._spk_active = False

        self._tts: Optional[TTSEngine] = None
        self._stt: Optional[STTEngine] = None
        self._tts_err = self._stt_err  = ""

        self._session_words   = 0
        self._session_entries = 0

        _PH          = "Type or paste text here to convert to speech…"
        self._ph_text = _PH
        self._ph_on   = True

        # ── Init ────────────────────────────────────────────────────────────
        self._init_engines()
        self._build_ui()
        self._bind_keys()
        self._toast = ToastNotification(self)
        self._poll()

        self.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.after(600, self._startup_banner)

    # ── Icon ────────────────────────────────────────────────────────────────

    def _set_icon(self):
        try:
            icon = tk.PhotoImage(data=(
                "R0lGODlhEAAQAPEAAAAAAHCw8P///wAAACH5BAEAAAAALAAAAAAQABAAAAI"
                "jhI+py+0Po5y02ouz3rz7D4biSJbmiabqyrbuC8fyTNf2UQAAOw=="))
            self.iconphoto(True, icon)
        except Exception:
            pass

    # ── Engine init ──────────────────────────────────────────────────────────

    def _init_engines(self):
        try:
            self._tts = TTSEngine(self.cfg)
        except Exception as e:
            self._tts_err = _format_error(e)
        try:
            self._stt = STTEngine(self.cfg)
        except Exception as e:
            self._stt_err = _format_error(e)

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_tabs()
        self._build_statusbar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C["surf1"], height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        sep = tk.Frame(hdr, bg=C["border"], height=1)
        sep.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        lg = tk.Frame(hdr, bg=C["surf1"])
        lg.pack(side="left", fill="y", padx=20)
        dot = tk.Canvas(lg, width=14, height=14, highlightthickness=0,
                        bd=0, bg=C["surf1"])
        dot.pack(side="left", pady=23)
        dot.create_oval(2, 2, 12, 12, fill=C["blue"],
                        outline=C["blue_glow"], width=1)
        dot.create_oval(5, 5, 9, 9, fill=C["white"], outline="")
        tk.Label(lg, text="  Voice Studio",
                 bg=C["surf1"], fg=C["text"],
                 font=(FONT_UI, 14, "bold")).pack(side="left", pady=18)
        tk.Label(lg, text=" Pro",
                 bg=C["surf1"], fg=C["blue"],
                 font=(FONT_UI, 10, "bold")).pack(side="left", pady=18)
        tk.Label(lg, text=f"  v{APP_VERSION}",
                 bg=C["surf1"], fg=C["text4"],
                 font=(FONT_UI, 8)).pack(side="left", pady=20)

        pills = tk.Frame(hdr, bg=C["surf1"])
        pills.pack(side="left", fill="y", padx=16)
        self._tts_pill = tk.Label(pills, text="● TTS: …",
                                  bg=C["surf2"], fg=C["text4"],
                                  font=(FONT_UI, 8), padx=10, pady=3)
        self._tts_pill.pack(side="left", padx=3, pady=20)
        self._stt_pill = tk.Label(pills, text="● STT: …",
                                  bg=C["surf2"], fg=C["text4"],
                                  font=(FONT_UI, 8), padx=10, pady=3)
        self._stt_pill.pack(side="left", padx=3, pady=20)

        right = tk.Frame(hdr, bg=C["surf1"])
        right.pack(side="right", fill="y", padx=14)
        for label, cmd, hbg in [
            ("⏱  History",  self._show_history,  C["purple"]),
            ("⚙  Settings", self._open_settings, C["blue"]),
        ]:
            RoundedButton(right, label, cmd,
                          hover_bg=hbg, pady=6).pack(
                              side="right", padx=3, pady=16)

    def _build_tabs(self):
        self._nb = ttk.Notebook(self, style=_NOTEBOOK_TAB_STYLE)
        self._nb.pack(fill="both", expand=True)
        self._nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self._stt_frame = tk.Frame(self._nb, bg=C["bg"])
        self._tts_frame = tk.Frame(self._nb, bg=C["bg"])
        self._nb.add(self._stt_frame, text="   🎙  Speech → Text   ")
        self._nb.add(self._tts_frame, text="   🔊  Text → Speech   ")

        self._build_stt_tab(self._stt_frame)
        self._build_tts_tab(self._tts_frame)

    def _build_statusbar(self):
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")
        self._status = StatusBar(self)
        self._status.pack(fill="x", side="bottom")

    # ══════════════════════════════════════════════════════════════════════════
    #  STT TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_stt_tab(self, parent):
        src_bar = tk.Frame(parent, bg=C["surf1"], height=48)
        src_bar.pack(fill="x"); src_bar.pack_propagate(False)
        tk.Frame(src_bar, bg=C["border"], height=1).pack(fill="x", side="bottom")

        tk.Label(src_bar, text="Source:",
                 bg=C["surf1"], fg=C["text3"],
                 font=(FONT_UI, 9, "bold")).pack(side="left", padx=(16, 6))

        self._stt_src = tk.StringVar(value="mic")
        for val, icon, lbl in [("mic",  "🎤", "Microphone"),
                                ("file", "📂", "Audio File")]:
            tk.Radiobutton(
                src_bar, text=f"{icon}  {lbl}",
                variable=self._stt_src, value=val,
                command=self._stt_src_changed,
                bg=C["surf1"], fg=C["text2"],
                activebackground=C["surf1"],
                selectcolor=C["blue"],
                font=(FONT_UI, 9), cursor="hand2").pack(side="left", padx=10)

        self._stt_file_bar = tk.Frame(src_bar, bg=C["surf1"])
        self._stt_file_var = tk.StringVar()
        self._stt_file_entry = tk.Entry(
            self._stt_file_bar, textvariable=self._stt_file_var,
            width=34, bg=C["surf2"], fg=C["text2"],
            insertbackground=C["text"], relief="flat",
            font=(FONT_UI, 9),
            highlightthickness=1, highlightbackground=C["border"])
        self._stt_file_entry.pack(side="left", padx=(10, 4), ipady=4)
        RoundedButton(self._stt_file_bar, "Browse…", self._stt_browse,
                      hover_bg=C["blue"], pady=4).pack(side="left")

        body = tk.Frame(parent, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=12)
        self._build_stt_sidebar(body)
        self._build_stt_main(body)

    def _build_stt_sidebar(self, parent):
        side = tk.Frame(parent, bg=C["surf2"], width=220)
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)

        inner = tk.Frame(side, bg=C["surf2"])
        inner.pack(fill="both", expand=True, padx=12, pady=14)

        srow = tk.Frame(inner, bg=C["surf2"])
        srow.pack(fill="x", pady=(0, 10))
        self._rec_dot = AnimatedDot(srow, C["red"], bg=C["surf2"])
        self._rec_dot.pack(side="left")
        self._stt_status_lbl = tk.Label(srow, text="Idle",
                                         bg=C["surf2"], fg=C["text4"],
                                         font=(FONT_UI, 9))
        self._stt_status_lbl.pack(side="left", padx=6)

        self._btn_rec = RoundedButton(
            inner, "⏺  Start Recording", self._toggle_record,
            hover_bg=C["red"], hover_fg=C["white"], font_size=9)
        self._btn_rec.pack(fill="x", pady=(0, 4))

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        tk.Label(inner, text="WAVEFORM", bg=C["surf2"], fg=C["text4"],
                 font=(FONT_UI, 7, "bold")).pack(anchor="w", pady=(0, 4))
        self._stt_wave = WaveformCanvas(inner, bars=24,
                                         bg=C["surf3"], height=48)
        self._stt_wave.pack(fill="x")

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        tk.Label(inner, text="SAVE FORMAT", bg=C["surf2"], fg=C["text4"],
                 font=(FONT_UI, 7, "bold")).pack(anchor="w", pady=(0, 4))
        self._stt_fmt = tk.StringVar(value="txt")
        for ext, lbl in [("txt", "Plain Text   .txt"),
                          ("md",  "Markdown     .md "),
                          ("log", "Log File     .log")]:
            tk.Radiobutton(
                inner, text=lbl, variable=self._stt_fmt, value=ext,
                bg=C["surf2"], fg=C["text2"],
                activebackground=C["surf2"], selectcolor=C["blue"],
                font=(FONT_MONO, 9), cursor="hand2").pack(anchor="w", pady=2)

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        for label, cmd, hbg in [
            ("💾  Save Transcript", self._stt_save,  C["green"]),
            ("📋  Copy All",        self._stt_copy,  C["blue"]),
            ("🗑  Clear",           self._stt_clear, C["text4"]),
        ]:
            RoundedButton(inner, label, cmd,
                          hover_bg=hbg, pady=6).pack(fill="x", pady=2)

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        self._stt_append = tk.BooleanVar(value=bool(self.cfg.append_mode))
        tk.Checkbutton(inner, text="Append results",
                       variable=self._stt_append,
                       bg=C["surf2"], fg=C["text3"],
                       activebackground=C["surf2"],
                       selectcolor=C["blue"],
                       font=(FONT_UI, 9), cursor="hand2").pack(anchor="w")

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        tk.Label(inner, text="SESSION STATS", bg=C["surf2"], fg=C["text4"],
                 font=(FONT_UI, 7, "bold")).pack(anchor="w", pady=(0, 4))
        self._stt_stats_lbl = tk.Label(
            inner, text="0 transcriptions\n0 total words",
            bg=C["surf2"], fg=C["text4"],
            font=(FONT_UI, 8), justify="left", anchor="w")
        self._stt_stats_lbl.pack(anchor="w")

    def _build_stt_main(self, parent):
        main = tk.Frame(parent, bg=C["bg"])
        main.pack(fill="both", expand=True)

        hrow = tk.Frame(main, bg=C["bg"])
        hrow.pack(fill="x", pady=(0, 8))
        tk.Label(hrow, text="Transcription Output",
                 bg=C["bg"], fg=C["text"],
                 font=(FONT_UI, 12, "bold")).pack(side="left")
        self._stt_wc = tk.Label(hrow, text="0 words · 0 chars",
                                  bg=C["bg"], fg=C["text4"],
                                  font=(FONT_UI, 9))
        self._stt_wc.pack(side="right")

        search_row = tk.Frame(main, bg=C["bg"])
        search_row.pack(fill="x", pady=(0, 6))
        tk.Label(search_row, text="🔍",
                 bg=C["bg"], fg=C["text4"],
                 font=(FONT_UI, 10)).pack(side="left")
        self._stt_search = tk.Entry(
            search_row, bg=C["surf2"], fg=C["text2"],
            insertbackground=C["text"], relief="flat",
            font=(FONT_UI, 9), width=30,
            highlightthickness=1, highlightbackground=C["border"])
        self._stt_search.pack(side="left", padx=6, ipady=3)
        self._stt_search.bind("<KeyRelease>",
                              lambda e: self._stt_search_text())
        RoundedButton(search_row, "Find", self._stt_search_text,
                      hover_bg=C["blue"], pady=3,
                      font_size=8).pack(side="left", padx=2)
        RoundedButton(search_row, "Clear Search",
                      lambda: [self._stt_search.delete(0, "end"),
                               self._stt_clear_highlight()],
                      hover_bg=C["text4"], pady=3,
                      font_size=8).pack(side="left", padx=2)

        outer = tk.Frame(main, bg=C["border"],
                         highlightthickness=1,
                         highlightbackground=C["border2"])
        outer.pack(fill="both", expand=True)

        self._stt_box = tk.Text(
            outer, bg=C["surf2"], fg=C["text"],
            insertbackground=C["blue"],
            relief="flat", bd=0, padx=18, pady=14,
            font=(FONT_UI, int(self.cfg.font_size)),
            wrap="word", undo=True, maxundo=200,
            selectbackground=C["blue_dim"],
            selectforeground=C["white"],
            spacing3=4)

        # FIX: use factory to avoid TclError on scrollbar style
        vsb = _make_scrollbar(outer, orient="vertical",
                              command=self._stt_box.yview)
        self._stt_box.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", pady=4)
        self._stt_box.pack(fill="both", expand=True)

        self._stt_box.tag_configure("highlight",
                                    background=C["orange"],
                                    foreground=C["bg"])
        self._stt_box.bind("<<Modified>>", self._stt_modified)

        tk.Label(main, text="  ↑ Drag & drop .wav / .mp3 files here",
                 bg=C["bg"], fg=C["text4"],
                 font=(FONT_UI, 8)).pack(anchor="w", pady=(3, 0))

    # ══════════════════════════════════════════════════════════════════════════
    #  TTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_tts_tab(self, parent):
        body = tk.Frame(parent, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=12)
        self._build_tts_sidebar(body)
        self._build_tts_main(body)

    def _build_tts_sidebar(self, parent):
        side = tk.Frame(parent, bg=C["surf2"], width=220)
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)

        inner = tk.Frame(side, bg=C["surf2"])
        inner.pack(fill="both", expand=True, padx=12, pady=14)

        srow = tk.Frame(inner, bg=C["surf2"])
        srow.pack(fill="x", pady=(0, 10))
        self._spk_dot = AnimatedDot(srow, C["blue"], bg=C["surf2"])
        self._spk_dot.pack(side="left")
        self._tts_status_lbl = tk.Label(srow, text="Idle",
                                         bg=C["surf2"], fg=C["text4"],
                                         font=(FONT_UI, 9))
        self._tts_status_lbl.pack(side="left", padx=6)

        self._btn_spk = RoundedButton(
            inner, "▶  Speak Text", self._toggle_speak,
            hover_bg=C["blue"], hover_fg=C["white"], font_size=9)
        self._btn_spk.pack(fill="x", pady=(0, 4))

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        tk.Label(inner, text="WAVEFORM", bg=C["surf2"], fg=C["text4"],
                 font=(FONT_UI, 7, "bold")).pack(anchor="w", pady=(0, 4))
        self._tts_wave = WaveformCanvas(inner, bars=24,
                                         bg=C["surf3"], height=48)
        self._tts_wave.pack(fill="x")

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        tk.Label(inner, text="TEXT SOURCE", bg=C["surf2"], fg=C["text4"],
                 font=(FONT_UI, 7, "bold")).pack(anchor="w", pady=(0, 4))
        self._tts_src = tk.StringVar(value="editor")
        for val, lbl in [("editor", "Type in editor"),
                          ("file",   "From text file"),
                          ("clip",   "From clipboard")]:
            tk.Radiobutton(
                inner, text=lbl, variable=self._tts_src, value=val,
                command=self._tts_src_changed,
                bg=C["surf2"], fg=C["text2"],
                activebackground=C["surf2"], selectcolor=C["blue"],
                font=(FONT_UI, 9), cursor="hand2").pack(anchor="w", pady=1)

        self._tts_file_frame = tk.Frame(inner, bg=C["surf2"])
        self._tts_file_var   = tk.StringVar()
        tk.Entry(self._tts_file_frame, textvariable=self._tts_file_var,
                 width=22, bg=C["surf3"], fg=C["text2"],
                 insertbackground=C["text"], relief="flat",
                 font=(FONT_UI, 8),
                 highlightthickness=1,
                 highlightbackground=C["border"]).pack(
                     fill="x", pady=(3, 0), ipady=3)
        RoundedButton(self._tts_file_frame, "Browse text file…",
                      self._tts_browse,
                      hover_bg=C["blue"], pady=4).pack(fill="x", pady=2)

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        tk.Label(inner, text="AUDIO FORMAT", bg=C["surf2"], fg=C["text4"],
                 font=(FONT_UI, 7, "bold")).pack(anchor="w", pady=(0, 4))
        self._tts_fmt = tk.StringVar(value="wav")
        for ext, lbl in [("wav", "WAV  (offline)"),
                          ("mp3", "MP3  (online) ")]:
            tk.Radiobutton(
                inner, text=lbl, variable=self._tts_fmt, value=ext,
                bg=C["surf2"], fg=C["text2"],
                activebackground=C["surf2"], selectcolor=C["blue"],
                font=(FONT_MONO, 9), cursor="hand2").pack(anchor="w", pady=2)

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        for label, cmd, hbg in [
            ("💾  Save as Audio",   self._tts_save_audio, C["green"]),
            ("📂  Load Text File",  self._tts_load_file,  C["purple"]),
            ("📋  Paste Clipboard", self._load_clipboard, C["cyan"]),
            ("🗑  Clear",           self._tts_clear,      C["text4"]),
        ]:
            RoundedButton(inner, label, cmd,
                          hover_bg=hbg, pady=5).pack(fill="x", pady=2)

        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=8)
        self._tts_wc = tk.Label(inner, text="0 words · 0 chars",
                                 bg=C["surf2"], fg=C["text4"],
                                 font=(FONT_UI, 8), anchor="w")
        self._tts_wc.pack(anchor="w")

    def _build_tts_main(self, parent):
        main = tk.Frame(parent, bg=C["bg"])
        main.pack(fill="both", expand=True)

        hrow = tk.Frame(main, bg=C["bg"])
        hrow.pack(fill="x", pady=(0, 6))
        tk.Label(hrow, text="Text Editor",
                 bg=C["bg"], fg=C["text"],
                 font=(FONT_UI, 12, "bold")).pack(side="left")
        tk.Label(hrow, text="  Type, paste, or load text to speak",
                 bg=C["bg"], fg=C["text4"],
                 font=(FONT_UI, 9)).pack(side="left")

        chips = tk.Frame(main, bg=C["surf3"])
        chips.pack(fill="x", pady=(0, 6))
        tk.Label(chips, text="  Quick: ",
                 bg=C["surf3"], fg=C["text4"],
                 font=(FONT_UI, 8)).pack(side="left", pady=5)
        for snip in QUICK_SNIPPETS:
            lbl = tk.Label(chips, text=snip[:28],
                           bg=C["surf4"], fg=C["text3"],
                           font=(FONT_UI, 8), padx=8, pady=4, cursor="hand2",
                           relief="flat",
                           highlightthickness=1,
                           highlightbackground=C["border"])
            lbl.pack(side="left", padx=3, pady=5)
            lbl.bind("<Button-1>", lambda e, s=snip: self._quick_insert(s))
            lbl.bind("<Enter>",
                     lambda e, w=lbl: w.config(bg=C["border3"], fg=C["text"]))
            lbl.bind("<Leave>",
                     lambda e, w=lbl: w.config(bg=C["surf4"], fg=C["text3"]))

        outer = tk.Frame(main, bg=C["border"],
                         highlightthickness=1,
                         highlightbackground=C["border2"])
        outer.pack(fill="both", expand=True)

        self._tts_box = tk.Text(
            outer, bg=C["surf2"], fg=C["text"],
            insertbackground=C["blue"],
            relief="flat", bd=0, padx=18, pady=14,
            font=(FONT_UI, int(self.cfg.font_size)),
            wrap="word", undo=True, maxundo=200,
            selectbackground=C["blue_dim"],
            selectforeground=C["white"],
            spacing3=4)

        # FIX: use factory here too
        vsb2 = _make_scrollbar(outer, orient="vertical",
                               command=self._tts_box.yview)
        self._tts_box.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y", pady=4)
        self._tts_box.pack(fill="both", expand=True)

        self._tts_box.bind("<<Modified>>", self._tts_modified)
        self._tts_box.bind("<FocusIn>",    self._ph_clear)
        self._tts_box.bind("<FocusOut>",   self._ph_restore)
        self._tts_box.bind("<Control-a>",
                           lambda e: (self._tts_box.tag_add("sel", "1.0", "end"),
                                      "break"))

        self._tts_char_bar = tk.Frame(main, bg=C["surf2"], height=3)
        self._tts_char_bar.pack(fill="x")
        self._tts_progress = tk.Frame(self._tts_char_bar,
                                       bg=C["blue"], height=3)
        self._tts_progress.place(x=0, y=0, relheight=1.0, width=0)

        self._tts_box.insert("1.0", self._ph_text)
        self._tts_box.config(fg=C["text4"])

    # ══════════════════════════════════════════════════════════════════════════
    #  KEYBOARD SHORTCUTS
    # ══════════════════════════════════════════════════════════════════════════

    def _bind_keys(self):
        for seq in ("<Control-r>", "<Control-R>"):
            self.bind(seq, lambda e: self._toggle_record())
        for seq in ("<Control-t>", "<Control-T>"):
            self.bind(seq, lambda e: self._toggle_speak())
        for seq in ("<Control-s>", "<Control-S>"):
            self.bind(seq, lambda e: self._smart_save())
        for seq in ("<Control-l>", "<Control-L>"):
            self.bind(seq, lambda e: self._smart_clear())
        self.bind("<Control-comma>", lambda e: self._open_settings())
        self.bind("<Control-h>",     lambda e: self._show_history())
        self.bind("<F1>",            lambda e: self._toggle_tab())

    def _smart_save(self):
        if self._nb.index("current") == 0:
            self._stt_save()
        else:
            self._tts_save_audio()

    def _smart_clear(self):
        if self._nb.index("current") == 0:
            self._stt_clear()
        else:
            self._tts_clear()

    def _toggle_tab(self):
        cur = self._nb.index("current")
        self._nb.select(1 - cur)

    def _on_tab_change(self, _e=None):
        pass

    # ══════════════════════════════════════════════════════════════════════════
    #  STT CONTROLS
    # ══════════════════════════════════════════════════════════════════════════

    def _stt_src_changed(self):
        if self._stt_src.get() == "file":
            self._stt_file_bar.pack(side="left", fill="y", padx=(10, 0))
        else:
            self._stt_file_bar.pack_forget()

    def _stt_browse(self):
        p = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio", "*.wav *.mp3"),
                       ("WAV", "*.wav"), ("MP3", "*.mp3"),
                       ("All", "*.*")],
            initialdir=self.cfg.save_dir, parent=self)
        if p:
            self._stt_file_var.set(p)

    def _toggle_record(self):
        if not self._stt:
            self._engine_error("STT", self._stt_err)
            return
        if self._rec_active:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        src  = self._stt_src.get()
        path = ""
        if src == "file":
            path = self._stt_file_var.get().strip()
            if not path:
                messagebox.showwarning("No File",
                                       "Please select an audio file first.",
                                       parent=self)
                return
            if not Path(path).exists():
                messagebox.showerror("File Not Found",
                                     f"File could not be found:\n{path}",
                                     parent=self)
                return

        self._rec_active = True
        self._rec_dot.start()
        self._stt_wave.start(color=C["red"])
        self._btn_rec.config_text("⏹  Stop",
                                  bg=C["red_dim"], fg=C["red"])
        self._stt_status_lbl.config(text="Starting…", fg=C["blue"])
        self._status.set("Recording…", C["red"])

        cb = dict(
            on_status=lambda m: self._q.put(("stt_status", m)),
            on_result=lambda t: self._q.put(("stt_result", t)),
            on_error =lambda e: self._q.put(("stt_error",  e)),
        )
        if src == "mic":
            self._stt.transcribe_mic(**cb)
        else:
            self._stt.transcribe_file(path, **cb)

    def _stop_record(self):
        self._rec_active = False
        if self._stt:
            self._stt.stop()
        self._rec_dot.stop()
        self._stt_wave.stop()
        self._btn_rec.config_text("⏺  Start Recording",
                                  bg=C["surf3"], fg=C["text2"])
        self._stt_status_lbl.config(text="Idle", fg=C["text4"])
        self._status.set("Recording stopped.", C["text3"])

    # ══════════════════════════════════════════════════════════════════════════
    #  TTS CONTROLS
    # ══════════════════════════════════════════════════════════════════════════

    def _tts_src_changed(self):
        if self._tts_src.get() == "file":
            self._tts_file_frame.pack(fill="x", pady=4)
        else:
            self._tts_file_frame.pack_forget()
        if self._tts_src.get() == "clip":
            self._load_clipboard()

    def _tts_browse(self):
        p = filedialog.askopenfilename(
            title="Select Text File", filetypes=TEXT_FILETYPES,
            initialdir=self.cfg.save_dir, parent=self)
        if p:
            self._tts_file_var.set(p)
            self._load_text_file(p)

    def _toggle_speak(self):
        if not self._tts:
            self._engine_error("TTS", self._tts_err)
            return
        if self._spk_active:
            self._stop_speak()
        else:
            self._start_speak()

    def _start_speak(self):
        text = self._get_tts_text()
        if not text.strip():
            messagebox.showwarning("Nothing to Speak",
                                   "The text editor is empty.\n"
                                   "Type or load text first.", parent=self)
            return

        self._tts._stop_evt.clear()
        self._spk_active = True
        self._spk_dot.start()
        self._tts_wave.start(color=C["blue"])
        self._btn_spk.config_text("⏹  Stop Speaking",
                                  bg=C["blue_dim"], fg=C["blue"])
        self._tts_status_lbl.config(text="Speaking…", fg=C["blue"])
        self._status.set("Speaking…", C["blue"])

        self._tts.speak_async(
            text,
            on_start=None,
            on_done =lambda: self._q.put(("tts_done", "")),
            on_error=lambda e: self._q.put(("tts_error", e)),
        )

    def _stop_speak(self):
        self._spk_active = False
        if self._tts:
            self._tts.stop()
        self._spk_dot.stop()
        self._tts_wave.stop()
        self._btn_spk.config_text("▶  Speak Text",
                                  bg=C["surf3"], fg=C["text2"])
        self._tts_status_lbl.config(text="Idle", fg=C["text4"])
        self._status.set("Speech stopped.", C["text3"])

    # ══════════════════════════════════════════════════════════════════════════
    #  TEXT OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _get_tts_text(self) -> str:
        src = self._tts_src.get()
        if src == "editor":
            return "" if self._ph_on else self._tts_box.get("1.0", "end-1c")
        if src == "file":
            p = self._tts_file_var.get().strip()
            if not p:
                return "" if self._ph_on else self._tts_box.get("1.0", "end-1c")
            try:
                return Path(p).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                messagebox.showerror("Read Error", str(e), parent=self)
                return ""
        if src == "clip":
            try:
                return self.clipboard_get()
            except Exception:
                return ""
        return ""

    def _load_text_file(self, path: str):
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            self._ph_clear(None)
            self._tts_box.delete("1.0", "end")
            self._tts_box.insert("1.0", text)
            self._tts_box.config(fg=C["text"])
            self.cfg.save_dir = str(Path(path).parent)
            size = _readable_size(Path(path))
            self._status.set(
                f"Loaded  {Path(path).name}  ({len(text):,} chars, {size})",
                C["green"])
            self._notify(f"Loaded {Path(path).name}", "success")
        except FileNotFoundError:
            messagebox.showerror("Not Found",
                                 f"File not found:\n{path}", parent=self)
        except PermissionError:
            messagebox.showerror("Permission Denied",
                                 f"Cannot read:\n{path}", parent=self)
        except OSError as e:
            messagebox.showerror("Read Error", str(e), parent=self)

    def _load_clipboard(self):
        try:
            text = self.clipboard_get()
            if not text.strip():
                messagebox.showwarning("Clipboard Empty",
                                       "Clipboard contains no text.",
                                       parent=self)
                return
            self._ph_clear(None)
            self._tts_box.delete("1.0", "end")
            self._tts_box.insert("1.0", text)
            self._tts_box.config(fg=C["text"])
            self._status.set(
                f"Pasted {len(text):,} chars from clipboard.", C["green"])
            self._notify(f"Pasted {len(text):,} chars", "success")
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e), parent=self)

    def _quick_insert(self, s: str):
        self._ph_clear(None)
        cur = self._tts_box.get("1.0", "end-1c")
        sep = " " if cur and not cur.endswith(" ") else ""
        self._tts_box.insert("end", sep + s)
        self._tts_box.config(fg=C["text"])
        self._tts_box.see("end")

    # ── Placeholder ──────────────────────────────────────────────────────────

    def _ph_clear(self, _e):
        if self._ph_on:
            self._tts_box.delete("1.0", "end")
            self._tts_box.config(fg=C["text"])
            self._ph_on = False

    def _ph_restore(self, _e):
        if not self._tts_box.get("1.0", "end-1c").strip():
            self._tts_box.insert("1.0", self._ph_text)
            self._tts_box.config(fg=C["text4"])
            self._ph_on = True

    # ── Search ───────────────────────────────────────────────────────────────

    def _stt_search_text(self):
        query = self._stt_search.get().strip()
        self._stt_box.tag_remove("highlight", "1.0", "end")
        if not query:
            return
        start = "1.0"
        count = 0
        while True:
            pos = self._stt_box.search(query, start, stopindex="end",
                                        nocase=True, regexp=False)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self._stt_box.tag_add("highlight", pos, end)
            start = end
            count += 1
        if count:
            first = self._stt_box.tag_ranges("highlight")
            if first:
                self._stt_box.see(first[0])
        msg = (f"Found {count} match{'es' if count != 1 else ''} for '{query}'"
               if query else "")
        self._status.set(msg, C["orange"] if count == 0 else C["green"])

    def _stt_clear_highlight(self):
        self._stt_box.tag_remove("highlight", "1.0", "end")

    # ── Word count ───────────────────────────────────────────────────────────

    def _stt_modified(self, _e):
        self._stt_box.edit_modified(False)
        t    = self._stt_box.get("1.0", "end-1c")
        w, c = _word_count(t)
        try:
            self._stt_wc.config(text=f"{w:,} words · {c:,} chars")
        except tk.TclError:
            pass

    def _tts_modified(self, _e):
        self._tts_box.edit_modified(False)
        if self._ph_on:
            try:
                self._tts_wc.config(text="0 words · 0 chars")
                self._tts_progress.place_configure(width=0)
            except tk.TclError:
                pass
            return
        t    = self._tts_box.get("1.0", "end-1c")
        w, c = _word_count(t)
        try:
            self._tts_wc.config(text=f"{w:,} words · {c:,} chars")
            frac  = min(1.0, c / 5000)
            bar_w = self._tts_char_bar.winfo_width()
            self._tts_progress.place_configure(width=int(bar_w * frac))
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  SAVE / LOAD
    # ══════════════════════════════════════════════════════════════════════════

    def _stt_save(self):
        text = self._stt_box.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Nothing to Save",
                                   "Transcription box is empty.", parent=self)
            return
        ext  = self._stt_fmt.get()
        path = filedialog.asksaveasfilename(
            title="Save Transcription",
            defaultextension=f".{ext}",
            filetypes=TEXT_FILETYPES,
            initialdir=self.cfg.save_dir,
            initialfile=_ts_filename("transcript", ext),
            parent=self)
        if not path:
            return
        try:
            p   = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if ext == "md":
                content = (f"# Transcription\n\n"
                           f"> *Voice Studio Pro v{APP_VERSION} — {now}*\n\n"
                           f"---\n\n{text}\n")
            elif ext == "log":
                sep     = "─" * 60
                content = (f"[{datetime.datetime.now().isoformat()}]"
                           f" TRANSCRIPTION\n{sep}\n{text}\n{sep}\n")
            else:
                content = text
            p.write_text(content, encoding="utf-8")
            self.cfg.save_dir = str(p.parent)
            self._log.append(HistoryEntry("STT Save", p.name))
            self._status.set(
                f"Saved → {p.name}  ({_readable_size(p)})", C["green"])
            self._notify(f"Saved {p.name}", "success")
        except PermissionError:
            messagebox.showerror("Permission Denied",
                                 f"Cannot write to:\n{path}", parent=self)
        except OSError as e:
            messagebox.showerror("Save Error", str(e), parent=self)

    def _stt_copy(self):
        text = self._stt_box.get("1.0", "end-1c").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._status.set("Copied to clipboard.", C["green"])
            self._notify("Copied to clipboard", "success")
        else:
            messagebox.showwarning("Empty", "Nothing to copy.", parent=self)

    def _stt_clear(self):
        if not self._stt_box.get("1.0", "end-1c").strip():
            return
        if messagebox.askyesno("Clear",
                               "Clear transcription output?", parent=self):
            self._stt_box.delete("1.0", "end")
            try:
                self._stt_wc.config(text="0 words · 0 chars")
            except tk.TclError:
                pass

    def _tts_save_audio(self):
        if not self._tts:
            self._engine_error("TTS", self._tts_err)
            return
        text = self._get_tts_text()
        if not text.strip():
            messagebox.showwarning("Nothing to Save",
                                   "Text editor is empty.", parent=self)
            return
        ext = self._tts_fmt.get()
        if ext == "mp3" and not HAS_GTTS:
            messagebox.showerror(
                "gTTS Required",
                "MP3 export requires gTTS (online engine).\n\n"
                "Install:  pip install gTTS\n\n"
                "Or switch to WAV format.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="Save Audio File",
            defaultextension=f".{ext}",
            filetypes=AUDIO_FILETYPES,
            initialdir=self.cfg.save_dir,
            initialfile=_ts_filename("speech", ext),
            parent=self)
        if not path:
            return

        orig_eng = self.cfg.get("tts_engine")
        if ext == "mp3":
            self.cfg.set("tts_engine", "gtts")

        self._status.set("Saving audio file…", C["orange"])
        self.update_idletasks()

        def _done(saved):
            self.cfg.set("tts_engine", orig_eng)
            self._q.put(("tts_saved", saved))

        def _err(msg):
            self.cfg.set("tts_engine", orig_eng)
            self._q.put(("tts_error", msg))

        self._tts.save_async(text, path, on_done=_done, on_error=_err)

    def _tts_load_file(self):
        p = filedialog.askopenfilename(
            title="Load Text File", filetypes=TEXT_FILETYPES,
            initialdir=self.cfg.save_dir, parent=self)
        if p:
            self._load_text_file(p)

    def _tts_clear(self):
        if not self._ph_on:
            self._tts_box.delete("1.0", "end")
            self._ph_restore(None)

    def _auto_save(self, text: str):
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            out = SAVE_DIR / _ts_filename("auto", "txt")
            out.write_text(text, encoding="utf-8")
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  QUEUE POLL  (thread → UI bridge)
    # ══════════════════════════════════════════════════════════════════════════

    def _poll(self):
        try:
            while True:
                kind, payload = self._q.get_nowait()

                if kind == "stt_status":
                    try:
                        self._stt_status_lbl.config(text=payload, fg=C["blue"])
                        self._status.set(payload, C["blue"])
                    except tk.TclError:
                        pass

                elif kind == "stt_result":
                    self._rec_active = False
                    try:
                        self._rec_dot.stop()
                        self._stt_wave.stop()
                        self._btn_rec.config_text("⏺  Start Recording",
                                                  bg=C["surf3"], fg=C["text2"])
                        self._stt_status_lbl.config(text="Done ✓", fg=C["green"])
                        words, _ = _word_count(payload)
                        prev = (payload[:65] + "…" if len(payload) > 65
                                else payload)
                        self._status.set(f"Transcribed:  {prev}", C["green"])
                        self._notify(f"Transcribed {words} words", "success")

                        if self._stt_append.get():
                            ex = self._stt_box.get("1.0", "end-1c").strip()
                            self._stt_box.insert(
                                "end", ("\n\n" if ex else "") + payload)
                        else:
                            self._stt_box.delete("1.0", "end")
                            self._stt_box.insert("1.0", payload)
                        self._stt_box.see("end")

                        self._session_entries += 1
                        self._session_words   += words
                        self._stt_stats_lbl.config(
                            text=(f"{self._session_entries} transcription"
                                  f"{'s' if self._session_entries != 1 else ''}\n"
                                  f"{self._session_words:,} total words"))
                        self._status.set_stats(
                            f"Session: {self._session_words:,} words")
                        self._log.append(HistoryEntry("STT", payload[:100]))
                        if self.cfg.auto_save:
                            self._auto_save(payload)
                    except tk.TclError:
                        pass

                elif kind == "stt_error":
                    self._rec_active = False
                    try:
                        self._rec_dot.stop()
                        self._stt_wave.stop()
                        self._btn_rec.config_text("⏺  Start Recording",
                                                  bg=C["surf3"], fg=C["text2"])
                        self._stt_status_lbl.config(text="Error", fg=C["red"])
                        first = payload.split("\n")[0][:80]
                        self._status.set(f"Error — {first}", C["red"])
                        self._notify(f"STT Error: {first}", "error")
                        messagebox.showerror("Transcription Error",
                                             payload, parent=self)
                    except tk.TclError:
                        pass

                elif kind == "tts_done":
                    self._spk_active = False
                    try:
                        self._spk_dot.stop()
                        self._tts_wave.stop()
                        self._btn_spk.config_text("▶  Speak Text",
                                                  bg=C["surf3"], fg=C["text2"])
                        self._tts_status_lbl.config(text="Done ✓", fg=C["green"])
                        self._status.set("Speech complete.", C["green"])
                        self._notify("Speech finished", "success")
                    except tk.TclError:
                        pass

                elif kind == "tts_error":
                    self._spk_active = False
                    try:
                        self._spk_dot.stop()
                        self._tts_wave.stop()
                        self._btn_spk.config_text("▶  Speak Text",
                                                  bg=C["surf3"], fg=C["text2"])
                        self._tts_status_lbl.config(text="Error", fg=C["red"])
                        first = payload.split("\n")[0][:80]
                        self._status.set(f"TTS Error — {first}", C["red"])
                        self._notify(f"TTS Error: {first}", "error")
                        messagebox.showerror("TTS Error", payload, parent=self)
                    except tk.TclError:
                        pass

                elif kind == "tts_saved":
                    try:
                        p    = Path(payload)
                        size = _readable_size(p)
                        self.cfg.save_dir = str(p.parent)
                        self._log.append(HistoryEntry("TTS Save", p.name))
                        self._status.set(
                            f"Audio saved → {p.name}  ({size})", C["green"])
                        self._notify(f"Saved {p.name}  ({size})", "success")
                        messagebox.showinfo(
                            "Audio Saved",
                            f"File saved successfully:\n{payload}\n\nSize: {size}",
                            parent=self)
                    except tk.TclError:
                        pass

        except queue.Empty:
            pass

        try:
            if self.winfo_exists():
                self.after(60, self._poll)
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  DIALOGS
    # ══════════════════════════════════════════════════════════════════════════

    def _open_settings(self):
        SettingsDialog(self, self.cfg, self._tts, self._stt)

    def _show_history(self):
        win = tk.Toplevel(self)
        win.title("Session History — Voice Studio Pro")
        win.geometry("620x480")
        win.configure(bg=C["bg"])
        win.transient(self)

        hdr = tk.Frame(win, bg=C["surf1"], height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  ⏱  Session History",
                 bg=C["surf1"], fg=C["text"],
                 font=(FONT_UI, 12, "bold")).pack(
                     side="left", padx=16, pady=14)
        tk.Label(hdr, text=f"{len(self._log)} entries",
                 bg=C["surf1"], fg=C["text4"],
                 font=(FONT_UI, 9)).pack(side="right", padx=16)
        tk.Frame(win, bg=C["border"], height=1).pack(fill="x")

        outer = tk.Frame(win, bg=C["border"])
        outer.pack(fill="both", expand=True, padx=16, pady=12)

        txt = tk.Text(outer, bg=C["surf2"], fg=C["text"],
                      relief="flat", bd=0, padx=14, pady=10,
                      font=(FONT_MONO, 9), wrap="word", state="disabled",
                      selectbackground=C["blue_dim"])

        # FIX: use factory for this scrollbar too
        sb = _make_scrollbar(outer, orient="vertical",
                             command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        txt.tag_configure("kind", foreground=C["blue"],
                          font=(FONT_MONO, 8, "bold"))
        txt.tag_configure("ts",   foreground=C["text4"],
                          font=(FONT_MONO, 8))
        txt.tag_configure("val",  foreground=C["text2"])

        txt.config(state="normal")
        if not self._log:
            txt.insert("1.0", "No activity recorded this session.")
        else:
            for entry in reversed(self._log):
                txt.insert("end", f"[{entry.fmt_time()}] ", "ts")
                txt.insert("end", f"[{entry.kind}]\n", "kind")
                txt.insert("end", f"  {entry.text}\n\n", "val")
        txt.config(state="disabled")

        bf = tk.Frame(win, bg=C["bg"])
        bf.pack(fill="x", padx=16, pady=(0, 12))

        def _clear_hist():
            self._log.clear()
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", "History cleared.")
            txt.config(state="disabled")

        RoundedButton(bf, "Clear History", _clear_hist,
                      hover_bg=C["red"]).pack(side="right")
        RoundedButton(bf, "Close", win.destroy,
                      hover_bg=C["text4"]).pack(side="right", padx=6)

    # ── Engine error helper ──────────────────────────────────────────────────

    def _engine_error(self, name: str, err: str):
        messagebox.showerror(
            f"{name} Unavailable",
            f"{name} engine is not available.\n\n{err}\n\n"
            f"Install missing packages and restart.",
            parent=self)

    # ── Toast ────────────────────────────────────────────────────────────────

    def _notify(self, msg: str, kind: str = "info"):
        if self.cfg.notifications:
            self._toast.show(msg, kind)

    # ── Startup banner ───────────────────────────────────────────────────────

    def _startup_banner(self):
        tts_ok = self._tts is not None
        stt_ok = self._stt is not None

        tts_label = (f"TTS: {self.cfg.tts_engine}" if tts_ok
                     else "TTS: unavailable")
        mic_label = ""
        if stt_ok:
            mic_ok    = self._stt.mic_available
            mic_label = "mic OK" if mic_ok else "no mic"
            stt_label = f"STT: Google ({mic_label})"
        else:
            stt_label = "STT: unavailable"

        tts_col = C["green"] if tts_ok else C["red"]
        stt_col = (C["green"]  if (stt_ok and mic_label == "mic OK")
                   else C["orange"] if stt_ok else C["red"])

        try:
            self._tts_pill.config(text=f"● {tts_label}", fg=tts_col)
            self._stt_pill.config(text=f"● {stt_label}", fg=stt_col)

            col   = C["green"] if (tts_ok and stt_ok) else C["orange"]
            parts = [tts_label, stt_label]
            self._status.set("Ready  ·  " + "   ·   ".join(parts), col)
        except tk.TclError:
            pass

        self.after(4000, self._hint_banner)

    def _hint_banner(self):
        try:
            if self.winfo_exists():
                self._status.set(
                    "Ctrl+R: Record  ·  Ctrl+T: Speak  ·  "
                    "Ctrl+S: Save  ·  F1: Switch tab",
                    C["text4"])
        except tk.TclError:
            pass

    # ── Quit ────────────────────────────────────────────────────────────────

    def _on_quit(self):
        if self._rec_active and self._stt:
            self._stt.stop()
        if self._spk_active and self._tts:
            self._tts.stop()
        self.cfg.save()
        try:
            self.after(200, self._do_quit)
        except tk.TclError:
            sys.exit(0)

    def _do_quit(self):
        try:
            self.destroy()
        except Exception:
            sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if getattr(sys, "frozen", False):
        try:
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")
        except Exception:
            pass

    try:
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        app = VoiceStudioPro()
        app.mainloop()

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        err = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Fatal Startup Error",
                f"Voice Studio Pro could not start:\n\n{err[:1200]}")
            root.destroy()
        except Exception:
            print(err, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
