# gfs_atmos.py
# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import urllib.request
from datetime import datetime, timedelta, timezone

GFS_ATMOS_VARS = {
    # --- Geopotenziale ---
    "Zero Isotherm Height (HGT 0C)": "&var_HGT=on&lev_0C_isotherm=on",
    "500 hPa Height (HGT 500mb)": "&var_HGT=on&lev_500_mb=on",
    "850 hPa Height (HGT 850mb)": "&var_HGT=on&lev_850_mb=on",

    # --- Temperature ---
    "Surface Temp (TMP sfc)": "&var_TMP=on&lev_surface=on",
    "2m Temperature (TMP 2m)": "&var_TMP=on&lev_2_m_above_ground=on",
    "850 hPa Temp (TMP 850mb)": "&var_TMP=on&lev_850_mb=on",
    "500 hPa Temp (TMP 500mb)": "&var_TMP=on&lev_500_mb=on",

    # --- Pressione e Precipitazioni ---
    "Pressione MSL": "&var_PRMSL=on&lev_mean_sea_level=on",
    "Total Precip (APCP sfc)": "&var_APCP=on&lev_surface=on",

    # --- Umidità Relativa ---
    "Relative Humidity 2m (RH 2m)": "&var_RH=on&lev_2_m_above_ground=on",
    "Relative Humidity 850hPa (RH 850mb)": "&var_RH=on&lev_850_mb=on",
    "Relative Humidity 500hPa (RH 500mb)": "&var_RH=on&lev_500_mb=on",
    "Relative Humidity 0C (RH 0C)": "&var_RH=on&lev_0C_isotherm=on",

    # --- Nuvolosità e Instabilità ---
    "Total Cloud Cover (TCDC)": "&var_TCDC=on&lev_entire_atmosphere=on",
    "CAPE (Surface)": "&var_CAPE=on&lev_surface=on",
    "CIN (Surface)": "&var_CIN=on&lev_surface=on",

    # --- Vento e Raffiche ---
    "10m Wind Vector (UGRD/VGRD)": "&var_UGRD=on&var_VGRD=on&lev_10_m_above_ground=on",
    "850hPa Wind Vector (UGRD/VGRD)": "&var_UGRD=on&var_VGRD=on&lev_850_mb=on",
    "500hPa Wind Vector (UGRD/VGRD)": "&var_UGRD=on&var_VGRD=on&lev_500_mb=on",
    "Surface Wind Gust (GUST)": "&var_GUST=on&lev_surface=on",
}


def _fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            return data if len(data) > 500 else None
    except Exception:
        return None


def fetch_gfs_atmos(
    run_dt,
    steps,
    north,
    south,
    west,
    east,
    selected_vars,
    progress_callback=None,
    status_callback=None,
):
    var_query = "".join(
        [GFS_ATMOS_VARS[v] for v in selected_vars if v in GFS_ATMOS_VARS]
    )
    if not var_query:
        return []

    buffers = []
    total = len(steps)
    for idx, h in enumerate(steps):
        target_dt = run_dt + timedelta(hours=h)
        c_date = target_dt.strftime("%Y%m%d")
        c_run = f"{run_dt.hour:02d}"
        c_fstep = f"{h:03d}"

        filename = f"gfs.t{c_run}z.pgrb2.0p25.f{c_fstep}"
        url = (
            f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
            f"file={filename}{var_query}"
            f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
            f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fatmos"
        )

        if status_callback:
            status_callback(f"GFS Atmos {h}h ({idx+1}/{total})...")

        data = _fetch_url(url)
        if data:
            buffers.append(data)

        if progress_callback:
            progress_callback(idx + 1, total)

    return buffers