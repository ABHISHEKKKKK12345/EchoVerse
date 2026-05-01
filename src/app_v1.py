"""
╔══════════════════════════════════════════════════════════════╗
║        VOICE STUDIO  —  Speech ↔ Text Converter              ║
║      Production-Grade · Cross-Platform · Bug-Free            ║
║                 Author: Abhishek                             ║
╚══════════════════════════════════════════════════════════════╝

Install dependencies:
    pip install SpeechRecognition pyttsx3 gTTS pyaudio pydub

On Linux also:
    sudo apt install portaudio19-dev python3-tk
"""

# ── Suppress pygame/pkg_resources deprecation warning BEFORE any imports ─────
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ── stdlib ────────────────────────────────────────────────────────────────────
import os
import sys
import threading
import queue
import time
import json
import tempfile
import datetime
import traceback
import re
from pathlib import Path
from typing import Optional, Callable

# ── Redirect stderr temporarily to suppress pygame banner ─────────────────────
import io
_real_stderr = sys.stderr
sys.stderr = io.StringIO()

# ── GUI ───────────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Restore stderr after GUI imports ─────────────────────────────────────────
sys.stderr = _real_stderr

# ── Speech ────────────────────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# ── Audio playback — suppress pygame console output ───────────────────────────
HAS_PYGAME = False
_saved_stderr = sys.stderr
_saved_stdout = sys.stdout
try:
    sys.stderr = io.StringIO()
    sys.stdout = io.StringIO()
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception:
    pass
finally:
    sys.stderr = _saved_stderr
    sys.stdout = _saved_stdout

HAS_PYDUB = False
try:
    from pydub import AudioSegment
    from pydub.playback import play as _pydub_play
    HAS_PYDUB = True
except Exception:
    pass


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE   = "Voice Studio"
APP_VERSION = "1.0"

P = {
    "bg":        "#080b14",
    "surface":   "#0e1220",
    "surf2":     "#141826",
    "surf3":     "#1c2233",
    "surf4":     "#232b40",
    "border":    "#2a3450",
    "border2":   "#3a4a6a",
    "accent":    "#4f8fff",
    "accent2":   "#ff6b6b",
    "accent3":   "#43e97b",
    "accent4":   "#f7c948",
    "purple":    "#a78bfa",
    "success":   "#2dd4bf",
    "warn":      "#fbbf24",
    "err":       "#f87171",
    "text":      "#e8eaf6",
    "dim":       "#8899bb",
    "muted":     "#4a5a7a",
    "glass":     "#ffffff08",
}

TEXT_FILETYPES  = [("Text", "*.txt"), ("Markdown", "*.md"),
                   ("Log",  "*.log"), ("All",      "*.*")]
AUDIO_FILETYPES = [("WAV",  "*.wav"), ("MP3",      "*.mp3"),
                   ("All",  "*.*")]

SAVE_DIR      = Path.home() / "VoiceStudio"
SETTINGS_PATH = SAVE_DIR / ".settings.json"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class Settings:
    _D = {
        "tts_engine":  "pyttsx3",
        "tts_rate":    175,
        "tts_volume":  1.0,
        "tts_voice":   0,
        "tts_lang":    "en",
        "stt_energy":  300,
        "stt_pause":   0.8,
        "stt_timeout": 10,
        "stt_phrase":  30,
        "save_dir":    str(SAVE_DIR),
        "auto_save":   False,
        "font_size":   11,
    }

    def __init__(self):
        self._d = dict(self._D)
        self._load()

    def _load(self):
        try:
            if SETTINGS_PATH.exists():
                saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                self._d.update({k: v for k, v in saved.items() if k in self._D})
        except Exception:
            pass

    def save(self):
        try:
            SETTINGS_PATH.write_text(json.dumps(self._d, indent=2), encoding="utf-8")
        except Exception:
            pass

    def __getattr__(self, k):
        if k.startswith("_"):
            raise AttributeError(k)
        return self._d.get(k, self._D.get(k))

    def __setattr__(self, k, v):
        if k.startswith("_"):
            object.__setattr__(self, k, v)
        else:
            self._d[k] = v
            self.save()


# ══════════════════════════════════════════════════════════════════════════════
#  TTS ENGINE  — Fixed: pyttsx3 re-init per call, thread-safe, no stale state
# ══════════════════════════════════════════════════════════════════════════════

class TTSEngine:
    """
    Thread-safe TTS engine.
    
    KEY FIX: pyttsx3 engines CANNOT be reused across threads or after runAndWait().
    We create a fresh engine for every speak call to avoid the "run loop already started"
    and "engine already stopped" errors that caused intermittent failures.
    """

    def __init__(self, cfg: Settings):
        self.cfg     = cfg
        self._lock   = threading.Lock()
        self._stop   = threading.Event()
        self._voices: list = []
        self._active_engine = None  # track current pyttsx3 instance

        # Probe voices once at startup
        if HAS_PYTTSX3:
            try:
                _eng = pyttsx3.init()
                self._voices = list(_eng.getProperty("voices") or [])
                _eng.stop()
                del _eng
            except Exception:
                self._voices = []

    @property
    def voices(self):
        return self._voices

    def _make_engine(self):
        """Create and configure a fresh pyttsx3 engine."""
        eng = pyttsx3.init()
        eng.setProperty("rate",   int(self.cfg.tts_rate))
        eng.setProperty("volume", float(self.cfg.tts_volume))
        if self._voices:
            idx = min(int(self.cfg.tts_voice), len(self._voices) - 1)
            eng.setProperty("voice", self._voices[idx].id)
        return eng

    def speak_async(self,
                    text:     str,
                    on_done:  Optional[Callable] = None,
                    on_error: Optional[Callable] = None) -> threading.Thread:
        self._stop.clear()

        def _run():
            with self._lock:
                try:
                    if self.cfg.tts_engine == "gtts" and HAS_GTTS:
                        self._speak_gtts(text)
                    elif HAS_PYTTSX3:
                        eng = self._make_engine()
                        self._active_engine = eng
                        if not self._stop.is_set():
                            eng.say(text)
                            eng.runAndWait()
                        self._active_engine = None
                        try:
                            eng.stop()
                        except Exception:
                            pass
                        del eng
                    else:
                        raise RuntimeError("No TTS engine available. Install pyttsx3 or gTTS.")
                    if not self._stop.is_set() and on_done:
                        on_done()
                except Exception as e:
                    self._active_engine = None
                    if not self._stop.is_set() and on_error:
                        on_error(str(e))

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def _speak_gtts(self, text: str):
        tts = gTTS(text=text, lang=self.cfg.tts_lang, slow=False)
        fd, tmp = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            tts.save(tmp)
            if not self._stop.is_set():
                self._play_audio(tmp)
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

    def _play_audio(self, path: str):
        if HAS_PYGAME:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if self._stop.is_set():
                        pygame.mixer.music.stop()
                        return
                    time.sleep(0.05)
                return
            except Exception:
                pass  # fall through to pydub/system

        if HAS_PYDUB:
            try:
                _pydub_play(AudioSegment.from_file(path))
                return
            except Exception:
                pass

        # OS fallback
        if sys.platform == "win32":
            os.system(f'start /wait "" "{path}"')
        elif sys.platform == "darwin":
            os.system(f'afplay "{path}"')
        else:
            os.system(f'aplay "{path}" 2>/dev/null || mpg123 "{path}" 2>/dev/null')

    def save_to_file(self,
                     text:     str,
                     path:     str,
                     on_done:  Optional[Callable] = None,
                     on_error: Optional[Callable] = None) -> threading.Thread:
        def _run():
            with self._lock:
                try:
                    p = Path(path)
                    if self.cfg.tts_engine == "gtts" and HAS_GTTS:
                        mp3 = p.with_suffix(".mp3")
                        gTTS(text=text, lang=self.cfg.tts_lang, slow=False).save(str(mp3))
                        if on_done:
                            on_done(str(mp3))
                    elif HAS_PYTTSX3:
                        wav = p.with_suffix(".wav")
                        eng = self._make_engine()
                        eng.save_to_file(text, str(wav))
                        eng.runAndWait()
                        try:
                            eng.stop()
                        except Exception:
                            pass
                        del eng
                        if on_done:
                            on_done(str(wav))
                    else:
                        raise RuntimeError("No TTS engine available.")
                except Exception as e:
                    if on_error:
                        on_error(str(e))

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def stop(self):
        """Signal stop — works for both gTTS/pygame and pyttsx3."""
        self._stop.set()
        # Stop pygame if playing
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        # Stop active pyttsx3 engine
        if self._active_engine is not None:
            try:
                self._active_engine.stop()
            except Exception:
                pass
            self._active_engine = None


