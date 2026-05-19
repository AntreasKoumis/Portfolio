from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
import csv
import os

@tool
def analyze_resume(file_path: str) -> str:
    """Liest den Text aus einer PDF-Bewerbung aus und gibt den Inhalt zurück. 
    Nutze dieses Tool, um Informationen über einen Kandidaten zu erhalten."""
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        resume_text = "\n".join([doc.page_content for doc in documents])
        return resume_text
    except Exception as e:
        return f"Fehler beim Analysieren der Bewerbung: {str(e)}"

@tool
def save_to_csv(name: str, skills: str, erfahrung: str, standort: str, programmiersprachen: str, score: str, fazit: str):
    """Speichert die Bewerberinformationen strukturiert in einer CSV-Datei (Exel-kompatibel)."""
    
    file_name = "bewerber.csv"
    header = ["Name", "Skills", "Erfahrung", "Standort", "Programmiersprachen", "Match-Score", "Fazit"]

    try:
        file_exists = os.path.isfile(file_name)

        with open(file_name, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=";")
            if not file_exists:
                writer.writerow(header)

            writer.writerow([name, skills, erfahrung, standort, programmiersprachen, score, fazit])
    
        return f"Daten erfolgreich in {file_name} für den Kandidaten {name} gespeichert."
    
    except Exception as e:
        return f"Fehler beim Speichern in die CSV-Datei: {str(e)}"
