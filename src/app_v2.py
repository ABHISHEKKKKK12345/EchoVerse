"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VOICE STUDIO   —  Production Edition                      ║
║          Speech ↔ Text · Premium UI · Robust · Cross-Platform                ║
║                          Author: Abhishek                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Install:
    pip install SpeechRecognition pyttsx3 gTTS pyaudio pydub pygame

Linux extras:
    sudo apt install portaudio19-dev python3-tk espeak
"""

# ── Suppress noise before any imports ─────────────────────────────────────────
import warnings, io, os, sys
warnings.filterwarnings("ignore")

_stderr0 = sys.stderr
sys.stderr = io.StringIO()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

sys.stderr = _stderr0

# ── stdlib ────────────────────────────────────────────────────────────────────
import threading
import queue
import time
import json
import tempfile
import datetime
import traceback
import logging
import hashlib  # noqa: F401 (reserved for future checksum use)
from pathlib import Path
from typing import Optional, Callable, Tuple
from dataclasses import dataclass, field

# ── Logging setup ─────────────────────────────────────────────────────────────
SAVE_DIR      = Path.home() / "VoiceStudio"
SETTINGS_PATH = SAVE_DIR / ".settings.json"
LOG_PATH      = SAVE_DIR / "voicestudio.log"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

_file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"))

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(message)s"))

logging.basicConfig(level=logging.DEBUG, handlers=[_file_handler, _console_handler])

# Silence noisy third-party loggers (comtypes, urllib3, etc.)
for _noisy in ("comtypes", "comtypes.client", "comtypes._post_coinit",
               "comtypes._post_coinit.unknwn", "comtypes.client._managing",
               "urllib3", "urllib3.connectionpool"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

log = logging.getLogger("VoiceStudio")

# ── Optional dependencies ──────────────────────────────────────────────────────
def _try_import(name, pip_name=None):
    try:
        mod = __import__(name)
        log.debug(f"Loaded: {name}")
        return mod, True
    except ImportError:
        log.warning(f"Optional dependency missing: {pip_name or name}")
        return None, False

sr_mod, HAS_SR         = _try_import("speech_recognition", "SpeechRecognition")
pyttsx3_mod, HAS_PY3   = _try_import("pyttsx3")
gtts_mod, HAS_GTTS     = _try_import("gtts")
pydub_mod, HAS_PYDUB   = _try_import("pydub")

if HAS_SR:   import speech_recognition as sr
if HAS_PY3:  import pyttsx3
if HAS_GTTS: from gtts import gTTS

HAS_PYGAME = False
_s0, _s1 = sys.stderr, sys.stdout
try:
    sys.stderr = sys.stdout = io.StringIO()
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
    log.debug("Loaded: pygame")
except Exception as e:
    log.warning(f"pygame unavailable: {e}")
finally:
    sys.stderr, sys.stdout = _s0, _s1

if HAS_PYDUB:
    from pydub import AudioSegment
    from pydub.playback import play as _pydub_play


# ══════════════════════════════════════════════════════════════════════════════
#  THEME  — Deep Cosmic Dark with Amber/Teal accents
# ══════════════════════════════════════════════════════════════════════════════

C = {
    # Base layers
    "void":      "#04050a",
    "bg":        "#070b12",
    "layer1":    "#0b1019",
    "layer2":    "#0f1522",
    "layer3":    "#14192e",
    "layer4":    "#19203a",
    "layer5":    "#1f2844",
    # Borders
    "edge0":     "#1a2236",
    "edge1":     "#243050",
    "edge2":     "#2e3d64",
    "edge3":     "#3a4d7a",
    # Accents
    "amber":     "#f5a623",
    "amber_dim": "#c47a10",
    "amber_glow":"#ff9500",
    "teal":      "#00d4aa",
    "teal_dim":  "#00a882",
    "teal_glow": "#00ffcc",
    "blue":      "#3d8eff",
    "blue_dim":  "#2265cc",
    "rose":      "#ff4d6d",
    "rose_dim":  "#cc2a47",
    "violet":    "#9f7aea",
    "gold":      "#ffd700",
    # Text
    "txt":       "#dde4f5",
    "txt_dim":   "#8899bb",
    "txt_muted": "#4a5a7a",
    "txt_faint": "#2a3450",
    # State
    "ok":        "#22d3a4",
    "warn":      "#f5a623",
    "err":       "#ff4d6d",
    "info":      "#3d8eff",
    # Misc
    "white":     "#ffffff",
    "black":     "#000000",
    "glass":     "#ffffff0a",
    "glass2":    "#ffffff14",
}

APP_TITLE   = "Voice Studio"
APP_VERSION = "2.0"
FONT_MONO   = "Consolas"
FONT_UI     = "Segoe UI"


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class Settings:
    DEFAULTS = {
        "tts_engine":    "pyttsx3",
        "tts_rate":      175,
        "tts_volume":    1.0,
        "tts_voice":     0,
        "tts_lang":      "en",
        "stt_energy":    300,
        "stt_pause":     0.8,
        "stt_timeout":   10,
        "stt_phrase":    30,
        "save_dir":      str(SAVE_DIR),
        "auto_save":     False,
        "font_size":     11,
        "theme_accent":  "amber",
        "history_limit": 200,
        "mic_index":     -1,
        "startup_tab":   0,
    }

    def __init__(self):
        self._d = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        try:
            if SETTINGS_PATH.exists():
                saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                self._d.update({k: v for k, v in saved.items() if k in self.DEFAULTS})
                log.debug("Settings loaded.")
        except Exception as e:
            log.warning(f"Settings load failed: {e}")

    def save(self):
        try:
            SETTINGS_PATH.write_text(
                json.dumps(self._d, indent=2), encoding="utf-8")
        except Exception as e:
            log.error(f"Settings save failed: {e}")

    def __getattr__(self, k):
        if k.startswith("_"): raise AttributeError(k)
        return self._d.get(k, self.DEFAULTS.get(k))

    def __setattr__(self, k, v):
        if k.startswith("_"):
            object.__setattr__(self, k, v)
        else:
            self._d[k] = v
            self.save()


# ══════════════════════════════════════════════════════════════════════════════
#  TTS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class TTSEngine:
    """Thread-safe TTS. Fresh pyttsx3 instance per call (prevents run-loop bugs)."""

    def __init__(self, cfg: Settings):
        self.cfg    = cfg
        self._lock  = threading.Lock()
        self._stop  = threading.Event()
        self._active_engine = None
        self._voices = []
        self._probe_voices()

    def _probe_voices(self):
        if not HAS_PY3: return
        try:
            eng = pyttsx3.init()
            self._voices = list(eng.getProperty("voices") or [])
            eng.stop(); del eng
            log.debug(f"TTS voices found: {len(self._voices)}")
        except Exception as e:
            log.warning(f"Voice probe failed: {e}")

    @property
    def voices(self): return self._voices

    def _make_engine(self):
        eng = pyttsx3.init()
        eng.setProperty("rate",   max(50, min(400, int(self.cfg.tts_rate))))
        eng.setProperty("volume", max(0.0, min(1.0, float(self.cfg.tts_volume))))
        if self._voices:
            idx = min(max(0, int(self.cfg.tts_voice)), len(self._voices) - 1)
            eng.setProperty("voice", self._voices[idx].id)
        return eng

    def speak_async(self, text: str, on_done=None, on_error=None) -> threading.Thread:
        self._stop.clear()
        def _run():
            with self._lock:
                try:
                    text_clean = text.strip()
                    if not text_clean:
                        raise ValueError("Empty text provided.")
                    if self.cfg.tts_engine == "gtts" and HAS_GTTS:
                        self._speak_gtts(text_clean)
                    elif HAS_PY3:
                        self._speak_pyttsx3(text_clean)
                    else:
                        raise RuntimeError(
                            "No TTS engine available.\nInstall: pip install pyttsx3")
                    if not self._stop.is_set() and on_done:
                        on_done()
                except Exception as e:
                    log.error(f"TTS speak error: {e}", exc_info=True)
                    self._active_engine = None
                    if not self._stop.is_set() and on_error:
                        on_error(str(e))
        t = threading.Thread(target=_run, daemon=True, name="TTS-speak")
        t.start()
        return t

    def _speak_pyttsx3(self, text: str):
        eng = self._make_engine()
        self._active_engine = eng
        try:
            if not self._stop.is_set():
                eng.say(text)
                eng.runAndWait()
        finally:
            self._active_engine = None
            try: eng.stop()
            except Exception: pass
            del eng

    def _speak_gtts(self, text: str):
        tts = gTTS(text=text, lang=self.cfg.tts_lang, slow=False)
        fd, tmp = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            tts.save(tmp)
            if not self._stop.is_set():
                self._play_file(tmp)
        finally:
            try: os.unlink(tmp)
            except Exception: pass

    def _play_file(self, path: str):
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
            except Exception as e:
                log.warning(f"Pygame playback failed: {e}")
        if HAS_PYDUB:
            try:
                _pydub_play(AudioSegment.from_file(path)); return
            except Exception as e:
                log.warning(f"Pydub playback failed: {e}")
        # OS fallback
        if sys.platform == "win32":
            os.system(f'start /wait "" "{path}"')
        elif sys.platform == "darwin":
            os.system(f'afplay "{path}"')
        else:
            os.system(f'aplay "{path}" 2>/dev/null || mpg123 "{path}" 2>/dev/null')

    def save_to_file(self, text: str, path: str,
                     on_done=None, on_error=None) -> threading.Thread:
        def _run():
            with self._lock:
                try:
                    text_clean = text.strip()
                    if not text_clean:
                        raise ValueError("Empty text.")
                    p = Path(path)
                    if self.cfg.tts_engine == "gtts" and HAS_GTTS:
                        out = p.with_suffix(".mp3")
                        gTTS(text=text_clean, lang=self.cfg.tts_lang,
                             slow=False).save(str(out))
                        if on_done: on_done(str(out))
                    elif HAS_PY3:
                        out = p.with_suffix(".wav")
                        eng = self._make_engine()
                        eng.save_to_file(text_clean, str(out))
                        eng.runAndWait()
                        try: eng.stop()
                        except Exception: pass
                        del eng
                        if on_done: on_done(str(out))
                    else:
                        raise RuntimeError("No TTS engine.")
                except Exception as e:
                    log.error(f"TTS save error: {e}", exc_info=True)
                    if on_error: on_error(str(e))
        t = threading.Thread(target=_run, daemon=True, name="TTS-save")
        t.start()
        return t

    def stop(self):
        self._stop.set()
        if HAS_PYGAME:
            try: pygame.mixer.music.stop()
            except Exception: pass
        if self._active_engine:
            try: self._active_engine.stop()
            except Exception: pass
            self._active_engine = None


# ══════════════════════════════════════════════════════════════════════════════
#  STT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class STTEngine:
    def __init__(self, cfg: Settings):
        if not HAS_SR:
            raise RuntimeError(
                "SpeechRecognition not installed.\n"
                "Run: pip install SpeechRecognition pyaudio")
        self.cfg  = cfg
        self.rec  = sr.Recognizer()
        self._stop = threading.Event()
        self._update_params()

    def _update_params(self):
        self.rec.energy_threshold         = int(self.cfg.stt_energy)
        self.rec.pause_threshold          = float(self.cfg.stt_pause)
        self.rec.dynamic_energy_threshold = True

    @property
    def mic_available(self) -> bool:
        try:
            names = sr.Microphone.list_microphone_names()
            return len(names) > 0
        except Exception:
            return False

    def list_mics(self) -> list:
        try: return sr.Microphone.list_microphone_names()
        except Exception: return []

    def transcribe_mic(self, mic_index=None,
                       on_status=None, on_result=None,
                       on_error=None) -> threading.Thread:
        self._stop.clear()
        self._update_params()

        def _run():
            try:
                kw = {} if (mic_index is None or mic_index < 0) \
                    else {"device_index": mic_index}
                with sr.Microphone(**kw) as src:
                    if on_status: on_status("Calibrating microphone…")
                    self.rec.adjust_for_ambient_noise(src, duration=1.2)
                    if self._stop.is_set(): return
                    if on_status: on_status("🔴  Listening…  Speak now")
                    audio = self.rec.listen(
                        src,
                        timeout=int(self.cfg.stt_timeout),
                        phrase_time_limit=int(self.cfg.stt_phrase),
                    )
                if self._stop.is_set(): return
                if on_status: on_status("⏳  Processing…")
                text = self.rec.recognize_google(audio)
                log.info(f"STT result: {text[:80]}…")
                if on_result: on_result(text)
            except sr.WaitTimeoutError:
                if on_error: on_error(
                    "No speech detected.\n\nCheck your microphone and try again.")
            except sr.UnknownValueError:
                if on_error: on_error(
                    "Speech was unclear.\n\nPlease speak more clearly and try again.")
            except sr.RequestError as e:
                if on_error: on_error(
                    f"Google Speech API error:\n{e}\n\nCheck your internet connection.")
            except OSError as e:
                if on_error: on_error(
                    f"Microphone error:\n{e}\n\n"
                    "• Ensure mic is connected and unmuted\n"
                    "• Check OS permissions\n"
                    "• Try a different device in Settings")
            except Exception as e:
                log.error(f"STT error: {e}", exc_info=True)
                if on_error: on_error(f"Unexpected error:\n{e}")

        t = threading.Thread(target=_run, daemon=True, name="STT-mic")
        t.start()
        return t

    def transcribe_file(self, path: str,
                        on_status=None, on_result=None,
                        on_error=None) -> threading.Thread:
        self._stop.clear()

        def _run():
            try:
                p = Path(path)
                if not p.exists():
                    raise FileNotFoundError(f"File not found:\n{path}")
                if on_status: on_status(f"Loading  {p.name}…")
                with sr.AudioFile(str(p)) as src:
                    audio = self.rec.record(src)
                if self._stop.is_set(): return
                if on_status: on_status("⏳  Transcribing file…")
                text = self.rec.recognize_google(audio)
                if on_result: on_result(text)
            except FileNotFoundError as e:
                if on_error: on_error(str(e))
            except sr.UnknownValueError:
                if on_error: on_error("Audio is unclear or contains no speech.")
            except sr.RequestError as e:
                if on_error: on_error(f"API error:\n{e}")
            except Exception as e:
                log.error(f"File STT error: {e}", exc_info=True)
                if on_error: on_error(f"File transcription error:\n{e}")

        t = threading.Thread(target=_run, daemon=True, name="STT-file")
        t.start()
        return t

    def stop(self): self._stop.set()


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORY LOG
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class HistoryEntry:
    kind:      str
    text:      str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    duration:  float = 0.0
    chars:     int = 0

    def preview(self, n=90):
        return (self.text[:n] + "…") if len(self.text) > n else self.text


class HistoryLog:
    def __init__(self, limit=200):
        self._entries: list[HistoryEntry] = []
        self._limit = limit

    def add(self, kind: str, text: str, **kw):
        e = HistoryEntry(kind=kind, text=text, chars=len(text), **kw)
        self._entries.append(e)
        if len(self._entries) > self._limit:
            self._entries = self._entries[-self._limit:]
        return e

    def clear(self): self._entries.clear()

    def __iter__(self): return iter(reversed(self._entries))
    def __len__(self): return len(self._entries)


# ══════════════════════════════════════════════════════════════════════════════
#  GUI PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

class FlatButton(tk.Frame):
    """Premium flat button with glow hover, ripple animation, icon support."""

    def __init__(self, parent, text="", command=None,
                 accent=C["amber"], icon="",
                 width=0, height=36, font_size=9, **kw):
        super().__init__(parent, bg=kw.pop("bg", C["layer3"]),
                         highlightthickness=1,
                         highlightbackground=C["edge1"],
                         highlightcolor=accent,
                         cursor="hand2", **kw)
        self._accent  = accent
        self._cmd     = command
        self._pressed = False

        self._lbl = tk.Label(
            self, text=f"{icon}  {text}".strip() if icon else text,
            bg=C["layer3"], fg=C["txt_dim"],
            font=(FONT_UI, font_size, "bold"),
            padx=16, pady=0)
        self._lbl.pack(fill="both", expand=True, ipady=height // 2 - 6)

        self.bind("<Enter>",        self._on_enter)
        self.bind("<Leave>",        self._on_leave)
        self.bind("<ButtonPress>",  self._on_press)
        self.bind("<ButtonRelease>",self._on_release)
        self._lbl.bind("<Enter>",        self._on_enter)
        self._lbl.bind("<Leave>",        self._on_leave)
        self._lbl.bind("<ButtonPress>",  self._on_press)
        self._lbl.bind("<ButtonRelease>",self._on_release)

    def _on_enter(self, _=None):
        self.config(bg=self._accent, highlightbackground=self._accent)
        self._lbl.config(bg=self._accent, fg=C["white"])

    def _on_leave(self, _=None):
        if not self._pressed:
            self._reset()

    def _on_press(self, _=None):
        self._pressed = True
        darker = self._accent  # could darken here
        self.config(bg=darker)

    def _on_release(self, _=None):
        self._pressed = False
        if self._cmd:
            try: self._cmd()
            except Exception as e:
                log.error(f"Button command error: {e}", exc_info=True)
        self._on_leave()

    def _reset(self):
        self.config(bg=C["layer3"], highlightbackground=C["edge1"])
        self._lbl.config(bg=C["layer3"], fg=C["txt_dim"])

    def set_text(self, text, icon=""):
        self._lbl.config(text=f"{icon}  {text}".strip() if icon else text)

    def set_accent(self, color):
        self._accent = color
        self.config(highlightcolor=color)

    def configure_state(self, active: bool, accent=None):
        if accent: self._accent = accent
        if active:
            self.config(bg=self._accent, highlightbackground=self._accent)
            self._lbl.config(bg=self._accent, fg=C["white"])
        else:
            self._reset()


class PulseDot(tk.Canvas):
    """Pulsing animated status indicator."""

    def __init__(self, parent, size=10, color=C["ok"], **kw):
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0,
                         bg=kw.pop("bg", C["layer2"]), **kw)
        self._s     = size
        self._color = color
        self._on    = False
        self._phase = 0
        self._draw(False)

    def _draw(self, bright: bool):
        self.delete("all")
        c = self._s // 2
        r = c - 1
        col = self._color if bright else C["txt_faint"]
        if bright:
            # Inner dot only (alpha ring not portable across Tk versions)
            self.create_oval(2, 2, self._s - 2, self._s - 2,
                             fill=col, outline="")
        else:
            self.create_oval(c - r + 1, c - r + 1, c + r - 1, c + r - 1,
                             fill=col, outline="")

    def start(self, color=None):
        if color: self._color = color
        self._on = True
        self._tick()

    def stop(self, color=None):
        self._on = False
        if color: self._color = color
        self._draw(False)

    def _tick(self):
        if not self._on: return
        self._phase = (self._phase + 1) % 12
        self._draw(self._phase < 6)
        self.after(120, self._tick)


class AnimatedProgressBar(tk.Frame):
    """Shimmer progress bar for active operations.
    Uses a Frame container so width is set via pack/grid, not Canvas width arg
    (large Canvas width values cause TclError: 'invalid command name N').
    """

    def __init__(self, parent, height=2, **kw):
        bg = kw.pop("bg", C["bg"])
        super().__init__(parent, bg=bg, height=height, **kw)
        self._h            = height
        self._on           = False
        self._pos          = -60
        self._active_color = C["amber"]
        self._track_color  = C["edge0"]
        # Canvas is created at pack-time with a safe initial width; resizes via configure
        self._canvas = tk.Canvas(self, height=height,
                                 highlightthickness=0, bd=0, bg=bg)
        self._canvas.pack(fill="x", expand=True)
        self._canvas.bind("<Configure>", self._on_resize)
        self._cw = 400  # fallback until first Configure event

    def _on_resize(self, event):
        self._cw = max(event.width, 1)
        if not self._on:
            self._draw_idle()

    def _draw_idle(self):
        self._canvas.delete("all")
        self._canvas.create_rectangle(0, 0, self._cw, self._h,
                                      fill=self._track_color, outline="")

    def start(self, color=None):
        if color: self._active_color = color
        self._on  = True
        self._pos = -60
        self._animate()

    def stop(self):
        self._on = False
        self._draw_idle()

    def _animate(self):
        if not self._on: return
        w = self._cw
        self._canvas.delete("all")
        self._canvas.create_rectangle(0, 0, w, self._h,
                                      fill=self._track_color, outline="")
        band = int(w * 0.18) + 30
        x0 = self._pos
        x1 = x0 + band
        x0c = max(0, x0); x1c = min(w, x1)
        if x1c > x0c:
            self._canvas.create_rectangle(x0c, 0, x1c, self._h,
                                          fill=self._active_color, outline="")
        self._pos += 4
        if self._pos > w + band:
            self._pos = -band
        self.after(16, self._animate)


class TooltipMixin:
    """Add tooltip to any widget."""

    def add_tooltip(self, widget, text):
        tip_win = None

        def show(_e):
            nonlocal tip_win
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 4
            tip_win = tk.Toplevel(widget)
            tip_win.wm_overrideredirect(True)
            tip_win.wm_geometry(f"+{x}+{y}")
            tip_win.configure(bg=C["edge2"])
            tk.Label(tip_win, text=text,
                     bg=C["layer4"], fg=C["txt"],
                     font=(FONT_UI, 8), padx=8, pady=4,
                     relief="flat", bd=1).pack()

        def hide(_e):
            nonlocal tip_win
            if tip_win:
                try: tip_win.destroy()
                except Exception: pass
                tip_win = None

        widget.bind("<Enter>", show, add=True)
        widget.bind("<Leave>", hide, add=True)


class SectionLabel(tk.Frame):
    """Styled section divider with label."""

    def __init__(self, parent, text, **kw):
        super().__init__(parent, bg=kw.pop("bg", C["layer2"]), **kw)
        tk.Label(self, text=text.upper(),
                 bg=C["layer2"], fg=C["txt_muted"],
                 font=(FONT_UI, 7, "bold"), padx=0).pack(side="left")
        tk.Frame(self, bg=C["edge0"], height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0), pady=6)


class StatusBar(tk.Frame):
    """Bottom status bar with animated state."""

    def __init__(self, parent):
        super().__init__(parent, bg=C["layer1"], height=30)
        self.pack_propagate(False)

        # Left: dot + message
        left = tk.Frame(self, bg=C["layer1"])
        left.pack(side="left", fill="y")
        self._dot = PulseDot(left, size=8, bg=C["layer1"])
        self._dot.pack(side="left", padx=(14, 6), pady=11)
        self._msg = tk.Label(left, text="Initializing…",
                             bg=C["layer1"], fg=C["txt_dim"],
                             font=(FONT_UI, 9), anchor="w")
        self._msg.pack(side="left", fill="x")

        # Right: version + clock
        right = tk.Frame(self, bg=C["layer1"])
        right.pack(side="right", fill="y")
        tk.Label(right, text=f"v{APP_VERSION}  ·  ",
                 bg=C["layer1"], fg=C["txt_faint"],
                 font=(FONT_UI, 8)).pack(side="left", pady=8)
        self._clk = tk.Label(right, text="",
                             bg=C["layer1"], fg=C["txt_muted"],
                             font=(FONT_MONO, 8), padx=14)
        self._clk.pack(side="left")
        self._tick()

    def set(self, text: str, color=C["txt_dim"], dot_color=None):
        self._msg.config(text=text, fg=color)
        self._dot._color = dot_color or color
        self._dot._draw(True)

    def pulse(self, color=C["amber"]):
        self._dot.start(color)

    def still(self, color=C["ok"]):
        self._dot.stop(color)

    def _tick(self):
        self._clk.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._tick)


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM SCROLLED TEXT
# ══════════════════════════════════════════════════════════════════════════════

class Editor(tk.Frame):
    """Styled text editor with line numbers, char count, and find/replace."""

    def __init__(self, parent, font_size=11, **kw):
        bg = kw.pop("bg", C["layer2"])
        super().__init__(parent, bg=bg,
                         highlightthickness=1,
                         highlightbackground=C["edge1"],
                         highlightcolor=C["amber"], **kw)
        self._fs   = font_size
        self._ph   = ""
        self._ph_on = False
        self._build()

    def _build(self):
        # Line numbers
        self._ln = tk.Text(
            self, width=4, bg=C["layer1"], fg=C["txt_faint"],
            font=(FONT_MONO, self._fs), relief="flat", bd=0,
            padx=8, pady=14, state="disabled",
            selectbackground=C["layer1"], cursor="arrow")
        self._ln.pack(side="left", fill="y")
        tk.Frame(self, bg=C["edge0"], width=1).pack(side="left", fill="y")

        # Main text
        self.text = tk.Text(
            self, bg=C["layer2"], fg=C["txt"],
            insertbackground=C["amber"],
            relief="flat", bd=0, padx=16, pady=14,
            font=(FONT_UI, self._fs),
            wrap="word", undo=True, maxundo=100,
            selectbackground=C["blue_dim"],
            selectforeground=C["white"],
            spacing1=2, spacing3=4,
            tabs=("1c",),
        )
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self._on_scroll)
        vsb.pack(side="right", fill="y")
        self._vsb = vsb
        self.text.pack(side="left", fill="both", expand=True)

        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._update_lns)

    def _on_scroll(self, *args):
        self._vsb.set(*args)
        self._sync_lns()

    def _sync_lns(self):
        self._ln.yview_moveto(self.text.yview()[0])

    def _update_lns(self, _=None):
        lines = int(self.text.index("end-1c").split(".")[0])
        self._ln.config(state="normal")
        self._ln.delete("1.0", "end")
        self._ln.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
        self._ln.config(state="disabled")
        self._sync_lns()

    def _on_modified(self, _=None):
        self.text.edit_modified(False)
        self._update_lns()
        self.event_generate("<<TextChanged>>")

    # ── Public interface (mirrors tk.Text) ────────────────────────────────────

    def get(self, *a, **kw):    return self.text.get(*a, **kw)
    def insert(self, *a, **kw): return self.text.insert(*a, **kw)
    def delete(self, *a, **kw): return self.text.delete(*a, **kw)
    def see(self, *a, **kw):    return self.text.see(*a, **kw)
    def bind(self, *a, **kw):   return self.text.bind(*a, **kw)
    def config(self, **kw):
        if "fg" in kw: self.text.config(fg=kw.pop("fg"))
        if kw: super().config(**kw)

    def set_placeholder(self, text: str):
        self._ph = text
        self._ph_on = False
        self._restore_ph(None)

    def clear_ph(self, _=None):
        if self._ph_on:
            self.text.delete("1.0", "end")
            self.text.config(fg=C["txt"])
            self._ph_on = False

    def _restore_ph(self, _=None):
        if not self.text.get("1.0", "end-1c").strip() and self._ph:
            self.text.insert("1.0", self._ph)
            self.text.config(fg=C["txt_muted"])
            self._ph_on = True

    def get_real_text(self) -> str:
        if self._ph_on: return ""
        return self.text.get("1.0", "end-1c")

    def word_count(self) -> Tuple[int, int]:
        t = self.get_real_text()
        words = len(t.split()) if t.strip() else 0
        return words, len(t)

    def set_font_size(self, size: int):
        self._fs = size
        self.text.config(font=(FONT_UI, size))
        self._ln.config(font=(FONT_MONO, size))


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG  — tabbed, polished
# ══════════════════════════════════════════════════════════════════════════════

class SettingsDialog(tk.Toplevel, TooltipMixin):
    def __init__(self, root, cfg: Settings,
                 tts: Optional[TTSEngine], stt: Optional[STTEngine]):
        super().__init__(root)
        self.cfg = cfg; self.tts = tts; self.stt = stt
        self.title("Settings")
        self.geometry("560x620")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.transient(root)
        self.grab_set()
        self._apply_style()
        self._build()
        self.focus_force()

    def _apply_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        for w in ("TNotebook", "TNotebook.Tab", "TScrollbar",
                  "TCombobox", "Vertical.TScrollbar"):
            try: s.configure(w)
            except Exception: pass
        s.configure("D.TNotebook", background=C["bg"], borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("D.TNotebook.Tab", background=C["layer2"],
                    foreground=C["txt_dim"],
                    padding=[16, 8], font=(FONT_UI, 9, "bold"), borderwidth=0)
        s.map("D.TNotebook.Tab",
              background=[("selected", C["layer3"])],
              foreground=[("selected", C["amber"])])
        s.configure("D.TCombobox", fieldbackground=C["layer3"],
                    background=C["layer3"], foreground=C["txt"],
                    arrowcolor=C["amber"])
        s.map("D.TCombobox", fieldbackground=[("readonly", C["layer3"])])

    def _frame(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=C["layer2"],
                     highlightthickness=1, highlightbackground=C["edge1"])
        f.pack(fill="x", padx=16, pady=6)
        return f

    def _row(self, parent, label: str) -> tk.Frame:
        r = tk.Frame(parent, bg=C["layer2"])
        r.pack(fill="x", padx=14, pady=5)
        tk.Label(r, text=label, width=22, anchor="w",
                 bg=C["layer2"], fg=C["txt_dim"],
                 font=(FONT_UI, 9)).pack(side="left")
        return r

    def _scale(self, parent, var, lo, hi, res=1):
        return tk.Scale(parent, variable=var, from_=lo, to=hi,
                        resolution=res, orient="horizontal",
                        bg=C["layer2"], fg=C["txt"],
                        troughcolor=C["edge1"],
                        activebackground=C["amber"],
                        highlightthickness=0, bd=0,
                        sliderrelief="flat", length=200)

    def _combo(self, parent, var, values, width=28):
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=width, style="D.TCombobox")
        return cb

    def _section(self, parent, text):
        tk.Label(parent, text=f"  {text.upper()}",
                 bg=C["layer2"], fg=C["amber"],
                 font=(FONT_UI, 8, "bold")).pack(
                     anchor="w", padx=14, pady=(12, 0))
        tk.Frame(parent, bg=C["edge0"], height=1).pack(
            fill="x", padx=14, pady=(2, 4))

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["layer1"], height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  Settings",
                 bg=C["layer1"], fg=C["txt"],
                 font=(FONT_UI, 13, "bold")).pack(side="left", padx=20, pady=14)
        tk.Frame(self, bg=C["edge0"], height=1).pack(fill="x")

        nb = ttk.Notebook(self, style="D.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        for tab_name, builder in [
            ("  TTS  ",     self._build_tts),
            ("  STT  ",     self._build_stt),
            ("  General  ", self._build_general),
        ]:
            frame = tk.Frame(nb, bg=C["layer2"])
            nb.add(frame, text=tab_name)
            builder(frame)

        # Footer
        tk.Frame(self, bg=C["edge0"], height=1).pack(fill="x")
        bf = tk.Frame(self, bg=C["bg"])
        bf.pack(fill="x", padx=16, pady=12)

        FlatButton(bf, "✕  Cancel", self.destroy,
                   accent=C["err"]).pack(side="right", padx=(4, 0))
        FlatButton(bf, "✓  Save", self._save,
                   accent=C["teal"]).pack(side="right", padx=4)

    def _build_tts(self, tab):
        scroll = tk.Frame(tab, bg=C["layer2"])
        scroll.pack(fill="both", expand=True)

        self._section(scroll, "Engine")
        r1 = self._row(scroll, "Engine:")
        self._v_eng = tk.StringVar(value=self.cfg.tts_engine)
        opts = ["pyttsx3 (offline)"]
        if HAS_GTTS: opts.append("gtts (online)")
        self._combo(r1, self._v_eng, opts).pack(side="left")

        self._section(scroll, "Voice (pyttsx3)")
        r2 = self._row(scroll, "Voice:")
        voices = ([f"{i}: {v.name}" for i, v in enumerate(self.tts.voices)]
                  if self.tts else [])
        idx = min(int(self.cfg.tts_voice), len(voices) - 1) if voices else 0
        self._v_voice = tk.StringVar(value=voices[idx] if voices else "(none)")
        self._combo(r2, self._v_voice, voices or ["(none)"]).pack(side="left")

        self._section(scroll, "Parameters")
        r3 = self._row(scroll, "Rate (wpm):")
        self._v_rate = tk.IntVar(value=int(self.cfg.tts_rate))
        self._scale(r3, self._v_rate, 50, 400).pack(side="left")
        tk.Label(r3, textvariable=self._v_rate,
                 bg=C["layer2"], fg=C["amber"],
                 font=(FONT_MONO, 9), width=4).pack(side="left", padx=4)

        r4 = self._row(scroll, "Volume:")
        self._v_vol = tk.DoubleVar(value=float(self.cfg.tts_volume))
        self._scale(r4, self._v_vol, 0.0, 1.0, res=0.05).pack(side="left")

        self._section(scroll, "gTTS Language")
        r5 = self._row(scroll, "Language:")
        self._v_lang = tk.StringVar(value=self.cfg.tts_lang)
        langs = ["en", "es", "fr", "de", "it", "pt", "nl", "ru",
                 "zh-cn", "ja", "ko", "hi", "ar", "tr", "pl", "sv", "da"]
        self._combo(r5, self._v_lang, langs, width=14).pack(side="left")

    def _build_stt(self, tab):
        self._section(tab, "Microphone")
        r1 = self._row(tab, "Device:")
        mics = ([f"{i}: {m}" for i, m in
                 enumerate(self.stt.list_mics() if self.stt else [])]
                or ["(none detected)"])
        self._v_mic = tk.StringVar(value=mics[0])
        self._combo(r1, self._v_mic, mics).pack(side="left")

        self._section(tab, "Recognition Parameters")
        r2 = self._row(tab, "Energy threshold:")
        self._v_energy = tk.IntVar(value=int(self.cfg.stt_energy))
        self._scale(r2, self._v_energy, 50, 4000).pack(side="left")
        tk.Label(r2, textvariable=self._v_energy,
                 bg=C["layer2"], fg=C["amber"],
                 font=(FONT_MONO, 9), width=5).pack(side="left", padx=4)

        r3 = self._row(tab, "Pause (s):")
        self._v_pause = tk.DoubleVar(value=float(self.cfg.stt_pause))
        self._scale(r3, self._v_pause, 0.3, 3.0, res=0.1).pack(side="left")

        r4 = self._row(tab, "Listen timeout (s):")
        self._v_timeout = tk.IntVar(value=int(self.cfg.stt_timeout))
        self._scale(r4, self._v_timeout, 3, 120).pack(side="left")
        tk.Label(r4, textvariable=self._v_timeout,
                 bg=C["layer2"], fg=C["amber"],
                 font=(FONT_MONO, 9), width=4).pack(side="left", padx=4)

        r5 = self._row(tab, "Phrase limit (s):")
        self._v_phrase = tk.IntVar(value=int(self.cfg.stt_phrase))
        self._scale(r5, self._v_phrase, 5, 180).pack(side="left")

    def _build_general(self, tab):
        self._section(tab, "Auto-Save")
        self._v_auto = tk.BooleanVar(value=bool(self.cfg.auto_save))
        row = tk.Frame(tab, bg=C["layer2"])
        row.pack(fill="x", padx=14, pady=6)
        tk.Checkbutton(row,
                       text="Auto-save each transcription to VoiceStudio folder",
                       variable=self._v_auto,
                       bg=C["layer2"], fg=C["txt"],
                       activebackground=C["layer2"],
                       selectcolor=C["amber"],
                       font=(FONT_UI, 9), cursor="hand2").pack(anchor="w")

        self._section(tab, "Display")
        r2 = self._row(tab, "Editor font size:")
        self._v_font = tk.IntVar(value=int(self.cfg.font_size))
        self._scale(r2, self._v_font, 8, 22).pack(side="left")
        tk.Label(r2, textvariable=self._v_font,
                 bg=C["layer2"], fg=C["amber"],
                 font=(FONT_MONO, 9), width=3).pack(side="left", padx=4)

        self._section(tab, "History")
        r3 = self._row(tab, "History limit:")
        self._v_hlim = tk.IntVar(value=int(self.cfg.history_limit))
        self._scale(r3, self._v_hlim, 50, 500, res=50).pack(side="left")

        self._section(tab, "Startup")
        r4 = self._row(tab, "Open on tab:")
        self._v_tab = tk.StringVar(
            value="Speech→Text" if self.cfg.startup_tab == 0 else "Text→Speech")
        self._combo(r4, self._v_tab,
                    ["Speech→Text", "Text→Speech"], width=16).pack(side="left")

    def _save(self):
        raw = self._v_eng.get()
        self.cfg.tts_engine = "gtts" if "gtts" in raw else "pyttsx3"
        try:
            self.cfg.tts_voice = int(self._v_voice.get().split(":")[0])
        except Exception: pass
        self.cfg.tts_rate     = int(self._v_rate.get())
        self.cfg.tts_volume   = round(float(self._v_vol.get()), 2)
        self.cfg.tts_lang     = self._v_lang.get()
        self.cfg.stt_energy   = int(self._v_energy.get())
        self.cfg.stt_pause    = round(float(self._v_pause.get()), 2)
        self.cfg.stt_timeout  = int(self._v_timeout.get())
        self.cfg.stt_phrase   = int(self._v_phrase.get())
        self.cfg.auto_save    = bool(self._v_auto.get())
        self.cfg.font_size    = int(self._v_font.get())
        self.cfg.history_limit= int(self._v_hlim.get())
        self.cfg.startup_tab  = 0 if "Speech" in self._v_tab.get() else 1
        self.cfg.save()
        log.info("Settings saved.")
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORY WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class HistoryWindow(tk.Toplevel):
    def __init__(self, root, hist: HistoryLog, on_copy):
        super().__init__(root)
        self.hist    = hist
        self._on_copy = on_copy
        self.title("Session History")
        self.geometry("660x500")
        self.configure(bg=C["bg"])
        self.transient(root)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["layer1"], height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⏱  Session History",
                 bg=C["layer1"], fg=C["txt"],
                 font=(FONT_UI, 13, "bold")).pack(side="left", padx=20, pady=14)
        self._cnt = tk.Label(hdr, text=f"{len(self.hist)} entries",
                             bg=C["layer1"], fg=C["txt_dim"],
                             font=(FONT_UI, 9))
        self._cnt.pack(side="right", padx=20)
        tk.Frame(self, bg=C["edge0"], height=1).pack(fill="x")

        # Filter bar
        fbar = tk.Frame(self, bg=C["layer2"])
        fbar.pack(fill="x", padx=16, pady=8)
        tk.Label(fbar, text="Filter:", bg=C["layer2"],
                 fg=C["txt_dim"], font=(FONT_UI, 9)).pack(side="left")
        self._fv = tk.StringVar()
        self._fv.trace("w", self._refresh)
        fe = tk.Entry(fbar, textvariable=self._fv,
                      bg=C["layer3"], fg=C["txt"],
                      insertbackground=C["amber"],
                      relief="flat", font=(FONT_UI, 9),
                      highlightthickness=1, highlightbackground=C["edge1"])
        fe.pack(side="left", fill="x", expand=True, padx=8, ipady=4)

        # Content
        outer = tk.Frame(self, bg=C["edge1"],
                         highlightthickness=1, highlightbackground=C["edge1"])
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._box = tk.Text(
            outer, bg=C["layer2"], fg=C["txt"],
            relief="flat", bd=0, padx=14, pady=10,
            font=(FONT_MONO, 9), wrap="word", state="disabled",
            selectbackground=C["blue_dim"], cursor="arrow")
        sb = ttk.Scrollbar(outer, orient="vertical", command=self._box.yview)
        self._box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._box.pack(fill="both", expand=True)

        # Tags for coloring
        for tag, col in [("stt", C["teal"]), ("tts", C["amber"]),
                         ("save", C["ok"]), ("err", C["err"]),
                         ("ts", C["txt_muted"]), ("preview", C["txt_dim"])]:
            self._box.tag_config(tag, foreground=col)

        # Footer
        tk.Frame(self, bg=C["edge0"], height=1).pack(fill="x")
        bf = tk.Frame(self, bg=C["bg"])
        bf.pack(fill="x", padx=16, pady=10)
        FlatButton(bf, "✕  Close", self.destroy,
                   accent=C["txt_muted"]).pack(side="right", padx=4)
        FlatButton(bf, "🗑  Clear", self._clear,
                   accent=C["err"]).pack(side="right", padx=4)
        FlatButton(bf, "💾  Export", self._export,
                   accent=C["teal"]).pack(side="right", padx=4)

        self._refresh()

    def _refresh(self, *_):
        filt = self._fv.get().lower()
        self._box.config(state="normal")
        self._box.delete("1.0", "end")
        shown = 0
        for e in self.hist:
            if filt and filt not in e.text.lower() and filt not in e.kind.lower():
                continue
            ts = datetime.datetime.fromisoformat(e.timestamp).strftime("%H:%M:%S")
            self._box.insert("end", f"[{ts}] ", "ts")
            tag = ("stt" if "STT" in e.kind.upper()
                   else "tts" if "TTS" in e.kind.upper()
                   else "save")
            self._box.insert("end", f"[{e.kind}]", tag)
            if e.chars:
                self._box.insert("end", f"  {e.chars:,} chars\n", "ts")
            else:
                self._box.insert("end", "\n", "ts")
            self._box.insert("end", f"  {e.preview()}\n\n", "preview")
            shown += 1
        if not shown:
            self._box.insert("1.0", "No matching entries.")
        self._box.config(state="disabled")
        self._cnt.config(text=f"{shown} / {len(self.hist)} entries")

    def _clear(self):
        self.hist.clear()
        self._refresh()

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="Export History",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile=f"history_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt",
            parent=self)
        if not path: return
        try:
            lines = []
            for e in self.hist:
                lines.append(
                    f"[{e.timestamp}] [{e.kind}] chars={e.chars}\n"
                    f"{e.text}\n{'─'*60}\n")
            Path(path).write_text("\n".join(lines), encoding="utf-8")
        except Exception as ex:
            messagebox.showerror("Export Error", str(ex), parent=self)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class VoiceStudio(tk.Tk, TooltipMixin):

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE}  {APP_VERSION}")
        self.geometry("1040x740")
        self.minsize(860, 620)
        self.configure(bg=C["bg"])
        try: self.wm_attributes("-alpha", 1.0)
        except Exception: pass

        self.cfg  = Settings()
        self.hist = HistoryLog(self.cfg.history_limit)
        self._q   = queue.Queue()

        self._rec_active = False
        self._spk_active = False
        self._tts_thread: Optional[threading.Thread] = None
        self._stt_thread: Optional[threading.Thread] = None
        self._spk_start:  float = 0.0
        self._rec_start:  float = 0.0

        self._tts: Optional[TTSEngine] = None
        self._stt: Optional[STTEngine] = None
        self._tts_err = self._stt_err = ""

        self._init_engines()
        self._apply_ttk_style()
        self._build()
        self._bind_shortcuts()
        self._poll()

        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.after(500, self._ready)
        log.info("VoiceStudio initialized.")

    # ── Engine init ───────────────────────────────────────────────────────────

    def _init_engines(self):
        try:
            self._tts = TTSEngine(self.cfg)
        except Exception as e:
            self._tts_err = str(e)
            log.error(f"TTS init failed: {e}", exc_info=True)
        try:
            self._stt = STTEngine(self.cfg)
        except Exception as e:
            self._stt_err = str(e)
            log.warning(f"STT init failed: {e}")

    # ── TTK styles ────────────────────────────────────────────────────────────

    def _apply_ttk_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",
                    background=C["bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=C["layer2"], foreground=C["txt_dim"],
                    padding=[22, 11], font=(FONT_UI, 10, "bold"), borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", C["layer3"])],
              foreground=[("selected", C["amber"])])
        s.configure("TScrollbar",
                    background=C["layer3"], troughcolor=C["layer1"],
                    arrowcolor=C["txt_muted"], borderwidth=0, relief="flat", width=6)
        s.configure("TCombobox",
                    fieldbackground=C["layer3"], background=C["layer3"],
                    foreground=C["txt"], arrowcolor=C["amber"],
                    selectbackground=C["layer3"], selectforeground=C["txt"])
        s.map("TCombobox", fieldbackground=[("readonly", C["layer3"])])
        s.configure("Vertical.TScrollbar", width=6)

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._build_header()
        self._build_progress()
        self._build_tabs()
        self.statusbar = StatusBar(self)
        self.statusbar.pack(fill="x", side="bottom")
        # Top edge line
        tk.Frame(self, bg=C["edge0"], height=1).pack(
            fill="x", side="bottom", before=self.statusbar)

    def _build_header(self):
        hdr = tk.Frame(self, bg=C["layer1"], height=62)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        # Accent line at top
        tk.Frame(hdr, bg=C["amber"], height=2).place(
            relx=0, rely=0, relwidth=1.0)

        # Logo group
        logo = tk.Frame(hdr, bg=C["layer1"])
        logo.pack(side="left", fill="y", padx=20)
        # Amber dot logo
        dot_c = tk.Canvas(logo, width=24, height=24,
                          highlightthickness=0, bg=C["layer1"])
        dot_c.pack(side="left", pady=19)
        dot_c.create_oval(3, 3, 21, 21, fill=C["amber_dim"], outline="")
        dot_c.create_oval(7, 7, 17, 17, fill=C["amber"], outline="")
        dot_c.create_oval(9, 9, 15, 15, fill=C["amber_glow"], outline="")

        tk.Label(logo, text=f" {APP_TITLE}",
                 bg=C["layer1"], fg=C["txt"],
                 font=(FONT_UI, 14, "bold")).pack(side="left", pady=18)
        tk.Label(logo, text=f" v{APP_VERSION}",
                 bg=C["layer1"], fg=C["txt_faint"],
                 font=(FONT_UI, 9)).pack(side="left", pady=18)

        # Engine pills
        pills = tk.Frame(hdr, bg=C["layer1"])
        pills.pack(side="left", fill="y", padx=16)
        self._tts_pill = self._pill(pills, "TTS", C["txt_muted"])
        self._tts_pill.pack(side="left", padx=4, pady=20)
        self._stt_pill = self._pill(pills, "STT", C["txt_muted"])
        self._stt_pill.pack(side="left", padx=4, pady=20)

        # Right controls
        right = tk.Frame(hdr, bg=C["layer1"])
        right.pack(side="right", fill="y", padx=12)

        for label, cmd, acc in [
            ("⚙  Settings", self._open_settings, C["txt_muted"]),
            ("⏱  History",  self._open_history,  C["violet"]),
            ("📋  Log",     self._open_log,       C["blue"]),
        ]:
            FlatButton(right, label, cmd, accent=acc,
                       height=32, font_size=9).pack(
                side="right", padx=4, pady=15)

        tk.Frame(hdr, bg=C["edge0"], height=1).pack(fill="x", side="bottom")

    def _pill(self, parent, label: str, color: str) -> tk.Label:
        return tk.Label(parent, text=f"● {label}: …",
                        bg=C["layer2"], fg=color,
                        font=(FONT_UI, 8), padx=10, pady=3)

    def _build_progress(self):
        self._progress = AnimatedProgressBar(self, height=2, bg=C["layer1"])
        self._progress.pack(fill="x")

    def _build_tabs(self):
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True)
        self._stt_tab = tk.Frame(self._nb, bg=C["bg"])
        self._tts_tab = tk.Frame(self._nb, bg=C["bg"])
        self._nb.add(self._stt_tab, text="   🎙  Speech → Text   ")
        self._nb.add(self._tts_tab, text="   🔊  Text → Speech   ")
        self._build_stt_tab(self._stt_tab)
        self._build_tts_tab(self._tts_tab)
        self._nb.select(min(self.cfg.startup_tab, 1))

    # ══════════════════════════════════════════════════════════════════════════
    #  STT TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_stt_tab(self, tab):
        # ── Source bar ────────────────────────────────────────────────────────
        src_bar = tk.Frame(tab, bg=C["layer1"], height=48)
        src_bar.pack(fill="x"); src_bar.pack_propagate(False)
        tk.Frame(src_bar, bg=C["edge0"], height=1).pack(fill="x", side="bottom")

        tk.Label(src_bar, text="Input Source:",
                 bg=C["layer1"], fg=C["txt_dim"],
                 font=(FONT_UI, 9, "bold")).pack(side="left", padx=(16, 8), pady=14)

        self._stt_src = tk.StringVar(value="mic")
        for val, icon, lbl in [("mic",  "🎤", "Microphone"),
                                ("file", "📂", "Audio File")]:
            rb = tk.Radiobutton(src_bar, text=f"{icon}  {lbl}",
                                variable=self._stt_src, value=val,
                                command=self._stt_src_toggle,
                                bg=C["layer1"], fg=C["txt"],
                                activebackground=C["layer1"],
                                selectcolor=C["amber"],
                                font=(FONT_UI, 9), cursor="hand2")
            rb.pack(side="left", padx=10, pady=14)

        # File path row
        self._stt_file_bar = tk.Frame(src_bar, bg=C["layer1"])
        self._stt_fv = tk.StringVar()
        fe = tk.Entry(self._stt_file_bar, textvariable=self._stt_fv,
                      width=32, bg=C["layer3"], fg=C["txt_dim"],
                      insertbackground=C["txt"], relief="flat",
                      font=(FONT_UI, 9),
                      highlightthickness=1, highlightbackground=C["edge1"])
        fe.pack(side="left", padx=(10, 4), ipady=3)
        FlatButton(self._stt_file_bar, "Browse…", self._stt_browse,
                   accent=C["txt_muted"], height=28,
                   font_size=8).pack(side="left")

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(tab, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Sidebar ───────────────────────────────────────────────────────────
        side = tk.Frame(body, bg=C["layer2"], width=210,
                        highlightthickness=1, highlightbackground=C["edge0"])
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)

        inner = tk.Frame(side, bg=C["layer2"])
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        # Status row
        st_row = tk.Frame(inner, bg=C["layer2"])
        st_row.pack(fill="x", pady=(0, 10))
        self._stt_dot = PulseDot(st_row, size=10, bg=C["layer2"])
        self._stt_dot.pack(side="left", padx=(0, 6))
        self._stt_st = tk.Label(st_row, text="Ready",
                                bg=C["layer2"], fg=C["txt_muted"],
                                font=(FONT_UI, 9))
        self._stt_st.pack(side="left")

        # Timer display
        self._stt_timer = tk.Label(inner, text="00:00",
                                   bg=C["layer2"], fg=C["txt_faint"],
                                   font=(FONT_MONO, 20, "bold"))
        self._stt_timer.pack(pady=(4, 8))

        self._btn_rec = FlatButton(inner, "⏺  Start Recording",
                                   self._toggle_record, accent=C["rose"])
        self._btn_rec.pack(fill="x", pady=(0, 4))

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        SectionLabel(inner, "Save Format", bg=C["layer2"]).pack(fill="x")

        self._stt_fmt = tk.StringVar(value="txt")
        for ext, label in [("txt", "Plain Text  (.txt)"),
                            ("md",  "Markdown    (.md) "),
                            ("log", "Log File    (.log)")]:
            tk.Radiobutton(inner, text=label, variable=self._stt_fmt, value=ext,
                           bg=C["layer2"], fg=C["txt"],
                           activebackground=C["layer2"],
                           selectcolor=C["amber"],
                           font=(FONT_MONO, 9), cursor="hand2").pack(
                               anchor="w", pady=2)

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        SectionLabel(inner, "Actions", bg=C["layer2"]).pack(fill="x")

        for label, cmd, acc in [
            ("💾  Save Transcript", self._stt_save,  C["teal"]),
            ("📋  Copy All",        self._stt_copy,  C["blue"]),
            ("🗑  Clear",           self._stt_clear, C["txt_muted"]),
        ]:
            FlatButton(inner, label, cmd, accent=acc, height=30,
                       font_size=8).pack(fill="x", pady=2)

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        self._stt_append = tk.BooleanVar(value=True)
        tk.Checkbutton(inner, text="Append results",
                       variable=self._stt_append,
                       bg=C["layer2"], fg=C["txt_dim"],
                       activebackground=C["layer2"],
                       selectcolor=C["amber"],
                       font=(FONT_UI, 9), cursor="hand2").pack(anchor="w")

        # ── Main area ─────────────────────────────────────────────────────────
        main = tk.Frame(body, bg=C["bg"])
        main.pack(fill="both", expand=True)

        top = tk.Frame(main, bg=C["bg"])
        top.pack(fill="x", pady=(0, 6))
        tk.Label(top, text="Transcription Output",
                 bg=C["bg"], fg=C["txt"],
                 font=(FONT_UI, 11, "bold")).pack(side="left")
        self._stt_info = tk.Label(top, text="0 words · 0 chars",
                                  bg=C["bg"], fg=C["txt_muted"],
                                  font=(FONT_UI, 9))
        self._stt_info.pack(side="right")

        self._stt_ed = Editor(main, font_size=int(self.cfg.font_size))
        self._stt_ed.pack(fill="both", expand=True)
        self._stt_ed.bind("<<TextChanged>>", self._stt_text_changed)

    # ══════════════════════════════════════════════════════════════════════════
    #  TTS TAB
    # ══════════════════════════════════════════════════════════════════════════

    def _build_tts_tab(self, tab):
        body = tk.Frame(tab, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Sidebar ───────────────────────────────────────────────────────────
        side = tk.Frame(body, bg=C["layer2"], width=210,
                        highlightthickness=1, highlightbackground=C["edge0"])
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)

        inner = tk.Frame(side, bg=C["layer2"])
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        # Speak status row
        spk_row = tk.Frame(inner, bg=C["layer2"])
        spk_row.pack(fill="x", pady=(0, 4))
        self._spk_dot = PulseDot(spk_row, size=10, bg=C["layer2"],
                                 color=C["amber"])
        self._spk_dot.pack(side="left", padx=(0, 6))
        self._spk_st = tk.Label(spk_row, text="Ready",
                                bg=C["layer2"], fg=C["txt_muted"],
                                font=(FONT_UI, 9))
        self._spk_st.pack(side="left")

        # Duration
        self._spk_timer = tk.Label(inner, text="00:00",
                                   bg=C["layer2"], fg=C["txt_faint"],
                                   font=(FONT_MONO, 20, "bold"))
        self._spk_timer.pack(pady=(4, 8))

        self._btn_spk = FlatButton(inner, "▶  Speak Text",
                                   self._toggle_speak, accent=C["amber"])
        self._btn_spk.pack(fill="x", pady=(0, 4))

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        SectionLabel(inner, "Text Source", bg=C["layer2"]).pack(fill="x")

        self._tts_src = tk.StringVar(value="editor")
        for val, lbl in [("editor", "Type in editor"),
                         ("file",   "Load from file"),
                         ("clip",   "From clipboard")]:
            tk.Radiobutton(inner, text=lbl, variable=self._tts_src, value=val,
                           command=self._tts_src_changed,
                           bg=C["layer2"], fg=C["txt"],
                           activebackground=C["layer2"],
                           selectcolor=C["amber"],
                           font=(FONT_UI, 9), cursor="hand2").pack(
                               anchor="w", pady=2)

        self._tts_file_frame = tk.Frame(inner, bg=C["layer2"])
        self._tts_fv = tk.StringVar()
        tk.Entry(self._tts_file_frame, textvariable=self._tts_fv,
                 width=20, bg=C["layer3"], fg=C["txt_dim"],
                 insertbackground=C["txt"], relief="flat",
                 font=(FONT_UI, 8),
                 highlightthickness=1,
                 highlightbackground=C["edge1"]).pack(
                     fill="x", pady=(3, 0), ipady=3)
        FlatButton(self._tts_file_frame, "Browse…", self._tts_browse,
                   accent=C["txt_muted"], height=26,
                   font_size=8).pack(fill="x", pady=2)

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        SectionLabel(inner, "Audio Format", bg=C["layer2"]).pack(fill="x")

        self._tts_fmt = tk.StringVar(value="wav")
        for ext, lbl in [("wav", "WAV (offline)"),
                         ("mp3", "MP3 (online)")]:
            tk.Radiobutton(inner, text=lbl, variable=self._tts_fmt, value=ext,
                           bg=C["layer2"], fg=C["txt"],
                           activebackground=C["layer2"],
                           selectcolor=C["amber"],
                           font=(FONT_MONO, 9), cursor="hand2").pack(
                               anchor="w", pady=2)

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        SectionLabel(inner, "Actions", bg=C["layer2"]).pack(fill="x")

        for label, cmd, acc in [
            ("💾  Save Audio",     self._tts_save_audio, C["teal"]),
            ("📂  Load Text File", self._tts_load_file,  C["rose"]),
            ("🗑  Clear",         self._tts_clear,      C["txt_muted"]),
        ]:
            FlatButton(inner, label, cmd, accent=acc, height=30,
                       font_size=8).pack(fill="x", pady=2)

        tk.Frame(inner, bg=C["edge0"], height=1).pack(fill="x", pady=8)
        self._tts_wc = tk.Label(inner, text="0 words  ·  0 chars",
                                bg=C["layer2"], fg=C["txt_muted"],
                                font=(FONT_UI, 8), anchor="w", wraplength=170)
        self._tts_wc.pack(anchor="w")

        # ── Main area ─────────────────────────────────────────────────────────
        main = tk.Frame(body, bg=C["bg"])
        main.pack(fill="both", expand=True)

        # Header + quick chips
        hdr = tk.Frame(main, bg=C["bg"])
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="Text Editor",
                 bg=C["bg"], fg=C["txt"],
                 font=(FONT_UI, 11, "bold")).pack(side="left")
        tk.Label(hdr, text="  type, paste, or load a file",
                 bg=C["bg"], fg=C["txt_muted"],
                 font=(FONT_UI, 9)).pack(side="left")

        # Keyboard shortcut hint
        tk.Label(hdr, text="Ctrl+↵ to Speak",
                 bg=C["bg"], fg=C["txt_faint"],
                 font=(FONT_UI, 8)).pack(side="right")

        # Quick-insert bar
        chips_bar = tk.Frame(main, bg=C["layer3"])
        chips_bar.pack(fill="x", pady=(0, 6))
        tk.Label(chips_bar, text="  Quick:",
                 bg=C["layer3"], fg=C["txt_muted"],
                 font=(FONT_UI, 8)).pack(side="left", pady=5)

        for snip in ["Hello, world!", "Testing 1 2 3.",
                     "Good morning!", "Thank you.", "The quick brown fox."]:
            b = tk.Label(chips_bar, text=snip,
                         bg=C["layer4"], fg=C["txt_dim"],
                         font=(FONT_UI, 8), padx=10, pady=4, cursor="hand2",
                         relief="flat",
                         highlightthickness=1, highlightbackground=C["edge0"])
            b.pack(side="left", padx=3, pady=5)
            b.bind("<Button-1>", lambda e, s=snip: self._quick_insert(s))
            b.bind("<Enter>", lambda e, w=b: w.config(bg=C["layer5"], fg=C["txt"]))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=C["layer4"], fg=C["txt_dim"]))

        # Editor
        self._tts_ed = Editor(main, font_size=int(self.cfg.font_size))
        self._tts_ed.pack(fill="both", expand=True)
        self._tts_ed.set_placeholder(
            "Type or paste the text you want to convert to speech…")
        self._tts_ed.text.bind("<FocusIn>",  self._tts_ed.clear_ph)
        self._tts_ed.text.bind("<FocusOut>", self._tts_ed._restore_ph)
        self._tts_ed.bind("<<TextChanged>>", self._tts_text_changed)

    # ══════════════════════════════════════════════════════════════════════════
    #  KEYBOARD SHORTCUTS
    # ══════════════════════════════════════════════════════════════════════════

    def _bind_shortcuts(self):
        self.bind_all("<Control-Return>", lambda _: self._toggle_speak())
        self.bind_all("<Control-r>",      lambda _: self._toggle_record())
        self.bind_all("<Control-s>",      lambda _: self._ctx_save())
        self.bind_all("<Control-h>",      lambda _: self._open_history())
        self.bind_all("<Control-comma>",  lambda _: self._open_settings())
        self.bind_all("<F1>",             self._show_shortcuts)
        self.bind_all("<Escape>",         self._stop_all)

    def _ctx_save(self):
        tab = self._nb.index("current")
        if tab == 0: self._stt_save()
        else:        self._tts_save_audio()

    def _stop_all(self, _=None):
        if self._rec_active: self._stop_record()
        if self._spk_active: self._stop_speak()

    def _show_shortcuts(self, _=None):
        win = tk.Toplevel(self)
        win.title("Keyboard Shortcuts")
        win.geometry("340x280")
        win.configure(bg=C["bg"])
        win.transient(self)
        tk.Label(win, text="⌨  Keyboard Shortcuts",
                 bg=C["bg"], fg=C["txt"],
                 font=(FONT_UI, 12, "bold")).pack(pady=(16, 8), padx=20, anchor="w")
        shortcuts = [
            ("Ctrl + Enter", "Speak text (TTS)"),
            ("Ctrl + R",     "Start/stop recording"),
            ("Ctrl + S",     "Save current output"),
            ("Ctrl + H",     "Open history"),
            ("Ctrl + ,",     "Open settings"),
            ("Escape",       "Stop all operations"),
            ("F1",           "Show this help"),
        ]
        for key, desc in shortcuts:
            row = tk.Frame(win, bg=C["layer2"])
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(row, text=key, width=16, anchor="w",
                     bg=C["layer2"], fg=C["amber"],
                     font=(FONT_MONO, 9, "bold")).pack(side="left", padx=8, pady=5)
            tk.Label(row, text=desc, anchor="w",
                     bg=C["layer2"], fg=C["txt_dim"],
                     font=(FONT_UI, 9)).pack(side="left", padx=4)
        FlatButton(win, "Close", win.destroy,
                   accent=C["txt_muted"]).pack(pady=12)

    # ══════════════════════════════════════════════════════════════════════════
    #  STT CONTROLS
    # ══════════════════════════════════════════════════════════════════════════

    def _stt_src_toggle(self):
        if self._stt_src.get() == "file":
            self._stt_file_bar.pack(side="left", padx=(12, 0), fill="y")
        else:
            self._stt_file_bar.pack_forget()

    def _stt_browse(self):
        p = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio", "*.wav *.mp3 *.flac *.ogg"),
                       ("WAV", "*.wav"), ("MP3", "*.mp3"), ("All", "*.*")],
            initialdir=self.cfg.save_dir, parent=self)
        if p: self._stt_fv.set(p)

    def _toggle_record(self):
        if not self._stt:
            self._err("STT Unavailable",
                      f"Speech recognition failed to load:\n\n{self._stt_err}")
            return
        if self._rec_active: self._stop_record()
        else:                self._start_record()

    def _start_record(self):
        src = self._stt_src.get()
        if src == "file":
            path = self._stt_fv.get().strip()
            if not path:
                self._warn("No File", "Please select an audio file."); return
            if not Path(path).exists():
                self._err("Not Found", f"File not found:\n{path}"); return

        self._rec_active = True
        self._rec_start  = time.time()
        self._stt_dot.start(C["rose"])
        self._btn_rec.configure_state(True, C["rose"])
        self._btn_rec.set_text("⏹  Stop Recording")
        self._stt_st.config(text="Starting…", fg=C["amber"])
        self.statusbar.set("Recording…", C["rose"])
        self.statusbar.pulse(C["rose"])
        self._progress.start(C["rose"])
        self._update_stt_timer()

        cb = dict(
            on_status=lambda m: self._q.put(("stt_st", m)),
            on_result=lambda t: self._q.put(("stt_ok", t)),
            on_error =lambda e: self._q.put(("stt_err", e)),
        )
        if src == "mic":
            self._stt_thread = self._stt.transcribe_mic(
                mic_index=self.cfg.mic_index, **cb)
        else:
            self._stt_thread = self._stt.transcribe_file(
                self._stt_fv.get().strip(), **cb)

    def _stop_record(self):
        self._rec_active = False
        if self._stt: self._stt.stop()
        self._stt_dot.stop()
        self._btn_rec.configure_state(False)
        self._btn_rec.set_text("⏺  Start Recording")
        self._stt_st.config(text="Idle", fg=C["txt_muted"])
        self._stt_timer.config(text="00:00")
        self.statusbar.set("Stopped.", C["txt_dim"])
        self.statusbar.still()
        self._progress.stop()

    def _update_stt_timer(self):
        if not self._rec_active: return
        elapsed = int(time.time() - self._rec_start)
        m, s = divmod(elapsed, 60)
        self._stt_timer.config(text=f"{m:02d}:{s:02d}", fg=C["rose"])
        self.after(500, self._update_stt_timer)

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
            filetypes=[("Text", "*.txt *.md *.log"), ("All", "*.*")],
            initialdir=self.cfg.save_dir, parent=self)
        if p:
            self._tts_fv.set(p)
            self._load_text_path(p)

    def _toggle_speak(self):
        if not self._tts:
            self._err("TTS Unavailable",
                      f"TTS engine failed:\n\n{self._tts_err}"); return
        if self._spk_active: self._stop_speak()
        else:                self._start_speak()

    def _start_speak(self):
        text = self._get_tts_text()
        if not text.strip():
            self._warn("Nothing to Speak",
                       "The editor is empty.\nType or load some text first.")
            return

        self._tts._stop.clear()
        self._spk_active = True
        self._spk_start  = time.time()
        self._spk_dot.start(C["amber"])
        self._btn_spk.configure_state(True, C["amber"])
        self._btn_spk.set_text("⏹  Stop")
        self._spk_st.config(text="Speaking…", fg=C["amber"])
        self.statusbar.set("Speaking…", C["amber"])
        self.statusbar.pulse(C["amber"])
        self._progress.start(C["amber"])
        self._update_spk_timer()

        self._tts_thread = self._tts.speak_async(
            text,
            on_done =lambda:   self._q.put(("tts_done", "")),
            on_error=lambda e: self._q.put(("tts_err",  e)),
        )

    def _stop_speak(self):
        self._spk_active = False
        if self._tts: self._tts.stop()
        self._spk_dot.stop()
        self._btn_spk.configure_state(False)
        self._btn_spk.set_text("▶  Speak Text")
        self._spk_st.config(text="Idle", fg=C["txt_muted"])
        self._spk_timer.config(text="00:00")
        self.statusbar.set("Stopped.", C["txt_dim"])
        self.statusbar.still()
        self._progress.stop()

    def _update_spk_timer(self):
        if not self._spk_active: return
        elapsed = int(time.time() - self._spk_start)
        m, s = divmod(elapsed, 60)
        self._spk_timer.config(text=f"{m:02d}:{s:02d}", fg=C["amber"])
        self.after(500, self._update_spk_timer)

    # ══════════════════════════════════════════════════════════════════════════
    #  TEXT / FILE HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _get_tts_text(self) -> str:
        src = self._tts_src.get()
        if src == "editor":
            return self._tts_ed.get_real_text()
        if src == "file":
            p = self._tts_fv.get().strip()
            if not p:
                return self._tts_ed.get_real_text()
            try:
                return Path(p).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                self._err("Read Error", str(e)); return ""
        if src == "clip":
            try: return self.clipboard_get()
            except Exception: return ""
        return ""

    def _load_text_path(self, path: str):
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            self._tts_ed.clear_ph(None)
            self._tts_ed.delete("1.0", "end")
            self._tts_ed.insert("1.0", text)
            self._tts_ed.text.config(fg=C["txt"])
            self.cfg.save_dir = str(Path(path).parent)
            self.statusbar.set(f"Loaded  {Path(path).name}  "
                               f"({len(text):,} chars)", C["teal"])
        except FileNotFoundError:
            self._err("Not Found", f"File not found:\n{path}")
        except PermissionError:
            self._err("Permission", f"Cannot read:\n{path}")
        except OSError as e:
            self._err("Read Error", str(e))

    def _load_clipboard(self):
        try:
            text = self.clipboard_get()
            if text.strip():
                self._tts_ed.clear_ph(None)
                self._tts_ed.delete("1.0", "end")
                self._tts_ed.insert("1.0", text)
                self._tts_ed.text.config(fg=C["txt"])
                self.statusbar.set(
                    f"Clipboard loaded — {len(text):,} chars", C["teal"])
        except Exception as e:
            self._err("Clipboard Error", str(e))

    def _quick_insert(self, s: str):
        self._tts_ed.clear_ph(None)
        cur = self._tts_ed.get("1.0", "end-1c")
        sep = " " if cur and not cur.endswith(" ") else ""
        self._tts_ed.insert("end", sep + s)
        self._tts_ed.text.config(fg=C["txt"])

    # ── Word / char counts ────────────────────────────────────────────────────

    def _stt_text_changed(self, _=None):
        t = self._stt_ed.get("1.0", "end-1c")
        w = len(t.split()) if t.strip() else 0
        self._stt_info.config(text=f"{w:,} words  ·  {len(t):,} chars")

    def _tts_text_changed(self, _=None):
        w, c = self._tts_ed.word_count()
        self._tts_wc.config(text=f"{w:,} words  ·  {c:,} chars")

    # ══════════════════════════════════════════════════════════════════════════
    #  SAVE / EXPORT
    # ══════════════════════════════════════════════════════════════════════════

    def _stt_save(self):
        text = self._stt_ed.get("1.0", "end-1c").strip()
        if not text:
            self._warn("Empty", "Transcription box is empty."); return
        ext = self._stt_fmt.get()
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title="Save Transcription",
            defaultextension=f".{ext}",
            filetypes=[("Text", "*.txt"), ("Markdown", "*.md"),
                       ("Log", "*.log"), ("All", "*.*")],
            initialdir=self.cfg.save_dir,
            initialfile=f"transcript_{ts}.{ext}",
            parent=self)
        if not path: return
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if ext == "md":
                content = (f"# Transcription\n\n"
                           f"> *Voice Studio v{APP_VERSION} — {now}*\n\n"
                           f"---\n\n{text}\n")
            elif ext == "log":
                content = (f"[{datetime.datetime.now().isoformat()}] TRANSCRIPTION\n"
                           f"{'─' * 64}\n{text}\n{'─' * 64}\n")
            else:
                content = text
            p.write_text(content, encoding="utf-8")
            self.cfg.save_dir = str(p.parent)
            self.hist.add("STT Save", text)
            self.statusbar.set(f"Saved  →  {p.name}", C["teal"])
            log.info(f"Transcript saved: {p}")
        except PermissionError:
            self._err("Permission Denied", f"Cannot write to:\n{path}")
        except OSError as e:
            self._err("Save Error", str(e))

    def _stt_copy(self):
        text = self._stt_ed.get("1.0", "end-1c").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.statusbar.set("Copied to clipboard.", C["teal"])

    def _stt_clear(self):
        self._stt_ed.delete("1.0", "end")
        self._stt_info.config(text="0 words · 0 chars")

    def _tts_save_audio(self):
        if not self._tts:
            self._err("Unavailable", "TTS engine is not available."); return
        text = self._get_tts_text()
        if not text.strip():
            self._warn("Empty", "Editor is empty."); return
        ext = self._tts_fmt.get()
        if ext == "mp3" and not HAS_GTTS:
            self._err("gTTS Required",
                      "MP3 export requires gTTS (online).\n"
                      "Install: pip install gTTS\n\nOr switch to WAV."); return

        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title="Save Audio",
            defaultextension=f".{ext}",
            filetypes=[("WAV", "*.wav"), ("MP3", "*.mp3"), ("All", "*.*")],
            initialdir=self.cfg.save_dir,
            initialfile=f"speech_{ts}.{ext}",
            parent=self)
        if not path: return

        orig_eng = self.cfg._d.get("tts_engine", "pyttsx3")
        if ext == "mp3": self.cfg._d["tts_engine"] = "gtts"

        self.statusbar.set("Saving audio…", C["warn"])
        self._progress.start(C["warn"])
        self.update_idletasks()

        def _done(saved):
            self.cfg._d["tts_engine"] = orig_eng
            self._q.put(("tts_saved", saved))

        def _err_cb(msg):
            self.cfg._d["tts_engine"] = orig_eng
            self._q.put(("tts_err", msg))

        self._tts.save_to_file(text, path, on_done=_done, on_error=_err_cb)

    def _tts_load_file(self):
        p = filedialog.askopenfilename(
            title="Load Text File",
            filetypes=[("Text", "*.txt *.md *.log"), ("All", "*.*")],
            initialdir=self.cfg.save_dir, parent=self)
        if p: self._load_text_path(p)

    def _tts_clear(self):
        self._tts_ed.delete("1.0", "end")
        self._tts_ed._restore_ph(None)

    # ── Auto-save ─────────────────────────────────────────────────────────────

    def _auto_save(self, text: str):
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            out = SAVE_DIR / f"auto_{ts}.txt"
            out.write_text(text, encoding="utf-8")
            log.info(f"Auto-saved: {out.name}")
        except Exception as e:
            log.warning(f"Auto-save failed: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    #  QUEUE POLL
    # ══════════════════════════════════════════════════════════════════════════

    def _poll(self):
        try:
            while True:
                kind, payload = self._q.get_nowait()

                if kind == "stt_st":
                    self._stt_st.config(text=payload, fg=C["amber"])
                    self.statusbar.set(payload, C["amber"])

                elif kind == "stt_ok":
                    self._rec_active = False
                    self._stt_dot.stop()
                    self._btn_rec.configure_state(False)
                    self._btn_rec.set_text("⏺  Start Recording")
                    self._stt_timer.config(text="00:00")
                    self._stt_st.config(text="Done ✓", fg=C["teal"])
                    self._progress.stop()
                    self.statusbar.set(
                        f"Transcribed  ·  {len(payload):,} chars", C["teal"])
                    self.statusbar.still(C["teal"])

                    if self._stt_append.get():
                        ex = self._stt_ed.get("1.0", "end-1c").strip()
                        self._stt_ed.insert("end",
                                            ("\n\n" if ex else "") + payload)
                    else:
                        self._stt_ed.delete("1.0", "end")
                        self._stt_ed.insert("1.0", payload)
                    self._stt_ed.see("end")
                    self.hist.add("STT", payload)
                    if self.cfg.auto_save:
                        self._auto_save(payload)

                elif kind == "stt_err":
                    self._rec_active = False
                    self._stt_dot.stop()
                    self._btn_rec.configure_state(False)
                    self._btn_rec.set_text("⏺  Start Recording")
                    self._stt_timer.config(text="00:00")
                    self._stt_st.config(text="Error", fg=C["err"])
                    self._progress.stop()
                    short = payload.split("\n")[0][:80]
                    self.statusbar.set(f"Error — {short}", C["err"])
                    self.statusbar.still(C["err"])
                    self._err("Transcription Error", payload)

                elif kind == "tts_done":
                    self._spk_active = False
                    self._spk_dot.stop()
                    self._btn_spk.configure_state(False)
                    self._btn_spk.set_text("▶  Speak Text")
                    self._spk_timer.config(text="00:00")
                    self._spk_st.config(text="Done ✓", fg=C["teal"])
                    self._progress.stop()
                    dur = time.time() - self._spk_start
                    self.statusbar.set(
                        f"Speech complete  ·  {dur:.1f}s", C["teal"])
                    self.statusbar.still(C["teal"])
                    text = self._get_tts_text()
                    if text:
                        self.hist.add("TTS", text,
                                      duration=dur)

                elif kind == "tts_err":
                    self._spk_active = False
                    self._spk_dot.stop()
                    self._btn_spk.configure_state(False)
                    self._btn_spk.set_text("▶  Speak Text")
                    self._spk_timer.config(text="00:00")
                    self._spk_st.config(text="Error", fg=C["err"])
                    self._progress.stop()
                    short = payload.split("\n")[0][:80]
                    self.statusbar.set(f"TTS Error — {short}", C["err"])
                    self.statusbar.still(C["err"])
                    self._err("TTS Error", payload)

                elif kind == "tts_saved":
                    self._progress.stop()
                    p = Path(payload)
                    self.cfg.save_dir = str(p.parent)
                    self.hist.add("TTS Save", payload)
                    try:
                        size_kb = p.stat().st_size // 1024
                        size_str = f"  ({size_kb} KB)"
                    except Exception:
                        size_str = ""
                    self.statusbar.set(
                        f"Audio saved  →  {p.name}{size_str}", C["teal"])
                    messagebox.showinfo("Audio Saved",
                                        f"Saved successfully:\n{payload}",
                                        parent=self)

        except queue.Empty:
            pass
        self.after(60, self._poll)

    # ══════════════════════════════════════════════════════════════════════════
    #  DIALOGS
    # ══════════════════════════════════════════════════════════════════════════

    def _open_settings(self):
        SettingsDialog(self, self.cfg, self._tts, self._stt)

    def _open_history(self):
        HistoryWindow(self, self.hist, on_copy=None)

    def _open_log(self):
        try:
            log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log_text = f"Could not read log file:\n{e}"

        win = tk.Toplevel(self)
        win.title("Application Log")
        win.geometry("780x500")
        win.configure(bg=C["bg"])
        win.transient(self)

        hdr = tk.Frame(win, bg=C["layer1"], height=48)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=f"📋  Log  ·  {LOG_PATH}",
                 bg=C["layer1"], fg=C["txt"],
                 font=(FONT_UI, 10, "bold")).pack(side="left", padx=16, pady=14)
        tk.Frame(win, bg=C["edge0"], height=1).pack(fill="x")

        outer = tk.Frame(win, bg=C["edge1"])
        outer.pack(fill="both", expand=True, padx=16, pady=12)
        box = tk.Text(outer, bg=C["layer2"], fg=C["txt_dim"],
                      relief="flat", bd=0, padx=14, pady=10,
                      font=(FONT_MONO, 8), wrap="none", state="disabled")
        xsb = ttk.Scrollbar(outer, orient="horizontal", command=box.xview)
        ysb = ttk.Scrollbar(outer, orient="vertical",   command=box.yview)
        box.configure(xscrollcommand=xsb.set, yscrollcommand=ysb.set)
        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        box.pack(fill="both", expand=True)

        box.config(state="normal")
        # Colorize log levels
        for tag, col in [("ERROR",   C["err"]),
                         ("WARNING", C["warn"]),
                         ("DEBUG",   C["txt_faint"]),
                         ("INFO",    C["txt_dim"])]:
            box.tag_config(tag, foreground=col)

        lines = log_text.split("\n")[-500:]  # last 500 lines
        for line in lines:
            for level in ("ERROR", "WARNING", "INFO", "DEBUG"):
                if f"[{level}" in line:
                    box.insert("end", line + "\n", level)
                    break
            else:
                box.insert("end", line + "\n")
        box.config(state="disabled")
        box.see("end")

        def _open_folder():
            try:
                if sys.platform == "win32":
                    os.startfile(str(SAVE_DIR))
                elif sys.platform == "darwin":
                    os.system(f'open "{SAVE_DIR}"')
                else:
                    os.system(f'xdg-open "{SAVE_DIR}" &')
            except Exception as ex:
                log.warning(f"Could not open folder: {ex}")

        bf = tk.Frame(win, bg=C["bg"])
        bf.pack(fill="x", padx=16, pady=(0, 12))
        FlatButton(bf, "✕  Close", win.destroy,
                   accent=C["txt_muted"]).pack(side="right", padx=4)
        FlatButton(bf, "📂  Open Folder", _open_folder,
                   accent=C["blue"]).pack(side="right", padx=4)

    # ── Helper dialogs ────────────────────────────────────────────────────────

    def _err(self, title, msg):
        log.error(f"[Dialog] {title}: {msg[:200]}")
        messagebox.showerror(title, msg, parent=self)

    def _warn(self, title, msg):
        log.warning(f"[Dialog] {title}: {msg[:200]}")
        messagebox.showwarning(title, msg, parent=self)

    # ── Ready ─────────────────────────────────────────────────────────────────

    def _ready(self):
        parts = []
        if self._tts:
            eng = self.cfg.tts_engine
            self._tts_pill.config(text=f"● TTS: {eng}", fg=C["ok"])
            parts.append(f"TTS: {eng}")
        else:
            self._tts_pill.config(text="● TTS: unavailable", fg=C["err"])
            parts.append("TTS: unavailable")

        if self._stt:
            avail = "mic OK" if self._stt.mic_available else "no mic"
            col   = C["ok"] if "OK" in avail else C["warn"]
            self._stt_pill.config(text=f"● STT: Google ({avail})", fg=col)
            parts.append(f"STT: {avail}")
        else:
            self._stt_pill.config(text="● STT: unavailable", fg=C["err"])
            parts.append("STT: unavailable")

        ok    = self._tts and self._stt
        color = C["ok"] if ok else C["warn"]
        self.statusbar.set("Ready  ·  " + "  ·  ".join(parts), color)
        self.statusbar.still(color)
        log.info("Ready. " + " | ".join(parts))

    # ── Quit ──────────────────────────────────────────────────────────────────

    def _quit(self):
        log.info("Shutting down…")
        self._stop_all()
        self.cfg.save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if getattr(sys, "frozen", False):
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    try:
        app = VoiceStudio()
        app.mainloop()
    except Exception:
        err = traceback.format_exc()
        log.critical(f"Fatal: {err}")
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Fatal Error",
                                 f"Voice Studio crashed:\n\n{err}")
            root.destroy()
        except Exception:
            print(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
