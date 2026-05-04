from flask import Blueprint, request, jsonify
import re
from ..services.rag import rag_pipeline
from ..services.guardrails import classify

chat_bp = Blueprint("chat", __name__)

def is_valid_query(query: str) -> tuple[bool, str]:
    if not query or len(query.strip()) == 0:
        return False, "Please enter a valid question"
    
    if not re.search(r'[a-zA-Z0-9]', query):
        return False, "Please enter a valid question with meaningful content"
    
    words = query.split()
    if len(words) < 2 and len(query) < 5:
        return False, "Please provide a more detailed question"
    
    return True, ""

def is_greeting(query: str) -> bool:
    greetings=['hello','hi','hey','thanks','thank you','thanks!','thank you!','hi there','hello there','howdy']
    return query.lower().strip() in greetings

@chat_bp.post("/chat")
def chat():
    data=request.get_json(force=True)
    query=(data.get("query") or "").strip()
    
    is_valid, error_msg=is_valid_query(query)
    if not is_valid:
        return jsonify({"error": error_msg, "response": error_msg}), 400

    if is_greeting(query):
        return jsonify({
            "response": "Hello there, i am here to help you with legal quries. Do you like to know something?",
            "classification": "GREETING",
            "citations": [],
            "contexts": []
        })

    response=rag_pipeline(query)
    
    if response['classification']=='NO_DOCUMENTS':
        return jsonify({
            "response": response['answer'],
            "classification": response['classification'],
            "citations": [],
            "error": response['answer']
        }), 400
    if response['classification']=='UNSAFE':
        return jsonify({
            "response": response['answer'],
            "classification": response['classification'],
            "citations": []
        }), 400
    return jsonify({
        "response": response['answer'],
        "classification": response['classification'],
        "citations": response.get('citations', []),
        "contexts": response.get('contexts', [])
    })