# ══════════════════════════════════════════════════════════════════════════════
#  STT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class STTEngine:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        if not HAS_SR:
            raise RuntimeError(
                "SpeechRecognition not installed.\nRun: pip install SpeechRecognition")
        self.rec   = sr.Recognizer()
        self._stop = threading.Event()
        self._update_rec()

    def _update_rec(self):
        self.rec.energy_threshold         = int(self.cfg.stt_energy)
        self.rec.pause_threshold          = float(self.cfg.stt_pause)
        self.rec.dynamic_energy_threshold = True

    @property
    def mic_available(self) -> bool:
        try:
            return len(sr.Microphone.list_microphone_names()) > 0
        except Exception:
            return False

    def list_mics(self) -> list:
        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def transcribe_mic(self,
                       mic_index:  Optional[int] = None,
                       on_status:  Optional[Callable] = None,
                       on_result:  Optional[Callable] = None,
                       on_error:   Optional[Callable] = None) -> threading.Thread:
        self._stop.clear()
        self._update_rec()

        def _run():
            try:
                kwargs = {} if mic_index is None else {"device_index": mic_index}
                with sr.Microphone(**kwargs) as src:
                    if on_status:
                        on_status("Calibrating microphone…")
                    self.rec.adjust_for_ambient_noise(src, duration=1)
                    if self._stop.is_set():
                        return
                    if on_status:
                        on_status("Listening — speak now")
                    audio = self.rec.listen(
                        src,
                        timeout=int(self.cfg.stt_timeout),
                        phrase_time_limit=int(self.cfg.stt_phrase),
                    )
                if self._stop.is_set():
                    return
                if on_status:
                    on_status("Processing speech…")
                text = self.rec.recognize_google(audio)
                if on_result:
                    on_result(text)
            except sr.WaitTimeoutError:
                if on_error:
                    on_error("No speech detected within the timeout window.")
            except sr.UnknownValueError:
                if on_error:
                    on_error("Speech was unclear — please try again.")
            except sr.RequestError as e:
                if on_error:
                    on_error(
                        f"Google Speech API error:\n{e}\n\nCheck your internet connection.")
            except OSError as e:
                if on_error:
                    on_error(
                        f"Microphone error: {e}\n\nTroubleshooting:\n"
                        "• Check mic is connected and not muted\n"
                        "• Check OS microphone permissions\n"
                        "• Try selecting a different device in Settings")
            except Exception as e:
                if on_error:
                    on_error(f"Unexpected STT error:\n{e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def transcribe_file(self,
                        path:      str,
                        on_status: Optional[Callable] = None,
                        on_result: Optional[Callable] = None,
                        on_error:  Optional[Callable] = None) -> threading.Thread:
        self._stop.clear()

        def _run():
            try:
                if on_status:
                    on_status(f"Loading {Path(path).name}…")
                with sr.AudioFile(path) as src:
                    audio = self.rec.record(src)
                if self._stop.is_set():
                    return
                if on_status:
                    on_status("Transcribing file…")
                text = self.rec.recognize_google(audio)
                if on_result:
                    on_result(text)
            except FileNotFoundError:
                if on_error:
                    on_error(f"File not found:\n{path}")
            except sr.UnknownValueError:
                if on_error:
                    on_error("Could not understand the audio file.")
            except sr.RequestError as e:
                if on_error:
                    on_error(f"Google Speech API error:\n{e}")
            except Exception as e:
                if on_error:
                    on_error(f"File transcription error:\n{e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop.set()


# ══════════════════════════════════════════════════════════════════════════════
#  GUI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _btn(parent,
         text:   str,
         cmd,
         color:  str  = P["accent"],
         width:  int  = 0,
         ipady:  int  = 7) -> tk.Button:
    """Flat styled button with hover effect."""
    kw = dict(width=width) if width else {}
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=P["surf3"], fg=P["dim"],
        activebackground=color, activeforeground="#ffffff",
        relief="flat", bd=0, cursor="hand2",
        font=("Segoe UI", 9, "bold"),
        padx=12, pady=ipady,
        **kw,
    )
    b._hover_color = color

    def _on(_e=None):
        b.config(bg=color, fg="#ffffff")

    def _off(_e=None):
        b.config(bg=P["surf3"], fg=P["dim"])

    b.bind("<Enter>", _on)
    b.bind("<Leave>", _off)
    return b


def _hsep(parent, pady: int = 8):
    tk.Frame(parent, bg=P["border"], height=1).pack(fill="x", pady=pady)


class PulseLight(tk.Canvas):
    """Animated recording dot."""
    def __init__(self, parent, size: int = 12, **kw):
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0,
                         bg=kw.pop("bg", P["bg"]), **kw)
        self._s     = size
        self._on    = False
        self._phase = 0
        self._draw(False)

    def _draw(self, bright: bool):
        self.delete("all")
        c = self._s // 2
        r = c - 1
        color = P["err"] if bright else P["muted"]
        self.create_oval(c - r, c - r, c + r, c + r, fill=color, outline="")

    def start(self):
        self._on = True
        self._tick()

    def stop(self):
        self._on = False
        self._draw(False)

    def _tick(self):
        if not self._on:
            return
        self._phase = (self._phase + 1) % 10
        self._draw(self._phase < 5)
        self.after(150, self._tick)


