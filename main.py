"""
IQES-Dashboard - Modular Version
Hauptanwendung mit sauberer, modularer Architektur
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.iqes_parser import IQESParser
from ui.visualizations import IQESVisualizations
from config.themes import (
    get_theme_for_question, 
    get_rating_category, 
    BILDUNGSGANG_CONFIG,
    get_theme_summary
)

# Streamlit-Konfiguration
st.set_page_config(
    page_title="IQES-Dashboard (Modular)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS-Styling
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
    .theme-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        color: white;
        font-size: 0.8rem;
        margin: 0.2rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


class ModularIQESDashboard:
    """Hauptklasse für das modulare IQES-Dashboard"""
    
    def __init__(self):
        self.parser = IQESParser()
        self.visualizations = IQESVisualizations()
        self.data = pd.DataFrame()
    
    def load_data(self, uploaded_files):
        """Lädt und verarbeitet IQES-Dateien"""
        try:
            self.data = self.parser.parse_multiple_files(uploaded_files)
            
            # Thematische Zuordnung hinzufügen
            if not self.data.empty:
                self.data['Thema'] = self.data['Fragenummer'].apply(
                    lambda x: get_theme_for_question(x)['theme']
                )
                self.data['Thema_Farbe'] = self.data['Fragenummer'].apply(
                    lambda x: get_theme_for_question(x)['color']
                )
                self.data['Bewertungskategorie'] = self.data['Bewertung'].apply(
                    lambda x: get_rating_category(x)['category']
                )
            
            return True
        except Exception as e:
            st.error(f"Fehler beim Laden der Daten: {str(e)}")
            return False
    
    def render_sidebar(self):
        """Rendert die Sidebar mit Upload und Filtern"""
        with st.sidebar:
            st.header("📁 IQES-Daten Upload")
            uploaded_files = st.file_uploader(
                "Excel-Dateien hochladen",
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                help="Laden Sie Ihre IQES-Evaluationsdateien hoch."
            )
            
            # Initialisiere Filter-Variablen
            selected_bildungsgang = 'Alle'
            selected_thema = 'Alle'
            selected_kategorie = 'Alle'
            
            if uploaded_files:
                with st.spinner('📊 Daten werden verarbeitet...'):
                    if self.load_data(uploaded_files):
                        st.success(f"✅ {len(uploaded_files)} Dateien erfolgreich geladen!")
                        
                        # Filter-Optionen
                        st.header("🔍 Filter")
                        
                        # Bildungsgang-Filter
                        bildungsgaenge = ['Alle'] + sorted(self.data['Bildungsgang'].unique())
                        selected_bildungsgang = st.selectbox("Bildungsgang", bildungsgaenge)
                        
                        # Thema-Filter
                        themen = ['Alle'] + sorted(self.data['Thema'].unique())
                        selected_thema = st.selectbox("Thema", themen)
                        
                        # Bewertungskategorie-Filter
                        kategorien = ['Alle'] + sorted(self.data['Bewertungskategorie'].unique())
                        selected_kategorie = st.selectbox("Bewertungskategorie", kategorien)
                        
                        # Statistiken anzeigen
                        st.header("📈 Daten-Übersicht")
                        st.metric("Gesamtfragen", len(self.data))
                        st.metric("Bildungsgänge", len(self.data['Bildungsgang'].unique()))
                        st.metric("Themen", len(self.data['Thema'].unique()))
                        
                    else:
                        st.error("❌ Fehler beim Laden der Dateien!")
            
            return uploaded_files, selected_bildungsgang, selected_thema, selected_kategorie
    
    def apply_filters(self, selected_bildungsgang, selected_thema, selected_kategorie):
        """Wendet Filter auf die Daten an"""
        filtered_data = self.data.copy()
        
        if selected_bildungsgang != 'Alle':
            filtered_data = filtered_data[filtered_data['Bildungsgang'] == selected_bildungsgang]
        
        if selected_thema != 'Alle':
            filtered_data = filtered_data[filtered_data['Thema'] == selected_thema]
        
        if selected_kategorie != 'Alle':
            filtered_data = filtered_data[filtered_data['Bewertungskategorie'] == selected_kategorie]
        
        return filtered_data
    
    def render_metrics(self, data):
        """Rendert KPI-Metriken"""
        if data.empty:
            return
        
        metrics = self.visualizations.create_metrics_cards_data(data)
        
        st.header("📊 Kennzahlen-Überblick")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Durchschnittsbewertung", f"{metrics['Durchschnittsbewertung']}/4.0")
        with col2:
            st.metric("Kritische Bereiche", metrics['Kritische_Fragen'])
        with col3:
            st.metric("Sehr gute Bereiche", metrics['Sehr_gute_Fragen'])
        with col4:
            st.metric("Evaluationszeiträume", metrics['Evaluationszeitraeume'])
    
    def render_visualizations(self, data):
        """Rendert alle Visualisierungen"""
        if data.empty:
            st.info("Keine Daten entsprechen den gewählten Filtern.")
            return
        
        # Hauptcharts
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("🚨 Kritische Bereiche")
            chart1 = self.visualizations.create_rating_chart(data)
            st.plotly_chart(chart1, use_container_width=True)
        
        with col2:
            st.header("📊 Bildungsgang-Vergleich")
            chart2 = self.visualizations.create_comparison_chart(data)
            st.plotly_chart(chart2, use_container_width=True)
        
        # Zusätzliche Charts
        col3, col4 = st.columns(2)
        
        with col3:
            st.header("📈 Bewertungsverteilung")
            chart3 = self.visualizations.create_distribution_chart(data)
            st.plotly_chart(chart3, use_container_width=True)
        
        with col4:
            st.header("📅 Trend-Analyse")
            chart4 = self.visualizations.create_timeline_chart(data)
            st.plotly_chart(chart4, use_container_width=True)
    
    def render_data_table(self, data):
        """Rendert Daten-Tabelle"""
        if data.empty:
            return
        
        st.header("📋 Detaildaten")
        
        # Themen-Übersicht
        if len(data['Thema'].unique()) > 1:
            theme_summary = data.groupby('Thema').agg({
                'Bewertung': ['mean', 'count'],
                'Thema_Farbe': 'first'
            }).round(2)
            theme_summary.columns = ['Durchschnitt', 'Anzahl', 'Farbe']
            theme_summary = theme_summary.reset_index()
            
            st.subheader("🎨 Themen-Übersicht")
            for _, row in theme_summary.iterrows():
                st.markdown(
                    f'<span class="theme-badge" style="background-color: {row["Farbe"]}">'
                    f'{row["Thema"]}: {row["Durchschnitt"]}/4.0 ({row["Anzahl"]} Fragen)</span>',
                    unsafe_allow_html=True
                )
        
        # Detailtabelle
        st.subheader("📊 Alle Daten")
        display_data = data[[
            'Datum', 'Bildungsgang', 'Thema', 'Fragenummer', 
            'Frage', 'Bewertung', 'Bewertungskategorie'
        ]].copy()
        
        display_data = display_data.sort_values('Bewertung')
        st.dataframe(display_data, use_container_width=True, hide_index=True)


def main():
    """Hauptfunktion"""
    # Header
    st.markdown('<h1 class="main-header">🎓 IQES-DASHBOARD (Modular)</h1>', unsafe_allow_html=True)
    
    # Dashboard-Instanz
    dashboard = ModularIQESDashboard()
    
    # Sidebar rendern und Filter erhalten
    uploaded_files, selected_bildungsgang, selected_thema, selected_kategorie = dashboard.render_sidebar()
    
    # Hauptbereich
    if not dashboard.data.empty:
        # Filter anwenden
        filtered_data = dashboard.apply_filters(selected_bildungsgang, selected_thema, selected_kategorie)
        
        # Inhalte rendern
        dashboard.render_metrics(filtered_data)
        dashboard.render_visualizations(filtered_data)
        dashboard.render_data_table(filtered_data)
        
    else:
        st.info("👆 Laden Sie IQES-Excel-Dateien hoch, um zu beginnen.")
        
        # Info-Sektion
        st.header("ℹ️ Über dieses Dashboard")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🏗️ Modulare Architektur**
            - Saubere Code-Struktur
            - Wartbare Module
            - Erweiterbare Funktionen
            """)
        
        with col2:
            st.markdown("""
            **📊 IQES-Features**
            - Excel-Upload & Parsing
            - Thematische Zuordnung
            - Interaktive Visualisierungen
            """)
        
        with col3:
            st.markdown("""
            **🔍 Analyse-Funktionen**
            - Kritische Bereiche
            - Bildungsgang-Vergleiche
            - Trend-Analysen
            """)


if __name__ == "__main__":
    main()