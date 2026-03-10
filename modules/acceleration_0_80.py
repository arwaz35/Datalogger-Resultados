import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

class Acceleration080Test(ctk.CTkFrame):
    def __init__(self, parent, controller, data_manager):
        super().__init__(parent)
        self.controller = controller
        self.data_manager = data_manager
        
        # Title
        ctk.CTkLabel(self, text="Prueba de Aceleración 0 - 80 km/h", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Files Inputs Area (Single File)
        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(fill="x", padx=10, pady=5)
        
        # Single File Input Row
        self.add_file_row()
            
        self.refresh_pilots()

    def add_file_row(self):
        row = ctk.CTkFrame(self.files_frame)
        row.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(row, text="Archivo:").pack(side="left", padx=5)
        
        # Pilot Combo
        self.pilot_combo = ctk.CTkComboBox(row, values=["Seleccione Piloto..."], width=200)
        self.pilot_combo.pack(side="left", padx=5)
        
        # Weight
        ctk.CTkLabel(row, text="Peso (Kg):").pack(side="left", padx=5)
        self.weight_entry = ctk.CTkEntry(row, width=60)
        self.weight_entry.pack(side="left", padx=5)
        
        # File Path
        self.path_entry = ctk.CTkEntry(row, width=300, placeholder_text="Ruta del archivo CSV...")
        self.path_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        def browse():
            f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
            if f:
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, f)
                
        ctk.CTkButton(row, text="Buscar", width=60, command=browse).pack(side="left", padx=5)

    def refresh_pilots(self):
        pilots = self.data_manager.load_pilotos()
        if not pilots: pilots = ["Nuevo Piloto"]
        
        current = self.pilot_combo.get()
        self.pilot_combo.configure(values=pilots)
        if current in pilots:
            self.pilot_combo.set(current)
        else:
            self.pilot_combo.set("Seleccione Piloto...")

    def get_data(self):
        path = self.path_entry.get()
        pilot = self.pilot_combo.get()
        weight = self.weight_entry.get()
        
        if path and os.path.exists(path) and pilot and pilot != "Seleccione Piloto...":
            return [{
                'filepath': path,
                'pilot': pilot,
                'weight': weight
            }]
        return []

    def process(self, moto_data, env_conditions, comments):
        valid_inputs = self.get_data()
        
        if not valid_inputs:
            messagebox.showerror("Error", "Debe seleccionar un archivo válido y asignar un piloto.")
            return False, "Sin entradas válidas"
            
        if hasattr(self.controller, 'evaluate_acceleration_0_80'):
            success, result = self.controller.evaluate_acceleration_0_80(valid_inputs, moto_data, comments, env_conditions)
            if success:
                from preview_window import PreviewWindow
                def on_confirm(sections_data):
                    final_success, filepath = self.controller.generate_pdf(result)
                    if final_success:
                        messagebox.showinfo("Éxito", f"Reporte generado exitosamente:\n{filepath}")
                    else:
                        messagebox.showerror("Error", "Ocurrió un error al generar el PDF.")
                        
                PreviewWindow(self, "Previsualización - Aceleración 0-80 km/h", result['sections'], on_confirm)
                return True, "Previsualización abierta"
            else:
                messagebox.showerror("Error", f"Error en el análisis:\n{result}")
                return False, result
        else:
            return False, "Método de análisis no implementado aún."
