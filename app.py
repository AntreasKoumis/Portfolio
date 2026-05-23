import streamlit as st
from main import CustomAgent
import os
import pandas as pd

st.set_page_config(page_title="AI Recruit Agent", page_icon="🤖", layout="centered",)

st.title("🤖 AI Recruit Agent")
st.subheader("Automatisierte Bewerberanalyse & Bewertung sowie Speicherung von Bewerberdaten in einer CSV-Datei für Excel")
st.write("Lade eine PDF-Bewerbung hoch, damit der Agent die Informationen extrahieren, bewerten und in einer CSV-Datei speichern kann.")#

@st.cache_resource
def get_agent():
    return CustomAgent()
agent = get_agent()

uploaded_file = st.file_uploader("Lade dein Lebenslauf hoch", type=["pdf"])

if uploaded_file is not None:
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Datei '{uploaded_file.name}' erfolgreich hochgeladen!")

    if st.button("🚀 Bewerbung analysieren"):
        with st.spinner("Der KI-Agent arbeitet... Bitte warten..."):
            user_input = f"Analysiere die Datei {uploaded_file.name}"
            response = agent.ask(user_input)

            st.markdown("### 📋 Analyse-Ergebnis:")

            clean_response = ""

            if isinstance(clean_response, list) and len(clean_response) > 0:
                first_element = clean_response[0]
                if isinstance(first_element, dict) and 'text' in first_element:
                    content = first_element['text']
                else:
                    content = str(first_element)
            else:
                content = str(clean_response)

            response_lower = clean_response.lower()
            
            if "einstellen" in response_lower:
                st.success(clean_response)
            elif "interview" in response_lower:
                st.warning(clean_response)
            else:
                st.error(clean_response)

    if os.path.exists(uploaded_file.name):
        os.remove(uploaded_file.name)

st.markdown("---")
st.subheader("📂 Bewerberdaten (Datenbank-Live-View)")

csv_file = "bewerber.csv"

if os.path.exists(csv_file):
    try:
        df = pd.read_csv(csv_file, sep=";")
        st.dataframe(df, use_container_width=True)
        
        with open(csv_file, "rb") as file:
            st.download_button(
                label="📥 Bewerberliste als Excel/CSV herunterladen",
                data=file,
                file_name="KI_Analyse_Bewerber_aufdit.csv",
                mime="text/csv",
            )
    except Exception as e:
        st.info("Die Datenbank wird gerade aktualisiert oder ist noch leer.")

else:
    st.info("Noch keine Bewerber in der Datenbank gespeichert. Lade die erste Bewerbung hoch!")