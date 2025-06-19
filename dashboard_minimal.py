import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import re

# Streamlit-Konfiguration
st.set_page_config(
    page_title="IQES-Dashboard (Minimal)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Basis-CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class MinimalIQESDashboard:
    def __init__(self):
        self.processed_data = pd.DataFrame()
    
    def extract_date_from_filename(self, filename):
        """Extrahiert Datum aus Dateiname"""
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
        
        return pd.to_datetime("today")
    
    def determine_bildungsgang(self, filename):
        """Bestimmt Bildungsgang aus Dateiname"""
        filename_upper = filename.upper()
        if "BM" in filename_upper or "BÜROMANAGEMENT" in filename_upper:
            return "BM (Büromanagement)"
        elif "VK" in filename_upper or "VERANSTALTUNG" in filename_upper:
            return "VK (Veranstaltungskaufleute)"
        elif "GK" in filename_upper:
            return "GK"
        elif "IT" in filename_upper:
            return "IT"
        return "Unbekannt"
    
    def process_excel_file(self, uploaded_file):
        """Verarbeitet eine IQES Excel-Datei"""
        try:
            # Excel laden
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            
            # Basis-Informationen extrahieren
            eval_date = self.extract_date_from_filename(uploaded_file.name)
            bildungsgang = self.determine_bildungsgang(uploaded_file.name)
            eval_type = "Abschluss" if "Abschluss" in uploaded_file.name else "Zwischenevaluation"
            
            questions = []
            
            # Durch alle Sheets iterieren
            for sheet_name, df in excel_data.items():
                if df.empty or "Antwortskala" not in sheet_name:
                    continue
                
                # Fragenummer aus Sheet-Name extrahieren
                question_num = ""
                if "Frage" in sheet_name:
                    question_num = sheet_name.split("Frage")[1].split("(")[0].strip()
                
                # Fragen verarbeiten (ab Zeile 2, da Zeile 1 meist Header ist)
                for idx in range(2, len(df)):
                    row = df.iloc[idx]
                    
                    # Frage-Text (Spalte A)
                    if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == "":
                        continue
                    
                    question_text = str(row.iloc[0]).strip()
                    
                    # Bewertung (Spalte J - Index 9)
                    if len(row) > 9 and pd.notna(row.iloc[9]):
                        try:
                            rating = float(row.iloc[9])
                            if 1 <= rating <= 4:  # Valide IQES-Bewertung
                                questions.append({
                                    'Datum': eval_date,
                                    'Bildungsgang': bildungsgang,
                                    'Evaluationstyp': eval_type,
                                    'Fragenummer': question_num,
                                    'Frage': question_text,
                                    'Bewertung': rating,
                                    'Quelldatei': uploaded_file.name
                                })
                        except (ValueError, TypeError):
                            continue
            
            return pd.DataFrame(questions)
            
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten von {uploaded_file.name}: {str(e)}")
            return pd.DataFrame()
    
    def load_files(self, uploaded_files):
        """Lädt mehrere IQES-Dateien"""
        all_data = []
        
        for uploaded_file in uploaded_files:
            data = self.process_excel_file(uploaded_file)
            if not data.empty:
                all_data.append(data)
        
        if all_data:
            self.processed_data = pd.concat(all_data, ignore_index=True)
            return True
        return False
    
    def create_basic_metrics(self):
        """Erstellt Basis-KPIs"""
        if self.processed_data.empty:
            return {}
        
        return {
            'Durchschnittsbewertung': round(self.processed_data['Bewertung'].mean(), 2),
            'Anzahl_Fragen': len(self.processed_data),
            'Anzahl_Bildungsgaenge': len(self.processed_data['Bildungsgang'].unique()),
            'Kritische_Fragen': len(self.processed_data[self.processed_data['Bewertung'] < 2.5])
        }
    
    def create_rating_chart(self, data):
        """Erstellt Bewertungs-Chart"""
        if data.empty:
            return go.Figure()
        
        # Top 10 schlechteste Bewertungen
        worst_ratings = data.nsmallest(10, 'Bewertung')
        
        fig = px.bar(
            worst_ratings,
            x='Bewertung',
            y='Frage',
            orientation='h',
            title="🚨 Top 10 Kritische Bereiche",
            color='Bewertung',
            color_continuous_scale='RdYlGn_r'
        )
        
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        return fig
    
    def create_comparison_chart(self, data):
        """Erstellt Bildungsgang-Vergleich"""
        if data.empty or len(data['Bildungsgang'].unique()) < 2:
            return go.Figure()
        
        # Durchschnitt pro Bildungsgang
        avg_by_bg = data.groupby('Bildungsgang')['Bewertung'].mean().reset_index()
        
        fig = px.bar(
            avg_by_bg,
            x='Bildungsgang',
            y='Bewertung',
            title="📊 Bewertung nach Bildungsgang",
            color='Bewertung',
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(height=400)
        return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 IQES-Dashboard (Minimal Version)</h1>', unsafe_allow_html=True)
    
    # Dashboard-Instanz
    dashboard = MinimalIQESDashboard()
    
    # Sidebar für Upload
    with st.sidebar:
        st.header("📁 IQES-Daten Upload")
        uploaded_files = st.file_uploader(
            "Excel-Dateien hochladen",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="Laden Sie Ihre IQES-Evaluationsdateien hoch."
        )
        
        # Initialisiere Filter-Variablen mit Standardwerten
        selected_bildungsgang = 'Alle'
        selected_eval_typ = 'Alle'
        
        if uploaded_files:
            with st.spinner('Daten werden verarbeitet...'):
                if dashboard.load_files(uploaded_files):
                    st.success(f"✅ {len(uploaded_files)} Dateien geladen!")
                    
                    # Filter-Optionen
                    st.header("🔍 Filter")
                    
                    # Bildungsgang-Filter
                    bildungsgaenge = ['Alle'] + list(dashboard.processed_data['Bildungsgang'].unique())
                    selected_bildungsgang = st.selectbox("Bildungsgang", bildungsgaenge)
                    
                    # Evaluationstyp-Filter  
                    eval_typen = ['Alle'] + list(dashboard.processed_data['Evaluationstyp'].unique())
                    selected_eval_typ = st.selectbox("Evaluationstyp", eval_typen)
                    
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
        
        # KPIs anzeigen
        metrics = dashboard.create_basic_metrics()
        if metrics:
            st.header("📊 Kennzahlen-Überblick")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Durchschnittsbewertung", f"{metrics['Durchschnittsbewertung']}/4.0")
            with col2:
                st.metric("Anzahl Fragen", metrics['Anzahl_Fragen'])
            with col3:
                st.metric("Bildungsgänge", metrics['Anzahl_Bildungsgaenge'])
            with col4:
                st.metric("Kritische Bereiche", metrics['Kritische_Fragen'])
        
        # Visualisierungen
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("🚨 Kritische Bereiche")
            chart1 = dashboard.create_rating_chart(filtered_data)
            if chart1.data:
                st.plotly_chart(chart1, use_container_width=True)
            else:
                st.info("Keine Daten für Bewertungs-Chart")
        
        with col2:
            st.header("📊 Bildungsgang-Vergleich")
            chart2 = dashboard.create_comparison_chart(filtered_data)
            if chart2.data:
                st.plotly_chart(chart2, use_container_width=True)
            else:
                st.info("Mindestens 2 Bildungsgänge für Vergleich erforderlich")
        
        # Daten-Tabelle
        st.header("📋 Detaildaten")
        if not filtered_data.empty:
            # Nur relevante Spalten anzeigen
            display_data = filtered_data[['Datum', 'Bildungsgang', 'Fragenummer', 'Frage', 'Bewertung']].copy()
            display_data = display_data.sort_values('Bewertung')  # Schlechteste zuerst
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Daten entsprechen den gewählten Filtern.")
    
    else:
        st.info("👆 Laden Sie IQES-Excel-Dateien hoch, um zu beginnen.")

if __name__ == "__main__":
    main()