import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from data_manager import DataManager
from analysis_controller import AnalysisController
from version import VERSION

# Import Modules
from modules.braking_test import BrakingTest
from modules.climbing_test import ClimbingTest
# from modules.acceleration_0_60 import Acceleration060Test # REPLACED/REMOVED
from modules.acceleration_0_80 import Acceleration080Test
from modules.recovery_test import RecoveryTest # NEW COMBINED MODULE
from modules.top_speed_test import TopSpeedTest # NEW MODULE

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"Sistema de Análisis Incol - v{VERSION}")
        self.geometry("1100x850")
        # Maximize window by default
        # self.after(0, lambda: self.state("zoomed"))
        
        self.data_manager = DataManager()
        self.controller = AnalysisController()
        
        self.active_module = None
        self.moto_values_map = []
        self.lugar_values_map = []
        
        self.show_main_menu()
        
    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        self.clear_window()
        
        menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        menu_frame.place(relx=0.5, rely=0.4, anchor="center")
        
        ctk.CTkLabel(menu_frame, text="Sistema de Análisis Incol", font=("Arial", 32, "bold")).pack(pady=40)
        ctk.CTkLabel(menu_frame, text="Seleccione el tipo de programa a ejecutar:", font=("Arial", 18)).pack(pady=20)
        
        btn_font = ("Arial", 16, "bold")
        
        # Main Execution Buttons Flow
        exec_frame = ctk.CTkFrame(menu_frame, fg_color="transparent")
        exec_frame.pack(pady=10)
        
        ctk.CTkButton(exec_frame, text="Comparativo", font=btn_font, width=250, height=50, 
                      command=self.show_comparativo_view).pack(side="left", padx=10)
                      
        ctk.CTkButton(exec_frame, text="Todas las pruebas", font=btn_font, width=250, height=50, 
                      command=self.show_todas_pruebas_view).pack(side="left", padx=10)
                      
        ctk.CTkButton(exec_frame, text="Individual", font=btn_font, width=250, height=50, 
                      command=self.show_individual_view).pack(side="left", padx=10)

        # Config & Ranking Area
        secondary_frame = ctk.CTkFrame(menu_frame, fg_color="transparent")
        secondary_frame.pack(pady=10)
        
        ctk.CTkButton(secondary_frame, text="🏆 Ranking de Frenado", font=("Arial", 16, "bold"), width=300, height=50, fg_color="purple", hover_color="#300030",
                      command=self.open_ranking_window).pack(pady=10)

        # Management Setup Bottom Area
        admin_frame = ctk.CTkFrame(self, fg_color="transparent")
        admin_frame.pack(side="bottom", fill="x", pady=40)
        
        mgmt_font = ("Arial", 14, "bold")
        inner_admin = ctk.CTkFrame(admin_frame, fg_color="transparent")
        inner_admin.pack(anchor="center")
        
        ctk.CTkButton(inner_admin, text="Gestión de Motos", font=mgmt_font, width=180, height=40, fg_color="#3B8ED0", hover_color="#1F6AA5",
                      command=self.show_gestion_motos_view).pack(side="left", padx=15)
        
        ctk.CTkButton(inner_admin, text="Gestión de Lugares", font=mgmt_font, width=180, height=40, fg_color="#3B8ED0", hover_color="#1F6AA5",
                      command=self.show_gestion_lugares_view).pack(side="left", padx=15)
                      
        ctk.CTkButton(inner_admin, text="Gestión de Pilotos", font=mgmt_font, width=180, height=40, fg_color="#3B8ED0", hover_color="#1F6AA5",
                      command=self.show_gestion_pilotos_view).pack(side="left", padx=15)

    def show_comparativo_view(self):
        self.clear_window()
        
        ctk.CTkLabel(self, text="Modo Comparativo", font=("Arial", 24, "bold")).pack(pady=50)
        ctk.CTkLabel(self, text="Este módulo aún no está disponible.", font=("Arial", 16)).pack(pady=10)
        
        bottom_nav = ctk.CTkFrame(self, fg_color="transparent")
        bottom_nav.pack(fill="x", side="bottom", padx=10, pady=20)
        ctk.CTkButton(bottom_nav, text="⬅ Regresar", font=("Arial", 14, "bold"), fg_color="gray", hover_color="darkgray", command=self.show_main_menu).pack(side="left")

    def show_todas_pruebas_view(self):
        self.clear_window()
        
        ctk.CTkLabel(self, text="Todas las Pruebas", font=("Arial", 24, "bold")).pack(pady=50)
        ctk.CTkLabel(self, text="Este módulo aún no está disponible.", font=("Arial", 16)).pack(pady=10)
        
        bottom_nav = ctk.CTkFrame(self, fg_color="transparent")
        bottom_nav.pack(fill="x", side="bottom", padx=10, pady=20)
        ctk.CTkButton(bottom_nav, text="⬅ Regresar", font=("Arial", 14, "bold"), fg_color="gray", hover_color="darkgray", command=self.show_main_menu).pack(side="left")

    def show_individual_view(self):
        self.clear_window()
        
        # --- 0. Back Button ---
        bottom_nav = ctk.CTkFrame(self, fg_color="transparent")
        bottom_nav.pack(fill="x", side="bottom", padx=10, pady=10)
        ctk.CTkButton(bottom_nav, text="⬅ Regresar al Menú", font=("Arial", 12, "bold"), fg_color="gray", hover_color="darkgray", command=self.show_main_menu).pack(side="left")
        
        # --- 1. Top Controls (Moto, Lugar, Ranking) ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=10, pady=2)
        
        # Moto Row
        self.moto_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.moto_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(self.moto_row, text="Motocicleta:", font=("Arial", 14, "bold"), width=100, anchor="w").pack(side="left", padx=5)
        self.moto_combo = ctk.CTkComboBox(self.moto_row, values=["Seleccione Moto..."], width=250)
        self.moto_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(self.moto_row, text="Actualizar Lista", command=self.refresh_motos, width=100).pack(side="left", padx=5)
        
        # Lugar Row
        self.lugar_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.lugar_row.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(self.lugar_row, text="Lugar:", font=("Arial", 14, "bold"), width=100, anchor="w").pack(side="left", padx=5)
        self.lugar_combo = ctk.CTkComboBox(self.lugar_row, values=["Seleccione Lugar..."], width=250)
        self.lugar_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(self.lugar_row, text="Actualizar Lugares", command=self.refresh_lugares, width=100).pack(side="left", padx=5)

        # --- 2. Test Selection (Segmented Button) ---
        self.test_selector_frame = ctk.CTkFrame(self)
        self.test_selector_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(self.test_selector_frame, text="Prueba:", font=("Arial", 14, "bold"), width=100, anchor="w").pack(side="left", padx=15, pady=5)
        
        self.tests_map = {
            "Frenado": BrakingTest,
            "Ascenso": ClimbingTest,
            "Aceleración 0-80": Acceleration080Test,
            "Recuperación": RecoveryTest,
            "Velocidad Máxima": TopSpeedTest
        }
        
        self.test_var = ctk.StringVar(value="Frenado")
        self.test_segmented = ctk.CTkSegmentedButton(
            self.test_selector_frame, 
            values=list(self.tests_map.keys()),
            variable=self.test_var,
            command=self.on_test_selected,
            font=("Arial", 12, "bold")
        )
        self.test_segmented.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        # --- 3. Dynamic Module Area ---
        self.module_container = ctk.CTkFrame(self, fg_color="transparent")
        self.module_container.pack(fill="both", expand=True, padx=10, pady=2)
        
        # --- 4. Env Conditions & Comments (Combined Footer) ---
        self.footer_frame = ctk.CTkFrame(self)
        self.footer_frame.pack(fill="x", padx=10, pady=5)
        
        # Conditions Row
        env_f = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        env_f.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(env_f, text="Condiciones Ambientales | ", font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkLabel(env_f, text="Temp. Amb (°C):", font=("Arial", 11)).pack(side="left", padx=(5, 2))
        self.temp_amb_entry = ctk.CTkEntry(env_f, width=50, height=25)
        self.temp_amb_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(env_f, text="Humedad (%):", font=("Arial", 11)).pack(side="left", padx=2)
        self.humidity_entry = ctk.CTkEntry(env_f, width=50, height=25)
        self.humidity_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(env_f, text="Temp. Suelo (°C):", font=("Arial", 11)).pack(side="left", padx=2)
        self.temp_ground_entry = ctk.CTkEntry(env_f, width=50, height=25)
        self.temp_ground_entry.pack(side="left", padx=2)
        
        # Comments & Button Row
        action_f = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        action_f.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(action_f, text="Comentarios:", font=("Arial", 12, "bold")).pack(side="left", anchor="n")
        self.comments_entry = ctk.CTkTextbox(action_f, height=45)
        self.comments_entry.pack(side="left", fill="x", expand=True, padx=10)
        
        self.generate_btn = ctk.CTkButton(action_f, text="PREVISUALIZAR\nREPORTE", 
                                        font=("Arial", 14, "bold"), 
                                        width=200, height=45,
                                        fg_color="#F29F05", hover_color="#C27A04", text_color="black",
                                        command=self.start_generation)
        self.generate_btn.pack(side="right", padx=5)

        # Initialize
        self.refresh_motos()
        self.refresh_lugares()
        
        # Set default module
        self.switch_module(BrakingTest)

    def on_test_selected(self, value):
        cls = self.tests_map[value]
        self.switch_module(cls)

    def switch_module(self, module_class):
        # Clear current module
        for widget in self.module_container.winfo_children():
            widget.destroy()
            
        # Instantiate new module
        # Pass controller and data_manager to all modules for consistency
        self.active_module = module_class(self.module_container, self.controller, self.data_manager)
        self.active_module.pack(fill="both", expand=True)

    def refresh_lugares(self):
        lugares = self.data_manager.load_lugares()
        values = [f"{l.get('Nombre','Unamed')}" for l in lugares]
        if not values: values = ["Sin lugares registrados"]
        self.lugar_combo.configure(values=values)
        self.lugar_values_map = lugares

    def refresh_motos(self):
        motos = self.data_manager.load_motos()
        values = [f"{m.get('Nombre Comercial','')} - {m.get('Placa','')}" for m in motos]
        if not values: values = ["Sin motos registradas"]
        if hasattr(self, 'moto_combo') and self.moto_combo.winfo_exists():
            self.moto_combo.configure(values=values)
        self.moto_values_map = motos

    # --- NUEVAS VISTAS DE GESTION ---
    
    def show_gestion_motos_view(self):
        self.clear_window()
        
        ctk.CTkLabel(self, text="Gestión de Motocicletas", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Table Frame
        table_frame = ctk.CTkScrollableFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        headers = ["Nom. Comercial", "Cod. Modelo", "Placa", "Cilindraje", "Peso(Kg)", "Potencia", "Torque"]
        widths = [200, 150, 100, 100, 100, 100, 100]
        
        header_f = ctk.CTkFrame(table_frame, fg_color="gray30")
        header_f.pack(fill="x", pady=2)
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_f, text=h, width=widths[i], font=("Arial", 12, "bold")).pack(side="left", padx=2)
            
        selected_idx = {'val': None, 'widget': None}
        
        def refresh_table():
            for w in table_frame.winfo_children():
                if w != header_f: w.destroy()
            
            motos = self.data_manager.load_motos()
            selected_idx['val'], selected_idx['widget'] = None, None
            btn_eliminar.configure(state="disabled")
            
            def select_row(idx, row_widget):
                if selected_idx['widget']:
                    try: selected_idx['widget'].configure(fg_color=["gray86", "gray17"])
                    except: pass
                selected_idx['val'] = idx
                selected_idx['widget'] = row_widget
                row_widget.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                btn_eliminar.configure(state="normal")
                
            for i, m in enumerate(motos):
                row = ctk.CTkFrame(table_frame)
                row.pack(fill="x", pady=1)
                row.bind("<Button-1>", lambda e, x=i, r=row: select_row(x, r))
                
                vals = [m.get('Nombre Comercial',''), m.get('Código Modelo',''), m.get('Placa',''),
                        m.get('Cilindraje (cc)',''), m.get('Peso (Kg)',''), m.get('Potencia (Hp)',''), m.get('Torque (Nm)','')]
                
                for j, v in enumerate(vals):
                    lbl = ctk.CTkLabel(row, text=v, width=widths[j])
                    lbl.pack(side="left", padx=2)
                    lbl.bind("<Button-1>", lambda e, x=i, r=row: select_row(x, r))

        # Controls
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=20, pady=10)
        
        def start_add_moto():
            win = ctk.CTkToplevel(self)
            win.title("Agregar Motocicleta")
            win.geometry("400x500")
            win.attributes("-topmost", True)
            
            fields = ["Fecha", "Nombre Comercial", "Placa", "Código Modelo", "Cilindraje (cc)", "Peso (Kg)", "Potencia (Hp)", "Torque (Nm)"]
            entries = {}
            for f in fields:
                r = ctk.CTkFrame(win)
                r.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(r, text=f).pack(side="left", padx=5)
                e = ctk.CTkEntry(r)
                e.pack(side="right", fill="x", expand=True, padx=5)
                entries[f] = e
            def save():
                data = {f: entries[f].get() for f in fields}
                self.data_manager.add_moto(data)
                refresh_table()
                win.destroy()
            ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

        def delete_moto():
            if selected_idx['val'] is not None:
                if messagebox.askyesno("Confirmar", "¿Eliminar motocicleta seleccionada?"):
                    self.data_manager.delete_moto(selected_idx['val'])
                    refresh_table()

        ctk.CTkButton(ctrl, text="Agregar Moto", font=("Arial", 14, "bold"), command=start_add_moto).pack(side="left", padx=10)
        btn_eliminar = ctk.CTkButton(ctrl, text="Eliminar Moto", font=("Arial", 14, "bold"), fg_color="red", hover_color="darkred", state="disabled", command=delete_moto)
        btn_eliminar.pack(side="right", padx=10)
        
        bottom_nav = ctk.CTkFrame(self, fg_color="transparent")
        bottom_nav.pack(fill="x", side="bottom", padx=10, pady=20)
        ctk.CTkButton(bottom_nav, text="⬅ Regresar", font=("Arial", 14, "bold"), fg_color="gray", hover_color="darkgray", command=self.show_main_menu).pack(side="left")
        
        refresh_table()

    def show_gestion_lugares_view(self):
        self.clear_window()
        ctk.CTkLabel(self, text="Gestión de Lugares", font=("Arial", 24, "bold")).pack(pady=20)
        
        table_frame = ctk.CTkScrollableFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        headers = ["Nombre del Lugar", "Altitud (msnm)", "Coordenadas"]
        widths = [300, 150, 400]
        
        header_f = ctk.CTkFrame(table_frame, fg_color="gray30")
        header_f.pack(fill="x", pady=2)
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_f, text=h, width=widths[i], font=("Arial", 12, "bold")).pack(side="left", padx=2)
            
        selected_idx = {'val': None, 'widget': None}
        
        def refresh_table():
            for w in table_frame.winfo_children():
                if w != header_f: w.destroy()
            
            lugares = self.data_manager.load_lugares()
            selected_idx['val'], selected_idx['widget'] = None, None
            btn_eliminar.configure(state="disabled")
            
            def select_row(idx, row_widget):
                if selected_idx['widget']:
                    try: selected_idx['widget'].configure(fg_color=["gray86", "gray17"])
                    except: pass
                selected_idx['val'] = idx
                selected_idx['widget'] = row_widget
                row_widget.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                btn_eliminar.configure(state="normal")
                
            for i, l in enumerate(lugares):
                row = ctk.CTkFrame(table_frame)
                row.pack(fill="x", pady=1)
                row.bind("<Button-1>", lambda e, x=i, r=row: select_row(x, r))
                
                vals = [l.get('Nombre',''), l.get('Altitud (msnm)',''), l.get('Coordenadas (Lat, Lon)','')]
                
                for j, v in enumerate(vals):
                    lbl = ctk.CTkLabel(row, text=v, width=widths[j])
                    lbl.pack(side="left", padx=2)
                    lbl.bind("<Button-1>", lambda e, x=i, r=row: select_row(x, r))

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=20, pady=10)

        def start_add_lugar():
            win = ctk.CTkToplevel(self)
            win.title("Agregar Lugar")
            win.geometry("400x300")
            win.attributes("-topmost", True)
            fields = ["Nombre", "Altitud (msnm)", "Coordenadas (Lat, Lon)"]
            entries = {}
            for f in fields:
                r = ctk.CTkFrame(win)
                r.pack(fill="x", padx=10, pady=10)
                ctk.CTkLabel(r, text=f).pack(side="left", padx=5)
                e = ctk.CTkEntry(r)
                e.pack(side="right", fill="x", expand=True, padx=5)
                entries[f] = e
            def save():
                data = {f: entries[f].get() for f in fields}
                if not data['Nombre']:
                    messagebox.showerror("Error", "Nombre es obligatorio", parent=win)
                    return
                self.data_manager.add_lugar(data)
                refresh_table()
                win.destroy()
            ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

        def delete_lugar():
            if selected_idx['val'] is not None:
                if messagebox.askyesno("Confirmar", "¿Eliminar lugar seleccionado?"):
                    self.data_manager.delete_lugar(selected_idx['val'])
                    refresh_table()

        ctk.CTkButton(ctrl, text="Agregar Lugar", font=("Arial", 14, "bold"), command=start_add_lugar).pack(side="left", padx=10)
        btn_eliminar = ctk.CTkButton(ctrl, text="Eliminar Lugar", font=("Arial", 14, "bold"), fg_color="red", hover_color="darkred", state="disabled", command=delete_lugar)
        btn_eliminar.pack(side="right", padx=10)
        
        bottom_nav = ctk.CTkFrame(self, fg_color="transparent")
        bottom_nav.pack(fill="x", side="bottom", padx=10, pady=20)
        ctk.CTkButton(bottom_nav, text="⬅ Regresar", font=("Arial", 14, "bold"), fg_color="gray", hover_color="darkgray", command=self.show_main_menu).pack(side="left")
        
        refresh_table()

    def show_gestion_pilotos_view(self):
        self.clear_window()
        ctk.CTkLabel(self, text="Gestión de Pilotos", font=("Arial", 24, "bold")).pack(pady=20)
        
        table_frame = ctk.CTkScrollableFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        headers = ["Nombre del Piloto", "Peso Acumulado (Kg)"]
        widths = [400, 200]
        
        header_f = ctk.CTkFrame(table_frame, fg_color="gray30")
        header_f.pack(fill="x", pady=2)
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_f, text=h, width=widths[i], font=("Arial", 12, "bold")).pack(side="left", padx=2)
            
        selected_idx = {'nombre': None, 'widget': None, 'peso': 0}
        
        def refresh_table():
            for w in table_frame.winfo_children():
                if w != header_f: w.destroy()
            
            pilotos = self.data_manager.load_pilotos()
            selected_idx['nombre'], selected_idx['widget'] = None, None
            btn_eliminar.configure(state="disabled")
            btn_actualizar.configure(state="disabled")
            
            def select_row(nombre, peso, row_widget):
                if selected_idx['widget']:
                    try: selected_idx['widget'].configure(fg_color=["gray86", "gray17"])
                    except: pass
                selected_idx['nombre'] = nombre
                selected_idx['peso'] = peso
                selected_idx['widget'] = row_widget
                row_widget.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                btn_eliminar.configure(state="normal")
                btn_actualizar.configure(state="normal")
                
            for p in pilotos:
                row = ctk.CTkFrame(table_frame)
                row.pack(fill="x", pady=1)
                
                nom = p.get('nombre', '')
                pes = p.get('peso', 0)
                
                row.bind("<Button-1>", lambda e, n=nom, w=pes, r=row: select_row(n, w, r))
                
                vals = [nom, str(pes)]
                
                for j, v in enumerate(vals):
                    lbl = ctk.CTkLabel(row, text=v, width=widths[j])
                    lbl.pack(side="left", padx=2)
                    lbl.bind("<Button-1>", lambda e, n=nom, w=pes, r=row: select_row(n, w, r))

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=20, pady=10)

        def start_add_piloto():
            win = ctk.CTkToplevel(self)
            win.title("Agregar Piloto")
            win.geometry("400x200")
            win.attributes("-topmost", True)
            
            r1 = ctk.CTkFrame(win)
            r1.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r1, text="Nombre:").pack(side="left", padx=5)
            e_n = ctk.CTkEntry(r1)
            e_n.pack(side="right", fill="x", expand=True, padx=5)
            
            r2 = ctk.CTkFrame(win)
            r2.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r2, text="Peso (Kg):").pack(side="left", padx=5)
            e_p = ctk.CTkEntry(r2)
            e_p.pack(side="right", fill="x", expand=True, padx=5)
            
            def save():
                npm = e_n.get().strip()
                try: p_val = float(e_p.get().replace(',','.')) if e_p.get() else 0.0
                except ValueError: p_val = 0.0
                
                if not npm:
                    messagebox.showerror("Error", "Nombre es obligatorio", parent=win)
                    return
                self.data_manager.add_piloto(npm, p_val)
                refresh_table()
                win.destroy()
            ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

        def start_update_piloto():
            if selected_idx['nombre'] is None: return
            win = ctk.CTkToplevel(self)
            win.title("Actualizar Piloto")
            win.geometry("400x200")
            win.attributes("-topmost", True)
            
            old_name = selected_idx['nombre']
            old_weight = selected_idx['peso']
            
            r1 = ctk.CTkFrame(win)
            r1.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r1, text="Nombre:").pack(side="left", padx=5)
            e_n = ctk.CTkEntry(r1)
            e_n.pack(side="right", fill="x", expand=True, padx=5)
            e_n.insert(0, old_name)
            
            r2 = ctk.CTkFrame(win)
            r2.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(r2, text="Peso (Kg):").pack(side="left", padx=5)
            e_p = ctk.CTkEntry(r2)
            e_p.pack(side="right", fill="x", expand=True, padx=5)
            e_p.insert(0, str(old_weight))
            
            def save():
                npm = e_n.get().strip()
                try: p_val = float(e_p.get().replace(',','.')) if e_p.get() else 0.0
                except ValueError: p_val = 0.0
                
                if not npm: return
                self.data_manager.update_piloto(old_name, npm, p_val)
                refresh_table()
                win.destroy()
            ctk.CTkButton(win, text="Actualizar", command=save).pack(pady=20)

        def delete_piloto():
            if selected_idx['nombre'] is not None:
                if messagebox.askyesno("Confirmar", "¿Eliminar piloto seleccionado?"):
                    self.data_manager.delete_piloto(selected_idx['nombre'])
                    refresh_table()

        ctk.CTkButton(ctrl, text="Agregar Piloto", font=("Arial", 14, "bold"), command=start_add_piloto).pack(side="left", padx=10)
        btn_actualizar = ctk.CTkButton(ctrl, text="Actualizar Datos", font=("Arial", 14, "bold"), fg_color="#F29F05", hover_color="#C27A04", text_color="black", state="disabled", command=start_update_piloto)
        btn_actualizar.pack(side="left", padx=10)
        btn_eliminar = ctk.CTkButton(ctrl, text="Eliminar Piloto", font=("Arial", 14, "bold"), fg_color="red", hover_color="darkred", state="disabled", command=delete_piloto)
        btn_eliminar.pack(side="right", padx=10)
        
        bottom_nav = ctk.CTkFrame(self, fg_color="transparent")
        bottom_nav.pack(fill="x", side="bottom", padx=10, pady=20)
        ctk.CTkButton(bottom_nav, text="⬅ Regresar", font=("Arial", 14, "bold"), fg_color="gray", hover_color="darkgray", command=self.show_main_menu).pack(side="left")
        
        refresh_table()

    def open_ranking_window(self):
        # Moved logic, kept same as before
        win = ctk.CTkToplevel(self)
        win.title("Ranking de Frenado")
        win.geometry("1000x600")
        
        ctrl_frame = ctk.CTkFrame(win)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ctrl_frame, text="Velocidad:").pack(side="left", padx=10)
        speed_var = ctk.StringVar(value="40")
        
        # Selection state
        selected_entry_data = {} # Container to hold current selection {'entry': None, 'widget': None}
        
        def delete_selected():
            if selected_entry_data.get('entry'):
                # Confirm
                if messagebox.askyesno("Confirmar", "¿Eliminar este registro del ranking?"):
                    if self.data_manager.delete_ranking_entry(selected_entry_data['entry']):
                        # Clear selection and refresh
                        selected_entry_data['entry'] = None
                        selected_entry_data['widget'] = None
                        btn_delete.configure(state="disabled")
                        refresh_table()
                    else:
                        messagebox.showerror("Error", "No se pudo eliminar el registro.")

        btn_delete = ctk.CTkButton(ctrl_frame, text="Eliminar Seleccionado", state="disabled", fg_color="red", hover_color="darkred", command=delete_selected)
        btn_delete.pack(side="right", padx=10)

        def refresh_table(val=None):
            target = int(speed_var.get())
            raw_data = self.data_manager.load_ranking()
            filtered = [d for d in raw_data if d.get('target_speed') == target]
            filtered.sort(key=lambda x: x['metrics']['dist_m'])
            
            for w in table_frame.winfo_children(): w.destroy()
            
            headers = ["Pos", "Fecha", "Modelo", "Piloto", "Peso Total (Kg) (Moto+Piloto)", "Distancia (m)", "Vel (km/h)", "Temp Amb", "Suelo"]
            col_widths = [40, 90, 150, 120, 200, 100, 90, 80, 80]
            
            header_frame = ctk.CTkFrame(table_frame, fg_color="gray30")
            header_frame.pack(fill="x", pady=2)
            
            for i, h in enumerate(headers):
                ctk.CTkLabel(header_frame, text=h, width=col_widths[i], font=("Arial", 12, "bold")).pack(side="left", padx=2)
            
            # Row Selection Logic
            def select_row(entry, row_widget):
                # Reset previous formatting if exists
                if selected_entry_data.get('widget'):
                    try:
                        selected_entry_data['widget'].configure(fg_color=["gray86", "gray17"]) # Default ctk color approx
                    except: pass
                
                # Set new selection
                selected_entry_data['entry'] = entry
                selected_entry_data['widget'] = row_widget
                row_widget.configure(fg_color=["#3B8ED0", "#1F6AA5"]) # Highlight color
                btn_delete.configure(state="normal")

            for i, entry in enumerate(filtered):
                row = ctk.CTkFrame(table_frame)
                row.pack(fill="x", pady=1)
                
                # Bind click to select
                # Use default argument capture for entry and row
                row.bind("<Button-1>", lambda event, e=entry, r=row: select_row(e, r))
                
                moto_str = f"{entry['moto_nombre']} ({entry['moto_codigo']})"
                env = entry.get('env', {})
                
                # Format Weight: "Total (Moto + Piloto)"
                moto_w = entry.get('moto_peso', 0)
                pilot_w = entry.get('piloto_peso', 0)
                weight_str = f"{entry['peso_total']:.1f} ({moto_w} + {pilot_w})"
                
                vals = [
                    f"{i+1}", 
                    entry['fecha'], 
                    moto_str, 
                    entry['piloto'],
                    weight_str, 
                    f"{entry['metrics']['dist_m']:.2f}",
                    f"{entry['metrics']['initial_speed']:.2f}", 
                    f"{env.get('temp_amb', '-')}", 
                    f"{env.get('temp_ground', '-')}"
                ]
                for j, v in enumerate(vals):
                    lbl = ctk.CTkLabel(row, text=v, width=col_widths[j])
                    lbl.pack(side="left", padx=2)
                    # Propagate click to children
                    lbl.bind("<Button-1>", lambda event, e=entry, r=row: select_row(e, r))

        ctk.CTkSegmentedButton(ctrl_frame, values=["40", "60"], variable=speed_var, command=refresh_table).pack(side="left", padx=10)
        table_frame = ctk.CTkScrollableFrame(win)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        refresh_table()

    def start_generation(self):
        if not self.active_module:
            return

        # 1. Get Moto
        moto_str = self.moto_combo.get()
        if moto_str == "Seleccione Moto..." or moto_str == "Sin motos registradas":
             messagebox.showerror("Error", "Seleccione una motocicleta.")
             return
        
        try:
            moto_data = next(m for m in self.moto_values_map if f"{m.get('Nombre Comercial','')} - {m.get('Placa','')}" == moto_str)
        except StopIteration:
            messagebox.showerror("Error", "Error identificando la moto seleccionada.")
            return

        # 1b. Get Lugar
        lugar_str = self.lugar_combo.get()
        if lugar_str == "Seleccione Lugar..." or lugar_str == "Sin lugares registrados":
             messagebox.showerror("Error", "Debe seleccionar un lugar de prueba.")
             return
             
        try:
            lugar_data = next(l for l in self.lugar_values_map if l.get('Nombre') == lugar_str)
        except StopIteration:
            messagebox.showerror("Error", "Error identificando el lugar seleccionado.")
            return

        # 2. Get Env
        env_conditions = {
            'temp_amb': self.temp_amb_entry.get(),
            'humidity': self.humidity_entry.get(),
            'temp_ground': self.temp_ground_entry.get(),
            'lugar': lugar_data
        }
        
        # 3. Get Comments
        comments = self.comments_entry.get("0.0", "end").strip()
        
        # 4. Delegate to Active Module
        self.generate_btn.configure(state="disabled", text="Procesando...")
        
        def run():
            try:
                # Expects (success, message/path)
                success, result = self.active_module.process(moto_data, env_conditions, comments)
                
                if success:
                    if "Previsualización" not in result:
                         self.after(0, lambda: messagebox.showinfo("Éxito", f"Reporte generado correctamente en:\n{result}"))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", f"Problema: {result}"))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.after(0, lambda err=e: messagebox.showerror("Error Excepción", str(err)))
            finally:
                self.after(0, lambda: self.generate_btn.configure(state="normal", text="PREVISUALIZAR REPORTE"))
        
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
