# 🎓 IQES-Schulqualitäts-Dashboard

Ein professionelles Dashboard zur Analyse und Visualisierung von IQES-Evaluationsdaten für die Schulentwicklung.

## ✨ Features

- **🔍 IQES-spezifische Datenverarbeitung** - Korrekte Interpretation der 1-4 Bewertungsskala
- **🤖 KI-gestützte Textanalyse** - Deutsche Sentiment-Analyse und OpenAI-Integration
- **📊 Intelligente Visualisierungen** - Zeitverlaufs-Analysen und Bildungsgang-Vergleiche
- **💡 Smart Recommendations** - Automatische Handlungsempfehlungen für kritische Bereiche
- **📈 Multi-Period Analysis** - Vergleich mehrerer Evaluationszeiträume
- **🎯 German-First Design** - Vollständig auf deutsche Bildungseinrichtungen optimiert

## 🚀 Schnellstart

### Lokale Installation
```bash
# 1. Repository klonen
git clone https://github.com/IHR-USERNAME/iqes-dashboard.git
cd iqes-dashboard

# 2. Setup ausführen
chmod +x setup_venv.sh
./setup_venv.sh

# 3. Dashboard starten
source venv/bin/activate
streamlit run dashboard.py
```

### Online Demo
🌐 **Live Dashboard:** [Ihr Streamlit Link]

## 📋 Unterstützte IQES-Dateiformate

- `.xlsx` und `.xls` Excel-Dateien von IQES
- Automatische Erkennung von:
  - **Antwortskala-Fragen** (1-4 Bewertungen)
  - **Offene Fragen** (Textantworten)
  - **Demographische Daten** (Multiple Choice)
  - **Metadaten** (Rücklaufquoten, Teilnehmerzahlen)

## 🎯 Zielgruppen

- **Schulleitung** - Strategische Qualitätsentwicklung
- **Lehrkräfte** - Feedback-Analyse und Verbesserungsmaßnahmen
- **Qualitätsbeauftragte** - Systematische Evaluationsauswertung
- **Bildungsforscher** - Datenanalyse und Trend-Identifikation

## 🔐 Datenschutz

- **Lokale Verarbeitung** - Daten verlassen nicht Ihr System
- **Keine Speicherung** - Hochgeladene Dateien werden nicht gespeichert
- **OpenAI optional** - KI-Features nur bei expliziter API-Key-Eingabe

## 🛠️ Technische Details

- **Framework:** Streamlit (Python)
- **Datenverarbeitung:** Pandas, NumPy
- **Visualisierung:** Plotly, Matplotlib
- **Machine Learning:** Scikit-learn
- **KI-Integration:** OpenAI GPT-3.5-turbo (optional)

## 📖 Dokumentation

- [Installationsanleitung](INSTALLATION.md)
- [Deployment Guide](deployment_guide.md)
- [Entwicklerdokumentation](CLAUDE.md)
- [Verbesserungsübersicht](VERBESSERUNGEN.md)

## 🤝 Beitragen

Verbesserungsvorschläge und Bug-Reports sind willkommen!

## 📄 Lizenz

MIT License - Frei für Bildungseinrichtungen verwendbar

---

**Entwickelt für die digitale Schulentwicklung 🎓**