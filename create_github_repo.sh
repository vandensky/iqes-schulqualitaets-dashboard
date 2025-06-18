#!/bin/bash

echo "🎓 IQES-Dashboard GitHub Repository Setup"
echo "========================================="
echo ""

# Repository-Informationen
REPO_NAME="iqes-schulqualitaets-dashboard"
REPO_DESCRIPTION="🎓 Professionelles Dashboard zur Analyse und Visualisierung von IQES-Evaluationsdaten"

echo "📋 Repository wird erstellt: $REPO_NAME"
echo ""

# Git initialisieren
echo "🔧 Git Repository initialisieren..."
git init

# Alle relevanten Dateien hinzufügen
echo "📁 Dateien für Upload vorbereiten..."
git add dashboard.py
git add requirements.txt
git add README.md
git add CLAUDE.md
git add INSTALLATION.md
git add deployment_guide.md
git add VERBESSERUNGEN.md
git add .streamlit/config.toml
git add setup_venv.sh
git add start_dashboard.sh

# .gitignore erstellen
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Streamlit
.streamlit/secrets.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Private data
*.xlsx
*.xls
dashboard_old.py
dashboard_fixed.py
EOF

git add .gitignore

# Commit erstellen
echo "💾 Ersten Commit erstellen..."
git commit -m "🎓 Initial commit: IQES-Schulqualitäts-Dashboard

✨ Features:
- IQES-spezifische Datenverarbeitung (1-4 Skala)
- KI-gestützte deutsche Textanalyse
- Intelligente Handlungsempfehlungen
- Bildungsgang-Vergleiche (BM vs VK)
- Zeitverlaufs-Analysen
- Professional UI für Bildungseinrichtungen

🚀 Ready for Streamlit Community Cloud deployment"

echo ""
echo "✅ Git Repository erfolgreich erstellt!"
echo ""
echo "🌐 Nächste Schritte:"
echo "1. Gehen Sie zu: https://github.com/new"
echo "2. Repository Name: $REPO_NAME"
echo "3. Description: $REPO_DESCRIPTION"
echo "4. Public Repository wählen"
echo "5. 'Create repository' klicken"
echo ""
echo "📤 Dann führen Sie aus:"
echo "git remote add origin https://github.com/IHR-USERNAME/$REPO_NAME.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "🎯 Streamlit Deployment:"
echo "1. Zu https://share.streamlit.io/ gehen"
echo "2. Mit GitHub anmelden"
echo "3. 'New app' erstellen"
echo "4. Repository: IHR-USERNAME/$REPO_NAME"
echo "5. Main file: dashboard.py"
echo "6. Deploy klicken!"