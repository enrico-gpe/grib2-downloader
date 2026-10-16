# download_gfs.py
# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime, timedelta, timezone
import urllib.request
import time

GFS_VARS = {
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


class GfsDownloader:

    @staticmethod
    def _fetch_url(url, retries=3):
        """Effettua la richiesta HTTP con riassunzione in caso di failure temporanea."""
        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    if data[:4] == b"GRIB":
                        return data
            except Exception:
                time.sleep(1)
        return None

    @staticmethod
    def _get_time_params(base_dt, h, offset_hours=0):
        """Mappa lo step richiesto sul run e sul file fXXX corretto.

        Per le ore negative (ore passate) il file f-XXX non esiste: lo
        step viene mappato sul run precedente piu' vicino, con un
        forecast step ridotto (0-5h) che mantiene la stessa validita'
        temporale assoluta."""
        if h < 0:
            target_dt = base_dt + timedelta(hours=h)
            target_run_hour = (target_dt.hour // 6) * 6
            run_base = target_dt.replace(
                hour=target_run_hour, minute=0, second=0, microsecond=0
            )
            f_hour = int((target_dt - run_base).total_seconds() // 3600)
            return (
                run_base.strftime("%Y%m%d"),
                f"{run_base.hour:02d}",
                f"{f_hour:03d}",
            )
        return (
            base_dt.strftime("%Y%m%d"),
            f"{base_dt.hour:02d}",
            f"{h + offset_hours:03d}",
        )

    @classmethod
    def download_gfs(
        cls,
        north,
        south,
        west,
        east,
        start_h,
        end_h,
        step_h,
        selected_vars,
        progress_callback=None,
        status_callback=None,
    ):
        steps = list(range(start_h, end_h + 1, step_h))
        now = datetime.now(timezone.utc)

        # Determina il ciclo più recente (00, 06, 12, 18 UTC)
        run_dt = now.replace(minute=0, second=0, microsecond=0)
        run_dt = run_dt - timedelta(hours=run_dt.hour % 6)

        var_query = "".join([GFS_VARS[v] for v in selected_vars if v in GFS_VARS])
        if not var_query:
            return [], []

        # Verifica disponibilità run nominale; in caso contrario retrocede di 6h
        test_filename = f"gfs.t{run_dt.hour:02d}z.pgrb2.0p25.f000"
        test_url = (
            f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
            f"file={test_filename}&dir=%2Fgfs.{run_dt.strftime('%Y%m%d')}%2F{run_dt.hour:02d}%2Fatmos"
        )

        offset_hours = 0
        if not cls._fetch_url(test_url, retries=1):
            run_dt -= timedelta(hours=6)
            offset_hours = 6  # Shift del forecast step per compensare il run precedente

        downloaded_buffers = []
        missing_steps = []
        for idx, h in enumerate(steps):
            c_date, c_run, c_fstep = cls._get_time_params(run_dt, h, offset_hours)

            filename = f"gfs.t{c_run}z.pgrb2.0p25.f{c_fstep}"
            url = (
                f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
                f"file={filename}{var_query}"
                f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
                f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fatmos"
            )

            if status_callback:
                status_callback(f"GFS Atmos +{h}h (f{c_fstep}) [{idx+1}/{len(steps)}]...")

            data = cls._fetch_url(url)
            if data:
                downloaded_buffers.append(data)
            else:
                missing_steps.append(h)

            if progress_callback:
                progress_callback(idx + 1, len(steps))

        return downloaded_buffers, missing_steps
