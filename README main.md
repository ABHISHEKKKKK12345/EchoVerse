<div align="center">

# 🎙️ Voice Studio

### Speech ↔ Text Converter · Desktop App · Cross-Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-FF6B35?style=flat-square)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-22d3a4?style=flat-square)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Abhishek%20Srivastava-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/abhishek-srivastava-1538461b1/)

*A production-grade, offline-capable speech-to-text and text-to-speech desktop application built entirely in Python.*

</div>

---

## ✨ Features

| Feature | Classic (`app_v1`) | Premium (`app_v2`) |
|---|:---:|:---:|
| Speech → Text (Microphone) | ✅ | ✅ |
| Speech → Text (Audio File) | ✅ | ✅ |
| Text → Speech — pyttsx3 (offline) | ✅ | ✅ |
| Text → Speech — gTTS (online) | ✅ | ✅ |
| Save transcript (.txt / .md / .log) | ✅ | ✅ |
| Export audio (.wav / .mp3) | ✅ | ✅ |
| Session history | ✅ | ✅ |
| Settings dialog (TTS/STT tuning) | ✅ | ✅ |
| Persistent settings (`.settings.json`) | ✅ | ✅ |
| Auto-save transcriptions | ✅ | ✅ |
| Blue-accented dark theme | ✅ | — |
| Deep cosmic dark theme (amber/teal) | — | ✅ |
| Animated shimmer progress bar | — | ✅ |
| Line-number editor | — | ✅ |
| Keyboard shortcuts | — | ✅ |
| Live recording timer | — | ✅ |
| In-app log viewer | — | ✅ |
| Structured file logging (`voicestudio.log`) | — | ✅ |
| History search / filter / export | — | ✅ |
| Quick-insert text chips | — | ✅ |
| Theme accent selector | — | ✅ |
| Configurable history limit | — | ✅ |

---

## 📦 Editions

### `app_v1.py` — Classic Edition
Clean, functional, and lightweight. Blue-accented dark UI (`#080b14` base) built with standard Tkinter widgets. All core STT/TTS features with a simple settings dialog and session history. Ideal for straightforward use or embedding in other projects.

### `app_v2.py` — Premium Edition ⭐ Recommended
Full production build featuring an amber/teal cosmic dark theme, animated shimmer indicators, structured file logging, keyboard shortcuts, a line-number editor, live recording timer, and an in-app log viewer. Settings include a configurable theme accent, history limit, mic device selector, and startup tab preference — all persisted automatically.

---

## 🖥️ Requirements

### System
- **Python** 3.9 or higher
- **Windows** 10/11 · **macOS** 12+ · **Linux** (Ubuntu 20.04+)
- Active **internet connection** for Google Speech Recognition and gTTS (offline pyttsx3 always works without it)

### Python Packages

```bash
pip install -r requirements.txt
```

| Package | Purpose | Required? |
|---|---|:---:|
| `SpeechRecognition` | Speech-to-text core (Google API) | ✅ Yes |
| `PyAudio` | Microphone access | ✅ Yes |
| `pyttsx3` | Offline TTS engine | ✅ Yes |
| `gTTS` | Online TTS + MP3 export | Optional |
| `pygame` | MP3 playback for gTTS output | Optional |
| `pydub` | Audio format conversion / fallback playback | Optional |

Both editions gracefully degrade — missing optional packages are detected at startup and the relevant features are disabled with a clear status indicator rather than crashing.

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

# 2. (Recommended) Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run

# Classic edition
python app_v1.py

