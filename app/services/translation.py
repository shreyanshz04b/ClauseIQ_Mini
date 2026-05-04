import re
from .ollama_client import chat_with_ollama

LEGAL_TERMS_HINDI = {
    "contract": "अनुबंध",
    "agreement": "समझौता",
    "clause": "खंड/शर्त",
    "liability": "देयता/जिम्मेदारी",
    "beneficiary": "लाभार्थी",
    "defendant": "प्रतिवादी",
    "plaintiff": "वादी",
    "jurisdiction": "न्यायक्षेत्र",
    "arbitration": "पंचाट",
    "indemnity": "क्षतिपूर्ति",
    "penalty": "दंड/जुर्माना",
    "provision": "प्रावधान",
    "statute": "विधि/कानून",
    "precedent": "पूर्वनिर्णय",
    "lien": "ग्रहणाधिकार",
    "mortgage": "बंधक",
    "property": "संपत्ति",
    "inheritance": "विरासत/उत्तराधिकार",
    "executor": "सम्पदा प्रशासक",
    "testator": "वसीयतकर्ता",
    "power of attorney": "वकालत नामा",
    "affidavit": "शपथपत्र",
    "deposition": "साक्ष्य कथन",
    "verdict": "निर्णय",
    "bail": "जमानत",
    "custody": "हिरासत",
    "prosecution": "अभियोजन",
    "defense": "बचाव/रक्षा",
    "evidence": "साक्ष्य",
    "witness": "गवाह",
    "oath": "शपथ",
    "perjury": "झूठी गवाही",
    "criminal": "आपराधिक",
    "civil": "नागरिक",
    "tort": "अतिक्रमण/कानूनी हानि",
    "negligence": "लापरवाही",
    "damages": "हर्जाना",
    "breach": "भंग/उल्लंघन",
    "performance": "कार्यान्वयन",
    "termination": "समाप्ति",
    "default": "चूक",
    "consideration": "प्रतिफल",
    "covenant": "प्रतिश्रुति",
    "warranty": "वारंटी/गारंटी",
    "fraud": "धोखाधड़ी",
    "misrepresentation": "गलत प्रतिनिधित्व",
    "duress": "बलात् कार्य",
    "undue influence": "अनुचित प्रभाव",
    "consideration": "प्रतिफल",
    "offer": "प्रस्ताव",
    "acceptance": "स्वीकृति",
    "confidentiality": "गोपनीयता",
    "intellectual property": "बौद्धिक संपत्ति",
    "trademark": "ट्रेडमार्क",
    "patent": "पेटेंट",
    "copyright": "लेखक अधिकार",
    "license": "लाइसेंस",
    "royalty": "रॉयल्टी",
}

def translate_to_hindi(english_text: str) -> dict:
    """Translate legal English to Hindi with simplification"""
    system_prompt = """You are a professional legal translator specializing in converting Indian legal documents from English to Hindi. 

IMPORTANT RULES:
1. Translate legal terms accurately using proper Hindi legal terminology
2. Simplify complex legal language into plain Hindi that students and small business owners can understand
3. Provide both technical and simplified translations
4. Keep the meaning exact - no omissions or additions
5. Format: 
   - ENGLISH: [original text]
   - HINDI (Technical): [proper legal terminology]
   - HINDI (Simple): [easy to understand version]
   - EXPLANATION: [brief explanation in simple Hindi]
"""

    user_message = f"""Translate and simplify this legal English text to Hindi:

TEXT: {english_text}

Provide:
1. Exact Hindi translation using legal terminology
2. Simplified Hindi version for students/business owners
3. Brief explanation of key terms"""

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_message}
    ]

    try:
        translation = chat_with_ollama(messages)
        if not translation:
            translation = "Unable to generate translation. Please try again."
    except Exception as e:
        translation = f"Translation error: {str(e)}"

    return {
        'original': english_text,
        'translation': translation,
        'status': 'success',
        'ok': True
    }

def translate_to_english(hindi_text: str) -> dict:
    """Translate legal Hindi to English"""
    system_prompt = """You are a professional legal translator specializing in converting Indian legal documents from Hindi to English.

IMPORTANT RULES:
1. Translate legal terms accurately using proper English legal terminology
2. Maintain the exact legal meaning - no simplification
3. Format:
   - HINDI: [original text]
   - ENGLISH (Legal): [proper legal terminology]
   - EXPLANATION: [brief explanation]
"""

    user_message = f"""Translate this legal Hindi text to English:

TEXT: {hindi_text}

Provide:
1. Exact English translation using legal terminology
2. Brief explanation of key terms"""

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_message}
    ]

    try:
        translation = chat_with_ollama(messages)
        if not translation:
            translation = "Unable to generate translation. Please try again."
    except Exception as e:
        translation = f"Translation error: {str(e)}"

    return {
        'original': hindi_text,
        'translation': translation,
        'status': 'success',
        'ok': True
    }

def get_legal_glossary(search_term: str = None) -> dict:
    """Get English-Hindi legal glossary"""
    glossary = []
    
    if search_term:
        search_term = search_term.lower().strip()
        for eng, hindi in LEGAL_TERMS_HINDI.items():
            if search_term in eng.lower():
                glossary.append({
                    'english': eng,
                    'hindi': hindi,
                    'category': 'legal_term'
                })
    else:
        for eng, hindi in LEGAL_TERMS_HINDI.items():
            glossary.append({
                'english': eng,
                'hindi': hindi,
                'category': 'legal_term'
            })
    
    return {
        'glossary': glossary,
        'total': len(glossary),
        'ok': True
    }
