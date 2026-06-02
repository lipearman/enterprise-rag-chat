from _common import call_ollama, clean_text
import sys

def rewrite_query(question):
    prompt = f"""
Rewrite this user question for enterprise insurance RAG search.
Add Thai/English synonyms. Keep meaning. Output search query only.

Question:
{question}

Search Query:
"""
    try:
        return clean_text(call_ollama(prompt, num_predict=250))
    except Exception:
        return question

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or input("Question: ")
    print(rewrite_query(q))
