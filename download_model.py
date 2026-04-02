"""

Set this as your Render Build Command:
    pip install -r requirements.txt && python download_model.py
"""
from sentence_transformers import SentenceTransformer

print("Pre-downloading all-MiniLM-L6-v2 ...")
SentenceTransformer("all-MiniLM-L6-v2")
print("Model cached successfully.")
