# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import os
import subprocess
import glob

class GradsHandler:

    @staticmethod
    def ottieni_ultimo_grib2(download_dir: str) -> str:
        """Trova il file .grib2 o .grb2 modificato più di recente nella directory specificata."""
        if not os.path.exists(download_dir):
            raise FileNotFoundError(
                f"La cartella {download_dir} non esiste."
            )

        # Cerca file con estensione .grib2 o .grb2
        pattern_grib2 = os.path.join(download_dir, "*.grib2")
        pattern_grb2 = os.path.join(download_dir, "*.grb2")
        file_list = glob.glob(pattern_grib2) + glob.glob(pattern_grb2)

        if not file_list:
            raise FileNotFoundError(
                f"Nessun file GRIB2 (.grib2 / .grb2) trovato in {download_dir}."
            )

        # Ordina per data di ultima modifica (il più recente per ultimo)
        ultimo_file = max(file_list, key=os.path.getmtime)
        return ultimo_file

    @staticmethod
    def visualizza_ultimo(download_dir: str):
        """Trova ed apre direttamente l'ultimo file scaricato in GrADS."""
        ultimo_file = GradsHandler.ottieni_ultimo_grib2(download_dir)
        print(f"[DEBUG GrADS] Apertura ultimo file trovato: {ultimo_file}")
        GradsHandler.visualizza_in_grads(ultimo_file)
    @staticmethod
    def visualizza_in_grads(filepath_grib2: str):
        """Prepara il file GRIB2 tramite g2ctl e gribmap, poi lo apre ed esegue l'ambiente in GrADS."""
        if not filepath_grib2 or not os.path.exists(filepath_grib2):
            raise FileNotFoundError(
                "Nessun file GRIB2 valido trovato da visualizzare."
            )

        work_dir = os.path.dirname(filepath_grib2)
        filename_grib2 = os.path.basename(filepath_grib2)
        filename_base, _ = os.path.splitext(filename_grib2)
        filename_ctl = f"{filename_base}.ctl"

        print(
            f"[DEBUG GrADS] Generazione CTL con g2ctl per {filename_grib2}..."
        )
        # 1. Genera il file .ctl con g2ctl
        cmd_g2ctl = f"g2ctl {filename_grib2} > {filename_ctl}"
        subprocess.run(
            cmd_g2ctl,
            shell=True,
            check=True,
            cwd=work_dir,
            capture_output=True,
        )

        print(
            f"[DEBUG GrADS] Indicizzazione IDX con gribmap per"
            f" {filename_ctl}..."
        )
        # 2. Crea l'indice .idx con gribmap
        cmd_gribmap = f"gribmap -v -i {filename_ctl}"
        subprocess.run(
            cmd_gribmap,
            shell=True,
            check=True,
            cwd=work_dir,
            capture_output=True,
        )

        # 3. Scrive lo script startup.gs minimale e reattivo
        gs_script_path = os.path.join(work_dir, "startup.gs")
        with open(gs_script_path, "w") as gs_file:
            gs_file.write(f"open {filename_ctl}\n")
            gs_file.write("query file\n")
            gs_file.write("set gxout shaded\n")
            gs_file.write("set mpdset hires\n")

        print(
            "[DEBUG GrADS] Avvio di GrADS con esecuzione sequenziale di"
            " startup.gs..."
        )

        # 4. Lancia GrADS passando l'esecuzione dello script
        cmd_grads = "grads -l -c 'exec startup.gs'"
        subprocess.Popen(cmd_grads, shell=True, cwd=work_dir)