import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

class BrakingTest(ctk.CTkFrame):
    def __init__(self, parent, controller, data_manager):
        super().__init__(parent)
        self.controller = controller
        self.data_manager = data_manager
        self.file_inputs = []
        
        # Title
        ctk.CTkLabel(self, text="Prueba de Frenado", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Files Inputs Area
        self.files_frame = ctk.CTkScrollableFrame(self, label_text="Archivos y Pilotos")
        self.files_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial 3 rows
        for i in range(3):
            self.add_file_row(i + 1)
            
        self.refresh_pilots()

    def add_file_row(self, index):
        row = ctk.CTkFrame(self.files_frame)
        row.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(row, text=f"Archivo {index}:").pack(side="left", padx=5)
        
        # Pilot Combo
        pilot_combo = ctk.CTkComboBox(row, values=["Seleccione Piloto..."], width=200)
        pilot_combo.pack(side="left", padx=5)
        
        # Weight
        ctk.CTkLabel(row, text="Peso (Kg):").pack(side="left", padx=5)
        weight_entry = ctk.CTkEntry(row, width=60)
        weight_entry.pack(side="left", padx=5)
        
        # File Path
        path_entry = ctk.CTkEntry(row, width=300, placeholder_text="Ruta del archivo CSV...")
        path_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        def browse():
            f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
            if f:
                path_entry.delete(0, "end")
                path_entry.insert(0, f)
                
        ctk.CTkButton(row, text="Buscar", width=60, command=browse).pack(side="left", padx=5)
        
        self.file_inputs.append({
            'pilot': pilot_combo,
            'weight': weight_entry,
            'path': path_entry
        })

    def refresh_pilots(self):
        pilots = self.data_manager.load_pilotos()
        if not pilots: pilots = ["Nuevo Piloto"]
        
        for inp in self.file_inputs:
            p_combo = inp['pilot']
            current = p_combo.get()
            p_combo.configure(values=pilots)
            if current in pilots:
                p_combo.set(current)
            else:
                p_combo.set("Seleccione Piloto...")

    def get_data(self):
        valid_inputs = []
        for inp in self.file_inputs:
            path = inp['path'].get()
            pilot = inp['pilot'].get()
            weight = inp['weight'].get()
            
            if path and os.path.exists(path) and pilot and pilot != "Seleccione Piloto...":
                valid_inputs.append({
                    'filepath': path,
                    'pilot': pilot,
                    'weight': weight
                })
        return valid_inputs

    def process(self, moto_data, env_conditions, comments):
        valid_inputs = self.get_data()
        
        if not valid_inputs:
            messagebox.showerror("Error", "Debe seleccionar al menos un archivo válido y asignar un piloto.")
            return False, "Sin entradas válidas"
            
        success, result = self.controller.evaluate_data(valid_inputs, moto_data, comments, env_conditions)
        if success:
            from preview_window import PreviewWindow
            def on_confirm(sections_data):
                # Pass the original result dict to the controller to finally generate PDF
                final_success, filepath = self.controller.generate_pdf(result)
                if final_success:
                    messagebox.showinfo("Éxito", f"Reporte generado exitosamente:\n{filepath}")
                else:
                    messagebox.showerror("Error", "Ocurrió un error al generar el PDF.")
                    
            PreviewWindow(self, "Previsualización - Frenado", result['sections'], on_confirm)
            return True, "Previsualización abierta"
        else:
            messagebox.showerror("Error", f"Error en el análisis:\n{result}")
            return False, result
