import streamlit as st
import math
from openai import OpenAI

st.set_page_config(page_title="Dobór Kabla do Silnika", page_icon="⚡", layout="wide")
st.title("⚡ Profesjonalny Kalkulator Doboru Przewodu i SWZ")

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

with col2:
    dlugosc = st.number_input("Długość linii L (m):", min_value=1, value=50, step=1)
    spadek_max = st.number_input("Dopuszczalny spadek napięcia (%):", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
    material = st.radio("Materiał żyły:", ["Miedź (Cu)", "Aluminium (Al)"])
    temperatura = st.slider("Temperatura otoczenia (°C):", min_value=10, max_value=60, value=30, step=5)
    
    st.markdown("---")
    st.subheader("Parametry sieci i zabezpieczeń")
    charakterystyka = st.selectbox("Charakterystyka bezpiecznika (wyłącznika):", ["B", "C", "D"], index=1)
    Z_sieci = st.number_input("Impedancja pętli zwarcia przed rozdzielnicą Z_sieci (Ω):", min_value=0.01, value=0.15, step=0.01)
    Ik = st.number_input("Spodziewany prąd zwarcia 3-faz. w rozdzielnicy Ik (A):", min_value=100, value=1500, step=100)
    t_zwarcie = st.number_input("Czas wyłączenia zwarcia dla cieplnej wytrzymałości t (s):", min_value=0.01, max_value=5.0, value=0.1, step=0.01)

# 2. TWARDE OBLICZENIA ELEKTRYCZNE
# Prąd znamionowy silnika
if U == 400:
    I_znamionowy = (P * 1000) / (math.sqrt(3) * U * cos_fi)
else:
    I_znamionowy = (P * 1000) / (U * cos_fi)

# Konduktywność materiału
gamma = 56 if "Miedź" in material else 34
# Rezystywność (potrzebna do SWZ)
rho = 1 / gamma

# Dobór prądu znamionowego zabezpieczenia (In_bezp) - uproszczony szereg
szereg_In = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250]
In_bezp = 6
for i in szereg_In:
    if i >= I_znamionowy * 1.25: # Współczynnik 1.25 na rozruch i przeciążenie
        In_bezp = i
        break

# Wyznaczenie krotności prądu zadziałania wyzwalacza zwarciowego (Ia) wg normy dla t <= 0.4s
# Uwzględniamy współczynnik bezpieczeństwa 1.2 lub maksymalne pasmo górne charakterystyki
if charakterystyka == "B":
    Ia = In_bezp * 5
elif charakterystyka == "C":
    Ia = In_bezp * 10
else: # D
    Ia = In_bezp * 20

# Iteracyjny dobór przekroju kabla z uwzględnieniem TRZECH warunków: Spadek, Wytrzymałość zwarciowa, SWZ
standardowe_przekroje = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
dobrany_przekroj = 1.5
powod_doboru = "Spadek napięcia / Obciążalność"

