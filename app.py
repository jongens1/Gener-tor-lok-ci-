import streamlit as st
            
            # Vykreslenie čiarového kódu (vycentrovaný)
            # barcode.drawOn kreslí od bodu 0,0 - musíme ho posunúť o polovicu šírky vľavo
            barcode.drawOn(c, -bw / 2, (draw_h * 0.1)) # 10% od stredu hore
            
        except Exception as e:
            pass

        # Vykreslenie textu
        c.setFont("Helvetica-Bold", f_size)
        # drawCentredString kreslí text centrovaný na X=0
        # Y posun dole pod čiarový kód
        c.drawCentredString(0, -(draw_h * 0.2), location_code)
        
        c.restoreState()

    # Logika stránkovania
    locs_per_page = params['cols'] * params['rows']
    for i, location in enumerate(locations):
        pos = i % locs_per_page
        col = pos % params['cols']
        row = pos // params['cols']
        
        x = col * box_width
        y = page_height - (row + 1) * box_height
        
        draw_label(c, x, y, location)
        
        if (i + 1) % locs_per_page == 0 and (i + 1) < len(locations):
            c.showPage()
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI APP ---
st.title("📦 Profesionálny generátor lokácií")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Zadanie dát")
    vstup_mode = st.radio("Spôsob zadania:", ["Automatický rozsah", "Vlastný zoznam"], horizontal=True)
    
    locations_to_print = []
    if vstup_mode == "Automatický rozsah":
        c1, c2 = st.columns(2)
        f_n_s = c1.number_input("Číslo od:", 1, 99, 1)
        f_n_e = c2.number_input("Číslo do:", 1, 99, 2)
        f_l_s = c1.selectbox("Písmeno od:", [chr(i) for i in range(65, 91)], index=0)
        f_l_e = c2.selectbox("Písmeno do:", [chr(i) for i in range(65, 91)], index=1)
        
        s_s = st.number_input("Druhý segment (napr. polica) do:", 1, 50, 5)
        
        for n in range(f_n_s, f_n_e + 1):
            for l in range(ord(f_l_s), ord(f_l_e) + 1):
                for s in range(1, s_s + 1):
                    locations_to_print.append(f"{n}{chr(l)}-{s:02d}")
    else:
        txt = st.text_area("Vložte lokácie (každá na nový riadok):", height=200, placeholder="A1-01\nA1-02")
        locations_to_print = [x.strip() for x in re.split(r'[;,\n\s]+', txt) if x.strip()]

with col2:
    st.subheader("2. Formátovanie (A5 = 1 stĺpec, 2 riadky)")
    cc1, cc2 = st.columns(2)
    cols = cc1.number_input("Stĺpce na A4:", 1, 10, 1)
    rows = cc2.number_input("Riadky na A4:", 1, 10, 2)
    
    rotate_content = st.checkbox("Otočiť obsah o 90° (Landscape)", value=True)
    
    st.divider()
    st.subheader("3. Jemné doladenie veľkosti")
    bar_width = st.slider("Hrúbka čiar kódu (mm):", 0.1, 1.5, 0.6, 0.05)
    bar_height = st.slider("Výška čiarového kódu (mm):", 5, 100, 30)
    font_size = st.slider("Veľkosť písma:", 10, 150, 60)

    params = {
        'cols': cols,
        'rows': rows,
        'rotate_content': rotate_content,
        'bar_width_mm': bar_width,
        'bar_height_mm': bar_height,
        'font_size': font_size
    }

    if st.button("🚀 Vygenerovať PDF", type="primary", use_container_width=True):
        if locations_to_print:
            pdf = generate_pdf(locations_to_print, params)
            st.success(f"Pripravených {len(locations_to_print)} štítkov")
            st.download_button("⬇️ Stiahnuť PDF", pdf, "lokacie.pdf", "application/pdf", use_container_width=True)
        else:
            st.error("Zoznam je prázdny!")

st.info(f"Aktuálny rozmer bunky: **{round(210/cols,1)} x {round(297/rows,1)} mm**")
