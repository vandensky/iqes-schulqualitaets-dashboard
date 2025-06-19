"""
IQES Visualizations - Chart-Funktionen
Erstellt interaktive Plotly-Charts für IQES-Daten
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


class IQESVisualizations:
    """Visualisierungsfunktionen für IQES-Daten"""
    
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'danger': '#e74c3c', 
            'warning': '#f39c12',
            'success': '#27ae60',
            'info': '#3498db'
        }
    
    def create_rating_chart(self, data: pd.DataFrame, top_n: int = 5) -> go.Figure:
        """
        Erstellt Chart mit Top 5 beste und Top 5 schlechteste Bewertungen
        
        Args:
            data: IQES-Daten DataFrame
            top_n: Anzahl der besten/schlechtesten Bewertungen (Standard: 5)
            
        Returns:
            Plotly Figure
        """
        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Keine Daten verfügbar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Top 5 beste und Top 5 schlechteste Bewertungen
        best_ratings = data.nlargest(top_n, 'Bewertung').copy()
        worst_ratings = data.nsmallest(top_n, 'Bewertung').copy()
        
        # Kombiniere beide DataFrames
        best_ratings['Kategorie'] = '🟢 Top Bereiche'
        worst_ratings['Kategorie'] = '🔴 Verbesserungsbereiche'
        
        combined_data = pd.concat([worst_ratings, best_ratings])
        
        # Kurze Frage-Labels für bessere Lesbarkeit
        combined_data['Frage_Label'] = combined_data.apply(
            lambda row: f"{row['Fragenummer']} - {row['Frage'][:50]}{'...' if len(row['Frage']) > 50 else ''}",
            axis=1
        )
        
        # Farben basierend auf Kategorie
        color_map = {
            '🔴 Verbesserungsbereiche': '#e74c3c',
            '🟢 Top Bereiche': '#27ae60'
        }
        
        fig = go.Figure()
        
        # Verbesserungsbereiche (rot)
        worst_data = combined_data[combined_data['Kategorie'] == '🔴 Verbesserungsbereiche']
        fig.add_trace(go.Bar(
            x=worst_data['Bewertung'],
            y=worst_data['Frage_Label'],
            orientation='h',
            name='🔴 Verbesserungsbereiche',
            marker_color='#e74c3c',
            hovertemplate='<b>%{y}</b><br>Bewertung: %{x:.2f}<br><extra></extra>'
        ))
        
        # Top Bereiche (grün)
        best_data = combined_data[combined_data['Kategorie'] == '🟢 Top Bereiche']
        fig.add_trace(go.Bar(
            x=best_data['Bewertung'],
            y=best_data['Frage_Label'],
            orientation='h',
            name='🟢 Top Bereiche',
            marker_color='#27ae60',
            hovertemplate='<b>%{y}</b><br>Bewertung: %{x:.2f}<br><extra></extra>'
        ))
        
        fig.update_layout(
            title=f"📊 Top {top_n} Bereiche & Top {top_n} Verbesserungsbereiche",
            height=600,
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Bewertung (1-4 IQES-Skala)",
            yaxis_title="",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Referenzlinien
        fig.add_vline(x=2.5, line_dash="dash", line_color="red", 
                      annotation_text="Kritische Grenze (2.5)")
        fig.add_vline(x=3.0, line_dash="dash", line_color="orange", 
                      annotation_text="Zielwert (3.0)")
        
        return fig
    
    def create_comparison_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        Erstellt Bildungsgang-Vergleichschart
        
        Args:
            data: IQES-Daten DataFrame
            
        Returns:
            Plotly Figure
        """
        if data.empty or len(data['Bildungsgang'].unique()) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Mindestens 2 Bildungsgänge für Vergleich erforderlich",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Durchschnitt pro Bildungsgang
        avg_by_bg = data.groupby('Bildungsgang').agg({
            'Bewertung': 'mean',
            'Frage': 'count'
        }).reset_index()
        avg_by_bg.columns = ['Bildungsgang', 'Durchschnittsbewertung', 'Anzahl_Fragen']
        avg_by_bg['Durchschnittsbewertung'] = avg_by_bg['Durchschnittsbewertung'].round(2)
        
        fig = px.bar(
            avg_by_bg,
            x='Bildungsgang',
            y='Durchschnittsbewertung',
            title="📊 Bewertung nach Bildungsgang",
            color='Durchschnittsbewertung',
            color_continuous_scale='RdYlGn',
            hover_data=['Anzahl_Fragen']
        )
        
        fig.update_layout(
            height=400,
            yaxis_title="Durchschnittsbewertung",
            yaxis_range=[1, 4]
        )
        
        # Ziellinien
        fig.add_hline(y=3.0, line_dash="dash", line_color="green", 
                      annotation_text="Zielwert (3.0)")
        fig.add_hline(y=2.5, line_dash="dash", line_color="orange", 
                      annotation_text="Kritische Grenze (2.5)")
        
        return fig
    
    def create_distribution_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        Erstellt Bewertungsverteilungs-Histogram
        
        Args:
            data: IQES-Daten DataFrame
            
        Returns:
            Plotly Figure
        """
        if data.empty:
            return go.Figure()
        
        fig = px.histogram(
            data,
            x='Bewertung',
            nbins=20,
            title="📈 Verteilung der Bewertungen",
            color_discrete_sequence=[self.colors['info']]
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Bewertung (1-4 IQES-Skala)",
            yaxis_title="Anzahl Fragen",
            xaxis_range=[1, 4]
        )
        
        # Durchschnittslinie
        mean_rating = data['Bewertung'].mean()
        fig.add_vline(x=mean_rating, line_dash="dash", line_color="red",
                      annotation_text=f"Durchschnitt: {mean_rating:.2f}")
        
        return fig
    
    def create_timeline_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        Erstellt Timeline-Chart für Trend-Analyse
        
        Args:
            data: IQES-Daten DataFrame
            
        Returns:
            Plotly Figure
        """
        if data.empty or len(data['Datum'].unique()) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Mindestens 2 Zeitpunkte für Trend-Analyse erforderlich",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Durchschnitt pro Datum und Bildungsgang
        timeline_data = data.groupby(['Datum', 'Bildungsgang'])['Bewertung'].mean().reset_index()
        
        fig = px.line(
            timeline_data,
            x='Datum',
            y='Bewertung',
            color='Bildungsgang',
            title="📅 Bewertungstrend über Zeit",
            markers=True
        )
        
        fig.update_layout(
            height=400,
            yaxis_title="Durchschnittsbewertung",
            yaxis_range=[1, 4],
            xaxis_title="Evaluationszeitraum"
        )
        
        return fig
    
    def create_metrics_cards_data(self, data: pd.DataFrame) -> dict:
        """
        Erstellt Daten für KPI-Metriken
        
        Args:
            data: IQES-Daten DataFrame
            
        Returns:
            Dictionary mit Metrik-Werten
        """
        if data.empty:
            return {}
        
        metrics = {
            'Durchschnittsbewertung': round(data['Bewertung'].mean(), 2),
            'Anzahl_Fragen': len(data),
            'Anzahl_Bildungsgaenge': len(data['Bildungsgang'].unique()),
            'Kritische_Fragen': len(data[data['Bewertung'] < 2.5]),
            'Sehr_gute_Fragen': len(data[data['Bewertung'] >= 3.5]),
            'Beste_Bewertung': round(data['Bewertung'].max(), 2),
            'Schlechteste_Bewertung': round(data['Bewertung'].min(), 2),
            'Evaluationszeitraeume': len(data['Datum'].unique())
        }
        
        return metrics