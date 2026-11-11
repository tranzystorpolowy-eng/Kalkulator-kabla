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
