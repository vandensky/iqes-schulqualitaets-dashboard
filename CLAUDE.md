# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a professional German educational evaluation dashboard application built with Streamlit for analyzing IQES (Instrumente für die Qualitätsentwicklung und Evaluation an Schulen) school quality data. The application has been completely rewritten to properly handle IQES-specific data structures and provides AI-powered insights for school development.

## Key Application Architecture

### Main Components

1. **SchulqualitätsDashboard** (`dashboard.py:109`): Main dashboard class with IQES-specific data processing
2. **KI_Schulqualitäts_Analyzer** (`dashboard.py:492`): AI-powered analysis class with German text processing and OpenAI integration

### IQES-Specific Data Processing

The dashboard correctly processes the standard IQES Excel structure:
- **Antwortskala sheets**: 4-point Likert scale questions (1="trifft nicht zu" to 4="trifft zu")
- **Offene Frage sheets**: Open-ended text responses with German sentiment analysis
- **Einfachauswahl sheets**: Multiple choice demographic questions
- **Allgemeine Angaben**: Metadata extraction (response rates, completion dates)

### Core Features

- **IQES-Compliant Data Extraction**: Proper parsing of column J (averages) and K (N values)
- **German Text Analysis**: Sentiment analysis with German keywords and OpenAI integration
- **Intelligent Recommendations**: AI-generated action items based on critical areas
- **Multi-Program Comparison**: BM (Büromanagement) vs VK (Veranstaltungskaufleute) analysis
- **Temporal Trend Analysis**: Multi-period evaluation comparison

## Running the Application

### Quick Start
```bash
chmod +x start_dashboard.sh
./start_dashboard.sh
```

### Manual Setup
```bash
# Install dependencies
./install_requirements.sh

# Start dashboard
streamlit run dashboard.py
```

### Optional: Enable AI Features
```bash
export OPENAI_API_KEY='your-api-key'
streamlit run dashboard.py
```

## Key Dependencies

- streamlit>=1.28.0 (web framework)
- pandas>=1.5.0 (IQES data processing)
- plotly>=5.15.0 (interactive visualizations)
- scikit-learn>=1.3.0 (ML clustering)
- openai>=1.0.0 (German text analysis, optional)
- openpyxl>=3.1.0 (Excel file processing)

## IQES Data Structure Support

### Expected File Structure
- BM evaluation files: `*BM*.xlsx` containing Büromanagement evaluations
- VK evaluation files: `*VK*.xlsx` containing Veranstaltungskaufleute evaluations
- Sheet names: "Frage X (Antwortskala)", "Frage Y (Offene Frage)", "Allgemeine Angaben"

### Data Processing Logic
- Column A: German question text
- Column J: Pre-calculated averages (primary metric)
- Column K: Response count (N values)
- Columns B,D,F,H: Response distribution counts
- Scale: 1-4 where <2.5 = high improvement need, <3.0 = medium, ≥3.0 = low

## AI-Powered Features

### German Text Analysis
- Sentiment analysis using German positive/negative word dictionaries
- Keyword extraction with German stopword filtering
- OpenAI integration for advanced insights and recommendations

### Smart Recommendations
- Critical question identification (scores <2.5)
- Program comparison analysis (BM vs VK performance gaps)
- Negative sentiment detection in open responses
- Timeline-based priority assignment

## Development Notes

- Application is fully German-localized for educational institutions
- Handles real IQES Excel export formats with proper column mapping
- Includes error handling for malformed IQES files
- CSS styling optimized for professional educational reporting
- Modular design allows easy extension for additional analysis types