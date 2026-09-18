# ===============================================================================
# Weather GRIB2 Downloader (Interactive Map Edition)
# ===============================================================================
# Modulo principale per lo scaricamento di dati meteorologici GRIB2 da modelli
# GFS (NOAA NOMADS) e ICON-EU (DWD OpenData) tramite selezione geografica
# interattiva su mappa.

# Versione: 2.0.0
# Autore: Enrico Pozzi
# ===============================================================================
# LICENZA / LICENSE (GNU General Public License v3.0)
# -------------------------------------------------------------------------------
# Questo programma è software libero; è possibile ridistribuirlo e/o modificarlo
# secondo i termini della Licenza Pubblica Generica GNU (GNU General Public License)
# pubblicata dalla Free Software Foundation; o la versione 3 della Licenza, o
# (a propria scelta) una qualsiasi versione successiva.

# Questo programma è distribuito nella speranza che sia utile, ma SENZA ALCUNA
# GARANZIA; senza neppure la garanzia implicita di COMMERCIABILITÀ o IDONEITÀ PER
# UNO SCOPO PARTICOLARE. Per maggiori dettagli consultare la GNU General Public
# License.

# Dovresti aver ricevuto una copia della Licenza Pubblica Generica GNU insieme
# a questo programma. In caso contrario, consultare <https://www.gnu.org/licenses/>.
# ===============================================================================

import bz2
import os
import threading
import urllib.request
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview

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
    "10m Wind Vector (UGRD/VGRD)": "&var_UGRD=on&var_VGRD=on&lev_10_m_above_ground=on",
    "Surface Wind Gust (GUST)": "&var_GUST=on&lev_surface=on"
}

ICON_VARS = {
    "Pressione liv. mare (prmslmsl)": [("pmsl", "PMSL")],
    "Temperatura 2m (tmp2m)": [("t_2m", "T_2M")],
    "Copertura Nuvolosa (tcdcsfc)": [("clct", "CLCT")],
    "CAPE Suolo (capesfc)": [("cape_ml", "CAPE_ML")],
    "Tasso Precip. (tpratesfc)": [("tot_prec", "TOT_PREC")],
    "Vento 10m (ugrd10m/vgrd10m)": [("u_10m", "U_10M"), ("v_10m", "V_10M")],
    "Raffica Vento (gustsfc)": [("vmax_10m", "VMAX_10M")],
}

