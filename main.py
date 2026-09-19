# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import tkinter as tk
from src.gui import GRIB2DownloaderGUI


def main():
    root = tk.Tk()
    app = GRIB2DownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()