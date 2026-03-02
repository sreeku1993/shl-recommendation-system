import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import re


# Load model 

model = SentenceTransformer("all-MiniLM-L6-v2")


# Load FAISS index

index = faiss.read_index("data/faiss_index.index")


# Load metadata

with open("data/index_mapping.json", "r", encoding="utf-8") as f:
    assessments = json.load(f)



def search_assessments(query, top_k=300):

    processed_query = clean_query(query)

    # Encode + normalize query
    query_embedding = model.encode([processed_query]).astype("float32")
    faiss.normalize_L2(query_embedding)

    # FAISS search (cosine similarity because IP + normalized)
    distances, indices = index.search(query_embedding, top_k)

    query_lower = query.lower()

    # Duration filter extraction
    duration_match = re.search(r'(\d+)\s*minutes?', query_lower)
    max_duration = int(duration_match.group(1)) if duration_match else None

    raw_candidates = []

    
    # Build candidate list
    
    for rank, idx in enumerate(indices[0]):

        item = assessments[idx]
        cosine_score = float(distances[0][rank])

        # Duration Filter 
        duration = item.get("duration", 0)
        if max_duration and (not duration or duration > max_duration):
            continue

        # Remote Filter 
        if "remote" in query_lower and not item.get("remote_support", False):
            continue

        #  Adaptive Filter
        if ("adaptive" in query_lower or "irt" in query_lower) and not item.get("adaptive_support", False):
            continue

        # Remove reports/guides 
        name_lower = item.get("name", "").lower()
        if "report" in name_lower or "guide" in name_lower:
            continue

        # Keyword Score 
        keyword_score = 0
        text = (item.get("name", "") + " " + item.get("description", "")).lower()

        for word in query_lower.split():
            if word in text:
                keyword_score += 1

        raw_candidates.append({
            "item": item,
            "cosine": cosine_score,
            "keyword": keyword_score
        })

    if not raw_candidates:
        return []

   
    # Normalize scores
    
    cosines = [c["cosine"] for c in raw_candidates]
    keywords = [c["keyword"] for c in raw_candidates]

    min_c, max_c = min(cosines), max(cosines)
    min_k, max_k = min(keywords), max(keywords)

    final_candidates = []

    for c in raw_candidates:

        # Normalize cosine (0–1)
        if max_c - min_c > 0:
            norm_cosine = (c["cosine"] - min_c) / (max_c - min_c)
        else:
            norm_cosine = 0

        # Normalize keyword (0–1)
        if max_k - min_k > 0:
            norm_keyword = (c["keyword"] - min_k) / (max_k - min_k)
        else:
            norm_keyword = 0

        # Hybrid scoring (tuned weights)
        final_score = (0.6 * norm_cosine) + (0.4 * norm_keyword)

        item_copy = c["item"].copy()
        item_copy["final_score"] = final_score

        final_candidates.append(item_copy)

    # Sort by final score
    final_candidates.sort(key=lambda x: x["final_score"], reverse=True)

    return final_candidates[:10]



# CLEAN QUERY

def clean_query(query):

    lines = query.split("\n")
    important_lines = []

    ignore_phrases = [
        "about us",
        "what shl can offer",
        "equal opportunity",
        "benefits",
        "#",
        "careersat",
        "get in touch"
    ]

    for line in lines:
        line_lower = line.lower()

        if any(phrase in line_lower for phrase in ignore_phrases):
            continue

        if len(line.strip()) < 5:
            continue

        important_lines.append(line.strip())

    return " ".join(important_lines[:15])



# Manual Testing

if __name__ == "__main__":
    query = input("Enter your hiring query: ")
    results = search_assessments(query)

    print("\nTop Recommendations:\n")
    for i, r in enumerate(results):
        print(f"{i+1}. {r.get('name')} ({r.get('test_type')})")
        print(f"   {r.get('url')}\n")