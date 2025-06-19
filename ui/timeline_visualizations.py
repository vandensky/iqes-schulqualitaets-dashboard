"""
IQES Timeline Visualizations - Spezialisierte Charts für Zeitreihenanalyse
Fokus auf Antwortskala-Fragen (1-4) und Trend-Vergleiche
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Optional
from core.timeline_analyzer import IQESTimelineAnalyzer


class IQESTimelineVisualizations:
    """UI-Komponenten für IQES-Zeitreihenanalyse"""
    
    def __init__(self):
        self.analyzer = IQESTimelineAnalyzer()
    
    def render_timeline_analysis(self, data: pd.DataFrame):
        """
        Rendert die komplette Timeline-Analyse mit Tabs
        
        Args:
            data: Vollständiger IQES-Datensatz
        """
        if data.empty:
            st.info("Keine Daten für Timeline-Analyse verfügbar")
            return
        
        # Nur Antwortskala-Fragen (1-4) filtern
        scale_data = self.analyzer.filter_rating_scale_questions(data)
        
        if scale_data.empty:
            st.warning("Keine Antwortskala-Fragen (1-4 Bewertung) für Timeline-Analyse gefunden")
            return
        
        # Prüfe ob mindestens 2 Zeiträume vorhanden
        if len(scale_data['Datum'].unique()) < 2:
            st.info("Mindestens 2 Evaluationszeiträume für Timeline-Analyse erforderlich")
            return
        
        # Timeline-Insights anzeigen
        insights = self.analyzer.get_timeline_insights(scale_data)
        self._render_timeline_insights(insights)
        
        # Tab-Navigation für verschiedene Timeline-Ansichten
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Thematische Trends", 
            "📈 Einzelfragen", 
            "📊 Bildungsgang-Vergleich",
            "📋 Trend-Übersicht"
        ])
        
        with tab1:
            self._render_thematic_timeline(scale_data)
        
        with tab2:
            self._render_individual_questions_timeline(scale_data)
        
        with tab3:
            self._render_bildungsgang_timeline(scale_data)
        
        with tab4:
            self._render_trend_summary_tables(scale_data)
    
    def _render_timeline_insights(self, insights: dict):
        """Rendert Key-Insights der Timeline-Analyse"""
        if not insights:
            return
        
        st.markdown("### 🔍 Timeline-Insights (nur Antwortskala 1-4)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gesamtfragen", insights.get('total_questions', 0))
        
        with col2:
            st.metric("Evaluationszeiträume", insights.get('total_periods', 0))
        
        with col3:
            st.metric("Multi-Period Fragen", insights.get('multi_period_questions', 0))
        
        with col4:
            overall_trend = insights.get('overall_trend')
            if overall_trend:
                trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(
                    overall_trend['direction'], "➡️"
                )
                st.metric(
                    "Gesamttrend", 
                    f"{trend_icon} {overall_trend['change']:+.2f}",
                    delta=overall_trend['change']
                )
        
        # Beste/schlechteste Trends
        if insights.get('best_improving_theme') or insights.get('worst_declining_theme'):
            st.markdown("#### 🎯 Auffällige Trends")
            
            col1, col2 = st.columns(2)
            
            with col1:
                best = insights.get('best_improving_theme')
                if best and best['change'] > 0.1:
                    st.success(f"📈 **Beste Verbesserung:** {best['name']} (+{best['change']:.2f})")
            
            with col2:
                worst = insights.get('worst_declining_theme')
                if worst and worst['change'] < -0.1:
                    st.error(f"📉 **Stärkster Rückgang:** {worst['name']} ({worst['change']:.2f})")
    
    def _render_thematic_timeline(self, scale_data: pd.DataFrame):
        """Rendert thematische Timeline-Analyse"""
        st.markdown("### 🎯 Thematische Entwicklung")
        st.markdown("*Nur Antwortskala-Fragen (1-4 Bewertung) werden berücksichtigt*")
        
        if 'Thema' not in scale_data.columns:
            st.warning("Keine Themen-Zuordnung in den Daten gefunden")
            return
        
        # Thematischer Timeline-Chart
        chart = self.analyzer.create_thematic_timeline_chart(scale_data)
        st.plotly_chart(chart, use_container_width=True)
        
        # Themen-Trend-Tabelle
        st.markdown("#### 📊 Themenbereiche-Übersicht")
        theme_trends = self.analyzer.generate_trend_summary_table(scale_data, 'Thema')
        
        if not theme_trends.empty:
            # Spalten für Anzeige auswählen (nur die die auch existieren)
            base_cols = ['Thema', 'Erste_Bewertung', 'Aktuelle_Bewertung', 'Trend_Change']
            display_cols = [col for col in base_cols if col in theme_trends.columns]
            
            # Status-Spalte hinzufügen wenn verfügbar
            if 'Trend_Status' in theme_trends.columns:
                display_cols.append('Trend_Status')
            
            # Anzahl Fragen hinzufügen wenn verfügbar
            if 'Anzahl_Fragen' in theme_trends.columns:
                display_cols.insert(1, 'Anzahl_Fragen')
            
            if display_cols:
                display_df = theme_trends[display_cols].copy()
                
                # Spalten-Namen anpassen
                col_mapping = {
                    'Thema': 'Themenbereich',
                    'Anzahl_Fragen': 'Anzahl Fragen',
                    'Erste_Bewertung': 'Erste Bewertung',
                    'Aktuelle_Bewertung': 'Aktuelle Bewertung',
                    'Trend_Change': 'Trend',
                    'Trend_Status': 'Entwicklung'
                }
                
                new_col_names = [col_mapping.get(col, col) for col in display_cols]
                display_df.columns = new_col_names
                
                # Farbkodierung für Trend-Werte
                def highlight_trends(val):
                    if isinstance(val, (int, float)):
                        if val > 0.1:
                            return 'background-color: lightgreen'
                        elif val < -0.1:
                            return 'background-color: lightcoral'
                        else:
                            return 'background-color: lightyellow'
                    return ''
                
                try:
                    # Use new pandas API if available, fallback to old one
                    styled_df = display_df.style.map(highlight_trends, subset=['Trend'] if 'Trend' in display_df.columns else [])
                except AttributeError:
                    styled_df = display_df.style.applymap(highlight_trends, subset=['Trend'] if 'Trend' in display_df.columns else [])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Keine anzuzeigenden Trend-Daten gefunden")
        else:
            st.info("Keine Trend-Daten für Themenbereiche verfügbar")
    
    def _render_individual_questions_timeline(self, scale_data: pd.DataFrame):
        """Rendert Einzelfragen-Timeline"""
        st.markdown("### 📈 Einzelfragen-Trends")
        st.markdown("*Nur Fragen die in mehreren Zeiträumen evaluiert wurden (Antwortskala 1-4)*")
        
        # Multi-Period-Fragen identifizieren
        multi_period_questions = self.analyzer.identify_multi_period_questions(scale_data)
        
        if not multi_period_questions:
            st.info("Keine Fragen gefunden, die in mehreren Zeiträumen evaluiert wurden")
            return
        
        # Fragenauswahl-Widget
        st.markdown(f"**{len(multi_period_questions)} Fragen** in mehreren Zeiträumen verfügbar")
        
        selected_questions = st.multiselect(
            "📋 Fragen für Trend-Vergleich auswählen:",
            options=multi_period_questions,
            default=multi_period_questions[:5] if len(multi_period_questions) >= 5 else multi_period_questions,
            help="Wählen Sie bis zu 10 Fragen für den Trend-Vergleich aus"
        )
        
        if selected_questions:
            # Einzelfragen-Timeline-Chart
            chart = self.analyzer.create_individual_questions_timeline(scale_data, selected_questions)
            st.plotly_chart(chart, use_container_width=True)
            
            # Trend-Details-Tabelle
            st.markdown("#### 📊 Trend-Details")
            question_trends = self.analyzer.generate_trend_summary_table(scale_data, 'Fragenummer')
            
            if not question_trends.empty:
                # Nur ausgewählte Fragen anzeigen
                selected_trends = question_trends[
                    question_trends['Fragenummer'].isin(selected_questions)
                ].copy()
                
                if not selected_trends.empty:
                    # Frage-Text hinzufügen wenn möglich
                    if 'Frage' in scale_data.columns:
                        question_texts = scale_data.groupby('Fragenummer')['Frage'].first().reset_index()
                        selected_trends = selected_trends.merge(question_texts, on='Fragenummer', how='left')
                        # Frage-Text kürzen
                        selected_trends['Frage_Kurz'] = selected_trends['Frage'].apply(
                            lambda x: str(x)[:80] + "..." if len(str(x)) > 80 else str(x)
                        )
                    
                    # Spalten für Anzeige (nur die die existieren)
                    base_cols = ['Fragenummer', 'Erste_Bewertung', 'Aktuelle_Bewertung', 'Trend_Change']
                    display_cols = [col for col in base_cols if col in selected_trends.columns]
                    col_names = ['Frage Nr.', 'Erste Bewertung', 'Aktuelle Bewertung', 'Trend']
                    
                    # Status-Spalte hinzufügen wenn verfügbar
                    if 'Trend_Status' in selected_trends.columns:
                        display_cols.append('Trend_Status')
                        col_names.append('Entwicklung')
                    
                    # Frage-Text einfügen wenn verfügbar
                    if 'Frage_Kurz' in selected_trends.columns:
                        display_cols.insert(1, 'Frage_Kurz')
                        col_names.insert(1, 'Fragetext')
                    
                    display_df = selected_trends[display_cols].copy()
                    display_df.columns = col_names
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Wählen Sie Fragen für die Timeline-Analyse aus")
    
    def _render_bildungsgang_timeline(self, scale_data: pd.DataFrame):
        """Rendert Bildungsgang-Vergleichs-Timeline"""
        st.markdown("### 📊 Bildungsgang-Entwicklung")
        st.markdown("*Vergleich der durchschnittlichen Bewertungen über Zeit (nur Antwortskala 1-4)*")
        
        if 'Bildungsgang' not in scale_data.columns:
            st.warning("Keine Bildungsgang-Information in den Daten gefunden")
            return
        
        if len(scale_data['Bildungsgang'].unique()) < 2:
            st.info("Mindestens 2 Bildungsgänge für Vergleich erforderlich")
            return
        
        # Bildungsgang-Timeline-Chart
        chart = self.analyzer.create_bildungsgang_timeline(scale_data)
        st.plotly_chart(chart, use_container_width=True)
        
        # Bildungsgang-Trend-Tabelle
        st.markdown("#### 📊 Bildungsgang-Trends")
        bg_trends = self.analyzer.generate_trend_summary_table(scale_data, 'Bildungsgang')
        
        if not bg_trends.empty:
            # Spalten auswählen die existieren
            base_cols = ['Bildungsgang', 'Erste_Bewertung', 'Aktuelle_Bewertung', 'Trend_Change']
            display_cols = [col for col in base_cols if col in bg_trends.columns]
            col_names = ['Bildungsgang', 'Erste Bewertung', 'Aktuelle Bewertung', 'Trend']
            
            # Status-Spalte hinzufügen wenn verfügbar
            if 'Trend_Status' in bg_trends.columns:
                display_cols.append('Trend_Status')
                col_names.append('Entwicklung')
            
            display_df = bg_trends[display_cols].copy()
            display_df.columns = col_names
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    def _render_trend_summary_tables(self, scale_data: pd.DataFrame):
        """Rendert zusammenfassende Trend-Tabellen"""
        st.markdown("### 📋 Trend-Zusammenfassung")
        st.markdown("*Umfassender Überblick aller Trends (nur Antwortskala 1-4)*")
        
        # Verschiedene Trend-Zusammenfassungen
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Top Verbesserungen")
            
            # Beste Verbesserungen auf Themen-Ebene
            if 'Thema' in scale_data.columns:
                theme_trends = self.analyzer.generate_trend_summary_table(scale_data, 'Thema')
                if not theme_trends.empty:
                    improvements = theme_trends[theme_trends['Trend_Change'] > 0.1].head(5)
                    if not improvements.empty:
                        for _, row in improvements.iterrows():
                            st.success(f"📈 **{row['Thema']}**: +{row['Trend_Change']:.2f}")
                    else:
                        st.info("Keine signifikanten Verbesserungen gefunden")
        
        with col2:
            st.markdown("#### ⚠️ Bereiche mit Rückgang")
            
            # Bereiche mit Verschlechterung
            if 'Thema' in scale_data.columns:
                theme_trends = self.analyzer.generate_trend_summary_table(scale_data, 'Thema')
                if not theme_trends.empty:
                    declines = theme_trends[theme_trends['Trend_Change'] < -0.1].head(5)
                    if not declines.empty:
                        for _, row in declines.iterrows():
                            st.error(f"📉 **{row['Thema']}**: {row['Trend_Change']:.2f}")
                    else:
                        st.info("Keine signifikanten Rückgänge gefunden")
        
        # Vollständige Trend-Tabelle
        st.markdown("#### 📊 Vollständige Trend-Übersicht")
        
        if 'Thema' in scale_data.columns:
            all_trends = self.analyzer.generate_trend_summary_table(scale_data, 'Thema')
            if not all_trends.empty:
                st.dataframe(all_trends, use_container_width=True, hide_index=True)
            else:
                st.info("Keine Trend-Daten verfügbar")
    
    def render_timeline_metrics(self, data: pd.DataFrame) -> dict:
        """
        Rendert Timeline-spezifische Metriken
        
        Args:
            data: IQES-Daten
            
        Returns:
            Dictionary mit Timeline-Metriken
        """
        scale_data = self.analyzer.filter_rating_scale_questions(data)
        
        if scale_data.empty:
            return {}
        
        insights = self.analyzer.get_timeline_insights(scale_data)
        
        return {
            'timeline_available': len(scale_data['Datum'].unique()) >= 2,
            'multi_period_questions': insights.get('multi_period_questions', 0),
            'total_periods': insights.get('total_periods', 0),
            'overall_trend_direction': insights.get('overall_trend', {}).get('direction', 'unknown'),
            'scale_questions_count': len(scale_data)
        }