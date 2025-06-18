# 🚀 IQES-Dashboard Installation

## Problem: macOS "externally-managed-environment"
Ihr macOS blockiert die direkte Installation von Python-Paketen. Hier sind 3 Lösungen:

## ✅ **Lösung 1: Automatisches Setup (Empfohlen)**
```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

Dann Dashboard starten:
```bash
source venv/bin/activate
streamlit run dashboard.py
```

## ✅ **Lösung 2: Ein-Klick-Start (Nach Setup)**
```bash
chmod +x start_dashboard.sh
./start_dashboard.sh
```

## ✅ **Lösung 3: Manuelle Installation**
```bash
# 1. Virtuelle Umgebung erstellen
python3 -m venv venv

# 2. Aktivieren
source venv/bin/activate

# 3. Pakete installieren
pip install streamlit pandas plotly numpy scikit-learn openpyxl openai

# 4. Dashboard starten
streamlit run dashboard.py
```

## 🔑 **Optionale KI-Features aktivieren**
Für erweiterte Textanalyse:
```bash
export OPENAI_API_KEY='ihr-openai-api-key'
```

## ⚡ **Schnellstart für die Zukunft**
Nach der ersten Installation:
```bash
source venv/bin/activate
streamlit run dashboard.py
```

## 🆘 **Problemlösung**
Falls Probleme auftreten:
1. Löschen Sie den `venv` Ordner: `rm -rf venv`
2. Führen Sie erneut aus: `./setup_venv.sh`

Das Dashboard öffnet sich automatisch in Ihrem Browser unter `http://localhost:8501`