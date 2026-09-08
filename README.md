# TYMusicV2

Windows music player companion for ESP32.

TYMusicV2 reads the currently playing music from Windows and sends music information and synchronized lyrics to an ESP32 over Bluetooth Classic.

## Features

* Spotify playback detection
* YouTube / YouTube Music support
* Current song title and artist
* Album artwork
* Playback progress
* Synchronized lyrics
* ESP32 Bluetooth connection
* Automatic Bluetooth reconnect
* OLED display support
* Windows installer

## Requirements

* Windows 10 / 11
* ESP32 WROOM-32
* OLED I2C 128×64
* Bluetooth enabled on the computer
* Python 3.14+ (only required when running from source)

## Installation

### Recommended: Installer

Download:

`TYMusicV2-Setup.exe`

Run the installer and follow the installation steps.

After installation, launch **TYMusicV2**.

### From source

Clone the repository:

```bash
git clone https://github.com/pitchakornofficial-prog/YTMusicV2.git
cd YTMusicV2
```

Create a virtual environment:

```bash
py -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
py -m pip install -r requirements.txt
```

Run:

```bash
py main.py
```

## ESP32 Setup

### 1. Upload the firmware

Open the ESP32 firmware:

```text
sketch_sep7a/
```

Open the `.ino` file with Arduino IDE and upload it to the ESP32.

### 2. Connect the OLED

| OLED | ESP32   |
| ---- | ------- |
| VCC  | 3.3V    |
| GND  | GND     |
| SDA  | GPIO 21 |
| SCL  | GPIO 22 |

OLED I2C address:

```text
0x3C
```

### 3. Bluetooth

The ESP32 Bluetooth device name is:

```text
TYMusicV2
```

Turn on Bluetooth on Windows and pair the computer with the ESP32.

## Usage

1. Turn on the ESP32.
2. Connect the OLED.
3. Pair **TYMusicV2** with Windows Bluetooth.
4. Start **TYMusicV2**.
5. Start playing music on Spotify, YouTube, or YouTube Music.
6. The music information and lyrics will be sent to the ESP32.
7. The ESP32 displays the information on the OLED.

The application automatically attempts to reconnect if the Bluetooth connection is lost.

## Project Structure

```text
YTMusicV2/
├── core/
│   ├── bluetooth.py
│   ├── music.py
│   ├── lyrics.py
│   └── sources/
├── sketch_sep7a/
│   └── ESP32 firmware
├── tests/
├── ui/
├── .gitignore
├── TYMusicV2.iss
├── config.py
├── main.py
├── requirements.txt
└── README.md
```

## Build

Build the Windows executable with PyInstaller:

```bash
pyinstaller --name TYMusicV2 --onefile --windowed main.py
```

The executable will be created in:

```text
dist/TYMusicV2.exe
```

Build the installer with Inno Setup:

```cmd
"C:\Users\<username>\AppData\Local\Programs\Inno Setup 7\ISCC.exe" TYMusicV2.iss
```

The installer will be created in:

```text
installer/TYMusicV2-Setup.exe
```

## Tests

Run the test suite with:

```bash
py -m unittest discover -s tests
```

## License

This project is provided for personal and educational use.
