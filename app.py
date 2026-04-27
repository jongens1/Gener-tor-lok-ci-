import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
import io
import re

# --- NASTAVENIA ---
st.set_page_config(page_title="Generátor lokácií PRO", layout="wide")

def generate_pdf(locations, params):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    # Rozmery bunky na papieri
    box_width = page_width / params['cols']
    box_height = page_height / params['rows']

    def draw_rotated_location(c, x, y, location_code):
        c.saveState()
        
        # 1. Presun na stred bunky
        center_x = x + box_width / 2
        center_y = y + box_height / 2
        c.translate(center_x, center_y)
        
        # 2. Otočenie
        c.rotate(90)
        
        # Po otočení o 90°:
        # Nová šírka kresliacej plochy (W) je pôvodná box_height
        # Nová výška kresliacej plochy (H) je pôvodná box_width
        W = box_height
        H = box_width
        
        # Posun do "nového" ľavého dolného rohu (relatívne k stredu)
        c.translate(-W / 2, -H / 2)

        # Pomocný rámček (jemne sivý)
        c.setLineWidth(0.1)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(0, 0, W, H)

        # --- DYNAMICKÉ ROZMERY ---
        # Čiarový kód zaberie cca 60% šírky a 30% výšky bunky
        target_barcode_width = W * 0.8
        barcode_h = H * 0.25
        
        # Výpočet barWidth tak, aby sa kód zmestil do target_barcode_width
        # Štandardný Code128 má cca 11 modulov na znak + start/stop
        estimated_modules = (len(location_code) + 2) * 11
        calculated_bar_width = (target_barcode_width / estimated_modules) * params['barcode_scale']
        
        try:
            barcode = code128.Code128(location_code, barHeight=barcode_h, barWidth=calculated_bar_width)
            # Vycentrovanie kódu
            bw = barcode.width
            bh = barcode_h
            barcode.drawOn(c, (W - bw) / 2, H * 0.45) # Umiestnenie nad stred
        except:
            # Ak je kód príliš dlhý, skúsime ho s minimálnou šírkou
            try:
                barcode = code128.Code128(location_code, barHeight=barcode_h, barWidth=0.2 * mm)
                barcode.drawOn(c, (W - barcode.width) / 2, H * 0.45)
            except:
                pass

        # --- TEXT ---
        # Veľkosť písma podľa výšky bunky
        font_size = H * 0.2
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(W / 2, H * 0.15, location_code)
        
        c.restoreState()

    locs_per_page = params['cols'] * params['rows']
    for i, location in enumerate(locations):
        pos = i % locs_per_page
        col = pos % params['cols']
        row = pos // params['cols']
        
        x = col * box_width
        # ReportLab počíta Y od nuly (spodok), preto musíme invertovať riadky
        y = page_height - (row + 1) * box_height
        
        draw_rotated_location(c, x, y, location)
        
        if (i + 1) % locs_per_page == 0 and (i + 1) < len(locations):
            c.showPage()
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("🔄 Generátor lokácií (Oprava A5/A4)")

vstup_mode = st.radio("Spôsob zadania:", ["Automatický rozsah", "Ručný zoznam"], horizontal=True)
locations_to_print = []

col1, col2 = st.columns([1, 1])

with col1:
    if vstup_mode == "Automatický rozsah":
        st.subheader("Bloky")
        b_count = st.selectbox("Počet segmentov:", [2, 3, 4], index=1)
        
        c1, c2 = st.columns(2)
        f_n_s = c1.number_input("Číslo od:", 0, 99, 1)
        f_n_e = c2.number_input("Číslo do:", 0, 99, 5)
        f_l_s = c1.selectbox("Písmeno od:", [chr(i) for i in range(65, 91)], index=0)
        f_l_e = c2.selectbox("Písmeno do:", [chr(i) for i in range(65, 91)], index=1)
        
        s_s, s_e = st.columns(2)
        s_val_s = s_s.number_input("S2 od:", 1, 99, 1)
        s_val_e = s_e.number_input("S2 do:", 1, 99, 5)
        
        # Generovanie
        num_r = range(f_n_s, f_n_e + 1)
        let_r = [chr(i) for i in range(ord(f_l_s), ord(f_l_e) + 1)]
        s2_r = range(s_val_s, s_val_e + 1)
        
        if b_count == 2:
            locations_to_print = [f"{n}{l}-{s:02d}" for n in num_r for l in let_r for s in s2_r]
        elif b_count == 3:
            t_s, t_e = st.columns(2)
            t_v_s = t_s.number_input("S3 od:", 1, 99, 1)
            t_v_e = t_e.number_input("S3 do:", 1, 99, 2)
            locations_to_print = [f"{n}{l}-{s:02d}-{t:02d}" for n in num_r for l in let_r for s in s2_r for t in range(t_v_s, t_v_e + 1)]
    else:
        input_text = st.text_area("Zoznam lokácií:", height=250)
        if input_text:
            locations_to_print = [x.strip() for x in re.split(r'[;,\n\s]+', input_text) if x.strip()]

with col2:
    st.subheader("Nastavenia tlače")
    cols = st.number_input("Počet stĺpcov:", 1, 15, 1)
    rows = st.number_input("Počet riadkov:", 1, 25, 2)
    b_scale = st.slider("Šírka čiar (Barcode scale):", 0.5, 3.0, 1.2, 0.1)
    
    # Info o rozmere
    w_mm = round(210/cols, 1)
    h_mm = round(297/rows, 1)
    st.info(f"Rozmer štítka: {w_mm} x {h_mm} mm")

    if st.button("🚀 Vygenerovať PDF", type="primary"):
        if locations_to_print:
            params = {'cols': cols, 'rows': rows, 'barcode_scale': b_scale}
            pdf = generate_pdf(locations_to_print, params)
            st.download_button("⬇️ Stiahnuť PDF", pdf, "lokacie.pdf", "application/pdf")
        else:
            st.error("Prázdny zoznam!")
