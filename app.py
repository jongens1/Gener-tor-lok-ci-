import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm
import io
import re

# --- NASTAVENIA ---
st.set_page_config(page_title="Generátor lokácií PRO", layout="wide")

def generate_pdf(locations, params):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    box_width = page_width / params['cols']
    box_height = page_height / params['rows']

    def draw_location(c, x, y, location_code):
        c.saveState()
        
        # Presun na stred bunky
        center_x = x + box_width / 2
        center_y = y + box_height / 2
        c.translate(center_x, center_y)
        
        # Rotácia ak je zvolená
        if params['rotate_90']:
            c.rotate(90)
            # Po rotácii o 90° sa šírka a výška kresliacej plochy vymenia
            draw_w, draw_h = box_height, box_width
        else:
            draw_w, draw_h = box_width, box_height

        # --- DYNAMICKÉ VEĽKOSTI ---
        # Barcode scale určuje hrúbku čiar (v mm)
        bar_width = params['barcode_scale'] * mm
        # Výška kódu je 30% výšky bunky, max 100mm
        bar_height = min(draw_h * 0.3, 100 * mm)
        # Font size je 20% výšky bunky
        font_size = draw_h * 0.15

        try:
            barcode = code128.Code128(location_code, barHeight=bar_height, barWidth=bar_width)
            b_w = barcode.width
            # Kreslíme kód vycentrovaný (posun o polovicu šírky vľavo)
            # Umiestnenie: nad stredom
            barcode.drawOn(c, -b_w / 2, draw_h * 0.05)
        except:
            pass

        # Text pod kódom
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(0, -draw_h * 0.2, location_code)
        
        c.restoreState()

    locs_per_page = params['cols'] * params['rows']
    for i, location in enumerate(locations):
        pos = i % locs_per_page
        col = pos % params['cols']
        row = pos // params['cols']
        
        x = col * box_width
        y = page_height - (row + 1) * box_height
        
        draw_location(c, x, y, location)
        
        if (i + 1) % locs_per_page == 0 and (i + 1) < len(locations):
            c.showPage()
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP (TVOJE PÔVODNÉ ZADÁVANIE) ---
st.title("🔄 Generátor lokácií (Opravený)")

vstup_mode = st.radio("Vyberte spôsob zadania lokácií:", ["Automatický rozsah", "Ručný zoznam (Enter)"], horizontal=True)
col1, col2 = st.columns(2)
locations_to_print = []

with col1:
    if vstup_mode == "Automatický rozsah":
        st.subheader("Konfigurácia blokov")
        block_count = st.selectbox("Počet blokov:", [2, 3, 4], index=1)
        c1, c2 = st.columns(2)
        f_n_s = c1.number_input("Číslo od (X):", 0, 99, 1)
        f_n_e = c2.number_input("Číslo do (X):", 0, 99, 8)
        f_l_s = c1.selectbox("Písmeno od (Y):", [chr(i) for i in range(65, 91)], index=0)
        f_l_e = c2.selectbox("Písmeno do (Y):", [chr(i) for i in range(65, 91)], index=6)
        
        s_s, s_e = st.columns(2)
        s_s_val = s_s.number_input("Blok 2 od:", 1, 999, 1)
        s_e_val = s_e.number_input("Blok 2 do:", 1, 999, 10)
        
        # Logika pre blok 3 a 4
        t_s_val, t_e_val = 1, 1
        fo_s_val, fo_e_val = 1, 1
        
        if block_count >= 3:
            t1, t2 = st.columns(2)
            t_s_val = t1.number_input("Blok 3 od:", 1, 999, 1)
            t_e_val = t2.number_input("Blok 3 do:", 1, 999, 10)
        if block_count == 4:
            fo1, fo2 = st.columns(2)
            fo_s_val = fo1.number_input("Blok 4 od:", 1, 999, 1)
            fo_e_val = fo2.number_input("Blok 4 do:", 1, 999, 10)

        # Generovanie zoznamu
        first_number_range = range(f_n_s, f_n_e + 1)
        first_letter_range = [chr(i) for i in range(ord(f_l_s), ord(f_l_e) + 1)]
        
        if block_count == 2:
            locations_to_print = [f"{n}{l}-{s:02d}" for n in first_number_range for l in first_letter_range for s in range(s_s_val, s_e_val + 1)]
        elif block_count == 3:
            locations_to_print = [f"{n}{l}-{s:02d}-{t:02d}" for n in first_number_range for l in first_letter_range for s in range(s_s_val, s_e_val + 1) for t in range(t_s_val, t_e_val + 1)]
        else:
            locations_to_print = [f"{n}{l}-{s:02d}-{t:02d}-{u:02d}" for n in first_number_range for l in first_letter_range for s in range(s_s_val, s_e_val + 1) for t in range(t_s_val, t_e_val + 1) for u in range(fo_s_val, fo_e_val + 1)]
    else:
        st.subheader("Ručné zadanie")
        input_text = st.text_area("Vložte lokácie (jedna na riadok):", height=300)
        if input_text.strip():
            locations_to_print = [x.strip() for x in re.split(r'[;,\n\s]+', input_text) if x.strip()]

with col2:
    st.subheader("Rozloženie a tlač")
    cols = st.number_input("Počet stĺpcov na A4:", 1, 15, 1) # Prednastavené pre A5
    rows = st.number_input("Počet riadkov na A4:", 1, 25, 2)   # Prednastavené pre A5
    
    rotate_90 = st.checkbox("Otočiť obsah (kód a text) o 90°", value=True)
    
    barcode_scale = st.slider("Hrúbka čiar kódu:", 0.1, 2.0, 0.6, 0.05)
    
    st.info(f"Veľkosť bunky: {round(210/cols,1)}x{round(297/rows,1)} mm")

    if st.button("🚀 Vygenerovať PDF", type="primary"):
        if locations_to_print:
            params = {
                'cols': cols, 
                'rows': rows, 
                'barcode_scale': barcode_scale,
                'rotate_90': rotate_90
            }
            pdf_buffer = generate_pdf(locations_to_print, params)
            st.success(f"Pripravených {len(locations_to_print)} lokácií.")
            st.download_button(label="⬇️ STIAHNUŤ PDF", data=pdf_buffer, file_name="lokacie.pdf", mime="application/pdf")
        else:
            st.error("Zoznam lokácií je prázdny!")
