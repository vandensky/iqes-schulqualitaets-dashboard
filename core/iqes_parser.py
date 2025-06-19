"""
IQES Excel Parser - Core Datenverarbeitung
Extrahiert und verarbeitet IQES-Evaluationsdaten aus Excel-Dateien
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional


class IQESParser:
    """Parser für IQES Excel-Dateien"""
    
    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls']
    
    def extract_date_from_filename(self, filename: str) -> pd.Timestamp:
        """
        Extrahiert Evaluationsdatum aus Dateiname
        
        Args:
            filename: Name der Excel-Datei
            
        Returns:
            Pandas Timestamp des Evaluationsdatums
        """
        date_patterns = [
            r'(\d{4})\.(\d{2})',  # 2024.11
            r'(\d{4})-(\d{2})',   # 2024-11
            r'(\d{4})(\d{2})',    # 202411
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                return pd.to_datetime(f"{year}-{month:02d}-01")
        
        return pd.to_datetime("today")
    
    def determine_bildungsgang(self, filename: str) -> str:
        """
        Bestimmt Bildungsgang aus Dateiname
        
        Args:
            filename: Name der Excel-Datei
            
        Returns:
            Bildungsgang-Bezeichnung
        """
        filename_upper = filename.upper()
        
        if "BM" in filename_upper or "BÜROMANAGEMENT" in filename_upper:
            return "BM (Büromanagement)"
        elif "VK" in filename_upper or "VERANSTALTUNG" in filename_upper:
            return "VK (Veranstaltungskaufleute)"
        elif "GK" in filename_upper:
            return "GK"
        elif "IT" in filename_upper:
            return "IT"
        
        return "Unbekannt"
    
    def determine_evaluation_type(self, filename: str) -> str:
        """
        Bestimmt Evaluationstyp aus Dateiname
        
        Args:
            filename: Name der Excel-Datei
            
        Returns:
            Evaluationstyp
        """
        return "Abschluss" if "Abschluss" in filename else "Zwischenevaluation"
    
    def extract_question_number(self, sheet_name: str) -> str:
        """
        Extrahiert Fragenummer aus Sheet-Name
        
        Args:
            sheet_name: Name des Excel-Sheets
            
        Returns:
            Fragenummer (z.B. "5.1")
        """
        if "Frage" in sheet_name:
            return sheet_name.split("Frage")[1].split("(")[0].strip()
        return ""
    
    def process_rating_scale_sheet(self, df: pd.DataFrame, sheet_name: str, 
                                 eval_date: pd.Timestamp, bildungsgang: str, 
                                 eval_type: str, filename: str) -> List[Dict]:
        """
        Verarbeitet ein Antwortskala-Sheet
        
        Args:
            df: Excel-Sheet als DataFrame
            sheet_name: Name des Sheets
            eval_date: Evaluationsdatum
            bildungsgang: Bildungsgang
            eval_type: Evaluationstyp
            filename: Quelldatei
            
        Returns:
            Liste von Fragen-Dictionaries
        """
        questions = []
        question_num = self.extract_question_number(sheet_name)
        
        # Durch alle Zeilen iterieren (ab Zeile 2, da Zeile 1 meist Header)
        for idx in range(2, len(df)):
            row = df.iloc[idx]
            
            # Frage-Text (Spalte A)
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == "":
                continue
            
            question_text = str(row.iloc[0]).strip()
            
            # Bewertung (Spalte J - Index 9)
            if len(row) > 9 and pd.notna(row.iloc[9]):
                try:
                    rating = float(row.iloc[9])
                    if 1 <= rating <= 4:  # Valide IQES-Bewertung
                        questions.append({
                            'Datum': eval_date,
                            'Bildungsgang': bildungsgang,
                            'Evaluationstyp': eval_type,
                            'Fragenummer': question_num,
                            'Frage': question_text,
                            'Bewertung': rating,
                            'Quelldatei': filename,
                            'Sheet': sheet_name
                        })
                except (ValueError, TypeError):
                    continue
        
        return questions
    
    def parse_excel_file(self, uploaded_file) -> pd.DataFrame:
        """
        Parst eine komplette IQES Excel-Datei
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            DataFrame mit allen extrahierten Fragen
        """
        try:
            # Excel laden
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            
            # Basis-Informationen extrahieren
            eval_date = self.extract_date_from_filename(uploaded_file.name)
            bildungsgang = self.determine_bildungsgang(uploaded_file.name)
            eval_type = self.determine_evaluation_type(uploaded_file.name)
            
            all_questions = []
            
            # Durch alle Sheets iterieren
            for sheet_name, df in excel_data.items():
                if df.empty or "Antwortskala" not in sheet_name:
                    continue
                
                questions = self.process_rating_scale_sheet(
                    df, sheet_name, eval_date, bildungsgang, 
                    eval_type, uploaded_file.name
                )
                all_questions.extend(questions)
            
            return pd.DataFrame(all_questions)
            
        except Exception as e:
            raise Exception(f"Fehler beim Parsen von {uploaded_file.name}: {str(e)}")
    
    def parse_multiple_files(self, uploaded_files) -> pd.DataFrame:
        """
        Parst mehrere IQES Excel-Dateien
        
        Args:
            uploaded_files: Liste von Streamlit uploaded file objects
            
        Returns:
            Kombinierter DataFrame aller Dateien
        """
        all_data = []
        
        for uploaded_file in uploaded_files:
            try:
                data = self.parse_excel_file(uploaded_file)
                if not data.empty:
                    all_data.append(data)
            except Exception as e:
                # Fehler weiterleiten, aber andere Dateien weiter verarbeiten
                raise Exception(f"Fehler in {uploaded_file.name}: {str(e)}")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()