<div align="center">

# 🎙️ Voice Studio

### Speech ↔ Text Converter · Premium Desktop App · Cross-Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-FF6B35?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-22d3a4?style=for-the-badge)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Abhishek%20Srivastava-0A66C2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/abhishek-srivastava-1538461b1/)

*A production-grade, offline-capable speech-to-text and text-to-speech desktop application built entirely in Python.*

---

[Features](#-features) · [Versions](#-versions) · [Installation](#-installation) · [Usage](#-usage) · [Build to EXE](#-build-to-exe) · [Project Structure](#-project-structure) · [Author](#-author)

</div>

---

## ✨ Features

| Feature | v1 (Classic) | v2 (Premium) |
|---|:---:|:---:|
| Speech → Text (Microphone) | ✅ | ✅ |
| Speech → Text (Audio File) | ✅ | ✅ |
| Text → Speech (pyttsx3 offline) | ✅ | ✅ |
| Text → Speech (gTTS online) | ✅ | ✅ |
| Save transcript (.txt / .md / .log) | ✅ | ✅ |
| Export audio (.wav / .mp3) | ✅ | ✅ |
| Session history | ✅ | ✅ |
| Settings dialog (TTS/STT tuning) | ✅ | ✅ |
| Persistent settings | ✅ | ✅ |
| Auto-save transcriptions | ✅ | ✅ |
| Deep cosmic dark theme | — | ✅ |
| Animated shimmer progress bar | — | ✅ |
| Line-number editor | — | ✅ |
| Keyboard shortcuts | — | ✅ |
| Live recording timer | — | ✅ |
| In-app log viewer | — | ✅ |
| Structured file logging | — | ✅ |
| History search / filter / export | — | ✅ |
| Quick-insert text chips | — | ✅ |

---

## 📦 Versions

### `src/app_v1.py` — Classic Edition
> Clean, functional, and lightweight. Blue-accented dark UI built with standard Tkinter widgets. Ideal for straightforward use or embedding in other projects.

### `src/app_v2.py` — Premium Edition ⭐ Recommended
> Full production build with an amber/teal cosmic dark theme, animated indicators, structured logging, keyboard shortcuts, a line-number editor, live timers, and an in-app log viewer. Everything v1 does — and significantly more.

---

## 🖥️ Requirements

### System
- **Python** 3.9 or higher
- **Windows** 10/11 · **macOS** 12+ · **Linux** (Ubuntu 20.04+)
- Active **internet connection** for Google Speech recognition and gTTS (offline pyttsx3 always works)

### Python Packages

```bash
pip install SpeechRecognition pyttsx3 gTTS pyaudio pydub pygame
```

| Package | Purpose | Required? |
|---|---|:---:|
| `SpeechRecognition` | Speech-to-text core | ✅ Yes |
| `pyaudio` | Microphone access | ✅ Yes |
| `pyttsx3` | Offline TTS engine | ✅ Yes |
| `gTTS` | Online TTS + MP3 export | Optional |
| `pydub` | Audio format conversion | Optional |
| `pygame` | MP3 playback (gTTS) | Optional |

### Linux Extras

```bash
sudo apt install portaudio19-dev python3-tk espeak
```

### macOS Extras

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

# 4. Run the app
#    Classic version:
python src/app_v1.py

#    Premium version (recommended):
python src/app_v2.py
```

---

## 🎯 Usage

### Speech → Text Tab 🎙️

1. Select **Microphone** or **Audio File** as input source
2. Click **⏺ Start Recording** (or `Ctrl + R`)
3. Speak clearly — the app calibrates ambient noise automatically
4. Transcription appears in the editor when done
5. Save as `.txt`, `.md`, or `.log` — or copy to clipboard

### Text → Speech Tab 🔊

1. Type directly in the editor, load a `.txt` file, or paste from clipboard
2. Use **Quick-insert chips** for fast test phrases
3. Click **▶ Speak Text** (or `Ctrl + Enter`) to hear it
4. Save the audio as `.wav` (offline) or `.mp3` (online via gTTS)

### ⌨️ Keyboard Shortcuts (v2 only)

| Shortcut | Action |
|---|---|
| `Ctrl + Enter` | Speak text (TTS) |
| `Ctrl + R` | Start / stop recording |
| `Ctrl + S` | Save current output |
| `Ctrl + H` | Open history |
| `Ctrl + ,` | Open settings |
| `Escape` | Stop all operations |
| `F1` | Show shortcut help |

### ⚙️ Settings

Both versions include a full **Settings dialog** with:
- **TTS tab** — engine selection (pyttsx3 / gTTS), voice, rate, volume, language
- **STT tab** — microphone device, energy threshold, pause/timeout/phrase limits
- **General tab** — auto-save, font size, history limit, startup tab

All settings are saved automatically to `~/VoiceStudio/.settings.json`.

---

## 🏗️ Build to EXE

Convert either script to a standalone `.exe` (Windows) or binary (macOS/Linux) using **PyInstaller**.

### Step 1 — Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2 — Build (Windows)

```bash
# Classic version — single file, no console window
pyinstaller --onefile --noconsole --name "VoiceStudio" src/app_v1.py

# Premium version — single file, no console window
pyinstaller --onefile --noconsole --name "VoiceStudio" src/app_v2.py
```

### Step 3 — Build with Custom Icon (optional)

```bash
# Prepare a .ico file (Windows) or .icns (macOS)
pyinstaller --onefile --noconsole --icon=assets/icon.ico --name "VoiceStudio" src/app_v2.py
```

### Step 4 — Find the Output

```
dist/
└── VoiceStudio.exe      ← your portable executable
```

> **Tip:** The `--onefile` flag bundles everything into a single binary. Remove it if you prefer a faster-starting `dist/VoiceStudio/` folder distribution.

### Build Flags Reference

| Flag | Effect |
|---|---|
| `--onefile` | Bundle into a single `.exe` |
| `--noconsole` | No terminal window on launch |
| `--icon=path.ico` | Custom app icon |
| `--name "AppName"` | Output file name |
| `--add-data "src;src"` | Include extra data files |
| `--hidden-import x` | Force-include a module PyInstaller misses |

### Common Hidden Imports for This App

If PyInstaller misses modules at runtime, add:

```bash
pyinstaller --onefile --noconsole \
  --hidden-import=pyttsx3.drivers \
  --hidden-import=pyttsx3.drivers.sapi5 \
  --hidden-import=speech_recognition \
  --name "VoiceStudio" src/app_v2.py
```

### macOS / Linux Build

```bash
# macOS — produces a .app bundle
pyinstaller --onefile --noconsole --name "VoiceStudio" src/app_v2.py

# Linux — produces a standalone binary
pyinstaller --onefile --name "VoiceStudio" src/app_v2.py
```

---

## 📁 Project Structure

```
voice-studio/
│
├── src/
│   ├── app_v1.py              # Classic Edition
│   └── app_v2.py              # Premium Edition (recommended)
│
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── LICENSE                    # MIT License
└── README.md                  # This file
```

### Auto-generated at Runtime

```
~/VoiceStudio/
├── .settings.json             # Saved user preferences
├── voicestudio.log            # Application log (v2 only)
└── auto_YYYYMMDD_HHMMSS.txt   # Auto-saved transcriptions
```

---

## 📋 `requirements.txt`

```
SpeechRecognition>=3.10.0
pyttsx3>=2.90
gTTS>=2.5.0
PyAudio>=0.2.14
pydub>=0.25.1
pygame>=2.5.0
pyinstaller>=6.0.0
```

---

## 🔧 Troubleshooting

**Microphone not detected**
- Check OS microphone permissions (Privacy settings on Windows/macOS)
- Ensure mic is not muted in system audio settings
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
- Ensure you have an active internet connection (Google Speech API)
- Increase energy threshold in Settings if background noise is high
- Speak clearly and closer to the microphone

**pyttsx3 no sound on Linux**
```bash
sudo apt install espeak
```

**EXE crashes on launch**
- Run from terminal first to see the error output
- Add `--hidden-import` flags for any missing modules
- Ensure all dependencies are installed in the same environment used to build

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

<div align="center">

**Abhishek Srivastava**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/abhishek-srivastava-1538461b1/)

*Built with Python, Tkinter, and a lot of ☕*

---

*If you found this useful, consider leaving a ⭐ on the repository!*

</div>
