from email import message
import os
from pyexpat.errors import messages
import re
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import analyze_resume, save_to_csv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme


class AgentUI:
    def __init__(self):

        theme_dictionary = {
            "info": "cyan",
            "warning": "yellow",
            "danger": "bold red",
            "success": "bold green",
            "agent_title": "bold blue",
            "status": "italic green",
            "border": "blue",
        }

        self.custom_theme = Theme(theme_dictionary)
        self.console = Console(theme=self.custom_theme)

    def update_status(self, message):
        """Zeigt einen Lade-Spinner an."""
        return self.console.status(f"[info]{message}...[/info]", spinner="dots")

    def render_agent_response(self, raw_response):
        """Bereitet die Antwort des Agenten für das Terminal auf."""
        try:
            content = ""

            # Überprüfung der Antwortstruklur, damit wir einen cleaneren Output im Terminal habenS
            if isinstance(raw_response, list) and len(raw_response) > 0:
                first_element = raw_response[0]
                if isinstance(first_element, dict) and 'text' in first_element:
                    content = first_element['text']
                else:
                    content = str(first_element)
            else:
                content = str(raw_response)

            # Styling für das Panel mit Rich
            content_lower = content.lower()
            border_color = "bright_blue"
            status_text = "[status]Status: Erfolgreich [/status]"
            
            if "Einstellen" in content_lower:
                border_color = "green"
                status_text = "[bold green]✅Top Kandidat (Einstellen)[/bold green]"
            elif "Zum interview einladen" in content_lower:
                border_color = "yellow"
                status_text = "[bold yellow]⏳Interessant (Interviews)[/bold yellow]"
            elif "Ablehnen" in content_lower:
                border_color = "red"
                status_text = "[bold red]❌Nicht geeignet (Ablehnen)[/bold red]"
        
            md = Markdown(content.strip())

            self.console.print("\n")
            self.console.print(
                Panel(
                    md,
                    title=f"[bold {border_color}]📊 KI-Agent Analyse [/bold {border_color}]",
                    subtitle=status_text,
                    border_style=border_color,
                    padding=(1, 2),
                    expand=False,
                )
            )
        except Exception as e:
            self.console.print(
                f"[danger]Fehler:[/danger] Ungültige Antwortstruktur vom Agenten erhalten. {str(e)}"
            )


class CustomAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        load_dotenv()
        os.environ["GOOGLE_API_VERSION"] = "v1"
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name

        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.7,
        )

        self.tools = [analyze_resume, save_to_csv]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def ask(self, user_input: str):

        system_prompt = (
            "Du bist ein Senior IT-Recruiter. Deine Aufgabe ist ein tiefgreifendes Audit von Bewerbern.\n\n"
            "BEWERTUNGSSCHEMA:\n"
            "1. Hard Skills (40%): Programmiersprachen, Tools, Abschlüsse.\n"
            "2. Erfahrung (40%): Relevante Projekte, Dauer der Anstellungen.\n"
            "3. Fit (20%): Standortnähe (Lingen/Osnabrück) und Motivation.\n\n"
            "DEINE AUFGABE:\n"
            "- Extrahiere die Daten mit 'analyze_resume'.\n"
            "- Berechne einen Match-Score von 0 bis 100.\n"
            "- Erstelle eine Liste mit 3 Stärken und 2 Schwächen (Gaps).\n"
            "- Rufe 'save_to_csv' auf, um ALLES zu speichern (erweitere die Spalten im Kopf).\n"
            "- Gib am Ende ein Fazit aus: 'Einstellen', 'Interview' oder 'Ablehnen'."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]

        try:
            while True:
                max_retries = 3
                ai_msg = None
                
                for attempt in range(max_retries):
                    try:
                         ai_msg = self.llm_with_tools.invoke(messages)
                         break
                    except Exception as api_error:
                        if "429" in str(api_error) or "RESOURCE_EXHAUSTED" in str(api_error):
                            print(f"⚠️ API-Limit erreicht. Versuche es in 10 Sekunden erneut (Versuch {attempt + 1}/{max_retries})...")
                            time.sleep(60)
                        else:
                            raise api_error
                
                if not ai_msg:
                    return "Der Agent konnte die API nach mehreren Versuchen nicht erreichen."
               
                messages.append(ai_msg)

                if not ai_msg.tool_calls:
                    return ai_msg.content

                for tool_call in ai_msg.tool_calls:

                    tool_name = tool_call["name"].lower()
                    args = tool_call["args"]

                    print(f"DEBUG: Führe Tool {tool_name} aus...")

                    if tool_name == "analyze_resume":
                        tool_output = analyze_resume.invoke(args)
                        print(
                            f"DEBUG - Tool Output (Vorschau): {str(tool_output)[:100]}..."
                        )

                    elif tool_name == "save_to_csv":
                        tool_output = save_to_csv.invoke(args)
                        print(f"DEBUG - CSV Tool Output: {tool_output}")
                    else:
                        tool_output = (
                            f"Fehler Tool: {tool_name}, ist nicht implementiert"
                        )
                        messages.append(
                            ToolMessage(
                                content=str(tool_output), tool_call_id=tool_call["id"]
                            )
                        )

                    messages.append(
                        ToolMessage(
                            content=str(tool_output), tool_call_id=tool_call["id"]
                        )
                    )

                    print("DEBUG: Warte kurz auf die API...")
                    time.sleep(2)

        except Exception as e:
            return f"Fehler im Agenten-Loop {str(e)}"


if __name__ == "__main__":
    agent = CustomAgent()
    ui = AgentUI()

    test_datei = "test_bewerbung.pdf"
    user_input = f"Analysiere die Datei {test_datei} und speichere die extrahierten Daten danach sofort in die CSV-Datei."

    with ui.update_status(
        "Der Agent analysiert die Bewerbung und extrahiert die Informationen"
    ):
        response = agent.ask(user_input)
    ui.render_agent_response(response)