class GRIB2DownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather GRIB2 Downloader (GFS / ICON-EU)")
        self.root.geometry("1280x850")

        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.left_container = ttk.Frame(self.paned_window)
        self.right_frame = ttk.Frame(self.paned_window, padding=5)

        self.paned_window.add(self.left_container, weight=1)
        self.paned_window.add(self.right_frame, weight=3)

        self.scrollbar = ttk.Scrollbar(self.left_container, orient="vertical")
        self.left_canvas = tk.Canvas(self.left_container, highlightthickness=0, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.left_canvas.yview)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.left_canvas, padding=10)
        self.canvas_window = self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")

        self.left_frame.bind("<Configure>", lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))
        self.left_canvas.bind("<Configure>", lambda e: self.left_canvas.itemconfig(self.canvas_window, width=e.width))

        self.click_step = 0
        self.click_coords = []
        self.temp_marker = None
        self.rect_map = None
        self.var_checks = {}

        self._build_controls()
        self._build_map()

    def _build_controls(self):
        lbl_model = ttk.LabelFrame(self.left_frame, text=" Modello Meteorologico ", padding=8)
        lbl_model.pack(fill=tk.X, pady=5)
        self.cmb_model = ttk.Combobox(lbl_model, values=["GFS (NOAA NOMADS)", "ICON-EU (DWD OpenData)"], state="readonly")
        self.cmb_model.current(0)
        self.cmb_model.pack(fill=tk.X, pady=2)
        self.cmb_model.bind("<<ComboboxSelected>>", self.on_model_change)

        lbl_area = ttk.LabelFrame(self.left_frame, text=" Bounding Box Area (°N / °E) ", padding=8)
        lbl_area.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_area, text="North (Lat Max):").grid(row=0, column=0, sticky="e")
        self.ent_north = ttk.Entry(lbl_area, width=8)
        self.ent_north.insert(0, "48.0")
        self.ent_north.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="South (Lat Min):").grid(row=1, column=0, sticky="e")
        self.ent_south = ttk.Entry(lbl_area, width=8)
        self.ent_south.insert(0, "43.5")
        self.ent_south.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="West (Lon Min):").grid(row=2, column=0, sticky="e")
        self.ent_west = ttk.Entry(lbl_area, width=8)
        self.ent_west.insert(0, "5.0")
        self.ent_west.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="East (Lon Max):").grid(row=3, column=0, sticky="e")
        self.ent_east = ttk.Entry(lbl_area, width=8)
        self.ent_east.insert(0, "16.0")
        self.ent_east.grid(row=3, column=1, padx=5, pady=2)

        self.btn_select_map = ttk.Button(lbl_area, text="📍 Seleziona su Mappa (2 Click)", command=self.enable_map_selection)
        self.btn_select_map.grid(row=4, column=0, columnspan=2, pady=3, sticky="ew")

        self.btn_update_map = ttk.Button(lbl_area, text="🔄 Aggiorna Rettangolo", command=self.draw_bbox_on_map)
        self.btn_update_map.grid(row=5, column=0, columnspan=2, pady=2, sticky="ew")

        self.lbl_vars = ttk.LabelFrame(self.left_frame, text=" Variabili Selezionate ", padding=8)
        self.lbl_vars.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(self.lbl_vars)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Tutte", command=lambda: [v.set(True) for v in self.var_checks.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Nessuna", command=lambda: [v.set(False) for v in self.var_checks.values()]).pack(side=tk.LEFT, padx=2)

        self.vars_container = ttk.Frame(self.lbl_vars)
        self.vars_container.pack(fill=tk.X, pady=4)
        self.update_variable_checkboxes()

        lbl_time = ttk.LabelFrame(self.left_frame, text=" Range Temporale ", padding=8)
        lbl_time.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_time, text="Ore Passate:").grid(row=0, column=0, sticky="e")
        self.ent_start_h = ttk.Entry(lbl_time, width=6)
        self.ent_start_h.insert(0, "-18")
        self.ent_start_h.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(lbl_time, text="Ore Future:").grid(row=1, column=0, sticky="e")
        self.ent_end_h = ttk.Entry(lbl_time, width=6)
        self.ent_end_h.insert(0, "120")
        self.ent_end_h.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(lbl_time, text="Passo Orario (h):").grid(row=2, column=0, sticky="e")
        self.ent_step_h = ttk.Entry(lbl_time, width=6)
        self.ent_step_h.insert(0, "3")
        self.ent_step_h.grid(row=2, column=1, padx=5, pady=2)

        lbl_out = ttk.LabelFrame(self.left_frame, text=" Output ", padding=8)
        lbl_out.pack(fill=tk.X, pady=5)
        ttk.Label(lbl_out, text="Nome File Output:").pack(anchor="w")
        self.ent_out_name = ttk.Entry(lbl_out)
        self.ent_out_name.insert(0, "custom_weather.grb2")
        self.ent_out_name.pack(fill=tk.X, pady=2)

        lbl_action = ttk.LabelFrame(self.left_frame, text=" Esecuzione ", padding=8)
        lbl_action.pack(fill=tk.X, pady=5)
        self.btn_download = ttk.Button(lbl_action, text="⚡ AVVIA DOWNLOAD GRIB2", command=self.start_download_thread)
        self.btn_download.pack(fill=tk.X, pady=5)
        self.progress = ttk.Progressbar(lbl_action, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=4)
        self.lbl_status = ttk.Label(lbl_action, text="Stato: In attesa...", foreground="gray")
        self.lbl_status.pack(anchor="w", pady=2)

    def log_debug(self, filename, url):
        print(f"[DEBUG] FILE: {filename}")
        print(f"[DEBUG] LINK: {url}")
        print("-" * 60)

    def set_widgets_state(self, state):
        entries = [
            self.ent_north, self.ent_south, self.ent_west, self.ent_east,
            self.ent_start_h, self.ent_end_h, self.ent_step_h
        ]
        for e in entries:
            e.config(state=state)
            
        btn_state = tk.NORMAL if state == "normal" else tk.DISABLED
        self.btn_select_map.config(state=btn_state)
        self.btn_update_map.config(state=btn_state)

    def on_model_change(self, event=None):
        if "ICON-EU" in self.cmb_model.get():
            self.set_widgets_state("normal")
            
            self.ent_start_h.delete(0, tk.END); self.ent_start_h.insert(0, "0")
            self.ent_end_h.delete(0, tk.END); self.ent_end_h.insert(0, "48")
            self.ent_step_h.delete(0, tk.END); self.ent_step_h.insert(0, "3")
            
            self.ent_north.delete(0, tk.END); self.ent_north.insert(0, "70.0")
            self.ent_south.delete(0, tk.END); self.ent_south.insert(0, "29.5")
            self.ent_west.delete(0, tk.END); self.ent_west.insert(0, "-23.5")
            self.ent_east.delete(0, tk.END); self.ent_east.insert(0, "45.0")
            
            self.set_widgets_state("disabled")
            self.draw_bbox_on_map()
        else:
            self.set_widgets_state("normal")
            self.ent_start_h.delete(0, tk.END); self.ent_start_h.insert(0, "-18")
            self.ent_end_h.delete(0, tk.END); self.ent_end_h.insert(0, "120")
            self.ent_step_h.delete(0, tk.END); self.ent_step_h.insert(0, "3")
            
            self.ent_north.delete(0, tk.END); self.ent_north.insert(0, "48.0")
            self.ent_south.delete(0, tk.END); self.ent_south.insert(0, "43.5")
            self.ent_west.delete(0, tk.END); self.ent_west.insert(0, "5.0")
            self.ent_east.delete(0, tk.END); self.ent_east.insert(0, "16.0")
            self.draw_bbox_on_map()

        self.update_variable_checkboxes()

    def update_variable_checkboxes(self):
        for widget in self.vars_container.winfo_children(): widget.destroy()
        self.var_checks.clear()
        target_dict = GFS_VARS if "GFS" in self.cmb_model.get() else ICON_VARS
        for name in target_dict.keys():
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.vars_container, text=name, variable=var)
            chk.pack(anchor="w", pady=2)
            self.var_checks[name] = var

    def _build_map(self):
        self.map_widget = tkintermapview.TkinterMapView(self.right_frame, width=800, height=600, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        self.map_widget.set_position(45.8, 10.5)
        self.map_widget.set_zoom(5)
        self.map_widget.add_left_click_map_command(self.on_map_click)
        self.root.after(500, self.draw_bbox_on_map)

    def enable_map_selection(self):
        if "ICON-EU" in self.cmb_model.get(): return
        self.click_step = 1
        self.click_coords.clear()
        if self.temp_marker: self.temp_marker.delete()
        self.btn_select_map.config(text="Click 1/2: Seleziona Nord-Ovest")
        self.lbl_status.config(text="Fai click sulla mappa per l'angolo Nord-Ovest...", foreground="blue")

    def on_map_click(self, coords):
        if "ICON-EU" in self.cmb_model.get(): return
        if self.click_step == 1:
            self.click_coords.append(coords)
            self.temp_marker = self.map_widget.set_marker(coords[0], coords[1], text="Punto 1")
            self.click_step = 2
            self.btn_select_map.config(text="Click 2/2: Seleziona Sud-Est")
            self.lbl_status.config(text="Fai click sulla mappa per l'angolo Sud-Est...", foreground="blue")
        elif self.click_step == 2:
            self.click_coords.append(coords)
            p1, p2 = self.click_coords[0], self.click_coords[1]
            north, south = max(p1[0], p2[0]), min(p1[0], p2[0])
            west, east = min(p1[1], p2[1]), max(p1[1], p2[1])

            self.ent_north.delete(0, tk.END); self.ent_north.insert(0, f"{north:.2f}")
            self.ent_south.delete(0, tk.END); self.ent_south.insert(0, f"{south:.2f}")
            self.ent_west.delete(0, tk.END); self.ent_west.insert(0, f"{west:.2f}")
            self.ent_east.delete(0, tk.END); self.ent_east.insert(0, f"{east:.2f}")

            if self.temp_marker: self.temp_marker.delete()
            self.click_step = 0
            self.btn_select_map.config(text="📍 Seleziona su Mappa (2 Click)")
            self.lbl_status.config(text="Area aggiornata con successo!", foreground="green")
            self.draw_bbox_on_map()

    def draw_bbox_on_map(self):
        try:
            north, south = float(self.ent_north.get()), float(self.ent_south.get())
            west, east = float(self.ent_west.get()), float(self.ent_east.get())
            if self.rect_map: self.rect_map.delete()
            polygon_path = [(north, west), (north, east), (south, east), (south, west)]
            self.rect_map = self.map_widget.set_polygon(polygon_path, outline_color="#d62728", fill_color="#ff4136", border_width=2)
        except ValueError:
            pass

    def start_download_thread(self):
        threading.Thread(target=self.run_download, daemon=True).start()

    def _find_latest_icon_run(self):
        now = datetime.now(timezone.utc)
        for offset_hours in range(0, 36, 3):
            check_dt = now - timedelta(hours=offset_hours)
            run_hour = (check_dt.hour // 6) * 6
            run_dt = check_dt.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            date_str = run_dt.strftime("%Y%m%d")
            run_str = f"{run_dt.hour:02d}"

            filename = f"icon-eu_europe_regular-lat-lon_single-level_{date_str}{run_str}_000_PMSL.grib2.bz2"
            test_url = f"https://opendata.dwd.de/weather/nwp/icon-eu/grib/{run_str}/pmsl/{filename}"
            
            if self._fetch_url(test_url, filename):
                return run_dt
        return None

    def run_download(self):
        try:
            self.btn_download.config(state=tk.DISABLED)
            selected_model = self.cmb_model.get()
            
            output_filename = self.ent_out_name.get().strip()
            if not output_filename.endswith(".grb2"): output_filename += ".grb2"

            selected_vars = [name for name, is_sel in self.var_checks.items() if is_sel.get()]
            if not selected_vars:
                messagebox.showwarning("Attenzione", "Seleziona almeno una variabile!")
                return

            downloaded_buffers = []

            # 1. GFS (NOAA)
            if "GFS" in selected_model:
                north, south = float(self.ent_north.get()), float(self.ent_south.get())
                west, east = float(self.ent_west.get()), float(self.ent_east.get())
                start_h, end_h, step_h = int(self.ent_start_h.get()), int(self.ent_end_h.get()), int(self.ent_step_h.get())
                steps = list(range(start_h, end_h + 1, step_h))

                now = datetime.now(timezone.utc)
                run_dt = now.replace(minute=0, second=0, microsecond=0)
                run_dt = run_dt - timedelta(hours=run_dt.hour % 6)
                
                var_query = "".join([GFS_VARS[v] for v in selected_vars])
                
                filename_test = f"gfs.t{run_dt.hour:02d}z.pgrb2.0p25.f000"
                test_url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file={filename_test}&dir=%2Fgfs.{run_dt.strftime('%Y%m%d')}%2F{run_dt.hour:02d}%2Fatmos"
                
                if not self._fetch_url(test_url, filename_test):
                    run_dt -= timedelta(hours=6)

                self.progress["maximum"] = len(steps)
                for idx, h in enumerate(steps):
                    c_date, c_run, c_fstep = self._get_time_params(run_dt, h)
                    filename = f"gfs.t{c_run}z.pgrb2.0p25.f{c_fstep}"
                    url = (f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
                           f"file={filename}{var_query}"
                           f"&subregion=on&leftlon={west}&rightlon={east}&toplat={north}&bottomlat={south}"
                           f"&dir=%2Fgfs.{c_date}%2F{c_run}%2Fatmos")
                    self.lbl_status.config(text=f"GFS Download {h}h ({idx+1}/{len(steps)})...")
                    data = self._fetch_url(url, filename)
                    if data: downloaded_buffers.append(data)
                    self.progress["value"] = idx + 1

            # 2. ICON-EU (DWD)
            else:
                self.lbl_status.config(text="Verifica run ICON-EU disponibile...")
                run_dt = self._find_latest_icon_run()
                if not run_dt:
                    messagebox.showerror("Errore", "Nessuna run recente valida trovata su OpenData DWD.")
                    return

                date_str = run_dt.strftime("%Y%m%d")
                run_str = f"{run_dt.hour:02d}"

                valid_steps = list(range(0, 49, 3))
                self.progress["maximum"] = len(valid_steps)

                for idx, h in enumerate(valid_steps):
                    self.lbl_status.config(text=f"ICON-EU (Run {run_str}Z) {h}h ({idx+1}/{len(valid_steps)})...")
                    step_buffer = bytearray()
                    for var_name in selected_vars:
                        for folder, var_code in ICON_VARS[var_name]:
                            filename = f"icon-eu_europe_regular-lat-lon_single-level_{date_str}{run_str}_{h:03d}_{var_code}.grib2.bz2"
                            url = f"https://opendata.dwd.de/weather/nwp/icon-eu/grib/{run_str}/{folder}/{filename}"
                            
                            raw_bz2 = self._fetch_url(url, filename)
                            if raw_bz2:
                                step_buffer.extend(bz2.decompress(raw_bz2))
                    if step_buffer:
                        downloaded_buffers.append(bytes(step_buffer))
                    self.progress["value"] = idx + 1

            if downloaded_buffers:
                out_path = os.path.join(os.getcwd(), output_filename)
                with open(out_path, "wb") as outfile:
                    for buf in downloaded_buffers: outfile.write(buf)
                size_mb = os.path.getsize(out_path) / (1024 * 1024)
                self.lbl_status.config(text=f"Completato! ({size_mb:.2f} MB)", foreground="green")
                messagebox.showinfo("Successo", f"File salvato con successo:\n{out_path}\n\nDimensione: {size_mb:.2f} MB")
            else:
                self.lbl_status.config(text="Download fallito.", foreground="red")
                messagebox.showerror("Errore", "Impossibile scaricare i dati GRIB2.")
        except Exception as ex:
            messagebox.showerror("Errore", str(ex))
        finally:
            self.btn_download.config(state=tk.NORMAL)

    def _get_time_params(self, base_dt, h):
        target_dt = base_dt + timedelta(hours=h)
        if h < 0:
            target_run_hour = (target_dt.hour // 6) * 6
            run_base = target_dt.replace(hour=target_run_hour, minute=0, second=0, microsecond=0)
            f_hour = int((target_dt - run_base).total_seconds() // 3600)
            return run_base.strftime("%Y%m%d"), f"{run_base.hour:02d}", f"{f_hour:03d}"
        return base_dt.strftime("%Y%m%d"), f"{base_dt.hour:02d}", f"{h:03d}"

    def _fetch_url(self, url, filename=""):
        try:
            self.log_debug(filename, url)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                return data if len(data) > 500 else None
        except Exception:
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = GRIB2DownloaderGUI(root)
    root.mainloop()