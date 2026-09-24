# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import os
import platform
import shutil
import subprocess


class XyGribHandler:

    @staticmethod
    def _trova_eseguibile():
        """Rileva l'eseguibile o il comando di avvio per XyGrib in base al sistema operativo."""
        os_name = platform.system()

        # 1. macOS (Darwin)
        if os_name == "Darwin":
            # Su macOS 'open -a XyGrib' avvia l'App Bundle nativo
            return "open_mac"

        # 2. Windows
        elif os_name == "Windows":
            default_paths = [
                r"C:\Program Files\XyGrib\XyGrib.exe",
                r"C:\Program Files (x86)\XyGrib\XyGrib.exe",
                os.path.expanduser(
                    r"~\AppData\Local\Programs\XyGrib\XyGrib.exe"
                ),
            ]
            for path in default_paths:
                if os.path.exists(path):
                    return path

            # Fallback nel caso sia stato aggiunto al PATH di Windows
            for cmd in ["XyGrib.exe", "xygrib.exe"]:
                if shutil.which(cmd):
                    return cmd

        # 3. Linux (e altri sistemi Unix-like)
        else:
            for cmd in ["xygrib", "XyGrib", "zygrib", "ZyGrib"]:
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
                "Eseguibile XyGrib non trovato nel sistema."
            )

        os_name = platform.system()
        work_dir = os.path.dirname(filepath_grib2)

        # Gestione del lancio del processo senza shell=True
        if os_name == "Darwin" and binario == "open_mac":
            # macOS: usa il comando nativo 'open'
            subprocess.Popen(
                ["open", "-a", "XyGrib", filepath_grib2], cwd=work_dir
            )
        else:
            # Linux e Windows: esecuzione diretta del binario con lista di argomenti
            subprocess.Popen([binario, filepath_grib2], cwd=work_dir)