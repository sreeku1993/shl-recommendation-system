import pandas as pd
import requests

# Load train data
train_df = pd.read_excel("data/Gen_AI Dataset.xlsx", sheet_name="Train-Set")

# Group ground truth URLs by query
ground_truth = {}

for _, row in train_df.iterrows():
    query = row["Query"]
    url = row["Assessment_url"]

    ground_truth.setdefault(query, []).append(url)

print(f"Total training queries: {len(ground_truth)}")


# Call recommend API
def get_predictions(query):
    try:
        response = requests.post(
            "https://shl-api-720651928669.us-central1.run.app/recommend",
            json={"query": query},
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        # Updated key
        return [item["url"] for item in data.get("recommended_assessments", [])]

    except Exception as e:
        print("API Error:", e)
        return []


# URL normalization
def normalize(url):
    return (
        url.lower()
        .replace("https://www.shl.com", "")
        .replace("/solutions", "")
        .rstrip("/")
    )



# Compute Recall@10

recall_scores = []

for query in ground_truth:

    true_urls = set(normalize(u) for u in ground_truth[query])
    predicted_urls = set(normalize(u) for u in get_predictions(query))

    correct = true_urls.intersection(predicted_urls)

    recall = len(correct) / len(true_urls) if true_urls else 0
    recall_scores.append(recall)

    print("\nQuery:")
    print(query)
    print(f"Recall@10: {recall:.2f}")
    print(f"Correct: {len(correct)} / {len(true_urls)}")
    print("True:", list(true_urls)[:1])
    print("Pred:", list(predicted_urls)[:1])

mean_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0

print("\n==============================")
print(f"Mean Recall@10: {mean_recall:.4f}")
print("==============================")