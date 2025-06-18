#!/bin/bash

echo "🚀 Installation der IQES-Dashboard Abhängigkeiten..."

# Erstelle requirements.txt wenn nicht vorhanden
cat > requirements.txt << EOF
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
numpy>=1.24.0
scikit-learn>=1.3.0
textblob>=0.17.0
seaborn>=0.12.0
matplotlib>=3.7.0
wordcloud>=1.9.0
openpyxl>=3.1.0
openai>=1.0.0
EOF

echo "📦 Installiere Python-Pakete..."
pip3 install -r requirements.txt

echo "✅ Installation abgeschlossen!"
echo ""
echo "🎯 Starten Sie das Dashboard mit:"
echo "streamlit run dashboard_fixed.py"
echo ""
echo "🔑 Für KI-Features (optional) setzen Sie:"
echo "export OPENAI_API_KEY='ihr-api-key'"