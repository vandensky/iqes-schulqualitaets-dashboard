# 📊 IQES EXCEL-STRUKTUR ANALYSE

## 🎯 KORREKTE DATENSTRUKTUR

### 📋 Sheet-Aufbau
```
Sheet-Name: "Frage X (Antwortskala)"
├── Spalte A (Index 0): Fragen-Texte  
├── Spalte J (Index 9): Durchschnittsbewertungen (1-4)
└── Spalten-Header[0]: THEMA-NAME
```

### 📊 THEMENBEREICHE UND FRAGEN

| Fragenummer | Themenbereich | Anzahl Unterfragen | Beispiel-Unterfragen |
|-------------|---------------|--------------------|-----------------------|
| **5** | Schulatmosphäre, Umgang und Unterstützung | 5 | 5.1, 5.2, 5.3, 5.4, 5.5 |
| **7** | Unterricht | 13 | 7.1, 7.2, 7.3, ..., 7.13 |  
| **9** | Feedback | 3 | 9.1, 9.2, 9.3 |
| **10** | Ideen-/Beschwerdemanagement | 4 | 10.1, 10.2, 10.3, 10.4 |
| **11** | Stärken und Schwächen der Schule | 9 | 11.1, 11.2, ..., 11.9 |
| **12** | Zufriedenheit | 3 | 12.1, 12.2, 12.3 |

### 🔍 DETAILSTRUKTUR BEISPIEL: "Frage 7 (Antwortskala)"

```
Columns: ['Unterricht', 'Qualitätseinschätzung', 'Unnamed: 2', ...]
                    ↑
               THEMA-NAME (df.columns[0])

Zeile 0: A=NaN              J='Durchschnittswerte'
Zeile 1: A=NaN              J=NaN  
Zeile 2: A='7.1 - Die Unterrichtseinheiten...'  J=3.06  ← ERSTE UNTERFRAGE
Zeile 3: A='7.2 - Zu Beginn einer...'           J=2.91  ← ZWEITE UNTERFRAGE
...
Zeile 14: A='7.13 - Die Leistungsbeurteilung...' J=3.0  ← LETZTE UNTERFRAGE
```

### 🎯 KORREKTE EXTRAKTIONS-STRATEGIE

#### 1. **Thema extrahieren**
```python
thema = df.columns[0]  # Erster Spalten-Header
# Beispiel: "Schulatmosphäre, Umgang und Unterstützung"
```

#### 2. **Fragenummer extrahieren** 
```python
if "Frage" in sheet_name:
    fragenummer = sheet_name.split("Frage")[1].split("(")[0].strip()
# Beispiel: "Frage 7 (Antwortskala)" → "7"
```

#### 3. **Einzelfragen extrahieren**
```python
for idx in range(2, len(df)):  # Ab Zeile 2
    frage_text = df.iloc[idx, 0]  # Spalte A
    bewertung = df.iloc[idx, 9]   # Spalte J
    
    # Unterfrage-Nummer aus Text extrahieren
    if frage_text.startswith(f"{fragenummer}."):
        unterfrage_nr = frage_text.split(" - ")[0]  # z.B. "7.1"
```

## ❌ MEIN BISHERIGER FEHLER

**Falsch interpretiert:**
- Thema aus A1 extrahieren → **A1 ist NaN!**
- Erste Frage als Thema verwenden → **Das ist eine Unterfrage!**

**Korrekt:**
- **Thema** = `df.columns[0]` (Spalten-Header)
- **Fragenummer** = aus Sheet-Name 
- **Unterfragen** = 7.1, 7.2, 7.3 etc. aus Spalte A ab Zeile 2

## 🎯 ZIEL DER TIMELINE-ANALYSE

### Themenvergleich über Zeit:
```
Thema "Unterricht" (Frage 7):
├── 2023.11: Ø 2.95 (Durchschnitt aller 7.x Fragen)
├── 2024.05: Ø 3.02 
└── 2024.11: Ø 3.01
```

### Einzelfragen-Vergleich:
```
Frage 7.1 "Unterrichtseinheiten orientieren sich...":
├── 2023.11: 2.89
├── 2024.05: 3.05  
└── 2024.11: 3.06
```

## ✅ IMPLEMENTIERUNGS-PLAN

1. **Parser anpassen**: Thema aus `df.columns[0]` extrahieren
2. **Fragenummer**: Aus Sheet-Name korrekt parsen  
3. **Unterfragen**: Format "X.Y - Text" korrekt behandeln
4. **Timeline**: Sowohl Themen-Level als auch Einzelfragen-Level
5. **Aggregation**: Themen-Durchschnitt aus allen X.Y Unterfragen berechnen

## 🚨 KRITISCHE ERKENNTNISSE

- **Ein Themenbereich** = Ein Sheet (z.B. "Unterricht" aus Frage 7)
- **Unterfragen** = 7.1, 7.2, ..., 7.13 innerhalb dieses Themas
- **Timeline-Vergleich** auf beiden Ebenen: Themen UND Einzelfragen
- **Bewertungen** immer in Spalte J (Index 9)