class SpeakLight(tk.Canvas):
    """Animated speaking dot — blue pulsing."""
    def __init__(self, parent, size: int = 12, **kw):
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0,
                         bg=kw.pop("bg", P["bg"]), **kw)
        self._s     = size
        self._on    = False
        self._phase = 0
        self._draw(False)

    def _draw(self, bright: bool):
        self.delete("all")
        c = self._s // 2
        r = c - 1
        color = P["accent"] if bright else P["muted"]
        self.create_oval(c - r, c - r, c + r, c + r, fill=color, outline="")

    def start(self):
        self._on = True
        self._tick()

    def stop(self):
        self._on = False
        self._draw(False)

    def _tick(self):
        if not self._on:
            return
        self._phase = (self._phase + 1) % 8
        self._draw(self._phase < 4)
        self.after(200, self._tick)


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=P["surface"], height=28)
        self.pack_propagate(False)
        # Left status indicator dot
        self._dot = tk.Canvas(self, width=8, height=8,
                              highlightthickness=0, bg=P["surface"])
        self._dot.pack(side="left", padx=(12, 0), pady=10)
        self._dot_id = self._dot.create_oval(1, 1, 7, 7,
                                             fill=P["success"], outline="")
        self._msg = tk.Label(
            self, text="Initializing…",
            bg=P["surface"], fg=P["dim"],
            font=("Segoe UI", 9), anchor="w", padx=8)
        self._msg.pack(side="left", fill="x", expand=True)
        self._clk = tk.Label(
            self, text="",
            bg=P["surface"], fg=P["muted"],
            font=("Segoe UI", 8), padx=14)
        self._clk.pack(side="right")
        self._tick()

    def set(self, text: str, color: str = P["dim"]):
        self._msg.config(text=text, fg=color)
        self._dot.itemconfig(self._dot_id, fill=color)

    def _tick(self):
        self._clk.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._tick)


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class SettingsWin(tk.Toplevel):
    def __init__(self, root, cfg: Settings,
                 tts: Optional[TTSEngine],
                 stt: Optional[STTEngine]):
        super().__init__(root)
        self.cfg = cfg
        self.tts = tts
        self.stt = stt
        self.title("Settings — Voice Studio")
        self.geometry("520x580")
        self.configure(bg=P["bg"])
        self.resizable(False, False)
        self.transient(root)
        self.grab_set()
        self._build()

    def _lf(self, parent, title: str) -> tk.LabelFrame:
        lf = tk.LabelFrame(
            parent, text=f"  {title}  ",
            bg=P["surf2"], fg=P["accent"],
            font=("Segoe UI", 9, "bold"),
            bd=1, relief="flat", labelanchor="nw",
            padx=10, pady=8)
        lf.pack(fill="x", padx=14, pady=6)
        return lf

    def _row(self, parent, label: str) -> tk.Frame:
        r = tk.Frame(parent, bg=P["surf2"])
        r.pack(fill="x", pady=4)
        tk.Label(r, text=label, width=24, anchor="w",
                 bg=P["surf2"], fg=P["dim"],
                 font=("Segoe UI", 9)).pack(side="left")
        return r

    def _scale(self, parent, var, lo, hi, res=1) -> tk.Scale:
        return tk.Scale(
            parent, variable=var, from_=lo, to=hi,
            resolution=res, orient="horizontal",
            bg=P["surf2"], fg=P["text"],
            troughcolor=P["border"],
            highlightthickness=0, bd=0, length=180,
            activebackground=P["accent"],
            sliderrelief="flat")

    def _combo(self, parent, var, values) -> ttk.Combobox:
        cb = ttk.Combobox(parent, textvariable=var,
                          values=values, state="readonly", width=26)
        return cb

    def _build(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("S.TNotebook",
                    background=P["bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("S.TNotebook.Tab",
                    background=P["surf2"], foreground=P["dim"],
                    padding=[14, 6], font=("Segoe UI", 9, "bold"))
        s.map("S.TNotebook.Tab",
              background=[("selected", P["surf3"])],
              foreground=[("selected", P["accent"])])
        s.configure("S.TCombobox",
                    fieldbackground=P["surf3"], background=P["surf3"],
                    foreground=P["text"], arrowcolor=P["accent"])
        s.map("S.TCombobox", fieldbackground=[("readonly", P["surf3"])])

        nb = ttk.Notebook(self, style="S.TNotebook")
        nb.pack(fill="both", expand=True, padx=14, pady=14)

        t1 = tk.Frame(nb, bg=P["surf2"])
        t2 = tk.Frame(nb, bg=P["surf2"])
        t3 = tk.Frame(nb, bg=P["surf2"])
        nb.add(t1, text="  TTS  ")
        nb.add(t2, text="  STT  ")
        nb.add(t3, text="  General  ")
        self._build_tts(t1)
        self._build_stt(t2)
        self._build_gen(t3)

        bf = tk.Frame(self, bg=P["bg"])
        bf.pack(fill="x", padx=14, pady=(0, 14))

        save_b = _btn(bf, "✓  Save & Close", self._save, color=P["success"])
        save_b.pack(side="right", padx=4)
        canc_b = _btn(bf, "✕  Cancel", self.destroy, color=P["err"])
        canc_b.pack(side="right", padx=4)

    def _build_tts(self, tab):
        f1 = self._lf(tab, "Engine")
        r  = self._row(f1, "Engine:")
        self._v_eng = tk.StringVar(value=self.cfg.tts_engine)
        opts = ["pyttsx3 (offline)"]
        if HAS_GTTS:
            opts.append("gtts (online)")
        self._combo(r, self._v_eng, opts).pack(side="left")

        f2 = self._lf(tab, "Voice  (pyttsx3)")
        r2 = self._row(f2, "Voice:")
        voices = ([f"{i}: {v.name}" for i, v in enumerate(self.tts.voices)]
                  if self.tts else [])
        idx = min(int(self.cfg.tts_voice), len(voices) - 1) if voices else 0
        self._v_voice = tk.StringVar(
            value=voices[idx] if voices else "(none)")
        self._combo(r2, self._v_voice, voices or ["(none)"]).pack(side="left")

        f3 = self._lf(tab, "Speech Parameters")
        r3 = self._row(f3, "Rate (words/min):")
        self._v_rate = tk.IntVar(value=int(self.cfg.tts_rate))
        self._scale(r3, self._v_rate, 50, 300).pack(side="left")

        r4 = self._row(f3, "Volume:")
        self._v_vol = tk.DoubleVar(value=float(self.cfg.tts_volume))
        self._scale(r4, self._v_vol, 0.0, 1.0, res=0.05).pack(side="left")

        f4 = self._lf(tab, "gTTS Language  (online only)")
        r5 = self._row(f4, "Language:")
        self._v_lang = tk.StringVar(value=self.cfg.tts_lang)
        langs = ["en", "es", "fr", "de", "it", "pt", "nl", "ru",
                 "zh-cn", "ja", "ko", "hi", "ar", "tr"]
        self._combo(r5, self._v_lang, langs).pack(side="left")

    def _build_stt(self, tab):
        f1  = self._lf(tab, "Microphone Device")
        r1  = self._row(f1, "Device:")
        mics = ([f"{i}: {m}" for i, m in
                 enumerate(self.stt.list_mics() if self.stt else [])]
                or ["(none detected)"])
        self._v_mic = tk.StringVar(value=mics[0])
        self._combo(r1, self._v_mic, mics).pack(side="left")

        f2 = self._lf(tab, "Recognition Parameters")
        r2 = self._row(f2, "Energy threshold:")
        self._v_energy = tk.IntVar(value=int(self.cfg.stt_energy))
        self._scale(r2, self._v_energy, 50, 4000).pack(side="left")

        r3 = self._row(f2, "Pause threshold (s):")
        self._v_pause = tk.DoubleVar(value=float(self.cfg.stt_pause))
        self._scale(r3, self._v_pause, 0.3, 3.0, res=0.1).pack(side="left")

        r4 = self._row(f2, "Listen timeout (s):")
        self._v_timeout = tk.IntVar(value=int(self.cfg.stt_timeout))
        self._scale(r4, self._v_timeout, 3, 60).pack(side="left")

        r5 = self._row(f2, "Phrase limit (s):")
        self._v_phrase = tk.IntVar(value=int(self.cfg.stt_phrase))
        self._scale(r5, self._v_phrase, 5, 120).pack(side="left")

    def _build_gen(self, tab):
        f1 = self._lf(tab, "Save Behaviour")
        self._v_auto = tk.BooleanVar(value=bool(self.cfg.auto_save))
        tk.Checkbutton(
            f1, text="Auto-save every transcription to VoiceStudio folder",
            variable=self._v_auto,
            bg=P["surf2"], fg=P["text"],
            activebackground=P["surf2"],
            selectcolor=P["accent"],
            font=("Segoe UI", 9)).pack(anchor="w")

        f2 = self._lf(tab, "Display")
        r  = self._row(f2, "Editor font size:")
        self._v_font = tk.IntVar(value=int(self.cfg.font_size))
        self._scale(r, self._v_font, 8, 20).pack(side="left")

    def _save(self):
        raw = self._v_eng.get()
        self.cfg.tts_engine = "gtts" if "gtts" in raw else "pyttsx3"
        try:
            self.cfg.tts_voice = int(self._v_voice.get().split(":")[0])
        except Exception:
            pass
        self.cfg.tts_rate    = int(self._v_rate.get())
        self.cfg.tts_volume  = round(float(self._v_vol.get()), 2)
        self.cfg.tts_lang    = self._v_lang.get()
        self.cfg.stt_energy  = int(self._v_energy.get())
        self.cfg.stt_pause   = round(float(self._v_pause.get()), 2)
        self.cfg.stt_timeout = int(self._v_timeout.get())
        self.cfg.stt_phrase  = int(self._v_phrase.get())
        self.cfg.auto_save   = bool(self._v_auto.get())
        self.cfg.font_size   = int(self._v_font.get())
        self.cfg.save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class VoiceStudio(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE}  {APP_VERSION}")
        self.geometry("960x700")
        self.minsize(820, 600)
        self.configure(bg=P["bg"])

        # Set window icon color hint via title bar (Windows DWM)
        try:
            self.wm_attributes("-alpha", 1.0)
        except Exception:
            pass

        self.cfg = Settings()
        self._q: queue.Queue = queue.Queue()
        self._hist: list     = []

        self._rec_active = False
        self._spk_active = False

        self._tts: Optional[TTSEngine] = None
        self._stt: Optional[STTEngine] = None
        self._tts_err = ""
        self._stt_err = ""

        # Placeholder state for TTS editor
        self._ph    = "Type or paste the text you want to convert to speech…"
        self._ph_on = True

        self._init_engines()
        self._apply_ttk_styles()
        self._build()
        self._poll()

        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.after(400, self._ready_message)

    # ── Engine init ───────────────────────────────────────────────────────────

    def _init_engines(self):
        try:
            self._tts = TTSEngine(self.cfg)
        except Exception as e:
            self._tts_err = str(e)
        try:
            self._stt = STTEngine(self.cfg)
        except Exception as e:
            self._stt_err = str(e)

    # ── TTK styles ────────────────────────────────────────────────────────────

    def _apply_ttk_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",
                    background=P["bg"], borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=P["surf2"], foreground=P["dim"],
                    padding=[18, 10], font=("Segoe UI", 10, "bold"),
                    borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", P["surf3"])],
              foreground=[("selected", P["accent"])])
        s.configure("TScrollbar",
                    background=P["surf3"], troughcolor=P["surface"],
                    arrowcolor=P["muted"], borderwidth=0, relief="flat",
                    width=8)
        s.configure("TCombobox",
                    fieldbackground=P["surf3"], background=P["surf3"],
                    foreground=P["text"], arrowcolor=P["accent"],
                    selectbackground=P["surf3"], selectforeground=P["text"])
        s.map("TCombobox", fieldbackground=[("readonly", P["surf3"])])

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._build_header()
        self._build_tabs()
        self.status = StatusBar(self)
        self.status.pack(fill="x", side="bottom")

    def _build_header(self):
        hdr = tk.Frame(self, bg=P["surface"], height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Accent line at bottom of header
        tk.Frame(hdr, bg=P["border"], height=1).place(relx=0, rely=1.0,
                                                       relwidth=1.0, anchor="sw")

        left = tk.Frame(hdr, bg=P["surface"])
        left.pack(side="left", fill="y", padx=20)

        # Logo dot
        dot = tk.Canvas(left, width=10, height=10,
                        highlightthickness=0, bg=P["surface"])
        dot.pack(side="left", pady=24)
        dot.create_oval(1, 1, 9, 9, fill=P["accent"], outline="")

        tk.Label(left, text=f"  {APP_TITLE}", bg=P["surface"],
                 fg=P["text"], font=("Segoe UI", 15, "bold")).pack(side="left", pady=16)
        tk.Label(left, text=f" v{APP_VERSION}", bg=P["surface"],
                 fg=P["muted"], font=("Segoe UI", 9)).pack(side="left", pady=16)

        # Engine status pills
        pill_frame = tk.Frame(hdr, bg=P["surface"])
        pill_frame.pack(side="left", fill="y", padx=20)
        self._tts_pill = tk.Label(pill_frame, text="",
                                  bg=P["surf3"], fg=P["dim"],
                                  font=("Segoe UI", 8), padx=8, pady=2)
        self._tts_pill.pack(side="left", padx=3, pady=19)
        self._stt_pill = tk.Label(pill_frame, text="",
                                  bg=P["surf3"], fg=P["dim"],
                                  font=("Segoe UI", 8), padx=8, pady=2)
        self._stt_pill.pack(side="left", padx=3, pady=19)

        right = tk.Frame(hdr, bg=P["surface"])
        right.pack(side="right", fill="y", padx=16)

        hist_b = _btn(right, "⏱  History", self._show_history, color=P["purple"])
        hist_b.pack(side="right", padx=4, pady=14)
        sets_b = _btn(right, "⚙  Settings", self._open_settings, color=P["dim"])
        sets_b.pack(side="right", padx=4, pady=14)

    def _build_tabs(self):
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True)

        self._stt_tab = tk.Frame(self._nb, bg=P["bg"])
        self._tts_tab = tk.Frame(self._nb, bg=P["bg"])
        self._nb.add(self._stt_tab, text="   🎙  Speech → Text   ")
        self._nb.add(self._tts_tab, text="   🔊  Text → Speech   ")

        self._build_stt_tab(self._stt_tab)
        self._build_tts_tab(self._tts_tab)

    # ══════════════════════════════════════════════════════════════════════════
    #  STT TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_stt_tab(self, tab):
        # ── Source bar ────────────────────────────────────────────────────────
        src = tk.Frame(tab, bg=P["surface"], height=50)
        src.pack(fill="x")
        src.pack_propagate(False)
        tk.Frame(src, bg=P["border"], height=1).pack(fill="x", side="bottom")

        tk.Label(src, text="Source:", bg=P["surface"], fg=P["dim"],
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(16, 6))

        self._stt_src = tk.StringVar(value="mic")
        for val, lbl, icon in [("mic",  "Microphone", "🎤"),
                                ("file", "Audio File", "📂")]:
            tk.Radiobutton(
                src, text=f"{icon}  {lbl}",
                variable=self._stt_src, value=val,
                command=self._stt_toggle_source,
                bg=P["surface"], fg=P["text"],
                activebackground=P["surface"],
                selectcolor=P["accent"],
                font=("Segoe UI", 9), cursor="hand2").pack(side="left", padx=10)

        self._stt_file_bar = tk.Frame(src, bg=P["surface"])
        self._stt_file_var = tk.StringVar()
        tk.Entry(
            self._stt_file_bar, textvariable=self._stt_file_var,
            width=30, bg=P["surf3"], fg=P["dim"],
            insertbackground=P["text"], relief="flat",
            font=("Segoe UI", 9)).pack(side="left", padx=(8, 2), ipady=3)
        _btn(self._stt_file_bar, "Browse…",
             self._stt_browse, color=P["muted"]).pack(side="left")

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(tab, bg=P["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=14)

        # ── Sidebar ───────────────────────────────────────────────────────────
        side = tk.Frame(body, bg=P["surf2"], width=204)
        side.pack(side="left", fill="y", padx=(0, 14))
        side.pack_propagate(False)

        # Padding inside sidebar
        inner = tk.Frame(side, bg=P["surf2"])
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        # Status row
        st_row = tk.Frame(inner, bg=P["surf2"])
        st_row.pack(fill="x", pady=(0, 8))
        self._pulse = PulseLight(st_row, bg=P["surf2"])
        self._pulse.pack(side="left")
        self._stt_st = tk.Label(st_row, text="Idle",
                                bg=P["surf2"], fg=P["muted"],
                                font=("Segoe UI", 9))
        self._stt_st.pack(side="left", padx=6)

        self._btn_rec = _btn(inner, "⏺  Start Recording",
                             self._toggle_record, color=P["err"])
        self._btn_rec.pack(fill="x", pady=(0, 4), ipady=6)

        _hsep(inner, pady=6)

        tk.Label(inner, text="SAVE FORMAT", bg=P["surf2"], fg=P["muted"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(4, 2))
        self._stt_fmt = tk.StringVar(value="txt")
        for ext, lbl in [("txt", "Plain Text  (.txt)"),
                         ("md",  "Markdown    (.md) "),
                         ("log", "Log File    (.log)")]:
            tk.Radiobutton(
                inner, text=lbl, variable=self._stt_fmt, value=ext,
                bg=P["surf2"], fg=P["text"],
                activebackground=P["surf2"], selectcolor=P["accent"],
                font=("Courier", 9), cursor="hand2").pack(anchor="w", pady=1)

        _hsep(inner, pady=6)

        _btn(inner, "💾  Save Transcript", self._stt_save,
             color=P["success"]).pack(fill="x", pady=2, ipady=4)
        _btn(inner, "📋  Copy All", self._stt_copy,
             color=P["accent"]).pack(fill="x", pady=2, ipady=4)
        _btn(inner, "🗑  Clear", self._stt_clear,
             color=P["muted"]).pack(fill="x", pady=2, ipady=4)

        _hsep(inner, pady=6)

        self._stt_append = tk.BooleanVar(value=True)
        tk.Checkbutton(
            inner, text="Append new results",
            variable=self._stt_append,
            bg=P["surf2"], fg=P["dim"],
            activebackground=P["surf2"], selectcolor=P["accent"],
            font=("Segoe UI", 9)).pack(anchor="w")

        # ── Right: text area ──────────────────────────────────────────────────
        right = tk.Frame(body, bg=P["bg"])
        right.pack(fill="both", expand=True)

        top = tk.Frame(right, bg=P["bg"])
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Transcription Output",
                 bg=P["bg"], fg=P["text"],
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        self._stt_wc = tk.Label(top, text="0 words",
                                bg=P["bg"], fg=P["muted"],
                                font=("Segoe UI", 9))
        self._stt_wc.pack(side="right")

        outer = tk.Frame(right, bg=P["border2"], bd=1)
        outer.pack(fill="both", expand=True)
        self._stt_box = tk.Text(
            outer, bg=P["surf2"], fg=P["text"],
            insertbackground=P["accent"],
            relief="flat", bd=0, padx=16, pady=12,
            font=("Segoe UI", int(self.cfg.font_size)),
            wrap="word", undo=True,
            selectbackground=P["accent"], selectforeground="#ffffff",
            spacing3=3,
        )
        vsb = ttk.Scrollbar(outer, orient="vertical",
                            command=self._stt_box.yview)
        self._stt_box.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._stt_box.pack(fill="both", expand=True)
        self._stt_box.bind("<<Modified>>", self._stt_modified)

    # ══════════════════════════════════════════════════════════════════════════
    #  TTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_tts_tab(self, tab):
        body = tk.Frame(tab, bg=P["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=14)

        # ── Sidebar ───────────────────────────────────────────────────────────
        side = tk.Frame(body, bg=P["surf2"], width=204)
        side.pack(side="left", fill="y", padx=(0, 14))
        side.pack_propagate(False)

        inner = tk.Frame(side, bg=P["surf2"])
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        # Speak status row
        spk_row = tk.Frame(inner, bg=P["surf2"])
        spk_row.pack(fill="x", pady=(0, 8))
        self._spk_light = SpeakLight(spk_row, bg=P["surf2"])
        self._spk_light.pack(side="left")
        self._spk_st = tk.Label(spk_row, text="Idle",
                                bg=P["surf2"], fg=P["muted"],
                                font=("Segoe UI", 9))
        self._spk_st.pack(side="left", padx=6)

        self._btn_spk = _btn(inner, "▶  Speak Text",
                             self._toggle_speak, color=P["accent"])
        self._btn_spk.pack(fill="x", pady=(0, 4), ipady=6)

        _hsep(inner, pady=6)

        tk.Label(inner, text="TEXT SOURCE", bg=P["surf2"], fg=P["muted"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(4, 2))
        self._tts_src = tk.StringVar(value="editor")
        for val, lbl in [("editor", "Type in editor"),
                         ("file",   "Load from file"),
                         ("clip",   "From clipboard")]:
            tk.Radiobutton(
                inner, text=lbl, variable=self._tts_src, value=val,
                command=self._tts_src_changed,
                bg=P["surf2"], fg=P["text"],
                activebackground=P["surf2"], selectcolor=P["accent"],
                font=("Segoe UI", 9), cursor="hand2").pack(anchor="w", pady=1)

        # File row (hidden initially)
        self._tts_file_frame = tk.Frame(inner, bg=P["surf2"])
        self._tts_file_var   = tk.StringVar()
        tk.Entry(
            self._tts_file_frame, textvariable=self._tts_file_var,
            width=20, bg=P["surf3"], fg=P["dim"],
            insertbackground=P["text"],
            relief="flat", font=("Segoe UI", 8)).pack(fill="x", pady=(3, 0),
                                                        ipady=3)
        _btn(self._tts_file_frame, "Browse text file…",
             self._tts_browse, color=P["muted"]).pack(fill="x", pady=2)

        _hsep(inner, pady=6)

        tk.Label(inner, text="AUDIO FORMAT", bg=P["surf2"], fg=P["muted"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(4, 2))
        self._tts_fmt = tk.StringVar(value="wav")
        for ext, lbl in [("wav", "WAV  (offline)"),
                         ("mp3", "MP3  (online) ")]:
            tk.Radiobutton(
                inner, text=lbl, variable=self._tts_fmt, value=ext,
                bg=P["surf2"], fg=P["text"],
                activebackground=P["surf2"], selectcolor=P["accent"],
                font=("Courier", 9), cursor="hand2").pack(anchor="w", pady=1)

        _hsep(inner, pady=6)

        _btn(inner, "💾  Save Audio", self._tts_save_audio,
             color=P["success"]).pack(fill="x", pady=2, ipady=4)
        _btn(inner, "📂  Load Text File", self._tts_load_file,
             color=P["accent2"]).pack(fill="x", pady=2, ipady=4)
        _btn(inner, "🗑  Clear", self._tts_clear,
             color=P["muted"]).pack(fill="x", pady=2, ipady=4)

        _hsep(inner, pady=6)

        self._tts_wc = tk.Label(inner, text="0 words  |  0 chars",
                                bg=P["surf2"], fg=P["muted"],
                                font=("Segoe UI", 8), anchor="w")
        self._tts_wc.pack(anchor="w")

        # ── Right: editor ─────────────────────────────────────────────────────
        right = tk.Frame(body, bg=P["bg"])
        right.pack(fill="both", expand=True)

        hdr = tk.Frame(right, bg=P["bg"])
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="Text Editor",
                 bg=P["bg"], fg=P["text"],
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(hdr, text="  Type, paste, or load a file",
                 bg=P["bg"], fg=P["muted"],
                 font=("Segoe UI", 9)).pack(side="left")

        # Quick-insert chips
        chips = tk.Frame(right, bg=P["surf3"])
        chips.pack(fill="x", pady=(0, 6))
        tk.Label(chips, text="  Quick insert: ",
                 bg=P["surf3"], fg=P["muted"],
                 font=("Segoe UI", 8)).pack(side="left", pady=5)
        for snip in ["Hello, world!", "Testing 1 2 3.", "Good morning!", "Thank you."]:
            b = tk.Button(
                chips, text=snip,
                bg=P["surf4"], fg=P["dim"],
                activebackground=P["border"], activeforeground=P["text"],
                relief="flat", font=("Segoe UI", 8),
                padx=8, pady=3, cursor="hand2",
                command=lambda s=snip: self._quick_insert(s))
            b.pack(side="left", padx=3, pady=5)

        outer = tk.Frame(right, bg=P["border2"], bd=1)
        outer.pack(fill="both", expand=True)
        self._tts_box = tk.Text(
            outer, bg=P["surf2"], fg=P["text"],
            insertbackground=P["accent"],
            relief="flat", bd=0, padx=16, pady=12,
            font=("Segoe UI", int(self.cfg.font_size)),
            wrap="word", undo=True,
            selectbackground=P["accent"], selectforeground="#ffffff",
            spacing3=3,
        )
        vsb2 = ttk.Scrollbar(outer, orient="vertical",
                             command=self._tts_box.yview)
        self._tts_box.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        self._tts_box.pack(fill="both", expand=True)
        self._tts_box.bind("<<Modified>>", self._tts_modified)

        # Set placeholder
        self._tts_box.insert("1.0", self._ph)
        self._tts_box.config(fg=P["muted"])
        self._tts_box.bind("<FocusIn>",  self._ph_clear)
        self._tts_box.bind("<FocusOut>", self._ph_restore)

    # ══════════════════════════════════════════════════════════════════════════
    #  STT CONTROLS
    # ══════════════════════════════════════════════════════════════════════════

    def _stt_toggle_source(self):
        if self._stt_src.get() == "file":
            self._stt_file_bar.pack(side="left", padx=(10, 0), fill="y")
        else:
            self._stt_file_bar.pack_forget()

    def _stt_browse(self):
        p = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=AUDIO_FILETYPES,
            initialdir=self.cfg.save_dir,
            parent=self)
        if p:
            self._stt_file_var.set(p)

    def _toggle_record(self):
        if not self._stt:
            messagebox.showerror(
                "STT Unavailable",
                f"Speech recognition engine failed:\n\n{self._stt_err}",
                parent=self)
            return
        if self._rec_active:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        src = self._stt_src.get()
        if src == "file":
            path = self._stt_file_var.get().strip()
            if not path:
                messagebox.showwarning(
                    "No File Selected",
                    "Please select an audio file first.", parent=self)
                return
            if not Path(path).exists():
                messagebox.showerror(
                    "File Not Found",
                    f"The file could not be found:\n{path}", parent=self)
                return

        self._rec_active = True
        self._pulse.start()
        self._btn_rec.config(text="⏹  Stop", bg=P["warn"], fg="#ffffff")
        self.status.set("Recording…", P["err"])

        cb = dict(
            on_status=lambda m: self._q.put(("stt_st", m)),
            on_result=lambda t: self._q.put(("stt_ok", t)),
            on_error =lambda e: self._q.put(("stt_err", e)),
        )
        if src == "mic":
            self._stt.transcribe_mic(**cb)
        else:
            self._stt.transcribe_file(self._stt_file_var.get().strip(), **cb)

    def _stop_record(self):
        self._rec_active = False
        if self._stt:
            self._stt.stop()
        self._pulse.stop()
        self._btn_rec.config(text="⏺  Start Recording", bg=P["surf3"],
                             fg=P["dim"])
        self._stt_st.config(text="Idle", fg=P["muted"])
        self.status.set("Recording stopped.", P["dim"])

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
            title="Select Text File",
            filetypes=TEXT_FILETYPES,
            initialdir=self.cfg.save_dir,
            parent=self)
        if p:
            self._tts_file_var.set(p)
            self._load_text_path(p)

    def _toggle_speak(self):
        if not self._tts:
            messagebox.showerror(
                "TTS Unavailable",
                f"Text-to-speech engine failed:\n\n{self._tts_err}",
                parent=self)
            return
        if self._spk_active:
            self._stop_speak()
        else:
            self._start_speak()

    def _start_speak(self):
        text = self._get_tts_text()
        if not text.strip():
            messagebox.showwarning(
                "Nothing to Speak",
                "The text editor is empty.\n"
                "Please type or load some text first.", parent=self)
            return

        # FIX: Reset stop flag before speaking
        if self._tts:
            self._tts._stop.clear()

        self._spk_active = True
        self._spk_light.start()
        self._btn_spk.config(text="⏹  Stop", bg=P["warn"], fg="#ffffff")
        self._spk_st.config(text="Speaking…", fg=P["accent"])
        self.status.set("Speaking…", P["accent"])

        self._tts.speak_async(
            text,
            on_done =lambda:   self._q.put(("tts_done", "")),
            on_error=lambda e: self._q.put(("tts_err",  e)),
        )

    def _stop_speak(self):
        self._spk_active = False
        if self._tts:
            self._tts.stop()
        self._spk_light.stop()
        self._btn_spk.config(text="▶  Speak Text", bg=P["surf3"], fg=P["dim"])
        self._spk_st.config(text="Idle", fg=P["muted"])
        self.status.set("Speech stopped.", P["dim"])

    # ══════════════════════════════════════════════════════════════════════════
    #  SAVE / LOAD
    # ══════════════════════════════════════════════════════════════════════════

    def _stt_save(self):
        text = self._stt_box.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Nothing to Save",
                                   "Transcription box is empty.", parent=self)
            return
        ext = self._stt_fmt.get()
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title="Save Transcription",
            defaultextension=f".{ext}",
            filetypes=TEXT_FILETYPES,
            initialdir=self.cfg.save_dir,
            initialfile=f"transcript_{ts}.{ext}",
            parent=self,
        )
        if not path:
            return
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if ext == "md":
                content = (f"# Transcription\n\n"
                           f"> *Voice Studio — {now}*\n\n---\n\n{text}\n")
            elif ext == "log":
                content = (f"[{datetime.datetime.now().isoformat()}] TRANSCRIPTION\n"
                           f"{'─' * 60}\n{text}\n{'─' * 60}\n")
            else:
                content = text
            p.write_text(content, encoding="utf-8")
            self.cfg.save_dir = str(p.parent)
            self._hist.append(("STT Save", p.name))
            self.status.set(f"Saved  →  {p.name}", P["success"])
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
            self.status.set("Copied to clipboard.", P["success"])

    def _stt_clear(self):
        self._stt_box.delete("1.0", "end")
        self._stt_wc.config(text="0 words")

    def _tts_save_audio(self):
        if not self._tts:
            messagebox.showerror("TTS Unavailable",
                                 "TTS engine is not available.", parent=self)
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
                "MP3 export requires gTTS (online).\n"
                "Install: pip install gTTS\n\n"
                "Or switch to WAV format.", parent=self)
            return

        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title="Save Audio File",
            defaultextension=f".{ext}",
            filetypes=AUDIO_FILETYPES,
            initialdir=self.cfg.save_dir,
            initialfile=f"speech_{ts}.{ext}",
            parent=self,
        )
        if not path:
            return

        # FIX: Temporarily override engine for mp3 export without mutating saved cfg
        orig_eng = self.cfg._d.get("tts_engine", "pyttsx3")
        if ext == "mp3":
            self.cfg._d["tts_engine"] = "gtts"

        self.status.set("Saving audio…", P["warn"])
        self.update_idletasks()

        def _done(saved):
            self.cfg._d["tts_engine"] = orig_eng
            self._q.put(("tts_saved", saved))

        def _err(msg):
            self.cfg._d["tts_engine"] = orig_eng
            self._q.put(("tts_err", msg))

        self._tts.save_to_file(text, path, on_done=_done, on_error=_err)

    def _tts_load_file(self):
        p = filedialog.askopenfilename(
            title="Load Text File",
            filetypes=TEXT_FILETYPES,
            initialdir=self.cfg.save_dir,
            parent=self)
        if p:
            self._load_text_path(p)

    def _tts_clear(self):
        self._tts_box.delete("1.0", "end")
        self._ph_restore(None)

    # ── Text helpers ──────────────────────────────────────────────────────────

    def _get_tts_text(self) -> str:
        src = self._tts_src.get()
        if src == "editor":
            if self._ph_on:
                return ""
            return self._tts_box.get("1.0", "end-1c")
        if src == "file":
            p = self._tts_file_var.get().strip()
            if not p:
                if self._ph_on:
                    return ""
                return self._tts_box.get("1.0", "end-1c")
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

    def _load_text_path(self, path: str):
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            self._ph_clear(None)
            self._tts_box.delete("1.0", "end")
            self._tts_box.insert("1.0", text)
            self._tts_box.config(fg=P["text"])
            self.cfg.save_dir = str(Path(path).parent)
            self.status.set(
                f"Loaded  {Path(path).name}  ({len(text):,} chars)", P["success"])
        except FileNotFoundError:
            messagebox.showerror("Not Found",  f"File not found:\n{path}",  parent=self)
        except PermissionError:
            messagebox.showerror("Permission", f"Cannot read:\n{path}",     parent=self)
        except OSError as e:
            messagebox.showerror("Read Error", str(e),                      parent=self)

    def _load_clipboard(self):
        try:
            text = self.clipboard_get()
            if text.strip():
                self._ph_clear(None)
                self._tts_box.delete("1.0", "end")
                self._tts_box.insert("1.0", text)
                self._tts_box.config(fg=P["text"])
                self.status.set(
                    f"Loaded {len(text):,} chars from clipboard.", P["success"])
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e), parent=self)

    def _quick_insert(self, s: str):
        self._ph_clear(None)
        pos = self._tts_box.index("end-1c")
        cur = self._tts_box.get("1.0", "end-1c")
        sep = " " if cur and not cur.endswith(" ") else ""
        self._tts_box.insert("end", sep + s)
        self._tts_box.config(fg=P["text"])

    # ── Placeholder ───────────────────────────────────────────────────────────

    def _ph_clear(self, _e):
        if self._ph_on:
            self._tts_box.delete("1.0", "end")
            self._tts_box.config(fg=P["text"])
            self._ph_on = False

    def _ph_restore(self, _e):
        if not self._tts_box.get("1.0", "end-1c").strip():
            self._tts_box.insert("1.0", self._ph)
            self._tts_box.config(fg=P["muted"])
            self._ph_on = True

    # ── Word count ────────────────────────────────────────────────────────────

    def _stt_modified(self, _e):
        self._stt_box.edit_modified(False)
        t = self._stt_box.get("1.0", "end-1c")
        w = len(t.split()) if t.strip() else 0
        self._stt_wc.config(text=f"{w:,} words")

    def _tts_modified(self, _e):
        self._tts_box.edit_modified(False)
        if self._ph_on:
            self._tts_wc.config(text="0 words  |  0 chars")
            return
        t = self._tts_box.get("1.0", "end-1c")
        w = len(t.split()) if t.strip() else 0
        self._tts_wc.config(text=f"{w:,} words  |  {len(t):,} chars")

    # ══════════════════════════════════════════════════════════════════════════
    #  QUEUE POLL  (thread-safe UI updates)
    # ══════════════════════════════════════════════════════════════════════════

    def _poll(self):
        try:
            while True:
                kind, payload = self._q.get_nowait()

                if kind == "stt_st":
                    self._stt_st.config(text=payload, fg=P["accent"])
                    self.status.set(payload, P["accent"])

                elif kind == "stt_ok":
                    self._rec_active = False
                    self._pulse.stop()
                    self._btn_rec.config(text="⏺  Start Recording",
                                        bg=P["surf3"], fg=P["dim"])
                    self._stt_st.config(text="Done ✓", fg=P["success"])
                    prev = payload[:70] + "…" if len(payload) > 70 else payload
                    self.status.set(f"Transcribed:  {prev}", P["success"])
                    if self._stt_append.get():
                        ex = self._stt_box.get("1.0", "end-1c").strip()
                        self._stt_box.insert("end",
                                             ("\n\n" if ex else "") + payload)
                    else:
                        self._stt_box.delete("1.0", "end")
                        self._stt_box.insert("1.0", payload)
                    self._stt_box.see("end")
                    self._hist.append(("STT", payload[:80]))
                    if self.cfg.auto_save:
                        self._auto_save(payload)

                elif kind == "stt_err":
                    self._rec_active = False
                    self._pulse.stop()
                    self._btn_rec.config(text="⏺  Start Recording",
                                        bg=P["surf3"], fg=P["dim"])
                    self._stt_st.config(text="Error", fg=P["err"])
                    self.status.set(f"Error — {payload[:80]}", P["err"])
                    messagebox.showerror("Transcription Error", payload,
                                        parent=self)

                elif kind == "tts_done":
                    self._spk_active = False
                    self._spk_light.stop()
                    self._btn_spk.config(text="▶  Speak Text",
                                        bg=P["surf3"], fg=P["dim"])
                    self._spk_st.config(text="Done ✓", fg=P["success"])
                    self.status.set("Speech complete.", P["success"])

                elif kind == "tts_err":
                    self._spk_active = False
                    self._spk_light.stop()
                    self._btn_spk.config(text="▶  Speak Text",
                                        bg=P["surf3"], fg=P["dim"])
                    self._spk_st.config(text="Error", fg=P["err"])
                    self.status.set(f"TTS Error — {payload[:80]}", P["err"])
                    messagebox.showerror("TTS Error", payload, parent=self)

                elif kind == "tts_saved":
                    self.cfg.save_dir = str(Path(payload).parent)
                    self._hist.append(("TTS Save", Path(payload).name))
                    self.status.set(
                        f"Audio saved  →  {Path(payload).name}", P["success"])
                    messagebox.showinfo(
                        "Audio Saved",
                        f"File saved successfully:\n{payload}", parent=self)

        except queue.Empty:
            pass
        self.after(80, self._poll)

    # ══════════════════════════════════════════════════════════════════════════
    #  DIALOGS
    # ══════════════════════════════════════════════════════════════════════════

    def _open_settings(self):
        SettingsWin(self, self.cfg, self._tts, self._stt)

    def _show_history(self):
        win = tk.Toplevel(self)
        win.title("Session History — Voice Studio")
        win.geometry("560x400")
        win.configure(bg=P["bg"])
        win.transient(self)

        hdr = tk.Frame(win, bg=P["surface"], height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Session History",
                 bg=P["surface"], fg=P["text"],
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=16, pady=12)

        count_lbl = tk.Label(
            hdr, text=f"{len(self._hist)} entries",
            bg=P["surface"], fg=P["muted"],
            font=("Segoe UI", 9))
        count_lbl.pack(side="right", padx=16)

        outer = tk.Frame(win, bg=P["border2"], bd=1)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        txt = tk.Text(
            outer, bg=P["surf2"], fg=P["text"],
            relief="flat", bd=0, padx=14, pady=10,
            font=("Consolas", 9), wrap="word", state="disabled",
            selectbackground=P["accent"])
        sb = ttk.Scrollbar(outer, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)

        txt.config(state="normal")
        if not self._hist:
            txt.insert("1.0", "No activity this session.")
        else:
            for kind, val in reversed(self._hist):
                ts_now = datetime.datetime.now().strftime("%H:%M")
                txt.insert("end", f"[{ts_now}] [{kind}]\n  {val}\n\n")
        txt.config(state="disabled")

        bf = tk.Frame(win, bg=P["bg"])
        bf.pack(fill="x", padx=16, pady=(0, 14))
        _btn(bf, "Clear History", lambda: [self._hist.clear(),
                                            txt.config(state="normal"),
                                            txt.delete("1.0", "end"),
                                            txt.insert("1.0",
                                                       "History cleared."),
                                            txt.config(state="disabled")],
             color=P["err"]).pack(side="right")
        _btn(bf, "Close", win.destroy, color=P["muted"]).pack(side="right",
                                                               padx=4)

    # ── Auto-save ─────────────────────────────────────────────────────────────

    def _auto_save(self, text: str):
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            (SAVE_DIR / f"auto_{ts}.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass

    # ── Ready message + status pills ─────────────────────────────────────────

    def _ready_message(self):
        parts = []

        if self._tts:
            eng  = self.cfg.tts_engine
            pill = f"TTS: {eng}"
            self._tts_pill.config(text=f"● {pill}",
                                  fg=P["success"], bg=P["surf3"])
            parts.append(pill)
        else:
            self._tts_pill.config(text="● TTS: unavailable",
                                  fg=P["err"], bg=P["surf3"])
            parts.append("TTS: unavailable")

        if self._stt:
            mic  = "mic OK" if self._stt.mic_available else "no mic"
            pill = f"STT: Google ({mic})"
            self._stt_pill.config(text=f"● {pill}",
                                  fg=P["success"] if "OK" in mic else P["warn"],
                                  bg=P["surf3"])
            parts.append(pill)
        else:
            self._stt_pill.config(text="● STT: unavailable",
                                  fg=P["err"], bg=P["surf3"])
            parts.append("STT: unavailable")

        color = P["success"] if (self._tts and self._stt) else P["warn"]
        self.status.set("Ready  ·  " + "   ·   ".join(parts), color)

    # ── Quit ──────────────────────────────────────────────────────────────────

    def _quit(self):
        if self._rec_active and self._stt:
            self._stt.stop()
        if self._spk_active and self._tts:
            self._tts.stop()
        self.cfg.save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Suppress all console output for packaged/GUI usage
    if getattr(sys, "frozen", False):
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    try:
        app = VoiceStudio()
        app.mainloop()
    except Exception:
        err = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Fatal Startup Error",
                f"Voice Studio could not start:\n\n{err}")
            root.destroy()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()