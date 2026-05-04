import requests
from flask import current_app


def chat_with_ollama(messages):
    base = current_app.config["OLLAMA_BASE_URL"].rstrip("/")
    model = current_app.config["OLLAMA_CHAT_MODEL"]

    try:
        response = requests.post(
            f"{base}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": 200,
                    "temperature": 0.2
                }
            },
            timeout=(5, 60),
        )
        if response.status_code < 400:
            data = response.json()
            answer = data.get("message", {}).get("content", "")
            if answer:
                return answer
    except requests.exceptions.Timeout as e:
        print(f"Chat timeout: {e}")
    except Exception as e:
        print(f"Chat error: {e}")

    return "SERVICE_UNAVAILABLE"


def embed_texts(texts):
    base = current_app.config["OLLAMA_BASE_URL"].rstrip("/")
    model = current_app.config["OLLAMA_EMBED_MODEL"]
    vectors = []

    try:
        response = requests.post(
            f"{base}/api/embed",
            json={
                "model": model,
                "input": texts
            },
            timeout=(5, 30),
        )
        if response.status_code < 400:
            data = response.json()
            embeddings = data.get("embeddings") or []
            if embeddings:
                return embeddings
    except Exception as e:
        print(f"Batch embed endpoint failed: {e}")

    for text in texts:
        try:
            response = requests.post(
                f"{base}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=(5, 20),
            )
            if response.status_code < 400:
                vectors.append(response.json().get("embedding", []))
                continue
        except Exception as e:
            print(f"Embeddings endpoint failed: {e}")

        try:
            response = requests.post(
                f"{base}/api/embed",
                json={"model": model, "input": text},
                timeout=(5, 20),
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings") or []
            vectors.append(embeddings[0] if embeddings else [])
        except Exception as e:
            print(f"Embed endpoint failed for text: {e}")
            vectors.append([])

    return vectors