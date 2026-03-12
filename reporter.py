from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os

class PDFReporter:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=0.3*inch, leftMargin=0.3*inch, topMargin=0.3*inch, bottomMargin=0.3*inch)
        self.elements = []
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        self.styles.add(ParagraphStyle(name='Header1', parent=self.styles['Heading1'], alignment=1, spaceAfter=20))
        self.styles.add(ParagraphStyle(name='Header2', parent=self.styles['Heading2'], spaceBefore=15, spaceAfter=10))
        self.styles.add(ParagraphStyle(name='NormalCenter', parent=self.styles['Normal'], alignment=1))

    def add_header(self, moto_info, pilots_info, comments, env_conditions=None, title=None, test_type="frenado"):
        # Title
        if title is None:
            title = f"Prueba de {test_type} del modelo {moto_info.get('Nombre Comercial', '')} ({moto_info.get('Código Modelo', '')})"
        self.elements.append(Paragraph(title, self.styles['Header1']))
        
        # Moto Info
        moto_data = [
            ["Nombre comercial:", moto_info.get('Nombre Comercial', ''), "Fecha:", datetime.now().strftime("%Y-%m-%d")],
            ["Código de Modelo:", moto_info.get('Código Modelo', ''), "Placa:", moto_info.get('Placa', '')],
            ["Cilindraje:", f"{moto_info.get('Cilindraje (cc)', '')} cc", "Peso Moto:", f"{moto_info.get('Peso (Kg)', '')} Kg"],
            ["Potencia:", f"{moto_info.get('Potencia (Hp)', '')} Hp", "Torque:", f"{moto_info.get('Torque (Nm)', '')} Nm"]
        ]
        
        # Adjust table widths for wider page (Total ~7.9 inches)
        # 7.9 / 4 = ~1.97. Let's make label cols smaller and value cols wider
        col_lbl = 1.8 * inch # Keep similar or slightly wider
        col_val = 2.15 * inch
        
        t = Table(moto_data, colWidths=[col_lbl, col_val, col_lbl, col_val]) 
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        self.elements.append(t)
        self.elements.append(Spacer(1, 12))
        
        # Environmental Conditions
        if env_conditions:
            lugar = env_conditions.get('lugar', None)
            
            if lugar:
                self.elements.append(Paragraph("<b>Condiciones Ambientales y Lugar de Prueba:</b>", self.styles['Normal']))
            else:
                self.elements.append(Paragraph("<b>Condiciones Ambientales:</b>", self.styles['Normal']))
                
            self.elements.append(Spacer(1, 4))
            
            if lugar:
                env_data = [
                    ["Lugar:", f"{lugar.get('Nombre', '')}", "Temp. Ambiente:", f"{env_conditions.get('temp_amb', '')} °C"],
                    ["Altitud:", f"{lugar.get('Altitud (msnm)', '')} msnm", "Humedad:", f"{env_conditions.get('humidity', '')} %"],
                    ["Coordenadas:", f"{lugar.get('Coordenadas (Lat, Lon)', '')}", "Temp. Suelo:", f"{env_conditions.get('temp_ground', '')} °C"]
                ]
                t_env = Table(env_data, colWidths=[col_lbl, col_val, col_lbl, col_val])
                t_env.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                    ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
                    ('PADDING', (0,0), (-1,-1), 6),
                ]))
            else:
                env_data = [
                    ["Temp. Ambiente:", f"{env_conditions.get('temp_amb', '')} °C"],
                    ["Humedad:", f"{env_conditions.get('humidity', '')} %"],
                    ["Temp. Suelo:", f"{env_conditions.get('temp_ground', '')} °C"]
                ]
                t_env = Table(env_data, colWidths=[col_lbl, col_val])
                t_env.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                    ('PADDING', (0,0), (-1,-1), 6),
                ]))
                
            self.elements.append(t_env)
            self.elements.append(Spacer(1, 12))
        
        # Pilot Info
        pilot_text = ", ".join([f"{p['name']} ({p['weight']} Kg)" for p in pilots_info])
        self.elements.append(Paragraph(f"<b>Pilotos:</b> {pilot_text}", self.styles['Normal']))
        
        if comments:
            self.elements.append(Spacer(1, 12))
            self.elements.append(Paragraph(f"<b>Comentarios:</b> {comments}", self.styles['Normal']))
            
        self.elements.append(Spacer(1, 20))

    def add_section(self, title):
        self.elements.append(Paragraph(title, self.styles['Header2']))

    def add_image(self, img_bytes, width=7.9*inch, height=None):
        from reportlab.lib.utils import ImageReader
        
        if img_bytes:
            # Read the true aspect ratio from the matplotlib image stream
            img_reader = ImageReader(img_bytes)
            orig_width, orig_height = img_reader.getSize()
            aspect_ratio = orig_height / orig_width
            
            # Autocalculate height if not strictly forced
            if height is None:
                calc_height = width * aspect_ratio
            else:
                calc_height = height
                
            im = Image(img_bytes, width=width, height=calc_height)
            self.elements.append(im)
            self.elements.append(Spacer(1, 12))

    def add_table(self, data, header=None):
        if header:
            data.insert(0, header)
            
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        self.elements.append(t)
        self.elements.append(Spacer(1, 12))

    def add_page_break(self):
        self.elements.append(PageBreak())

    def build(self):
        try:
            from version import VERSION
            
            def add_version_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(colors.gray)
                # Bottom right corner
                canvas.drawRightString(doc.pagesize[0] - 0.3*inch, 0.3*inch, f"Sistema Incol v{VERSION}")
                canvas.restoreState()
                
            self.doc.build(self.elements, onFirstPage=add_version_footer, onLaterPages=add_version_footer)
            return True
        except Exception as e:
            print(f"Error building PDF: {e}")
            return False
