"""
IQES Timeline Analyzer - Zeitreihenanalyse für IQES-Daten
Spezialisiert auf Antwortskala-Fragen (1-4 Bewertung) und Trend-Analysen
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class IQESTimelineAnalyzer:
    """
    Spezialisierte Klasse für Zeitreihenanalyse von IQES-Evaluationsdaten
    Fokus auf Antwortskala-Fragen (1-4 Bewertung) und Trend-Vergleiche
    """
    
    def __init__(self):
        self.trend_threshold = 0.1  # Schwellenwert für signifikante Trends
        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    
    def filter_rating_scale_questions(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Filtert nur Antwortskala-Fragen (1-4 Bewertung) für Zeitreihenanalyse
        
        Args:
            data: Vollständiger IQES-Datensatz
            
        Returns:
            Gefilterte Daten nur mit Antwortskala-Fragen
        """
        if data.empty:
            return pd.DataFrame()
        
        # Nur Antwortskala-Fragen berücksichtigen
        scale_data = data[data['Fragentyp'] == 'Antwortskala'].copy() if 'Fragentyp' in data.columns else data.copy()
        
        # Zusätzliche Validierung: Bewertung muss zwischen 1-4 liegen
        if 'Bewertung' in scale_data.columns:
            scale_data = scale_data[
                (scale_data['Bewertung'] >= 1) & 
                (scale_data['Bewertung'] <= 4) &
                (scale_data['Bewertung'].notna())
            ]
        
        return scale_data
    
    def identify_multi_period_questions(self, data: pd.DataFrame) -> List[str]:
        """
        Identifiziert Unterfragen, die in mehreren Zeiträumen evaluiert wurden
        
        Args:
            data: IQES-Daten (bereits gefiltert für Antwortskala)
            
        Returns:
            Liste von Unterfragen-Nummern (z.B. "7.1", "7.2") die in ≥2 Zeiträumen vorhanden sind
        """
        if data.empty or 'Fragenummer' not in data.columns or 'Datum' not in data.columns:
            return []
        
        # Gruppiere nach Unterfrage-Nummer (Fragenummer) und zähle einzigartige Zeiträume
        question_timeline = data.groupby(['Fragenummer', 'Datum'])['Bewertung'].mean().reset_index()
        question_counts = question_timeline.groupby('Fragenummer')['Datum'].count()
        
        # Nur Unterfragen mit mindestens 2 Zeiträumen
        multi_period_questions = question_counts[question_counts >= 2].index.tolist()
        
        return multi_period_questions
    
    def calculate_trend_metrics(self, data: pd.DataFrame, group_by: str) -> pd.DataFrame:
        """
        Berechnet Trend-Metriken für gegebene Gruppierung
        
        Args:
            data: Zeitreihen-Daten
            group_by: Gruppierungs-Spalte ('Fragenummer', 'Thema', etc.)
            
        Returns:
            DataFrame mit Trend-Metriken
        """
        if data.empty or group_by not in data.columns:
            return pd.DataFrame()
        
        timeline_data = data.groupby([group_by, 'Datum'])['Bewertung'].mean().reset_index()
        trend_results = []
        
        for group_value in timeline_data[group_by].unique():
            group_data = timeline_data[timeline_data[group_by] == group_value].sort_values('Datum')
            
            if len(group_data) >= 2:
                first_val = group_data.iloc[0]['Bewertung']
                latest_val = group_data.iloc[-1]['Bewertung']
                trend_change = latest_val - first_val
                
                # Trend-Klassifikation
                if trend_change > self.trend_threshold:
                    trend_status = "📈 Verbessert"
                    trend_icon = "📈"
                elif trend_change < -self.trend_threshold:
                    trend_status = "📉 Verschlechtert"
                    trend_icon = "📉"
                else:
                    trend_status = "➡️ Stabil"
                    trend_icon = "➡️"
                
                trend_results.append({
                    group_by: group_value,
                    'Erste_Bewertung': round(first_val, 2),
                    'Aktuelle_Bewertung': round(latest_val, 2),
                    'Trend_Change': round(trend_change, 2),
                    'Trend_Status': trend_status,
                    'Trend_Icon': trend_icon,
                    'Anzahl_Zeitraeume': len(group_data),
                    'Zeitspanne': f"{group_data.iloc[0]['Datum'].strftime('%Y-%m')} bis {group_data.iloc[-1]['Datum'].strftime('%Y-%m')}"
                })
        
        return pd.DataFrame(trend_results)
    
    def create_thematic_timeline_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        Erstellt thematischen Timeline-Chart für Antwortskala-Fragen
        
        Args:
            data: Gefilterte IQES-Daten mit Themen-Zuordnung
            
        Returns:
            Plotly Figure für thematische Zeitreihen
        """
        if data.empty or 'Thema' not in data.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="Keine thematischen Daten für Timeline verfügbar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Thematische Timeline erstellen
        theme_timeline = data.groupby(['Thema', 'Datum']).agg({
            'Bewertung': 'mean',
            'Thema_Farbe': 'first'
        }).reset_index()
        
        # Trend-Metriken berechnen
        trend_metrics = self.calculate_trend_metrics(data, 'Thema')
        
        fig = go.Figure()
        
        # Für jedes Thema eine Linie hinzufügen
        for theme in theme_timeline['Thema'].unique():
            theme_data = theme_timeline[theme_timeline['Thema'] == theme].sort_values('Datum')
            
            if len(theme_data) > 0:
                # Trend-Icon aus Metriken holen
                trend_icon = ""
                if not trend_metrics.empty:
                    theme_trend = trend_metrics[trend_metrics['Thema'] == theme]
                    if not theme_trend.empty:
                        trend_icon = f" {theme_trend.iloc[0]['Trend_Icon']}"
                
                theme_color = theme_data.iloc[0]['Thema_Farbe'] if 'Thema_Farbe' in theme_data.columns else '#1f77b4'
                
                fig.add_trace(go.Scatter(
                    x=theme_data['Datum'],
                    y=theme_data['Bewertung'],
                    mode='lines+markers',
                    name=f"{theme}{trend_icon}",
                    line=dict(width=4, color=theme_color),
                    marker=dict(size=10, color=theme_color),
                    hovertemplate=f'<b>{theme}</b><br>' +
                                 'Datum: %{x}<br>' +
                                 'Durchschnitt: %{y:.2f}<br>' +
                                 '<extra></extra>'
                ))
        
        fig.update_layout(
            title="🎯 Thematische Entwicklung über Zeit (nur Antwortskala 1-4)",
            xaxis_title="Evaluationszeitraum",
            yaxis_title="Durchschnittsbewertung (1-4 IQES-Skala)",
            yaxis=dict(range=[1, 4]),
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        # Referenzlinien hinzufügen
        fig.add_hline(y=3.0, line_dash="dash", line_color="green", 
                      annotation_text="Zielwert (3.0)")
        fig.add_hline(y=2.5, line_dash="dash", line_color="orange", 
                      annotation_text="Kritische Grenze (2.5)")
        
        return fig
    
    def create_individual_questions_timeline(self, data: pd.DataFrame, 
                                           selected_questions: List[str] = None, 
                                           max_questions: int = 10) -> go.Figure:
        """
        Erstellt Timeline für individuelle Fragen
        
        Args:
            data: Gefilterte IQES-Daten 
            selected_questions: Liste ausgewählter Fragennummern
            max_questions: Maximum anzuzeigende Fragen
            
        Returns:
            Plotly Figure für Einzelfragen-Timeline
        """
        if data.empty:
            return go.Figure()
        
        # Multi-Period-Fragen identifizieren
        multi_period_questions = self.identify_multi_period_questions(data)
        
        if not multi_period_questions:
            fig = go.Figure()
            fig.add_annotation(
                text="Keine Fragen in mehreren Zeiträumen verfügbar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Fragenauswahl
        if selected_questions:
            questions_to_show = [q for q in selected_questions if q in multi_period_questions][:max_questions]
        else:
            questions_to_show = multi_period_questions[:max_questions]
        
        if not questions_to_show:
            return go.Figure()
        
        # Timeline-Daten erstellen
        question_timeline = data.groupby(['Fragenummer', 'Datum'])['Bewertung'].mean().reset_index()
        
        fig = go.Figure()
        
        for i, question_num in enumerate(questions_to_show):
            question_data = question_timeline[question_timeline['Fragenummer'] == question_num].sort_values('Datum')
            
            # Trend berechnen
            trend_icon = "➡️"
            if len(question_data) >= 2:
                latest_val = question_data.iloc[-1]['Bewertung']
                first_val = question_data.iloc[0]['Bewertung']
                trend_change = latest_val - first_val
                
                if trend_change > self.trend_threshold:
                    trend_icon = "📈"
                elif trend_change < -self.trend_threshold:
                    trend_icon = "📉"
            
            color = self.colors[i % len(self.colors)]
            
            fig.add_trace(go.Scatter(
                x=question_data['Datum'],
                y=question_data['Bewertung'],
                mode='lines+markers',
                name=f"{trend_icon} Frage {question_num}",
                line=dict(width=3, color=color),
                marker=dict(size=8),
                hovertemplate=f'<b>Frage {question_num}</b><br>' +
                             'Datum: %{x}<br>' +
                             'Bewertung: %{y:.2f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title="📈 Einzelfragen-Trends über Zeit (nur Antwortskala 1-4)",
            xaxis_title="Evaluationszeitraum",
            yaxis_title="Bewertung (1-4 IQES-Skala)",
            yaxis=dict(range=[1, 4]),
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        # Referenzlinien
        fig.add_hline(y=3.0, line_dash="dash", line_color="green", 
                      annotation_text="Zielwert (3.0)")
        fig.add_hline(y=2.5, line_dash="dash", line_color="orange", 
                      annotation_text="Kritische Grenze (2.5)")
        
        return fig
    
    def create_bildungsgang_timeline(self, data: pd.DataFrame) -> go.Figure:
        """
        Erstellt Timeline-Vergleich zwischen Bildungsgängen
        
        Args:
            data: Gefilterte IQES-Daten
            
        Returns:
            Plotly Figure für Bildungsgang-Timeline
        """
        if data.empty or 'Bildungsgang' not in data.columns:
            return go.Figure()
        
        if len(data['Bildungsgang'].unique()) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Mindestens 2 Bildungsgänge für Vergleich erforderlich",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Timeline pro Bildungsgang
        bg_timeline = data.groupby(['Bildungsgang', 'Datum'])['Bewertung'].mean().reset_index()
        
        fig = px.line(
            bg_timeline,
            x='Datum',
            y='Bewertung',
            color='Bildungsgang',
            title="📊 Bildungsgang-Vergleich über Zeit (nur Antwortskala 1-4)",
            markers=True,
            color_discrete_sequence=['#3498db', '#e74c3c', '#27ae60', '#9b59b6']
        )
        
        fig.update_layout(
            height=400,
            yaxis_title="Durchschnittsbewertung (1-4 IQES-Skala)",
            yaxis_range=[1, 4],
            xaxis_title="Evaluationszeitraum",
            template='plotly_white'
        )
        
        # Referenzlinien
        fig.add_hline(y=3.0, line_dash="dash", line_color="green", 
                      annotation_text="Zielwert (3.0)")
        fig.add_hline(y=2.5, line_dash="dash", line_color="orange", 
                      annotation_text="Kritische Grenze (2.5)")
        
        return fig
    
    def generate_trend_summary_table(self, data: pd.DataFrame, group_by: str = 'Thema') -> pd.DataFrame:
        """
        Generiert zusammenfassende Trend-Tabelle
        
        Args:
            data: Gefilterte IQES-Daten
            group_by: Gruppierungs-Kriterium ('Thema', 'Fragenummer', 'Bildungsgang')
            
        Returns:
            DataFrame mit Trend-Zusammenfassung
        """
        if data.empty or group_by not in data.columns:
            return pd.DataFrame()
        
        trend_metrics = self.calculate_trend_metrics(data, group_by)
        
        if trend_metrics.empty:
            return pd.DataFrame()
        
        # Sortiere nach Trend (beste Verbesserungen zuerst)
        trend_metrics = trend_metrics.sort_values('Trend_Change', ascending=False)
        
        # Bereiche mit Fragenanzahl anreichern wenn möglich
        if group_by == 'Thema' and 'Fragenummer' in data.columns:
            question_counts = data.groupby('Thema')['Fragenummer'].nunique().reset_index()
            question_counts.columns = ['Thema', 'Anzahl_Fragen']
            trend_metrics = trend_metrics.merge(question_counts, on='Thema', how='left')
        
        return trend_metrics
    
    def get_timeline_insights(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        Generiert automatische Insights aus Timeline-Daten
        
        Args:
            data: Gefilterte IQES-Daten (nur Antwortskala)
            
        Returns:
            Dictionary mit Key-Insights
        """
        if data.empty:
            return {}
        
        insights = {
            'total_questions': len(data['Fragenummer'].unique()) if 'Fragenummer' in data.columns else 0,
            'total_periods': len(data['Datum'].unique()) if 'Datum' in data.columns else 0,
            'multi_period_questions': len(self.identify_multi_period_questions(data)),
            'overall_trend': None,
            'best_improving_theme': None,
            'worst_declining_theme': None,
            'stable_themes': []
        }
        
        # Thematische Trends analysieren
        if 'Thema' in data.columns:
            theme_trends = self.calculate_trend_metrics(data, 'Thema')
            if not theme_trends.empty:
                # Beste Verbesserung
                best_improvement = theme_trends.loc[theme_trends['Trend_Change'].idxmax()]
                insights['best_improving_theme'] = {
                    'name': best_improvement['Thema'],
                    'change': best_improvement['Trend_Change']
                }
                
                # Stärkster Rückgang
                worst_decline = theme_trends.loc[theme_trends['Trend_Change'].idxmin()]
                insights['worst_declining_theme'] = {
                    'name': worst_decline['Thema'],
                    'change': worst_decline['Trend_Change']
                }
                
                # Stabile Bereiche
                stable = theme_trends[
                    (theme_trends['Trend_Change'] >= -self.trend_threshold) & 
                    (theme_trends['Trend_Change'] <= self.trend_threshold)
                ]
                insights['stable_themes'] = stable['Thema'].tolist()
        
        # Gesamttrend berechnen
        if len(data['Datum'].unique()) >= 2:
            overall_timeline = data.groupby('Datum')['Bewertung'].mean().reset_index().sort_values('Datum')
            if len(overall_timeline) >= 2:
                overall_change = overall_timeline.iloc[-1]['Bewertung'] - overall_timeline.iloc[0]['Bewertung']
                insights['overall_trend'] = {
                    'change': round(overall_change, 2),
                    'direction': 'improving' if overall_change > self.trend_threshold else 'declining' if overall_change < -self.trend_threshold else 'stable'
                }
        
        return insights