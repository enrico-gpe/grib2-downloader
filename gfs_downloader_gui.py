import os
import threading
import urllib.request
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview

# -------------------------------------------------------------------
# MAPPATURA VARIABILI GFS (Accoppiamento esplicito Variabile + Livello)
# -------------------------------------------------------------------
AVAILABLE_VARS = {
    "Zero Isotherm Height (HGT 0C)": "&var_HGT=on&lev_0C_isotherm=on",
    "2m Temperature (TMP 2m)": "&var_TMP=on&lev_2_m_above_ground=on",
    "850 hPa Temp (TMP 850mb)": "&var_TMP=on&lev_850_mb=on",
    "500 hPa Height (HGT 500mb)": "&var_HGT=on&lev_500_mb=on",
    "Total Precip (APCP sfc)": "&var_APCP=on&lev_surface=on",
    "Relative Humidity 2m (RH 2m)": "&var_RH=on&lev_2_m_above_ground=on",
    "Total Cloud Cover (TCDC)": "&var_TCDC=on&lev_entire_atmosphere=on",
    "CAPE (Surface)": "&var_CAPE=on&lev_surface=on",
    "CIN (Surface)": "&var_CIN=on&lev_surface=on",
    "10m Wind Vector (UGRD/VGRD)": "&var_UGRD=on&var_VGRD=on&lev_10_m_above_ground=on",
    "Surface Wind Gust (GUST)": "&var_GUST=on&lev_surface=on"
}


class GFSDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GFS GRIB2 Subregion Downloader")
        self.root.geometry("1250x780")

        # ---------------------------------------------------------------
        # PANEDWINDOW: Pannello separatore trascinabile col mouse
        # ---------------------------------------------------------------
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Container Sinistra (Controlli)
        self.left_container = ttk.Frame(self.paned_window)

        # Container Destra (Mappa)
        self.right_frame = ttk.Frame(self.paned_window, padding=5)

        # Aggiunta pannelli alla PanedWindow
        self.paned_window.add(self.left_container, weight=1)
        self.paned_window.add(self.right_frame, weight=3)

        # ---------------------------------------------------------------
        # CANVAS + SCROLLBAR PER COLONNA SINISTRA
        # ---------------------------------------------------------------
        self.scrollbar = ttk.Scrollbar(self.left_container, orient="vertical")
        self.left_canvas = tk.Canvas(
            self.left_container, 
            highlightthickness=0, 
            yscrollcommand=self.scrollbar.set
        )
        self.scrollbar.config(command=self.left_canvas.yview)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.left_canvas, padding=10)
        self.canvas_window = self.left_canvas.create_window(
            (0, 0), window=self.left_frame, anchor="nw"
        )

        # Eventi di ridimensionamento dinamico del canvas
        self.left_frame.bind("<Configure>", self._on_frame_configure)
        self.left_canvas.bind("<Configure>", self._on_canvas_configure)

        # Abilita lo scroll tramite la rotellina del mouse
        self.left_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._build_controls()
        self._build_map()

        self.rect_map = None

    def _on_frame_configure(self, event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Mantiene il frame interno largo quanto il canvas durante il ridimensionamento
        self.left_canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Supporto per scroll con la rotellina
        self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_controls(self):
        # 1. Coordinate Bounding Box
        lbl_area = ttk.LabelFrame(self.left_frame, text=" Bounding Box Area (°N / °E) ", padding=8)
        lbl_area.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_area, text="North (Lat Max):").grid(row=0, column=0, sticky='e')
        self.ent_north = ttk.Entry(lbl_area, width=8)
        self.ent_north.insert(0, "48.0")
        self.ent_north.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="South (Lat Min):").grid(row=1, column=0, sticky='e')
        self.ent_south = ttk.Entry(lbl_area, width=8)
        self.ent_south.insert(0, "43.5")
        self.ent_south.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="West (Lon Min):").grid(row=2, column=0, sticky='e')
        self.ent_west = ttk.Entry(lbl_area, width=8)
        self.ent_west.insert(0, "5.0")
        self.ent_west.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="East (Lon Max):").grid(row=3, column=0, sticky='e')
        self.ent_east = ttk.Entry(lbl_area, width=8)
        self.ent_east.insert(0, "16.0")
        self.ent_east.grid(row=3, column=1, padx=5, pady=2)

        btn_update_map = ttk.Button(lbl_area, text="Aggiorna Rettangolo Mappa", command=self.draw_bbox_on_map)
        btn_update_map.grid(row=4, column=0, columnspan=2, pady=5)

        # 2. Selezione Variabili
        lbl_vars = ttk.LabelFrame(self.left_frame, text=" Variabili GFS ", padding=8)
        lbl_vars.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(lbl_vars)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Tutte", command=self.select_all_vars).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Nessuna", command=self.deselect_all_vars).pack(side=tk.LEFT, padx=2)

        vars_container = ttk.Frame(lbl_vars)
        vars_container.pack(fill=tk.X, pady=4)

        self.var_checks = {}
        for name in AVAILABLE_VARS.keys():
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(vars_container, text=name, variable=var)
            chk.pack(anchor='w', pady=2)
            self.var_checks[name] = var

        # 3. Finestra Temporale
        lbl_time = ttk.LabelFrame(self.left_frame, text=" Range Temporale ", padding=8)
        lbl_time.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_time, text="Ore Passate (es. -18):").grid(row=0, column=0, sticky='e')
        self.ent_start_h = ttk.Entry(lbl_time, width=6)
        self.ent_start_h.insert(0, "-18")
        self.ent_start_h.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(lbl_time, text="Ore Future (es. 120):").grid(row=1, column=0, sticky='e')
        self.ent_end_h = ttk.Entry(lbl_time, width=6)
        self.ent_end_h.insert(0, "120")
        self.ent_end_h.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(lbl_time, text="Passo Orario (h):").grid(row=2, column=0, sticky='e')
        self.ent_step_h = ttk.Entry(lbl_time, width=6)
        self.ent_step_h.insert(0, "3")
        self.ent_step_h.grid(row=2, column=1, padx=5, pady=2)

        # 4. Output File
        lbl_out = ttk.LabelFrame(self.left_frame, text=" Output ", padding=8)
        lbl_out.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_out, text="Nome File Output:").pack(anchor='w')
        self.ent_out_name = ttk.Entry(lbl_out)
        self.ent_out_name.insert(0, "gfs_custom_alps.grb2")
        self.ent_out_name.pack(fill=tk.X, pady=2)

        # 5. Bottone Download & Stato
        lbl_action = ttk.LabelFrame(self.left_frame, text=" Esecuzione ", padding=8)
        lbl_action.pack(fill=tk.X, pady=10)

        self.btn_download = ttk.Button(lbl_action, text="⚡ AVVIA DOWNLOAD GRIB2", command=self.start_download_thread)
        self.btn_download.pack(fill=tk.X, pady=5)

        self.progress = ttk.Progressbar(lbl_action, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=4)

        self.lbl_status = ttk.Label(lbl_action, text="Stato: In attesa...", foreground="gray")
        self.lbl_status.pack(anchor='w', pady=2)

    def select_all_vars(self):
        for var in self.var_checks.values():
            var.set(True)

    def deselect_all_vars(self):
        for var in self.var_checks.values():
            var.set(False)

    def _build_map(self):
        self.map_widget = tkintermapview.TkinterMapView(self.right_frame, width=800, height=600, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        self.map_widget.set_position(45.8, 10.5)
        self.map_widget.set_zoom(7)

        self.root.after(500, self.draw_bbox_on_map)

    def draw_bbox_on_map(self):
        try:
            north = float(self.ent_north.get())
            south = float(self.ent_south.get())
            west = float(self.ent_west.get())
            east = float(self.ent_east.get())

            if self.rect_map:
                self.rect_map.delete()

            polygon_path = [
                (north, west),
                (north, east),
                (south, east),
                (south, west)
            ]

            self.rect_map = self.map_widget.set_polygon(
                polygon_path,
                outline_color="#d62728",
                fill_color="#ff4136",
                border_width=2
            )
        except ValueError:
            messagebox.showerror("Errore", "Coordinate non valide. Inserisci valori numerici.")

    def start_download_thread(self):
        threading.Thread(target=self.run_download, daemon=True).start()

    def run_download(self):
        try:
            self.btn_download.config(state=tk.DISABLED)
            north = float(self.ent_north.get())
            south = float(self.ent_south.get())
            west = float(self.ent_west.get())
            east = float(self.ent_east.get())

            start_h = int(self.ent_start_h.get())
            end_h = int(self.ent_end_h.get())
            step_h = int(self.ent_step_h.get())

            output_filename = self.ent_out_name.get().strip()
            if not output_filename.endswith(".grb2"):
                output_filename += ".grb2"

            # Costruzione sequenziale dei filtri variabili/livelli conforme a NOMADS
            var_query = ""
            for name, is_selected in self.var_checks.items():
                if is_selected.get():
                    var_query += AVAILABLE_VARS[name]

            if not var_query:
                messagebox.showwarning("Attenzione", "Seleziona almeno una variabile!")
                self.btn_download.config(state=tk.NORMAL)
                return

            # Determinazione del run operativo corrente (00, 06, 12, 18 UTC)
            now = datetime.now(timezone.utc)
            run_hour = (now.hour // 6) * 6
            latest_run_dt = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)

            run_str = f"{latest_run_dt.hour:02d}"
            date_str = latest_run_dt.strftime('%Y%m%d')

            self.lbl_status.config(text="Verifica server NOAA NOMADS...", foreground="blue")

            # Test presenza file sul server
            test_url = (
                f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
                f"file=gfs.t{run_str}z.pgrb2.0p25.f000{var_query}"
                f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
                f"&dir=%2Fgfs.{date_str}%2F{run_str}%2Fatmos"
            )

            try:
                req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp:
                    if len(resp.read()) < 500:
                        raise ValueError()
            except Exception:
                # Se il run corrente non è ancora pronto sul server, usa quello di 6 ore prima
                latest_run_dt -= timedelta(hours=6)
                run_str = f"{latest_run_dt.hour:02d}"
                date_str = latest_run_dt.strftime('%Y%m%d')

            self.lbl_status.config(text=f"Run operativo: {date_str} {run_str}Z", foreground="green")

            steps = list(range(start_h, end_h + 1, step_h))
            downloaded_buffers = []

            self.progress["maximum"] = len(steps)
            self.progress["value"] = 0

            for idx, h in enumerate(steps):
                target_dt = latest_run_dt + timedelta(hours=h)

                if h < 0:
                    # Mappa l'ora passata al ciclo run GFS più vicino (00, 06, 12, 18)
                    target_run_hour = (target_dt.hour // 6) * 6
                    base_dt = target_dt.replace(hour=target_run_hour, minute=0, second=0, microsecond=0)

                    forecast_hour = int((target_dt - base_dt).total_seconds() // 3600)

                    c_date = base_dt.strftime('%Y%m%d')
                    c_run = f"{base_dt.hour:02d}"
                    c_fstep = f"{forecast_hour:03d}"
                else:
                    c_date = date_str
                    c_run = run_str
                    c_fstep = f"{h:03d}"

                url = (
                    f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
                    f"file=gfs.t{c_run}z.pgrb2.0p25.f{c_fstep}{var_query}"
                    f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
                    f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fatmos"
                )

                self.lbl_status.config(text=f"Download {h}h ({idx+1}/{len(steps)})...")

                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        data = response.read()
                        if len(data) > 500:
                            downloaded_buffers.append(data)
                        else:
                            print(f"File non disponibile per step {h}h")
                except Exception as e:
                    print(f"Errore step {h}h: {e}")

                self.progress["value"] = idx + 1

            if downloaded_buffers:
                out_path = os.path.join(os.getcwd(), output_filename)
                with open(out_path, 'wb') as outfile:
                    for buf in downloaded_buffers:
                        outfile.write(buf)

                size_mb = os.path.getsize(out_path) / (1024 * 1024)
                self.lbl_status.config(text=f"Completato! ({size_mb:.2f} MB)", foreground="green")
                messagebox.showinfo("Successo", f"File salvato con successo!\n\nFile: {out_path}\nDimensione: {size_mb:.2f} MB")
            else:
                self.lbl_status.config(text="Download fallito.", foreground="red")
                messagebox.showerror("Errore", "Download non riuscito. Verifica la connessione o l'area selezionata.")

        except Exception as ex:
            messagebox.showerror("Errore", str(ex))
        finally:
            self.btn_download.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = GFSDownloaderGUI(root)
    root.mainloop()