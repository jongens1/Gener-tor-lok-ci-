import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm
import io
import re

# --- NASTAVENIA STRÁNKY ---
st.set_page_config(page_title="Generátor lokácií PRO", layout="wide")

def generate_pdf(locations, params):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    # Rozmery bunky (napr. A5 na stojato = 1 stĺpec, 2 riadky)
    box_width = page_width / params['cols']
    box_height = page_height / params['rows']

    def draw_label(c, x, y, location_code):
        c.saveState()
        
        # 1. Presun na stred bunky
        cx = x + box_width / 2
        cy = y + box_height / 2
        c.translate(cx, cy)
        
        # 2. Rotácia obsahu (0 alebo 90 stupňov)
        if params['rotate_content']:
            c.rotate(90)
            draw_w, draw_h = box_height, box_width
        else:
            draw_w, draw_h = box_width, box_height

        # --- VÝPOČET ROZMEROV ---
        b_width = params['bar_width_mm'] * mm
        b_height = params['bar_height_mm'] * mm
        f_size = params['font_size']
        
        # Výpočet pozície (kód hore, text dole)
        # Súradnice sú relatívne k stredu bunky (0,0)
        barcode_y_offset = (draw_h * 0.1)  # Mierne nad stredom
        text_y_offset = -(draw_h * 0.25)   # Pod stredom

        try:
            # Generovanie čiarového kódu
            barcode = code128.Code128(location_code, barHeight=b_height, barWidth=b_width)
            bw = barcode.width
            # Vykreslenie (centrované horizontálne: -bw/2)
            barcode.drawOn(c, -bw / 2, barcode_y_offset)
        except:
            pass

        # Vykreslenie textu
        c.setFont("Helvetica-Bold", f_size)
        c.drawCentredString(0, text_y_offset, location_code)
        
        c.restoreState()

    # Logika stránkovania
    locs_per_page = params['cols'] * params['rows']
    for i, location in enumerate(locations):
        pos = i % locs_per_page
        col = pos % params['cols']
        row = pos // params['cols']
        
        x = col * box_width
        # ReportLab počíta Y odspodu
        y = page_height - (row + 1) * box_height
        
        draw_label(c, x, y, location)
        
        if (i + 1) % locs_per_page == 0 and (i + 1) < len(locations):
            c.showPage()
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("📦 Generátor skladových lokácií")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Dáta")
    vstup_mode = st.radio("Vstup:", ["Rozsah", "Zoznam"], horizontal=True)
    
    locations_to_print = []
    if vstup_mode == "Rozsah":
        c1, c2 = st.columns(2)
        f_n_s = c1.number_input("Číslo od:", 1, 99, 1)
        f_n_e = c2.number_input("Číslo do:", 1, 99, 2)
        f_l_s = c1.selectbox("Písmeno od:", [chr(i) for i in range(65, 91)], index=0)
        f_l_e = c2.selectbox("Písmeno do:", [chr(i) for i in range(65, 91)], index=1)
        s_max = st.number_input("Segment 2 (polica) do:", 1, 50, 5)
        
        for n in range(f_n_s, f_n_e + 1):
            for l in range(ord(f_l_s), ord(f_l_e) + 1):
                for s in range(1, s_max + 1):
                    locations_to_print.append(f"{n}{chr(l)}-{s:02d}")
    else:
        txt = st.text_area("Lokácie (jedna na riadok):", height=200)
        locations_to_print = [x.strip() for x in re.split(r'[;,\n\s]+', txt) if x.strip()]

with col2:
    st.subheader("2. Formát a Orientácia")
    cc1, cc2 = st.columns(2)
    cols = cc1.number_input("Stĺpce (A4):", 1, 10, 1)
    rows = cc2.number_input("Riadky (A4):", 1, 10, 2)
    
    # Možnosť rotácie o 90 stupňov
    rotate_content = st.toggle("Otočiť kód a text o 90°", value=True)
    
    st.divider()
    st.subheader("3. Veľkosti (v mm / pt)")
    # Slidery pre presné doladenie
    b_w = st.slider("Hrúbka čiary kódu (mm):", 0.1, 1.5, 0.5, 0.05)
    b_h = st.slider("Výška kódu (mm):", 5, 120, 40)
    f_s = st.slider("Veľkosť písma:", 10, 200, 80)

    if st.button("🚀 GENEROVAŤ PDF", type="primary", use_container_width=True):
        if locations_to_print:
            params = {
                'cols': cols,
                'rows': rows,
                'rotate_content': rotate_content,
                'bar_width_mm': b_w,
                'bar_height_mm': b_h,
                'font_size': f_s
            }
            pdf = generate_pdf(locations_to_print, params)
            st.download_button("⬇️ STIAHNUŤ PDF", pdf, "lokacie.pdf", "application/pdf", use_container_width=True)
        else:
            st.error("Zoznam lokácií je prázdny!")

# Pomocná informácia o rozmere bunky
st.caption(f"Aktuálny rozmer jedného štítka: {round(210/cols, 1)}x{round(297/rows, 1)} mm")
