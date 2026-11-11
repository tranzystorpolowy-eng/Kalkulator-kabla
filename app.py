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
    
    # NOWE POLE: Sposób ułożenia kabla
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

with col2:
    dlugosc = st.number_input("Długość linii L (m):", min_value=1, value=30, step=1)
    spadek_max = st.number_input("Dopuszczalny spadek napięcia (%):", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
    material = st.radio("Materiał żyły:", ["Miedź (Cu)", "Aluminium (Al)"])
    
    # NOWE POLE: Temperatura otoczenia
    temperatura = st.slider("Temperatura otoczenia (°C):", min_value=10, max_value=60, value=30, step=5)

# 2. TWARDE OBLICZENIA ELEKTRYCZNE (Backend inżynierski)
if U == 400:
    I_znamionowy = (P * 1000) / (math.sqrt(3) * U * cos_fi)
else:
    I_znamionowy = (P * 1000) / (U * cos_fi)

# Konduktywność materiału
gamma = 56 if "Miedź" in material else 34

# Minimalny przekrój ze względu na spadek napięcia
if U == 400:
    S_min = (100 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))
else:
    S_min = (200 * P * 1000 * dlugosc) / (gamma * spadek_max * (U ** 2))

# Standardowe przekroje kabli w mm2
standardowe_przekroje = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
dobrany_przekroj = 1.5
for s in standardowe_przekroje:
    if s >= S_min:
        dobrany_przekroj = s
        break

# Wyświetlenie wyników matematycznych
st.header("2. Wyniki obliczeń technicznych")
st.metric(label="Obliczony prąd znamionowy silnika (In):", value=f"{I_znamionowy:.2f} A")
st.success(f"Sugerowany minimalny przekrój kabla (ze wp. na spadek napięcia): **{dobrany_przekroj} mm²**")

# 3. ANALIZA I KOMENTARZ EXPERTA AI
st.header("3. Opinia i zalecenia Asystenta AI")

if st.button("Wygeneruj raport i zalecenia montażowe"):
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        with st.spinner("AI analizuje warunki układania kabla..."):
            prompt = f"""
            Jesteś doświadczonym inżynierem elektrykiem, ekspertem od normy PN-HD 60364-5-52. 
            Użytkownik dobrał kabel dla silnika {P} kW, napięcie {U}V, cosφ={cos_fi}, długość trasy {dlugosc}m.
            Materiał żyły: {material}. Wyliczony prąd to {I_znamionowy:.2f}A. Wyliczony przekrój ze względu na spadek napięcia to {dobrany_przekroj} mm2.
            
            Warunki montażowe wprowadzone przez użytkownika:
            - Sposób ułożenia kabla: {ulozenie}
            - Temperatura otoczenia: {temperatura} °C
            
            Napisz krótką, ekspercką opinię (max 4-5 zdań w punktach):
            1. Jak podana temperatura otoczenia ({temperatura}°C) oraz sposób ułożenia wpływają na obciążalność długotrwałą kabla (czy potrzebne są współczynniki poprawkowe, czy przekrój {dobrany_przekroj} mm2 na pewno wystarczy)?
            2. Jak prąd rozruchowy tego silnika może wpłynąć na spadek napięcia w momencie startu?
            3. Jakie zabezpieczenie nadprądowe (charakterystyka gG, C lub D) i o jakim prądzie znamionowym wstępnie rekomendujesz do tego układu?
            Pisz konkretnie, zwięźle, czystym językiem elektryków.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            st.write(response.choices.message.content)
    else:
        st.warning("Aplikacja działa w trybie offline (brak klucza API w ustawieniach Streamlita). Wyliczenia matematyczne powyżej są poprawne, ale funkcja doradztwa AI wymaga klucza.")
