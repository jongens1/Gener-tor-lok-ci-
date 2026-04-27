import streamlit as st
        y = page_height - (row + 1) * box_height
        
        draw_rotated_location(c, x, y, location)
        
        if (i + 1) % locs_per_page == 0 and (i + 1) < len(locations):
            c.showPage()
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("🔄 Generátor lokácií (A4/A5/Štítky)")

vstup_mode = st.radio("Vyberte spôsob zadania lokácií:", ["Automatický rozsah", "Ručný zoznam (Enter)"], horizontal=True)
col1, col2 = st.columns(2)
locations_to_print = []

with col1:
    if vstup_mode == "Automatický rozsah":
        st.subheader("Konfigurácia")
        block_count = st.selectbox("Počet segmentov v kóde:", [2, 3, 4], index=1, help="Napr. 2 segmenty: 1A-01, 3 segmenty: 1A-01-01")
        
        c1, c2 = st.columns(2)
        f_n_s = c1.number_input("Číslo od:", 0, 99, 1)
        f_n_e = c2.number_input("Číslo do:", 0, 99, 5)
        f_l_s = c1.selectbox("Písmeno od:", [chr(i) for i in range(65, 91)], index=0)
        f_l_e = c2.selectbox("Písmeno do:", [chr(i) for i in range(65, 91)], index=2)
        
        s_s, s_e = st.columns(2)
        s_s_val = s_s.number_input("Segment 2 od:", 1, 999, 1)
        s_e_val = s_e.number_input("Segment 2 do:", 1, 999, 5)
        
        # Generovanie rozsahov
        first_number_range = range(f_n_s, f_n_e + 1)
        first_letter_range = [chr(i) for i in range(ord(f_l_s), ord(f_l_e) + 1)]
        sec_range = range(s_s_val, s_e_val + 1)

        if block_count == 2:
            locations_to_print = [f"{n}{l}-{s:02d}" for n in first_number_range for l in first_letter_range for s in sec_range]
        elif block_count == 3:
            t_s, t_e = st.columns(2)
            t_s_val = t_s.number_input("Segment 3 od:", 1, 999, 1)
            t_e_val = t_e.number_input("Segment 3 do:", 1, 999, 2)
            locations_to_print = [f"{n}{l}-{s:02d}-{t:02d}" for n in first_number_range for l in first_letter_range for s in sec_range for t in range(t_s_val, t_e_val + 1)]
        # ... (podobne pre 4 bloky ak treba)
    else:
        st.subheader("Ručné zadanie")
        input_text = st.text_area("Vložte lokácie (jedna na riadok):", height=200)
        if input_text.strip():
            locations_to_print = [x.strip() for x in re.split(r'[;,\n\s]+', input_text) if x.strip()]

with col2:
    st.subheader("Rozloženie tlače")
    # Pre A5 na A4 nastav: Stĺpce 1, Riadky 2 (na stojato) alebo Stĺpce 2, Riadky 1
    cols = st.number_input("Počet stĺpcov:", 1, 15, 1)
    rows = st.number_input("Počet riadkov:", 1, 25, 2)
    barcode_scale = st.slider("Hustota čiarového kódu:", 0.5, 4.0, 1.2, 0.1)
    
    st.info(f"Veľkosť jednej bunky: {round(210/cols, 1)} x {round(297/rows, 1)} mm")

    params = {'cols': cols, 'rows': rows, 'barcode_scale': barcode_scale}
    
    if st.button("🚀 Vygenerovať PDF", type="primary"):
        if locations_to_print:
            pdf_buffer = generate_pdf(locations_to_print, params)
            st.success(f"Vygenerovaných {len(locations_to_print)} štítkov.")
            st.download_button(label="⬇️ STIAHNUŤ PDF", data=pdf_buffer, file_name="lokacie.pdf", mime="application/pdf")
        else:
            st.error("Žiadne lokácie na tlač!")
