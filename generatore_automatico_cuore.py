import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
import platform
import subprocess

# --- COMPATIBILITÀ MACOS (RISOLUZIONE BLOCCO COLORI BOTTONI APPLE) ---
IS_MAC = platform.system() == "Darwin"
HAS_TKMACOSX = False
if IS_MAC:
    try:
        from tkmacosx import Button as CyberButton
        HAS_TKMACOSX = True
    except ImportError:
        CyberButton = tk.Button # Bottone di riserva
else:
    CyberButton = tk.Button

# --- COSTANTI PALETTE CYBERPUNK ---
BG_DARK = "#06070B"       # Nero profondo cyber
BG_PANEL = "#0F111A"      # Sfondo dei pannelli (ossidiana)
NEON_CYAN = "#00F0FF"     # Celeste neon splendente
NEON_PINK = "#FF007F"     # Rosa neon / Magenta acido
NEON_YELLOW = "#FCEE09"   # Giallo Cyberpunk 2077
TEXT_WHITE = "#FFFFFF"    # Testo chiaro principale
TEXT_GRAY = "#7E8B9B"     # Testo disattivato/secondario

class MockupAppPro:
    def __init__(self, root):
        self.root = root
        self.root.title("MOCKUPPER // Generatore Mockup HD Pro")
        self.root.geometry("1280x850")
        self.root.minsize(1200, 800)
        self.root.resizable(True, True)
        self.root.configure(bg=BG_DARK)
        
        if IS_MAC and not HAS_TKMACOSX:
            messagebox.showinfo("Miglioramento Grafica Mac", 
                                "Per vedere i pulsanti in stile Cyberpunk su macOS apri il Terminale e digita:\n\npip install tkmacosx\n\n(Il programma funzionerà lo stesso anche senza, ma la grafica dei pulsanti sarà quella standard grigia).")

        self.cartella_interna = self.resource_path("modelli_magliette")
        self.doc_path = Path.home() / "Documents" / "MieiMockupMagliette"
        self.cartella_esterna = str(self.doc_path)
        os.makedirs(self.cartella_esterna, exist_ok=True)
        
        self.mappa_modelli = {}
        self.preview_size = 400
        self.current_scale = 1.0  
        self.img_left = 0         
        self.img_top = 0          
        self.offset_x = None 
        self.offset_y = None  
        self.resize_width = 150 
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.soglia_calamita = 25 
        self.snap_verticale = tk.BooleanVar(value=True)
        self.snap_orizzontale = tk.BooleanVar(value=True)
        self.snap_cuore = tk.BooleanVar(value=True)
        self.soglia_var = tk.IntVar(value=25)
        self.base_resize_width = self.resize_width
        self.resize_percent = tk.IntVar(value=100)
        
        self.sfondo_trasparente = tk.BooleanVar(value=False)
        self.rimuovi_sfondo_maglietta = tk.BooleanVar(value=False)

        self.file_singolo = ""
        self.cartella_batch = ""
        self.recent_images = []

        self.carica_colori()
        self.setup_styles()
        
        self.outer_frame = tk.Frame(self.root, bg=BG_DARK, bd=2, relief="solid", highlightbackground=NEON_CYAN)
        self.outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.home_frame = tk.Frame(self.outer_frame, bg=BG_DARK)
        self.workspace_frame = tk.Frame(self.outer_frame, bg=BG_DARK)

        self.setup_home_ui()
        self.setup_ui()
        self.show_home()

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def carica_colori(self):
        self.mappa_modelli = {}
        if os.path.exists(self.cartella_interna):
            for file in os.listdir(self.cartella_interna):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    nome_colore = os.path.splitext(file)[0].capitalize()
                    self.mappa_modelli[nome_colore] = os.path.join(self.cartella_interna, file)
                    
        if os.path.exists(self.cartella_esterna):
            for file in os.listdir(self.cartella_esterna):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    nome_colore = os.path.splitext(file)[0].capitalize()
                    self.mappa_modelli[nome_colore] = os.path.join(self.cartella_esterna, file)
        
        self.colori_reali = sorted(list(self.mappa_modelli.keys()))
        self.opzioni_colore = ["Tutti i colori"] + self.colori_reali

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("TCombobox", fieldbackground=BG_PANEL, background=BG_DARK, foreground=NEON_CYAN,
                             darkcolor=BG_DARK, lightcolor=BG_DARK, arrowcolor=NEON_CYAN, bordercolor=NEON_CYAN,
                             font=("Consolas", 10, "bold"))
        self.style.map("TCombobox", fieldbackground=[("readonly", BG_PANEL)], selectbackground=[("readonly", BG_PANEL)],
                       selectforeground=[("readonly", NEON_CYAN)], background=[("readonly", BG_DARK)])
        
        self.root.option_add("*TCombobox*Listbox.background", BG_PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", NEON_CYAN)
        self.root.option_add("*TCombobox*Listbox.selectBackground", NEON_CYAN)
        self.root.option_add("*TCombobox*Listbox.selectForeground", BG_DARK)
        self.root.option_add("*TCombobox*Listbox.font", ("Consolas", 10, "bold"))

        self.style.configure("TRadiobutton", background=BG_PANEL, foreground=TEXT_WHITE, font=("Consolas", 10, "bold"),
                             indicatorcolor=BG_DARK, focuscolor=BG_PANEL)
        self.style.map("TRadiobutton", foreground=[("selected", NEON_CYAN), ("active", NEON_CYAN)],
                       background=[("selected", BG_PANEL), ("active", BG_PANEL)])

        self.style.configure("TProgressbar", troughcolor=BG_DARK, background=NEON_PINK, bordercolor=NEON_CYAN,
                             lightcolor=NEON_PINK, darkcolor=NEON_PINK)

    def create_neon_button(self, parent, text, command, color=NEON_CYAN, width=None):
        kwargs = {
            "bg": BG_DARK, "fg": color, "activebackground": color, "activeforeground": BG_DARK,
            "font": ("Consolas", 10, "bold"), "bd": 1, "relief": "solid", "cursor": "hand2"
        }
        if HAS_TKMACOSX:
            kwargs["borderless"] = 1
        else:
            kwargs["highlightbackground"] = color
            kwargs["highlightcolor"] = color
            kwargs["padx"] = 12
            kwargs["pady"] = 6
            
        btn = CyberButton(parent, text=text, command=command, **kwargs)
        if width:
            btn.config(width=width)
        
        btn.bind("<Enter>", lambda e: btn.config(bg=color, fg=BG_DARK))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG_DARK, fg=color))
        return btn

    def create_cyber_check(self, parent, text, variable):
        cb = tk.Checkbutton(parent, text=text, variable=variable, bg=BG_PANEL, fg=TEXT_WHITE, 
                            activebackground=BG_PANEL, activeforeground=NEON_CYAN, selectcolor=BG_DARK,
                            font=("Consolas", 9, "bold"), relief="flat", bd=0, cursor="hand2")
        return cb

    def show_home(self):
        self.workspace_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)
        self.carica_anteprime_home()

    def show_workspace(self):
        self.home_frame.pack_forget()
        self.workspace_frame.pack(fill="both", expand=True)
        self.aggiorna_anteprima()

    def setup_home_ui(self):
        left_menu = tk.Frame(self.home_frame, bg=BG_PANEL, bd=1, relief="solid", highlightbackground="#1E1F29", width=400)
        left_menu.pack(side="left", fill="both", expand=False)
        left_menu.pack_propagate(False)

        right_gallery = tk.Frame(self.home_frame, bg=BG_DARK)
        right_gallery.pack(side="left", fill="both", expand=True, padx=25, pady=20)

        brand_frame = tk.Frame(left_menu, bg=BG_PANEL)
        brand_frame.pack(fill="x", pady=(40, 20), padx=20)

        title_top = tk.Label(brand_frame, text="M O C K U P P E R", bg=BG_PANEL, fg=NEON_PINK, font=("Consolas", 26, "bold"))
        title_top.pack(anchor="w")
        title_bot = tk.Label(brand_frame, text="S Y S T E M", bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 24, "bold"))
        title_bot.pack(anchor="w")
        
        lbl_ver = tk.Label(brand_frame, text="SYSTEM v3.0 // CYBERPUNK PORTAL", bg=BG_PANEL, fg=TEXT_GRAY, font=("Consolas", 8, "bold"))
        lbl_ver.pack(anchor="w", pady=(5, 0))

        sep = tk.Frame(left_menu, height=2, bg=NEON_CYAN)
        sep.pack(fill="x", pady=20, padx=20)

        lbl_welcome = tk.Label(left_menu, text=">>> INITIALIZE MOCKUPPER CORE", bg=BG_PANEL, fg=NEON_YELLOW, font=("Consolas", 9, "bold"))
        lbl_welcome.pack(anchor="w", padx=20, pady=(0, 20))

        btn_new = self.create_neon_button(left_menu, "[ + ] NUOVO PROGETTO", self.show_workspace, color=NEON_CYAN)
        btn_new.pack(fill="x", padx=20, pady=8)

        btn_open = self.create_neon_button(left_menu, "[ 📂 ] APRI FILE DISEGNO", self.sfoglia_e_apri, color=NEON_PINK)
        btn_open.pack(fill="x", padx=20, pady=8)

        btn_docs = self.create_neon_button(left_menu, "[ 📁 ] CARTELLE ASSETS", self.apri_cartella_os, color=NEON_YELLOW)
        btn_docs.pack(fill="x", padx=20, pady=8)

        lbl_credits = tk.Label(left_menu, text="CORE PROTOCOL // ONLINE\nSECURE CONNECTION", bg=BG_PANEL, fg=TEXT_GRAY, font=("Consolas", 8), justify="center")
        lbl_credits.pack(side="bottom", pady=25)

        gallery_header = tk.Frame(right_gallery, bg=BG_DARK)
        gallery_header.pack(fill="x", pady=(10, 15))

        lbl_gallery_title = tk.Label(gallery_header, text="PROGETTI RECENTI & ANTEPRIME", bg=BG_DARK, fg=NEON_PINK, font=("Consolas", 14, "bold"), anchor="w")
        lbl_gallery_title.pack(side="left")

        lbl_gallery_hint = tk.Label(gallery_header, text="[CLICCA SULL'ANTEPRIMA PER MODIFICARE]", bg=BG_DARK, fg=TEXT_GRAY, font=("Consolas", 8, "italic"))
        lbl_gallery_hint.pack(side="right", pady=5)

        self.recent_grid = tk.Frame(right_gallery, bg=BG_DARK)
        self.recent_grid.pack(fill="both", expand=True)

    def carica_anteprime_home(self):
        for child in self.recent_grid.winfo_children():
            child.destroy()
        self.recent_images.clear()

        all_files = []
        if os.path.exists(self.cartella_esterna):
            for file in os.listdir(self.cartella_esterna):
                if file.lower().endswith((".png", ".jpg", ".jpeg")) and not file.startswith("._"):
                    all_files.append(os.path.join(self.cartella_esterna, file))

            for root_dir, dirs, files in os.walk(self.cartella_esterna):
                for file in files:
                    if file.lower().endswith((".png", ".jpg", ".jpeg")) and not file.startswith("._"):
                        full_p = os.path.join(root_dir, file)
                        if full_p not in all_files:
                            all_files.append(full_p)

        all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        recent_files = all_files[:9]

        if not recent_files:
            lbl_empty = tk.Label(self.recent_grid, text="[ NESSUNA ANTEPRIMA RILEVATA NEL SYSTEM ]\n\nI tuoi lavori salvati appariranno qui automaticamente.\nUtilizza la cartella Documenti per caricare file di design o template base.",
                                 bg=BG_DARK, fg=TEXT_GRAY, font=("Consolas", 10), justify="center")
            lbl_empty.pack(expand=True, fill="both", pady=100)
            return

        for i, filepath in enumerate(recent_files):
            row = i // 3
            col = i % 3

            card = tk.Frame(self.recent_grid, bg=BG_PANEL, bd=1, relief="solid", highlightbackground="#1E1F29", padx=10, pady=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            try:
                img = Image.open(filepath)
                img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.recent_images.append(tk_img)

                img_lbl = tk.Label(card, image=tk_img, bg=BG_DARK, cursor="hand2")
                img_lbl.pack()

                filename = os.path.basename(filepath)
                if len(filename) > 18:
                    filename = filename[:15] + "..."
                text_lbl = tk.Label(card, text=filename, bg=BG_PANEL, fg=TEXT_WHITE, font=("Helvetica", 8, "bold"), cursor="hand2")
                text_lbl.pack(pady=(8, 0))

                for widget in (card, img_lbl, text_lbl):
                    widget.bind("<Button-1>", lambda e, path=filepath: self.carica_file_recente(path))

            except Exception as e:
                print(f"Impossibile renderizzare miniatura per {filepath}: {e}")

    def sfoglia_e_apri(self):
        self.sfoglia()
        if self.file_singolo or self.cartella_batch:
            self.show_workspace()

    def carica_file_recente(self, path):
        if os.path.isdir(path):
            self.cartella_batch = path
            self.modo_var.set("batch")
            trovati = len([f for f in os.listdir(path) if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("._")])
            self.lbl_stato.config(text=f"Cartella: {os.path.basename(path)} ({trovati} file Trovati)")
            self.btn_esporta.config(state="normal" if trovati > 0 else "disabled")
        else:
            self.file_singolo = path
            self.modo_var.set("singolo")
            self.lbl_stato.config(text=f"File: {os.path.basename(path)}")
            self.btn_esporta.config(state="normal")

        self.show_workspace()
        self.aggiorna_anteprima()

    def setup_ui(self):
        if not self.colori_reali:
            err_frame = tk.Frame(self.workspace_frame, bg=BG_DARK)
            err_frame.pack(fill="both", expand=True)
            tk.Label(err_frame, text="!!! SYSTEM CRITICAL ERROR !!!\n\nNessun modello base trovato.\nCrea o copia immagini mockup base in:\n" + self.cartella_esterna,
                     fg=NEON_PINK, bg=BG_DARK, font=("Consolas", 12, "bold"), justify="center").pack(expand=True)
            return

        header_ws = tk.Frame(self.workspace_frame, bg=BG_PANEL, bd=1, relief="solid", highlightbackground="#1E1F29")
        header_ws.pack(fill="x", pady=(0, 15), ipady=5)

        lbl_title_ws = tk.Label(header_ws, text="MOCKUPPER // WORKSPACE EDITOR", bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 13, "bold"))
        lbl_title_ws.pack(side="left", padx=15)

        btn_home_nav = self.create_neon_button(header_ws, "<- TORNA ALLA HOME", self.show_home, color=NEON_PINK)
        btn_home_nav.pack(side="right", padx=15)

        columns_container = tk.Frame(self.workspace_frame, bg=BG_DARK)
        columns_container.pack(fill="both", expand=True)

        left_col = tk.Frame(columns_container, bg=BG_PANEL, bd=1, relief="solid", highlightbackground="#1E1F29", width=360)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_col.pack_propagate(False)

        tk.Label(left_col, text="[01] SELEZIONE MODELLO", bg=BG_PANEL, fg=NEON_PINK, font=("Consolas", 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        tk.Label(left_col, text="COLORE BASE MAGLIA:", bg=BG_PANEL, fg=TEXT_WHITE, font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        
        self.colore_selezionato = tk.StringVar()
        self.dropdown_colori = ttk.Combobox(left_col, textvariable=self.colore_selezionato, values=self.opzioni_colore, state="readonly")
        self.dropdown_colori.pack(fill="x", padx=15, pady=(0, 10))
        self.dropdown_colori.current(0)
        self.dropdown_colori.bind("<<ComboboxSelected>>", self.aggiorna_anteprima)

        btn_open_ext = self.create_neon_button(left_col, "APRI CARTELLE MODELLI (OS)", self.apri_cartella_os, color=NEON_CYAN)
        btn_open_ext.pack(fill="x", padx=15, pady=(0, 20))

        tk.Label(left_col, text="[02] CALAMITE & ASSISTENTI", bg=BG_PANEL, fg=NEON_PINK, font=("Consolas", 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(5, 5))
        
        cb_vert = self.create_cyber_check(left_col, "Calamita Centro Verticale", self.snap_verticale)
        cb_vert.pack(anchor="w", padx=15, pady=2)
        cb_vert.config(command=self.aggiorna_anteprima)

        cb_horiz = self.create_cyber_check(left_col, "Calamita Centro Orizzontale", self.snap_orizzontale)
        cb_horiz.pack(anchor="w", padx=15, pady=2)
        cb_horiz.config(command=self.aggiorna_anteprima)

        cb_heart = self.create_cyber_check(left_col, "Calamita Lato Cuore", self.snap_cuore)
        cb_heart.pack(anchor="w", padx=15, pady=2)
        cb_heart.config(command=self.aggiorna_anteprima)

        cb_scont = self.create_cyber_check(left_col, "Scontorna Maglia (Buca Sfondo)", self.rimuovi_sfondo_maglietta)
        cb_scont.pack(anchor="w", padx=15, pady=(5, 10))
        cb_scont.config(command=self.aggiorna_anteprima)

        tk.Label(left_col, text="FORZA SOGLIA CALAMITA (PX):", bg=BG_PANEL, fg=TEXT_WHITE, font=("Consolas", 8, "bold"), anchor="w").pack(fill="x", padx=15, pady=(8, 2))
        self.scale_soglia = tk.Scale(left_col, from_=0, to=50, orient="horizontal", variable=self.soglia_var,
                                     bg=BG_PANEL, fg=TEXT_WHITE, troughcolor=BG_DARK, activebackground=NEON_CYAN,
                                     highlightbackground=BG_PANEL, relief="flat", font=("Consolas", 8),
                                     command=lambda e: setattr(self, "soglia_calamita", self.soglia_var.get()))
        self.scale_soglia.pack(fill="x", padx=15, pady=(0, 20))

        tk.Label(left_col, text="[03] SCALA DISEGNO / PROGETTO", bg=BG_PANEL, fg=NEON_PINK, font=("Consolas", 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(5, 5))
        
        sz_panel = tk.Frame(left_col, bg=BG_PANEL)
        sz_panel.pack(fill="x", padx=15, pady=2)
        tk.Label(sz_panel, text="VALORE PERCENTUALE: ", bg=BG_PANEL, fg=TEXT_WHITE, font=("Helvetica", 9)).pack(side="left")
        self.lbl_percent = tk.Label(sz_panel, text="100%", bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 10, "bold"))
        self.lbl_percent.pack(side="left")

        btns_resizer = tk.Frame(left_col, bg=BG_PANEL)
        btns_resizer.pack(fill="x", padx=15, pady=5)
        self.create_neon_button(btns_resizer, "-10", lambda: self.change_percent(-10), color=NEON_CYAN).pack(side="left", fill="x", expand=True, padx=1)
        self.create_neon_button(btns_resizer, "-5", lambda: self.change_percent(-5), color=NEON_CYAN).pack(side="left", fill="x", expand=True, padx=1)
        self.create_neon_button(btns_resizer, "100%", self.reset_percent, color=NEON_YELLOW).pack(side="left", fill="x", expand=True, padx=1)
        self.create_neon_button(btns_resizer, "+5", lambda: self.change_percent(5), color=NEON_CYAN).pack(side="left", fill="x", expand=True, padx=1)
        self.create_neon_button(btns_resizer, "+10", lambda: self.change_percent(10), color=NEON_CYAN).pack(side="left", fill="x", expand=True, padx=1)

        self.scale_percent = tk.Scale(left_col, from_=25, to=300, orient="horizontal", variable=self.resize_percent,
                                      bg=BG_PANEL, fg=TEXT_WHITE, troughcolor=BG_DARK, activebackground=NEON_CYAN,
                                      highlightbackground=BG_PANEL, relief="flat", font=("Consolas", 8),
                                      command=self.on_percent_change)
        self.scale_percent.pack(fill="x", padx=15, pady=10)

        mid_col = tk.Frame(columns_container, bg=BG_PANEL, bd=1, relief="solid", highlightbackground="#1E1F29")
        mid_col.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(mid_col, text="[REALTIME PREVIEW MONITOR v3]", bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(15, 10))

        canvas_neon_frame = tk.Frame(mid_col, bg=NEON_CYAN, bd=1)
        canvas_neon_frame.pack(pady=10)

        self.canvas = tk.Canvas(canvas_neon_frame, width=self.preview_size, height=self.preview_size,
                                bg="#161722", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        tk.Label(mid_col, text="<<< Trascina per spostare // Rotellina per scalare >>>", bg=BG_PANEL, fg=TEXT_GRAY, font=("Helvetica", 8, "italic")).pack(pady=5)

        progress_ws = tk.Frame(mid_col, bg=BG_PANEL)
        progress_ws.pack(fill="x", side="bottom", pady=20, padx=25)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_ws, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(0, 5))

        self.lbl_progress = tk.Label(progress_ws, text="SYSTEM IDLE // PRONTO ALL'ESPORTAZIONE", bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 9, "bold"))
        self.lbl_progress.pack()

        right_col = tk.Frame(columns_container, bg=BG_PANEL, bd=1, relief="solid", highlightbackground="#1E1F29", width=360)
        right_col.pack(side="left", fill="both", expand=False, padx=(10, 0))
        right_col.pack_propagate(False)

        tk.Label(right_col, text="[04] STRATEGIA DI PROGETTO", bg=BG_PANEL, fg=NEON_PINK, font=("Consolas", 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(15, 5))

        self.modo_var = tk.StringVar(value="singolo")
        radio_box = tk.Frame(right_col, bg=BG_PANEL)
        radio_box.pack(fill="x", padx=15, pady=5)

        r_singolo = ttk.Radiobutton(radio_box, text="Singolo Disegno", variable=self.modo_var, value="singolo", command=self.cambia_modo)
        r_singolo.pack(side="left", expand=True, anchor="w", padx=5)

        r_batch = ttk.Radiobutton(radio_box, text="Batch Cartella", variable=self.modo_var, value="batch", command=self.cambia_modo)
        r_batch.pack(side="left", expand=True, anchor="w", padx=5)

        terminal_status_box = tk.Frame(right_col, bg=BG_DARK, bd=1, relief="solid", highlightbackground="#252735", padx=10, pady=10)
        terminal_status_box.pack(fill="x", padx=15, pady=10)

        self.lbl_stato = tk.Label(terminal_status_box, text=">>> NESSUN DISEGNO RILEVATO <<<", bg=BG_DARK, fg=NEON_YELLOW, font=("Consolas", 9, "bold"), wraplength=290)
        self.lbl_stato.pack(fill="x")

        btn_browse_design = self.create_neon_button(right_col, "CARICA IMMAGINE O CARTELLE BATCH", self.sfoglia, color=NEON_CYAN)
        btn_browse_design.pack(fill="x", padx=15, pady=(5, 20))

        tk.Label(right_col, text="[05] STRATEGIA ESPORTAZIONE", bg=BG_PANEL, fg=NEON_PINK, font=("Consolas", 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(5, 5))
        tk.Label(right_col, text="FORMATO FILE DI SALVATAGGIO:", bg=BG_PANEL, fg=TEXT_WHITE, font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        
        self.formato_var = tk.StringVar(value="PNG")
        self.combo_formato = ttk.Combobox(right_col, textvariable=self.formato_var, values=["PNG", "JPG", "WEBP"], state="readonly")
        self.combo_formato.pack(fill="x", padx=15, pady=(0, 10))

        cb_transparency = self.create_cyber_check(right_col, "Mantieni Sfondo Trasparente\n(Funzionale solo su PNG/WEBP)", self.sfondo_trasparente)
        cb_transparency.pack(anchor="w", padx=15, pady=5)

        kwargs_esporta = {
            "text": "AVVIA ESPORTAZIONE // RENDER", "bg": BG_DARK, "fg": NEON_YELLOW,
            "activebackground": NEON_YELLOW, "activeforeground": BG_DARK,
            "font": ("Consolas", 11, "bold"), "bd": 2, "relief": "solid",
            "command": self.esegui_esportazione, "state": "disabled",
            "cursor": "hand2"
        }
        if HAS_TKMACOSX:
            kwargs_esporta["borderless"] = 1
        else:
            kwargs_esporta["highlightbackground"] = NEON_YELLOW
            kwargs_esporta["highlightcolor"] = NEON_YELLOW
            kwargs_esporta["padx"] = 10
            kwargs_esporta["pady"] = 15

        self.btn_esporta = CyberButton(right_col, **kwargs_esporta)
        self.btn_esporta.pack(fill="x", side="bottom", padx=15, pady=20)

        self.btn_esporta.bind("<Enter>", lambda e: self.btn_esporta.config(bg=NEON_YELLOW, fg=BG_DARK) if self.btn_esporta["state"] == "normal" else None)
        self.btn_esporta.bind("<Leave>", lambda e: self.btn_esporta.config(bg=BG_DARK, fg=NEON_YELLOW) if self.btn_esporta["state"] == "normal" else None)

    def cambia_modo(self):
        self.file_singolo = ""
        self.cartella_batch = ""
        self.lbl_stato.config(text="Nessun file selezionato")
        self.btn_esporta.config(state="disabled")
        self.aggiorna_anteprima()

    def sfoglia(self):
        if self.modo_var.get() == "singolo":
            path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
            if path:
                self.file_singolo = path
                self.lbl_stato.config(text=f"File: {os.path.basename(path)}")
                self.btn_esporta.config(state="normal")
        else:
            path = filedialog.askdirectory()
            if path:
                self.cartella_batch = path
                trovati = len([f for f in os.listdir(path) if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("._")])
                self.lbl_stato.config(text=f"Cartella: {os.path.basename(path)} ({trovati} file Trovati)")
                if trovati > 0:
                    self.btn_esporta.config(state="normal")
                else:
                    self.btn_esporta.config(state="disabled")
        self.aggiorna_anteprima()

    def update_percent_ui(self):
        self.lbl_percent.config(text=f"{self.resize_percent.get()}%")

    def on_percent_change(self, value):
        self.resize_percent.set(int(float(value)))
        self.resize_width = int(self.base_resize_width * self.resize_percent.get() / 100)
        self.update_percent_ui()
        self.aggiorna_anteprima()

    def change_percent(self, delta):
        v = max(25, min(300, self.resize_percent.get() + delta))
        self.resize_percent.set(v)
        self.on_percent_change(v)

    def reset_percent(self):
        self.resize_percent.set(100)
        self.on_percent_change(100)

    def on_mouse_wheel(self, event):
        if hasattr(self, "design_item") and self.design_item:
            delta = 10 if event.delta > 0 else -10
            self.resize_width = max(30, min(1500, self.resize_width + delta))
            perc = max(25, min(500, round(self.resize_width / self.base_resize_width * 100)))
            self.resize_percent.set(perc)
            self.update_percent_ui()
            self.aggiorna_anteprima()

    def on_drag_start(self, event):
        self.drag_data["item"] = self.design_item
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag_motion(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.canvas.move(self.drag_data["item"], dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_drag_release(self, event):
        if self.drag_data["item"]:
            self.drag_data["item"] = None
            coords = self.canvas.coords(self.design_item)
            x, y = coords[0], coords[1]
            
            self.soglia_calamita = self.soglia_var.get()

            if self.snap_verticale.get():
                if abs(x - self.img_center_x) <= self.soglia_calamita: x = self.img_center_x
            if self.snap_orizzontale.get():
                if abs(y - self.img_center_y) <= self.soglia_calamita: y = self.img_center_y
            if self.snap_cuore.get():
                if abs(x - self.cuore_x) <= self.soglia_calamita: x = self.cuore_x
                if abs(y - self.cuore_y) <= self.soglia_calamita: y = self.cuore_y

            self.canvas.coords(self.design_item, x, y)
            
            self.offset_x = int((x - self.img_left) * self.current_scale)
            self.offset_y = int((y - self.img_top) * self.current_scale)

    def scontorna_mockup(self, img, tolleranza=25):
        img = img.convert("RGBA")
        colore_trasparente = (255, 255, 255, 0)
        
        ImageDraw.floodfill(img, xy=(0, 0), value=colore_trasparente, thresh=tolleranza)
        ImageDraw.floodfill(img, xy=(img.width - 1, 0), value=colore_trasparente, thresh=tolleranza)
        ImageDraw.floodfill(img, xy=(0, img.height - 1), value=colore_trasparente, thresh=tolleranza)
        ImageDraw.floodfill(img, xy=(img.width - 1, img.height - 1), value=colore_trasparente, thresh=tolleranza)
        
        return img

    def aggiorna_anteprima(self, event=None):
        self.canvas.delete("all")
        path_anteprima = None
        if self.modo_var.get() == "singolo" and self.file_singolo:
            path_anteprima = self.file_singolo
        elif self.modo_var.get() == "batch" and self.cartella_batch:
            files = [f for f in os.listdir(self.cartella_batch) if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("._")]
            if files: path_anteprima = os.path.join(self.cartella_batch, files[0])

        colore_scelto = self.colore_selezionato.get()
        colore_anteprima = self.colori_reali[0] if colore_scelto == "Tutti i colori" else colore_scelto
        if colore_anteprima not in self.mappa_modelli: return

        try:
            mockup = Image.open(self.mappa_modelli[colore_anteprima]).convert("RGBA")
            if self.rimuovi_sfondo_maglietta.get():
                mockup = self.scontorna_mockup(mockup)

            hd_w, hd_h = mockup.size
            ratio = min(self.preview_size / hd_w, self.preview_size / hd_h)
            self.current_scale = 1 / ratio
            prev_w = max(1, int(hd_w * ratio))
            prev_h = max(1, int(hd_h * ratio))
            
            if self.offset_x is None:
                self.offset_x = hd_w * 0.65
                self.offset_y = hd_h * 0.35
                
            self.img_left = (self.preview_size - prev_w) / 2
            self.img_top = (self.preview_size - prev_h) / 2
            self.img_center_x = self.img_left + (prev_w / 2)
            self.img_center_y = self.img_top + (prev_h / 2)
            self.cuore_x = self.img_left + (prev_w * 0.65)
            self.cuore_y = self.img_top + (prev_h * 0.35)

            mockup_preview = mockup.resize((prev_w, prev_h), Image.Resampling.LANCZOS)
            self.tk_mockup = ImageTk.PhotoImage(mockup_preview)
            self.canvas.create_image(self.preview_size/2, self.preview_size/2, image=self.tk_mockup, anchor="center")

            self.canvas.create_rectangle(self.cuore_x-40, self.cuore_y-40, self.cuore_x+40, self.cuore_y+40, outline="red", dash=(4,4), tags="guida")
            self.canvas.create_line(self.img_center_x, self.img_top, self.img_center_x, self.img_top+prev_h, dash=(4,4), fill="#00FFFF", tags="guida")
            self.canvas.create_line(self.img_left, self.img_center_y, self.img_left+prev_w, self.img_center_y, dash=(4,4), fill="#00FFFF", tags="guida")
            self.canvas.tag_raise("guida")

            if path_anteprima:
                design = Image.open(path_anteprima).convert("RGBA")
                w_percent = (self.resize_width / float(design.size[0]))
                h_size = int((float(design.size[1]) * float(w_percent)))
                prev_design_w = max(1, int(self.resize_width / self.current_scale))
                prev_design_h = max(1, int(h_size / self.current_scale))
                design_preview = design.resize((prev_design_w, prev_design_h), Image.Resampling.LANCZOS)
                
                self.tk_design = ImageTk.PhotoImage(design_preview)
                px = self.img_left + (self.offset_x / self.current_scale)
                py = self.img_top + (self.offset_y / self.current_scale)
                
                self.design_item = self.canvas.create_image(px, py, image=self.tk_design, anchor="center")
                self.canvas.tag_bind(self.design_item, "<ButtonPress-1>", self.on_drag_start)
                self.canvas.tag_bind(self.design_item, "<B1-Motion>", self.on_drag_motion)
                self.canvas.tag_bind(self.design_item, "<ButtonRelease-1>", self.on_drag_release)
                self.canvas.tag_bind(self.design_item, "<Enter>", lambda e: self.canvas.config(cursor="fleur"))
                self.canvas.tag_bind(self.design_item, "<Leave>", lambda e: self.canvas.config(cursor=""))
        except Exception as e:
            print(f"Errore caricamento anteprima: {e}")

    def genera_immagine_hd(self, design_path, colore):
        mockup = Image.open(self.mappa_modelli[colore]).convert("RGBA")
        if self.rimuovi_sfondo_maglietta.get():
            mockup = self.scontorna_mockup(mockup)

        formato = self.formato_var.get()
        if self.sfondo_trasparente.get() and formato != "JPG":
            risultato = mockup.copy()
        else:
            risultato = Image.new("RGBA", mockup.size, "WHITE")
            risultato.paste(mockup, (0, 0), mockup)
        
        design = Image.open(design_path).convert("RGBA")
        w_percent = (self.resize_width / float(design.size[0]))
        h_size = int((float(design.size[1]) * float(w_percent)))
        design = design.resize((self.resize_width, h_size), Image.Resampling.LANCZOS)

        pos_x = int(self.offset_x - (self.resize_width / 2))
        pos_y = int(self.offset_y - (h_size / 2))
        risultato.paste(design, (pos_x, pos_y), design)
        
        if formato == "JPG":
            return risultato.convert("RGB")
        else:
            return risultato

    def esegui_esportazione(self):
        colore_scelto = self.colore_selezionato.get()
        colori_da_processare = self.colori_reali if colore_scelto == "Tutti i colori" else [colore_scelto]
        
        formato_scelto = self.formato_var.get()
        ext = formato_scelto.lower()
        formato_pil = "JPEG" if formato_scelto == "JPG" else formato_scelto

        if self.modo_var.get() == "singolo":
            cartella_dest = filedialog.askdirectory(title="Dove salvare l'immagine?")
            if not cartella_dest: return
            
            nome_base = os.path.splitext(os.path.basename(self.file_singolo))[0]
            try:
                for col in colori_da_processare:
                    img = self.genera_immagine_hd(self.file_singolo, col)
                    nome_file = f"{nome_base}-{col.lower()}-HD.{ext}"
                    img.save(os.path.join(cartella_dest, nome_file), format=formato_pil, quality=95)
                messagebox.showinfo("Fatto", f"Immagine salvata in formato {formato_scelto} con successo!")
            except Exception as e:
                messagebox.showerror("Errore", str(e))
                
        else: 
            files = [f for f in os.listdir(self.cartella_batch) if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("._")]
            totale = len(files) * len(colori_da_processare)
            self.progress_bar["maximum"] = totale
            self.progress_var.set(0)
            self.btn_esporta.config(state="disabled")

            cartella_output = os.path.join(self.cartella_batch, f"FILE_MOCKUP_{formato_scelto}")
            os.makedirs(cartella_output, exist_ok=True)

            operazione = 0
            for file in files:
                percorso_completo = os.path.join(self.cartella_batch, file)
                nome_base = os.path.splitext(file)[0]

                for col in colori_da_processare:
                    operazione += 1
                    nome_file_output = f"{nome_base}-{col.lower()}-HD.{ext}"
                    self.lbl_progress.config(text=f"{operazione}/{totale} - {nome_file_output}")
                    self.progress_var.set(operazione)
                    self.root.update()

                    try:
                        img = self.genera_immagine_hd(percorso_completo, col)
                        img.save(os.path.join(cartella_output, nome_file_output), format=formato_pil, quality=95)
                    except Exception as e:
                        print(f"Errore su {file}: {e}")

            self.lbl_progress.config(text="Completato!")
            self.btn_esporta.config(state="normal")
            messagebox.showinfo("Fatto", f"Batch completato! Tutti i file salvati in formato {formato_scelto}.")

    def apri_cartella_os(self):
        if IS_MAC:
            subprocess.Popen(["open", self.cartella_esterna])
        elif platform.system() == "Windows":
            os.startfile(self.cartella_esterna)
        else:
            subprocess.Popen(["xdg-open", self.cartella_esterna])

if __name__ == "__main__":
    root = tk.Tk()
    app = MockupAppPro(root)
    root.mainloop()
