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
import io
warnings.filterwarnings('ignore')

# Environment Variables laden
from dotenv import load_dotenv
load_dotenv()

# KI-Features für Textanalyse und Empfehlungen
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google Gemini AI Integration
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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

# Performance-Optimierungen
import streamlit.runtime.caching.hashing as hash_funcs

# Session State für Performance
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = pd.DataFrame()
if 'last_file_hash' not in st.session_state:
    st.session_state.last_file_hash = None

# Performance-Konfiguration
CHUNK_SIZE = 1000  # Chunk-Größe für große Datasets
MAX_MEMORY_MB = 500  # Maximaler Speicherverbrauch in MB
TIMEOUT_SECONDS = 120  # Timeout für datenintensive Operationen

# Threading-basiertes Timeout für Streamlit-Kompatibilität
import threading
import functools
import time

def streamlit_timeout_decorator(seconds):
    """Streamlit-kompatibles Timeout mit Threading"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                st.error(f"⏰ Operation abgebrochen nach {seconds}s Timeout. Versuchen Sie Cache zu leeren oder weniger Daten zu verarbeiten.")
                return None
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator

# Custom CSS für Executive Dashboard Design
st.markdown("""
<style>
    /* Hauptlayout */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header-Design */
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, #1f77b4, #667eea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
        font-weight: 700;
    }
    
    /* Executive KPI Cards */
    .kpi-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .kpi-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.25);
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .kpi-label {
        font-size: 1.1rem;
        opacity: 0.95;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Executive Section Headers */
    .executive-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 2rem 0 1rem 0;
        padding: 1rem 0;
        border-bottom: 2px solid #3498db;
        background: linear-gradient(90deg, #3498db20, transparent);
        padding-left: 1rem;
        border-radius: 8px;
    }
    
    /* Status-Badges */
    .status-critical {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
        box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
    }
    
    .status-success {
        background: linear-gradient(135deg, #27ae60, #2ecc71);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
    }
    
    /* Ranking Cards */
    .ranking-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border-left: 5px solid;
        transition: all 0.3s ease;
    }
    
    .ranking-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .ranking-card.critical {
        border-left-color: #e74c3c;
        background: linear-gradient(90deg, #e74c3c05, rgba(255, 255, 255, 0.95));
    }
    
    .ranking-card.success {
        border-left-color: #27ae60;
        background: linear-gradient(90deg, #27ae6005, rgba(255, 255, 255, 0.95));
    }
    
    /* Metric Cards */
    .metric-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Chart Container */
    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Executive Summary */
    .executive-summary {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    }
    
    .executive-summary h3 {
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .kpi-container {
            padding: 1rem;
        }
        
        .kpi-value {
            font-size: 2rem;
        }
        
        .executive-header {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class SchulqualitätsDashboard:
    def __init__(self):
        self.data = None
        self.processed_data = pd.DataFrame()
        self.metadata = pd.DataFrame()
        self.ki_analyzer = None  # Wird bei Bedarf initialisiert
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
    
    def _process_excel_file(self, file_content, filename):
        """Excel-Verarbeitung ohne Caching (wegen Streamlit-Kompatibilität)"""
        try:
            excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            return excel_data
        except Exception as e:
            st.error(f"Fehler beim Lesen von {filename}: {e}")
            return None
    
    def load_excel_files(self, uploaded_files):
        """Lädt und verarbeitet IQES Excel-Dateien mit Performance-Optimierung"""
        # File Hash für Cache-Invalidierung
        import hashlib
        file_hash = hashlib.md5()
        for f in uploaded_files:
            file_hash.update(f.name.encode())
        current_hash = file_hash.hexdigest()
        
        # Session State für Performance prüfen
        if (st.session_state.get('data_loaded', False) and 
            st.session_state.get('last_file_hash') == current_hash and
            'processed_data' in st.session_state and 
            not st.session_state.processed_data.empty):
            self.processed_data = st.session_state.processed_data
            st.success("✅ Daten aus Cache geladen (Performance-Optimierung)")
            return True
        
        all_data = []
        progress_bar = st.progress(0)
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Progress anzeigen
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Cache-fähige Excel-Verarbeitung
                file_content = uploaded_file.read()
                excel_data = self._process_excel_file(file_content, uploaded_file.name)
                
                if excel_data is None:
                    continue
                
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
                    
                # Memory cleanup
                del excel_data
                        
            except Exception as e:
                st.error(f"Fehler beim Laden von {uploaded_file.name}: {str(e)}")
                continue
        
        # Progress Bar entfernen
        progress_bar.empty()
        
        if all_data:
            self.processed_data = pd.concat(all_data, ignore_index=True)
            
            # Datenqualität sicherstellen
            self.processed_data = self.clean_data(self.processed_data)
            
            # In Session State cachen
            st.session_state.processed_data = self.processed_data
            st.session_state.data_loaded = True
            st.session_state.last_file_hash = current_hash
            
            return True
        return False
    
    def clean_data(self, data):
        """Datenqualität sicherstellen"""
        if data.empty:
            return data
            
        # Duplikate entfernen
        data = data.drop_duplicates()
        
        # Nur valide Bewertungen behalten
        if 'Bewertung' in data.columns:
            data = data[(data['Bewertung'] >= 1) & (data['Bewertung'] <= 4)]
        
        # Leer-Strings in Fragen entfernen
        if 'Frage' in data.columns:
            data = data[data['Frage'].str.strip() != '']
        
        return data
    
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
        """Verarbeitet Likert-Skala Fragen (Antwortskala) - GRUPPIERT für Zeitvergleiche"""
        questions = []
        
        try:
            # Überschrift aus den ersten Zeilen extrahieren (robuste Methode)
            category = ""
            
            # Versuche verschiedene Zeilen für Kategorie-Text
            for row_idx in range(min(3, len(df))):  # Erste 3 Zeilen durchsuchen
                if not df.empty and len(df.iloc[row_idx]) > 0:
                    cell_value = df.iloc[row_idx, 0]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        potential_category = str(cell_value).strip()
                        
                        # Ignoriere numerische Werte und kurze Strings
                        if (not potential_category.replace('.', '').isdigit() and 
                            len(potential_category) > 3 and
                            not potential_category.lower() in ['nan', 'none', 'null']):
                            category = potential_category
                            break
            
            # Fallback: Versuche Sheet-Name zu analysieren für Kategorie
            if not category and "Frage" in sheet_name:
                # Extrahiere Hauptfragebereich basierend auf Fragenummer
                question_num = sheet_name.split("Frage")[1].split("(")[0].strip()
                main_num = question_num.split('.')[0] if '.' in question_num else question_num
                
                # Standard IQES-Kategorien basierend auf Fragenummer
                iqes_categories = {
                    '1': 'Demografische Daten', '2': 'Demografische Daten', '3': 'Demografische Daten', '4': 'Demografische Daten',
                    '5': 'Schulatmosphäre und Schulklima', 
                    '6': 'Offenes Feedback zur Atmosphäre',
                    '7': 'Unterricht und Lehre',
                    '8': 'Offenes Feedback zum Unterricht', 
                    '9': 'Leistungsbewertung und Prüfungen',
                    '10': 'Individuelle Förderung und Unterstützung',
                    '11': 'Digitalisierung und Medien',
                    '12': 'Zukunftsperspektiven und Berufsvorbereitung',
                    '13': 'Offenes Feedback allgemein',
                    '14': 'Weitere Anregungen'
                }
                category = iqes_categories.get(main_num, f"Bereich {main_num}")
                
            # DEBUG: Log die gefundenen Kategorien (in Session State sammeln)
            if 'debug_categories' not in st.session_state:
                st.session_state.debug_categories = []
            st.session_state.debug_categories.append(f"Sheet '{sheet_name}': '{category}' (Methode: {'Excel' if category and not sheet_name else 'Fallback'})")
            
            # DEBUG: Log alle gefundenen Fragenummern
            if 'debug_questions' not in st.session_state:
                st.session_state.debug_questions = []
            
            # Fragenummer aus Sheet-Name extrahieren (ohne "Frage" Präfix)
            question_number = ""
            if "Frage" in sheet_name:
                question_number = sheet_name.split("Frage")[1].split("(")[0].strip()
            
            # Alle Unterfragen sammeln
            sub_questions = []
            valid_ratings = []
            total_responses = 0
            
            # Durch Datenzeilen iterieren (ab Zeile 2, da 0=Header, 1=Skala)
            for idx in range(2, len(df)):
                row = df.iloc[idx]
                
                # Frage-Text aus Spalte 0 (Format: "X.Y - Fragentext")
                question_text = ""
                individual_question_number = ""
                if pd.notna(row.iloc[0]):
                    full_text = str(row.iloc[0]).strip()
                    question_text = full_text
                    
                    # Einzelne Fragenummer extrahieren (z.B. "9.2" aus "9.2 - Fragentext")
                    import re
                    match = re.match(r'^(\d+\.\d+)\s*-?\s*(.*)$', full_text)
                    if match:
                        individual_question_number = match.group(1)
                        question_text = match.group(2).strip() if match.group(2) else full_text
                    
                # Durchschnittswert aus Spalte 9 (laut Excel-Struktur-Analyse)
                average_rating = None
                if len(row) > 9 and pd.notna(row.iloc[9]):
                    try:
                        average_rating = float(row.iloc[9])
                    except (ValueError, TypeError):
                        continue
                
                # N-Wert aus Spalte 10 (laut Excel-Struktur-Analyse)
                n_responses = None
                if len(row) > 10 and pd.notna(row.iloc[10]):
                    try:
                        n_responses = int(row.iloc[10])
                    except (ValueError, TypeError):
                        n_responses = 0
                
                # Antwortverteilung extrahieren (Spalten 1,3,5,7 laut Analyse)
                response_distribution = {}
                rating_columns = [1, 3, 5, 7]  # Direkte Spalten für Antworten 1,2,3,4
                for i, scale_point in enumerate([1, 2, 3, 4]):
                    col_index = rating_columns[i]
                    if len(row) > col_index and pd.notna(row.iloc[col_index]):
                        try:
                            response_distribution[f'antwort_{scale_point}'] = int(row.iloc[col_index])
                        except (ValueError, TypeError):
                            response_distribution[f'antwort_{scale_point}'] = 0
                
                # Nur verarbeiten wenn gültige Daten vorhanden
                if question_text and average_rating is not None and average_rating > 0:
                    # Erstelle individuelle Frage (nicht gruppiert)
                    # Verwende individuelle Fragenummer wenn verfügbar, sonst Sheet-Nummer
                    final_question_number = individual_question_number if individual_question_number else question_number
                    
                    # Thema zuordnen basierend auf echtem Bereichstext
                    theme_info = self.assign_theme_to_question(final_question_number, category)
                    
                    # DEBUG: Log alle gefundenen Fragen und Themen-Zuordnung
                    if 'debug_questions' not in st.session_state:
                        st.session_state.debug_questions = []
                    if 'debug_themes' not in st.session_state:
                        st.session_state.debug_themes = []
                    
                    st.session_state.debug_questions.append(f"GEFUNDEN: Frage {final_question_number} - {question_text[:50]}...")
                    st.session_state.debug_themes.append(f"Frage {final_question_number}: '{category}' → {theme_info['theme']} (Strategisch: {theme_info['strategic']})")
                    
                    question_data = {
                        'Datum': eval_date,
                        'Bildungsgang': bildungsgang,
                        'Evaluationstyp': eval_type,
                        'Bereich': category,
                        'Fragenummer': final_question_number,  # Individuelle Nummer wie "9.2"
                        'Frage': question_text,  # Vollständiger Fragetext
                        'Fragentyp': 'Antwortskala',
                        'Bewertung': average_rating,
                        'Anzahl_Antworten': n_responses or 0,
                        'Verbesserungsbedarf': self.calculate_improvement_need(average_rating),
                        'Trend': self.calculate_trend(average_rating),
                        'Thema': theme_info['theme'],  # Thematische Gruppierung
                        'Thema_Farbe': theme_info['color'],  # Farbkodierung
                        'Thema_Priorität': theme_info['priority'],  # Priorisierung
                        'Strategisch': theme_info['strategic'],  # Strategische Relevanz
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
            
            # Intelligente Kategorisierung für Segmentierung
            def detect_segmentation_type(question_text, choices):
                """Erkennt ob eine Einfachauswahl-Frage für Segmentierung geeignet ist"""
                question_lower = question_text.lower()
                choice_texts = [choice['text'].lower() for choice in choices.values()]
                
                # Geschlecht
                if any(word in question_lower for word in ['geschlecht', 'männlich', 'weiblich']):
                    return 'Geschlecht'
                if any('männlich' in text or 'weiblich' in text for text in choice_texts):
                    return 'Geschlecht'
                    
                # Alter/Altersgruppe
                if any(word in question_lower for word in ['alter', 'lebensjahr', 'geboren']):
                    return 'Alter'
                if any('jahr' in text or 'alt' in text for text in choice_texts):
                    return 'Alter'
                    
                # Herkunft/Migration
                if any(word in question_lower for word in ['herkunft', 'migration', 'geburtsland', 'staatsangehörigkeit']):
                    return 'Herkunft'
                    
                # Bildungsweg/Vorbildung
                if any(word in question_lower for word in ['schulabschluss', 'abschluss', 'vorbildung', 'bildungsweg']):
                    return 'Bildungsweg'
                    
                return 'Sonstige'
            
            # Erstelle Datensatz für Multiple-Choice Frage
            if question_text and choices:
                segmentation_type = detect_segmentation_type(question_text, choices)
                is_segmentation = segmentation_type in ['Geschlecht', 'Alter', 'Herkunft', 'Bildungsweg']
                
                # Thema zuordnen
                theme_info = self.assign_theme_to_question(question_number, 'Demographische Daten')
                
                question_data = {
                    'Datum': eval_date,
                    'Bildungsgang': bildungsgang,
                    'Evaluationstyp': eval_type,
                    'Bereich': 'Demographische Daten',
                    'Fragenummer': question_number,  # Ohne "Frage" Präfix
                    'Frage': question_text,
                    'Fragentyp': 'Einfachauswahl',
                    'Bewertung': None,  # Keine numerische Bewertung
                    'Anzahl_Antworten': total_responses,
                    'Verbesserungsbedarf': 'N/A',
                    'Trend': 'N/A',
                    'Thema': theme_info['theme'],
                    'Thema_Farbe': theme_info['color'],
                    'Thema_Priorität': theme_info['priority'],
                    'Segmentierungstyp': segmentation_type,
                    'Für_Segmentierung': is_segmentation,
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
    
    def get_color_for_category(self, category_text):
        """Ordnet IQES-Bereichstext eine Farbe zu (intelligente Erkennung)"""
        if not category_text:
            return {'theme': '❓ Unbekannt', 'color': '#7f8c8d', 'priority': 5}
        
        category_lower = category_text.lower()
        
        # Schulatmosphäre und Zwischenmenschliches
        if any(word in category_lower for word in ['atmosphäre', 'umgang', 'klima', 'zusammenleben', 'gemeinschaft', 'schulklima']):
            return {'theme': '🏫 Schulatmosphäre & Umgang', 'color': '#3498db', 'priority': 1}
        
        # Unterricht und Lehre  
        elif any(word in category_lower for word in ['unterricht', 'lehre', 'lehr', 'didaktik', 'methodik', 'vermittlung']):
            return {'theme': '📚 Unterricht & Lehre', 'color': '#e74c3c', 'priority': 1}
            
        # Bewertung und Leistung
        elif any(word in category_lower for word in ['bewertung', 'beurteilung', 'leistung', 'note', 'prüfung']):
            return {'theme': '📝 Leistungsbewertung', 'color': '#f39c12', 'priority': 2}
            
        # Förderung und Unterstützung
        elif any(word in category_lower for word in ['förderung', 'unterstützung', 'hilfe', 'beratung', 'individuell']):
            return {'theme': '🎯 Individuelle Förderung', 'color': '#9b59b6', 'priority': 2}
            
        # Digitalisierung und Technik
        elif any(word in category_lower for word in ['digital', 'technik', 'computer', 'internet', 'medien']):
            return {'theme': '💻 Digitalisierung & Medien', 'color': '#1abc9c', 'priority': 2}
            
        # Zukunft und Perspektiven
        elif any(word in category_lower for word in ['zukunft', 'perspektive', 'beruf', 'karriere', 'entwicklung', 'vorbereitung']):
            return {'theme': '🚀 Zukunftsperspektiven', 'color': '#27ae60', 'priority': 3}
            
        # Offene Fragen und Feedback
        elif any(word in category_lower for word in ['offen', 'feedback', 'rückmeldung', 'anregung', 'wunsch']):
            return {'theme': '💬 Offenes Feedback', 'color': '#34495e', 'priority': 3}
            
        # Demografische Daten
        elif any(word in category_lower for word in ['demograf', 'hintergrund', 'angaben', 'daten']):
            return {'theme': '📊 Demografische Daten', 'color': '#95a5a6', 'priority': 4}
        
        # Spezielle IQES-Kategorien (Fallback für unklare Texte)
        elif 'gebäude' in category_lower or 'räume' in category_lower or 'ausstattung' in category_lower:
            return {'theme': '🏢 Infrastruktur & Ausstattung', 'color': '#8e44ad', 'priority': 3}
        
        # Fallback: Verwende gekürzten Bereichstext
        short_name = category_text[:30] + "..." if len(category_text) > 30 else category_text
        return {'theme': f'📋 {short_name}', 'color': '#7f8c8d', 'priority': 3}
    
    def get_strategic_theme_mapping(self):
        """Strategische Fragengruppierung für IQES-Dashboard basierend auf echten Daten"""
        return {
            # STRATEGISCHE KERNBEREICHE (basierend auf echten Excel-Daten)
            
            # Schulatmosphäre, Umgang und Unterstützung (5.1-5.5)
            '5.1': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
            '5.2': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
            '5.3': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
            '5.4': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
            '5.5': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
            
            # Unterricht (7.1-7.13)
            '7.1': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.2': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.3': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.4': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.5': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.6': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.7': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.8': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.9': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.10': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.11': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.12': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            '7.13': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
            
            # Feedback (9.1-9.3)  
            '9.1': {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True},
            '9.2': {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True},
            '9.3': {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True},
            
            # SPEZIELLE FRAGENTYPEN (andere Auswertung)
            
            # Demografische Fragen (1.x-2.x) - nicht in Trends
            '1': {'theme': '📊 Demografie', 'color': '#95a5a6', 'priority': 5, 'strategic': False},
            '1.1': {'theme': '📊 Demografie', 'color': '#95a5a6', 'priority': 5, 'strategic': False},
            '1.2': {'theme': '📊 Demografie', 'color': '#95a5a6', 'priority': 5, 'strategic': False},
            '2': {'theme': '📊 Demografie', 'color': '#95a5a6', 'priority': 5, 'strategic': False},
            '2.1': {'theme': '📊 Demografie', 'color': '#95a5a6', 'priority': 5, 'strategic': False},
            '2.2': {'theme': '📊 Demografie', 'color': '#95a5a6', 'priority': 5, 'strategic': False},
            
            # Offene Fragen (4.x, 6.x, 8.x) - qualitative Auswertung
            '4': {'theme': '💭 Offene Antworten', 'color': '#34495e', 'priority': 4, 'strategic': False},
            '6': {'theme': '💭 Offene Antworten', 'color': '#34495e', 'priority': 4, 'strategic': False},
            '8': {'theme': '💭 Offene Antworten', 'color': '#34495e', 'priority': 4, 'strategic': False},
            
            # Sonstige Einzelfragen - separate Behandlung
            '9': {'theme': '📋 Sonstige Bereiche', 'color': '#7f8c8d', 'priority': 3, 'strategic': False},
            '10': {'theme': '📋 Sonstige Bereiche', 'color': '#7f8c8d', 'priority': 3, 'strategic': False},
            '11': {'theme': '📋 Sonstige Bereiche', 'color': '#7f8c8d', 'priority': 3, 'strategic': False},
            '12': {'theme': '📋 Sonstige Bereiche', 'color': '#7f8c8d', 'priority': 3, 'strategic': False},
        }
    
    def assign_theme_to_question(self, question_number, category_text=""):
        """Ordnet Thema basierend auf strategischer Fragengruppierung UND Inhaltsanalyse zu"""
        strategic_mapping = self.get_strategic_theme_mapping()
        
        # Exakte Übereinstimmung suchen
        if question_number in strategic_mapping:
            return strategic_mapping[question_number]
        
        # Hauptnummer suchen (z.B. "5" für "5.10" falls nicht in Mapping)
        main_number = question_number.split('.')[0]
        if main_number in strategic_mapping:
            base_info = strategic_mapping[main_number].copy()
            return base_info
        
        # ADAPTIVE ERKENNUNG für unterschiedliche IQES-Versionen
        # Basiert auf Frageninhalt statt nur Nummern
        if category_text:
            category_lower = category_text.lower()
            
            # Schulatmosphäre-Keywords
            if any(keyword in category_lower for keyword in [
                'schulgemeinschaft', 'vertrauen', 'respekt', 'unterstützung', 'hilfe', 
                'umgang', 'atmosphäre', 'gemeinschaft', 'ort', 'geschätzt', 'kultur'
            ]):
                return {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True}
            
            # Unterricht-Keywords  
            elif any(keyword in category_lower for keyword in [
                'unterricht', 'beruflich', 'ziele', 'inhalte', 'methodisch', 'lernen',
                'lernbedürfnisse', 'arbeitsaufträge', 'anspruchsvoll', 'kompetent', 
                'begeistern', 'leistungsbeurteilung', 'lernumgebung', 'fehler'
            ]):
                return {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True}
            
            # Feedback-Keywords
            elif any(keyword in category_lower for keyword in [
                'rückmeldung', 'feedback', 'auswertung', 'vereinbarung', 'maßnahmen'
            ]):
                return {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True}
        
        # Fallback für unbekannte Fragen
        return {'theme': '❓ Unbekannt', 'color': '#7f8c8d', 'priority': 5, 'strategic': False}
    
    def calculate_trend(self, value):
        """Berechnet Trend für IQES-Skala (1-4)"""
        if value >= 3.5:
            return "↑ Positiv"
        elif value >= 2.5:
            return "→ Stabil"
        else:
            return "↓ Negativ"
    
    def create_kpi_metrics(self):
        """Erstellt KPI-Metriken für IQES-Daten (nur strategische Kernbereiche)"""
        if self.processed_data.empty:
            return None
        
        # Nur strategische Antwortskala-Fragen für KPIs verwenden
        scale_data = self.processed_data[self.processed_data['Fragentyp'] == 'Antwortskala']
        
        # Filter für strategische Fragen
        if 'Strategisch' in scale_data.columns:
            strategic_data = scale_data[scale_data['Strategisch'] == True]
            if not strategic_data.empty:
                scale_data = strategic_data
        
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
    
    def create_timeline_visualization(self, data):
        """Erstellt Zeitreihen-Visualisierung für echte Trend-Analyse mit gruppierten Fragen"""
        if data.empty or 'Bewertung' not in data.columns:
            st.warning("Keine Bewertungsdaten für Zeitreihen-Analyse verfügbar.")
            return
        
        # Nur strategische Antwortskala-Daten für Zeitreihen verwenden
        scale_data = data[data['Fragentyp'] == 'Antwortskala'].copy()
        
        # Filter für strategische Fragen wenn verfügbar
        if 'Strategisch' in scale_data.columns:
            strategic_data = scale_data[scale_data['Strategisch'] == True].copy()
            if not strategic_data.empty:
                scale_data = strategic_data
                st.info(f"📊 Fokus auf strategische Kernbereiche: {len(scale_data)} von {len(data[data['Fragentyp'] == 'Antwortskala'])} Fragen")
            else:
                st.warning("⚠️ Keine strategischen Kernfragen gefunden - zeige alle Antwortskala-Fragen")
        
        if scale_data.empty:
            st.info("Keine auswertbaren Daten für Zeitreihen verfügbar.")
            return
        
        # Prüfe ob mehrere Zeiträume vorhanden
        if len(scale_data['Datum'].unique()) < 2:
            st.info("Mindestens zwei Evaluationszeiträume erforderlich für Trend-Analyse.")
            return
            
        # Tabs für verschiedene Ansichten
        tab1, tab2, tab3 = st.tabs(["📊 Gesamttrend", "🎯 Themen-Trends", "📈 Einzelfragen-Trends"])
        
        with tab1:
            # Gesamttrend nach Bildungsgang
            timeline_data = scale_data.groupby(['Datum', 'Bildungsgang'])['Bewertung'].agg(['mean', 'count']).reset_index()
            timeline_data.columns = ['Datum', 'Bildungsgang', 'Durchschnitt', 'Anzahl_Fragen']
            
            # Plotly Zeitreihen-Chart
            fig = go.Figure()
            
            for bildungsgang in timeline_data['Bildungsgang'].unique():
                bg_data = timeline_data[timeline_data['Bildungsgang'] == bildungsgang]
                
                fig.add_trace(go.Scatter(
                    x=bg_data['Datum'],
                    y=bg_data['Durchschnitt'],
                    mode='lines+markers',
                    name=bildungsgang,
                    line=dict(width=4),
                    marker=dict(size=10),
                    hovertemplate=f'<b>{bildungsgang}</b><br>' +
                                 'Datum: %{x}<br>' +
                                 'Durchschnitt: %{y:.2f}<br>' +
                                 'Anzahl Fragen: %{text}<br>' +
                                 '<extra></extra>',
                    text=bg_data['Anzahl_Fragen']
                ))
            
            fig.update_layout(
                title="📈 Gesamtbewertung-Entwicklung über Zeit (alle Fragen)",
                xaxis_title="Evaluationszeitraum",
                yaxis_title="Durchschnittsbewertung (1-4 IQES-Skala)",
                yaxis=dict(range=[1, 4]),
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Trend-Zusammenfassung
            col1, col2, col3 = st.columns(3)
            with col1:
                latest_avg = timeline_data.groupby('Datum')['Durchschnitt'].mean().iloc[-1]
                if len(timeline_data['Datum'].unique()) > 1:
                    previous_avg = timeline_data.groupby('Datum')['Durchschnitt'].mean().iloc[-2]
                    trend = latest_avg - previous_avg
                    st.metric("Aktueller Trend", f"{latest_avg:.2f}", f"{trend:+.2f}", delta_color="normal")
                else:
                    st.metric("Aktueller Durchschnitt", f"{latest_avg:.2f}")
            
            with col2:
                total_questions = len(scale_data['Fragenummer'].unique())
                st.metric("Ausgewertete Fragen", total_questions)
            
            with col3:
                critical_count = len(scale_data[scale_data['Verbesserungsbedarf'] == 'HOCH'])
                st.metric("Kritische Bereiche", critical_count, delta_color="inverse")
        
        with tab2:
            # Thematische Trends - Gruppiert nach Entwicklungsbereichen
            if 'Thema' in scale_data.columns:
                st.markdown("### 🎯 Entwicklung nach Themenbereichen")
                
                # Themen-Timeline erstellen
                theme_timeline = scale_data.groupby(['Datum', 'Thema', 'Thema_Farbe'])['Bewertung'].mean().reset_index()
                
                # Plotly Chart für thematische Trends
                fig_themes = go.Figure()
                
                # Unique Themen mit Farben
                themes = scale_data[['Thema', 'Thema_Farbe', 'Thema_Priorität']].drop_duplicates()
                themes = themes.sort_values('Thema_Priorität')  # Nach Priorität sortieren
                
                for _, theme_row in themes.iterrows():
                    theme_name = theme_row['Thema']
                    theme_color = theme_row['Thema_Farbe']
                    
                    theme_data = theme_timeline[theme_timeline['Thema'] == theme_name]
                    
                    if len(theme_data) > 0:
                        # Trend berechnen
                        if len(theme_data) >= 2:
                            latest_val = theme_data.iloc[-1]['Bewertung']
                            first_val = theme_data.iloc[0]['Bewertung']
                            trend_change = latest_val - first_val
                            trend_icon = " 📈" if trend_change > 0.1 else " 📉" if trend_change < -0.1 else " ➡️"
                        else:
                            trend_icon = ""
                        
                        fig_themes.add_trace(go.Scatter(
                            x=theme_data['Datum'],
                            y=theme_data['Bewertung'],
                            mode='lines+markers',
                            name=f"{theme_name}{trend_icon}",
                            line=dict(width=4, color=theme_color),
                            marker=dict(size=10, color=theme_color),
                            hovertemplate=f'<b>{theme_name}</b><br>' +
                                         'Datum: %{x}<br>' +
                                         'Durchschnitt: %{y:.2f}<br>' +
                                         '<extra></extra>'
                        ))
                
                fig_themes.update_layout(
                    title="🎯 Thematische Entwicklungsbereiche über Zeit",
                    xaxis_title="Evaluationszeitraum",
                    yaxis_title="Durchschnittsbewertung (1-4 IQES-Skala)",
                    yaxis=dict(range=[1, 4]),
                    hovermode='x unified',
                    template='plotly_white',
                    height=500,
                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                )
                
                st.plotly_chart(fig_themes, use_container_width=True)
                
                # Themen-Trend-Übersicht
                st.markdown("### 📊 Themenbereiche-Übersicht")
                
                theme_summary = []
                for _, theme_row in themes.iterrows():
                    theme_name = theme_row['Thema']
                    theme_data = theme_timeline[theme_timeline['Thema'] == theme_name]
                    
                    if len(theme_data) >= 2:
                        latest_val = theme_data.iloc[-1]['Bewertung']
                        first_val = theme_data.iloc[0]['Bewertung']
                        trend_change = latest_val - first_val
                        
                        # Anzahl Fragen in diesem Thema
                        question_count = len(scale_data[scale_data['Thema'] == theme_name]['Fragenummer'].unique())
                        
                        theme_summary.append({
                            'Themenbereich': theme_name,
                            'Anzahl Fragen': question_count,
                            'Erste Bewertung': f"{first_val:.2f}",
                            'Aktuelle Bewertung': f"{latest_val:.2f}",
                            'Trend': f"{trend_change:+.2f}",
                            'Entwicklung': "📈 Verbessert" if trend_change > 0.1 else "📉 Verschlechtert" if trend_change < -0.1 else "➡️ Stabil"
                        })
                
                if theme_summary:
                    # Nach Trend sortieren (beste Verbesserungen zuerst)
                    theme_df = pd.DataFrame(theme_summary)
                    theme_df['Trend_Numeric'] = theme_df['Trend'].str.replace('+', '').astype(float)
                    theme_df = theme_df.sort_values('Trend_Numeric', ascending=False)
                    theme_df = theme_df.drop('Trend_Numeric', axis=1)
                    
                    # Farbkodierung für die Tabelle
                    def highlight_trend(row):
                        if "📈" in row['Entwicklung']:
                            return ['background-color: #d5f4e6'] * len(row)
                        elif "📉" in row['Entwicklung']:
                            return ['background-color: #ffeaa7'] * len(row)
                        else:
                            return [''] * len(row)
                    
                    styled_df = theme_df.style.apply(highlight_trend, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.info("Thematische Daten werden geladen...")
        
        with tab3:
            # Einzelfragen-Trends (nur Fragen die in mehreren Zeiträumen vorhanden sind)
            question_timeline = scale_data.groupby(['Fragenummer', 'Datum'])['Bewertung'].mean().reset_index()
            
            # Nur Fragen zeigen die in mindestens 2 Zeiträumen vorhanden sind
            question_counts = question_timeline.groupby('Fragenummer')['Datum'].count()
            multi_period_questions = question_counts[question_counts >= 2].index
            
            if len(multi_period_questions) == 0:
                st.info("Keine Fragen gefunden, die in mehreren Zeiträumen evaluiert wurden.")
                return
            
            # Dropdown für Fragenauswahl
            selected_questions = st.multiselect(
                "📋 Fragen für Trend-Vergleich auswählen:",
                options=multi_period_questions.tolist(),
                default=multi_period_questions.tolist()[:5] if len(multi_period_questions) >= 5 else multi_period_questions.tolist(),
                help="Wählen Sie bis zu 10 Fragen für den Trend-Vergleich aus"
            )
            
            if selected_questions:
                # Einzelfragen-Chart
                fig_individual = go.Figure()
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                         '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                
                for i, question_num in enumerate(selected_questions[:10]):  # Max 10 Fragen
                    question_data = question_timeline[question_timeline['Fragenummer'] == question_num]
                    
                    # Trend berechnen
                    if len(question_data) >= 2:
                        latest_val = question_data.iloc[-1]['Bewertung']
                        first_val = question_data.iloc[0]['Bewertung']
                        trend_change = latest_val - first_val
                        trend_icon = "📈" if trend_change > 0.1 else "📉" if trend_change < -0.1 else "➡️"
                    else:
                        trend_icon = "➡️"
                    
                    fig_individual.add_trace(go.Scatter(
                        x=question_data['Datum'],
                        y=question_data['Bewertung'],
                        mode='lines+markers',
                        name=f"{trend_icon} Frage {question_num}",
                        line=dict(width=3, color=colors[i % len(colors)]),
                        marker=dict(size=8),
                        hovertemplate=f'<b>Frage {question_num}</b><br>' +
                                     'Datum: %{x}<br>' +
                                     'Bewertung: %{y:.2f}<br>' +
                                     '<extra></extra>'
                    ))
                
                fig_individual.update_layout(
                    title="📈 Einzelfragen-Trends über Zeit",
                    xaxis_title="Evaluationszeitraum",
                    yaxis_title="Bewertung (1-4 IQES-Skala)",
                    yaxis=dict(range=[1, 4]),
                    hovermode='x unified',
                    template='plotly_white',
                    height=500,
                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                )
                
                st.plotly_chart(fig_individual, use_container_width=True)
                
                # Trend-Tabelle
                st.markdown("### 📊 Trend-Übersicht")
                trend_summary = []
                for question_num in selected_questions:
                    question_data = question_timeline[question_timeline['Fragenummer'] == question_num]
                    if len(question_data) >= 2:
                        latest_val = question_data.iloc[-1]['Bewertung']
                        first_val = question_data.iloc[0]['Bewertung']
                        trend_change = latest_val - first_val
                        
                        # Frage-Text aus ursprünglichen Daten
                        frage_text = scale_data[scale_data['Fragenummer'] == question_num]['Bereich'].iloc[0]
                        
                        trend_summary.append({
                            'Frage': f"Frage {question_num}",
                            'Bereich': frage_text,
                            'Erste Bewertung': f"{first_val:.2f}",
                            'Aktuelle Bewertung': f"{latest_val:.2f}",
                            'Trend': f"{trend_change:+.2f}",
                            'Status': "📈 Verbessert" if trend_change > 0.1 else "📉 Verschlechtert" if trend_change < -0.1 else "➡️ Stabil"
                        })
                
                if trend_summary:
                    trend_df = pd.DataFrame(trend_summary)
                    st.dataframe(trend_df, use_container_width=True, hide_index=True)
    
    def _calculate_rankings_data(self, data):
        """Berechnung der Rankings ohne Caching"""
        scale_data = data[data['Fragentyp'] == 'Antwortskala'].copy()
        if scale_data.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Rankings erstellen mit thematischer Gruppierung
        if 'Thema' in scale_data.columns:
            question_rankings = scale_data.groupby(['Frage', 'Fragenummer', 'Thema', 'Thema_Farbe']).agg({
                'Bewertung': 'mean',
                'Anzahl_Antworten': 'sum',
                'Verbesserungsbedarf': 'first'
            }).reset_index()
        else:
            question_rankings = scale_data.groupby(['Frage', 'Fragenummer']).agg({
                'Bewertung': 'mean',
                'Anzahl_Antworten': 'sum',
                'Verbesserungsbedarf': 'first'
            }).reset_index()
            question_rankings['Thema'] = '❓ Sonstige'
            question_rankings['Thema_Farbe'] = '#7f8c8d'
        
        # Top 5 kritische Fragen (niedrigste Bewertungen)
        bottom_5 = question_rankings.nsmallest(5, 'Bewertung')
        
        # Top 5 beste Fragen (höchste Bewertungen)
        top_5 = question_rankings.nlargest(5, 'Bewertung')
        
        return bottom_5, top_5
    
    def create_rankings_visualization(self, data):
        """Erstellt Top/Bottom Rankings für kritische Bereiche"""
        if data.empty or 'Bewertung' not in data.columns:
            st.warning("Keine Bewertungsdaten für Rankings verfügbar.")
            return
        
        # Verwende gecachte Berechnung
        bottom_5, top_5 = self._calculate_rankings_data(data)
        
        if bottom_5.empty and top_5.empty:
            st.info("Keine Antwortskala-Daten für Rankings verfügbar.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🚨 Top 5 Kritische Bereiche")
            for idx, row in bottom_5.iterrows():
                rating = row['Bewertung']
                question = row['Frage'][:100] + "..." if len(row['Frage']) > 100 else row['Frage']
                n_answers = int(row['Anzahl_Antworten'])
                theme = row.get('Thema', '❓ Sonstige')
                theme_color = row.get('Thema_Farbe', '#7f8c8d')
                question_num = row.get('Fragenummer', '')
                
                # Farbkodierung basierend auf Bewertung
                if rating < 2.5:
                    icon = "🚨"
                    card_class = "critical"
                elif rating < 3.0:
                    icon = "⚠️"
                    card_class = "critical"
                else:
                    icon = "✅"
                    card_class = "success"
                
                st.markdown(f"""
                <div class="ranking-card {card_class}" style="border-left-color: {theme_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="font-size: 1.2rem;">{icon} {rating:.2f}/4.0</strong>
                        <span class="status-{'critical' if rating < 2.5 else 'warning' if rating < 3.0 else 'success'}">
                            {n_answers} Antworten
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: {theme_color}; font-weight: 600; margin-bottom: 0.3rem;">
                        {theme} • Frage {question_num}
                    </div>
                    <div style="font-size: 0.95rem; line-height: 1.4; color: #2c3e50;">
                        {question}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### ✅ Top 5 Best Practices")
            for idx, row in top_5.iterrows():
                rating = row['Bewertung']
                question = row['Frage'][:100] + "..." if len(row['Frage']) > 100 else row['Frage']
                n_answers = int(row['Anzahl_Antworten'])
                theme = row.get('Thema', '❓ Sonstige')
                theme_color = row.get('Thema_Farbe', '#7f8c8d')
                question_num = row.get('Fragenummer', '')
                
                st.markdown(f"""
                <div class="ranking-card success" style="border-left-color: {theme_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="font-size: 1.2rem;">✅ {rating:.2f}/4.0</strong>
                        <span class="status-success">
                            {n_answers} Antworten
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: {theme_color}; font-weight: 600; margin-bottom: 0.3rem;">
                        {theme} • Frage {question_num}
                    </div>
                    <div style="font-size: 0.95rem; line-height: 1.4; color: #2c3e50;">
                        {question}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def create_comparison_visualization(self, data):
        """Erstellt verbesserte BM vs VK Vergleichscharts"""
        if data.empty or 'Bewertung' not in data.columns:
            st.warning("Keine Bewertungsdaten für Vergleich verfügbar.")
            return
        
        scale_data = data[data['Fragentyp'] == 'Antwortskala'].copy()
        if scale_data.empty:
            st.info("Keine Antwortskala-Daten für Vergleich verfügbar.")
            return
        
        # Strategische Themen-basierte Vergleichsdaten (bessere Gruppierung)
        if 'Thema' in scale_data.columns and 'Strategisch' in scale_data.columns:
            # Nur strategische Themen für bessere Übersicht
            strategic_data = scale_data[scale_data['Strategisch'] == True]
            comparison_data = strategic_data.groupby(['Bildungsgang', 'Thema'])['Bewertung'].mean().reset_index()
            x_field = 'Thema'
            title = "📊 Strategische Themen: BM vs VK Vergleich"
        else:
            # Fallback auf Bereich
            comparison_data = scale_data.groupby(['Bildungsgang', 'Bereich'])['Bewertung'].mean().reset_index()
            x_field = 'Bereich'
            title = "📊 Bewertungsvergleich nach Bildungsgang"
        
        if len(comparison_data['Bildungsgang'].unique()) < 2:
            st.info("Mindestens zwei Bildungsgänge erforderlich für Vergleich.")
            return
        
        # Gruppierte vertikale Balken für direkten Vergleich
        fig = px.bar(
            comparison_data, 
            x=x_field,
            y='Bewertung',
            color='Bildungsgang',
            barmode='group',  # Balken nebeneinander statt gestapelt!
            title=title,
            labels={'Bewertung': 'Durchschnittsbewertung (1-4)', x_field: 'Bereich'},
            color_discrete_sequence=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'],
            text='Bewertung'  # Zeige Werte auf Balken
        )
        
        # Bessere Formatierung für Vergleichbarkeit
        fig.update_traces(
            texttemplate='%{text:.2f}', 
            textposition='outside',
            textfont_size=11
        )
        fig.update_layout(
            yaxis=dict(range=[1, 4.2], title='Durchschnittsbewertung (1-4)'),  # Etwas mehr Platz für Text
            xaxis=dict(title=x_field),
            template='plotly_white',
            height=500,  # Feste Höhe für bessere Proportionen
            font=dict(size=12),
            legend=dict(orientation="h", x=0.5, y=1.05, xanchor='center'),
            showlegend=True,
            margin=dict(l=50, r=50, t=100, b=100)  # Ausreichend Margin für Beschriftungen
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Zusätzliches Radar-Chart für multidimensionalen Vergleich
        if len(comparison_data[x_field].unique()) >= 3:
            st.markdown("#### 🎯 Multidimensionaler Vergleich (Radar-Chart)")
            
            # Pivot für Radar Chart
            pivot_data = comparison_data.pivot(index=x_field, columns='Bildungsgang', values='Bewertung').reset_index()
            
            fig_radar = go.Figure()
            
            # Definiere Farben für konsistente Darstellung (BM=Blau, VK=Rot)
            colors_and_fills = {
                'BM (Büromanagement)': {'line': '#3498db', 'fill': 'rgba(52,152,219,0.1)'},
                'VK (Veranstaltungskaufleute)': {'line': '#e74c3c', 'fill': 'rgba(231,76,60,0.1)'},
                'BM': {'line': '#3498db', 'fill': 'rgba(52,152,219,0.1)'},
                'VK': {'line': '#e74c3c', 'fill': 'rgba(231,76,60,0.1)'}
            }
            
            for bildungsgang in pivot_data.columns[1:]:  # Skip index column
                # Bestimme Farben basierend auf Bildungsgang
                colors = colors_and_fills.get(bildungsgang, {
                    'line': '#f39c12', 
                    'fill': 'rgba(243,156,18,0.1)'
                })
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=pivot_data[bildungsgang].tolist(),
                    theta=pivot_data[x_field].tolist(),
                    fill='toself',
                    name=bildungsgang,
                    line=dict(width=3, color=colors['line']),
                    fillcolor=colors['fill']
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[1, 4],
                        tickvals=[1, 2, 3, 4],
                        ticktext=['1 (Schlecht)', '2 (Verbesserung)', '3 (Gut)', '4 (Sehr gut)']
                    )),
                showlegend=True,
                title="🎯 Radar-Vergleich der Bildungsgänge",
                height=500
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
        
        # Verbesserte Delta-Analyse mit detaillierter Gap-Visualisierung
        if len(comparison_data['Bildungsgang'].unique()) == 2:
            st.markdown("### 📈 Performance-Gap-Analyse")
            
            bildungsgänge = comparison_data['Bildungsgang'].unique()
            bg1_data = comparison_data[comparison_data['Bildungsgang'] == bildungsgänge[0]]
            bg2_data = comparison_data[comparison_data['Bildungsgang'] == bildungsgänge[1]]
            
            # Durchschnittliche Differenz
            avg_diff = bg1_data['Bewertung'].mean() - bg2_data['Bewertung'].mean()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"Durchschnitt {bildungsgänge[0]}", f"{bg1_data['Bewertung'].mean():.2f}")
            
            with col2:
                st.metric(f"Durchschnitt {bildungsgänge[1]}", f"{bg2_data['Bewertung'].mean():.2f}")
            
            with col3:
                delta_color = "normal" if avg_diff >= 0 else "inverse"
                st.metric("Performance-Gap", f"{abs(avg_diff):.2f}", f"{avg_diff:+.2f}", delta_color=delta_color)
            
            # Detaillierte Gap-Analyse pro Bereich/Thema
            st.markdown("#### 🔍 Gap-Analyse nach Bereichen")
            
            # Merge der beiden Bildungsgänge für Gap-Berechnung
            merged_data = bg1_data.merge(bg2_data, on=x_field, suffixes=('_BG1', '_BG2'))
            merged_data['Gap'] = merged_data['Bewertung_BG1'] - merged_data['Bewertung_BG2']
            merged_data['Abs_Gap'] = abs(merged_data['Gap'])
            
            # Gap-Visualisierung (Waterfall-ähnlich)
            fig_gap = go.Figure()
            
            colors = ['#e74c3c' if gap < 0 else '#2ecc71' for gap in merged_data['Gap']]
            
            fig_gap.add_trace(go.Bar(
                x=merged_data[x_field],
                y=merged_data['Gap'],
                marker_color=colors,
                text=[f"{gap:+.2f}" for gap in merged_data['Gap']],
                textposition='outside',
                name='Performance-Gap'
            ))
            
            fig_gap.update_layout(
                title=f"📊 Performance-Gap: {bildungsgänge[0]} vs {bildungsgänge[1]}",
                yaxis_title="Bewertungsdifferenz",
                xaxis_title=x_field,
                template='plotly_white',
                height=400,
                yaxis=dict(range=[-1, 1]),
                annotations=[
                    dict(text="Grün = BG1 besser", x=0.02, y=0.98, xref="paper", yref="paper", 
                         showarrow=False, font=dict(color="#2ecc71")),
                    dict(text="Rot = BG2 besser", x=0.02, y=0.92, xref="paper", yref="paper", 
                         showarrow=False, font=dict(color="#e74c3c"))
                ]
            )
            
            # Nulllinie hinzufügen
            fig_gap.add_hline(y=0, line_dash="dash", line_color="gray")
            
            st.plotly_chart(fig_gap, use_container_width=True)
            
            # Top Gap-Bereiche identifizieren
            top_gaps = merged_data.nlargest(3, 'Abs_Gap')
            if not top_gaps.empty:
                st.markdown("#### ⚠️ Größte Performance-Unterschiede")
                for _, row in top_gaps.iterrows():
                    direction = "besser" if row['Gap'] > 0 else "schlechter"
                    color = "🟢" if row['Gap'] > 0 else "🔴"
                    st.write(f"{color} **{row[x_field]}**: {bildungsgänge[0]} ist {abs(row['Gap']):.2f} Punkte {direction} ({row['Gap']:+.2f})")
    
    def create_segmentation_analysis(self, data):
        """Intelligente Kombination aller Fragentypen für Segmentierungs-Analyse"""
        if data.empty:
            st.warning("Keine Daten für Segmentierung verfügbar.")
            return
        
        # Separate Fragentypen
        scale_data = data[data['Fragentyp'] == 'Antwortskala']
        choice_data = data[data['Fragentyp'] == 'Einfachauswahl']
        open_data = data[data['Fragentyp'] == 'Offene Frage']
        
        # Verfügbare Segmentierungsoptionen finden
        segmentation_options = []
        if not choice_data.empty and 'Für_Segmentierung' in choice_data.columns:
            seg_questions = choice_data[choice_data['Für_Segmentierung'] == True]
            segmentation_options = [(row['Fragenummer'], row['Segmentierungstyp'], row['Frage']) 
                                  for _, row in seg_questions.iterrows()]
        
        if not segmentation_options and not scale_data.empty:
            st.info("💡 Segmentierungs-Analyse: Aktuell nur nach Bildungsgang verfügbar. Demografische Daten werden erkannt sobald Einfachauswahl-Fragen vorhanden sind.")
            
            # Fallback: Nur Bildungsgang-basierte Analyse
            tab1, tab2 = st.tabs(["📊 Quantitative Trends", "💬 Qualitative Insights"])
            
            with tab1:
                self._show_quantitative_summary(scale_data)
            
            with tab2:
                self._show_qualitative_summary(open_data)
                
        elif segmentation_options:
            st.markdown("### 🎯 Multidimensionale Analyse")
            
            # Segmentierungs-Auswahl
            selected_segment = st.selectbox(
                "📋 Segmentierung auswählen:",
                options=[f"{seg_type}: {question[:60]}..." if len(question) > 60 else f"{seg_type}: {question}" 
                        for _, seg_type, question in segmentation_options],
                help="Wählen Sie eine demografische Dimension für die Analyse aus"
            )
            
            if selected_segment:
                # Tabs für verschiedene Analysedimensionen
                tab1, tab2, tab3 = st.tabs(["📊 Segmentierte Trends", "🔍 Vergleichsanalyse", "💬 Qualitative Insights"])
                
                with tab1:
                    self._show_segmented_trends(scale_data, choice_data, selected_segment)
                
                with tab2:
                    self._show_segment_comparison(scale_data, choice_data, selected_segment)
                
                with tab3:
                    self._show_qualitative_by_segment(open_data, choice_data, selected_segment)
        else:
            st.info("📋 Keine auswertbaren Daten für Segmentierung verfügbar.")
    
    def _show_quantitative_summary(self, scale_data):
        """Zeigt quantitative Zusammenfassung ohne Segmentierung"""
        if scale_data.empty:
            st.info("Keine quantitativen Daten verfügbar.")
            return
            
        # Grundlegende Statistiken
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_rating = scale_data['Bewertung'].mean()
            st.metric("Durchschnittsbewertung", f"{avg_rating:.2f}/4.0")
        
        with col2:
            critical_count = len(scale_data[scale_data['Verbesserungsbedarf'] == 'HOCH'])
            st.metric("Kritische Bereiche", critical_count)
        
        with col3:
            total_responses = scale_data['Anzahl_Antworten'].sum()
            st.metric("Gesamtantworten", f"{total_responses:,}")
        
        # DEBUG: Zeige alle gefundenen Fragen und Themen
        if st.checkbox("🔍 Debug: Gefundene Fragen anzeigen", value=False):
            if hasattr(st.session_state, 'debug_questions') and st.session_state.debug_questions:
                st.write("**Alle gefundenen Fragen:**")
                for question in st.session_state.debug_questions[-20:]:  # Nur letzte 20
                    st.write(f"- {question}")
            else:
                st.write("Keine Debug-Daten verfügbar")
                
            if hasattr(st.session_state, 'debug_themes') and st.session_state.debug_themes:
                st.write("**Themen-Zuordnungen:**")
                for theme in st.session_state.debug_themes[-20:]:  # Nur letzte 20
                    st.write(f"- {theme}")
            else:
                st.write("Keine Themen-Debug-Daten verfügbar")
        
        # Top Themen nach Bewertung
        if 'Thema' in scale_data.columns:
            st.markdown("#### 📊 Themenbereiche-Performance")
            theme_performance = scale_data.groupby('Thema')['Bewertung'].agg(['mean', 'count']).round(2)
            theme_performance.columns = ['Durchschnitt', 'Anzahl Fragen']
            theme_performance = theme_performance.sort_values('Durchschnitt', ascending=False)
            
            # Farbkodierung für Performance
            def color_performance(val):
                if val >= 3.0:
                    return 'background-color: #d5f4e6'
                elif val >= 2.5:
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #f8d7da'
            
            styled_performance = theme_performance.style.applymap(color_performance, subset=['Durchschnitt'])
            st.dataframe(styled_performance, use_container_width=True)
    
    def _show_qualitative_summary(self, open_data):
        """Zeigt qualitative Zusammenfassung"""
        if open_data.empty:
            st.info("Keine qualitativen Daten verfügbar.")
            return
            
        st.markdown("#### 💬 Qualitative Rückmeldungen")
        
        # Anzahl offener Antworten
        total_open_responses = open_data['Anzahl_Antworten'].sum()
        st.metric("Offene Antworten gesamt", f"{total_open_responses:,}")
        
        # Thematische Verteilung offener Fragen
        if 'Thema' in open_data.columns:
            theme_distribution = open_data.groupby('Thema')['Anzahl_Antworten'].sum().sort_values(ascending=False)
            
            fig = px.pie(
                values=theme_distribution.values,
                names=theme_distribution.index,
                title="Verteilung offener Rückmeldungen nach Thema"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_segmented_trends(self, scale_data, choice_data, selected_segment):
        """Placeholder für segmentierte Trend-Analyse"""
        st.info("🚧 Segmentierte Trend-Analyse wird implementiert wenn demografische Daten verfügbar sind.")
    
    def _show_segment_comparison(self, scale_data, choice_data, selected_segment):
        """Placeholder für Segment-Vergleiche"""
        st.info("🚧 Segment-Vergleiche werden implementiert wenn demografische Daten verfügbar sind.")
    
    def _show_qualitative_by_segment(self, open_data, choice_data, selected_segment):
        """Placeholder für qualitative Analyse nach Segmenten"""
        st.info("🚧 Qualitative Segmentierung wird implementiert wenn demografische Daten verfügbar sind.")

class KI_Schulqualitäts_Analyzer:
    """KI-gestützte Analyse von IQES-Schulqualitätsdaten mit Google Gemini"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.pca = None
        self.gemini_client = None
        self.openai_client = None  # Fallback
        self.setup_ai_clients()
    
    def setup_ai_clients(self):
        """Setup AI-Clients: Primär Gemini, Fallback OpenAI"""
        # Google Gemini (primär)
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GOOGLE_AI_API_KEY')
            if api_key:
                try:
                    self.gemini_client = genai.Client(api_key=api_key)
                    # Test API connection
                    test_response = self.gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents="Test"
                    )
                    st.sidebar.success("🤖 Google Gemini AI verbunden")
                except Exception as e:
                    st.sidebar.error(f"❌ Gemini Verbindungsfehler: {str(e)[:100]}...")
                    self.gemini_client = None
        
        # OpenAI (Fallback)
        if OPENAI_AVAILABLE and not self.gemini_client:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    st.sidebar.info("🤖 OpenAI Fallback verbunden")
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
        
        # Erweiterte AI-Analyse mit Gemini (primär) oder OpenAI (fallback)
        if self.gemini_client:
            analysis['ai_insights'] = self.generate_gemini_insights_german(text_responses)
            analysis['ai_recommendations'] = self.generate_gemini_recommendations(text_responses)
        elif self.openai_client:
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
    
    def generate_gemini_insights_german(self, texts):
        """Generiert KI-Insights für deutsche Texte mit Google Gemini"""
        if not self.gemini_client or len(texts) == 0:
            return None
        
        sample_texts = texts[:8] if len(texts) > 8 else texts
        combined_text = '\n\n'.join(sample_texts)
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""Du bist ein Experte für Schulentwicklung und IQES-Evaluationen. 
                
Analysiere diese deutschen Schülerrückmeldungen und gib eine strukturierte Analyse:

SCHÜLERRÜCKMELDUNGEN:
{combined_text}

AUFGABE:
1. 📊 HAUPTTHEMEN: Identifiziere die 3 wichtigsten Themen
2. 😊 POSITIVE ASPEKTE: Was läuft gut?
3. ⚠️ PROBLEMBEREICHE: Welche Herausforderungen gibt es?
4. 🎯 SOFORTMASSNAHMEN: 2-3 konkrete, umsetzbare Empfehlungen

Antworte auf Deutsch, strukturiert und praxisorientiert für Schulleitung."""
            )
            
            return response.text
            
        except Exception as e:
            st.error(f"Gemini Fehler: {e}")
            return None
    
    def generate_gemini_recommendations(self, texts):
        """Generiert spezifische Handlungsempfehlungen mit Gemini"""
        if not self.gemini_client or len(texts) == 0:
            return []
        
        sample_texts = texts[:5] if len(texts) > 5 else texts
        combined_text = '\n\n'.join(sample_texts)
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""Basierend auf diesen IQES-Schülerrückmeldungen, erstelle 3 priorisierte Handlungsempfehlungen:

RÜCKMELDUNGEN:
{combined_text}

FORMAT (JSON-ähnlich):
1. PRIORITÄT: HOCH/MITTEL/NIEDRIG
   TITEL: Kurzer, prägnanter Titel
   MASSNAHME: Konkrete Aktion
   ZEITRAHMEN: Wann umsetzen
   BEGRÜNDUNG: Warum wichtig

Fokus auf umsetzbare, realistische Maßnahmen für Schulleitung. Auf Deutsch antworten."""
            )
            
            # Parse response into structured recommendations
            recommendations_text = response.text
            recommendations = []
            
            # Simple parsing - in Produktion würde man robusteres Parsing verwenden
            if "1." in recommendations_text and "PRIORITÄT" in recommendations_text:
                recommendations.append({
                    'source': 'Gemini AI',
                    'content': recommendations_text,
                    'type': 'Strukturierte Empfehlungen'
                })
            
            return recommendations
            
        except Exception as e:
            st.error(f"Gemini Empfehlungen Fehler: {e}")
            return []
    
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
                try:
                    result = dashboard.load_excel_files(uploaded_files)
                    if result:
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
                        
                        # KI-Features Aktivierung (optional)
                        st.header("🤖 KI-Features")
                        
                        enable_ai_analysis = st.checkbox(
                            "🧠 KI-Analyse aktivieren", 
                            value=False,
                            help="Aktiviert intelligente Textanalyse mit Google Gemini AI. Standard deaktiviert um API-Calls zu vermeiden."
                        )
                        
                        if enable_ai_analysis:
                            # KI-Analyzer nur bei Bedarf initialisieren
                            if dashboard.ki_analyzer is None:
                                try:
                                    dashboard.ki_analyzer = KI_Schulqualitäts_Analyzer()
                                    if dashboard.ki_analyzer.gemini_client:
                                        st.success("✅ Google Gemini AI verbunden")
                                    elif dashboard.ki_analyzer.openai_client:
                                        st.info("🔄 OpenAI Fallback aktiv")
                                    else:
                                        st.warning("⚠️ Keine KI-Services verfügbar")
                                        enable_ai_analysis = False
                                except Exception as e:
                                    st.error(f"❌ KI-Setup Fehler: {e}")
                                    enable_ai_analysis = False
                        else:
                            st.info("💡 KI-Features deaktiviert (spart API-Calls)")
                        
                        # Performance-Tools
                        st.header("⚡ Performance")
                        
                        if st.button("🗑️ Cache leeren", help="Leert den Daten-Cache und erzwingt Neuverarbeitung"):
                            if 'processed_data' in st.session_state:
                                del st.session_state.processed_data
                            if 'data_loaded' in st.session_state:
                                del st.session_state.data_loaded
                            if 'last_file_hash' in st.session_state:
                                del st.session_state.last_file_hash
                            st.cache_data.clear()
                            st.success("✅ Cache geleert!")
                            st.rerun()
                        
                        # Memory usage info
                        if not dashboard.processed_data.empty:
                            memory_usage = dashboard.processed_data.memory_usage(deep=True).sum() / 1024 / 1024
                            st.metric("💾 Speicherverbrauch", f"{memory_usage:.1f} MB")
                            if memory_usage > MAX_MEMORY_MB:
                                st.warning(f"⚠️ Hoher Speicherverbrauch (>{MAX_MEMORY_MB}MB). Cache leeren empfohlen.")
                        
                        # DEBUG-Informationen anzeigen
                        with st.expander("🔍 Debug-Informationen", expanded=False):
                            if hasattr(st.session_state, 'debug_categories'):
                                st.write("**Gefundene Kategorien:**")
                                for cat in st.session_state.debug_categories:
                                    st.write(f"• {cat}")
                            
                            if hasattr(st.session_state, 'debug_themes'):
                                st.write("**Themen-Zuordnungen:**")
                                for theme in st.session_state.debug_themes:
                                    st.write(f"• {theme}")
                                
                    else:
                        st.error("❌ Fehler beim Laden der IQES-Dateien!")
                        enable_ai_analysis = False
                except Exception as e:
                    st.error(f"❌ Unerwarteter Fehler beim Laden: {str(e)}")
                    st.info("💡 Versuchen Sie Cache zu leeren oder kontaktieren Sie den Support.")
                    enable_ai_analysis = False
    
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
        
        # Executive Summary
        st.markdown('<div class="executive-summary">', unsafe_allow_html=True)
        st.markdown("### 📋 Executive Summary")
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        scale_data = filtered_data[filtered_data['Fragentyp'] == 'Antwortskala']
        if not scale_data.empty:
            avg_rating = scale_data['Bewertung'].mean()
            critical_count = len(scale_data[scale_data['Verbesserungsbedarf'] == 'HOCH'])
            total_responses = scale_data['Anzahl_Antworten'].sum()
            
            with summary_col1:
                st.markdown(f"**Gesamtbewertung:** {avg_rating:.2f}/4.0")
                trend_icon = "📈" if avg_rating >= 3.0 else "⚠️" if avg_rating >= 2.5 else "🚨"
                st.markdown(f"{trend_icon} Qualitätsniveau: {'Hoch' if avg_rating >= 3.0 else 'Mittel' if avg_rating >= 2.5 else 'Kritisch'}")
                
            with summary_col2:
                st.markdown(f"**Kritische Bereiche:** {critical_count}")
                st.markdown(f"📊 Gesamtantworten: {total_responses:,}")
                
            with summary_col3:
                if len(filtered_data['Bildungsgang'].unique()) > 1:
                    st.markdown(f"**Bildungsgänge:** {len(filtered_data['Bildungsgang'].unique())}")
                if len(filtered_data['Datum'].unique()) > 1:
                    st.markdown(f"**Evaluationszeiträume:** {len(filtered_data['Datum'].unique())}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        
        # Executive Visualisierungen
        st.header("📈 Executive Dashboard")
        
        # Zeitreihen-Visualisierung
        if len(filtered_data['Datum'].unique()) > 1:
            st.subheader("⏱️ Zeitreihen-Analyse")
            dashboard.create_timeline_visualization(filtered_data)
        
        # Top/Bottom Rankings
        st.subheader("🎯 Kritische Bereiche & Best Practices")
        dashboard.create_rankings_visualization(filtered_data)
        
        # BM vs VK Vergleich
        if len(filtered_data['Bildungsgang'].unique()) > 1:
            st.subheader("📊 Bildungsgang-Vergleich")
            dashboard.create_comparison_visualization(filtered_data)
        
        # Intelligente Segmentierung (Kombination aller Fragentypen)
        st.subheader("🎯 Intelligente Segmentierungs-Analyse")
        dashboard.create_segmentation_analysis(filtered_data)
        
        # KI-gestützte Analyse (wenn aktiviert)
        if enable_ai_analysis:
            st.header("🤖 KI-gestützte Analyse & Empfehlungen")
            
            # KI-Textanalyse für offene Antworten
            open_questions_data = filtered_data[filtered_data['Fragentyp'] == 'Offene Frage']
            if not open_questions_data.empty:
                with st.expander("📝 KI-Textanalyse offener Antworten", expanded=True):
                    
                    # Sammle alle Textantworten
                    all_text_responses = []
                    for _, row in open_questions_data.iterrows():
                        if 'Textantworten' in row and row['Textantworten']:
                            all_text_responses.extend(row['Textantworten'])
                    
                    if all_text_responses and dashboard.ki_analyzer:
                        text_analysis = dashboard.ki_analyzer.analyze_german_text_responses(all_text_responses)
                        
                        # Sentiment Analyse
                        if 'sentiment_analysis' in text_analysis:
                            sentiment = text_analysis['sentiment_analysis']
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("😊 Positive Stimmung", f"{sentiment['positive_ratio']*100:.1f}%")
                            with col2:
                                st.metric("😐 Neutrale Stimmung", f"{(1-sentiment['positive_ratio']-sentiment['negative_ratio'])*100:.1f}%")
                            with col3:
                                st.metric("😟 Negative Stimmung", f"{sentiment['negative_ratio']*100:.1f}%")
                        
                        # Keywords
                        if 'keyword_analysis' in text_analysis:
                            st.write("**📋 Häufigste Begriffe:**")
                            keywords = text_analysis['keyword_analysis']
                            keyword_text = " • ".join([f"{word} ({count})" for word, count in list(keywords.items())[:10]])
                            st.write(keyword_text)
                        
                        # KI-Insights
                        if 'ai_insights' in text_analysis and text_analysis['ai_insights']:
                            st.write("**🧠 KI-Analyse:**")
                            st.write(text_analysis['ai_insights'])
                        
                        # KI-Empfehlungen
                        if 'ai_recommendations' in text_analysis and text_analysis['ai_recommendations']:
                            st.write("**🎯 KI-Empfehlungen:**")
                            for rec in text_analysis['ai_recommendations']:
                                st.write(rec['content'])
                    else:
                        st.info("Keine Textantworten für KI-Analyse verfügbar.")
            
            # Datenbasierte Empfehlungen
            st.subheader("📊 Intelligente Handlungsempfehlungen")
            if dashboard.ki_analyzer:
                recommendations = dashboard.ki_analyzer.generate_smart_recommendations(filtered_data)
            else:
                recommendations = []
        
        if enable_ai_analysis and recommendations:
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