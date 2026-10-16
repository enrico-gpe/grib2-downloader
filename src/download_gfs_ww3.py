# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3

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


# src/download_gfs_ww3.py
# ----------------------------------------------------------------------
# Modulo di download combinato GFS + WW3 per XyGrib / GrADS
# Con controlli di validità dei buffer e feedback in tempo reale.
# ----------------------------------------------------------------------

from .download_gfs import GfsDownloader, GFS_VARS
from .download_WW3 import Ww3Downloader, WW3_VARS

class GfsWw3Downloader:

    @classmethod
    def download_gfs_ww3(
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
        """
        Scarica i dati GFS e WW3 separatamente, valida i buffer binari
        e li concatena garantendo la coerenza dei flussi per XyGrib e GrADS.
        """
        if status_callback:
            status_callback("🚀 Avvio download combinato: GFS (Atmosfera) + WW3 (Onde)...")

        gfs_vars_sel = [v for v in selected_vars if v in GFS_VARS]
        ww3_vars_sel = [v for v in selected_vars if v in WW3_VARS]

        all_buffers = []
        missing_steps_total = []

        # Wrapper locale per monitorare il download in tempo reale e filtrare i dati corrotti
        def monitored_fetch(downloader_class, vars_list, label):
            buffers = []
            missing = []
            
            # Se il downloader sottostante supporta un ciclo personalizzato o restituisce già una lista di buffer:
            # Qui eseguiamo il download standard richiamando il metodo esistente, ma intercettiamo l'esito.
            raw_buffers, raw_missing = downloader_class.download_gfs( # o download_ww3 a seconda del chiamante
                north, south, west, east, start_h, end_h, step_h,
                vars_list, progress_callback, status_callback
            ) if label == "GFS" else downloader_class.download_ww3(
                north, south, west, east, start_h, end_h, step_h,
                vars_list, progress_callback, status_callback
            )

            # Validazione chirurgica dei singoli blocchi binari ricevuti
            for idx, buf in enumerate(raw_buffers):
                if buf and len(buf) > 1024:  # Un messaggio GRIB2 valido supera sempre 1 KB
                    buffers.append(buf)
                    kb_size = len(buf) / 1024.0
                    msg = f"[{label}] Blocco {idx+1}: scaricati {kb_size:.1f} KB con successo."
                    print(f"[DEBUG] {msg}")
                    if status_callback:
                        status_callback(msg)
                else:
                    print(f"[DEBUG] ⚠️ [{label}] Blocco {idx+1}: scartato (troppo piccolo o vuoto).")
                    if status_callback:
                        status_callback(f"⚠️ [{label}] Avviso: blocco {idx+1} vuoto o non valido.")

            missing.extend(raw_missing)
            return buffers, missing

        # 1. Download GFS con monitoraggio
        if gfs_vars_sel:
            if status_callback:
                status_callback("📥 Scaricamento dati GFS (Atmosfera) in corso...")
            gfs_buffers, gfs_missing = monitored_fetch(GfsDownloader, gfs_vars_sel, "GFS")
            missing_steps_total.extend(gfs_missing)
            all_buffers.extend(gfs_buffers)

        # 2. Download WW3 con monitoraggio
        if ww3_vars_sel:
            if status_callback:
                status_callback("🌊 Scaricamento dati WW3 (Onde) in corso...")
            ww3_buffers, ww3_missing = monitored_fetch(Ww3Downloader, ww3_vars_sel, "WW3")
            missing_steps_total.extend(ww3_missing)
            if ww3_buffers:
                all_buffers.extend(ww3_buffers)
                if status_callback:
                    status_callback("✅ Aggiunta record WW3 completata con successo.")
            else:
                if status_callback:
                    status_callback("⚠️ Attenzione: Nessun dato WW3 valido disponibile per la combinazione.")

        total_size_kb = sum(len(b) for b in all_buffers) / 1024.0
        if status_callback and all_buffers:
            status_callback(f"✨ Download combinato completato! Totale buffer validi: {total_size_kb:.1f} KB.")

        return all_buffers, list(set(missing_steps_total))