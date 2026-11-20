import streamlit as st
import math
from openai import OpenAI

st.set_page_config(page_title="Dobór Kabla do Silnika", page_icon="⚡", layout="wide")
st.title("⚡ Profesjonalny Przemysłowy Kalkulator Doboru Przewodu i SWZ")

# 1. FORMULARZ DANYCH WEJŚCIOWYCH
st.header("1. Dane silnika i instalacji")

col1, col2 = st.columns(2)

with col1:
    P = st.number_input("Moc znamionowa silnika P (kW):", min_value=0.1, value=7.5, step=0.1)
    U = st.selectbox("Napięcie zasilania U (V):", [230, 400], index=1)
    cos_fi = st.number_input("Współczynnik mocy (cos φ):", min_value=0.5, max_value=1.0, value=0.85, step=0.01)
    
    ulozenie = st.selectbox(
        "Sposób ułożenia kabla (wg normy PN-HD 60364-5-52):",
        [
            "A1 - Przewody jednożyłowe w rurze w ścianie izolowanej cieplnie",
            "B1 - Przewody jednożyłowe w rurze na ścianie drewnianej",
            "C - Kabel wielożyłowy bezpośrednio na ścianie lub w korytku",
            "D1 - Kabel wielożyłowy w rurze w ziemi",
            "D2 - Kabel wielożyłowy bezpośrednio w ziemi",
            "E - Kabel wielożyłowy w powietrzu (wolna przestrzeń)"
        ],
        index=2
    )
    izolacja = st.radio("Typ izolacji kabla:", ["PVC (polwinit)", "XLPE / EPR (polietylen sieciowany)"])
    
    st.markdown("---")
    methoda_zasilania = st.radio("Metoda zasilania silnika:", ["Bezpośrednie z sieci (DOL)", "Zasilanie z falownika (VSD / ABB ACS880)"])

