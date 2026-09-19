# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

from datetime import datetime, timedelta, timezone
import urllib.request

GFS_VARS = {
    "Zero Isotherm Height (HGT 0C)": "&var_HGT=on&lev_0C_isotherm=on",
    "2m Temperature (TMP 2m)": "&var_TMP=on&lev_2_m_above_ground=on",
    "850 hPa Temp (TMP 850mb)": "&var_TMP=on&lev_850_mb=on",
    "500 hPa Height (HGT 500mb)": "&var_HGT=on&lev_500_mb=on",
    "Total Precip (APCP sfc)": "&var_APCP=on&lev_surface=on",
    "Relative Humidity 2m (RH 2m)": "&var_RH=on&lev_2_m_above_ground=on",
    "Total Cloud Cover (TCDC)": "&var_TCDC=on&lev_entire_atmosphere=on",
    "CAPE (Surface)": "&var_CAPE=on&lev_surface=on",
    "CIN (Surface)": "&var_CIN=on&lev_surface=on",
    "10m Wind Vector (UGRD/VGRD)": (
        "&var_UGRD=on&var_VGRD=on&lev_10_m_above_ground=on"
    ),
    "Surface Wind Gust (GUST)": "&var_GUST=on&lev_surface=on",
}


class GfsDownloader:

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
        run_dt = now.replace(minute=0, second=0, microsecond=0)
        run_dt = run_dt - timedelta(hours=run_dt.hour % 6)

        var_query = "".join([GFS_VARS[v] for v in selected_vars if v in GFS_VARS])

        filename_test = f"gfs.t{run_dt.hour:02d}z.pgrb2.0p25.f000"
        test_url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file={filename_test}&dir=%2Fgfs.{run_dt.strftime('%Y%m%d')}%2F{run_dt.hour:02d}%2Fatmos"

        if not cls._fetch_url(test_url):
            run_dt -= timedelta(hours=6)

        downloaded_buffers = []
        for idx, h in enumerate(steps):
            c_date, c_run, c_fstep = cls._get_time_params(run_dt, h)
            filename = f"gfs.t{c_run}z.pgrb2.0p25.f{c_fstep}"
            url = (
                f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
                f"file={filename}{var_query}"
                f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
                f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fatmos"
            )

            if status_callback:
                status_callback(f"GFS Download {h}h ({idx+1}/{len(steps)})...")

            data = cls._fetch_url(url)
            if data:
                downloaded_buffers.append(data)

            if progress_callback:
                progress_callback(idx + 1, len(steps))

        return downloaded_buffers