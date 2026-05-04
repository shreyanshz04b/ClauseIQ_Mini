from .ollama_client import chat_with_ollama
from .guardrails import classify
from ..models import vector_search


def rag_pipeline(query: str) -> dict:
    if not query or len(query.strip()) == 0:
        return {
            'answer': 'Please enter a valid question',
            'classification': 'INVALID_INPUT',
            'contexts': [],
            'citations': [],
            'ok': False
        }

    classification = classify(query)
    if classification == 'UNSAFE':
        return {
            'answer': 'Invalid request. Jailbreak attempts are not allowed.',
            'classification': classification,
            'contexts': [],
            'ok': False
        }

    query_lower = query.lower()

    document_keywords = ['document', 'uploaded', 'deed', 'file', 'tell me', 'what is in', 'analyze', 'summarize', 'about this', 'this document', 'my file', 'contents', 'details of', 'explain this', 'review']

    general_keywords = ['what is', 'explain', 'define', 'section', 'ipc', 'constitution', 'how to', 'procedure', 'law', 'legal', 'rights', 'clause', 'provision']

    nonlegal_keywords = ['cook', 'recipe', 'bake', 'movie', 'actor', 'football', 'weather', 'game', 'music', 'stock', 'programming', 'python', 'javascript', 'hair', 'makeup']

    has_doc_keywords = 0
    for kw in document_keywords:
        if kw in query_lower:
            has_doc_keywords += 1

    has_general_keywords = 0
    for kw in general_keywords:
        if kw in query_lower:
            has_general_keywords += 1

    has_nonlegal_keywords = 0
    for kw in nonlegal_keywords:
        if kw in query_lower:
            has_nonlegal_keywords += 1

    if has_nonlegal_keywords > has_doc_keywords and has_nonlegal_keywords > has_general_keywords:
        intent = "NONLEGAL"
    elif has_doc_keywords > has_general_keywords:
        intent = "DOCUMENT"
    else:
        intent = "GENERAL"

    contexts = []
    try:
        search_results = vector_search(query, limit=5)
        for item in search_results:
            contexts.append(item[0])
    except Exception as e:
        print(f"retrieval error: {e}")
        contexts = []

    if intent == "NONLEGAL":
        return {
            'answer': 'I can only assist with legal matters. Please ask questions related to Indian law, legal documents, or property procedures.',
            'classification': 'NON_LEGAL',
            'contexts': [],
            'citations': [],
            'ok': False
        }

    if intent == "DOCUMENT" and not contexts:
        return {
            'answer': 'No relevant documents found. Please upload the documents you\'d like me to analyze.',
            'classification': 'NO_DOCUMENTS',
            'contexts': [],
            'citations': [],
            'ok': False
        }

    context_lines = []
    idx = 1
    for ctx in contexts[:5]:
        context_lines.append(f"[Document {idx}]\n{ctx}")
        idx += 1
    context_text = "\n\n---\n\n".join(context_lines)

    if intent == "DOCUMENT":
        system_prompt = """You are a professional legal document analyzer. Analyze the provided documents accurately.
CRITICAL RULES:
1. Answer ONLY from the provided documents
2. ALWAYS cite [Document 1], [Document 2], etc. after each fact
3. For summary requests: List all key clauses.
4. For specific questions: Find exact answers in the documents
5. If asking about something not in documents, say: "This information is not in the provided documents."
6. Use format: ...fact here [Document X]..."""

        user_message = f"""Analyze these legal documents carefully.

Documents:
{context_text}

---

User Question: {query}

If asking for summary: provide complete overview of all key information
If asking specific question: find and cite the exact information from documents"""

    else:
        system_prompt = """You are an Indian legal expert. Answer legal questions based on your knowledge.

RULES:
1. For general legal knowledge: use your training knowledge
2. If relevant documents are provided below, cite them: [Document 1]
3. Always cite laws/sources when possible
4. Be accurate about Indian law (IPC, Constitution, property law, etc.)"""

        if contexts:
            user_message = f"""Question: {query}

Relevant documents provided:
{context_text}

Answer the question using your legal knowledge. If relevant info is in the documents, cite them. Otherwise answer from your knowledge."""
        else:
            user_message = f"""Question: {query}

Answer this legal question based on Indian law. Provide accurate information about legal procedures, rights, and regulations."""

    messages = [
        {
            'role': 'system',
            'content': system_prompt
        },
        {
            'role': 'user',
            'content': user_message
        }
    ]

    try:
        answer = chat_with_ollama(messages)
        if not answer or "SERVICE_UNAVAILABLE" in answer:
            answer = "I am currently not able to process your query, kindly try after some time."
    except Exception as e:
        print(f"llm error: {e}")
        answer = "I am having trouble with this question. Please try again or rephrase your query."

    citations = []
    cited_docs = set()

    idx = 0
    while idx<len(answer):
        if answer[idx:idx+9].lower()=='[document' or answer[idx:idx+9].lower()=='document ':
            start=idx
            while idx<len(answer) and answer[idx] not in ']\n':
                idx+=1

            doc_str=answer[start:idx]
            doc_num=""
            for char in doc_str:
                if char.isdigit():
                    doc_num+=char

            if doc_num:
                doc_num_int=int(doc_num)-1
                if 0<=doc_num_int<len(contexts) and doc_num_int not in cited_docs:
                    cited_docs.add(doc_num_int)
                    text=contexts[doc_num_int].strip()

                    if len(text)>200:
                        snippet=text[:200]+"..."
                    else:
                        snippet=text

                    spaces_collapsed=""
                    for char in snippet:
                        if char==' ' or char=='\n' or char=='\t':
                            if not spaces_collapsed or spaces_collapsed[-1]!=' ':
                                spaces_collapsed+=' '
                        else:
                            spaces_collapsed+=char

                    snippet=spaces_collapsed.lstrip('.')
                    citations.append(snippet)
        else:
            idx+=1

    return {
        'answer': answer,
        'classification': 'PROCESSED',
        'contexts': contexts,
        'citations': citations,
        'ok': True
    }

