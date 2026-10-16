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

import bz2
from datetime import datetime, timedelta, timezone
import urllib.request

ICON_VARS = {
    "Pressione liv. mare (prmslmsl)": [("pmsl", "PMSL")],
    "Temperatura 2m (tmp2m)": [("t_2m", "T_2M")],
    "Copertura Nuvolosa (tcdcsfc)": [("clct", "CLCT")],
    "CAPE Suolo (capesfc)": [("cape_ml", "CAPE_ML")],
    "Tasso Precip. (tpratesfc)": [("tot_prec", "TOT_PREC")],
    "Vento 10m (ugrd10m/vgrd10m)": [("u_10m", "U_10M"), ("v_10m", "V_10M")],
    "Raffica Vento (gustsfc)": [("vmax_10m", "VMAX_10M")],
}


class IconEuDownloader:

    @staticmethod
    def _fetch_url(url):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                return data if data[:4] == b"GRIB" else None
        except Exception:
            return None

    @classmethod
    def find_latest_icon_run(cls):
        now = datetime.now(timezone.utc)
        for offset_hours in range(0, 36, 3):
            check_dt = now - timedelta(hours=offset_hours)
            run_hour = (check_dt.hour // 6) * 6
            run_dt = check_dt.replace(
                hour=run_hour, minute=0, second=0, microsecond=0
            )
            date_str = run_dt.strftime("%Y%m%d")
            run_str = f"{run_dt.hour:02d}"

            filename = f"icon-eu_europe_regular-lat-lon_single-level_{date_str}{run_str}_000_PMSL.grib2.bz2"
            test_url = f"https://opendata.dwd.de/weather/nwp/icon-eu/grib/{run_str}/pmsl/{filename}"

            if cls._fetch_url(test_url):
                return run_dt
        return None

    @classmethod
    def download_icon_eu(
        cls,
        selected_vars,
        progress_callback=None,
        status_callback=None,
    ):
        if status_callback:
            status_callback("Verifica run ICON-EU disponibile...")

        run_dt = cls.find_latest_icon_run()
        if not run_dt:
            return [], []

        date_str = run_dt.strftime("%Y%m%d")
        run_str = f"{run_dt.hour:02d}"
        valid_steps = list(range(0, 49, 3))

        downloaded_buffers = []
        missing_steps = []
        for idx, h in enumerate(valid_steps):
            if status_callback:
                status_callback(
                    f"ICON-EU (Run {run_str}Z) {h}h ({idx+1}/{len(valid_steps)})..."
                )

            step_buffer = bytearray()
            for var_name in selected_vars:
                if var_name in ICON_VARS:
                    for folder, var_code in ICON_VARS[var_name]:
                        filename = f"icon-eu_europe_regular-lat-lon_single-level_{date_str}{run_str}_{h:03d}_{var_code}.grib2.bz2"
                        url = f"https://opendata.dwd.de/weather/nwp/icon-eu/grib/{run_str}/{folder}/{filename}"

                        raw_bz2 = cls._fetch_url(url)
                        if raw_bz2:
                            step_buffer.extend(bz2.decompress(raw_bz2))

            if step_buffer:
                downloaded_buffers.append(bytes(step_buffer))
            else:
                missing_steps.append(h)

            if progress_callback:
                progress_callback(idx + 1, len(valid_steps))

        return downloaded_buffers, missing_steps