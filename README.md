# Weather GRIB2 Downloader v3.2.2
## Automated Subregion Extraction with GFS, WW3 & ICON-EU + Direct XyGrib / GrADS Integration 🌍📊

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Format](https://img.shields.io/badge/Data-GRIB2-orange.svg)](https://www.wmo.int/)
[![GrADS](https://img.shields.io/badge/GrADS-Compatible-green.svg)](http://cola.gmu.edu/grads/)
[![XyGrib](https://img.shields.io/badge/XyGrib-Supported-brightgreen.svg)](https://opengribs.org/)

Weather GRIB2 Downloader v3.2.2 is a powerful Python GUI application designed to extract subsetted **GFS** (0.25°), **GFS Wave**, and **ICON-EU** weather data in **GRIB2** format. It features an intuitive tabbed interface, persistent configuration management, and seamless one-click integration with **XyGrib** and **GrADS** for real-time visualization and spatial analysis.

---

## 🌟 Key Features

* **Interactive Map Selector:** Define your geographic bounding box (N/S/W/E) visually using a 2-click interface powered by OpenStreetMap.
* **Modular Multi-Model Support:**
  * **GFS (NOAA NOMADS)**: Multi-step atmospheric data (Surface & Isobaric pressure levels).
  * **WW3 (NOAA WaveWatch III)**: Dedicated oceanographic and marine wave model (Significant height, wind waves, and full swell partition).
  * **ICON-EU (DWD)**: Automated download and `.bz2` decompression of high-resolution European model data.
* **Dynamic GUI Tab Navigation:** Interface automatically adapts its notebook layout based on the active model (2 tabs for GFS, 1 tab for WW3, 1 tab for ICON-EU).
* **Tab-Scoped Selection Controls:** Quick selection controls (`Tutte (scheda)` / `Nessuna (scheda)`) act strictly within the currently open tab.
* **Unified GRIB2 Output:** Concatenates all hourly forecast steps into a single persistent `.grb2` file ready for instant visualization.
* **Automated GrADS Integration:** Dynamic generation of descriptor (`.ctl`) files using `g2ctl -0` for clean surface coordinate mapping ($Z=1$).
* **Cross-Platform XyGrib Integration:** One-click launch across Linux, macOS, and Windows.
* **Persistent Settings Management:** Automatically saves and restores user preferences, bounding boxes, and variable selections across restarts via JSON.
* **Multi-threaded Architecture:** Keeps the graphical interface smooth and responsive during active downloads.
---

## 📸 Application Screenshots

<p align="center">
  <b>1. Main Tabbed Interface & Interactive Map Selection</b><br>
  <img src="docs/gui_preview.jpg" alt="Interactive Map Selection" width="850"/>
</p>

<br>

<p align="center">
  <b>2. Real-Time Multi-threaded Download Progress</b><br>
  <img src="docs/download.jpg" alt="Download Progress" width="500"/>
</p>

<br>

<p align="center">
  <b>3. Direct One-Click Visualization in XyGrib and GrADS</b><br>
  <img src="docs/preview.jpg" alt="XyGrib and GrADS Visualization" width="900"/>
</p>

---

## 🚀 What's New in Version 3.2.2

### 🛠️ Bug Fixes & Code Cleanups
- **Direct CTL Loading**: Replaced temporary startup script (`startup.gs`) execution with direct `.ctl` file invocation in GrADS, avoiding console clutter and syntax issues.
- **Robust Multi-Step Indexing**: Aligned `gribmap` execution parameters (`gribmap -v -i file.ctl 0`) to resolve duplicate GRIB2 record conflicts from NOMADS (e.g., accumulated precipitation fields).
- **GUI & Handler Stability**: Fixed indentation bugs and scoping issues (`UnboundLocalError`) in `grads_handler.py`.
- **Console Aesthetics**: Neutralized terminal color override issues on OpenGrADS invocations.

### 🌐 Compatibility & Workflow
- Fully validated seamless 5-day continuous forecast indexing (`Tsize=41`).
- Preserved run fallback logic (`offset_hours`) for continuity during NOAA GFS update windows.

---

## 🛠️ System Requirements & Dependencies

### Linux (Ubuntu / Debian / Fedora)
Ensure Python 3, Tkinter, and external visualizers are installed on your system:

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk grads g2ctl xygrib

# Fedora / RHEL
sudo dnf install python3 python3-pip python3-tkinter grads xygrib

```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone [https://github.com/enrico-gpe/grib2-downloader.git](https://github.com/enrico-gpe/grib2-downloader.git)
cd grib2-downloader

```

### 2. Set Up Python Virtual Environment (venv)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

### 3. Run the Application

```bash
python3 main.py

```

---

## 📊 Data Visualization Workflow

Once your download completes (e.g., `custom_weather.grb2`), you can explore the data directly from the application's GUI:

* 📊 **VISUALIZZA IN GRADS:** Automatically runs `g2ctl` and `gribmap`, creates `startup.gs`, and opens the session.
* 🌍 **APRI IN XYGRIB:** Launches XyGrib and opens the `.grb2` file immediately.

> **Note:** GrADS functionality is guaranteed when downloaded from OpenGrADS or compiled with native GRIB2 support; in some Linux distribution packages, `gribmap` may fail to index GRIB2 files properly.

---

## 💡 Quick Launch Alias

To launch the downloader quickly from any terminal session, add the function to your shell configuration file:

* **Linux (Bash):** `~/.bashrc`
* **macOS (Zsh):** `~/.zshrc`

```bash
function xygrib-downloader() {
    cd ~/Programmi/gfs-icon-grads/gfs_downloader || return
    source venv/bin/activate
    python3 main.py
    deactivate
}

```

After editing, apply the changes with `source ~/.bashrc` (Linux) or `source ~/.zshrc` (macOS).

---

### 📄 License

Distributed under the GNU General Public License v3.0 (GNU GPLv3). See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

```

```