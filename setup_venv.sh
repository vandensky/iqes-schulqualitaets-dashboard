#!/bin/bash

echo "🎓 IQES-Dashboard Setup mit virtueller Umgebung..."
echo ""

# Erstelle virtuelle Umgebung
if [ ! -d "venv" ]; then
    echo "📦 Erstelle virtuelle Python-Umgebung..."
    python3 -m venv venv
    echo "✅ Virtuelle Umgebung erstellt"
else
    echo "✅ Virtuelle Umgebung bereits vorhanden"
fi

# Aktiviere virtuelle Umgebung
echo "🔧 Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Update pip..."
pip install --upgrade pip

# Installiere Pakete
echo "📦 Installiere IQES-Dashboard Abhängigkeiten..."
pip install streamlit>=1.28.0
pip install pandas>=1.5.0
pip install plotly>=5.15.0
pip install numpy>=1.24.0
pip install scikit-learn>=1.3.0
pip install textblob>=0.17.0
pip install seaborn>=0.12.0
pip install matplotlib>=3.7.0
pip install wordcloud>=1.9.0
pip install openpyxl>=3.1.0
pip install openai>=1.0.0

echo ""
echo "✅ Installation erfolgreich abgeschlossen!"
echo ""
echo "🚀 Dashboard starten:"
echo "source venv/bin/activate"
echo "streamlit run dashboard.py"
echo ""
echo "🔑 Für KI-Features (optional):"
echo "export OPENAI_API_KEY='ihr-api-key'"