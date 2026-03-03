import pandas as pd
import requests

# Load test sheet
test_df = pd.read_excel("data/Gen_AI Dataset.xlsx", sheet_name="Test-Set")

queries = test_df["Query"].unique()

print(f"Total test queries: {len(queries)}")

# Call recommend endpoint
def get_predictions(query):
    try:
        response = requests.post(
            "https://shl-api-720651928669.us-central1.run.app/recommend",  # Change if deployed
            json={"query": query},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        return [item["url"] for item in data.get("recommended_assessments", [])]

    except Exception as e:
        print("API Error:", e)
        return []



# Build submission rows

rows = []

for query in queries:

    predictions = get_predictions(query)

    #take top 10
    predictions = predictions[:10]

    for url in predictions:
        rows.append({
            "Query": query,
            "Assessment_url": url
        })



# Save CSV 

submission_df = pd.DataFrame(rows, columns=["Query", "Assessment_url"])

submission_df.to_csv("final_test_submission.csv", index=False)

print("✅ final_test_submission.csv generated successfully")