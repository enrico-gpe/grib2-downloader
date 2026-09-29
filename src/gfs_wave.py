# gfs_wave.py
# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import urllib.request
from datetime import datetime, timedelta, timezone

GFS_WAVE_VARS = {
    "Significant Height of Combined Waves (HTSGW)": "&var_HTSGW=on&lev_surface=on",
    "Primary Wave Direction (DIRPW)": "&var_DIRPW=on&lev_surface=on",
    "Primary Wave Mean Period (PERPW)": "&var_PERPW=on&lev_surface=on",
    "Primary Swell Wave Height (SWELL)": "&var_SWELL=on&lev_surface=on",
    "Primary Swell Wave Direction (SWDIR)": "&var_SWDIR=on&lev_surface=on",
    "Primary Swell Wave Period (SWPER)": "&var_SWPER=on&lev_surface=on",
    "Wind Wave Height (WVHGT)": "&var_WVHGT=on&lev_surface=on",
    "Wind Wave Direction (WVDIR)": "&var_WVDIR=on&lev_surface=on",
    "Wind Wave Period (WVPER)": "&var_WVPER=on&lev_surface=on",
}


def _fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            return data if len(data) > 500 else None
    except Exception:
        return None


def fetch_gfs_wave(
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
        [GFS_WAVE_VARS[v] for v in selected_vars if v in GFS_WAVE_VARS]
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

        filename = f"gfswave.t{c_run}z.global.0p25.f{c_fstep}.grib2"
        url = (
            f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl?"
            f"file={filename}{var_query}"
            f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
            f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fwave%2Fgridded"
        )

        if status_callback:
            status_callback(f"WW3 Wave {h}h ({idx+1}/{total})...")

        data = _fetch_url(url)
        if data:
            buffers.append(data)

        if progress_callback:
            progress_callback(idx + 1, total)

    return buffers