# Premium edition (recommended)
python app_v2.py
```

---

## 🎯 Usage

### Speech → Text (STT) 🎙️

1. Select **Microphone** or **Audio File** as input source
2. Click **⏺ Start Recording** (or `Ctrl+R` in Premium)
3. Speak clearly — the app calibrates ambient noise automatically
4. Transcription appears in the editor when done
5. Save as `.txt`, `.md`, or `.log`, or copy to clipboard

### Text → Speech (TTS) 🔊

1. Type directly in the editor, load a `.txt` file, or paste from clipboard
2. Use **Quick-insert chips** for fast test phrases (Premium only)
3. Click **▶ Speak Text** (or `Ctrl+Enter` in Premium) to hear it
4. Export audio as `.wav` (offline via pyttsx3) or `.mp3` (online via gTTS)

### ⌨️ Keyboard Shortcuts — Premium Edition Only

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Speak text (TTS) |
| `Ctrl+R` | Start / stop recording |
| `Ctrl+S` | Save current output |
| `Ctrl+H` | Open history |
| `Ctrl+,` | Open settings |
| `Escape` | Stop all operations |
| `F1` | Show shortcut help |

### ⚙️ Settings

Both editions include a full **Settings dialog** with three tabs:

- **TTS** — engine (pyttsx3 / gTTS), voice, rate, volume, language
- **STT** — microphone device, energy threshold, pause/timeout/phrase limits
- **General** — auto-save, font size, history limit, startup tab (Premium), theme accent (Premium)

All settings are persisted automatically to `~/VoiceStudio/.settings.json`.

---

## 📁 Project Structure

```
voice-studio/
│
├── app_v1.py              # Classic Edition (v1.0)
├── app_v2.py              # Premium Edition (v2.0) — recommended
├── requirements.txt       # Python dependencies
├── .gitignore
├── LICENSE                # MIT License
└── README.md
```

### Auto-generated at Runtime

```
~/VoiceStudio/
├── .settings.json              # Saved user preferences
├── voicestudio.log             # Structured application log (Premium only)
└── auto_YYYYMMDD_HHMMSS.txt    # Auto-saved transcriptions (when enabled)
```

---

## 🏗️ Build to Executable

Convert either script to a standalone `.exe` (Windows) or binary (macOS/Linux) using **PyInstaller**.

### Install PyInstaller

```bash
pip install pyinstaller
```

### Windows

```bash
# Classic edition
pyinstaller --onefile --noconsole --name "VoiceStudio" app_v1.py

# Premium edition (recommended)
pyinstaller --onefile --noconsole --name "VoiceStudio" app_v2.py
```

### With a Custom Icon (optional)

Prepare a `.ico` file (Windows) or `.icns` (macOS), then:

```bash
pyinstaller --onefile --noconsole --icon=assets/icon.ico --name "VoiceStudio" app_v2.py
```

### macOS

```bash
pyinstaller --onefile --noconsole --name "VoiceStudio" app_v2.py
```

### Linux

```bash
pyinstaller --onefile --name "VoiceStudio" app_v2.py
```

### Output

```
dist/
└── VoiceStudio.exe      ← portable executable (Windows)
└── VoiceStudio          ← binary (macOS/Linux)
```

> **Tip:** `--onefile` bundles everything into a single binary. Remove it to get a faster-starting `dist/VoiceStudio/` folder distribution instead.

### Build Flags Reference

| Flag | Effect |
|---|---|
| `--onefile` | Bundle into a single executable |
| `--noconsole` | No terminal window on launch |
| `--icon=path.ico` | Custom app icon |
| `--name "AppName"` | Output file name |
| `--add-data "src;src"` | Include extra data files |
| `--hidden-import x` | Force-include a module PyInstaller misses |

### Required Hidden Imports

pyttsx3 and speech_recognition drivers are often missed by PyInstaller's auto-analysis. Add these flags to avoid runtime crashes:

```bash
# Windows
pyinstaller --onefile --noconsole \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.sapi5 \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" app_v2.py

# macOS
pyinstaller --onefile --noconsole \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.nsss \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" app_v2.py

# Linux
pyinstaller --onefile \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.espeak \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" app_v2.py
```

---

## 🔧 Troubleshooting

**Microphone not detected**
- Check OS microphone permissions (Privacy settings on Windows/macOS)
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
- Ensure you have an active internet connection (Google Speech API is required for STT)
- Increase the energy threshold in Settings → STT if background noise is high
- Speak clearly and closer to the microphone

**pyttsx3 no sound on Linux**
```bash
sudo apt install espeak
```

**EXE crashes on launch**
- Run the script directly first (`python app_v2.py`) to see the full error in the terminal
- Add the appropriate `--hidden-import` flags listed above
- Ensure all dependencies are installed in the same environment used to build

**`run loop already started` / `engine already stopped` (pyttsx3)**
Both editions create a fresh pyttsx3 engine for each speak call to avoid this — it is handled internally and should not surface to the user.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

Third-party packages used: SpeechRecognition (BSD), PyAudio (MIT), pyttsx3 (BSD-2), gTTS (MIT), pygame (LGPL-2.1), pydub (MIT), PyInstaller (GPL-2 + bootloader exception). Speech recognition is powered by the Google Speech Recognition API — internet use is subject to Google's Terms of Service.

---

## 👤 Author

<div align="center">

**Abhishek Srivastava**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/abhishek-srivastava-1538461b1/)

*Built with Python, Tkinter, and a lot of ☕*

*If you found this useful, consider leaving a ⭐ on the repository!*

</div>
