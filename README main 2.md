<div align="center">

# 🎙️ Voice Studio

### Speech ↔ Text Converter &nbsp;·&nbsp; Desktop App &nbsp;·&nbsp; Cross-Platform

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+"></a>
  <a href="https://docs.python.org/3/library/tkinter.html"><img src="https://img.shields.io/badge/GUI-Tkinter-FF6B35?style=for-the-badge" alt="Tkinter"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22d3a4?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.linkedin.com/in/abhishek-srivastava-1538461b1/"><img src="https://img.shields.io/badge/Author-Abhishek%20Srivastava-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
</p>

*A production-grade, offline-capable speech-to-text and text-to-speech desktop application built entirely in Python.*

**[Features](#-features) &nbsp;·&nbsp; [Editions](#-editions) &nbsp;·&nbsp; [Requirements](#%EF%B8%8F-requirements) &nbsp;·&nbsp; [Installation](#-installation) &nbsp;·&nbsp; [Usage](#-usage) &nbsp;·&nbsp; [Settings](#%EF%B8%8F-settings) &nbsp;·&nbsp; [Build to EXE](#%EF%B8%8F-build-to-exe) &nbsp;·&nbsp; [Project Structure](#-project-structure) &nbsp;·&nbsp; [Troubleshooting](#-troubleshooting) &nbsp;·&nbsp; [License](#-license) &nbsp;·&nbsp; [Author](#-author)**

</div>

---

## ✨ Features

| Feature | Classic `app_v1` | Premium `app_v2` |
|---|:---:|:---:|
| Speech → Text via Microphone | ✅ | ✅ |
| Speech → Text via Audio File — WAV / MP3 | ✅ | ✅ |
| Speech → Text via Audio File — FLAC / OGG | — | ✅ |
| Text → Speech — pyttsx3 offline (50–300 wpm) | ✅ | — |
| Text → Speech — pyttsx3 offline (50–400 wpm) | — | ✅ |
| Text → Speech — gTTS online (14 languages) | ✅ | — |
| Text → Speech — gTTS online (18 languages) | — | ✅ |
| Export audio — WAV (offline) / MP3 (online) | ✅ | ✅ |
| Save transcript — .txt / .md / .log | ✅ | ✅ |
| Word & character count | ✅ | ✅ |
| Quick-insert text chips | ✅ | ✅ |
| Append / replace transcription mode | ✅ | ✅ |
| Animated recording & speaking indicator dots | ✅ | ✅ |
| Session history | ✅ | ✅ |
| Settings dialog — TTS / STT / General | ✅ | ✅ |
| Persistent settings (`.settings.json`) | ✅ | ✅ |
| Auto-save transcriptions | ✅ | ✅ |
| Blue-accented dark theme | ✅ | — |
| Deep cosmic dark theme (amber / teal) | — | ✅ |
| Animated shimmer progress bar | — | ✅ |
| Line-number editor | — | ✅ |
| Keyboard shortcuts (7 bindings) | — | ✅ |
| Live MM:SS timer — recording & speaking | — | ✅ |
| History search, filter & export | — | ✅ |
| In-app log viewer (colour-coded, last 500 lines) | — | ✅ |
| Structured file logging (`voicestudio.log`) | — | ✅ |
| Configurable history limit (50–500 entries) | — | ✅ |
| Startup tab preference | — | ✅ |

---

## 📦 Editions

### `src/app_v1.py` — Classic Edition (v1.0)

Clean, functional, and lightweight. Blue-accented dark UI (`#080b14` base) built with standard Tkinter. Covers all core features: microphone and file-based STT (WAV/MP3), offline and online TTS, WAV/MP3 audio export, transcript save in `.txt`/`.md`/`.log`, quick-insert chips, word/char count, animated recording and speaking dots, session history, and a full three-tab Settings dialog. The General tab provides auto-save and font size (8–20) controls.

### `src/app_v2.py` — Premium Edition (v2.0) ⭐ Recommended

Everything in Classic, plus an amber/teal cosmic dark theme, animated shimmer progress bar, line-number editor, seven keyboard shortcuts, live MM:SS timers on recording and speaking, colour-coded in-app log viewer (INFO / WARNING / ERROR / DEBUG, last 500 lines), searchable/filterable history with export, and structured file logging to `voicestudio.log`. Settings General tab gains history limit (50–500 step 50) and startup tab selector. TTS rate extends to 400 wpm. Audio file input additionally accepts FLAC and OGG. gTTS language list grows from 14 to 18 (adds Polish, Swedish, Danish, and more). Header bar adds a one-click **📋 Log** button alongside ⏱ History and ⚙ Settings.

---

## 🖥️ Requirements

### System

- **Python** 3.9 or higher
- **Windows** 10/11 &nbsp;·&nbsp; **macOS** 12+ &nbsp;·&nbsp; **Linux** (Ubuntu 20.04+)
- Active **internet connection** for Google Speech Recognition and gTTS — offline pyttsx3 TTS always works without it

### Python Packages

```bash
pip install -r requirements.txt
```

| Package | Purpose | Required? |
|---|---|:---:|
| [`SpeechRecognition`](https://github.com/Uberi/speech_recognition) | Speech-to-text core via Google Speech API | ✅ Yes |
| [`PyAudio`](https://people.csail.mit.edu/hubert/pyaudio/) | Microphone access | ✅ Yes |
| [`pyttsx3`](https://github.com/nateshmbhat/pyttsx3) | Offline TTS engine | ✅ Yes |
| [`gTTS`](https://github.com/pndurette/gTTS) | Online TTS + MP3 export | Optional |
| [`pygame`](https://www.pygame.org/) | MP3 playback for gTTS output | Optional |
| [`pydub`](https://github.com/jiaaro/pydub) | Audio format conversion / fallback playback | Optional |
| [`PyInstaller`](https://pyinstaller.org/) | Package app to standalone binary | Build only |

> Both editions detect missing optional packages at startup and disable the affected features gracefully — no crashes.

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
pip install -r requirements.txt

# 4. Launch

# Classic edition
python src/app_v1.py

# Premium edition (recommended)
python src/app_v2.py
```

---

## 🎯 Usage

### Speech → Text 🎙️

1. Select **Microphone** or **Audio File** as the input source
2. Click **⏺ Start Recording** — or press `Ctrl+R` (Premium)
3. Speak clearly; the app auto-calibrates for ambient noise before listening
4. Transcription appears in the editor once recognition completes
5. Save as `.txt`, `.md`, or `.log` — or copy to clipboard

> Audio file support: both editions accept WAV and MP3. Premium additionally accepts FLAC and OGG.

### Text → Speech 🔊

1. Type in the editor, load a `.txt` / `.md` / `.log` file, or select **From clipboard**
2. Use the **Quick-insert chips** for instant test phrases (available in both editions)
3. Click **▶ Speak Text** — or press `Ctrl+Enter` (Premium)
4. Export audio as `.wav` via pyttsx3 (offline) or `.mp3` via gTTS (online, internet required)

### ⌨️ Keyboard Shortcuts — Premium Edition Only

| Shortcut | Action |
|---|---|
| `Ctrl + Enter` | Speak text (TTS) |
| `Ctrl + R` | Start / stop recording |
| `Ctrl + S` | Save current output — transcript on STT tab, audio on TTS tab |
| `Ctrl + H` | Open history |
| `Ctrl + ,` | Open settings |
| `Escape` | Stop all operations |
| `F1` | Show keyboard shortcut help |

---

## ⚙️ Settings

Both editions open the Settings dialog via the **⚙ Settings** button (or `Ctrl+,` in Premium).

### TTS Tab

| Setting | Classic | Premium |
|---|---|---|
| Engine | pyttsx3 (offline) / gTTS (online) | pyttsx3 (offline) / gTTS (online) |
| Voice | System voices via pyttsx3 | System voices via pyttsx3 |
| Rate | 50–300 wpm slider | 50–400 wpm slider + live readout |
| Volume | 0.0–1.0 | 0.0–1.0 |
| gTTS Language | 14 (en, es, fr, de, it, pt, nl, ru, zh-cn, ja, ko, hi, ar, tr) | 18 (adds pl, sv, da + more) |

### STT Tab

| Setting | Classic | Premium |
|---|---|---|
| Microphone device | Dropdown from detected devices | Dropdown from detected devices |
| Energy threshold | 50–4000 | 50–4000 + live readout |
| Pause threshold | 0.3–3.0 s | 0.3–3.0 s |
| Listen timeout | 3–60 s | 3–120 s |
| Phrase time limit | 5–120 s | 5–180 s |

### General Tab

| Setting | Classic | Premium |
|---|---|---|
| Auto-save every transcription | ✅ | ✅ |
| Editor font size | 8–20 | 8–22 + live readout |
| History limit | — | 50–500 entries (step 50) |
| Startup tab | — | Speech→Text or Text→Speech |

All settings persist automatically to `~/VoiceStudio/.settings.json`.

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
# Classic edition
pyinstaller --onefile --noconsole --name "VoiceStudio" src/app_v1.py

# Premium edition (recommended)
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
└── VoiceStudio.exe      ← Windows portable executable
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
| `--hidden-import x` | Force-include a module PyInstaller's analysis misses |

### Required Hidden Imports

`pyttsx3` and `speech_recognition` drivers are frequently missed by PyInstaller's static analysis. Add the flags for your platform to avoid silent runtime failures:

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
├── .settings.json              # Saved user preferences (both editions)
├── voicestudio.log             # Structured application log (Premium only)
└── auto_YYYYMMDD_HHMMSS.txt    # Auto-saved transcriptions (when enabled)
```

> These runtime paths are excluded from version control via `.gitignore`.

### What `.gitignore` Excludes

- Python cache — `__pycache__/`, `*.py[cod]`, `*.pyo`, `*.pyd`, `*$py.class`, `.Python`
- Virtual environments — `venv/`, `.venv/`, `env/`, `ENV/`, `.env/`, `Lib/`, `Scripts/`
- Build output — `build/`, `dist/`, `*.spec`, `*.egg-info/`, `*.egg`, `MANIFEST`
- Runtime data — `VoiceStudio/`, `*.log`, `auto_*.txt`, `.settings.json`
- Audio files — `*.wav`, `*.mp3`, `*.flac`, `*.ogg`, `*.aac`, `*.m4a`
- OS & temp files — `.DS_Store`, `Thumbs.db`, `Desktop.ini`, `$RECYCLE.BIN/`, `*.lnk`, `*~`, `*.tmp`, `*.bak`, `*.swp`, `tempCodeRunnerFile.py`
- IDE files — `.vscode/`, `.idea/`, `*.sublime-project`, `*.sublime-workspace`, `*.suo`, `*.sln`, `.project`, `.settings/`

---

## 🔧 Troubleshooting

**Microphone not detected**
- Check OS microphone permissions — Privacy & Security on Windows/macOS, PulseAudio/ALSA on Linux
- Ensure the mic is not muted in system audio settings
- Try selecting a different device in Settings → STT → Device

**`PyAudio` install fails on Windows**
```bash
pip install pipwin
pipwin install pyaudio
```

**`PyAudio` install fails on Linux**
```bash
sudo apt install portaudio19-dev
pip install pyaudio
```

**Speech not recognised**
- Confirm an active internet connection — Google Speech API is required for all STT
- Raise the energy threshold in Settings → STT if background noise is high
- Speak clearly at normal pace, close to the microphone

**No sound from pyttsx3 on Linux**
```bash
sudo apt install espeak
```

**MP3 export fails**
- MP3 export requires both `gTTS` (encoding) and `pygame` (playback)
- Install: `pip install gTTS pygame`
- If gTTS is unavailable the app shows a clear error — switch to WAV as the fallback

**EXE crashes on launch**
- Run `python src/app_v2.py` directly first to read the full traceback in the terminal
- Add the platform-specific `--hidden-import` flags from the [Required Hidden Imports](#required-hidden-imports) section
- Confirm all dependencies are installed in the same Python environment used to build

**`run loop already started` / `engine already stopped` (pyttsx3)**
Both editions create a fresh `pyttsx3` engine instance per speak call to avoid this known upstream bug. It is handled internally and should never surface to the user.

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
