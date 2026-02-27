import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

class ClimbingTest(ctk.CTkFrame):
    def __init__(self, parent, controller, data_manager):
        super().__init__(parent)
        self.controller = controller
        self.data_manager = data_manager
        
        # Title
        ctk.CTkLabel(self, text="Prueba de Ascenso (0-70m)", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Main Container
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- SECTION 1: SOLO PILOT ---
        self.solo_frame = ctk.CTkFrame(self.main_frame)
        self.solo_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.solo_frame, text="Sección 1: Solo Piloto (Seleccionar 1 Archivo)", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # Row 1: Pilot & Weight
        row1 = ctk.CTkFrame(self.solo_frame, fg_color="transparent")
        row1.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row1, text="Piloto:").pack(side="left", padx=5)
        self.solo_pilot_combo = ctk.CTkComboBox(row1, values=["Seleccione Piloto..."], width=200)
        self.solo_pilot_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(row1, text="Peso (Kg):").pack(side="left", padx=5)
        self.solo_weight_entry = ctk.CTkEntry(row1, width=60)
        self.solo_weight_entry.pack(side="left", padx=5)
        
        # Row 2: File
        row2 = ctk.CTkFrame(self.solo_frame, fg_color="transparent")
        row2.pack(fill="x", padx=5, pady=2)
        
        self.solo_file_entry = ctk.CTkEntry(row2, width=300, placeholder_text="Ruta del archivo CSV...")
        self.solo_file_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(row2, text="Buscar", width=60, command=lambda: self.browse_file(self.solo_file_entry)).pack(side="left", padx=5)
        
        
        # --- SECTION 2: PILOT + PASSENGER ---
        self.passenger_frame = ctk.CTkFrame(self.main_frame)
        self.passenger_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.passenger_frame, text="Sección 2: Piloto + Pasajero (Seleccionar 1 Archivo)", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # Row 1: Pilot & Pass Selection
        row3 = ctk.CTkFrame(self.passenger_frame, fg_color="transparent")
        row3.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row3, text="Piloto:").pack(side="left", padx=5)
        self.pp_pilot_combo = ctk.CTkComboBox(row3, values=["Seleccione Piloto..."], width=150)
        self.pp_pilot_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(row3, text="Pasajero:").pack(side="left", padx=5)
        self.pp_passenger_combo = ctk.CTkComboBox(row3, values=["Seleccione Pasajero..."], width=150)
        self.pp_passenger_combo.pack(side="left", padx=5)
        
        # Row 2: Weights
        row4 = ctk.CTkFrame(self.passenger_frame, fg_color="transparent")
        row4.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row4, text="Peso Piloto (Kg):").pack(side="left", padx=5)
        self.pp_pilot_weight = ctk.CTkEntry(row4, width=50)
        self.pp_pilot_weight.pack(side="left", padx=5)
        
        ctk.CTkLabel(row4, text="Peso Pasajero (Kg):").pack(side="left", padx=5)
        self.pp_pass_weight = ctk.CTkEntry(row4, width=50)
        self.pp_pass_weight.pack(side="left", padx=5)
        
        ctk.CTkLabel(row4, text="Peso Extra (Kg):").pack(side="left", padx=5)
        self.pp_extra_weight = ctk.CTkEntry(row4, width=50)
        self.pp_extra_weight.pack(side="left", padx=5)
        
        # Row 3: File
        row5 = ctk.CTkFrame(self.passenger_frame, fg_color="transparent")
        row5.pack(fill="x", padx=5, pady=2)
        
        self.pp_file_entry = ctk.CTkEntry(row5, width=300, placeholder_text="Ruta del archivo CSV...")
        self.pp_file_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(row5, text="Buscar", width=60, command=lambda: self.browse_file(self.pp_file_entry)).pack(side="left", padx=5)

        # Process Button - REMOVED (User uses main Generate Button)
        # self.process_btn = ctk.CTkButton(self, text="Generar Reporte de Ascenso", command=self.process, height=40, font=("Arial", 14, "bold"))
        # self.process_btn.pack(pady=20, padx=20, fill="x")

        self.refresh_pilots()

    def browse_file(self, entry_widget):
        f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
        if f:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, f)

    def refresh_pilots(self):
        pilots = self.data_manager.load_pilotos()
        if not pilots: pilots = ["Nuevo Piloto"]
        
        # Update all 3 combos
        for combo in [self.solo_pilot_combo, self.pp_pilot_combo, self.pp_passenger_combo]:
            current = combo.get()
            combo.configure(values=pilots)
            if current not in pilots and current != "Seleccione Piloto..." and current != "Seleccione Pasajero...":
                combo.set("Seleccione Piloto...")

    def get_data(self):
        # Validate Solo Section
        solo_data = None
        s_path = self.solo_file_entry.get()
        if s_path and os.path.exists(s_path):
            solo_data = {
                'pilot': self.solo_pilot_combo.get(),
                'weight': self.solo_weight_entry.get(),
                'filepath': s_path,
                'type': 'SOLO'
            }
            
        # Validate Passenger Section
        passenger_data = None
        p_path = self.pp_file_entry.get()
        if p_path and os.path.exists(p_path):
            passenger_data = {
                'pilot': self.pp_pilot_combo.get(),
                'passenger': self.pp_passenger_combo.get(),
                'pilot_weight': self.pp_pilot_weight.get(),
                'pass_weight': self.pp_pass_weight.get(),
                'extra_weight': self.pp_extra_weight.get(),
                'filepath': p_path,
                'weight': str(float(self.pp_pilot_weight.get() or 0) + float(self.pp_pass_weight.get() or 0) + float(self.pp_extra_weight.get() or 0)), # Total weight
                'type': 'PASSENGER'
            }
            
        return solo_data, passenger_data

    def process(self, moto_data, env_conditions, comments):
        # This is called by main app
        solo_data, passenger_data = self.get_data()
        
        if not solo_data and not passenger_data:
             messagebox.showerror("Error", "Debe cargar al menos un archivo (Solo o Pasajero).")
             return False, "No data"
             
        # Call controller
        return self.controller.process_climbing(solo_data, passenger_data, moto_data, comments, env_conditions)
