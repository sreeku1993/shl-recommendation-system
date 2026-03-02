import streamlit as st
import requests

st.title("SHL Assessment Recommendation System")

query = st.text_area("Enter Job Description or Query")

if st.button("Get Recommendations"):

    if query.strip() == "":
        st.warning("Please enter a query.")
    else:
        try:
            response = requests.post(
                "http://127.0.0.1:8000/recommend",  
                json={"query": query},
                timeout=60
            )

            data = response.json()
            results = data.get("recommended_assessments", [])

            if results:
                for r in results:
                    st.subheader(r["name"])
                    st.write(r["description"])
                    st.write("Duration:", r["duration"], "minutes")
                    st.write("Remote Support:", r["remote_support"])
                    st.write("Adaptive:", r["adaptive_support"])
                    st.markdown(f"[View Assessment]({r['url']})")
                    st.divider()
            else:
                st.error("No recommendations found.")

        except Exception as e:
            st.error(f"Error: {e}")