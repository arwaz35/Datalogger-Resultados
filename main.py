import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from data_manager import DataManager
from analysis_controller import AnalysisController

# Import Modules
from modules.braking_test import BrakingTest
from modules.climbing_test import ClimbingTest
# from modules.acceleration_0_60 import Acceleration060Test # REPLACED/REMOVED
from modules.acceleration_0_80 import Acceleration080Test
from modules.recovery_test import RecoveryTest # NEW COMBINED MODULE
# from modules.recovery_100m import Recovery100mTest # REMOVED
# from modules.recovery_200m import Recovery200mTest # REMOVED

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Sistema de Análisis Incol")
        self.geometry("1100x900")
        # Maximize window by default
        # self.after(0, lambda: self.state("zoomed"))
        
        self.data_manager = DataManager()
        self.controller = AnalysisController()
        
        self.active_module = None
        self.moto_values_map = []
        
        self.create_layouts()
        
    def create_layouts(self):
        # --- 1. Moto Selection (Fixed Top) ---
        self.moto_frame = ctk.CTkFrame(self)
        self.moto_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.moto_frame, text="Selección de Motocicleta", font=("Arial", 16, "bold")).pack(pady=5)
        
        self.moto_combo = ctk.CTkComboBox(self.moto_frame, values=["Seleccione Moto..."], width=300)
        self.moto_combo.pack(side="left", padx=20, pady=10)
        
        ctk.CTkButton(self.moto_frame, text="Nueva Moto", command=self.open_new_moto_window).pack(side="left", padx=10)
        ctk.CTkButton(self.moto_frame, text="Actualizar Lista", command=self.refresh_motos).pack(side="left", padx=10)
        ctk.CTkButton(self.moto_frame, text="Gestionar Pilotos", command=self.open_pilot_manager).pack(side="right", padx=20)
        
        # --- 2. Ranking (Fixed Top) ---
        self.ranking_frame = ctk.CTkFrame(self)
        self.ranking_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.ranking_frame, text="Ranking", font=("Arial", 16, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(self.ranking_frame, text="Ranking Frenos", command=self.open_ranking_window, fg_color="purple", hover_color="#300030").pack(side="left", padx=10)

        # --- 3. Test Selection (New) ---
        self.test_selector_frame = ctk.CTkFrame(self)
        self.test_selector_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.test_selector_frame, text="Selección de Prueba:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=2)
        
        # Grid of buttons
        tests = [
            ("Prueba de Frenado", BrakingTest),
            ("Prueba de Ascenso", ClimbingTest),
            ("Aceleración 0-80", Acceleration080Test),
            ("Prueba de Recuperación", RecoveryTest)
        ]
        
        btn_grid = ctk.CTkFrame(self.test_selector_frame, fg_color="transparent")
        btn_grid.pack(fill="x", padx=5, pady=5)
        
        # Grid Configuration (2x2)
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)
        
        for i, (name, cls) in enumerate(tests):
            # Layout: 2 Columns
            row = i // 2
            col = i % 2
            
            btn = ctk.CTkButton(btn_grid, text=name, command=lambda c=cls: self.switch_module(c))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        # --- 4. Dynamic Module Area ---
        self.module_container = ctk.CTkFrame(self, fg_color="transparent")
        self.module_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- 5. Env Conditions (Common Footer) ---
        self.env_frame = ctk.CTkFrame(self)
        self.env_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.env_frame, text="Condiciones Ambientales:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=2)
        
        env_grid = ctk.CTkFrame(self.env_frame, fg_color="transparent")
        env_grid.pack(fill="x", padx=10, pady=5)
        
        # Temp Ambient
        ctk.CTkLabel(env_grid, text="Temp. Amb (°C):").grid(row=0, column=0, padx=5, pady=2)
        self.temp_amb_entry = ctk.CTkEntry(env_grid, width=60)
        self.temp_amb_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # Humedad
        ctk.CTkLabel(env_grid, text="Humedad (%):").grid(row=0, column=2, padx=5, pady=2)
        self.humidity_entry = ctk.CTkEntry(env_grid, width=60)
        self.humidity_entry.grid(row=0, column=3, padx=5, pady=2)
        
        # Temp Suelo
        ctk.CTkLabel(env_grid, text="Temp. Suelo (°C):").grid(row=0, column=4, padx=5, pady=2)
        self.temp_ground_entry = ctk.CTkEntry(env_grid, width=60)
        self.temp_ground_entry.grid(row=0, column=5, padx=5, pady=2)
            
        # --- 6. Comments and Action (Common Footer) ---
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.action_frame, text="Comentarios:").pack(anchor="w", padx=10)
        self.comments_entry = ctk.CTkTextbox(self.action_frame, height=60)
        self.comments_entry.pack(fill="x", padx=10, pady=5)
        
        self.generate_btn = ctk.CTkButton(self.action_frame, text="PREVISUALIZAR REPORTE", 
                                        font=("Arial", 16, "bold"), 
                                        height=50,
                                        fg_color="#F29F05", hover_color="#C27A04", text_color="black",
                                        command=self.start_generation)
        self.generate_btn.pack(fill="x", padx=20, pady=10)
        
        # Initialize
        self.refresh_motos()
        
        # Set default module
        self.switch_module(BrakingTest)

    def switch_module(self, module_class):
        # Clear current module
        for widget in self.module_container.winfo_children():
            widget.destroy()
            
        # Instantiate new module
        # Pass controller and data_manager to all modules for consistency
        self.active_module = module_class(self.module_container, self.controller, self.data_manager)
        self.active_module.pack(fill="both", expand=True)

    def refresh_motos(self):
        motos = self.data_manager.load_motos()
        values = [f"{m.get('Nombre Comercial','')} - {m.get('Placa','')}" for m in motos]
        if not values: values = ["Sin motos registradas"]
        self.moto_combo.configure(values=values)
        self.moto_values_map = motos

    def open_new_moto_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Agregar Motocicleta")
        win.geometry("400x500")
        win.attributes("-topmost", True)
        
        fields = ["Fecha", "Nombre Comercial", "Placa", "Código Modelo", "Cilindraje (cc)", "Peso (Kg)", "Potencia (Hp)", "Torque (Nm)"]
        entries = {}
        
        for f in fields:
            row = ctk.CTkFrame(win)
            row.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(row, text=f).pack(side="left", padx=5)
            e = ctk.CTkEntry(row)
            e.pack(side="right", fill="x", expand=True, padx=5)
            entries[f] = e
            
        def save():
            data = {f: entries[f].get() for f in fields}
            self.data_manager.add_moto(data)
            self.refresh_motos()
            win.destroy()
            
        ctk.CTkButton(win, text="Guardar", command=save).pack(pady=20)

    def open_pilot_manager(self):
        win = ctk.CTkToplevel(self)
        win.title("Gestionar Pilotos")
        win.geometry("300x400")
        win.attributes("-topmost", True)
        
        entry = ctk.CTkEntry(win, placeholder_text="Nombre del piloto")
        entry.pack(pady=10, padx=10, fill="x")
        
        def add():
            name = entry.get()
            if name:
                self.data_manager.add_piloto(name)
                refresh_list()
                # Notify active module to refresh if it has pilots
                if hasattr(self.active_module, 'refresh_pilots'):
                    self.active_module.refresh_pilots()
                entry.delete(0, "end")
                
        ctk.CTkButton(win, text="Agregar", command=add).pack(pady=5)
        
        list_frame = ctk.CTkScrollableFrame(win)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh_list():
            for widget in list_frame.winfo_children(): widget.destroy()
            pilots = self.data_manager.load_pilotos()
            for p in pilots:
                r = ctk.CTkFrame(list_frame)
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=p).pack(side="left", padx=5)
        
        refresh_list()

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
        if moto_str == "Seleccione Moto...":
             messagebox.showerror("Error", "Seleccione una motocicleta.")
             return
        
        try:
            moto_data = next(m for m in self.moto_values_map if f"{m.get('Nombre Comercial','')} - {m.get('Placa','')}" == moto_str)
        except StopIteration:
            messagebox.showerror("Error", "Error identificando la moto seleccionada.")
            return

        # 2. Get Env
        env_conditions = {
            'temp_amb': self.temp_amb_entry.get(),
            'humidity': self.humidity_entry.get(),
            'temp_ground': self.temp_ground_entry.get()
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