with col2:
    dlugosc = st.number_input("Długość linii L (m):", min_value=1, value=50, step=1)
    spadek_max = st.number_input("Dopuszczalny spadek napięcia (%):", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
    material = st.radio("Materiał żyły:", ["Miedź (Cu)", "Aluminium (Al)"])
    
    kod_ulozenia = ulozenie.split(" - ")[0]
    domyslna_temp = 20 if kod_ulozenia in ["D1", "D2"] else 30
    temperatura = st.slider(
        "Temperatura otoczenia / gruntu (°C):",
        min_value=10,
        max_value=60,
        value=domyslna_temp,
        step=5,
        help="Wg normy PN-HD 60364-5-52 temperatura odniesienia wynosi 30°C dla powietrza (A1-C, E) oraz 20°C dla gruntu (D1, D2)."
    )
    
    st.markdown("---")
    st.subheader("Parametry sieci i zabezpieczeń")
    
    typ_zabezpieczenia = st.radio("Rodzaj zabezpieczenia głównego:", ["Wyłącznik kompaktowy / modułowy (MCCB/MCB)", "Bezpiecznik topikowy (gG/gM)"])
    
    if "Wyłącznik" in typ_zabezpieczenia:
        charakterystyka = st.selectbox("Charakterystyka wyłącznika:", ["B", "C", "D"], index=1)
    else:
        charakterystyka = "gG"
        
    Z_sieci = st.number_input("Impedancja pętli zwarcia przed rozdzielnicą Z_sieci (Ω):", min_value=0.01, value=0.15, step=0.01)
    Ik = st.number_input("Spodziewany prąd zwarcia 3-faz. w rozdzielnicy Ik (A):", min_value=100, value=1500, step=100)
    t_zwarcie = st.number_input("Czas wyłączenia zwarcia dla cieplnej wytrzymałości t (s):", min_value=0.01, max_value=5.0, value=0.01, step=0.01)
    
    st.markdown("---")
    st.subheader("Konfiguracja linii")
    N = st.selectbox("Liczba kabli połączonych równolegle na fazę (N):", [1, 2, 3, 4], index=0)

# --- TABELE OBCIĄŻALNOŚCI DŁUGOTRWAŁEJ WG PN-HD 60364-5-52 (3 żyły obciążone, Cu) ---
# Wartości dla 30°C (A1, B1, C, E) oraz 20°C w gruncie (D1, D2)
tabele_normowe_Cu = {
    "PVC": {
        "A1": {1.5: 13.5, 2.5: 18.0, 4: 24.0, 6: 31.0, 10: 42.0, 16: 56.0, 25: 73.0, 35: 89.0, 50: 108.0, 70: 136.0, 95: 164.0, 120: 188.0, 150: 216.0, 185: 245.0, 240: 286.0},
        "B1": {1.5: 15.5, 2.5: 21.0, 4: 28.0, 6: 36.0, 10: 50.0, 16: 68.0, 25: 89.0, 35: 110.0, 50: 134.0, 70: 171.0, 95: 207.0, 120: 239.0, 150: 275.0, 185: 314.0, 240: 370.0},
        "C":  {1.5: 17.5, 2.5: 24.0, 4: 32.0, 6: 41.0, 10: 57.0, 16: 76.0, 25: 96.0, 35: 119.0, 50: 144.0, 70: 184.0, 95: 223.0, 120: 259.0, 150: 299.0, 185: 341.0, 240: 403.0},
        "D1": {1.5: 18.0, 2.5: 24.0, 4: 31.0, 6: 39.0, 10: 52.0, 16: 67.0, 25: 86.0, 35: 103.0, 50: 122.0, 70: 151.0, 95: 179.0, 120: 203.0, 150: 230.0, 185: 258.0, 240: 297.0},
        "D2": {1.5: 22.0, 2.5: 29.0, 4: 38.0, 6: 47.0, 10: 63.0, 16: 81.0, 25: 104.0, 35: 125.0, 50: 148.0, 70: 183.0, 95: 216.0, 120: 246.0, 150: 278.0, 185: 312.0, 240: 361.0},
        "E":  {1.5: 18.5, 2.5: 25.0, 4: 34.0, 6: 43.0, 10: 60.0, 16: 80.0, 25: 101.0, 35: 126.0, 50: 153.0, 70: 196.0, 95: 238.0, 120: 276.0, 150: 319.0, 185: 364.0, 240: 430.0},
    },
    "XLPE": {
        "A1": {1.5: 17.0, 2.5: 23.0, 4: 30.0, 6: 39.0, 10: 52.0, 16: 69.0, 25: 90.0, 35: 111.0, 50: 133.0, 70: 168.0, 95: 201.0, 120: 232.0, 150: 265.0, 185: 300.0, 240: 351.0},
        "B1": {1.5: 20.0, 2.5: 27.0, 4: 37.0, 6: 48.0, 10: 66.0, 16: 88.0, 25: 117.0, 35: 144.0, 50: 175.0, 70: 222.0, 95: 269.0, 120: 312.0, 150: 358.0, 185: 408.0, 240: 481.0},
        "C":  {1.5: 23.0, 2.5: 31.0, 4: 42.0, 6: 54.0, 10: 75.0, 16: 100.0, 25: 127.0, 35: 158.0, 50: 192.0, 70: 246.0, 95: 298.0, 120: 346.0, 150: 399.0, 185: 456.0, 240: 538.0},
        "D1": {1.5: 22.0, 2.5: 29.0, 4: 37.0, 6: 46.0, 10: 61.0, 16: 79.0, 25: 101.0, 35: 122.0, 50: 144.0, 70: 178.0, 95: 211.0, 120: 240.0, 150: 271.0, 185: 304.0, 240: 351.0},
        "D2": {1.5: 26.0, 2.5: 34.0, 4: 44.0, 6: 56.0, 10: 73.0, 16: 95.0, 25: 121.0, 35: 146.0, 50: 173.0, 70: 213.0, 95: 252.0, 120: 287.0, 150: 324.0, 185: 363.0, 240: 419.0},
        "E":  {1.5: 24.0, 2.5: 33.0, 4: 45.0, 6: 58.0, 10: 80.0, 16: 107.0, 25: 135.0, 35: 169.0, 50: 207.0, 70: 268.0, 95: 328.0, 120: 383.0, 150: 444.0, 185: 510.0, 240: 607.0},
    }
}

def pobierz_wspolczynnik_temp(temp, izolacja_str, kod_ul):
    typ_iz = "PVC" if "PVC" in izolacja_str else "XLPE"
    if kod_ul in ["D1", "D2"]:
        # Tabela B.52.15 - Grunt (temp. odniesienia 20°C)
        wsp_grunt = {
            "PVC":  {10: 1.10, 15: 1.05, 20: 1.00, 25: 0.95, 30: 0.89, 35: 0.84, 40: 0.77, 45: 0.71, 50: 0.63, 55: 0.55, 60: 0.45},
            "XLPE": {10: 1.07, 15: 1.04, 20: 1.00, 25: 0.96, 30: 0.93, 35: 0.89, 40: 0.85, 45: 0.80, 50: 0.76, 55: 0.71, 60: 0.65}
        }
        return wsp_grunt[typ_iz].get(temp, 1.0)
    else:
        # Tabela B.52.14 - Powietrze (temp. odniesienia 30°C)
        wsp_powietrze = {
            "PVC":  {10: 1.22, 15: 1.17, 20: 1.12, 25: 1.06, 30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50},
            "XLPE": {10: 1.15, 15: 1.12, 20: 1.08, 25: 1.04, 30: 1.00, 35: 0.96, 40: 0.91, 45: 0.87, 50: 0.82, 55: 0.76, 60: 0.71}
        }
        return wsp_powietrze[typ_iz].get(temp, 1.0)

typ_izolacji_klucz = "PVC" if "PVC" in izolacja else "XLPE"
tabela_bazowa_Cu = tabele_normowe_Cu[typ_izolacji_klucz][kod_ulozenia]
tabele_Iz = tabela_bazowa_Cu if "Miedź" in material else {k: round(v * 0.78, 1) for k, v in tabela_bazowa_Cu.items()}

f_temp = pobierz_wspolczynnik_temp(temperatura, izolacja, kod_ulozenia)
f_grup = {1: 1.0, 2: 0.80, 3: 0.70, 4: 0.65}.get(N, 0.60)

# 2. TWARDE OBLICZENIA ELEKTRYCZNE
if U == 400:
    I_znamionowy = (P * 1000) / (math.sqrt(3) * U * cos_fi)
else:
    I_znamionowy = (P * 1000) / (U * cos_fi)

gamma = 56 if "Miedź" in material else 34
rho = 1 / gamma

if "falownika" in methoda_zasilania:
    baza_ABB_ACS880 = [
        {"max_kw": 1.5, "s": 1.5, "fuse": 16, "model": "ACS880-01-04A0-3"},
        {"max_kw": 3.0, "s": 1.5, "fuse": 16, "model": "ACS880-01-07A2-3"},
        {"max_kw": 5.5, "s": 1.5, "fuse": 25, "model": "ACS880-01-12A6-3"},
        {"max_kw": 7.5, "s": 2.5, "fuse": 32, "model": "ACS880-01-17A0-3"},
        {"max_kw": 11.0, "s": 4.0, "fuse": 40, "model": "ACS880-01-25A0-3"},
        {"max_kw": 15.0, "s": 6.0, "fuse": 50, "model": "ACS880-01-32A0-3"},
        {"max_kw": 22.0, "s": 10.0, "fuse": 63, "model": "ACS880-01-45A0-3"},
        {"max_kw": 30.0, "s": 16.0, "fuse": 80, "model": "ACS880-01-61A0-3"},
        {"max_kw": 45.0, "s": 25.0, "fuse": 100, "model": "ACS880-01-87A0-3"},
        {"max_kw": 55.0, "s": 35.0, "fuse": 125, "model": "ACS880-01-105A-3"},
        {"max_kw": 75.0, "s": 50.0, "fuse": 160, "model": "ACS880-01-145A-3"},
        {"max_kw": 90.0, "s": 70.0, "fuse": 200, "model": "ACS880-01-169A-3"},
        {"max_kw": 110.0, "s": 95.0, "fuse": 250, "model": "ACS880-01-206A-3"},
        {"max_kw": 132.0, "s": 120.0, "fuse": 315, "model": "ACS880-01-246A-3"},
        {"max_kw": 160.0, "s": 150.0, "fuse": 400, "model": "ACS880-01-293A-3"},
        {"max_kw": 200.0, "s": 185.0, "fuse": 500, "model": "ACS880-04-505A-3"},
        {"max_kw": 250.0, "s": 240.0, "fuse": 630, "model": "ACS880-04-585A-3"},
        {"max_kw": 355.0, "s": 240.0, "fuse": 700, "model": "ACS880-04-681A-3"},
    ]
    
    dobrany_rek = baza_ABB_ACS880[-1]
    for rek in baza_ABB_ACS880:
        if P <= rek["max_kw"]:
            dobrany_rek = rek
            break
            
    dobrany_przekroj = dobrany_rek["s"]
    standardowe_przekroje = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
    for s in standardowe_przekroje:
        if s >= dobrany_przekroj:
            Iz_check = N * tabele_Iz[s] * f_temp * f_grup
            if Iz_check >= I_znamionowy:
                dobrany_przekroj = s
                break

    In_bezp = dobrany_rek["fuse"]
    model_falownika = dobrany_rek["model"]
    Ia = In_bezp * 1.5
    typ_zabezpieczenia = "Bezpieczniki ultraszybkie aR (Rekomendacja ABB)"
    charakterystyka = "aR"
    
    S_ost_calkowity = dobrany_przekroj * N
    R_kabla_ost = 2 * (rho * 1.5 * dlugosc) / S_ost_calkowity
    X_kabla_ost = 2 * (0.08 * dlugosc / 1000) / N
    Z_petli_ost = math.sqrt((Z_sieci + R_kabla_ost)**2 + X_kabla_ost**2)
    Ik1_ost = 230 / Z_petli_ost
    swz_spelniony = True
    Iz_ost = N * tabele_Iz[dobrany_przekroj] * f_temp * f_grup
else:
    szereg_In = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000]
    wymagany_prad_bezpiecznika = I_znamionowy * 1.25
    In_bezp = szereg_In[-1]
    for i in szereg_In:
        if i >= wymagany_prad_bezpiecznika:
            In_bezp = i
            break

    if "Wyłącznik" in typ_zabezpieczenia:
        if In_bezp <= 100:
            if charakterystyka == "B": Ia = In_bezp * 5
            elif charakterystyka == "C": Ia = In_bezp * 10
            else: Ia = In_bezp * 20
        else:
            if charakterystyka == "B": Ia = In_bezp * 3
            elif charakterystyka == "C": Ia = In_bezp * 5
            else: Ia = In_bezp * 10
    else:
        Ia = In_bezp * 15

    standardowe_przekroje = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
    dobrany_przekroj = standardowe_przekroje[-1]

    for s in standardowe_przekroje:
        S_calkowity = s * N
        if U == 400:
            S_min_spadek = (100 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
        else:
            S_min_spadek = (200 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
            
        k_coeff = 115 if "Miedź" in material else 76
        if "XLPE" in izolacja:
            k_coeff = 143 if "Miedź" in material else 94
        S_min_cieplne = (Ik * math.sqrt(t_zwarcie)) / k_coeff
        
        R_kabla = 2 * (rho * 1.5 * dlugosc) / S_calkowity
        X_kabla = 2 * (0.08 * dlugosc / 1000) / N
        Z_petli = math.sqrt((Z_sieci + R_kabla)**2 + X_kabla**2)
        Ik1_koniec = 230 / Z_petli 
        
        Iz_realne_linii = N * tabele_Iz[s] * f_temp * f_grup
        
        # Warunek przeciążeniowy wg normy: Ib <= In <= Iz
        if S_calkowity >= S_min_spadek and S_calkowity >= S_min_cieplne and Ik1_koniec >= Ia and Iz_realne_linii >= In_bezp:
            dobrany_przekroj = s
            break

    R_kabla_ost = 2 * (rho * 1.5 * dlugosc) / (dobrany_przekroj * N)
    X_kabla_ost = 2 * (0.08 * dlugosc / 1000) / N
    Z_petli_ost = math.sqrt((Z_sieci + R_kabla_ost)**2 + X_kabla_ost**2)
    Ik1_ost = 230 / Z_petli_ost
    swz_spelniony = Ik1_ost >= Ia
    Iz_ost = N * tabele_Iz[dobrany_przekroj] * f_temp * f_grup

# Rzeczywisty spadek napięcia (%)
if U == 400:
    spadek_rzeczywisty = (100 * P * 1000 * dlugosc) / (gamma * (dobrany_przekroj * N) * (U ** 2))
else:
    spadek_rzeczywisty = (200 * P * 1000 * dlugosc) / (gamma * (dobrany_przekroj * N) * (U ** 2))


# --- RESPONSYWNA DYNAMICZNA WIZUALIZACJA ---
st.header("🖼️ Graficzny schemat instalacji zasilającej")

oznaczenie_kabla = "YKY" if "Miedź" in material else "YAKY"
zyly = "3x" if U == 230 else "4x"
format_kabla = f"{N}x({oznaczenie_kabla} {zyly}{dobrany_przekroj} mm²)" if N > 1 else f"{oznaczenie_kabla} {zyly}{dobrany_przekroj} mm²"
predkosc_animacji = max(0.3, min(2.0, 20 / (I_znamionowy + 1)))

css_style = (
    "<style>"
    "@keyframes flow_anim { 0% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: -20; } }"
    ".main-container { background: #ffffff; padding: 25px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; font-family: sans-serif; color: #1e293b; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }"
    ".cable-section { flex-grow: 1; margin: 0 10px; text-align: center; min-width: 80px; }"
    ".cable-line { display: block; width: 100%; height: 16px; }"
    "@media (max-width: 768px) {"
    "  .main-container { flex-direction: column; gap: 20px; padding: 15px; }"
    "  .cable-section { width: 100%; margin: 5px 0; }"
    "  .cable-line { width: 40px; height: 60px; margin: 0 auto; }"
    "  .cable-line rect { width: 12px; height: 100%; x: 14px; y: 0; }"
    "  .cable-line line { x1: 20px; y1: 0; x2: 20px; y2: 100%; }"
    "}"
    "</style>"
)

if "falownika" in methoda_zasilania:
    przekroj_sieciowy = 1.5
    for s_test in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]:
        if s_test >= dobrany_przekroj * 0.8:
            przekroj_sieciowy = s_test
            break
    format_kabla_sieciowego = f"{oznaczenie_kabla} {zyly}{przekroj_sieciowy} mm²"

    html_vis = css_style + (
        '<div class="main-container">'
        '  <div style="background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 12px; width: 130px; text-align: center; flex-shrink: 0;">'
        f'    <svg width="50" height="70" viewBox="0 0 80 120" style="display: block; margin: 0 auto 5px auto;"><rect x="5" y="5" width="70" height="110" rx="6" fill="#e2e8f0" stroke="#94a3b8" stroke-width="3"/><rect x="15" y="15" width="50" height="30" fill="#0f172a" rx="3"/><text x="40" y="35" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">{charakterystyka}</text><circle cx="40" cy="70" r="8" fill="#eab308"/></svg>'
        f'    <div style="font-size: 11px; font-weight: 700; color: #334155;">Zasilanie sieciowe</div><div style="font-size: 10px; color: #64748b; margin-top: 2px;">Bezpieczniki {In_bezp}A</div>'
        '  </div>'
        '  <div class="cable-section">'
        '    <div style="font-size: 10px; font-weight: 700; background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 10px; display: inline-block; margin-bottom: 4px;">Kabel zasilający VSD</div>'
        f'    <svg class="cable-line"><rect x="0" y="2" width="100%" height="8" rx="4" fill="#475569"/><line x1="0" y1="6" x2="100%" y2="6" stroke="#cbd5e1" stroke-width="3" stroke-dasharray="6, 10" style="animation: flow_anim {predkosc_animacji:.2f}s linear infinite;" /></svg>'
        f'    <div style="font-size: 9px; color: #64748b; margin-top: 3px;">{format_kabla_sieciowego}</div>'
        '  </div>'
        '  <div style="background: #fffbeb; border: 2px solid #fde68a; border-radius: 10px; padding: 12px; width: 150px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); flex-shrink: 0;">'
        '    <svg width="55" height="75" viewBox="0 0 80 120" style="display: block; margin: 0 auto 5px auto;">'
        '      <rect x="10" y="5" width="60" height="110" rx="4" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/><rect x="10" y="5" width="60" height="20" fill="#334155" rx="2"/><rect x="25" y="30" width="30" height="25" fill="#0f172a" rx="2" stroke="#475569"/>'
        f'      <text x="40" y="44" fill="#22c55e" font-size="10" font-family="monospace" text-anchor="middle">50.0Hz</text><text x="40" y="52" fill="#38bdf8" font-size="8" font-family="monospace" text-anchor="middle">{I_znamionowy:.1f}A</text><rect x="20" y="10" width="40" height="4" fill="#ff0000"/><line x1="20" y1="105" x2="60" y2="105" stroke="#94a3b8" stroke-width="3" stroke-dasharray="2, 2"/>'
        '    </svg>'
        f'    <div style="font-size: 11px; font-weight: 700; color: #b45309;">Przemiennik VSD</div><div style="font-size: 10px; font-weight: bold; color: #1e293b; margin-top: 2px;">ABB {model_falownika}</div>'
        '  </div>'
        '  <div class="cable-section">'
        f'    <div style="font-size: 10px; font-weight: 700; background: #fff7ed; color: #c2410c; padding: 3px 8px; border-radius: 10px; display: inline-block; margin-bottom: 4px;">Kabel silnikowy (Sposób {kod_ulozenia})</div>'
        f'    <svg class="cable-line"><rect x="0" y="2" width="100%" height="8" rx="4" fill="#334155"/><line x1="0" y1="6" x2="100%" y2="6" stroke="#fbbf24" stroke-width="3" stroke-dasharray="6, 10" style="animation: flow_anim {predkosc_animacji:.2f}s linear infinite;" /></svg>'
        f'    <div style="font-size: 10px; font-weight: bold; color: #b45309; margin-top: 3px;">{format_kabla}</div><div style="font-size: 9px; color: #9a3412;">Długość: {dlugosc}m | Iz: {Iz_ost:.1f}A</div>'
        '  </div>'
        '  <div style="background: #f0f9ff; border: 2px solid #bae6fd; border-radius: 10px; padding: 12px; width: 140px; text-align: center; flex-shrink: 0;">'
        '    <svg width="60" height="55" viewBox="0 0 100 100" style="display: block; margin: 0 auto 5px auto;"><rect x="20" y="20" width="55" height="50" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/><line x1="30" y1="20" x2="30" y2="70" stroke="#0369a1" stroke-width="1"/><line x1="45" y1="20" x2="45" y2="70" stroke="#0369a1" stroke-width="1"/><rect x="35" y="8" width="25" height="12" fill="#0ea5e9"/><rect x="75" y="40" width="15" height="10" fill="#94a3b8"/><rect x="5" y="25" width="15" height="40" rx="3" fill="#475569"/></svg>'
        f'    <div style="font-size: 11px; font-weight: 700; color: #0369a1;">Silnik Klatkowy</div><div style="font-size: 11px; font-weight: bold; color: #0f172a;">{P} kW</div><div style="font-size: 10px; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px; font-weight: bold;">In: {I_znamionowy:.1f} A</div>'
        '  </div>'
        '</div>'
    )
else:
    html_vis = css_style + (
        '<div class="main-container">'
        '  <div style="background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 15px; width: 150px; text-align: center; flex-shrink: 0;">'
        f'    <svg width="60" height="80" viewBox="0 0 80 120" style="display: block; margin: 0 auto 10px auto;"><rect x="5" y="5" width="70" height="110" rx="6" fill="#e2e8f0" stroke="#94a3b8" stroke-width="3"/><rect x="15" y="15" width="50" height="30" fill="#0f172a" rx="3"/><text x="40" y="35" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">{"char. " + charakterystyka if "Wyłącznik" in typ_zabezpieczenia else "gG"}</text><circle cx="25" cy="65" r="5" fill="#ef4444"/><circle cx="40" cy="70" r="5" fill="#eab308"/><circle cx="55" cy="70" r="5" fill="#22c55e"/></svg>'
        f'    <div style="font-size: 13px; font-weight: 700; color: #334155;">{"Wyłącznik" if "Wyłącznik" in typ_zabezpieczenia else "Bezpiecznik"}</div><div style="font-size: 12px; font-weight: bold; color: #0284c7; margin-top: 2px;">In: {In_bezp} A</div>'
        '  </div>'
        '  <div class="cable-section">'
        f'    <div style="font-size: 12px; font-weight: 700; background: #f1f5f9; color: #b45309; padding: 5px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px; border: 1px solid #e2e8f0;">⚡ {format_kabla} (Ułożenie {kod_ulozenia})</div>'
        f'    <svg class="cable-line"><rect x="0" y="2" width="100%" height="12" rx="6" fill="#334155"/><line x1="0" y1="8" x2="100%" y2="8" stroke="#fbbf24" stroke-width="4" stroke-dasharray="8, 12" style="animation: flow_anim {predkosc_animacji:.2f}s linear infinite;" /></svg>'
        f'    <div style="font-size: 11px; font-weight: 600; color: #475569; margin-top: 6px;">Trasa: {dlugosc}m | Iz: {Iz_ost:.1f}A | Ik1: {Ik1_ost:.1f}A</div>'
        '  </div>'
        '  <div style="background: #f0f9ff; border: 2px solid #bae6fd; border-radius: 10px; padding: 15px; width: 160px; text-align: center; flex-shrink: 0;">'
        '    <svg width="60" height="60" viewBox="0 0 100 100" style="display: block; margin: 0 auto 10px auto;"><rect x="20" y="20" width="55" height="50" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/><line x1="30" y1="20" x2="30" y2="70" stroke="#0369a1" stroke-width="1"/><rect x="35" y="8" width="25" height="12" fill="#0ea5e9"/><rect x="75" y="40" width="15" height="10" fill="#94a3b8"/><rect x="5" y="25" width="15" height="40" rx="3" fill="#475569"/></svg>'
        f'    <div style="font-size: 13px; font-weight: 700; color: #0369a1;">Silnik {P} kW</div><div style="font-size: 10px; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px; font-weight: bold;">In: {I_znamionowy:.1f} A</div>'
        '  </div>'
        '</div>'
    )

iframe_height = 420 if "falownika" in methoda_zasilania else 320
st.components.v1.html(html_vis, height=iframe_height)


# 3. WYNIKI TECHNICZNE W KAFELKACH
st.header("2. Wyniki analizy technicznej")

if Ik > 15000:
    st.warning(
        "⚠️ **Wysoki prąd zwarcia źródła!** Wpisany prąd zwarcia przekracza 15 kA (charakterystyczny dla dużych rozdzielnic głównych, np. z aparatem 2500A). "
        "Jeśli linia odpływowa silnika jest dobezpieczona bezpiecznikami topikowymi (np. wkładką NH gG) lub wyłącznikiem silnikowym/kompaktowym z funkcją ograniczania, "
        "w polu 'Spodziewany prąd zwarcia Ik' należy wpisać wartość **prądu ograniczonego (odciętego)** pobraną z katalogu producenta aparatu. "
        "Zapobiegnie to drastycznemu, sztucznemu przewymiarowaniu przekrojów kabli dla mniejszych silników."
    )

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.info("📦 Dobór Kabla i Aparatu")
    st.markdown(f"Dobrany przewód: **{format_kabla}**")
    st.markdown(f"Obciążalność linii $I_z$ (ułożenie **{kod_ulozenia}**): **{Iz_ost:.1f} A** *(wsp. temp: {f_temp}, grup: {f_grup})*")
    st.markdown(f"Zabezpieczenie $I_n$: **{In_bezp} A** ({typ_zabezpieczenia})")
    st.markdown(f"Próg zadziałania $I_a$: **{Ia:.0f} A**")

with res_col2:
    st.info("📉 Parametry zwarciowe i spadek ΔU")
    st.markdown(f"Spadek napięcia $\Delta U$: **{spadek_rzeczywisty:.2f}%** (dopuszczalny: {spadek_max:.1f}%)")
    st.markdown(f"Impedancja pętli zwarcia $Z_s$: **{Z_petli_ost:.3f} Ω**")
    st.markdown(f"Wyliczony prąd zwarcia 1-fazowego $I_{{k1}}$: **{Ik1_ost:.1f} A**")

with res_col3:
    if swz_spelniony:
        st.success("✅ Warunek SWZ SPEŁNIONY!")
        st.markdown("**Wzór sprawdzający normy PN-HD 60364-4-41:**")
        st.latex(rf"I_{{k1}} \ge I_a \implies {Ik1_ost:.1f}	ext{{ A}} \ge {Ia:.0f}	ext{{ A}}")
        st.markdown("<span style='color: #22c55e; font-weight: bold;'>Wynik: POZYTYWNY.</span> Prąd zwarcia na końcu kabla jest wystarczający do natychmiastowego wyzwolenia ochrony w czasie t ≤ 0.4s.", unsafe_allow_html=True)
    else:
        st.error("❌ Warunek SWZ NIE SPEŁNIONY!")
        st.markdown("**Wzór sprawdzający normy PN-HD 60364-4-41:**")
        st.latex(rf"I_{{k1}} \ge I_a \implies {Ik1_ost:.1f}	ext{{ A}} 
ot\ge {Ia:.0f}	ext{{ A}}")
        st.markdown("<span style='color: #ef4444; font-weight: bold;'>Wynik: NEGATYWNY.</span> Prąd zwarcia jest **ZA MAŁY**, aby wyzwolić człon zwarciowy! Zagrożenie porażeniowe. Zwiększ przekrój miedzi, zwiększ liczbę kabli (N) lub wybierz bezpiecznik o czulszej charakterystyce.", unsafe_allow_html=True)

# 4. OPINIA AI
st.header("3. Raport inżynierski Asystenta AI")
if st.button("Generuj analizę ekspercką"):
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        with st.spinner("AI analizuje pętlę zwarcia i warunki SWZ..."):
            prompt = (
                f"Jesteś inżynierem elektrykiem. Użytkownik dobrał przewód dla silnika {P}kW ({U}V), prąd znamionowy Ib={I_znamionowy:.1f}A.
"
                f"Sposób ułożenia: {ulozenie}, izolacja: {izolacja}, temperatura: {temperatura}°C.
"
                f"Zabezpieczenie to {typ_zabezpieczenia} o prądzie {In_bezp}A (wymagany prąd wyłączenia Ia = {Ia}A).
"
                f"Długość kabla: {dlugosc}m, materiał: {material}, ułożony równolegle w liczbie N={N} sztuk. Dobrany przekrój pojedynczy: {dobrany_przekroj}mm2 (obciążalność Iz={Iz_ost:.1f}A).
"
                f"Wyliczony prąd zwarcia jednofazowego na końcu linii wynosi {Ik1_ost:.1f}A.
"
                f"Status SWZ: {'SPEŁNIONY' if swz_spelniony else 'NIE SPEŁNIONY'}.

"
                f"Napisz zwięzłą opinię ekspercką w 3-4 punktach, używając żargonu elektryków:
"
                f"1. Skomentuj wynik SWZ w kontekście wybranego aparatu ({typ_zabezpieczenia}).
"
                f"2. Odnieś się do decyzji o ułożeniu linii wielotorowej N={N} oraz doboru przekroju dla sposobu ułożenia {kod_ulozenia}.
"
                f"3. Podaj jedną praktyczną wskazówkę wykonawczą dla tych warunków ułożenia ({ulozenie}) i temperatury ({temperatura}°C)."
            )
            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
            st.write(response.choices[0].message.content)
    else:
        st.warning("Brak klucza API OpenAI w Secrets – obliczenia inżynierskie i grafika działają poprawnie bez klucza.")
