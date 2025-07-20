import streamlit as st
import pandas as pd
from groq import Groq
import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq setup
groq_client = Groq(api_key=GROQ_API_KEY)

# Load menu from CSV
menu_df = pd.read_csv("menu.csv")
menu_dict = dict(zip(menu_df.item.str.lower(), menu_df.price))

# Session state
if "order_history" not in st.session_state:
    st.session_state.order_history = []

# Extract ordered items using Groq API
def extract_items_from_order(order_text):
    prompt = f"""You are a helpful assistant that extracts structured data.

Given the food order: "{order_text}", extract a JSON list of dictionaries with `item` and `quantity`.

Respond ONLY with a valid JSON list like this:
[{{"item": "burger", "quantity": 2}}, {{"item": "coke", "quantity": 1}}]
"""

    response = groq_client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        import json
        items = json.loads(response.choices[0].message.content.strip())
        return items
    except Exception as e:
        st.error(f"❌ JSON parsing failed: {e}")
        st.write("🔁 Raw model output:", response.choices[0].message.content)
        return []

# Calculate total price
def calculate_price(items):
    total = 0
    not_found = []
    bill_details = []

    for entry in items:
        item = entry['item'].lower()
        quantity = entry.get('quantity', 1)
        if item in menu_dict:
            price = menu_dict[item] * quantity
            bill_details.append(f"{item.title()} x{quantity} = {price} BDT")
            total += price
        else:
            not_found.append(item)
    
    return total, bill_details, not_found

# Suggest based on history
def suggest_items():
    flat_list = [item for order in st.session_state.order_history for item in order]
    if not flat_list:
        return None
    freq = pd.Series(flat_list).value_counts()
    return freq.head(3).index.tolist()

# Streamlit UI
st.title("Text-Based Food Ordering Assistant")

order_text = st.text_input("📝 Type your order here (e.g. '2 burgers and 1 coke')")

if st.button("🧾 Submit Order") and order_text.strip():
    st.write(f"🗣 You typed: {order_text}")

    extracted = extract_items_from_order(order_text)
    if not extracted:
        st.error("❌ Could not extract order. Please try again.")
    else:
        total, details, not_found = calculate_price(extracted)
        st.session_state.order_history.append([item['item'] for item in extracted])

        st.success("🧾 Your Bill:")
        for line in details:
            st.write("- " + line)
        st.write(f"💵 Total: {total} BDT")

        if not_found:
            st.warning("❌ These items are not available:")
            for nf in not_found:
                st.write("- " + nf.title())

        suggestions = suggest_items()
        if suggestions:
            st.info(f"🍽️ You often order: {', '.join(suggestions)}")
