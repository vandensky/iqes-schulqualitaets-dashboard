"""
IQES Themes Configuration
Thematische Zuordnungen und Konfigurationen für IQES-Fragen
"""

# Strategische Themen-Mappings basierend auf IQES-Fragenstruktur
IQES_THEMES = {
    # Schulatmosphäre, Umgang und Unterstützung (5.1-5.5)
    '5.1': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
    '5.2': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
    '5.3': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
    '5.4': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
    '5.5': {'theme': '🏫 Schulatmosphäre', 'color': '#3498db', 'priority': 1, 'strategic': True},
    
    # Unterricht (7.1-7.13)
    '7.1': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.2': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.3': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.4': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.5': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.6': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.7': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.8': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.9': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.10': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.11': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.12': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    '7.13': {'theme': '📚 Unterricht', 'color': '#e74c3c', 'priority': 1, 'strategic': True},
    
    # Feedback und Kommunikation (9.1-9.3)
    '9.1': {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True},
    '9.2': {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True},
    '9.3': {'theme': '💬 Feedback', 'color': '#f39c12', 'priority': 2, 'strategic': True},
}

# Bildungsgang-Konfiguration
BILDUNGSGANG_CONFIG = {
    'BM (Büromanagement)': {
        'color': '#3498db',
        'short': 'BM',
        'icon': '🏢',
        'description': 'Büromanagement'
    },
    'VK (Veranstaltungskaufleute)': {
        'color': '#e74c3c', 
        'short': 'VK',
        'icon': '🎪',
        'description': 'Veranstaltungskaufleute'
    },
    'GK': {
        'color': '#27ae60',
        'short': 'GK', 
        'icon': '🏥',
        'description': 'Gesundheit'
    },
    'IT': {
        'color': '#9b59b6',
        'short': 'IT',
        'icon': '💻', 
        'description': 'Informationstechnik'
    }
}

# IQES-Bewertungsskala
IQES_SCALE = {
    1: {'label': 'trifft nicht zu', 'color': '#e74c3c', 'level': 'kritisch'},
    2: {'label': 'trifft eher nicht zu', 'color': '#f39c12', 'level': 'verbesserungsbedürftig'},
    3: {'label': 'trifft eher zu', 'color': '#f1c40f', 'level': 'akzeptabel'},
    4: {'label': 'trifft zu', 'color': '#27ae60', 'level': 'gut'}
}

# Bewertungs-Kategorien
RATING_CATEGORIES = {
    'kritisch': {'min': 1.0, 'max': 2.5, 'color': '#e74c3c', 'icon': '🚨'},
    'verbesserungsbedürftig': {'min': 2.5, 'max': 3.0, 'color': '#f39c12', 'icon': '⚠️'},
    'gut': {'min': 3.0, 'max': 3.5, 'color': '#f1c40f', 'icon': '👍'},
    'sehr_gut': {'min': 3.5, 'max': 4.0, 'color': '#27ae60', 'icon': '✅'}
}

def get_theme_for_question(question_number: str) -> dict:
    """
    Ermittelt Thema für eine Fragenummer
    
    Args:
        question_number: Fragenummer (z.B. "5.1")
        
    Returns:
        Themen-Dictionary oder Default-Werte
    """
    if question_number in IQES_THEMES:
        return IQES_THEMES[question_number]
    
    # Default für unbekannte Fragen
    return {
        'theme': '❓ Sonstige', 
        'color': '#7f8c8d', 
        'priority': 3, 
        'strategic': False
    }

def get_rating_category(rating: float) -> dict:
    """
    Ermittelt Bewertungskategorie für einen Wert
    
    Args:
        rating: Bewertungswert (1-4)
        
    Returns:
        Kategorie-Dictionary
    """
    for category, config in RATING_CATEGORIES.items():
        if config['min'] <= rating < config['max']:
            return {'category': category, **config}
    
    # Fallback für 4.0
    if rating == 4.0:
        return {'category': 'sehr_gut', **RATING_CATEGORIES['sehr_gut']}
    
    # Default
    return {'category': 'unbekannt', 'color': '#7f8c8d', 'icon': '❓'}

def get_strategic_questions() -> list:
    """
    Gibt Liste aller strategischen Fragen zurück
    
    Returns:
        Liste von Fragennummern
    """
    return [q for q, config in IQES_THEMES.items() if config['strategic']]

def get_theme_summary() -> dict:
    """
    Gibt Zusammenfassung aller Themen zurück
    
    Returns:
        Dictionary mit Themen-Statistiken
    """
    themes = {}
    for question_num, config in IQES_THEMES.items():
        theme_name = config['theme']
        if theme_name not in themes:
            themes[theme_name] = {
                'color': config['color'],
                'priority': config['priority'],
                'questions': [],
                'strategic': config['strategic']
            }
        themes[theme_name]['questions'].append(question_num)
    
    return themes