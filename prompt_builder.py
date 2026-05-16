import os

def load_document() -> str:
    path = os.environ.get("DOCUMENT_PATH", "document.txt")
    with open(path, "r") as f:
        return f.read()

DOCUMENT = load_document()