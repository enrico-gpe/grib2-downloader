# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import json
import os

CONFIG_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "model": "GFS (NOAA NOMADS)",
    "north": "48.0",
    "south": "43.5",
    "west": "5.0",
    "east": "16.0",
    "start_h": "-18",
    "end_h": "120",
    "step_h": "3",
    "output_dir": os.getcwd(),
    "output_file": "custom_weather.grb2",
    "selected_vars_gfs": [],
    "selected_vars_icon": [],
}


class ConfigManager:

    @staticmethod
    def load_config() -> dict:
        """Carica le impostazioni da settings.json. Se non esiste, crea quelle predefinite."""
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_SETTINGS.copy()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Unisce i valori caricati con quelli predefiniti per gestire eventuali nuove chiavi
                merged_config = DEFAULT_SETTINGS.copy()
                merged_config.update(config)
                return merged_config
        except Exception as e:
            print(f"[DEBUG] Errore durante il caricamento di {CONFIG_FILE}: {e}")
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_config(data: dict) -> bool:
        """Salva il dizionario delle impostazioni su settings.json."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("[DEBUG] Impostazioni salvate correttamente su settings.json.")
            return True
        except Exception as e:
            print(f"[DEBUG] Errore durante il salvataggio delle impostazioni: {e}")
            return False