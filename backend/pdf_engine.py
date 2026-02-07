from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import os
from datetime import datetime

# --- PALETA DE COLORES ---
COLOR_TEXT = colors.HexColor("#ffffff")     # Blanco Puro
COLOR_ACCENT = colors.HexColor("#00f0ff")   # Cyan Cyberpunk (Títulos)
COLOR_SAFE = colors.HexColor("#00ff41")     # Verde Hacker
COLOR_WARN = colors.HexColor("#ffb700")     # Naranja Precaución
COLOR_DANGER = colors.HexColor("#ff003c")   # Rojo Crítico

class PDFReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        
        # AJUSTE DE MARGENES
        # topMargin=180*mm empuja el texto hacia abajo para que entre en la caja inferior
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=15*mm, leftMargin=15*mm,
            topMargin=180*mm, 
            bottomMargin=15*mm
        )
        self.styles = getSampleStyleSheet()
        self._crear_estilos_personalizados()
        self.story = []

    def _crear_estilos_personalizados(self):
        # Títulos grandes en Cyan
        self.styles.add(ParagraphStyle(
            name='CyberTitle',
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=COLOR_ACCENT,
            spaceAfter=12
        ))
        # Texto normal en blanco
        self.styles.add(ParagraphStyle(
            name='NormalWhite',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=COLOR_TEXT,
            leading=15 # Interlineado cómodo
        ))
        # Bloques de código o datos técnicos
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            fontName='Courier',
            fontSize=10,
            textColor=colors.lime,
            backColor=colors.black,
            borderPadding=6,
            spaceBefore=6
        ))

    def _draw_background_image(self, canvas, doc):
        """Pone tu plantilla JPG de fondo en cada página"""
        canvas.saveState()
        
        # ⚠️ IMPORTANTE: Asegúrate de que este archivo está en la misma carpeta
        bg_path = "plantilla_fondo.png"
        
        if os.path.exists(bg_path):
            # Dibujamos la imagen ocupando todo el folio A4
            canvas.drawImage(bg_path, 0, 0, width=A4[0], height=A4[1])
        else:
            # Si falla la imagen, fondo negro de emergencia
            canvas.setFillColor(colors.HexColor("#0b0c15"))
            canvas.rect(0, 0, A4[0], A4[1], fill=1)
            canvas.setFont("Helvetica", 10)
            canvas.setFillColor(colors.red)
            canvas.drawString(100, 800, f"ERROR: No se encuentra {bg_path}")

        canvas.restoreState()

    def _draw_dynamic_data(self, canvas, doc, risk_score, risk_label):
        """Escribe los datos flotantes y DIBUJA el gráfico circular"""
        canvas.saveState()

        # --- 1. LÓGICA DE COLORES (SEMÁFORO) ---
        if risk_score < 40: 
            c = COLOR_SAFE      # Verde
        elif risk_score < 70: 
            c = COLOR_WARN      # Amarillo
        else: 
            c = COLOR_DANGER    # Rojo

        # --- 2. CONFIGURACIÓN DEL GAUGE (Geometría) ---
        gauge_x = 52 * mm  
        gauge_y = A4[1] - 52 * mm 
        
        radius = 22 * mm      
        thickness = 5 * mm    

        # --- 3. DIBUJAR EL ANILLO DE FONDO (Pista gris) ---
        canvas.setLineWidth(thickness)
        canvas.setStrokeColor(colors.HexColor("#2a2a2a")) 
        canvas.setLineCap(1) 
        
        p_bg = canvas.beginPath()
        p_bg.arc(gauge_x - radius, gauge_y - radius, 
                 gauge_x + radius, gauge_y + radius, 
                 90, 360) 
        
        canvas.drawPath(p_bg, stroke=1, fill=0)

        # --- 4. DIBUJAR EL ANILLO DE PROGRESO (Color dinámico) ---
        angle_extent = -3.6 * risk_score 
        
        canvas.setStrokeColor(c) 
        
        p_prog = canvas.beginPath()
        p_prog.arc(gauge_x - radius, gauge_y - radius, 
                   gauge_x + radius, gauge_y + radius, 
                   90, angle_extent) 
        
        canvas.drawPath(p_prog, stroke=1, fill=0)

        # --- 5. TEXTO CENTRAL ---
        
        # PORCENTAJE (NÚMERO GIGANTE)
        # Lo subimos un poquito (-4mm) para que quede bien centrado en el hueco
        canvas.setFont("Helvetica-Bold", 42) 
        canvas.setFillColor(c)
        canvas.drawCentredString(gauge_x, gauge_y - 4*mm, f"{risk_score}%")
        
        # ETIQUETA DE ESTADO (CRITICAL / SAFE)
        # CAMBIO AQUÍ: Bajamos de -18mm a -32mm
        # Esto lo saca del anillo rojo y lo pone debajo.
        canvas.setFont("Helvetica-Bold", 14) # Un pelín más grande (14) queda mejor solo
        canvas.setFillColor(COLOR_TEXT)
        canvas.drawCentredString(gauge_x, gauge_y - 32*mm, risk_label) 

        # --- 6. DATOS DE CABECERA (Sin cambios) ---
        data_x_start = 115*mm 
        
        # Target ID
        y_pos = A4[1] - 48*mm
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLOR_ACCENT)
        canvas.drawString(data_x_start, y_pos, "TARGET IDENTIFIER:")
        
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(COLOR_TEXT)
        display_name = (self.target_name[:22] + '..') if len(self.target_name) > 22 else self.target_name
        canvas.drawString(data_x_start, y_pos - 5*mm, display_name)

        # Fecha
        y_pos_date = A4[1] - 75*mm
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLOR_ACCENT)
        canvas.drawString(data_x_start, y_pos_date, "AUDIT TIMESTAMP:")
        
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(COLOR_TEXT)
        fecha_actual = datetime.now().strftime("%Y.%m.%d | %H:%M UTC")
        canvas.drawString(data_x_start, y_pos_date - 5*mm, fecha_actual)

        canvas.restoreState()

    def generar_informe_auditoria(self, datos):
        self.target_name = datos.get('origen_codigo', 'Unknown Target')
        
        # Procesar riesgo
        try: risk_val = int(datos.get('riesgo', 0))
        except: risk_val = 0
        
        # Etiqueta de texto
        veredicto = datos.get('veredicto', '').upper()
        if "SEGURO" in veredicto: label = "SECURE"
        elif "PELIGRO" in veredicto: label = "CRITICAL"
        else: label = "CAUTION"

        # Definimos la función que pinta el fondo + datos
        draw_ui_callback = lambda c, d: (self._draw_background_image(c, d), self._draw_dynamic_data(c, d, risk_val, label))

        # --- CONSTRUCCIÓN DEL CONTENIDO (TEXTO ABAJO) ---
        
        # Si hay datos OSINT
        if "datos" in datos:
            self.story.append(Paragraph("INTELLIGENCE REPORT (OSINT)", self.styles['CyberTitle']))
            self._render_osint(datos)
        # Si es Auditoría de Código
        else:
            self.story.append(Paragraph("TECHNICAL AUDIT SUMMARY", self.styles['CyberTitle']))
            self._render_audit(datos)

        print(f"[PDF ENGINE] Generando PDF Cyberpunk: {self.filename}...")
        # onFirstPage: Dibuja fondo + datos del gauge
        # onLaterPages: Solo dibuja el fondo (sin gauge, para que no se repita)
        self.doc.build(self.story, onFirstPage=draw_ui_callback, onLaterPages=draw_ui_callback)
        print("[PDF ENGINE] ¡PDF Completado!")

    def _render_audit(self, datos):
        """Pinta la tabla y explicación técnica"""
        
        # Tabla transparente para datos clave
        data_table = [
            ["VULNERABILITY:", datos.get('tipo_vulnerabilidad', 'None')],
            ["LOCATION:", datos.get('ubicacion', 'N/A')],
        ]
        
        t = Table(data_table, colWidths=[50*mm, 110*mm])
        t.setStyle(TableStyle([
            ('TEXTCOLOR', (0,0), (-1,-1), COLOR_TEXT), # Texto blanco
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), # Primera col negrita
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey), # Líneas grises finas
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 8*mm))
        
        # Explicación IA
        self.story.append(Paragraph("AI ANALYSIS & CONTEXT:", self.styles['NormalWhite']))
        self.story.append(Spacer(1, 2*mm))
        
        # Formatear saltos de línea
        texto_explicacion = datos.get('explicacion', '').replace('\n', '<br/>')
        self.story.append(Paragraph(texto_explicacion, self.styles['NormalWhite']))

    def _render_osint(self, root_data):
        """Pinta los datos de OSINT"""
        data = root_data.get('datos', {})
        
        # CASO 1: TOKEN
        if data.get('es_token'):
            hp = "DETECTED 🚨" if "SÍ" in data.get('honeypot', '') else "SAFE ✅"
            
            t_data = [
                ["TOKEN NAME:", f"{data.get('nombre')} ({data.get('simbolo')})"],
                ["HONEYPOT STATUS:", hp],
                ["BUY/SELL TAX:", data.get('impuestos', 'N/A')],
                ["OWNERSHIP:", data.get('dueño_renunciado', 'N/A')]
            ]
            t = Table(t_data, colWidths=[50*mm, 110*mm])
            t.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,-1), COLOR_TEXT),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            self.story.append(t)
            
            # Riesgos extra
            if data.get('riesgos_detectados'):
                self.story.append(Spacer(1, 5*mm))
                self.story.append(Paragraph("CRITICAL FLAGS:", self.styles['CodeBlock']))
                for r in data['riesgos_detectados']:
                    self.story.append(Paragraph(f"> {r}", self.styles['CodeBlock']))

        # CASO 2: WEB2 / PERSONA
        elif data.get('huella_digital_web2'):
            self.story.append(Paragraph("DIGITAL FOOTPRINT:", self.styles['NormalWhite']))
            for item in data['huella_digital_web2']:
                plat = item.get('plataforma', 'Unknown')
                url = item.get('url', '#')
                self.story.append(Paragraph(f"• {plat}: {url}", self.styles['CodeBlock']))


# ==========================================
# ZONA DE PRUEBAS
# ==========================================
if __name__ == "__main__":
    # Prueba rápida para ajustar coordenadas sin encender el servidor
    engine = PDFReportGenerator("test_final.pdf")
    
    # Prueba con 85% (ROJO)
    engine.generar_informe_auditoria({
        "riesgo": 38, 
        "veredicto": "SEGURO", 
        "origen_codigo": "USDT_SMART_CONTRACT_V2",
        "tipo_vulnerabilidad": "Minting Ilimitado",
        "ubicacion": "function _mint()",
        "explicacion": "El propietario puede crear tokens infinitos y hundir el precio."
    })
    print("PDF Generado: test_final.pdf")