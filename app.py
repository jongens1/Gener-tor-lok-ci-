import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
import io

# --- NASTAVENIA ---
st.set_page_config(page_title="Generátor lokácií", layout="wide")

def generate_pdf(params):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    # Výpočet rozmerov bunky
    box_width = page_width / params['cols']
    box_height = page_height / params['rows']
    
    # Generovanie zoznamu lokácií
    locations = []
    first_number_range = range(params['f_n_s'], params['f_n_e'] + 1)
    first_letter_range = [chr(i) for i in range(ord(params['f_l_s']), ord(params['f_l_e']) + 1)]
    second_range = range(params['s_s'], params['s_e'] + 1)
    third_range = range(params['t_s'], params['t_e'] + 1)
    fourth_range = range(params['fo_s'], params['fo_e'] + 1)

    if params['block_count'] == 2:
        locations = [f"{n}{l}-{s:02d}" for n in first_number_range for l in first_letter_range for s in second_range]
    elif params['block_count'] == 3:
        locations = [f"{n}{l}-{s:02d}-{t:02d}" for n in first_number_range for l in first_letter_range for s in second_range for t in third_range]
    else:
        locations = [f"{n}{l}-{s:02d}-{t:02d}-{u:02d}" for n in first_number_range for l in first_letter_range for s in second_range for t in third_range for u in fourth_range]

    def draw_rotated_location(c, x, y, location_code):
        c.saveState()
        center_x = x + box_width / 2
        center_y = y + box_height / 2
        c.translate(center_x, center_y)
        c.rotate(90)
        c.translate(-box_height / 2, -box_width / 2)
        
        # Obdĺžnik
        c.setLineWidth(0.2)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.rect(0, 0, box_height, box_width)
        
        # Rozmery pre obsah
        font_size = min(box_width, box_height) * 0.15
        barcode_height = box_height * 0.25
        barcode_width_factor = 0.2 * (box_width / 100) * params['barcode_scale']
        
        try:
            barcode = code128.Code128(location_code, barHeight=barcode_height, barWidth=barcode_width_factor)
            barcode_width = barcode.width
            barcode.drawOn(c, (box_height - barcode_width) / 2, box_width / 2)
        except:
            pass
            
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(box_height / 2, box_width / 2 - (font_size * 1.5), location_code)
        c.restoreState()

    locs_per_page = params['cols'] * params['rows']
    for i, location in enumerate(locations):
        pos = i % locs_per_page
        col = pos % params['cols']
        row = pos // params['cols']
        x = col * box_width
        y = page_height - (row + 1) * box_height
        draw_rotated_location(c, x, y, location)
        if (i + 1) % locs_per_page == 0 and (i + 1) < len(locations):
            c.showPage()
            
    c.save()
    buffer.seek(0)
    return buffer, len(locations)

# --- UI APP ---
st.title("🔄 Generátor lokácií (otočený o 90°)")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Konfigurácia blokov")
    block_count = st.selectbox("Počet blokov:", [2, 3, 4], index=1)
    c1, c2 = st.columns(2)
    f_n_s = c1.number_input("Číslo od (X):", 0, 99, 1)
    f_n_e = c2.number_input("Číslo do (X):", 0, 99, 8)
    f_l_s = c1.selectbox("Písmeno od (Y):", [chr(i) for i in range(65, 91)], index=0)
    f_l_e = c2.selectbox("Písmeno do (Y):", [chr(i) for i in range(65, 91)], index=6)
    s_s, s_e = st.columns(2)
    s_s = s_s.number_input("Blok 2 od:", 1, 999, 1)
    s_e = s_e.number_input("Blok 2 do:", 1, 999, 10)
    if block_count >= 3:
        t_s, t_e = st.columns(2)
        t_s = t_s.number_input("Blok 3 od:", 1, 999, 1)
        t_e = t_e.number_input("Blok 3 do:", 1, 999, 10)
    else: t_s, t_e = 1, 1
    if block_count == 4:
        fo_s, fo_e = st.columns(2)
        fo_s = fo_s.number_input("Blok 4 od:", 1, 999, 1)
        fo_e = fo_e.number_input("Blok 4 do:", 1, 999, 10)
    else: fo_s, fo_e = 1, 1

with col2:
    st.subheader("Rozloženie a tlač")
    cols = st.number_input("Počet stĺpcov:", 1, 15, 8)
    rows = st.number_input("Počet riadky:", 1, 20, 6)
    barcode_scale = st.slider("Šírka čiarového kódu:", 0.5, 3.0, 1.0, 0.1)
    params = {'block_count': block_count, 'f_n_s': f_n_s, 'f_n_e': f_n_e, 'f_l_s': f_l_s, 'f_l_e': f_l_e, 's_s': s_s, 's_e': s_e, 't_s': t_s, 't_e': t_e, 'fo_s': fo_s, 'fo_e': fo_e, 'cols': cols, 'rows': rows, 'barcode_scale': barcode_scale}
    if st.button("🚀 Vygenerovať PDF", type="primary"):
        pdf_buffer, count = generate_pdf(params)
        st.success(f"Vygenerovaných {count} lokácií.")
        st.download_button(label="⬇️ STIAHNUŤ PDF", data=pdf_buffer, file_name="lokacie.pdf", mime="application/pdf")
