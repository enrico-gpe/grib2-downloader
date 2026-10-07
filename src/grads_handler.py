# src/grads_handler.py
# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import glob
import os
import subprocess


class GradsHandler:

    @staticmethod
    def ottieni_ultimo_grib2(cartella: str) -> str:
        """Cerca il file GRIB2 più recente all'interno della cartella specificata."""
        files = glob.glob(os.path.join(cartella, "*.grb2"))
        if not files:
            raise FileNotFoundError(
                f"Nessun file .grb2 trovato nella cartella {cartella}"
            )
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]

    @staticmethod
    def visualizza_in_grads(grib_path: str):
        """Genera il CTL con g2ctl e l'indice con gribmap (con flag 0), poi avvia GrADS."""
        if not os.path.exists(grib_path):
            raise FileNotFoundError(f"File GRIB2 non trovato: {grib_path}")

        working_dir = os.path.dirname(os.path.abspath(grib_path))
        base_path = os.path.splitext(grib_path)[0]
        ctl_path = f"{base_path}.ctl"
        idx_path = f"{base_path}.idx"

        # 1. Rimuovi vecchi file di controllo per evitare sovrapposizioni
        for f in [ctl_path, idx_path]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

        # 2. Genera il file .ctl (esattamente: g2ctl custom_weather.grb2 > custom_weather.ctl)
        print(f"[GRADS HANDLER] Generazione CTL per: {grib_path}")
        cmd_g2ctl = f"g2ctl {grib_path} > {ctl_path}"
        res_g2ctl = subprocess.run(
            cmd_g2ctl, shell=True, capture_output=True, text=True, cwd=working_dir
        )

        if res_g2ctl.returncode != 0:
            raise RuntimeError(
                f"Errore durante l'esecuzione di g2ctl:\n{res_g2ctl.stderr}"
            )

        # 3. Genera l'indice (esattamente: gribmap -v -i custom_weather.ctl 0)
        print("[GRADS HANDLER] Indicizzazione GRIB2 tramite gribmap...")
        cmd_gribmap = f"gribmap -v -i {ctl_path} 0"
        res_gribmap = subprocess.run(
            cmd_gribmap, shell=True, capture_output=True, text=True, cwd=working_dir
        )

        if res_gribmap.returncode != 0:
            raise RuntimeError(
                f"Errore durante l'esecuzione di gribmap:\n{res_gribmap.stderr}"
            )

        # 4. Avvia GrADS o opengrads aprendo direttamente il file .ctl
        grads_exec = "grads"
        if subprocess.call(["which", "opengrads"], stdout=subprocess.DEVNULL) == 0:
            grads_exec = "grads"

        print(f"[GRADS HANDLER] Avvio di {grads_exec} caricando {ctl_path}...")

        subprocess.Popen(
            [grads_exec, "-l", "-c", f"open {ctl_path}"],
            cwd=working_dir
        )
