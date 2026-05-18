<div align="center">

# 🎙️ Voice Studio

### Speech ↔ Text Desktop Application &nbsp;·&nbsp; Cross-Platform &nbsp;·&nbsp; Offline-Capable

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+"></a>
  <a href="https://docs.python.org/3/library/tkinter.html"><img src="https://img.shields.io/badge/GUI-Tkinter-FF6B35?style=for-the-badge" alt="Tkinter"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22d3a4?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.linkedin.com/in/abhishek-srivastava-1538461b1/"><img src="https://img.shields.io/badge/Author-Abhishek%20Srivastava-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
</p>

*A production-grade, offline-capable speech-to-text and text-to-speech desktop application built entirely in Python — no Electron, no web frameworks, pure Tkinter.*

**[Features](#-features) &nbsp;·&nbsp; [Editions](#-editions) &nbsp;·&nbsp; [Requirements](#%EF%B8%8F-requirements) &nbsp;·&nbsp; [Installation](#-installation) &nbsp;·&nbsp; [Usage](#-usage) &nbsp;·&nbsp; [Keyboard Shortcuts](#%EF%B8%8F-keyboard-shortcuts) &nbsp;·&nbsp; [Settings](#%EF%B8%8F-settings) &nbsp;·&nbsp; [Build to EXE](#%EF%B8%8F-build-to-exe) &nbsp;·&nbsp; [Project Structure](#-project-structure) &nbsp;·&nbsp; [Troubleshooting](#-troubleshooting) &nbsp;·&nbsp; [License](#-license) &nbsp;·&nbsp; [Author](#-author)**

</div>

---

## ✨ Features

| Feature | Classic `app_v1` | Premium `app_v2` |
|---|:---:|:---:|
| Speech → Text via Microphone | ✅ | ✅ |
| Speech → Text via Audio File — WAV / MP3 | ✅ | ✅ |
| Speech → Text via Audio File — FLAC / OGG / AIFF | — | ✅ |
| Text → Speech — pyttsx3 offline (50–400 wpm) | ✅ | ✅ |
| Text → Speech — gTTS online (16 languages) | ✅ | ✅ |
| Text → Speech — gTTS online (24 languages) | — | ✅ |
| TTS character limit guard (8,000 chars) | — | ✅ |
| Export audio — WAV (offline) | ✅ | ✅ |
| Export audio — MP3 (online via gTTS) | ✅ | ✅ |
| Save transcript — `.txt` / `.md` / `.log` | ✅ | ✅ |
| Word & character count | ✅ | ✅ |
| Quick-insert text chips | ✅ | ✅ |
| Append / replace transcription mode | ✅ | ✅ |
| Animated waveform visualiser | ✅ | — |
| Animated recording & speaking indicator dots | ✅ | ✅ |
| Toast notifications | ✅ | — |
| In-text search / highlight (STT tab) | ✅ | — |
| Session history (view & clear) | ✅ | ✅ |
| Settings dialog — TTS / STT / General | ✅ | ✅ |
| Persistent settings (`.settings_v1.json` / `.settings.json`) | ✅ | ✅ |
| Debounced settings save | — | ✅ |
| Window geometry persistence | — | ✅ |
| Auto-save transcriptions | ✅ | ✅ |
| Thread-safe auto-save (non-blocking) | — | ✅ |
| Blue-accented dark theme (`#050810` base) | ✅ | — |
| Deep cosmic dark theme — amber / teal (`#070b12` base) | — | ✅ |
| Animated shimmer progress bar | — | ✅ |
| Line-number editor gutter | — | ✅ |
| Font zoom buttons (A− / A+) | — | ✅ |
| 7+ keyboard shortcuts | ✅ | ✅ |
| Live MM:SS timer — recording & speaking | — | ✅ |
| Refresh mic list button | — | ✅ |
| STT recognition language selector | — | ✅ |
| History search / filter | — | ✅ |
| History export — `.txt` / `.json` | — | ✅ |
| Configurable history limit (50–500 entries) | — | ✅ |
| In-app log viewer (colour-coded, last 500 lines) | — | ✅ |
| Structured file logging (`voicestudio.log`) | — | ✅ |
| About dialog | — | ✅ |
| Startup tab preference | — | ✅ |
| Safe `pyttsx3` engine — fresh instance per call | ✅ | ✅ |
| Python 3.12 + Windows scrollbar TclError fix | ✅ | ✅ |

---

## 📦 Editions

### `src/app_v1.py` — Classic Edition (v1.0)

Clean, functional, and lightweight. Blue-accented dark UI (`#050810` base) built with standard Tkinter.

Covers all core features: microphone and file-based STT (WAV/MP3), offline and online TTS (50–400 wpm), WAV/MP3 audio export, transcript save in `.txt`/`.md`/`.log`, animated waveform visualiser, in-text search with highlighting, toast notifications, quick-insert chips, word/char count, append/replace mode, session history, and a full three-tab Settings dialog (TTS / STT / General). Settings include auto-save, word wrap, and font size controls.

Notable engineering details: all `ttk` styles are registered after `theme_use()`, a scrollbar factory (`_make_scrollbar`) falls back gracefully to `tk.Scrollbar` on Python 3.12 + Windows to avoid `TclError`, `pyttsx3` engines are created fresh per call and always `del`'d after use, and all `widget.after()` calls are guarded with `winfo_exists()`.

### `src/app_v2.py` — Premium Edition (v2.0) ⭐ Recommended

Everything in Classic, plus:

- **Amber/teal cosmic dark theme** (`#070b12` base) with a coloured top accent stripe
- **Animated shimmer progress bar** — shows activity during recording, speaking, and saving
- **Line-number editor** with real-time gutter sync
- **Live MM:SS timers** on recording and speaking
- **Font zoom** — A− / A+ buttons in both sidebars, `Ctrl+=`/`Ctrl+-` shortcuts
- **Escape** key stops all active operations instantly
- **STT recognition language** selector (22 BCP-47 locales, e.g. `en-US`, `hi-IN`, `zh-cmn-Hans-CN`)
- **Refresh mic list** button in Settings → STT
- **History** with text filter, entry count, and export to `.txt` or `.json`
- **In-app log viewer** — colour-coded by level (DEBUG / INFO / WARNING / ERROR), last 500 lines, open-folder button
- **Structured file logging** to `~/VoiceStudio/voicestudio.log` via `logging`
- **TTS character limit** — inputs over 8,000 chars are truncated with a UI warning
- **Debounced settings save** — coalesces rapid writes into one disk operation
- **Window geometry persistence** — restores size and position between sessions
- **About dialog** — Python version, active backends, save directory
- **Startup tab preference** — open on Speech→Text or Text→Speech

gTTS language list expands from 16 to 24 locales (adds `en-uk`, `en-au`, `zh-tw`, `da`, `fi`, `el`, `bn`, `ur`). Audio file input additionally accepts FLAC, OGG, and AIFF via the browse dialog.

---

## 🖥️ Requirements

### System

- **Python** 3.9 or higher (3.12 fully supported)
- **Windows** 10/11 &nbsp;·&nbsp; **macOS** 12+ &nbsp;·&nbsp; **Linux** (Ubuntu 20.04+)
- Active **internet connection** for Google Speech Recognition and gTTS — offline pyttsx3 TTS always works without it

### Python Packages

```bash
pip install SpeechRecognition pyttsx3 gTTS pyaudio pydub pygame
```

Or install from a requirements file:

```bash
pip install -r requirements.txt
```

| Package | Purpose | Required? |
|---|---|:---:|
| [`SpeechRecognition`](https://github.com/Uberi/speech_recognition) | Speech-to-text via Google Speech API | ✅ Yes |
| [`PyAudio`](https://people.csail.mit.edu/hubert/pyaudio/) | Microphone access | ✅ Yes |
| [`pyttsx3`](https://github.com/nateshmbhat/pyttsx3) | Offline TTS engine | ✅ Yes |
| [`gTTS`](https://github.com/pndurette/gTTS) | Online TTS + MP3 export | Optional |
| [`pygame`](https://www.pygame.org/) | MP3 playback for gTTS output | Optional |
| [`pydub`](https://github.com/jiaaro/pydub) | Audio format conversion / fallback playback | Optional |
| [`PyInstaller`](https://pyinstaller.org/) | Package app to standalone binary | Build only |

> Both editions detect missing optional packages at startup and disable affected features gracefully — no crashes, no import errors.

### Linux

```bash
sudo apt install portaudio19-dev python3-tk espeak
```

### macOS

```bash
brew install portaudio
```

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/voice-studio.git
cd voice-studio

# 2. Create a virtual environment (recommended)
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install SpeechRecognition pyttsx3 gTTS pyaudio pydub pygame

# 4. Launch

# Classic Edition
python src/app_v1.py

# Premium Edition (recommended)
python src/app_v2.py
```

---

## 🎯 Usage

### Speech → Text 🎙️

1. Open the **Speech → Text** tab
2. Select **🎤 Microphone** or **📂 Audio File** as the input source
3. If using an audio file, click **Browse…** to pick a `.wav`, `.mp3` (or `.flac`/`.ogg`/`.aiff` in Premium)
4. Click **⏺ Start Recording** — or press `Ctrl+R`
5. The app auto-calibrates for ambient noise before listening
6. Transcription appears in the editor once recognition completes
7. Save as `.txt`, `.md`, or `.log` — or click **📋 Copy All**

> The **Append results** checkbox controls whether new transcriptions are added to existing text or replace it.

### Text → Speech 🔊

1. Open the **Text → Speech** tab
2. Choose a text source: **Type in editor**, **From text file**, or **From clipboard**
3. Use the **Quick-insert chips** at the top for instant test phrases
4. Click **▶ Speak Text** — or press `Ctrl+Enter` (Premium) / `Ctrl+T` (Classic)
5. Export audio as `.wav` via pyttsx3 (offline) or `.mp3` via gTTS (online, internet required)

> Premium Edition: if the input exceeds 8,000 characters a warning label appears and only the first 8,000 chars are synthesised.

---

## ⌨️ Keyboard Shortcuts

### Classic Edition (`app_v1.py`)

| Shortcut | Action |
|---|---|
| `Ctrl + R` | Start / stop recording |
| `Ctrl + T` | Speak / stop text |
| `Ctrl + S` | Save current output |
| `Ctrl + C` | Copy all (STT tab) |
| `Ctrl + L` | Clear current tab |
| `Ctrl + ,` | Open Settings |
| `Ctrl + H` | Show History |
| `F1` | Toggle tab (STT ↔ TTS) |

### Premium Edition (`app_v2.py`)

| Shortcut | Action |
|---|---|
| `Ctrl + Enter` | Speak text (TTS) |
| `Ctrl + R` | Start / stop recording |
| `Ctrl + S` | Save — transcript or audio |
| `Ctrl + H` | Open history |
| `Ctrl + ,` | Open settings |
| `Ctrl + Shift + V` | Paste clipboard → TTS editor |
| `Ctrl + =` / `Ctrl + +` | Zoom font in |
| `Ctrl + -` / `Ctrl + _` | Zoom font out |
| `Escape` | Stop all operations |
| `F1` | Show keyboard shortcut help |
| `F2` | Open About dialog |

---

## ⚙️ Settings

Both editions open the Settings dialog via the **⚙ Settings** header button.

### TTS Tab

| Setting | Classic | Premium |
|---|---|---|
| Engine | pyttsx3 (offline) / gTTS (online) | pyttsx3 (offline) / gTTS (online) |
| Voice | System voices via pyttsx3 | System voices via pyttsx3 |
| Rate | 50–400 wpm slider | 50–450 wpm slider + live readout |
| Volume | 0.0–1.0 | 0.0–1.0 + live readout |
| gTTS Language | 16 locales (en, hi, es, fr, de, it, pt, ru, zh-cn, ja, ko, ar, tr, nl, pl, sv) | 24 locales (adds en-uk, en-au, zh-tw, da, fi, el, bn, ur) |

### STT Tab

| Setting | Classic | Premium |
|---|---|---|
| Microphone device | Dropdown from detected devices | Dropdown + ↺ Refresh button |
| Recognition language | Fixed (en-US) | 22 BCP-47 locales (en-US, hi-IN, zh-cmn-Hans-CN, …) |
| Energy threshold | 50–4000 | 50–4000 + live readout |
| Pause threshold | 0.3–3.0 s | 0.3–3.0 s + live readout |
| Listen timeout | 2–120 s | 3–120 s + live readout |
| Phrase time limit | 3–180 s | 5–300 s + live readout |

### General Tab

| Setting | Classic | Premium |
|---|---|---|
| Auto-save every transcription | ✅ | ✅ |
| Show toast notifications | ✅ | — |
| Word wrap | ✅ | ✅ |
| Editor font size | 8–24 | 8–22 + live readout |
| Save directory (browse) | ✅ | — |
| History limit | — | 50–500 entries (step 50) |
| Startup tab | — | Speech→Text or Text→Speech |

Settings persist automatically:

| Edition | Settings file |
|---|---|
| Classic (`app_v1.py`) | `~/VoiceStudio/.settings_v1.json` |
| Premium (`app_v2.py`) | `~/VoiceStudio/.settings.json` |

---

## 🏗️ Build to EXE

Convert either script to a standalone `.exe` (Windows) or binary (macOS/Linux) using [PyInstaller](https://pyinstaller.org/).

### Step 1 — Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2 — Build

**Windows**
```bash
# Classic Edition
pyinstaller --onefile --noconsole --name "VoiceStudio-Classic" src/app_v1.py

# Premium Edition (recommended)
pyinstaller --onefile --noconsole --name "VoiceStudio" src/app_v2.py
```

**macOS**
```bash
pyinstaller --onefile --noconsole --name "VoiceStudio" src/app_v2.py
```

**Linux**
```bash
pyinstaller --onefile --name "VoiceStudio" src/app_v2.py
```

### Step 3 — Add a Custom Icon (optional)

```bash
# Windows — .ico file required
pyinstaller --onefile --noconsole --icon=assets/icon.ico --name "VoiceStudio" src/app_v2.py

# macOS — .icns file required
pyinstaller --onefile --noconsole --icon=assets/icon.icns --name "VoiceStudio" src/app_v2.py
```

### Step 4 — Locate the Output

```
dist/
├── VoiceStudio.exe      ← Windows portable executable
└── VoiceStudio          ← macOS / Linux binary
```

> **Tip:** `--onefile` bundles everything into a single file. Remove it for a faster-starting `dist/VoiceStudio/` folder distribution.

### Build Flags Reference

| Flag | Effect |
|---|---|
| `--onefile` | Bundle into a single executable |
| `--noconsole` | No terminal window on launch (Windows / macOS) |
| `--icon=path` | Custom app icon — `.ico` on Windows, `.icns` on macOS |
| `--name "AppName"` | Set the output file name |
| `--add-data "src;src"` | Bundle extra data files alongside the binary |
| `--hidden-import x` | Force-include a module PyInstaller's static analysis misses |

### Required Hidden Imports

`pyttsx3` and `speech_recognition` drivers are frequently missed by PyInstaller. Add the platform flags below to avoid silent runtime failures:

**Windows**
```bash
pyinstaller --onefile --noconsole \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.sapi5 \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" src/app_v2.py
```

**macOS**
```bash
pyinstaller --onefile --noconsole \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.nsss \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" src/app_v2.py
```

**Linux**
```bash
pyinstaller --onefile \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.espeak \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" src/app_v2.py
```

---

## 📁 Project Structure

```
voice-studio/
│
├── src/
│   ├── app_v1.py              # Classic Edition — v1.0
│   └── app_v2.py              # Premium Edition — v2.0 (recommended)
│
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes build/, dist/, *.spec, runtime data & audio
├── LICENSE                    # MIT License — © 2026 Abhishek Srivastava
└── README.md                  # This file
```

### Auto-generated at Runtime

```
~/VoiceStudio/
├── .settings_v1.json           # Classic Edition saved preferences
├── .settings.json              # Premium Edition saved preferences
├── voicestudio.log             # Structured application log (Premium only)
└── auto_YYYYMMDD_HHMMSS.txt    # Auto-saved transcriptions (when enabled)
```

> These runtime paths should be excluded from version control via `.gitignore`.

### Recommended `.gitignore` Entries

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python

# Virtual environments
venv/
.venv/
env/
ENV/

# Build output
build/
dist/
*.spec
*.egg-info/
*.egg
MANIFEST

# Runtime data
VoiceStudio/
*.log
auto_*.txt
.settings.json
.settings_v1.json

# Audio files
*.wav
*.mp3
*.flac
*.ogg
*.aiff
*.aac
*.m4a

# OS & temp files
.DS_Store
Thumbs.db
Desktop.ini
$RECYCLE.BIN/
*.lnk
*~
*.tmp
*.bak
*.swp
tempCodeRunnerFile.py

# IDE
.vscode/
.idea/
*.sublime-project
*.sublime-workspace
```

---

## 🔧 Troubleshooting

**Microphone not detected**
- Check OS microphone permissions — Privacy & Security on Windows/macOS, PulseAudio/ALSA on Linux
- Ensure the mic is not muted in system audio settings
- Try selecting a different device in **Settings → STT → Device**
- In Premium, click ↺ **Refresh** in the mic dropdown to re-scan devices

**`PyAudio` install fails on Windows**
```bash
pip install pipwin
pipwin install pyaudio
```
Or download a pre-built wheel from [Christoph Gohlke's repository](https://www.cgohlke.com/) and install with `pip install PyAudio‑*.whl`.

**`PyAudio` install fails on Linux**
```bash
sudo apt install portaudio19-dev
pip install pyaudio
```

**Speech not recognised**
- Confirm an active internet connection — Google Speech API is required for all STT
- Raise the energy threshold in **Settings → STT** if background noise is high
- Speak clearly at normal pace, close to the microphone
- Try lowering the pause threshold if phrases are being cut off early

**No sound from pyttsx3 on Linux**
```bash
sudo apt install espeak
```

**MP3 export fails**
- MP3 export requires `gTTS` (encoding) and `pygame` (playback)
- Install: `pip install gTTS pygame`
- If gTTS is unavailable the app shows a clear error — switch to WAV as the fallback

**`_tkinter.TclError` on scrollbar / ttk style (Python 3.12 + Windows)**
Both editions handle this via a scrollbar factory that falls back to `tk.Scrollbar` when the `ttk` style cannot be registered. All `ttk` styles are registered after `theme_use()` and before any widget is created. If you still see this error, ensure you are running the latest version of the file.

**`run loop already started` / `engine already stopped` (pyttsx3)**
Both editions create a fresh `pyttsx3` engine instance per speak call to avoid this known upstream bug — it is handled internally and should not surface to the user.

**EXE crashes on launch**
- Run `python src/app_v2.py` directly first to read the full traceback
- Add the platform-specific `--hidden-import` flags from the [Required Hidden Imports](#required-hidden-imports) section
- Confirm all dependencies are installed in the same Python environment used to build

**Settings not saving**
- Check that `~/VoiceStudio/` is writable — the app falls back to `%TEMP%/VoiceStudio/` on write failure (Premium)
- Classic Edition writes synchronously; Premium Edition uses a 0.4 s debounced write, so changes may not persist if the app is force-killed immediately

---

## 📄 License

This project is licensed under the **[MIT License](LICENSE)** — © 2026 Abhishek Srivastava.

### Third-party Acknowledgements

| Library | License | Repository |
|---|---|---|
| [SpeechRecognition](https://github.com/Uberi/speech_recognition) | BSD | github.com/Uberi/speech_recognition |
| [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) | MIT | people.csail.mit.edu/hubert/pyaudio |
| [pyttsx3](https://github.com/nateshmbhat/pyttsx3) | BSD-2-Clause | github.com/nateshmbhat/pyttsx3 |
| [gTTS](https://github.com/pndurette/gTTS) | MIT | github.com/pndurette/gTTS |
| [pygame](https://www.pygame.org/) | LGPL-2.1 | pygame.org |
| [pydub](https://github.com/jiaaro/pydub) | MIT | github.com/jiaaro/pydub |
| [PyInstaller](https://pyinstaller.org/) | GPL-2 + Bootloader Exception | pyinstaller.org |

Speech recognition is powered by the [Google Speech Recognition API](https://cloud.google.com/speech-to-text). This application does not store, transmit, or share any audio data beyond what is required to perform recognition. Use is subject to [Google's Terms of Service](https://policies.google.com/terms).

---

## 👤 Author

<div align="center">

**Abhishek Srivastava**

<a href="https://www.linkedin.com/in/abhishek-srivastava-1538461b1/">
  <img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
</a>

<br><br>

*Built with Python, Tkinter, and a lot of ☕*

*If you found this useful, consider leaving a ⭐ on the repository!*

</div>
