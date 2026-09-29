# download_gfs.py
# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import urllib.request
from datetime import datetime, timedelta, timezone

# Importazione dei due sottomoduli dedicati
from .gfs_atmos import GFS_ATMOS_VARS, fetch_gfs_atmos
from .gfs_wave import GFS_WAVE_VARS, fetch_gfs_wave


class GfsDownloader:

    @staticmethod
    def _check_run_availability(run_dt):
        # Verifica veloce se il run scelto è pronto su NOAA
        test_file = f"gfs.t{run_dt.hour:02d}z.pgrb2.0p25.f000"
        url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file={test_file}&dir=%2Fgfs.{run_dt.strftime('%Y%m%d')}%2F{run_dt.hour:02d}%2Fatmos"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return len(resp.read()) > 500
        except Exception:
            return False

    @classmethod
    def download_and_merge(
        cls,
        north,
        south,
        west,
        east,
        start_h,
        end_h,
        step_h,
        selected_atmos_vars,
        selected_wave_vars,
        output_filepath=None,
        progress_callback=None,
        status_callback=None,
    ):
        steps = list(range(start_h, end_h + 1, step_h))

        # 1. Determinazione run UTC (00, 06, 12, 18)
        now = datetime.now(timezone.utc)
        run_dt = now.replace(minute=0, second=0, microsecond=0)
        run_dt = run_dt - timedelta(hours=run_dt.hour % 6)

        # Fallback a -6h se il run corrente non è ancora presente
        if not cls._check_run_availability(run_dt):
            run_dt -= timedelta(hours=6)

        all_buffers = []

        # 2. Scarico componenti Atmosferiche (se selezionate)
        if selected_atmos_vars:
            atmos_bufs = fetch_gfs_atmos(
                run_dt,
                steps,
                north,
                south,
                west,
                east,
                selected_atmos_vars,
                progress_callback,
                status_callback,
            )
            all_buffers.extend(atmos_bufs)

        # 3. Scarico componenti Onde WW3 (se selezionate)
        if selected_wave_vars:
            wave_bufs = fetch_gfs_wave(
                run_dt,
                steps,
                north,
                south,
                west,
                east,
                selected_wave_vars,
                progress_callback,
                status_callback,
            )
            all_buffers.extend(wave_bufs)

        # 4. Unione / Merge su file fisico (se specificato il percorso)
        if output_filepath and all_buffers:
            if status_callback:
                status_callback("Scrittura e merge file GRIB2 in corso...")
            with open(output_filepath, "wb") as f:
                for chunk in all_buffers:
                    f.write(chunk)

        return all_buffers
