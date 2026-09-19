# ----------------------------------------------------------------------
# Copyright (C) 2026 Enrico Pozzi - GNU GPLv3
# ----------------------------------------------------------------------

import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import tkintermapview

from .download_gfs import GFS_VARS, GfsDownloader
from .download_icon import ICON_VARS, IconEuDownloader
from .grads_handler import GradsHandler
from .xygrib_handler import XyGribHandler


class GRIB2DownloaderGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Weather GRIB2 Downloader v3.0 (GFS / ICON-EU)")
        self.root.geometry("1280x850")

        self.last_downloaded_file = None

        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.left_container = ttk.Frame(self.paned_window)
        self.right_frame = ttk.Frame(self.paned_window, padding=5)

        self.paned_window.add(self.left_container, weight=1)
        self.paned_window.add(self.right_frame, weight=3)

        self.scrollbar = ttk.Scrollbar(self.left_container, orient="vertical")
        self.left_canvas = tk.Canvas(
            self.left_container,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set,
        )
        self.scrollbar.config(command=self.left_canvas.yview)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.left_canvas, padding=10)
        self.canvas_window = self.left_canvas.create_window(
            (0, 0), window=self.left_frame, anchor="nw"
        )

        self.left_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(
                scrollregion=self.left_canvas.bbox("all")
            ),
        )
        self.left_canvas.bind(
            "<Configure>",
            lambda e: self.left_canvas.itemconfig(
                self.canvas_window, width=e.width
            ),
        )

        self.click_step = 0
        self.click_coords = []
        self.temp_marker = None
        self.rect_map = None
        self.var_checks = {}

        self._build_controls()
        self._build_map()

        # Popola subito le variabili all'avvio
        self.update_variable_checkboxes()

        # Controlla se esiste gia un file GRIB2 nella cartella corrente per abilitare i tasti
        try:
            ultimo = GradsHandler.ottieni_ultimo_grib2(self.ent_dir_path.get())
            self.last_downloaded_file = ultimo
            self.btn_grads.config(state=tk.NORMAL)
            self.btn_xygrib.config(state=tk.NORMAL)
            print(f"[DEBUG] Trovato file esistente all'avvio: {ultimo}")
        except Exception:
            pass

        print("[DEBUG] Interfaccia v3.0 inizializzata correttamente.")

    def _build_controls(self):
        # 1. Modello
        lbl_model = ttk.LabelFrame(
            self.left_frame, text=" Modello Meteorologico ", padding=8
        )
        lbl_model.pack(fill=tk.X, pady=5)
        self.cmb_model = ttk.Combobox(
            lbl_model,
            values=["GFS (NOAA NOMADS)", "ICON-EU (DWD OpenData)"],
            state="readonly",
        )
        self.cmb_model.current(0)
        self.cmb_model.pack(fill=tk.X, pady=2)
        self.cmb_model.bind("<<ComboboxSelected>>", self.on_model_change)

        # 2. Area Bounding Box
        lbl_area = ttk.LabelFrame(
            self.left_frame, text=" Bounding Box Area (°N / °E) ", padding=8
        )
        lbl_area.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_area, text="North (Lat Max):").grid(
            row=0, column=0, sticky="e"
        )
        self.ent_north = ttk.Entry(lbl_area, width=8)
        self.ent_north.insert(0, "48.0")
        self.ent_north.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="South (Lat Min):").grid(
            row=1, column=0, sticky="e"
        )
        self.ent_south = ttk.Entry(lbl_area, width=8)
        self.ent_south.insert(0, "43.5")
        self.ent_south.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="West (Lon Min):").grid(
            row=2, column=0, sticky="e"
        )
        self.ent_west = ttk.Entry(lbl_area, width=8)
        self.ent_west.insert(0, "5.0")
        self.ent_west.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(lbl_area, text="East (Lon Max):").grid(
            row=3, column=0, sticky="e"
        )
        self.ent_east = ttk.Entry(lbl_area, width=8)
        self.ent_east.insert(0, "16.0")
        self.ent_east.grid(row=3, column=1, padx=5, pady=2)

        self.btn_select_map = ttk.Button(
            lbl_area,
            text="📍 Seleziona su Mappa (2 Click)",
            command=self.enable_map_selection,
        )
        self.btn_select_map.grid(
            row=4, column=0, columnspan=2, pady=3, sticky="ew"
        )

        self.btn_update_map = ttk.Button(
            lbl_area,
            text="🔄 Aggiorna Rettangolo",
            command=self.draw_bbox_on_map,
        )
        self.btn_update_map.grid(
            row=5, column=0, columnspan=2, pady=2, sticky="ew"
        )

        # 3. Variabili
        self.lbl_vars = ttk.LabelFrame(
            self.left_frame, text=" Variabili Selezionate ", padding=8
        )
        self.lbl_vars.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(self.lbl_vars)
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(
            btn_frame,
            text="Tutte",
            command=lambda: [
                v.set(True) for v in self.var_checks.values()
            ],
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="Nessuna",
            command=lambda: [
                v.set(False) for v in self.var_checks.values()
            ],
        ).pack(side=tk.LEFT, padx=2)

        self.vars_container = ttk.Frame(self.lbl_vars)
        self.vars_container.pack(fill=tk.X, pady=4)

        # 4. Range Temporale
        lbl_time = ttk.LabelFrame(
            self.left_frame, text=" Range Temporale ", padding=8
        )
        lbl_time.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_time, text="Ore Passate:").grid(
            row=0, column=0, sticky="e"
        )
        self.ent_start_h = ttk.Entry(lbl_time, width=6)
        self.ent_start_h.insert(0, "-18")
        self.ent_start_h.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(lbl_time, text="Ore Future:").grid(
            row=1, column=0, sticky="e"
        )
        self.ent_end_h = ttk.Entry(lbl_time, width=6)
        self.ent_end_h.insert(0, "120")
        self.ent_end_h.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(lbl_time, text="Passo Orario (h):").grid(
            row=2, column=0, sticky="e"
        )
        self.ent_step_h = ttk.Entry(lbl_time, width=6)
        self.ent_step_h.insert(0, "3")
        self.ent_step_h.grid(row=2, column=1, padx=5, pady=2)

        # 5. Output
        lbl_out = ttk.LabelFrame(self.left_frame, text=" Output ", padding=8)
        lbl_out.pack(fill=tk.X, pady=5)

        ttk.Label(lbl_out, text="Cartella di Destinazione:").pack(anchor="w")
        dir_frame = ttk.Frame(lbl_out)
        dir_frame.pack(fill=tk.X, pady=2)

        self.ent_dir_path = ttk.Entry(dir_frame)
        self.ent_dir_path.insert(0, os.getcwd())
        self.ent_dir_path.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2)
        )

        btn_browse = ttk.Button(
            dir_frame, text="Sfoglia...", command=self.browse_directory
        )
        btn_browse.pack(side=tk.RIGHT)

        ttk.Label(lbl_out, text="Nome File Output:").pack(
            anchor="w", pady=(5, 0)
        )
        self.ent_out_name = ttk.Entry(lbl_out)
        self.ent_out_name.insert(0, "custom_weather.grb2")
        self.ent_out_name.pack(fill=tk.X, pady=2)

        # 6. Esecuzione & Visualizzatori
        lbl_action = ttk.LabelFrame(
            self.left_frame, text=" Esecuzione & Visualizzazione ", padding=8
        )
        lbl_action.pack(fill=tk.X, pady=5)
        self.btn_download = ttk.Button(
            lbl_action,
            text="⚡ AVVIA DOWNLOAD GRIB2",
            command=self.start_download_thread,
        )
        self.btn_download.pack(fill=tk.X, pady=3)

        self.btn_grads = ttk.Button(
            lbl_action,
            text="📊 VISUALIZZA IN GRADS",
            command=self.apri_in_grads,
            state=tk.DISABLED,
        )
        self.btn_grads.pack(fill=tk.X, pady=3)

        self.btn_xygrib = ttk.Button(
            lbl_action,
            text="🌍 APRI IN XYGRIB",
            command=self.apri_in_xygrib,
            state=tk.DISABLED,
        )
        self.btn_xygrib.pack(fill=tk.X, pady=3)

        self.progress = ttk.Progressbar(
            lbl_action, orient="horizontal", mode="determinate"
        )
        self.progress.pack(fill=tk.X, pady=4)
        self.lbl_status = ttk.Label(
            lbl_action, text="Stato: In attesa...", foreground="gray"
        )
        self.lbl_status.pack(anchor="w", pady=2)

    def browse_directory(self):
        selected_dir = filedialog.askdirectory(
            initialdir=self.ent_dir_path.get()
        )
        if selected_dir:
            self.ent_dir_path.delete(0, tk.END)
            self.ent_dir_path.insert(0, selected_dir)
            print(f"[DEBUG] Cartella output impostata: {selected_dir}")

    def set_widgets_state(self, state):
        entries = [
            self.ent_north,
            self.ent_south,
            self.ent_west,
            self.ent_east,
            self.ent_start_h,
            self.ent_end_h,
            self.ent_step_h,
        ]
        for e in entries:
            e.config(state=state)

        btn_state = tk.NORMAL if state == "normal" else tk.DISABLED
        self.btn_select_map.config(state=btn_state)
        self.btn_update_map.config(state=btn_state)

    def on_model_change(self, event=None):
        model_name = self.cmb_model.get()
        print(f"[DEBUG] Modello selezionato: {model_name}")

        if "ICON-EU" in model_name:
            self.set_widgets_state("normal")

            self.ent_start_h.delete(0, tk.END)
            self.ent_start_h.insert(0, "0")
            self.ent_end_h.delete(0, tk.END)
            self.ent_end_h.insert(0, "48")
            self.ent_step_h.delete(0, tk.END)
            self.ent_step_h.insert(0, "3")

            self.ent_north.delete(0, tk.END)
            self.ent_north.insert(0, "70.0")
            self.ent_south.delete(0, tk.END)
            self.ent_south.insert(0, "29.5")
            self.ent_west.delete(0, tk.END)
            self.ent_west.insert(0, "-23.5")
            self.ent_east.delete(0, tk.END)
            self.ent_east.insert(0, "45.0")

            self.set_widgets_state("disabled")
            self.draw_bbox_on_map()
        else:
            self.set_widgets_state("normal")
            self.ent_start_h.delete(0, tk.END)
            self.ent_start_h.insert(0, "-18")
            self.ent_end_h.delete(0, tk.END)
            self.ent_end_h.insert(0, "120")
            self.ent_step_h.delete(0, tk.END)
            self.ent_step_h.insert(0, "3")

            self.ent_north.delete(0, tk.END)
            self.ent_north.insert(0, "48.0")
            self.ent_south.delete(0, tk.END)
            self.ent_south.insert(0, "43.5")
            self.ent_west.delete(0, tk.END)
            self.ent_west.insert(0, "5.0")
            self.ent_east.delete(0, tk.END)
            self.ent_east.insert(0, "16.0")
            self.draw_bbox_on_map()

        self.update_variable_checkboxes()

    def update_variable_checkboxes(self):
        for widget in self.vars_container.winfo_children():
            widget.destroy()

        self.var_checks.clear()

        target_dict = GFS_VARS if "GFS" in self.cmb_model.get() else ICON_VARS
        print(f"[DEBUG] Generazione Checkbox per {len(target_dict)} variabili.")

        for name in target_dict.keys():
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.vars_container, text=name, variable=var)
            chk.pack(anchor="w", pady=2)
            self.var_checks[name] = var

        # Forza il ricalcolo delle dimensioni della scrollbar
        self.left_frame.update_idletasks()
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _build_map(self):
        self.map_widget = tkintermapview.TkinterMapView(
            self.right_frame, width=800, height=600, corner_radius=0
        )
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        self.map_widget.set_position(45.8, 10.5)
        self.map_widget.set_zoom(5)
        self.map_widget.add_left_click_map_command(self.on_map_click)
        self.root.after(500, self.draw_bbox_on_map)

    def enable_map_selection(self):
        if "ICON-EU" in self.cmb_model.get():
            return
        self.click_step = 1
        self.click_coords.clear()
        if self.temp_marker:
            self.temp_marker.delete()
            self.temp_marker = None

        self.btn_select_map.config(text="Click 1/2: Seleziona Nord-Ovest")
        self.lbl_status.config(
            text="Fai click sulla mappa per l'angolo Nord-Ovest...",
            foreground="blue",
        )
        print("[DEBUG] Modalita selezione mappa attivata: Attesa Click 1.")

    def on_map_click(self, coords):
        print(f"[DEBUG] Click rilevato su mappa: Lat={coords[0]}, Lon={coords[1]}")
        if "ICON-EU" in self.cmb_model.get():
            return

        if self.click_step == 1:
            self.click_coords.append(coords)
            if self.temp_marker:
                self.temp_marker.delete()

            self.temp_marker = self.map_widget.set_marker(
                coords[0], coords[1], text="Punto NW"
            )
            self.click_step = 2
            self.btn_select_map.config(text="Click 2/2: Seleziona Sud-Est")
            self.lbl_status.config(
                text="Fai click sulla mappa per l'angolo Sud-Est...",
                foreground="blue",
            )
            print("[DEBUG] Registrato Punto 1. Attesa Click 2.")

        elif self.click_step == 2:
            self.click_coords.append(coords)
            p1, p2 = self.click_coords[0], self.click_coords[1]
            north, south = max(p1[0], p2[0]), min(p1[0], p2[0])
            west, east = min(p1[1], p2[1]), max(p1[1], p2[1])

            self.ent_north.delete(0, tk.END)
            self.ent_north.insert(0, f"{north:.2f}")
            self.ent_south.delete(0, tk.END)
            self.ent_south.insert(0, f"{south:.2f}")
            self.ent_west.delete(0, tk.END)
            self.ent_west.insert(0, f"{west:.2f}")
            self.ent_east.delete(0, tk.END)
            self.ent_east.insert(0, f"{east:.2f}")

            if self.temp_marker:
                self.temp_marker.delete()
                self.temp_marker = None

            self.click_step = 0
            self.btn_select_map.config(text="📍 Seleziona su Mappa (2 Click)")
            self.lbl_status.config(
                text="Area aggiornata con successo!", foreground="green"
            )
            print(f"[DEBUG] Bounding box impostato: N={north:.2f}, S={south:.2f}, W={west:.2f}, E={east:.2f}")
            self.draw_bbox_on_map()

    def draw_bbox_on_map(self):
        try:
            north, south = float(self.ent_north.get()), float(
                self.ent_south.get()
            )
            west, east = float(self.ent_west.get()), float(self.ent_east.get())

            if self.rect_map:
                self.rect_map.delete()
                self.rect_map = None

            polygon_path = [
                (north, west),
                (north, east),
                (south, east),
                (south, west),
            ]

            # Disegna il rettangolo rosso
            self.rect_map = self.map_widget.set_polygon(
                polygon_path,
                outline_color="#d62728",
                fill_color="#ff4136",
                border_width=2,
            )
            print("[DEBUG] Rettangolo Bounding Box ridisegnato sulla mappa.")
        except ValueError as err:
            print(f"[DEBUG] Errore conversione coordinate Bounding Box: {err}")

    def start_download_thread(self):
        threading.Thread(target=self.run_download, daemon=True).start()

    def run_download(self):
        try:
            self.btn_download.config(state=tk.DISABLED)

            # NOTIFICA IMMEDIATA ALL'UTENTE
            self.lbl_status.config(
                text="Dati in preparazione sul server (verifica run e coordinate)...",
                foreground="blue"
            )
            self.root.update_idletasks()
            print("[DOWNLOAD STATUS] Dati in preparazione sul server...")

            selected_model = self.cmb_model.get()

            target_dir = self.ent_dir_path.get().strip()
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            output_filename = self.ent_out_name.get().strip()
            if not output_filename.endswith(".grb2"):
                output_filename += ".grb2"

            selected_vars = [
                name
                for name, is_sel in self.var_checks.items()
                if is_sel.get()
            ]

            if not selected_vars:
                messagebox.showwarning(
                    "Attenzione", "Seleziona almeno una variabile!"
                )
                self.lbl_status.config(
                    text="Nessuna variabile selezionata.", foreground="red"
                )
                return

            def update_progress(val, max_val):
                self.progress["maximum"] = max_val
                self.progress["value"] = val

            def update_status(text):
                self.lbl_status.config(text=text, foreground="black")
                print(f"[DOWNLOAD STATUS] {text}")

            if "GFS" in selected_model:
                downloaded_buffers = GfsDownloader.download_gfs(
                    north=float(self.ent_north.get()),
                    south=float(self.ent_south.get()),
                    west=float(self.ent_west.get()),
                    east=float(self.ent_east.get()),
                    start_h=int(self.ent_start_h.get()),
                    end_h=int(self.ent_end_h.get()),
                    step_h=int(self.ent_step_h.get()),
                    selected_vars=selected_vars,
                    progress_callback=update_progress,
                    status_callback=update_status,
                )
            else:
                downloaded_buffers = IconEuDownloader.download_icon_eu(
                    selected_vars=selected_vars,
                    progress_callback=update_progress,
                    status_callback=update_status,
                )

            if downloaded_buffers:
                out_path = os.path.join(target_dir, output_filename)
                with open(out_path, "wb") as outfile:
                    for buf in downloaded_buffers:
                        outfile.write(buf)

                size_mb = os.path.getsize(out_path) / (1024 * 1024)

                self.last_downloaded_file = out_path
                self.btn_grads.config(state=tk.NORMAL)
                self.btn_xygrib.config(state=tk.NORMAL)

                self.lbl_status.config(
                    text=f"Completato! ({size_mb:.2f} MB)", foreground="green"
                )
                print(f"[DEBUG] Download completato e salvato in {out_path} ({size_mb:.2f} MB)")
                messagebox.showinfo(
                    "Successo",
                    f"File salvato con successo:\n{out_path}\n\nDimensione:"
                    f" {size_mb:.2f} MB",
                )
            else:
                self.lbl_status.config(
                    text="Download fallito.", foreground="red"
                )
                messagebox.showerror(
                    "Errore", "Impossibile scaricare i dati GRIB2."
                )
        except Exception as ex:
            print(f"[DEBUG] Errore durante il download: {ex}")
            messagebox.showerror("Errore", str(ex))
            self.lbl_status.config(
                text="Errore durante il download.", foreground="red"
            )
        finally:
            self.btn_download.config(state=tk.NORMAL)

    def apri_in_grads(self):
        if not self.last_downloaded_file or not os.path.exists(
            self.last_downloaded_file
        ):
            messagebox.showerror(
                "Errore File", "Nessun file GRIB2 scaricato da visualizzare."
            )
            return

        try:
            print(f"[DEBUG] Invocazione GrADS per {self.last_downloaded_file}")
            self.lbl_status.config(
                text="Apertura GrADS in corso...", foreground="blue"
            )
            self.root.update_idletasks()

            GradsHandler.visualizza_in_grads(self.last_downloaded_file)

            self.lbl_status.config(
                text="Display GrADS attivato.", foreground="green"
            )
        except subprocess.CalledProcessError as err:
            err_msg = (
                err.stderr.decode("utf-8", errors="ignore")
                if err.stderr
                else str(err)
            )
            print(f"[DEBUG] Errore g2ctl/gribmap: {err_msg}")
            messagebox.showerror(
                "Errore GrADS Processing",
                f"Errore durante l'esecuzione di g2ctl o gribmap.\n\nDettaglio:\n{err_msg}",
            )
            self.lbl_status.config(
                text="Errore preparazione GrADS.", foreground="red"
            )
        except Exception as e:
            print(f"[DEBUG] Errore avvio GrADS: {e}")
            messagebox.showerror(
                "Errore Avvio", f"Impossibile avviare GrADS:\n{e}"
            )
            self.lbl_status.config(text="Errore GrADS.", foreground="red")

    def apri_in_xygrib(self):
        if not self.last_downloaded_file or not os.path.exists(
            self.last_downloaded_file
        ):
            messagebox.showerror(
                "Errore File", "Nessun file GRIB2 scaricato da visualizzare."
            )
            return

        try:
            print(f"[DEBUG] Invocazione XyGrib per {self.last_downloaded_file}")
            self.lbl_status.config(
                text="Apertura in XyGrib...", foreground="blue"
            )
            self.root.update_idletasks()

            XyGribHandler.apri_in_xygrib(self.last_downloaded_file)

            self.lbl_status.config(
                text="XyGrib avviato.", foreground="green"
            )
        except Exception as e:
            print(f"[DEBUG] Errore avvio XyGrib: {e}")
            messagebox.showerror(
                "Errore XyGrib", f"Impossibile avviare XyGrib:\n{e}"
            )
            self.lbl_status.config(text="Errore XyGrib.", foreground="red")