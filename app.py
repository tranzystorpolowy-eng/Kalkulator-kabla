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
# Dla aluminium stosuje się przelicznik ~0.78 (w normie Al zaczyna się zwykle od 10/16 mm2, tu przeliczamy pełny szereg dla ciągłości obliczeń)
tabele_Iz = tabela_bazowa_Cu if "Miedź" in material else {k: round(v * 0.78, 1) for k, v in tabela_bazowa_Cu.items()}

f_temp = pobierz_wspolczynnik_temp(temperatura, izolacja, kod_ulozenia)
# Współczynnik grupowania dla przewodów ułożonych wiązką / obok siebie (uproszczony wg Tab. B.52.17)
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
    # Weryfikacja czy przy trudnym ułożeniu (np. A1, wysoka temp.) katalogowy przekrój ABB nie jest za mały termicznie
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
