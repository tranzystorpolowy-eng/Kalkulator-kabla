import streamlit as st
import math
from openai import OpenAI

st.set_page_config(page_title="Dobór Kabla do Silnika", page_icon="⚡")
st.title("⚡ Kalkulator Doboru Przekroju Kabla Zasilającego")

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
    
    # NOWE: Izolacja kabla potrzebna do współczynnika 'k'
    izolacja = st.radio("Typ izolacji kabla:", ["PVC (polwinit)", "XLPE / EPR (polietylen sieciowany)"])

with col2:
    dlugosc = st.number_input("Długość linii L (m):", min_value=1, value=30, step=1)
    spadek_max = st.number_input("Dopuszczalny spadek napięcia (%):", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
    material = st.radio("Materiał żyły:", ["Miedź (Cu)", "Aluminium (Al)"])
    temperatura = st.slider("Temperatura otoczenia (°C):", min_value=10, max_value=60, value=30, step=5)
    
    # NOWE: Parametry zwarciowe
    st.markdown("---")
    st.subheader("Parametry zwarciowe")
    Ik = st.number_input("Spodziewany prąd zwarciowy Ik (A):", min_value=100, value=1500, step=100)
    t_zwarcie = st.number_input("Czas wyłączenia zwarcia t (s):", min_value=0.01, max_value=5.0, value=0.1, step=0.01)

# 2. TWARDE OBLICZENIA ELEKTRYCZNE
# Prąd znamionowy
if U == 400:
    I_znamionowy = (P * 1000) / (math.sqrt(3) * U * cos_fi)
else:
    I_znamionowy = (P * 1000) / (U * cos_fi)

# Konduktywność materiału (spadek napięcia)
gamma = 56 if "Miedź" in material else 34

# Minimalny przekrój ze względu na spadek napięcia
if U == 400:
    S_min_spadek = (100 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
else:
    S_min_spadek = (200 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))

# NOWE: Wyznaczenie współczynnika k dla zwarć (PN-HD 60364-5-54)
if "Miedź" in material:
    k = 115 if "PVC" in izolacja else 143
else:  # Aluminium
    k = 76 if "PVC" in izolacja else 94

# NOWE: Minimalny przekrój ze względu na zwarcie
S_min_zwarcie = (Ik * math.sqrt(t_zwarcie)) / k

# Wybór ostatecznego przekroju (musi spełniać OBA warunki: spadek napięcia i zwarcie)
S_wymagany = max(S_min_spadek, S_min_zwarcie)

# Standardowe przekroje kabli w mm2
standardowe_przekroje = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
dobrany_przekroj = 1.5
for s in standardowe_przekroje:
    if s >= S_wymagany:
        dobrany_przekroj = s
        break

# Wyświetlenie wyników matematycznych

# --- SEKCJA GRAFICZNA (Schemat blokowy układu) ---
# --- ZAAWANSOWANA WIZUALIZACJA HTML/CSS/SVG ---
st.header("🖼️ Interaktywny podgląd instalacji (Na żywo)")

# Przygotowanie danych do etykiet
oznaczenie_kabla = "YKY" if "Miedź" in material else "YAKY"
zyly = "3x" if U == 230 else "4x"

# Kod HTML + inline CSS + SVG z animacją płynącego prądu
html_vis = f"""
<div style="
    background: #1e293b; 
    padding: 30px; 
    border-radius: 12px; 
    display: flex; 
    justify-content: space-around; 
    align-items: center; 
    font-family: 'Helvetica', Arial, sans-serif;
    color: white;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
">
    
    <!-- 1. ROZDZIELNICA -->
    <div style="text-align: center; width: 140px;">
        <svg width="80" height="120" viewBox="0 0 80 120" fill="none" xmlns="http://w3.org">
            <rect x="5" y="5" width="70" height="110" rx="4" fill="#3f4756" stroke="#64748b" stroke-width="3"/>
            <rect x="15" y="15" width="50" height="30" fill="#0f172a" stroke="#475569" stroke-width="2"/>
            <text x="40" y="34" fill="#38bdf8" font-size="14" font-weight="bold" text-anchor="middle">{U}V</text>
            <circle cx="25" cy="65" r="5" fill="#ef4444"/>
            <circle cx="40" cy="65" r="5" fill="#eab308"/>
            <circle cx="55" cy="65" r="5" fill="#22c55e"/>
            <rect x="25" y="85" width="30" height="15" fill="#1e293b" rx="2"/>
            <line x1="40" y1="85" x2="40" y2="100" stroke="#ef4444" stroke-width="3"/>
        </svg>
        <div style="font-size: 13px; font-weight: bold; margin-top: 8px; color: #94a3b8;">Rozdzielnica</div>
        <div style="font-size: 11px; color: #64748b;">Ik = {Ik}A</div>
    </div>

    <!-- 2. PRZEWÓD Z ANIMACJĄ PRĄDU -->
    <div style="flex-grow: 1; position: relative; margin: 0 20px; text-align: center;">
        <div style="font-size: 12px; background: #334155; padding: 6px 12px; border-radius: 20px; display: inline-block; margin-bottom: 10px; border: 1px solid #475569;">
            <b style="color: #f59e0b;">{oznaczenie_kabla} {zyly}{dobrany_przekroj} mm²</b> ({dlugosc}m)
        </div>
        
        <!-- Przewód jako linia SVG z animowanymi kropkami -->
        <svg width="100%" height="20" style="display: block;">
            <!-- Tło kabla (powłoka zewnętrzna) -->
            <rect x="0" y="4" width="100%" height="12" rx="6" fill="#0f172a" stroke="#475569" stroke-width="1"/>
            
            <!-- Linia prądu (efekt pulsowania) -->
            <line x1="0" y1="10" x2="100%" y2="10" 
                  stroke="#eab308" 
                  stroke-width="4" 
                  stroke-dasharray="10, 15" 
                  style="animation: flow 1s linear infinite;" />
        </svg>
        
        <style>
            @keyframes flow {{
                0% {{ stroke-dashoffset: 0; }}
                100% {{ stroke-dashoffset: -25; }}
            }}
        </style>
        <div style="font-size: 11px; color: #64748b; margin-top: 5px;">Izolacja: {izolacja}</div>
    </div>

    <!-- 3. SILNIK ELEKTRYCZNY -->
    <div style="text-align: center; width: 150px;">
        <svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://w3.org">
            <!-- Żebrowany korpus silnika -->
            <rect x="20" y="20" width="55" height="50" rx="6" fill="#0284c7" stroke="#0369a1" stroke-width="2"/>
            <line x1="30" y1="20" x2="30" y2="70" stroke="#0369a1" stroke-width="2"/>
            <line x1="40" y1="20" x2="40" y2="70" stroke="#0369a1" stroke-width="2"/>
            <line x1="50" y1="20" x2="50" y2="70" stroke="#0369a1" stroke-width="2"/>
            <line x1="60" y1="20" x2="60" y2="70" stroke="#0369a1" stroke-width="2"/>
            
            <!-- Skrzynka zaciskowa -->
            <rect x="35" y="8" width="25" height="12" fill="#0ea5e9" stroke="#0369a1" stroke-width="2" rx="1"/>
            
            <!-- Wał silnika -->
            <rect x="75" y="40" width="18" height="10" fill="#94a3b8" stroke="#64748b" stroke-width="1"/>
            
            <!-- Przewietrznik / Wentylator -->
            <rect x="5" y="25" width="15" height="40" rx="3" fill="#334155" stroke="#475569" stroke-width="2"/>
            <line x1="12" y1="25" x2="12" y2="65" stroke="#475569" stroke-width="1"/>
            
            <!-- Łapy silnika -->
            <rect x="25" y="70" width="10" height="8" fill="#334155"/>
            <rect x="60" y="70" width="10" height="8" fill="#334155"/>
            <rect x="15" y="76" width="65" height="4" fill="#475569" rx="1"/>
        </svg>
        <div style="font-size: 13px; font-weight: bold; margin-top: 8px; color: #38bdf8;">Silnik {P} kW</div>
        <div style="font-size: 12px; color: #22c55e; font-weight: bold;">{I_znamionowy:.2f} A</div>
    </div>
</div>
<br>
"""

# Renderowanie kodu HTML w Streamlit
st.components.v1.html(html_vis, height=220)


st.header("2. Wyniki obliczeń technicznych")

col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric(label="Obliczony prąd znamionowy silnika (In):", value=f"{I_znamionowy:.2f} A")
    st.write(f"Min. przekrój ze wp. na spadek napięcia: {S_min_spadek:.2f} mm²")
    st.write(f"Min. przekrój ze wp. na wytrzymałość zwarciową: {S_min_zwarcie:.2f} mm²")

with col_res2:
    st.success(f"Ostatecznie dobrany przekrój kabla: **{dobrany_przekroj} mm²**")
    if S_min_zwarcie > S_min_spadek:
        st.warning("⚠️ Uwaga: Warunek zwarciowy wymusił zwiększenie przekroju kabla!")

# 3. ANALIZA I KOMENTARZ EXPERTA AI
st.header("3. Opinia i zalecenia Asystenta AI")

if st.button("Wygeneruj raport i zalecenia montażowe"):
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        with st.spinner("AI analizuje warunki układania i wytrzymałość zwarciową..."):
            prompt = f"""
            Jesteś inżynierem elektrykiem, ekspertem od norm PN-HD 60364-5-52 oraz PN-HD 60364-5-54.
            Użytkownik dobrał kabel dla silnika {P} kW, napięcie {U}V, cosφ={cos_fi}, trasa {dlugosc}m.
            Kabel: żyła {material}, izolacja {izolacja}. 
            Prąd silnika: {I_znamionowy:.2f}A. 
            Wyliczony przekrój ostateczny: {dobrany_przekroj} mm2.
            
            Warunki zwarciowe: spodziewany prąd zwarcia {Ik}A przez czas {t_zwarcie}s (współczynnik k={k}).
            Przekrój min. ze wzgl. na spadek: {S_min_spadek:.2f} mm2, ze wzgl. na zwarcie: {S_min_zwarcie:.2f} mm2.
            Sposób ułożenia kabla: {ulozenie}, temp. otoczenia: {temperatura} °C.
            
            Napisz krótką, ekspercką opinię (max 4-5 zdań w punktach):
            1. Oceń, który warunek (spadek napięcia czy wytrzymałość zwarciowa przy {Ik}A) okazał się tutaj bardziej krytyczny dla kabla.
            2. Odnieś się do wpływu temperatury ({temperatura}°C) i sposobu ułożenia na bezpieczeństwo termiczne tego kabla.
            3. Jaką charakterystykę i prąd zabezpieczenia sugerujesz, aby skutecznie i szybko (w czasie {t_zwarcie}s) wyłączyło takie zwarcie, jednocześnie pozwalając na rozruch silnika?
            Pisz konkretnie, żargonem elektryków.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            st.write(response.choices.message.content)
    else:
        st.warning("Aplikacja działa w trybie offline (brak klucza API). Matematyka działa poprawnie, ale AI nie wygeneruje opinii.")
