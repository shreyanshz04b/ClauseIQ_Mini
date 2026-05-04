from flask import Blueprint, request, jsonify
from ..services.translation import translate_to_hindi, translate_to_english, get_legal_glossary

translation_bp = Blueprint("translation", __name__)

@translation_bp.post("/translate/to-hindi")
def translate_to_hindi_route():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    
    if not text or len(text) < 3:
        return jsonify({"error": "Please provide valid text to translate (minimum 3 characters)"}), 400
    
    if len(text) > 5000:
        return jsonify({"error": "Text exceeds maximum limit of 5000 characters"}), 400
    
    result = translate_to_hindi(text)
    return jsonify(result)

@translation_bp.post("/translate/to-english")
def translate_to_english_route():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    
    if not text or len(text) < 3:
        return jsonify({"error": "Please provide valid text to translate (minimum 3 characters)"}), 400
    
    if len(text) > 5000:
        return jsonify({"error": "Text exceeds maximum limit of 5000 characters"}), 400
    
    result = translate_to_english(text)
    return jsonify(result)

@translation_bp.get("/glossary")
def glossary_route():
    search_term = request.args.get("search", "").strip()
    result = get_legal_glossary(search_term if search_term else None)
    return jsonify(result)

@translation_bp.get("/glossary/<term>")
def glossary_search_route(term):
    result = get_legal_glossary(term)
    return jsonify(result)
