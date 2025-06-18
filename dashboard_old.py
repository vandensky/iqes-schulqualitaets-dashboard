import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from textblob import TextBlob
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

# KI-Features für Textanalyse und Empfehlungen
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.warning("OpenAI nicht verfügbar. Installieren Sie 'openai' für erweiterte KI-Features.")

# Deutsche Stoppwörter für Textanalyse
GERMAN_STOPWORDS = {
    'der', 'die', 'und', 'in', 'zu', 'den', 'das', 'nicht', 'von', 'sie', 'ist', 'des', 'sich', 'mit',
    'dem', 'dass', 'er', 'es', 'ein', 'ich', 'auf', 'so', 'eine', 'auch', 'als', 'an', 'nach', 'wie',
    'im', 'für', 'man', 'aber', 'aus', 'durch', 'wenn', 'nur', 'war', 'noch', 'werden', 'bei', 'hat',
    'wir', 'was', 'wird', 'sein', 'einen', 'welche', 'sind', 'oder', 'zur', 'um', 'haben', 'einer',
    'mir', 'über', 'ihm', 'diese', 'einem', 'ihr', 'uns', 'da', 'zum', 'kann', 'doch', 'vor', 'dieser',
    'mich', 'ihn', 'du', 'hatte', 'seine', 'mehr', 'am', 'denn', 'nun', 'unter', 'sehr', 'selbst',
    'schon', 'hier', 'bis', 'habe', 'ihre', 'dann', 'ihnen', 'seiner', 'alle', 'wieder', 'meine',
    'zeit', 'gegen', 'vom', 'ganz', 'einzelnen', 'wo', 'muss', 'ohne', 'eines', 'können', 'sei'
}

