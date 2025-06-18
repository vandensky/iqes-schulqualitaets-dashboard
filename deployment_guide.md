# 🌐 IQES-Dashboard Deployment Guide

## 🆓 **Option 1: Streamlit Community Cloud (Kostenlos)**

### Schritt 1: GitHub Repository vorbereiten
```bash
# Repository erstellen auf github.com
# Dann lokal:
git init
git add dashboard.py requirements.txt CLAUDE.md
git commit -m "Initial IQES Dashboard"
git remote add origin https://github.com/IHR-USERNAME/iqes-dashboard.git
git push -u origin main
```

### Schritt 2: Streamlit Community Cloud
1. Gehen Sie zu: **https://share.streamlit.io/**
2. **Sign in** mit GitHub Account
3. **"New app"** klicken
4. Repository auswählen: `IHR-USERNAME/iqes-dashboard`
5. Main file: `dashboard.py`
6. **Deploy** klicken

### Schritt 3: URL teilen
Sie erhalten eine URL wie: `https://ihr-username-iqes-dashboard-main-dashboard-xyz.streamlit.app/`

---

## 🚀 **Option 2: Hugging Face Spaces (Kostenlos)**

### Vorteile:
- Kostenlos bis 2GB RAM
- Einfaches Setup
- Keine GitHub-Konfiguration nötig

### Setup:
1. **Account auf huggingface.co erstellen**
2. **New Space erstellen**
3. **Streamlit als Framework wählen**
4. **Dateien hochladen**

---

## 💰 **Option 3: Kommerzielle Hosting-Optionen**

### Heroku (Kostenpflichtig)
- **Kosten:** ~$7/Monat für Hobby Plan
- **Vorteile:** Professionell, custom domains

### Railway (Freemium)
- **Kostenlos:** 500 Stunden/Monat
- **Kostenpflichtig:** $5/Monat unlimited

### DigitalOcean App Platform
- **Kosten:** $5/Monat basic plan
- **Vorteile:** Mehr Kontrolle, bessere Performance

---

## 🔐 **Sicherheitsüberlegungen für Schulen**

### Datenschutz:
- **Lokales Hosting** in der Schule (empfohlen für sensible Daten)
- **Private GitHub Repos** für vertraulichen Code
- **Umgebungsvariablen** für API-Keys

### Setup für lokales Schulnetzwerk:
```bash
# Dashboard im Schulnetzwerk verfügbar machen
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
```
Dann erreichbar unter: `http://IHRE-IP:8501`

---

## 📋 **Empfehlung für Ihr IQES-Dashboard**

### Für **öffentliche Demo/Portfolio:**
→ **Streamlit Community Cloud** (kostenlos)

### Für **Schulinternen Einsatz:**
→ **Lokales Hosting** im Schulnetzwerk (datenschutzkonform)

### Für **kommerzielle Nutzung:**
→ **Railway oder DigitalOcean** (professionell)

---

## 🎯 **Nächste Schritte**

1. **GitHub Repository erstellen**
2. **Code uploaden**  
3. **Streamlit Community Cloud deployment**
4. **URL an Kollegen teilen**

Soll ich Ihnen beim GitHub-Setup helfen?