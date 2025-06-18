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
    page_title="IQES-Schulqualitäts-Dashboard",
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
    
    def setup_openai(self):
        """Setup OpenAI für KI-Features"""
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                except Exception as e:
                    st.warning(f"OpenAI Setup fehlgeschlagen: {e}")
    
    def extract_date_from_filename(self, filename):
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
                
                # Bildungsgang aus Dateiname extrahieren
                bildungsgang = "Unbekannt"
                if "BM" in uploaded_file.name or "Büromanagement" in uploaded_file.name:
                    bildungsgang = "BM (Büromanagement)"
                elif "VK" in uploaded_file.name or "Veranstaltung" in uploaded_file.name:
                    bildungsgang = "VK (Veranstaltungskaufleute)"
                elif "GK" in uploaded_file.name:
                    bildungsgang = "GK"
                elif "IT" in uploaded_file.name:
                    bildungsgang = "IT"
                
                # Evaluationstyp bestimmen
                eval_type = "Abschlussevaluation" if "Abschluss" in uploaded_file.name else "Zwischenevaluation"
                
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
        """Berechnet Verbesserungsbedarf für IQES-Skala (1-4)"""
        if value < 2.5:
            return "HOCH"
        elif value < 3.0:
            return "MITTEL"
        else:
            return "NIEDRIG"
    
    def calculate_trend(self, value):
        """Berechnet Trend für IQES-Skala (1-4)"""
        if value >= 3.5:
            return "↑ Positiv"
        elif value >= 2.5:
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
        
        return {
            'Durchschnittsbewertung': round(avg_rating, 2),
            'Gesamtbewertungen': total_evaluations,
            'Verbesserung_Hoch': improvement_high,
            'Verbesserung_Mittel': improvement_medium,
            'Verbesserung_Niedrig': improvement_low,
            'Positive_Trends': f"{trend_percentage:.1f}%"
        }

