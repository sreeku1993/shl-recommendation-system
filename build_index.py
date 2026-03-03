import json, os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
save_path = "./local_model"
# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")
os.makedirs(save_path, exist_ok=True)

model.save(save_path)#saved to local to prevent gcloud-huggingface errors
# Load assessment data
with open("data/assessments.json", "r", encoding="utf-8") as f:
    assessments = json.load(f)

print(f"Loaded {len(assessments)} assessments")

# Prepare text for embedding
texts = []

test_type_map = {
    "A": "Ability and Aptitude",
    "B": "Biodata and Situational Judgement",
    "C": "Competencies",
    "D": "Development and 360",
    "E": "Assessment Exercises",
    "K": "Knowledge and Skills",
    "P": "Personality and Behaviour",
    "S": "Simulations"
}

for item in assessments:

    test_type_full = test_type_map.get(item.get("test_type", ""), "")

    remote_text = "Remote Supported" if item.get("remote_support") else "Not Remote"
    adaptive_text = "Adaptive IRT Supported" if item.get("adaptive_support") else "Not Adaptive"

    combined_text = (
        item["name"] + " "
        + item.get("description", "") + " "
        + " Test Category: " + test_type_full + " "
        + " Duration: " + str(item.get("duration", 0)) + " minutes "
        + remote_text + " "
        + adaptive_text
    )

    texts.append(combined_text)

# Generate embeddings
embeddings = model.encode(texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# Create FAISS index
dimension = embeddings.shape[1]
# Normalize embeddings
faiss.normalize_L2(embeddings)

index = faiss.IndexFlatIP(dimension)  # inner product = cosine
index.add(embeddings)

print("Total vectors in index:", index.ntotal)

# Save index
faiss.write_index(index, "data/faiss_index.index")

# Save metadata order
with open("data/index_mapping.json", "w", encoding="utf-8") as f:
    json.dump(assessments, f)

print("Index saved successfully.")