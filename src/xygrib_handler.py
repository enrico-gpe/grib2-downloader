# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import os
import shutil
import subprocess


class XyGribHandler:

    @staticmethod
    def _trova_eseguibile():
        """Rileva automaticamente l'eseguibile XyGrib/zyGrib presente nel PATH di sistema."""
        for cmd in ["XyGrib", "xygrib", "zygrib", "ZyGrib"]:
            if shutil.which(cmd):
                return cmd
        return None

    @classmethod
    def apri_in_xygrib(cls, filepath_grib2: str):
        """Apre il file GRIB2 scaricato all'interno di XyGrib."""
        if not filepath_grib2 or not os.path.exists(filepath_grib2):
            raise FileNotFoundError(
                "Nessun file GRIB2 valido trovato da aprire."
            )

        binario = cls._trova_eseguibile()
        if not binario:
            raise FileNotFoundError(
                "Eseguibile XyGrib non trovato nel PATH di sistema."
            )

        work_dir = os.path.dirname(filepath_grib2)
        cmd = f"{binario} '{filepath_grib2}'"

        # Avvia XyGrib in un processo separato
        subprocess.Popen(cmd, shell=True, cwd=work_dir)