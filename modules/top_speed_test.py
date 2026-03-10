import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

class TopSpeedTest(ctk.CTkFrame):
    def __init__(self, parent, controller, data_manager):
        super().__init__(parent)
        self.controller = controller
        self.data_manager = data_manager
        
        # Title
        ctk.CTkLabel(self, text="Prueba de Velocidad Máxima", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Files Inputs Area (Single File)
        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(fill="x", padx=10, pady=10)
        
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

    def process(self, moto_data, env_conditions, comments):
        # Gather data from UI
        pilot = self.pilot_combo.get()
        weight_str = self.weight_entry.get()
        filepath = self.path_entry.get()
        
        # Validate
        if pilot == "Seleccione Piloto..." or not pilot:
            return False, "Por favor seleccione un piloto."
        if not weight_str:
             return False, "Por favor ingrese el peso del piloto."
        try:
             weight = float(weight_str.replace(',', '.'))
        except ValueError:
             return False, "Peso del piloto inválido."
        if not filepath or not os.path.exists(filepath):
             return False, "Por favor seleccione un archivo CSV válido."
             
        inputs = [{
            'pilot': pilot,
            'weight': weight,
            'filepath': filepath
        }]
        
        data = inputs[0]
        success, result_or_error = self.controller.evaluate_top_speed(data, moto_data, comments, env_conditions)
        
        if success:
            preview_data = result_or_error  # This is the dict with 'sections'
            # Launch Preview Window
            from preview_window import PreviewWindow
            def on_generate(modified_sections=None):
                if modified_sections:
                    preview_data['sections'] = modified_sections
                success_gen, pdf_path = self.controller.generate_pdf(preview_data)
                if success_gen:
                    messagebox.showinfo("Éxito", f"Reporte final (Velocidad Máxima) generado correctamente en:\\n{pdf_path}")
                else:
                    messagebox.showerror("Error", f"Error generando PDF:\\n{pdf_path}")
            
            # Launch async to not block UI thread
            import threading
            def show_gui():
                PreviewWindow(self.winfo_toplevel(), "Reporte de Velocidad Máxima", preview_data['sections'], on_generate)
            
            self.after(0, show_gui)
            return True, "Previsualización"
        else:
            return False, result_or_error
