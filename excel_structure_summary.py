#!/usr/bin/env python3
"""
IQES Excel File Structure Analysis Summary
==========================================

Based on analysis of multiple IQES evaluation Excel files from different time periods and programs (BM/VK).

Key Findings:
"""

STRUCTURE_SUMMARY = """
IQES EXCEL FILE STRUCTURE ANALYSIS
==================================

1. SHEET ORGANIZATION:
   - All files follow consistent pattern with 15 sheets
   - Sheet naming: 'Frage X (Type)' where Type is:
     * Einfachauswahl: Multiple choice questions
     * Antwortskala: Rating scale questions (1-4 scale)
     * Offene Frage: Open text questions
   - Always starts with 'Allgemeine Angaben' (General Information)

2. SHEET TYPES AND PATTERNS:

   A) ALLGEMEINE ANGABEN (General Information):
      - Key-value pairs in 2 columns
      - Column 1: Description (German)
      - Column 2: Value
      - Contains:
        * Abschlussdatum der Befragung: Survey completion date (ISO format)
        * Verwendeter Fragebogen: Questionnaire name
        * Total eingeladene Befragte: Total invited participants (integer)
        * Vollständig beantwortete Fragebogen: Completed responses (integer)
        * Rücklaufquote: Response rate (percentage as decimal)

   B) EINFACHAUSWAHL (Multiple Choice):
      - 3 columns structure:
        * Column 1: Question text (header) + numeric codes (1.0, 2.0, etc.)
        * Column 2: Answer options text (NaN in header row)
        * Column 3: Response counts (NaN in header row)
      - Bottom rows contain metadata: N= (total), KA= (no answer)

   C) ANTWORTSKALA (Rating Scale):
      - 13 columns structure:
        * Column 1: Question category/topic
        * Column 2: "Qualitätseinschätzung" (Quality Assessment)
        * Columns 3-12: Rating scale data
        * Columns 11-13: N=, KA=, SA= (metadata)
      - Row structure:
        * Row 0: Headers ("trifft nicht zu", "trifft eher nicht zu", etc.)
        * Row 1: Scale numbers (1, 2, 3, 4) and percentages
        * Row 2+: Individual questions with response data
      - Rating scale: 1=trifft nicht zu, 2=trifft eher nicht zu, 3=trifft eher zu, 4=trifft zu
      - Data includes both counts and percentages
      - Durchschnittswerte (average values) in column 9

   D) OFFENE FRAGE (Open Questions):
      - 2 columns:
        * Column 1: Question text/numbering
        * Column 2: Response text
      - First row: participation summary ("Diese Frage haben X von Y Teilnehmenden beantwortet")
      - Numbered responses (1, 2, 3, etc.) with actual text answers

3. DATA EXTRACTION PATTERNS:

   For Rating Scale Questions:
   - Question text: Column 1, rows 2+ (format: "X.Y - Question text")
   - Average rating: Column 9 ("Durchschnittswerte")
   - Response count: Column 10 ("N=")
   - No answers: Column 11 ("KA=")
   - Individual rating counts: Columns 2, 4, 6, 8 (values 1-4)
   - Individual rating percentages: Columns 3, 5, 7, 9

   For Multiple Choice:
   - Question text: Column 1 header
   - Options: Column 2, rows with text
   - Counts: Column 3, corresponding rows

   For Open Questions:
   - Question text: Column 1 header
   - Responses: Column 2, rows 2+ (excluding summary row)

4. METADATA LOCATIONS:
   - Survey dates: 'Allgemeine Angaben' sheet
   - Participant counts: 'Allgemeine Angaben' sheet
   - Response rates: 'Allgemeine Angaben' sheet
   - Question-level response counts: Last columns of each question sheet

5. PROGRAM IDENTIFICATION:
   - BM files: "Büromanagement" program
   - VK files: "Veranstaltungskaufleute" program
   - Program name appears in sheet headers and file names

6. TIME PERIOD IDENTIFICATION:
   - Date format: YYYY-MM in file names (e.g., "2024.04", "2025.04")
   - Exact completion dates in 'Allgemeine Angaben' sheet (ISO format)

7. CONSISTENT QUESTION CATEGORIES:
   - Frage 1-4: Demographics/background (Einfachauswahl)
   - Frage 5: School atmosphere (Antwortskala)
   - Frage 6: Open feedback on atmosphere (Offene Frage)
   - Frage 7: Teaching/instruction (Antwortskala)
   - Frage 8: Open feedback on teaching (Offene Frage)
   - Frage 9-12: Various rating categories (Antwortskala)
   - Frage 13-14: Open questions (Offene Frage)
"""

def print_structure_analysis():
    """Print the complete structure analysis"""
    print(STRUCTURE_SUMMARY)
    
    print("\nRECOMMENDED DATA PROCESSING APPROACH:")
    print("=====================================")
    print("1. Extract metadata from 'Allgemeine Angaben' sheet")
    print("2. Process rating scale sheets for quantitative data")
    print("3. Extract open question responses for qualitative analysis")
    print("4. Use consistent column positions for reliable data extraction")
    print("5. Handle NaN values appropriately in each sheet type")
    print("\nSpecific column mappings for rating scales:")
    print("- Questions: Column 0 (rows 2+)")
    print("- Averages: Column 9")
    print("- Response counts: Column 10")
    print("- Rating 1 count: Column 1, percentage: Column 2")
    print("- Rating 2 count: Column 3, percentage: Column 4")
    print("- Rating 3 count: Column 5, percentage: Column 6")
    print("- Rating 4 count: Column 7, percentage: Column 8")

if __name__ == "__main__":
    print_structure_analysis()