for s in standardowe_przekroje:
    # 1. Warunek spadku napięcia
    if U == 400:
        S_min_spadek = (100 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
    else:
        S_min_spadek = (200 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
        
    # 2. Warunek wytrzymałości cieplnej przy zwarciu 3f
    k_coeff = 115 if "Miedź" in material else 76
    if "XLPE" in izolacja:
        k_coeff = 143 if "Miedź" in material else 94
    S_min_cieplne = (Ik * math.sqrt(t_zwarcie)) / k_coeff
    
    # 3. Warunek SWZ (Zwarcie 1-fazowe na końcu kabla)
    # Rezystancja przewodu fazowego i ochronnego (zakładamy przekrój PE = Faza)
    # Uwzględniamy nagrzanie żył podczas zwarcia (współczynnik 1.5 dla rezystancji wg wytycznych)
    R_kabla = 2 * (rho * 1.5 * dlugosc) / s 
    X_kabla = 2 * (0.08 * dlugosc / 1000) # Reaktancja jednostkowa ok. 0.08 Ω/km
    
    Z_pętli = math.sqrt((Z_sieci + R_kabla)**2 + X_kabla**2)
    Ik1_koniec = 230 / Z_pętli # Prąd zwarcia jednofazowego na końcu kabla
    
    if s >= S_min_spadek and s >= S_min_cieplne and Ik1_koniec >= Ia:
        dobrany_przekroj = s
        if Ik1_koniec < Ia:
            powod_doboru = "SWZ (Warunek samoczynnego wyłączenia)"
        elif S_min_cieplne > S_min_spadek:
            powod_doboru = "Cieplna wytrzymałość zwarciowa"
        break
    else:
        dobrany_przekroj = s # Przypisanie awaryjne najwyższego jeśli pętla nie zamyka

# Ponowne przeliczenie parametrów ostatecznych dla wybranego przekroju do wyświetlenia
R_kabla_ost = 2 * (rho * 1.5 * dlugosc) / dobrany_przekroj
X_kabla_ost = 2 * (0.08 * dlugosc / 1000)
Z_petli_ost = math.sqrt((Z_sieci + R_kabla_ost)**2 + X_kabla_ost**2)
Ik1_ost = 230 / Z_petli_ost
swz_spelniony = Ik1_ost >= Ia

# --- ANIMACJA I PODGLĄD GRAFICZNY ---
# --- ANIMACJA I PODGLĄD GRAFICZNY ---
st.header("🖼️ Interaktywny podgląd instalacji i SWZ (Na żywo)")
oznaczenie_kabla = "YKY" if "Miedź" in material else "YAKY"
zyly = "3x" if U == 230 else "4x"

# Prędkość prądu w animacji zależna od prądu znamionowego silnika
predkosc_animacji = max(0.2, min(2.0, 15 / (I_znamionowy + 1)))

# POPRAWIONE: Zmieniono {characterystyka} na {charakterystyka} w kodzie HTML poniżej
html_vis = f"""
<div style="background: #1e293b; padding: 25px; border-radius: 12px; display: flex; justify-content: space-around; align-items: center; font-family: Arial; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
    <div style="text-align: center; width: 140px;">
        <svg width="70" height="100" viewBox="0 0 80 120">
            <rect x="5" y="5" width="70" height="110" rx="4" fill="#3f4756" stroke="#64748b" stroke-width="3"/>
            <rect x="15" y="15" width="50" height="30" fill="#0f172a"/>
            <text x="40" y="35" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">{charakterystyka}{In_bezp}A</text>
            <circle cx="40" cy="70" r="10" fill="#22c55e" />
        </svg>
        <div style="font-size: 12px; font-weight: bold; margin-top: 5px; color: #94a3b8;">Zabezpieczenie</div>
        <div style="font-size: 10px; color: #64748b;">Wymagane Ia: {Ia:.0f}A</div>
    </div>

    <div style="flex-grow: 1; margin: 0 20px; text-align: center;">
        <div style="font-size: 12px; background: #334155; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 5px;">
            <b style="color: #f59e0b;">{oznaczenie_kabla} {zyly}{dobrany_przekroj} mm²</b> ({dlugosc}m)
        </div>
        <svg width="100%" height="16">
            <rect x="0" y="2" width="100%" height="12" rx="6" fill="#0f172a"/>
            <line x1="0" y1="8" x2="100%" y2="8" stroke="#eab308" stroke-width="4" stroke-dasharray="10, 15" style="animation: flow {predkosc_animacji:.2f}s linear infinite;" />
        </svg>
        <style> @keyframes flow {{ 0% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -25; }} }} </style>
        <div style="font-size: 11px; color: #a1a1aa; margin-top: 5px;">Ik1 na końcu: <b>{Ik1_ost:.1f} A</b></div>
    </div>

    <div style="text-align: center; width: 140px;">
        <svg width="90" height="90" viewBox="0 0 100 100">
            <rect x="20" y="20" width="55" height="50" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
            <rect x="35" y="8" width="25" height="12" fill="#0ea5e9"/>
            <rect x="75" y="40" width="15" height="10" fill="#94a3b8"/>
            <rect x="5" y="25" width="15" height="40" rx="3" fill="#334155"/>
        </svg>
        <div style="font-size: 12px; font-weight: bold; margin-top: 5px; color: #38bdf8;">Silnik {P} kW</div>
        <div style="font-size: 11px; color: #22c55e; font-weight: bold;">In: {I_znamionowy:.1f} A</div>
    </div>
</div>
"""

st.components.v1.html(html_vis, height=180)

# 3. WYNIKI TECHNICZNE W KAFELKACH
st.header("2. Wyniki analizy technicznej")
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.info("📦 Zabezpieczenie obwodu")
    st.markdown(f"Sugerowany wyłącznik: **{charakterystyka} {In_bezp} A**")
    st.markdown(f"Próg wyzwolenia magnetycznego ($I_a$): **{Ia} A**")

with res_col2:
    st.info("📉 Warunki zwarciowe na końcu linii")
    st.markdown(f"Impedancja pętli zwarcia $Z_s$: **{Z_petli_ost:.3f} Ω**")
    st.markdown(f"Spodziewany prąd zwarcia $I_{{k1}}$: **{Ik1_ost:.1f} A**")

with res_col3:
    if swz_spelniony:
        st.success("✅ Warunek SWZ SPEŁNIONY!")
        st.markdown(f"Prąd zwarcia (${Ik1_ost:.1f}\\text{{ A}}$) jest WIĘKSZY niż prąd wymagany (${Ia}\\text{{ A}}$). Wyłącznik zadziała natychmiast.")
    else:
        st.error("❌ Warunek SWZ NIE SPEŁNIONY!")
        st.markdown(f"Prąd zwarcia (${Ik1_ost:.1f}\\text{{ A}}$) jest ZA MAŁY, by wyzwolić człon zwarciowy (${Ia}\\text{{ A}}$)! **Zwiększ przekrój kabla lub zmień charakterystykę na B.**")

# 4. OPINIA AI
st.header("3. Raport inżynierski Asystenta AI")
if st.button("Generuj analizę ekspercką"):
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        with st.spinner("AI analizuje pętlę zwarcia i warunki SWZ..."):
            
            # Bezpiecznie sformatowany prompt bez długich linii
            prompt = (
                f"Jesteś inżynierem elektrykiem. Użytkownik dobrał przewód dla silnika {P}kW ({U}V).\n"
                f"Wybrane zabezpieczenie to {characterystyka}{In_bezp}A (wymagany prąd wyłączenia Ia = {Ia}A).\n"
                f"Długość kabla: {dlugosc}m, materiał: {material}. Dobrany przekrój: {dobrany_przekroj}mm2.\n"
                f"Wyliczony prąd zwarcia jednofazowego na końcu linii wynosi {Ik1_ost:.1f}A.\n"
                f"Status SWZ: {'SPEŁNIONY' if swz_spelniony else 'NIE SPEŁNIONY'}.\n\n"
                f"Napisz zwięzłą opinię ekspercką w 3-4 punktach, używając żargonu elektryków:\n"
                f"1. Skomentuj wynik SWZ. Jeśli warunek nie jest spełniony, wyjaśnij z czego to wynika.\n"
                f"2. Odnieś się do doboru prądu znamionowego wyłącznika ({In_bezp}A) pod kątem rozruchu.\n"
                f"3. Podaj jedną praktyczną wskazówkę montażową dla tych warunków ułożenia ({ulozenie})."
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[{"role": "user", "content": prompt}]
            )
            st.write(response.choices.message.content)
    else:
        st.warning("Brak klucza API OpenAI w Secrets – obliczenia inżynierskie i grafika działają poprawnie bez klucza.")
