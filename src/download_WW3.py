# download_WW3.py
# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

from datetime import datetime, timedelta, timezone
import urllib.request

WW3_VARS = {
    # 1. Combined Wave (Mare Totale) - Livello: Surface
    "Significant Height of Combined Waves (HTSGW)": "&var_HTSGW=on&lev_surface=on",
    "Primary Wave Direction (DIRPW)": "&var_DIRPW=on&lev_surface=on",
    "Primary Wave Mean Period (PERPW)": "&var_PERPW=on&lev_surface=on",

    # 2. Primary Swell (Mare Lungo) - Livello: 1 in sequence
    "Primary Swell Wave Height (SWELL)": "&var_SWELL=on&lev_1_in_sequence=on",
    "Primary Swell Wave Direction (SWDIR)": "&var_SWDIR=on&lev_1_in_sequence=on",
    "Primary Swell Wave Period (SWPER)": "&var_SWPER=on&lev_1_in_sequence=on",

    # 3. Wind Wave (Mare Vivo / Vento) - Livello: Surface
    "Wind Wave Height (WVHGT)": "&var_WVHGT=on&lev_surface=on",
    "Wind Wave Direction (WVDIR)": "&var_WVDIR=on&lev_surface=on",
    "Wind Wave Period (WVPER)": "&var_WVPER=on&lev_surface=on",
}


class Ww3Downloader:

    @staticmethod
    def _fetch_url(url):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                return data if len(data) > 500 else None
        except Exception:
            return None

    @staticmethod
    def _get_time_params(base_dt, h):
        target_dt = base_dt + timedelta(hours=h)
        if h < 0:
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
        return base_dt.strftime("%Y%m%d"), f"{base_dt.hour:02d}", f"{h:03d}"

    @classmethod
    def download_ww3(
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
        run_dt = now.replace(minute=0, second=0, microsecond=0)
        run_dt = run_dt - timedelta(hours=run_dt.hour % 6)

        var_query = "".join([WW3_VARS[v] for v in selected_vars if v in WW3_VARS])
        if not var_query:
            return []

        filename_test = f"gfswave.t{run_dt.hour:02d}z.global.0p25.f000.grib2"
        test_url = (
            f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl?"
            f"file={filename_test}&dir=%2Fgfs.{run_dt.strftime('%Y%m%d')}%2F{run_dt.hour:02d}%2Fwave%2Fgridded"
        )

        if not cls._fetch_url(test_url):
            run_dt -= timedelta(hours=6)

        downloaded_buffers = []
        for idx, h in enumerate(steps):
            c_date, c_run, c_fstep = cls._get_time_params(run_dt, h)
            filename = f"gfswave.t{c_run}z.global.0p25.f{c_fstep}.grib2"
            url = (
                f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl?"
                f"file={filename}{var_query}"
                f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
                f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fwave%2Fgridded"
            )

            if status_callback:
                status_callback(f"WW3 Wave {h}h ({idx+1}/{len(steps)})...")

            data = cls._fetch_url(url)
            if data:
                downloaded_buffers.append(data)

            if progress_callback:
                progress_callback(idx + 1, len(steps))

        return downloaded_buffers
