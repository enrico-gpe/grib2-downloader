# GFS & ICON-EU GRIB2 Subregion Downloader
## (Interactive Map & Visualizer Edition) 🌍🌦️

Weather GRIB2 Downloader v3.0 is a Python-based GUI application designed to simplify downloading and visualizing subsetted **GFS** (0.25°) and **ICON-EU** meteorological data in **GRIB2** format directly from NOAA NOMADS and DWD OpenData servers[cite: 1, 2].

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Format](https://img.shields.io/badge/Data-GRIB2-orange.svg)](https://www.wmo.int/)
[![GrADS](https://img.shields.io/badge/GrADS-Compatible-green.svg)](http://cola.gmu.edu/grads/)
[![XyGrib](https://img.shields.io/badge/XyGrib-Supported-brightgreen.svg)](https://opengribs.org/)

---

## 🌟 Key Features

* **Interactive Map Selector:** Define your geographic bounding box (N/S/W/E) visually using a 2-click interface powered by OpenStreetMap[cite: 1, 2].
* **Strict Variable & Level Mapping:** Direct coupling of meteorological variables to specific vertical levels to prevent HTTP 404 server errors on NOAA NOMADS[cite: 2].
* **Multi-Model Support:**
  * **GFS (NOAA)**: Custom subsetting by bounding box, time step ranges, and target variables (2m/850hPa Temp, 0°C Isotherm, 500hPa Geopotential Height, 10m Wind & Gusts, CAPE, CIN, Total Precipitation, Cloud Cover)[cite: 1, 2].
  * **ICON-EU (DWD)**: Automated download and `.bz2` decompression of single-level parameters directly from DWD OpenData[cite: 1, 2].
* **Flexible Time Horizon:** Seamlessly merges past analysis runs and future forecast steps into a single unified file[cite: 2].
* **Automated GrADS Integration:** Dynamic generation of `startup.gs` control scripts with automatic `g2ctl` and `gribmap` indexing.
* **XyGrib Integration:** One-click launch via `/usr/bin/XyGrib` for smooth spatial navigation of downloaded fields.
* **Auto File Detection:** Automatically detects previously downloaded `.grb2` files in the working directory on startup, enabling visualizer buttons instantly.
* **Multi-threaded Architecture:** Keeps the graphical user interface smooth and responsive during active downloads[cite: 2].

---

## 🚀 What's New in Version 3.0

* **Modular Refactoring:** Clean project architecture organized into reusable Python packages inside the `src/` directory.
* **Automated GrADS Pipeline**:
  * Synchronous execution of startup commands (`open`, `query file`, `set gxout shaded`, `set mpdset hires`) via `startup.gs`.
  * Reactive rendering optimized for single-timestep defaults ($t=1$) for maximum performance.
* **XyGrib Support:** Dynamic binary path detection and launch capabilities.
* **Existing File Detection:** Startup scan enables visualization buttons if a `.grb2` dataset is already present in the destination path.

---

## 🛠️ System Requirements & Dependencies

### 1. System Dependencies (Linux / Ubuntu)
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


## 📊 Data Visualization Workflow

Once your download completes (e.g., custom_weather.grb2), you can explore the data using either option:
## Option A: Via GUI (Recommended)

Use the built-in action buttons directly in the application:

    📊 VISUALIZZA IN GRADS: Automatically runs g2ctl and gribmap, creates startup.gs, and opens the session.

    🌍 APRI IN XYGRIB: Launches XyGrib and opens the .grb2 file immediately.

## Option B: Manual Command Line (GrADS)

### 1. Generate control file (.ctl)
g2ctl custom_weather.grb2 > custom_weather.ctl

### 2. Build GRIB map index file (.idx)
gribmap -v -i custom_weather.ctl 0

### 3. Launch GrADS session
grads -l
ga-> open custom_weather.ctl
ga-> q file
ga-> set gxout shaded
ga-> d hgt500mb

## Note: 

GrADS functionality is guaranteed when downloaded from OpenGrADS or compiled with native GRIB2 support; in some Ubuntu package versions, gribmap may fail to index GRIB2 files properly.


### 📄 License

Distributed under the GNU General Public License v3.0 (GNU GPLv3). See the LICENSE file for details
