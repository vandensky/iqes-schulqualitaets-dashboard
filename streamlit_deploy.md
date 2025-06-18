# 🚀 Streamlit Community Cloud Deployment

## 📋 Schritt-für-Schritt Anleitung

### 1. GitHub Repository erstellen
```bash
# Ausführen:
./create_github_repo.sh
```

### 2. GitHub Repository online erstellen
1. Gehen Sie zu: **https://github.com/new**
2. **Repository Name:** `iqes-schulqualitaets-dashboard`
3. **Description:** `🎓 Professionelles Dashboard zur Analyse und Visualisierung von IQES-Evaluationsdaten`
4. **Public** auswählen
5. **"Create repository"** klicken

### 3. Code hochladen
```bash
# Ersetzen Sie IHR-USERNAME mit Ihrem GitHub-Namen:
git remote add origin https://github.com/IHR-USERNAME/iqes-schulqualitaets-dashboard.git
git branch -M main
git push -u origin main
```

### 4. Streamlit Community Cloud Deployment
1. Gehen Sie zu: **https://share.streamlit.io/**
2. **"Sign in with GitHub"**
3. **"New app"** klicken
4. **Repository:** `IHR-USERNAME/iqes-schulqualitaets-dashboard`
5. **Branch:** `main`
6. **Main file path:** `dashboard.py`
7. **"Deploy!"** klicken

### 5. Ihre Dashboard-URL
Nach dem Deployment erhalten Sie eine URL wie:
```
https://ihr-username-iqes-schulqualitaets-dashboard-main-dashboard-abc123.streamlit.app/
```

## 🎯 Ergebnis
- ✅ **Kostenlos gehostet** auf Streamlit Community Cloud
- ✅ **Automatische Updates** bei Code-Änderungen
- ✅ **Professionelle URL** zum Teilen
- ✅ **Anonymisierte IQES-Daten** sicher verarbeitbar

## 🔄 Updates deployen
Nach Änderungen am Code:
```bash
git add .
git commit -m "Update: Neue Features hinzugefügt"
git push
```
→ Streamlit Cloud aktualisiert automatisch!

## 📊 Dashboard-Features für Nutzer
- Upload von IQES-Excel-Dateien
- Automatische Analyse und Visualisierung
- KI-gestützte Handlungsempfehlungen
- Bildungsgang-Vergleiche
- Export-Funktionen