# Konfiguration der Streamlit-Seite
st.set_page_config(
    page_title="Schulqualitäts-Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für besseres Design
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
    }
    .kpi-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .kpi-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .improvement-high {
        background-color: #ff4444 !important;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .improvement-medium {
        background-color: #ff9800 !important;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .improvement-low {
        background-color: #4caf50 !important;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class SchulqualitätsDashboard:
    def __init__(self):
        self.data = None
        self.processed_data = pd.DataFrame()
        self.metadata = pd.DataFrame()
        self.ki_analyzer = KI_Schulqualitäts_Analyzer()
        self.openai_client = None
        self.setup_openai()
        
    def setup_openai(self):\n        \"\"\"Setup OpenAI für KI-Features\"\"\"\n        if OPENAI_AVAILABLE:\n            api_key = os.getenv('OPENAI_API_KEY')\n            if api_key:\n                try:\n                    self.openai_client = openai.OpenAI(api_key=api_key)\n                except Exception as e:\n                    st.warning(f\"OpenAI Setup fehlgeschlagen: {e}\")\n    \n    def extract_date_from_filename(self, filename):
        """Extrahiert Datum aus Dateiname"""
        # Suche nach Mustern wie 2024.11, 2025.04, etc.
        date_patterns = [
            r'(\d{4})\.(\d{2})',  # 2024.11
            r'(\d{4})-(\d{2})',   # 2024-11
            r'(\d{4})(\d{2})',    # 202411
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                return pd.to_datetime(f"{year}-{month:02d}-01")
        
        # Fallback: aktuelles Datum
        return pd.to_datetime("today")
    
    def load_excel_files(self, uploaded_files):
        """Lädt und verarbeitet IQES Excel-Dateien"""
        all_data = []
        
        for uploaded_file in uploaded_files:
            try:
                # Excel-Datei laden - alle Blätter
                excel_data = pd.read_excel(uploaded_file, sheet_name=None)
                
                # Datum aus Dateiname extrahieren
                eval_date = self.extract_date_from_filename(uploaded_file.name)
                
                # Bildungsgang aus Pfad/Name extrahieren
                bildungsgang = "Unbekannt"  # Default
                if "BM" in uploaded_file.name or "Büromanagement" in uploaded_file.name:
                    bildungsgang = "BM"
                elif "VK" in uploaded_file.name or "Veranstaltung" in uploaded_file.name:
                    bildungsgang = "VK"
                elif "GK" in uploaded_file.name or "Gesundheit" in uploaded_file.name:
                    bildungsgang = "GK"
                elif "IT" in uploaded_file.name:
                    bildungsgang = "IT"
                
                # Evaluationstyp bestimmen
                eval_type = "Abschluss" if "Abschluss" in uploaded_file.name else "Zwischenevaluation"
                
                # Metadaten aus 'Allgemeine Angaben' extrahieren
                metadata = self.extract_metadata(excel_data.get('Allgemeine Angaben'))
                
                # IQES-spezifische Verarbeitung
                processed_data = self.process_iqes_file(excel_data, eval_date, bildungsgang, eval_type, uploaded_file.name, metadata)
                if not processed_data.empty:
                    all_data.append(processed_data)
                        
            except Exception as e:
                st.error(f"Fehler beim Laden von {uploaded_file.name}: {str(e)}")
                continue
        
        if all_data:
            self.processed_data = pd.concat(all_data, ignore_index=True)
            return True
        return False
    
    def extract_metadata(self, general_info_df):
        """Extrahiert Metadaten aus dem 'Allgemeine Angaben' Blatt"""
        metadata = {}
        
        if general_info_df is None or general_info_df.empty:
            return metadata
            
        try:
            # Durchsuche die ersten Zeilen nach Metadaten
            for idx, row in general_info_df.iterrows():
                if idx > 10:  # Nur erste 10 Zeilen betrachten
                    break
                    
                first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                second_col = row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None
                
                if "Abschlussdatum" in first_col and second_col:
                    metadata['completion_date'] = second_col
                elif "Fragebogen" in first_col and second_col:
                    metadata['questionnaire'] = second_col
                elif "eingeladene Befragte" in first_col and second_col:
                    metadata['invited_participants'] = second_col
                elif "beantwortete Fragebogen" in first_col and second_col:
                    metadata['completed_responses'] = second_col
                elif "Rücklaufquote" in first_col and second_col:
                    metadata['response_rate'] = second_col
                elif idx == 0 and first_col:  # Survey name
                    metadata['survey_name'] = first_col
                    
        except Exception as e:
            st.warning(f"Fehler beim Extrahieren der Metadaten: {str(e)}")
            
        return metadata
    
    def process_iqes_file(self, excel_data, eval_date, bildungsgang, eval_type, filename, metadata):
        """Verarbeitet eine komplette IQES Excel-Datei"""
        all_questions = []
        
        for sheet_name, df in excel_data.items():
            if df.empty:
                continue
                
            # Bestimme Fragentyp basierend auf Sheet-Name
            if "Antwortskala" in sheet_name:
                questions = self.process_scale_questions(df, sheet_name, eval_date, bildungsgang, eval_type, filename, metadata)
                all_questions.extend(questions)
            elif "Einfachauswahl" in sheet_name:
                questions = self.process_multiple_choice_questions(df, sheet_name, eval_date, bildungsgang, eval_type, filename, metadata)
                all_questions.extend(questions)
            elif "Offene Frage" in sheet_name:
                questions = self.process_open_questions(df, sheet_name, eval_date, bildungsgang, eval_type, filename, metadata)
                all_questions.extend(questions)
                
        return pd.DataFrame(all_questions)
    
    def process_scale_questions(self, df, sheet_name, eval_date, bildungsgang, eval_type, filename, metadata):
        """Verarbeitet Likert-Skala Fragen (Antwortskala)"""
        questions = []
        
        try:
            # Überschrift aus erster Zeile extrahieren
            category = ""
            if not df.empty and pd.notna(df.iloc[0, 0]):
                category = str(df.iloc[0, 0]).strip()
            
            # Fragenummer aus Sheet-Name extrahieren
            question_number = ""
            if "Frage" in sheet_name:
                question_number = sheet_name.split("Frage")[1].split("(")[0].strip()
            
            # Durch Datenzeilen iterieren (ab Zeile 3, da 0-2 Header sind)
            for idx in range(3, len(df)):
                row = df.iloc[idx]
                
                # Frage-Text aus Spalte A
                question_text = ""
                if pd.notna(row.iloc[0]):
                    question_text = str(row.iloc[0]).strip()
                    
                # Durchschnittswert aus Spalte J (Index 9)
                average_rating = None
                if len(row) > 9 and pd.notna(row.iloc[9]):
                    try:
                        average_rating = float(row.iloc[9])
                    except (ValueError, TypeError):
                        continue
                
                # N-Wert aus Spalte K (Index 10)
                n_responses = None
                if len(row) > 10 and pd.notna(row.iloc[10]):
                    try:
                        n_responses = int(row.iloc[10])
                    except (ValueError, TypeError):
                        n_responses = 0
                
                # Antwortverteilung extrahieren (Spalten B, D, F, H)
                response_distribution = {}
                for i, scale_point in enumerate([1, 2, 3, 4]):
                    col_index = 1 + (i * 2)  # Spalten B(1), D(3), F(5), H(7)
                    if len(row) > col_index and pd.notna(row.iloc[col_index]):
                        try:
                            response_distribution[f'antwort_{scale_point}'] = int(row.iloc[col_index])
                        except (ValueError, TypeError):
                            response_distribution[f'antwort_{scale_point}'] = 0
                
                # Nur verarbeiten wenn gültige Daten vorhanden
                if question_text and average_rating is not None and average_rating > 0:
                    question_data = {
                        'Datum': eval_date,
                        'Bildungsgang': bildungsgang,
                        'Evaluationstyp': eval_type,
                        'Bereich': category,
                        'Fragenummer': f"Frage {question_number}",
                        'Frage': question_text,
                        'Fragentyp': 'Antwortskala',
                        'Bewertung': average_rating,
                        'Anzahl_Antworten': n_responses or 0,
                        'Verbesserungsbedarf': self.calculate_improvement_need(average_rating),
                        'Trend': self.calculate_trend(average_rating),
                        'Quelldatei': filename,
                        'Arbeitsblatt': sheet_name,
                        'Antwortverteilung': response_distribution,
                        'Metadaten': metadata
                    }
                    questions.append(question_data)
                    
        except Exception as e:
            st.warning(f"Fehler bei der Verarbeitung von Skala-Fragen in '{sheet_name}': {str(e)}")
            
        return questions
    
    def process_multiple_choice_questions(self, df, sheet_name, eval_date, bildungsgang, eval_type, filename, metadata):
        """Verarbeitet Multiple-Choice Fragen (Einfachauswahl)"""
        questions = []
        
        try:
            # Frage-Text aus erster Zeile
            question_text = ""
            if not df.empty and pd.notna(df.iloc[0, 0]):
                question_text = str(df.iloc[0, 0]).strip()
            
            # Fragenummer aus Sheet-Name extrahieren
            question_number = ""
            if "Frage" in sheet_name:
                question_number = sheet_name.split("Frage")[1].split("(")[0].strip()
            
            choices = {}
            total_responses = 0
            
            # Durch Antwortoptionen iterieren (ab Zeile 2)
            for idx in range(2, len(df)):
                row = df.iloc[idx]
                
                # Prüfe ob gültige Zeile (hat Nummer und Text)
                if len(row) >= 2 and pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                    try:
                        choice_num = int(row.iloc[0])
                        choice_text = str(row.iloc[1]).strip()
                        choice_percentage = float(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 0
                        
                        choices[choice_num] = {
                            'text': choice_text,
                            'percentage': choice_percentage
                        }
                        
                    except (ValueError, TypeError):
                        # Prüfe auf N= Zeile
                        if "N=" in str(row.iloc[1]):
                            try:
                                total_responses = int(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 0
                            except (ValueError, TypeError):
                                pass
            
            # Erstelle einen Datensatz für die gesamte Multiple-Choice Frage
            if question_text and choices:
                question_data = {
                    'Datum': eval_date,
                    'Bildungsgang': bildungsgang,
                    'Evaluationstyp': eval_type,
                    'Bereich': 'Demographische Daten',
                    'Fragenummer': f"Frage {question_number}",
                    'Frage': question_text,
                    'Fragentyp': 'Einfachauswahl',
                    'Bewertung': None,  # Keine numerische Bewertung
                    'Anzahl_Antworten': total_responses,
                    'Verbesserungsbedarf': 'N/A',
                    'Trend': 'N/A',
                    'Quelldatei': filename,
                    'Arbeitsblatt': sheet_name,
                    'Antwortoptionen': choices,
                    'Metadaten': metadata
                }
                questions.append(question_data)
                
        except Exception as e:
            st.warning(f"Fehler bei der Verarbeitung von Multiple-Choice Fragen in '{sheet_name}': {str(e)}")
            
        return questions
    
    def process_open_questions(self, df, sheet_name, eval_date, bildungsgang, eval_type, filename, metadata):
        """Verarbeitet offene Fragen"""
        questions = []
        
        try:
            # Frage-Text aus erster Zeile
            question_text = ""
            if not df.empty and pd.notna(df.iloc[0, 0]):
                question_text = str(df.iloc[0, 0]).strip()
            
            # Fragenummer aus Sheet-Name extrahieren
            question_number = ""
            if "Frage" in sheet_name:
                question_number = sheet_name.split("Frage")[1].split("(")[0].strip()
            
            # Anzahl Antworten aus zweiter Zeile
            response_count = 0
            if len(df) > 1 and pd.notna(df.iloc[1, 0]):
                response_info = str(df.iloc[1, 0])
                if "haben" in response_info and "beantwortet" in response_info:
                    # Extrahiere Zahl aus Text wie "19 von 19 Teilnehmenden"
                    import re
                    numbers = re.findall(r'\d+', response_info)
                    if numbers:
                        response_count = int(numbers[0])
            
            # Sammle alle Textantworten
            text_responses = []
            for idx in range(3, len(df)):
                row = df.iloc[idx]
                
                # Antwort-Text aus Spalte B (Index 1)
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    response_text = str(row.iloc[1]).strip()
                    if response_text and len(response_text) > 1:  # Ignoriere sehr kurze Antworten
                        text_responses.append(response_text)
            
            # Erstelle einen Datensatz für die offene Frage
            if question_text:
                question_data = {
                    'Datum': eval_date,
                    'Bildungsgang': bildungsgang,
                    'Evaluationstyp': eval_type,
                    'Bereich': 'Qualitative Rückmeldungen',
                    'Fragenummer': f"Frage {question_number}",
                    'Frage': question_text,
                    'Fragentyp': 'Offene Frage',
                    'Bewertung': None,  # Keine numerische Bewertung
                    'Anzahl_Antworten': response_count,
                    'Verbesserungsbedarf': 'N/A',
                    'Trend': 'N/A',
                    'Quelldatei': filename,
                    'Arbeitsblatt': sheet_name,
                    'Textantworten': text_responses,
                    'Metadaten': metadata
                }
                questions.append(question_data)
                
        except Exception as e:
            st.warning(f"Fehler bei der Verarbeitung von offenen Fragen in '{sheet_name}': {str(e)}")
            
        return questions
    
    def calculate_improvement_need(self, value):
        """Berechnet Verbesserungsbedarf"""
        if value < 3.0:
            return "HOCH"
        elif value < 3.5:
            return "MITTEL"
        else:
            return "NIEDRIG"
    
    def calculate_trend(self, value):
        """Berechnet Trend (vereinfacht)"""
        if value >= 4.0:
            return "↑ Positiv"
        elif value >= 3.0:
            return "→ Stabil"
        else:
            return "↓ Negativ"
    
    def create_kpi_metrics(self):
        """Erstellt KPI-Metriken für IQES-Daten"""
        if self.processed_data.empty:
            return None
        
        # Nur Skala-Fragen für numerische Auswertung
        scale_data = self.processed_data[self.processed_data['Fragentyp'] == 'Antwortskala']
        
        if scale_data.empty:
            return None
        
        # Grundlegende Statistiken
        avg_rating = scale_data['Bewertung'].mean()
        total_evaluations = len(scale_data)
        improvement_high = len(scale_data[scale_data['Verbesserungsbedarf'] == 'HOCH'])
        improvement_medium = len(scale_data[scale_data['Verbesserungsbedarf'] == 'MITTEL'])
        improvement_low = len(scale_data[scale_data['Verbesserungsbedarf'] == 'NIEDRIG'])
        
        # Trend berechnen
        positive_trends = len(scale_data[scale_data['Trend'] == '↑ Positiv'])
        total_trends = len(scale_data)
        trend_percentage = (positive_trends / total_trends * 100) if total_trends > 0 else 0
        
        # Zusätzliche IQES-spezifische Metriken
        total_responses = scale_data['Anzahl_Antworten'].sum()
        unique_questions = len(scale_data['Frage'].unique())
        bildungsgaenge = len(scale_data['Bildungsgang'].unique())
        
        return {
            'Durchschnittsbewertung': round(avg_rating, 2),
            'Gesamtbewertungen': total_evaluations,
            'Verbesserung_Hoch': improvement_high,
            'Verbesserung_Mittel': improvement_medium,
            'Verbesserung_Niedrig': improvement_low,
            'Positive_Trends': f"{trend_percentage:.1f}%",
            'Gesamtantworten': total_responses,
            'Anzahl_Fragen': unique_questions,
            'Bildungsgaenge': bildungsgaenge
        }
    
    def create_trend_chart(self, filtered_data):
        """Erstellt Trend-Liniendiagramm für IQES-Daten"""
        if filtered_data.empty:
            return None
        
        # Nur Skala-Fragen für Trend-Analyse
        scale_data = filtered_data[filtered_data['Fragentyp'] == 'Antwortskala']
        
        if scale_data.empty:
            return None
        
        # Daten nach Datum und Bildungsgang gruppieren
        trend_data = scale_data.groupby(['Datum', 'Bildungsgang'])['Bewertung'].mean().reset_index()
        trend_data = trend_data.sort_values('Datum')
        
        fig = go.Figure()
        
        # Separate Linien für jeden Bildungsgang
        bildungsgaenge = trend_data['Bildungsgang'].unique()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, bg in enumerate(bildungsgaenge):
            bg_data = trend_data[trend_data['Bildungsgang'] == bg]
            fig.add_trace(go.Scatter(
                x=bg_data['Datum'],
                y=bg_data['Bewertung'],
                mode='lines+markers',
                name=f'Bildungsgang {bg}',
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8, color=colors[i % len(colors)])
            ))
        
        # Verbesserungsbereich markieren (unter 3.0)
        fig.add_hline(y=3.0, line_dash="dash", line_color="red", 
                     annotation_text="Verbesserungsgrenze (3.0)")
        
        # Zielbereich markieren (über 3.5)
        fig.add_hline(y=3.5, line_dash="dash", line_color="green", 
                     annotation_text="Zielbereich (3.5+)")
        
        fig.update_layout(
            title={
                'text': '📈 Zeitliche Entwicklung der IQES-Bewertungen',
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis_title='Evaluationszeitraum',
            yaxis_title='Durchschnittsbewertung (1-4 Skala)',
            yaxis=dict(range=[1, 4]),
            height=400,
            hovermode='x',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def create_improvement_chart(self, filtered_data):
        """Erstellt Verbesserungsbereich-Balkendiagramm für IQES-Daten"""
        if filtered_data.empty:
            return None
        
        # Nur Skala-Fragen für Verbesserungsanalyse
        scale_data = filtered_data[filtered_data['Fragentyp'] == 'Antwortskala']
        
        if scale_data.empty:
            return None
        
        improvement_counts = scale_data['Verbesserungsbedarf'].value_counts()
        
        colors = {
            'HOCH': '#ff4444',
            'MITTEL': '#ff9800', 
            'NIEDRIG': '#4caf50'
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=improvement_counts.index,
                y=improvement_counts.values,
                marker_color=[colors.get(x, '#1f77b4') for x in improvement_counts.index],
                text=improvement_counts.values,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Anzahl Fragen: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': '🎯 IQES-Verbesserungsbereiche',
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis_title='Verbesserungsbedarf',
            yaxis_title='Anzahl IQES-Fragen',
            height=400
        )
        
        return fig
    
    def create_category_chart(self, filtered_data):
        """Erstellt IQES-Fragen-Auswertungsdiagramm"""
        if filtered_data.empty:
            return None
        
        # Nur Skala-Fragen für Kategorien-Analyse
        scale_data = filtered_data[filtered_data['Fragentyp'] == 'Antwortskala']
        
        if scale_data.empty:
            return None
        
        # Bewertungen nach Bereichen/Kategorien gruppieren
        category_avg = scale_data.groupby('Bereich')['Bewertung'].mean().sort_values()
        
        # Farben basierend auf IQES-Bewertung (1-4 Skala)
        colors = ['#ff4444' if x < 2.5 else '#ff9800' if x < 3.0 else '#4caf50' for x in category_avg.values]
        
        fig = go.Figure(data=[
            go.Bar(
                y=category_avg.index,
                x=category_avg.values,
                orientation='h',
                marker_color=colors,
                text=[f'{x:.2f}' for x in category_avg.values],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Durchschnitt: %{x:.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': '📊 IQES-Bewertungen nach Themenbereichen',
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis_title='Durchschnittsbewertung (1-4 Skala)',
            yaxis_title='IQES-Themenbereiche',
            height=max(400, len(category_avg) * 40),
            xaxis=dict(range=[1, 4]),
            margin=dict(l=200)  # Mehr Platz für lange Kategorienamen
        )
        
        return fig
    
    def create_detailed_questions_chart(self, filtered_data):
        """Erstellt detaillierte IQES-Einzelfragen-Auswertung"""
        if filtered_data.empty:
            return None
        
        # Nur Skala-Fragen
        scale_data = filtered_data[filtered_data['Fragentyp'] == 'Antwortskala']
        
        if scale_data.empty:
            return None
        
        # Top 10 und Bottom 10 Fragen
        question_avg = scale_data.groupby('Frage')['Bewertung'].mean().sort_values()
        
        # Nur die besten und schlechtesten 10 anzeigen für bessere Lesbarkeit
        top_questions = question_avg.tail(10)
        bottom_questions = question_avg.head(10)
        
        # Kombinieren
        selected_questions = pd.concat([bottom_questions, top_questions]).drop_duplicates()
        
        # Fragen-Text kürzen für Anzeige
        shortened_labels = []
        for question in selected_questions.index:
            if len(question) > 60:
                shortened_labels.append(question[:57] + "...")
            else:
                shortened_labels.append(question)
        
        # Farben basierend auf Bewertung
        colors = ['#ff4444' if x < 2.5 else '#ff9800' if x < 3.0 else '#4caf50' for x in selected_questions.values]
        
        fig = go.Figure(data=[
            go.Bar(
                y=shortened_labels,
                x=selected_questions.values,
                orientation='h',
                marker_color=colors,
                text=[f'{x:.2f}' for x in selected_questions.values],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Bewertung: %{x:.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': '📋 IQES-Einzelfragen (Beste/Schlechteste)',
                'x': 0.5,
                'font': {'size': 18}
            },
            xaxis_title='Durchschnittsbewertung (1-4 Skala)',
            yaxis_title='Fragen',
            height=max(600, len(selected_questions) * 30),
            xaxis=dict(range=[1, 4]),
            margin=dict(l=300),  # Viel Platz für Fragen-Text
            yaxis=dict(tickfont=dict(size=10))
        )
        
        return fig
    
    def create_text_analysis_section(self, filtered_data):
        """Erstellt Textanalyse für offene Fragen"""
        if filtered_data.empty:
            return
        
        # Nur offene Fragen
        open_questions = filtered_data[filtered_data['Fragentyp'] == 'Offene Frage']
        
        if open_questions.empty:
            return
        
        st.header("💬 Textanalyse offener Fragen")
        
        # Sammle alle Textantworten
        all_responses = []
        for _, row in open_questions.iterrows():
            if 'Textantworten' in row and isinstance(row['Textantworten'], list):
                all_responses.extend(row['Textantworten'])
        
        if not all_responses:
            st.info("Keine Textantworten gefunden.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Antwort-Statistiken")
            st.metric("Gesamtanzahl Antworten", len(all_responses))
            
            # Längste und kürzeste Antworten
            response_lengths = [len(resp) for resp in all_responses]
            st.metric("Durchschnittliche Länge", f"{sum(response_lengths) / len(response_lengths):.0f} Zeichen")
            st.metric("Längste Antwort", f"{max(response_lengths)} Zeichen")
            
            # Häufige Wörter (einfache Analyse)
            import re
            from collections import Counter
            
            # Alle Wörter sammeln und normalisieren
            all_words = []
            for response in all_responses:
                words = re.findall(r'\b\w+\b', response.lower())
                # Filtere sehr kurze Wörter und häufige Stoppwörter
                filtered_words = [w for w in words if len(w) > 3 and w not in 
                                ['dass', 'sich', 'auch', 'eine', 'sind', 'haben', 'wird', 'kann', 'mehr', 'sehr', 'gibt', 'wenn', 'aber', 'oder', 'nur', 'noch', 'alle', 'man', 'bei', 'mit', 'für', 'auf', 'aus', 'ein', 'ist', 'der', 'die', 'das', 'und', 'den', 'dem', 'des', 'sie', 'er', 'es', 'ich', 'wir', 'ihr', 'mich', 'mir', 'uns']]
                all_words.extend(filtered_words)
            
            # Top Wörter
            word_counts = Counter(all_words)
            top_words = word_counts.most_common(10)
            
            st.subheader("🔤 Häufigste Begriffe")
            for word, count in top_words:
                st.write(f"• **{word}**: {count}x")
        
        with col2:
            st.subheader("📝 Beispiel-Antworten")
            
            # Zeige einige repräsentative Antworten
            sample_responses = all_responses[:5] if len(all_responses) >= 5 else all_responses
            
            for i, response in enumerate(sample_responses, 1):
                with st.expander(f"Antwort {i} ({len(response)} Zeichen)"):
                    st.write(response)
        
        # Sentiment-Analyse (vereinfacht)
        st.subheader("😊 Sentiment-Analyse")
        
        positive_words = ['gut', 'super', 'toll', 'prima', 'perfekt', 'zufrieden', 'positiv', 'freundlich', 'hilfsbereit', 'kompetent']
        negative_words = ['schlecht', 'langweilig', 'schwierig', 'problem', 'fehler', 'unfreundlich', 'chaotisch', 'unorganisiert', 'stress', 'ärgerlich']
        
        positive_count = sum([response.lower().count(word) for response in all_responses for word in positive_words])
        negative_count = sum([response.lower().count(word) for response in all_responses for word in negative_words])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🟢 Positive Begriffe", positive_count)
        
        with col2:
            st.metric("🔴 Negative Begriffe", negative_count)
        
        with col3:
            if positive_count + negative_count > 0:
                sentiment_ratio = positive_count / (positive_count + negative_count) * 100
                st.metric("😊 Positiv-Rate", f"{sentiment_ratio:.1f}%")
            else:
                st.metric("😊 Positiv-Rate", "N/A")
    
    def create_smart_insights_section(self, filtered_data):
        """Erstellt KI-gestützte Insights-Sektion"""
        if filtered_data.empty:
            return
        
        st.header("🤖 KI-Analysen & Smart Insights")
        
        # Quality Score
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quality_score = self.ki_analyzer.calculate_quality_score(filtered_data)
            score_color = "#4caf50" if quality_score >= 70 else "#ff9800" if quality_score >= 50 else "#ff4444"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {score_color}, {score_color}dd); 
                        padding: 1.5rem; border-radius: 10px; text-align: center; color: white;">
                <h3>🎯 Qualitätsscore</h3>
                <div style="font-size: 3rem; font-weight: bold;">{quality_score}</div>
                <div>von 100 Punkten</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Trend-Prediction
            trend_prediction = self.ki_analyzer.predict_future_trends(filtered_data)
            if trend_prediction:
                trend_icon = "📈" if trend_prediction['current_trend'] == 'steigend' else "📉" if trend_prediction['current_trend'] == 'fallend' else "➡️"
                trend_color = "#4caf50" if trend_prediction['current_trend'] == 'steigend' else "#ff4444" if trend_prediction['current_trend'] == 'fallend' else "#ff9800"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {trend_color}, {trend_color}dd); 
                            padding: 1.5rem; border-radius: 10px; text-align: center; color: white;">
                    <h3>{trend_icon} Trend-Vorhersage</h3>
                    <div style="font-size: 2rem; font-weight: bold;">{trend_prediction['current_trend'].upper()}</div>
                    <div>Konfidenz: {trend_prediction['confidence']:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            # Pattern Recognition
            patterns = self.ki_analyzer.detect_patterns(filtered_data)
            pattern_count = len(patterns)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #9c27b0, #9c27b0dd); 
                        padding: 1.5rem; border-radius: 10px; text-align: center; color: white;">
                <h3>🔍 Erkannte Muster</h3>
                <div style="font-size: 3rem; font-weight: bold;">{pattern_count}</div>
                <div>Signifikante Erkenntnisse</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Smart Recommendations
        st.subheader("💡 Intelligente Handlungsempfehlungen")
        recommendations = self.ki_analyzer.generate_smart_recommendations(filtered_data)
        
        if recommendations:
            for i, rec in enumerate(recommendations[:5]):  # Top 5 Empfehlungen
                priority_color = {"HOCH": "#ff4444", "MITTEL": "#ff9800", "NIEDRIG": "#4caf50"}[rec['priority']]
                priority_icon = {"HOCH": "🚨", "MITTEL": "⚠️", "NIEDRIG": "💡"}[rec['priority']]
                
                with st.expander(f"{priority_icon} {rec['title']} (Priorität: {rec['priority']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Typ:** {rec['type']}")
                        st.write(f"**Beschreibung:** {rec['description']}")
                        st.write(f"**Empfohlene Maßnahme:** {rec['action']}")
                    
                    with col2:
                        st.write(f"**Zeitrahmen:** {rec['timeline']}")
                        st.write(f"**Erwarteter Impact:** {rec['impact']}")
                        
                        st.markdown(f"""
                        <div style="background-color: {priority_color}; color: white; 
                                    padding: 0.5rem; border-radius: 5px; text-align: center; margin-top: 1rem;">
                            <strong>Priorität: {rec['priority']}</strong>
                        </div>
                        """, unsafe_allow_html=True)
    
    def create_advanced_analytics_tab(self, filtered_data):
        """Erstellt erweiterte Analytics-Tab"""
        if filtered_data.empty:
            st.info("Keine Daten für erweiterte Analysen verfügbar.")
            return
        
        st.header("🔬 Erweiterte Datenanalyse")
        
        # Cluster-Analyse
        cluster_analysis = self.ki_analyzer.analyze_improvement_patterns(filtered_data)
        if cluster_analysis:
            st.subheader("🎯 Cluster-Analyse (Machine Learning)")
            st.info("Die KI hat Ihre Daten in ähnliche Muster gruppiert:")
            
            for cluster_name, info in cluster_analysis.items():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(f"📊 {cluster_name}", f"{info['avg_rating']:.2f}", f"({info['count']} Bewertungen)")
                
                with col2:
                    trend_color = "🟢" if info['trend'] == 'Verbesserung' else "🔴"
                    st.write(f"**Trend:** {trend_color} {info['trend']}")
                
                with col3:
                    st.write(f"**Kategorien:** {len(info['categories'])}")
                    with st.expander("Details anzeigen"):
                        for cat in info['categories'][:5]:
                            st.write(f"• {cat}")
        
        # Korrelationsanalyse
        st.subheader("🔗 Korrelationsanalyse")
        
        # Numerische Korrelation
        numeric_data = filtered_data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 1:
            corr_matrix = numeric_data.corr()
            
            fig = px.imshow(
                corr_matrix, 
                title="Korrelationsmatrix der numerischen Werte",
                color_continuous_scale="RdBu_r",
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistische Zusammenfassung
        st.subheader("📈 Statistische Kennzahlen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Deskriptive Statistik:**")
            desc_stats = filtered_data['Bewertung'].describe()
            for stat, value in desc_stats.items():
                st.write(f"• {stat.title()}: {value:.3f}")
        
        with col2:
            st.write("**Verteilungsanalyse:**")
            
            # Histogramm
            fig = px.histogram(
                filtered_data, 
                x='Bewertung', 
                nbins=20,
                title="Verteilung der Bewertungen"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_prediction_chart(self, filtered_data):
        """Erstellt Vorhersage-Chart"""
        trend_prediction = self.ki_analyzer.predict_future_trends(filtered_data)
        
        if not trend_prediction:
            return None
        
        # Historische Daten
        historical_data = filtered_data.sort_values('Datum')
        
        # Future predictions
        last_date = historical_data['Datum'].max()
        future_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]  # 3 Monate
        
        fig = go.Figure()
        
        # Historische Linie
        fig.add_trace(go.Scatter(
            x=historical_data['Datum'],
            y=historical_data['Bewertung'],
            mode='lines+markers',
            name='Historische Daten',
            line=dict(color='#1f77b4', width=3)
        ))
        
        # Vorhersage-Linie
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=trend_prediction['future_predictions'],
            mode='lines+markers',
            name='KI-Vorhersage',
            line=dict(color='#ff7f0e', width=3, dash='dash'),
            marker=dict(symbol='diamond', size=10)
        ))
        
        # Unsicherheitsbereich
        confidence = trend_prediction['confidence'] / 100
        predictions = trend_prediction['future_predictions']
        
        upper_bound = [p + (1-confidence) * 0.5 for p in predictions]
        lower_bound = [p - (1-confidence) * 0.5 for p in predictions]
        
        fig.add_trace(go.Scatter(
            x=future_dates + future_dates[::-1],
            y=upper_bound + lower_bound[::-1],
            fill='toself',
            fillcolor='rgba(255,127,14,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Unsicherheitsbereich',
            showlegend=True
        ))
        
        fig.update_layout(
            title={
                'text': '🔮 KI-Trendvorhersage (Nächste 3 Monate)',
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis_title='Zeitraum',
            yaxis_title='Vorhergesagte Bewertung',
            height=400,
            hovermode='x'
        )
        
        return fig

class KI_Schulqualitäts_Analyzer:
    """KI-gestützte Analyse von Schulqualitätsdaten"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.pca = None\n        self.openai_client = None\n        self.setup_openai()\n    \n    def setup_openai(self):\n        \"\"\"Setup OpenAI für erweiterte KI-Features\"\"\"\n        if OPENAI_AVAILABLE:\n            api_key = os.getenv('OPENAI_API_KEY')\n            if api_key:\n                try:\n                    self.openai_client = openai.OpenAI(api_key=api_key)\n                except Exception:\n                    pass
        
    def analyze_improvement_patterns(self, data):
        """Analysiert Verbesserungsmuster mit Machine Learning"""
        if data.empty:
            return None
            
        # Features für ML vorbereiten
        features = []
        for _, row in data.iterrows():
            features.append([
                row['Bewertung'],
                pd.to_datetime(row['Datum']).timestamp(),
                len(str(row['Kategorie'])),  # Kategorie-Komplexität
                hash(row['Bereich']) % 1000,  # Bereich-Hash
            ])
        
        if len(features) < 3:
            return None
            
        features = np.array(features)
        
        # Clustering für Verbesserungsmuster
        try:
            scaled_features = self.scaler.fit_transform(features)
            n_clusters = min(3, len(features))
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = self.kmeans.fit_predict(scaled_features)
            
            # Cluster-Analyse
            cluster_analysis = {}
            for i in range(n_clusters):
                cluster_data = data[clusters == i]
                cluster_analysis[f'Cluster_{i}'] = {
                    'avg_rating': cluster_data['Bewertung'].mean(),
                    'count': len(cluster_data),
                    'categories': list(cluster_data['Kategorie'].unique()),
                    'trend': 'Verbesserung' if cluster_data['Bewertung'].mean() > data['Bewertung'].mean() else 'Verschlechterung'
                }
            
            return cluster_analysis
        except:
            return None
    
    def predict_future_trends(self, data):
        """Vorhersage zukünftiger Trends basierend auf historischen Daten"""
        if data.empty:
            return None
            
        # Zeitbasierte Trendanalyse
        data_sorted = data.sort_values('Datum')
        
        # Einfache lineare Regression für Trend
        x = np.arange(len(data_sorted))
        y = data_sorted['Bewertung'].values
        
        if len(x) > 1:
            trend = np.polyfit(x, y, 1)[0]  # Steigung
            
            # Nächste 3 Monate vorhersagen
            future_months = 3
            future_x = np.arange(len(x), len(x) + future_months)
            future_trend = np.poly1d(np.polyfit(x, y, 1))
            future_values = future_trend(future_x)
            
            return {
                'current_trend': 'steigend' if trend > 0 else 'fallend' if trend < 0 else 'stabil',
                'trend_strength': abs(trend),
                'future_predictions': future_values.tolist(),
                'confidence': min(100, max(0, (1 - abs(trend)) * 100))
            }
        
        return None
    
    def generate_smart_recommendations(self, data):
        """Generiert intelligente Verbesserungsempfehlungen"""
        if data.empty:
            return []
            
        recommendations = []
        
        # 1. Kritische Bereiche identifizieren
        critical_areas = data[data['Bewertung'] < 3.0]['Bereich'].value_counts()
        for area, count in critical_areas.head(3).items():
            recommendations.append({
                'priority': 'HOCH',
                'type': 'Kritischer Bereich',
                'title': f'Sofortmaßnahmen für "{area}"',
                'description': f'Bereich zeigt {count} kritische Bewertungen (< 3.0). Dringende Intervention erforderlich.',
                'action': f'Workshop und Analyse für "{area}" durchführen',
                'timeline': 'Sofort',
                'impact': 'Hoch'
            })
        
        # 2. Trend-basierte Empfehlungen
        declining_categories = []
        for category in data['Kategorie'].unique():
            cat_data = data[data['Kategorie'] == category].sort_values('Datum')
            if len(cat_data) > 1:
                recent_avg = cat_data.tail(2)['Bewertung'].mean()
                older_avg = cat_data.head(2)['Bewertung'].mean()
                if recent_avg < older_avg - 0.3:  # Verschlechterung um 0.3 Punkte
                    declining_categories.append((category, recent_avg, older_avg))
        
        for cat, recent, older in declining_categories[:2]:
            recommendations.append({
                'priority': 'MITTEL',
                'type': 'Negativer Trend',
                'title': f'Trend-Umkehr bei "{cat}"',
                'description': f'Bewertung ist von {older:.1f} auf {recent:.1f} gesunken.',
                'action': f'Ursachenanalyse und Verbesserungsplan für "{cat}"',
                'timeline': '2-4 Wochen',
                'impact': 'Mittel'
            })
        
        # 3. Erfolgsbeispiele identifizieren
        success_areas = data[data['Bewertung'] >= 4.0]['Bereich'].value_counts()
        for area, count in success_areas.head(2).items():
            recommendations.append({
                'priority': 'NIEDRIG',
                'type': 'Best Practice',
                'title': f'Erfolgsmodell "{area}" übertragen',
                'description': f'Bereich zeigt {count} sehr gute Bewertungen (≥ 4.0).',
                'action': f'Best Practices aus "{area}" auf andere Bereiche übertragen',
                'timeline': '1-3 Monate',
                'impact': 'Hoch'
            })
        
        # 4. Statistische Anomalien
        overall_mean = data['Bewertung'].mean()
        overall_std = data['Bewertung'].std()
        
        for category in data['Kategorie'].unique():
            cat_mean = data[data['Kategorie'] == category]['Bewertung'].mean()
            if abs(cat_mean - overall_mean) > 2 * overall_std:
                priority = 'HOCH' if cat_mean < overall_mean else 'NIEDRIG'
                recommendations.append({
                    'priority': priority,
                    'type': 'Statistische Anomalie',
                    'title': f'Ausreißer-Analyse für "{category}"',
                    'description': f'Kategorie weicht stark vom Durchschnitt ab (Ø{cat_mean:.1f} vs {overall_mean:.1f}).',
                    'action': f'Detailanalyse der Ursachen für extreme Bewertung',
                    'timeline': '1-2 Wochen',
                    'impact': 'Mittel'
                })
        
        return sorted(recommendations, key=lambda x: {'HOCH': 3, 'MITTEL': 2, 'NIEDRIG': 1}[x['priority']], reverse=True)
    
    def calculate_quality_score(self, data):
        """Berechnet einen intelligenten Qualitätsscore"""
        if data.empty:
            return 0
        
        # Gewichtete Berechnung
        weights = {
            'current_performance': 0.4,  # Aktuelle Leistung
            'trend': 0.3,               # Entwicklungstrend
            'consistency': 0.2,         # Konsistenz
            'coverage': 0.1             # Abdeckung
        }
        
        # Aktuelle Leistung (0-100)
        current_score = (data['Bewertung'].mean() - 1) / 4 * 100
        
        # Trend-Score
        recent_data = data.sort_values('Datum').tail(10)
        older_data = data.sort_values('Datum').head(10)
        trend_score = 50  # Neutral
        if len(recent_data) > 0 and len(older_data) > 0:
            trend_diff = recent_data['Bewertung'].mean() - older_data['Bewertung'].mean()
            trend_score = max(0, min(100, 50 + trend_diff * 25))
        
        # Konsistenz-Score (niedriger Std = höhere Konsistenz)
        consistency_score = max(0, 100 - data['Bewertung'].std() * 50)
        
        # Abdeckungs-Score (mehr Kategorien = bessere Abdeckung)
        coverage_score = min(100, len(data['Kategorie'].unique()) * 10)
        
        # Gewichteter Gesamtscore
        total_score = (
            current_score * weights['current_performance'] +
            trend_score * weights['trend'] +
            consistency_score * weights['consistency'] +
            coverage_score * weights['coverage']
        )
        
        return round(total_score, 1)
    
    def detect_patterns(self, data):
        """Erkennt Muster in den Daten"""
        patterns = []
        
        if data.empty:
            return patterns
        
        # Saisonale Muster
        data['Monat'] = pd.to_datetime(data['Datum']).dt.month
        monthly_avg = data.groupby('Monat')['Bewertung'].mean()
        
        if len(monthly_avg) > 1:
            best_month = monthly_avg.idxmax()
            worst_month = monthly_avg.idxmin()
            
            patterns.append({
                'type': 'Saisonales Muster',
                'description': f'Beste Bewertungen im Monat {best_month} ({monthly_avg[best_month]:.1f}), schlechteste im Monat {worst_month} ({monthly_avg[worst_month]:.1f})',
                'significance': 'Mittel'
            })
        
        # Kategorie-Korrelationen
        category_scores = data.groupby('Kategorie')['Bewertung'].mean().sort_values(ascending=False)
        
        if len(category_scores) > 1:
            patterns.append({
                'type': 'Kategorie-Ranking',
                'description': f'Beste Kategorie: "{category_scores.index[0]}" ({category_scores.iloc[0]:.1f}), Schwächste: "{category_scores.index[-1]}" ({category_scores.iloc[-1]:.1f})',
                'significance': 'Hoch'
            })
        
        return patterns

    def analyze_german_text_responses(self, text_responses):\n        \"\"\"Analysiert deutsche Textantworten mit KI-Features\"\"\"\n        if not text_responses or len(text_responses) == 0:\n            return {}\n        \n        analysis = {\n            'total_responses': len(text_responses),\n            'avg_length': np.mean([len(text) for text in text_responses]),\n            'sentiment_analysis': self.analyze_sentiment_german(text_responses),\n            'keyword_analysis': self.extract_german_keywords(text_responses)\n        }\n        \n        # Erweiterte OpenAI-Analyse falls verf\u00fcgbar\n        if self.openai_client:\n            analysis['ai_insights'] = self.generate_ai_insights_german(text_responses)\n        \n        return analysis\n    \n    def analyze_sentiment_german(self, texts):\n        \"\"\"Analysiert Sentiment deutscher Texte\"\"\"\n        positive_words = {\n            'gut', 'super', 'toll', 'sch\u00f6n', 'prima', 'klasse', 'perfekt', 'zufrieden', \n            'positiv', 'gefallen', 'freude', 'erfolg', 'dankbar', 'empfehlen'\n        }\n        \n        negative_words = {\n            'schlecht', 'schlimm', 'negativ', 'problem', 'schwierig', 'unzufrieden',\n            'fehler', 'mangel', 'kritik', 'beschwerde', 'verbesserung', 'stress'\n        }\n        \n        sentiment_scores = []\n        for text in texts:\n            words = set(text.lower().split())\n            positive_count = len(words.intersection(positive_words))\n            negative_count = len(words.intersection(negative_words))\n            \n            if positive_count + negative_count > 0:\n                score = (positive_count - negative_count) / (positive_count + negative_count)\n            else:\n                score = 0\n            \n            sentiment_scores.append(score)\n        \n        return {\n            'avg_sentiment': np.mean(sentiment_scores),\n            'positive_ratio': len([s for s in sentiment_scores if s > 0]) / len(sentiment_scores),\n            'negative_ratio': len([s for s in sentiment_scores if s < 0]) / len(sentiment_scores)\n        }\n    \n    def extract_german_keywords(self, texts):\n        \"\"\"Extrahiert deutsche Schl\u00fcsselw\u00f6rter\"\"\"\n        word_freq = {}\n        \n        for text in texts:\n            words = re.findall(r'\\b\\w+\\b', text.lower())\n            for word in words:\n                if len(word) > 3 and word not in GERMAN_STOPWORDS:\n                    word_freq[word] = word_freq.get(word, 0) + 1\n        \n        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)\n        return dict(sorted_words[:15])  # Top 15 W\u00f6rter\n    \n    def generate_ai_insights_german(self, texts):\n        \"\"\"Generiert KI-Insights f\u00fcr deutsche Texte mit OpenAI\"\"\"\n        if not self.openai_client or len(texts) == 0:\n            return None\n        \n        sample_texts = texts[:8] if len(texts) > 8 else texts\n        combined_text = '\\n\\n'.join(sample_texts)\n        \n        try:\n            response = self.openai_client.chat.completions.create(\n                model=\"gpt-3.5-turbo\",\n                messages=[\n                    {\n                        \"role\": \"system\",\n                        \"content\": \"Du bist Schulentwicklungsexperte. Analysiere IQES-Sch\u00fclerr\u00fcckmeldungen auf Deutsch.\"\n                    },\n                    {\n                        \"role\": \"user\",\n                        \"content\": f\"Analysiere diese Antworten und gib 3 konkrete Handlungsempfehlungen:\\n\\n{combined_text}\"\n                    }\n                ],\n                max_tokens=400,\n                temperature=0.3\n            )\n            \n            return response.choices[0].message.content\n            \n        except Exception:\n            return None\n\ndef main():
    # Header
    st.markdown('<h1 class="main-header">🎓 IQES-AUSWERTUNGS-DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Dashboard-Instanz
    dashboard = SchulqualitätsDashboard()
    
    # Sidebar für Upload und Filter
    with st.sidebar:
        st.header("📁 Daten-Upload")
        uploaded_files = st.file_uploader(
            "IQES Excel-Dateien hochladen",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="Laden Sie Ihre IQES-Evaluationsdateien hoch. Mehrere Dateien und Arbeitsblätter werden automatisch verarbeitet."
        )
        
        if uploaded_files:
            with st.spinner('📊 Daten werden verarbeitet...'):
                if dashboard.load_excel_files(uploaded_files):
                    st.success(f"✅ {len(uploaded_files)} Dateien erfolgreich geladen!")
                    
                    # Filter-Optionen
                    st.header("🔍 Filter")
                    
                    # Bildungsgang-Filter
                    bildungsgaenge = ['Alle'] + list(dashboard.processed_data['Bildungsgang'].unique())
                    selected_bildungsgang = st.selectbox("Bildungsgang", bildungsgaenge)
                    
                    # Evaluationstyp-Filter
                    eval_typen = ['Alle'] + list(dashboard.processed_data['Evaluationstyp'].unique())
                    selected_eval_typ = st.selectbox("Evaluationstyp", eval_typen)
                    
                    # Zeitraum-Filter
                    if not dashboard.processed_data.empty:
                        min_date = dashboard.processed_data['Datum'].min()
                        max_date = dashboard.processed_data['Datum'].max()
                        
                        date_range = st.date_input(
                            "Zeitraum",
                            value=(min_date, max_date),
                            min_value=min_date,
                            max_value=max_date
                        )
                else:
                    st.error("❌ Fehler beim Laden der Dateien!")
    
    # Hauptbereich
    if not dashboard.processed_data.empty:
        # Daten filtern
        filtered_data = dashboard.processed_data.copy()
        
        if selected_bildungsgang != 'Alle':
            filtered_data = filtered_data[filtered_data['Bildungsgang'] == selected_bildungsgang]
        
        if selected_eval_typ != 'Alle':
            filtered_data = filtered_data[filtered_data['Evaluationstyp'] == selected_eval_typ]
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_data = filtered_data[
                (filtered_data['Datum'] >= pd.to_datetime(start_date)) &
                (filtered_data['Datum'] <= pd.to_datetime(end_date))
            ]
        
        # KPI-Metriken
        kpis = dashboard.create_kpi_metrics()
        if kpis:
            st.header("📊 Kennzahlen-Überblick")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f'<div class="metric-container">'
                    f'<div class="kpi-value" style="color: #1f77b4;">{kpis["Durchschnittsbewertung"]}</div>'
                    f'<div class="kpi-label">Durchschnittsbewertung</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f'<div class="metric-container">'
                    f'<div class="kpi-value" style="color: #ff4444;">{kpis["Verbesserung_Hoch"]}</div>'
                    f'<div class="kpi-label">Hoher Verbesserungsbedarf</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    f'<div class="metric-container">'
                    f'<div class="kpi-value" style="color: #4caf50;">{kpis["Positive_Trends"]}</div>'
                    f'<div class="kpi-label">Positive Trends</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            with col4:
                st.markdown(
                    f'<div class="metric-container">'
                    f'<div class="kpi-value" style="color: #764ba2;">{kpis["Gesamtbewertungen"]}</div>'
                    f'<div class="kpi-label">Gesamtbewertungen</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        # Charts
        st.header("📈 Visualisierungen")
        
        # Trend-Chart
        trend_chart = dashboard.create_trend_chart(filtered_data)
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)
        
        # Zwei Spalten für weitere Charts
        col1, col2 = st.columns(2)
        
        with col1:
            improvement_chart = dashboard.create_improvement_chart(filtered_data)
            if improvement_chart:
                st.plotly_chart(improvement_chart, use_container_width=True)
        
        with col2:
            category_chart = dashboard.create_category_chart(filtered_data)
            if category_chart:
                st.plotly_chart(category_chart, use_container_width=True)
        
        # Detaillierte Fragen-Auswertung
        st.header("🔍 Detaillierte Fragen-Analyse")
        detailed_chart = dashboard.create_detailed_questions_chart(filtered_data)
        if detailed_chart:
            st.plotly_chart(detailed_chart, use_container_width=True)
        
        # IQES-spezifische Auswertungen
        if not filtered_data[filtered_data['Fragentyp'] == 'Antwortskala'].empty:
            st.header("📊 IQES-Auswertungen")
            
            # Übersicht der Fragenbereiche
            scale_data = filtered_data[filtered_data['Fragentyp'] == 'Antwortskala']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Bewertungen nach Fragentyp")
                question_stats = scale_data.groupby('Fragenummer').agg({
                    'Bewertung': 'mean',
                    'Anzahl_Antworten': 'mean',
                    'Frage': 'first'
                }).round(2)
                st.dataframe(question_stats.sort_values('Bewertung'), use_container_width=True)
            
            with col2:
                st.subheader("🎯 Verbesserungspotential")
                critical_questions = scale_data[scale_data['Bewertung'] < 3.0]
                if not critical_questions.empty:
                    st.error(f"⚠️ {len(critical_questions)} Fragen unter 3.0!")
                    for _, row in critical_questions.iterrows():
                        st.write(f"• **{row['Fragenummer']}**: {row['Bewertung']:.2f} - {row['Frage'][:50]}...")
                else:
                    st.success("✅ Alle Fragen über 3.0!")
        
        # Detaildaten-Tabelle
        st.header("📋 Detaildaten")
        with st.expander("Daten anzeigen"):
            st.dataframe(
                filtered_data.sort_values(['Datum', 'Bewertung']),
                use_container_width=True
            )
        
        # Export-Funktionalität
        st.header("💾 Export")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📁 Daten als CSV exportieren",
                data=csv,
                file_name=f'schulqualitaet_export_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv'
            )
        
        with col2:
            st.info("💡 **Tipp:** Verwenden Sie die Filter in der Sidebar, um spezifische Auswertungen zu erstellen!")
        
        # Textanalyse für offene Fragen
        dashboard.create_text_analysis_section(filtered_data)
        
        # KI-gestützte Insights
        dashboard.create_smart_insights_section(filtered_data)
        
        # Erweiterte Analytics
        with st.expander("🔬 Erweiterte Analytics anzeigen"):
            dashboard.create_advanced_analytics_tab(filtered_data)
    else:
        # Anleitung für neue Benutzer
        st.markdown("""
        ## 🚀 Willkommen beim IQES-Auswertungs-Dashboard!
        
        ### So starten Sie:
        1. **📁 IQES Excel-Dateien hochladen** über die Sidebar links
        2. **🔍 Filter anwenden** nach Bildungsgang (BM/VK), Evaluationstyp oder Zeitraum  
        3. **📊 Automatische IQES-Visualisierungen** werden erstellt
        4. **💾 Daten exportieren** als CSV für weitere Analysen
        
        ### 📋 Unterstützte IQES-Dateiformate:
        - **IQES Excel-Ergebnisberichte** (`.xlsx` Format)
        - **Automatische Erkennung** von Skala-Fragen (1-4 Bewertung)
        - **Multiple-Choice Fragen** (Einfachauswahl)
        - **Offene Fragen** mit Textanalyse
        - **Metadaten-Extraktion** (Teilnehmerzahlen, Rücklaufquoten)
        
        ### 🎯 IQES-spezifische Features:
        - ✅ **Echte IQES-Fragen** mit korrekten deutschen Texten
        - ✅ **Bewertungsskala 1-4** ("trifft nicht zu" bis "trifft zu")
        - ✅ **Themenbereiche** (Schulatmosphäre, Lehrpersonen, etc.)
        - ✅ **Zeitliche Trends** zwischen verschiedenen Evaluationen
        - ✅ **Bildungsgang-Vergleiche** (BM vs VK)
        - ✅ **Textanalyse** für qualitative Rückmeldungen
        - ✅ **Verbesserungspotential-Analyse** (kritische Fragen < 3.0)
        
        **Laden Sie Ihre IQES-Evaluationsdateien hoch, um zu beginnen! →**
        """)

if __name__ == "__main__":
    main()
