import streamlit as st
        
        # Rozmery pre obsah
        font_size = min(box_width, box_height) * 0.15
        barcode_height = box_height * 0.25
        # Výpočet šírky čiar (fixnutý vzorec z pôvodného skriptu)
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
    with c1:
        f_n_s = st.number_input("Číslo od (X):", 0, 99, 1)
        f_l_s = st.selectbox("Písmeno od (Y):", [chr(i) for i in range(65, 91)], index=0)
    with c2:
        f_n_e = st.number_input("Číslo do (X):", 0, 99, 8)
        f_l_e = st.selectbox("Písmeno do (Y):", [chr(i) for i in range(65, 91)], index=6)

    s_s, s_e = st.columns(2)
    s_s = s_s.number_input("Blok 2 od:", 1, 999, 1)
    s_e = s_e.number_input("Blok 2 do:", 1, 999, 10)

    if block_count >= 3:
        t_s, t_e = st.columns(2)
        t_s = t_s.number_input("Blok 3 od:", 1, 999, 1)
        t_e = t_e.number_input("Blok 3 do:", 1, 999, 10)
    else:
        t_s, t_e = 1, 1

    if block_count == 4:
        fo_s, fo_e = st.columns(2)
        fo_s = fo_s.number_input("Blok 4 od:", 1, 999, 1)
        fo_e = fo_e.number_input("Blok 4 do:", 1, 999, 10)
    else:
        fo_s, fo_e = 1, 1

with col2:
    st.subheader("Rozloženie a tlač")
    cols = st.number_input("Počet stĺpcov:", 1, 15, 8)
    rows = st.number_input("Počet riadkov:", 1, 20, 6)
    barcode_scale = st.slider("Šírka čiarového kódu:", 0.5, 3.0, 1.0, 0.1)

    params = {
        'block_count': block_count, 'f_n_s': f_n_s, 'f_n_e': f_n_e,
        'f_l_s': f_l_s, 'f_l_e': f_l_e, 's_s': s_s, 's_e': s_e,
        't_s': t_s, 't_e': t_e, 'fo_s': fo_s, 'fo_e': fo_e,
        'cols': cols, 'rows': rows, 'barcode_scale': barcode_scale
    }

    if st.button("🚀 Vygenerovať PDF", type="primary"):
        pdf_buffer, count = generate_pdf(params)
        st.success(f"Vygenerovaných {count} lokácií.")
        st.download_button(
            label="⬇️ STIAHNUŤ PDF",
            data=pdf_buffer,
            file_name="lokacie_otocene.pdf",
            mime="application/pdf"
        )
