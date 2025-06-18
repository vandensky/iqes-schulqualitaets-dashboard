#!/bin/bash

echo "🎓 IQES-Schulqualitäts-Dashboard wird gestartet..."

# Prüfe ob virtuelle Umgebung existiert
if [ ! -d "venv" ]; then
    echo "❌ Virtuelle Umgebung nicht gefunden. Starte Setup..."
    ./setup_venv.sh
    echo ""
fi

# Aktiviere virtuelle Umgebung
echo "🔧 Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Prüfe ob Streamlit installiert ist
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit nicht gefunden. Installiere Abhängigkeiten..."
    pip install streamlit pandas plotly numpy scikit-learn openpyxl openai
fi

echo "🚀 Dashboard wird gestartet..."
echo "📊 Ihr Dashboard öffnet sich automatisch im Browser"
echo "🔑 Für KI-Features (optional): export OPENAI_API_KEY='ihr-api-key'"
echo ""

# Starte das Dashboard
streamlit run dashboard.py --server.address localhost --server.port 8501