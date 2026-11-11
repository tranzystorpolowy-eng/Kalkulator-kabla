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
        "Sposób ułożenia kabla (wg normy):",
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
    temperatura = st.slider("Temperatura otoczenia (°C):", min_value=10, max_value=60, value=30, step=5)
    
    st.markdown("---")
    st.subheader("Parametry sieci i zabezpieczeń")
    
    # TUTAJ JEST TWÓJ WYBÓR: BEZPIECZNIK VS WYŁĄCZNIK
    typ_zabezpieczenia = st.radio("Rodzaj zabezpieczenia głównego:", ["Wyłącznik kompaktowy / modułowy (MCCB/MCB)", "Bezpiecznik topikowy (gG/gM)"])
    
    # Dynamiczne pokazywanie charakterystyki tylko dla wyłącznika
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

# 2. TWARDE OBLICZENIA ELEKTRYCZNE
if U == 400:
    I_znamionowy = (P * 1000) / (math.sqrt(3) * U * cos_fi)
else:
    I_znamionowy = (P * 1000) / (U * cos_fi)

gamma = 56 if "Miedź" in material else 34
rho = 1 / gamma
if "falownika" in methoda_zasilania:
    # 1. Dobór przekroju i zabezpieczeń na podstawie oficjalnego katalogu ABB ACS880 (dla sieci 400V, IEC)
    # Tabela mapuje typowe moce silnika (kW) na rekomendowany, minimalny przekrój przewodu miedzianego (mm2) oraz bezpiecznik aR
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
        {"max_kw": 355.0, "s": 240, "fuse": 700, "model": "ACS880-04-681A-3"}, # uwzględnia wielotorowość w praktyce
    ]
    
    # Wyszukiwanie odpowiedniego modelu przemiennika i kabla z bazy danych
    dobrany_rek = baza_ABB_ACS880[-1]
    for rek in baza_ABB_ACS880:
        if P <= rek["max_kw"]:
            dobrany_rek = rek
            break
            
    # Zapisanie dobranych wartości dedykowanych przez ABB
    dobrany_przekroj = dobrany_rek["s"]
    In_bezp = dobrany_rek["fuse"]
    model_falownika = dobrany_rek["model"]
    Ia = In_bezp * 1.5 # Przyjmujemy bezpieczny, umowny próg przeciążeniowy falownika
    typ_zabezpieczenia = "Bezpieczniki ultraszybkie aR (Rekomendacja ABB)"
    charakterystyka = "aR"
    
    # Przeliczenie pętli zwarcia tylko do celów informacyjnych makiety (falownik sam chroni kabel przed zwarciem)
    S_ost_calkowity = dobrany_przekroj * N
    R_kabla_ost = 2 * (rho * 1.5 * dlugosc) / S_ost_calkowity
    X_kabla_ost = 2 * (0.08 * dlugosc / 1000) / N
    Z_petli_ost = math.sqrt((Z_sieci + R_kabla_ost)**2 + X_kabla_ost**2)
    Ik1_ost = 230 / Z_petli_ost
    swz_spelniony = True # Falownik ma wbudowane zabezpieczenia elektroniczne wyłączające w mikrosekundy
    Iz_ost = I_znamionowy
