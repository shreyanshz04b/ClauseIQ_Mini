"""
Legal Sections Explorer Routes
Provides APIs for searching, browsing, and explaining legal sections
"""

from flask import Blueprint, request, jsonify
from ..services.legal_explorer_loader import get_loader
from ..services.ollama_client import chat_with_ollama

explorer_bp = Blueprint("explorer", __name__)

@explorer_bp.before_request
def load_sections():
    """Ensure sections are loaded before processing requests"""
    request.loader = get_loader()

@explorer_bp.get("/api/explorer/acts")
def get_all_acts():
    """Get list of all available legal acts"""
    try:
        loader = request.loader
        acts = loader.get_all_acts()
        stats = loader.get_statistics()
        
        return jsonify({
            "ok": True,
            "acts": acts,
            "statistics": stats
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@explorer_bp.get("/api/explorer/search")
def search_sections():
    """Search legal sections
    
    Query parameters:
    - query: search term (required)
    - act: filter by act (optional)
    - limit: max results (default: 20)
    """
    try:
        query = request.args.get('query', '').strip()
        act_filter = request.args.get('act', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not query or len(query) < 2:
            return jsonify({
                "ok": False,
                "error": "Query must be at least 2 characters"
            }), 400
        
        loader = request.loader
        results = loader.search_sections(query, act_filter or None)
        
        # Limit results
        results = results[:limit]
        
        # Convert to response format (exclude full_description for search results)
        search_results = []
        for section in results:
            search_results.append({
                'id': section['id'],
                'section_number': section['section_number'],
                'act_name': section['act_name'],
                'title': section['title'],
                'description': section['description'],
                'category': section['category'],
                'keywords': section['keywords']
            })
        
        return jsonify({
            "ok": True,
            "query": query,
            "act_filter": act_filter,
            "count": len(search_results),
            "results": search_results
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@explorer_bp.get("/api/explorer/section/<section_id>")
def get_section_detail(section_id):
    """Get full details of a specific section"""
    try:
        loader = request.loader
        section = loader.get_section_by_id(section_id)
        
        if not section:
            return jsonify({
                "ok": False,
                "error": f"Section '{section_id}' not found"
            }), 404
        
        return jsonify({
            "ok": True,
            "section": section
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@explorer_bp.get("/api/explorer/act/<act_name>")
def get_sections_by_act(act_name):
    """Get all sections for a specific act
    
    Query parameters:
    - limit: max results (default: 50)
    """
    try:
        limit = int(request.args.get('limit', 50))
        
        loader = request.loader
        sections = loader.get_sections_by_act(act_name)
        
        if not sections:
            return jsonify({
                "ok": False,
                "error": f"Act '{act_name}' not found"
            }), 404
        
        # Limit results
        sections = sections[:limit]
        
        # Convert to response format
        results = []
        for section in sections:
            results.append({
                'id': section['id'],
                'section_number': section['section_number'],
                'title': section['title'],
                'description': section['description'],
                'category': section['category']
            })
        
        return jsonify({
            "ok": True,
            "act": act_name,
            "count": len(results),
            "sections": results
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@explorer_bp.post("/api/explorer/explain")
def explain_section():
    """Get AI explanation of a section
    
    JSON body:
    {
        "section_id": "CPC-1",  # or
        "text": "Section text",  # if section_id not provided
        "style": "simple"  # or "detailed", "example", "importance"
    }
    """
    try:
        data = request.get_json(force=True)
        section_id = data.get('section_id', '').strip()
        text = data.get('text', '').strip()
        style = data.get('style', 'simple').lower()
        
        loader = request.loader
        section = None
        
        # Get section data if ID provided
        if section_id:
            section = loader.get_section_by_id(section_id)
            if not section:
                return jsonify({
                    "ok": False,
                    "error": f"Section '{section_id}' not found"
                }), 404
            text = section['full_description']
            title = section['title']
        elif not text:
            return jsonify({
                "ok": False,
                "error": "Either section_id or text must be provided"
            }), 400
        else:
            title = "Legal Text"
        
        # Prepare explanation prompt based on style
        if style == "simple":
            system_prompt = """You are a legal expert who explains Indian law in simple, easy-to-understand language. 
Explain the given legal text in a way that:
1. A non-lawyer can understand
2. Uses simple everyday examples
3. Avoids jargon
4. Focuses on "what does this mean for me?"
5. Keep it under 200 words"""
            
        elif style == "example":
            system_prompt = """You are a legal expert. For the given legal text, provide:
1. What this law is about (2-3 sentences)
2. A real-life example of when this applies (50-100 words)
3. What you need to know (key points)"""
            
        elif style == "importance":
            system_prompt = """You are a legal expert. For the given legal text, explain:
1. Why is this law important?
2. Who is affected by this law?
3. What are the consequences of violating this?
4. When would you need to know about this?"""
            
        else:  # detailed
            system_prompt = """You are a legal expert. Provide a detailed explanation of the given legal text including:
1. What the law says
2. Key terms and their meanings
3. When it applies
4. Exceptions or special cases
5. Related laws"""
        
        user_message = f"Section: {title}\n\nText:\n{text}"
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]
        
        # Get explanation from Ollama
        explanation = chat_with_ollama(messages)
        
        if not explanation:
            explanation = "Unable to generate explanation. Please try again."
        
        return jsonify({
            "ok": True,
            "section_id": section_id,
            "title": title,
            "style": style,
            "explanation": explanation,
            "source": "AI (Ollama)"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@explorer_bp.post("/api/explorer/explain-hindi")
def explain_section_hindi():
    """Get AI explanation of a section in Hindi
    
    JSON body:
    {
        "section_id": "CPC-1",
        "style": "simple"
    }
    """
    try:
        data = request.get_json(force=True)
        section_id = data.get('section_id', '').strip()
        style = data.get('style', 'simple').lower()
        
        if not section_id:
            return jsonify({
                "ok": False,
                "error": "section_id is required"
            }), 400
        
        loader = request.loader
        section = loader.get_section_by_id(section_id)
        
        if not section:
            return jsonify({
                "ok": False,
                "error": f"Section '{section_id}' not found"
            }), 404
        
        # Prepare Hindi explanation prompt
        system_prompt = """आप एक कानूनी विशेषज्ञ हैं जो भारतीय कानून को सरल, आसान हिंदी में समझाते हैं।
दिए गए कानूनी पाठ को इस तरह समझाएं:
1. सामान्य आदमी समझ सके
2. रोजमर्रा के उदाहरण दें
3. कानूनी शब्दावली से बचें
4. "इसका मेरे लिए क्या मतलब है?" पर ध्यान दें
5. 200 शब्दों से कम रखें"""
        
        text = section['full_description']
        title = section['title']
        
        user_message = f"अनुभाग: {title}\n\nपाठ:\n{text}"
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]
        
        # Get explanation from Ollama
        explanation = chat_with_ollama(messages)
        
        if not explanation:
            explanation = "व्याख्या उत्पन्न नहीं कर सकते। कृपया पुनः प्रयास करें।"
        
        return jsonify({
            "ok": True,
            "section_id": section_id,
            "title": title,
            "language": "Hindi",
            "explanation": explanation,
            "source": "AI (Ollama)"
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