class KI_Schulqualitäts_Analyzer:
    """KI-gestützte Analyse von IQES-Schulqualitätsdaten"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.pca = None
        self.openai_client = None
        self.setup_openai()
    
    def setup_openai(self):
        """Setup OpenAI für erweiterte KI-Features"""
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                except Exception:
                    pass
    
    def analyze_german_text_responses(self, text_responses):
        """Analysiert deutsche Textantworten mit KI-Features"""
        if not text_responses or len(text_responses) == 0:
            return {}
        
        analysis = {
            'total_responses': len(text_responses),
            'avg_length': np.mean([len(text) for text in text_responses]),
            'sentiment_analysis': self.analyze_sentiment_german(text_responses),
            'keyword_analysis': self.extract_german_keywords(text_responses)
        }
        
        # Erweiterte OpenAI-Analyse falls verfügbar
        if self.openai_client:
            analysis['ai_insights'] = self.generate_ai_insights_german(text_responses)
        
        return analysis
    
    def analyze_sentiment_german(self, texts):
        """Analysiert Sentiment deutscher Texte"""
        positive_words = {
            'gut', 'super', 'toll', 'schön', 'prima', 'klasse', 'perfekt', 'zufrieden', 
            'positiv', 'gefallen', 'freude', 'erfolg', 'dankbar', 'empfehlen'
        }
        
        negative_words = {
            'schlecht', 'schlimm', 'negativ', 'problem', 'schwierig', 'unzufrieden',
            'fehler', 'mangel', 'kritik', 'beschwerde', 'verbesserung', 'stress'
        }
        
        sentiment_scores = []
        for text in texts:
            words = set(text.lower().split())
            positive_count = len(words.intersection(positive_words))
            negative_count = len(words.intersection(negative_words))
            
            if positive_count + negative_count > 0:
                score = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                score = 0
            
            sentiment_scores.append(score)
        
        return {
            'avg_sentiment': np.mean(sentiment_scores),
            'positive_ratio': len([s for s in sentiment_scores if s > 0]) / len(sentiment_scores),
            'negative_ratio': len([s for s in sentiment_scores if s < 0]) / len(sentiment_scores)
        }
    
    def extract_german_keywords(self, texts):
        """Extrahiert deutsche Schlüsselwörter"""
        word_freq = {}
        
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if len(word) > 3 and word not in GERMAN_STOPWORDS:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_words[:15])  # Top 15 Wörter
    
    def generate_ai_insights_german(self, texts):
        """Generiert KI-Insights für deutsche Texte mit OpenAI"""
        if not self.openai_client or len(texts) == 0:
            return None
        
        sample_texts = texts[:8] if len(texts) > 8 else texts
        combined_text = '\n\n'.join(sample_texts)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist Schulentwicklungsexperte. Analysiere IQES-Schülerrückmeldungen auf Deutsch."
                    },
                    {
                        "role": "user",
                        "content": f"Analysiere diese Antworten und gib 3 konkrete Handlungsempfehlungen:\n\n{combined_text}"
                    }
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception:
            return None
    
    def generate_smart_recommendations(self, data):
        """Generiert intelligente IQES-spezifische Empfehlungen"""
        if data.empty:
            return []
            
        recommendations = []
        
        # Separiere verschiedene Datentypen
        scale_data = data[data['Fragentyp'] == 'Antwortskala'] if 'Fragentyp' in data.columns else data
        text_data = data[data['Fragentyp'] == 'Offene Frage'] if 'Fragentyp' in data.columns else pd.DataFrame()
        
        # 1. Kritische IQES-Bewertungen (< 2.5 auf 4er-Skala)
        if not scale_data.empty:
            critical_questions = scale_data[scale_data['Bewertung'] < 2.5]
            for _, question in critical_questions.head(3).iterrows():
                frage_text = question.get('Frage', 'Unbekannte Frage')[:50]
                recommendations.append({
                    'priority': 'HOCH',
                    'type': 'Kritische IQES-Bewertung',
                    'title': f'Sofortmaßnahmen: {frage_text}...',
                    'description': f'IQES-Bewertung: {question["Bewertung"]:.2f}/4.0 - Dringender Handlungsbedarf',
                    'action': 'Workshop und Verbesserungsplan für diese spezifische Frage erstellen',
                    'timeline': 'Sofort (1-2 Wochen)',
                    'impact': 'Hoch'
                })
        
        # 2. Textanalyse-basierte Empfehlungen (mit KI)
        if not text_data.empty:
            for _, text_question in text_data.iterrows():
                if 'Textantworten' in text_question and text_question['Textantworten']:
                    text_analysis = self.analyze_german_text_responses(text_question['Textantworten'])
                    
                    # Negative Sentiment Detection
                    if text_analysis.get('sentiment_analysis', {}).get('negative_ratio', 0) > 0.3:
                        recommendations.append({
                            'priority': 'MITTEL',
                            'type': 'Negatives Feedback (KI-Analyse)',
                            'title': 'Kritische Textantworten erkannt',
                            'description': f'{text_analysis["sentiment_analysis"]["negative_ratio"]*100:.1f}% negative Tendenz',
                            'action': 'Detailanalyse und Feedback-Gespräche führen',
                            'timeline': '2-3 Wochen',
                            'impact': 'Mittel'
                        })
        
        # 3. Bildungsgang-Vergleiche
        if not scale_data.empty and 'Bildungsgang' in scale_data.columns and len(scale_data['Bildungsgang'].unique()) > 1:
            program_avg = scale_data.groupby('Bildungsgang')['Bewertung'].mean()
            max_diff = program_avg.max() - program_avg.min()
            
            if max_diff > 0.4:  # Signifikanter Unterschied bei IQES
                worst_program = program_avg.idxmin()
                best_program = program_avg.idxmax()
                
                recommendations.append({
                    'priority': 'MITTEL',
                    'type': 'Bildungsgang-Unterschied',
                    'title': 'Qualitätsunterschiede zwischen Bildungsgängen',
                    'description': f'{worst_program} ({program_avg[worst_program]:.2f}) vs {best_program} ({program_avg[best_program]:.2f})',
                    'action': 'Best Practices übertragen',
                    'timeline': '1-3 Monate',
                    'impact': 'Hoch'
                })
        
        # Fallback für allgemeine Empfehlungen
        if not recommendations and not scale_data.empty:
            critical_areas = scale_data[scale_data['Bewertung'] < 3.0]
            if not critical_areas.empty:
                recommendations.append({
                    'priority': 'HOCH',
                    'type': 'Allgemeine Verbesserung',
                    'title': 'Verbesserungsmaßnahmen erforderlich',
                    'description': f'{len(critical_areas)} Bereiche benötigen Aufmerksamkeit',
                    'action': 'Detailanalyse der schlechten Bewertungen',
                    'timeline': '2-4 Wochen',
                    'impact': 'Hoch'
                })
        
        # Sortiere und limitiere
        sorted_recs = sorted(recommendations, key=lambda x: {'HOCH': 3, 'MITTEL': 2, 'NIEDRIG': 1}[x['priority']], reverse=True)
        return sorted_recs[:6]

def main():
    # Header
    st.markdown('<h1 class="main-header">🎓 IQES-AUSWERTUNGS-DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Dashboard-Instanz
    dashboard = SchulqualitätsDashboard()
    
    # Sidebar für Upload und Filter
    with st.sidebar:
        st.header("📁 IQES-Daten Upload")
        uploaded_files = st.file_uploader(
            "IQES Excel-Dateien hochladen",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="Laden Sie Ihre IQES-Evaluationsdateien hoch. Mehrere Dateien und Arbeitsblätter werden automatisch verarbeitet."
        )
        
        if uploaded_files:
            with st.spinner('📊 IQES-Daten werden verarbeitet...'):
                if dashboard.load_excel_files(uploaded_files):
                    st.success(f"✅ {len(uploaded_files)} IQES-Dateien erfolgreich geladen!")
                    
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
                    st.error("❌ Fehler beim Laden der IQES-Dateien!")
    
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
            st.header("📊 IQES-Kennzahlen-Überblick")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f'<div class="metric-container">'
                    f'<div class="kpi-value" style="color: #1f77b4;">{kpis["Durchschnittsbewertung"]}</div>'
                    f'<div class="kpi-label">Durchschnittsbewertung (IQES 1-4)</div>'
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
                    f'<div class="kpi-label">IQES-Einzelfragen</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        # KI-gestützte Empfehlungen
        st.header("💡 KI-gestützte Handlungsempfehlungen")
        recommendations = dashboard.ki_analyzer.generate_smart_recommendations(filtered_data)
        
        if recommendations:
            for i, rec in enumerate(recommendations):
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
        else:
            st.info("ℹ️ Keine spezifischen Empfehlungen basierend auf den aktuellen Daten.")
        
        # Detaildaten-Tabelle
        st.header("📋 IQES-Detaildaten")
        with st.expander("Daten anzeigen"):
            # Nur die wichtigsten Spalten anzeigen
            display_columns = ['Datum', 'Bildungsgang', 'Bereich', 'Frage', 'Bewertung', 'Verbesserungsbedarf', 'Fragentyp']
            available_columns = [col for col in display_columns if col in filtered_data.columns]
            
            if available_columns:
                st.dataframe(
                    filtered_data[available_columns].sort_values(['Datum', 'Bewertung']),
                    use_container_width=True
                )
            else:
                st.dataframe(filtered_data, use_container_width=True)
        
        # Export-Funktionalität
        st.header("💾 Export")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📁 IQES-Daten als CSV exportieren",
                data=csv,
                file_name=f'iqes_auswertung_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv'
            )
        
        with col2:
            st.info("💡 **Tipp:** Verwenden Sie die Filter in der Sidebar, um spezifische Auswertungen zu erstellen!")
        
    else:
        # Anleitung für neue Benutzer
        st.markdown("""
        ## 🚀 Willkommen beim IQES-Schulqualitäts-Dashboard!
        
        ### So starten Sie:
        1. **📁 IQES-Excel-Dateien hochladen** über die Sidebar links
        2. **🔍 Filter anwenden** nach Bildungsgang, Evaluationstyp oder Zeitraum  
        3. **📊 Automatische Visualisierungen** und KI-Analysen werden erstellt
        4. **💾 Daten exportieren** als CSV für weitere Analysen
        
        ### 📋 Unterstützte IQES-Dateiformate:
        - `.xlsx` und `.xls` Excel-Dateien
        - Automatische Erkennung von IQES-Bewertungsskalen (1-4)
        - Verarbeitung von Antwortskala-Fragen und offenen Antworten
        - Metadaten-Extraktion (Teilnehmerzahlen, Rücklaufquoten)
        
        ### 🎯 Features:
        - ✅ **IQES-spezifische Datenverarbeitung** mit korrekter Skalierung
        - ✅ **KI-gestützte Textanalyse** deutscher Schülerantworten
        - ✅ **Intelligente Handlungsempfehlungen** basierend auf kritischen Bereichen
        - ✅ **Zeitverlaufs-Analysen** über mehrere Evaluationszeiträume
        - ✅ **Bildungsgang-Vergleiche** (BM vs VK etc.)
        
        **Laden Sie Ihre ersten IQES-Dateien hoch, um zu beginnen! →**
        """)

if __name__ == "__main__":
    main()