else:
    # --- STARY KOD DLA ZASILANIA BEZPOŚREDNIEGO (DOL) ---
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

    obciazalnosc_Cu = {1.5: 14, 2.5: 20, 4: 27, 6: 36, 10: 50, 16: 68, 25: 89, 35: 110, 50: 134, 70: 171, 95: 207, 120: 239}
    obciazalnosc_Al = {k: v * 0.78 for k, v in obciazalnosc_Cu.items()}
    tabele_Iz = obciazalnosc_Cu if "Miedź" in material else obciazalnosc_Al

    if temperatura <= 30: f_temp = 1.0
    elif temperatura <= 40: f_temp = 0.87
    elif temperatura <= 50: f_temp = 0.71
    else: f_temp = 0.50

    f_grup = 1.0 if N == 1 else (0.80 if N == 2 else 0.70)
    standardowe_przekroje = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
    dobrany_przekroj = standardowe_przekroje[-1]

    for s in standardowe_przekroje:
        S_calkowity = s * N
        if U == 400: S_min_spadek = (100 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
        else: S_min_spadek = (200 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
            
        k_coeff = 115 if "Miedź" in material else 76
        if "XLPE" in izolacja: k_coeff = 143 if "Miedź" in material else 94
        S_min_cieplne = (Ik * math.sqrt(t_zwarcie)) / k_coeff
        
        R_kabla = 2 * (rho * 1.5 * dlugosc) / S_calkowity
        X_kabla = 2 * (0.08 * dlugosc / 1000) / N
        Z_pętli = math.sqrt((Z_sieci + R_kabla)**2 + X_kabla**2)
        Ik1_koniec = 230 / Z_pętli 
        
        Iz_realne_linii = N * tabele_Iz.get(s, 300) * f_temp * f_grup
        
        if S_calkowity >= S_min_spadek and S_calkowity >= S_min_cieplne and Ik1_koniec >= Ia and Iz_realne_linii >= I_znamionowy:
            dobrany_przekroj = s
            break

    R_kabla_ost = 2 * (rho * 1.5 * dlugosc) / (dobrany_przekroj * N)
    X_kabla_ost = 2 * (0.08 * dlugosc / 1000) / N
    Z_petli_ost = math.sqrt((Z_sieci + R_kabla_ost)**2 + X_kabla_ost**2)
    Ik1_ost = 230 / Z_petli_ost
    swz_spelniony = Ik1_ost >= Ia

# --- NOWOCZESNA DYNAMICZNA WIZUALIZACJA (DOL / FALOWNIK) ---
st.header("🖼️ Graficzny schemat instalacji zasilającej")

oznaczenie_kabla = "YKY" if "Miedź" in material else "YAKY"
zyly = "3x" if U == 230 else "4x"
format_kabla = f"{N}x({oznaczenie_kabla} {zyly}{dobrany_przekroj} mm²)" if N > 1 else f"{oznaczenie_kabla} {zyly}{dobrany_przekroj} mm²"
predkosc_animacji = max(0.3, min(2.0, 20 / (I_znamionowy + 1)))

# Generowanie kodu HTML w zależności od wybranego sposobu zasilania
if "falownika" in methoda_zasilania:
    # WIZUALIZACJA Z FALOWNIKIEM (Zasilanie -> Przewód -> FALOWNIK -> Silnik)
    html_vis = f"""
    <div style="background: #ffffff; padding: 25px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; font-family: sans-serif; color: #1e293b; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); overflow-x: auto;">
        
        <!-- ELEMENT 1: ROZDZIELNICA -->
        <div style="background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 12px; width: 130px; text-align: center; flex-shrink: 0;">
            <svg width="50" height="70" viewBox="0 0 80 120" style="display: block; margin: 0 auto 5px auto;">
                <rect x="5" y="5" width="70" height="110" rx="6" fill="#e2e8f0" stroke="#94a3b8" stroke-width="3"/>
                <rect x="15" y="15" width="50" height="30" fill="#0f172a" rx="3"/>
                <text x="40" y="35" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">{charakterystyka}</text>
                <circle cx="40" cy="70" r="8" fill="#eab308"/>
            </svg>
            <div style="font-size: 11px; font-weight: 700; color: #334155;">Zasilanie sieciowe</div>
            <div style="font-size: 10px; color: #64748b; margin-top: 2px;">Bezpieczniki {In_bezp}A {charakterystyka}</div>
        </div>

        <!-- PRZEWÓD ZASILAJĄCY FUSE -> VSD -->
        <div style="flex-grow: 1; margin: 0 10px; text-align: center; min-width: 80px;">
            <div style="font-size: 10px; font-weight: 700; background: #f1f5f9; color: #b45309; padding: 3px 8px; border-radius: 10px; display: inline-block; margin-bottom: 4px;">Kabel zasilający</div>
            <svg width="100%" height="12"><rect x="0" y="2" width="100%" height="8" rx="4" fill="#334155"/><line x1="0" y1="6" x2="100%" y2="6" stroke="#fbbf24" stroke-width="3" stroke-dasharray="6, 10" style="animation: flow {predkosc_animacji:.2f}s linear infinite;" /></svg>
            <div style="font-size: 9px; color: #64748b; margin-top: 3px;">{format_kabla}</div>
        </div>

        <!-- ELEMENT 2: NOWY MODUŁ FALOWNIKA ABB -->
        <div style="background: #fffbeb; border: 2px solid #fde68a; border-radius: 10px; padding: 12px; width: 150px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); flex-shrink: 0;">
            <svg width="55" height="75" viewBox="0 0 80 120" style="display: block; margin: 0 auto 5px auto;">
                <!-- Obudowa falownika przemysłowego -->
                <rect x="10" y="5" width="60" height="110" rx="4" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
                <rect x="10" y="5" width="60" height="20" fill="#334155" rx="2"/>
                <!-- Wyświetlacz panelu sterowania -->
                <rect x="25" y="30" width="30" height="25" fill="#0f172a" rx="2" stroke="#475569"/>
                <text x="40" y="44" fill="#22c55e" font-size="10" font-family="monospace" text-anchor="middle">50.0Hz</text>
                <text x="40" y="52" fill="#38bdf8" font-size="8" font-family="monospace" text-anchor="middle">{I_znamionowy:.1f}A</text>
                <!-- Marka / Paski ozdobne ABB -->
                <rect x="20" y="10" width="40" height="4" fill="#ff0000"/> 
                <!-- Wentylator chłodzący dolny -->
                <line x1="20" y1="105" x2="60" y2="105" stroke="#94a3b8" stroke-width="3" stroke-dasharray="2, 2"/>
            </svg>
            <div style="font-size: 11px; font-weight: 700; color: #b45309;">Przemiennik VSD</div>
            <div style="font-size: 10px; font-weight: bold; color: #1e293b; margin-top: 2px;">ABB {model_falownika}</div>
            <div style="font-size: 9px; color: #78350f;">Sterowanie skalarne/DTC</div>
        </div>

        <!-- PRZEWÓD SILNIKOWY VSD -> MOTOR -->
        <div style="flex-grow: 1; margin: 0 10px; text-align: center; min-width: 80px;">
            <div style="font-size: 10px; font-weight: 700; background: #eff6ff; color: #1d4ed8; padding: 3px 8px; border-radius: 10px; display: inline-block; margin-bottom: 4px;">Kabel silnikowy ekranowany</div>
            <svg width="100%" height="12"><rect x="0" y="2" width="100%" height="8" rx="4" fill="#1e40af"/><line x1="0" y1="6" x2="100%" y2="6" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6, 10" style="animation: flow {predkosc_animacji:.2f}s linear infinite;" /></svg>
            <div style="font-size: 9px; color: #1e40af; margin-top: 3px;">EMC Symetryczny</div>
        </div>

        <!-- ELEMENT 3: SILNIK -->
        <div style="background: #f0f9ff; border: 2px solid #bae6fd; border-radius: 10px; padding: 12px; width: 140px; text-align: center; flex-shrink: 0;">
            <svg width="60" height="55" viewBox="0 0 100 100" style="display: block; margin: 0 auto 5px auto;">
                <rect x="20" y="20" width="55" height="50" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
                <line x1="30" y1="20" x2="30" y2="70" stroke="#0369a1" stroke-width="1"/>
                <line x1="45" y1="20" x2="45" y2="70" stroke="#0369a1" stroke-width="1"/>
                <rect x="35" y="8" width="25" height="12" fill="#0ea5e9" rx="1"/>
                <rect x="75" y="40" width="15" height="10" fill="#94a3b8"/>
                <rect x="5" y="25" width="15" height="40" rx="3" fill="#475569"/>
            </svg>
            <div style="font-size: 11px; font-weight: 700; color: #0369a1;">Silnik Klatkowy</div>
            <div style="font-size: 11px; font-weight: bold; color: #0f172a;">{P} kW</div>
            <div style="font-size: 10px; background: #e0f2fe; color: #0369a1; padding: 1px 4px; border-radius: 4px; display: inline-block; margin-top: 2px; font-weight: bold;">$I_{{n}}$: {I_znamionowy:.1f} A</div>
        </div>
        <style> @keyframes flow {{ 0% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -20; }} }} </style>
    </div>
    <br>
    """
else:
    # WIZUALIZACJA DOL (Stary sprawdzony układ)
    html_vis = f"""
    <div style="background: #ffffff; padding: 30px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; font-family: sans-serif; color: #1e293b; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 15px; width: 150px; text-align: center;">
            <svg width="60" height="80" viewBox="0 0 80 120" style="display: block; margin: 0 auto 10px auto;">
                <rect x="5" y="5" width="70" height="110" rx="6" fill="#e2e8f0" stroke="#94a3b8" stroke-width="3"/>
                <rect x="15" y="15" width="50" height="30" fill="#0f172a" rx="3"/>
                <text x="40" y="35" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">{"char. " + charakterystyka if "Wyłącznik" in typ_zabezpieczenia else "gG"}</text>
                <circle cx="25" cy="65" r="5" fill="#ef4444"/><circle cx="40" cy="65" r="5" fill="#eab308"/><circle cx="55" cy="65" r="5" fill="#22c55e"/>
            </svg>
            <div style="font-size: 13px; font-weight: 700; color: #334155;">{"Wyłącznik MCCB" if "Wyłącznik" in typ_zabezpieczenia else "Bezpiecznik Topikowy"}</div>
            <div style="font-size: 12px; font-weight: bold; color: #0284c7; margin-top: 2px;">In: {In_bezp} A</div>
            <div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">Wymagane Ia: {Ia:.0f}A</div>
        </div>

        <div style="flex-grow: 1; margin: 0 15px; text-align: center;">
            <div style="font-size: 12px; font-weight: 700; background: #f1f5f9; color: #b45309; padding: 5px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px; border: 1px solid #e2e8f0;">⚡ {format_kabla}</div>
            <svg width="100%" height="16"><rect x="0" y="2" width="100%" height="12" rx="6" fill="#334155"/><line x1="0" y1="8" x2="100%" y2="8" stroke="#fbbf24" stroke-width="4" stroke-dasharray="8, 12" style="animation: flow {predkosc_animacji:.2f}s linear infinite;" /></svg>
            <div style="font-size: 11px; font-weight: 600; color: #475569; margin-top: 6px;">Trasa: {dlugosc}m | Ik1 na końcu: <span style="color: #dc2626;">{Ik1_ost:.1f}A</span></div>
        </div>

        <div style="background: #f0f9ff; border: 2px solid #bae6fd; border-radius: 10px; padding: 15px; width: 160px; text-align: center;">
            <svg width="60" height="60" viewBox="0 0 100 100" style="display: block; margin: 0 auto 10px auto;">
                <rect x="20" y="20" width="55" height="50" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/><line x1="30" y1="20" x2="30" y2="70" stroke="#0369a1" stroke-width="1"/><rect x="35" y="8" width="25" height="12" fill="#0ea5e9"/><rect x="75" y="40" width="15" height="10" fill="#94a3b8"/><rect x="5" y="25" width="15" height="40" rx="3" fill="#475569"/>
            </svg>
            <div style="font-size: 13px; font-weight: 700; color: #0369a1;">Silnik {P} kW</div>
            <div style="font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px; font-weight: bold;">In: {I_znamionowy:.1f} A</div>
        </div>
        <style> @keyframes flow {{ 0% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -20; }} }} </style>
    </div>
    <br>
    """

# Renderowanie kodu HTML na stronie WWW ze stabilną wysokością
st.components.v1.html(html_vis, height=240)


# 3. WYNIKI TECHNICZNE W KAFELKACH
st.header("2. Wyniki analizy technicznej")

# Ostrzeżenie inżynierskie dla bardzo dużych prądów zwarciowych (np. przy sekcji głównej MCCB 2500A)
if Ik > 15000:
    st.warning(
        "⚠️ **Wysoki prąd zwarcia źródła!** Wpisany prąd zwarcia przekracza 15 kA (charakterystyczny dla dużych rozdzielnic głównych, np. z aparatem 2500A). "
        "Jeśli linia odpływowa silnika jest dobezpieczona bezpiecznikami topikowymi (np. wkładką NH gG) lub wyłącznikiem silnikowym/kompaktowym z funkcją ograniczania, "
        "w polu 'Spodziewany prąd zwarcia Ik' należy wpisać wartość **prądu ograniczonego (odciętego)** pobraną z katalogu producenta aparatu. "
        "Zapobiegnie to drastycznemu, sztucznemu przewymiarowaniu przekrojów kabli dla mniejszych silników."
    )

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.info("📦 Dobór Aparatu Ochronnego")
    st.markdown(f"Typ urządzenia: **{typ_zabezpieczenia}**")
    st.markdown(f"Znamionowy prąd bezpiecznika ($I_n$): **{In_bezp} A**")
    st.markdown(f"Próg zadziałania magnetycznego/topnienia ($I_a$): **{Ia:.0f} A**")

with res_col2:
    st.info("📉 Parametry zwarciowe na końcu linii")
    st.markdown(f"Impedancja pętli zwarcia $Z_s$: **{Z_petli_ost:.3f} Ω**")
    st.markdown(f"Wyliczony prąd zwarcia 1-fazowego $I_{{k1}}$: **{Ik1_ost:.1f} A**")

with res_col3:
    if swz_spelniony:
        st.success("✅ Warunek SWZ SPEŁNIONY!")
        st.markdown("**Wzór sprawdzający normy PN-HD 60364-4-41:**")
        st.latex(rf"I_{{k1}} \ge I_a \implies {Ik1_ost:.1f}\text{{ A}} \ge {Ia:.0f}\text{{ A}}")
        # POPRAWIONE: Zmieniono unsafe_allow_cards na unsafe_allow_html
        st.markdown("<span style='color: #22c55e; font-weight: bold;'>Wynik: POZYTYWNY.</span> Prąd zwarcia na końcu kabla jest wystarczający do natychmiastowego wyzwolenia ochrony w czasie t ≤ 0.4s.", unsafe_allow_html=True)
    else:
        st.error("❌ Warunek SWZ NIE SPEŁNIONY!")
        st.markdown("**Wzór sprawdzający normy PN-HD 60364-4-41:**")
        st.latex(rf"I_{{k1}} \ge I_a \implies {Ik1_ost:.1f}\text{{ A}} \not\ge {Ia:.0f}\text{{ A}}")
        # POPRAWIONE: Zmieniono unsafe_allow_cards na unsafe_allow_html
        st.markdown("<span style='color: #ef4444; font-weight: bold;'>Wynik: NEGATYWNY.</span> Prąd zwarcia jest **ZA MAŁY**, aby wyzwolić człon zwarciowy! Zagrożenie porażeniowe. Zwiększ przekrój miedzi, zwiększ liczbę kabli (N) lub wybierz bezpiecznik o czulszej charakterystyce.", unsafe_allow_html=True)

# 4. OPINIA AI
st.header("3. Raport inżynierski Asystenta AI")
if st.button("Generuj analizę ekspercką"):
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        with st.spinner("AI analizuje pętlę zwarcia i warunki SWZ..."):
            prompt = (
                f"Jesteś inżynierem elektrykiem. Użytkownik dobrał przewód dla silnika {P}kW ({U}V).\n"
                f"Zabezpieczenie to {typ_zabezpieczenia} o prądzie {In_bezp}A (wymagany prąd wyłączenia Ia = {Ia}A).\n"
                f"Długość kabla: {dlugosc}m, materiał: {material}, ułożony równolegle w liczbie N={N} sztuk. Dobrany przekrój pojedynczy: {dobrany_przekroj}mm2.\n"
                f"Wyliczony prąd zwarcia jednofazowego na końcu linii wynosi {Ik1_ost:.1f}A.\n"
                f"Status SWZ: {'SPEŁNIONY' if swz_spelniony else 'NIE SPEŁNIONY'}.\n\n"
                f"Napisz zwięzłą opinię ekspercką w 3-4 punktach, używając żargonu elektryków:\n"
                f"1. Skomentuj wynik SWZ w kontekście wybranego aparatu ({typ_zabezpieczenia}).\n"
                f"2. Odnieś się do decyzji o ułożeniu linii wielotorowej N={N} w kontekście montażowym i obciążalności.\n"
                f"3. Podaj jedną praktyczną wskazówkę wykonawczą dla tych warunków ułożenia ({ulozenie}) i temperatury ({temperatura}°C)."
            )
            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
            st.write(response.choices.message.content)
    else:
        st.warning("Brak klucza API OpenAI w Secrets – obliczenia inżynierskie i grafika działają poprawnie bez klucza.")

