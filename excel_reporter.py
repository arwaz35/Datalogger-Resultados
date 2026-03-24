import os
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import pandas as pd
import io
from PIL import Image

class ExcelReporter:
    def __init__(self, templates_dir="/Users/danielvelasquez/Library/CloudStorage/OneDrive-Personal/Proyectos Incol/Datalogger/Formatos",
                 output_dir="/Users/danielvelasquez/Library/CloudStorage/OneDrive-Personal/Proyectos Incol/Datalogger/Resultados"):
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_acceleration(self, preview_data):
        try:
            template_path = os.path.join(self.templates_dir, "ft-nm-000-008.xlsx")
            if not os.path.exists(template_path):
                return False, f"Plantilla no encontrada: {template_path}"
                
            wb = openpyxl.load_workbook(template_path)
            ws = wb.active
            
            # --- MAPPING DATA ---
            moto = preview_data.get('moto_info', {})
            env_cond = preview_data.get('env_conditions', {})
            lugar = env_cond.get('lugar', {}) if env_cond else {}
            inputs = preview_data.get('inputs', [{}])[0]
            
            # Header info
            ws['D7'] = pd.Timestamp.now().strftime("%d/%m/%Y")
            ws['D8'] = moto.get('Placa', '')
            ws['D9'] = moto.get('Peso (Kg)', '')
            
            ws['G7'] = moto.get('Nombre Comercial', '')
            ws['G8'] = moto.get('Chasis', '')
            ws['G9'] = moto.get('Potencia (Hp)', '')
            
            ws['J7'] = moto.get('Código Modelo', '')
            ws['J8'] = moto.get('Motor', '')
            ws['J9'] = moto.get('Torque (Nm)', '')
            
            ws['A12'] = preview_data.get('comments', '')
            
            # Pilot Info
            ws['C18'] = inputs.get('pilot', '')
            ws['C19'] = inputs.get('weight', '')
            ws['C20'] = inputs.get('altura', '')
            
            # Env Cond
            ws['H18'] = lugar.get('Nombre', '')
            ctx = preview_data.get('contexto_gps', {})
            
            if ctx:
                ws['H19'] = ctx.get('altitud_promedio_msnm', lugar.get('Altitud (m)', ''))
                ws['H20'] = f"{ctx.get('latitud_inicial', '')}, {ctx.get('longitud_inicial', '')}"
                ws['H21'] = ctx.get('google_maps_link', '')
            else:
                ws['H19'] = lugar.get('Altitud (m)', '')
            
            ws['K18'] = env_cond.get('temp_amb', '') if env_cond else ''
            ws['K19'] = env_cond.get('humidity', '') if env_cond else ''
            ws['K20'] = env_cond.get('temp_ground', '') if env_cond else ''
            
            # --- RESULTS (Tables) ---
            top_3 = preview_data.get('top_3_events', [])
            for i, ev in enumerate(top_3):
                row = 52 + i
                m = ev['metrics']
                ws[f'C{row}'] = f"Evento {ev['id']}"
                ws[f'F{row}'] = m.get('v_start', 0.0)
                ws[f'G{row}'] = m.get('v_final', 80.0)
                ws[f'H{row}'] = m.get('time_s', 0.0)
                ws[f'I{row}'] = m.get('dist_m', 0.0)
                ws[f'J{row}'] = m.get('avg_acc', 0.0)
                ws[f'K{row}'] = m.get('top_rpm', 0.0)
                
            # Best event segments
            segments = preview_data.get('best_event_segments', [])
            # Segments will be [("0-20", t, d, a, rpm), ("0-40", ...)]
            for i, seg in enumerate(segments):
                row = 90 + i
                ws[f'F{row}'] = seg[1] # Tiempo
                ws[f'G{row}'] = seg[2] # Distancia
                ws[f'H{row}'] = seg[3] # Aceleracion
                ws[f'I{row}'] = seg[4] # RPM
                
            # --- IMAGES ---
            def insert_img(bytes_data, cell):
                if bytes_data:
                    if isinstance(bytes_data, dict): bytes_data = bytes_data.get('bytes')
                    try:
                        # Load via PIL to verify and optionally resize/format
                        pil_img = Image.open(io.BytesIO(bytes_data))
                        img_byte_arr = io.BytesIO()
                        pil_img.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        
                        xl_img = OpenpyxlImage(img_byte_arr)
                        # We might need to scale image to fit cells nicely. 
                        # User wants them embedded in specific cells.
                        # xl_img.width = 500
                        # xl_img.height = 300
                        ws.add_image(xl_img, cell)
                    except Exception as e:
                        print(f"Error inserting image at {cell}: {e}")
            
            insert_img(preview_data.get('context_map'), 'G23')
            insert_img(preview_data.get('img_combined'), 'B56')
            insert_img(preview_data.get('img_detail_gps'), 'B95')
            insert_img(preview_data.get('img_detail_v'), 'B135')
            insert_img(preview_data.get('img_detail_a'), 'B158')
            insert_img(preview_data.get('img_detail_rpm'), 'B173')

            # --- SAVE ---
            
            def clean(s): return "".join([c for c in str(s) if c.isalnum() or c in (' ', '-', '_')]).strip()
            moto_str = clean(moto.get('Nombre Comercial', 'Moto'))
            fecha_str = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Aceleracion_{moto_str}_{fecha_str}.xlsx"
            filepath = os.path.join(self.output_dir, filename)
            
            wb.save(filepath)
            return True, filepath
            
        except Exception as e:
            return False, str(e)
