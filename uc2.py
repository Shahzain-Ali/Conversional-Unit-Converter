import streamlit as st
import requests
import json
import re
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(page_title="Conversational Unit Converter")

# Simple header
st.title("Conversational Unit Converter")
st.write("Select units and get a friendly conversational response from an AI assistant.")

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")

if api_key:
    st.sidebar.success("API Key loaded automatically!")
else:
    st.sidebar.error("API Key not found in environment variables")

# Select model
model_options = ["mistralai/Mistral-7B-Instruct-v0.2", "meta-llama/Llama-2-7b-chat-hf"]
selected_model = st.sidebar.selectbox("Select AI Model:", model_options)

# Define unit categories and their respective units
unit_categories = {
    "Length": ["mm", "cm", "m", "km", "in", "ft", "yd", "mi"],
    "Weight/Mass": ["mg", "g", "kg", "oz", "lb", "ton"],
    "Volume": ["ml", "L", "gal", "pt", "qt", "fl oz", "cm³", "m³"],
    "Temperature": ["°C", "°F", "K"],
    "Time": ["sec", "min", "hr", "day", "week", "month", "year"],
    "Area": ["mm²", "cm²", "m²", "km²", "in²", "ft²", "acre", "hectare"],
    "Speed": ["m/s", "km/h", "mph", "knot"],
    "Pressure": ["Pa", "kPa", "bar", "psi", "atm"],
    "Energy": ["J", "cal", "kcal", "kWh", "eV"],
    "Data": ["bit", "byte", "KB", "MB", "GB", "TB"]
}

# Main input area using columns and dropdowns
col1, col2, col3, col4 = st.columns([1, 1, 0.2 , 1])

with col1:
    # Category selection
    selected_category = st.selectbox("Category:", list(unit_categories.keys()))

# Initialize from_unit and to_unit in session state if not present
if 'from_unit' not in st.session_state or st.session_state.get('current_category') != selected_category:
    st.session_state.from_unit = unit_categories[selected_category][0]
    st.session_state.to_unit = unit_categories[selected_category][1] if len(unit_categories[selected_category]) > 1 else unit_categories[selected_category][0]
    st.session_state.current_category = selected_category

with col1:
    # Value input
    value = st.number_input("Value:", step=0.1)

with col2:
    # From unit selection
    from_unit = st.selectbox(
        "From Unit:", 
        unit_categories[selected_category],
        index=unit_categories[selected_category].index(st.session_state.from_unit)
    )
    st.session_state.from_unit = from_unit

with col3:
    st.write("")
    st.write("")
    st.write("→")

with col4:
    # To unit selection
    to_options = [unit for unit in unit_categories[selected_category] if unit != from_unit]
    # Add back from_unit at the end (useful in some cases)
    to_options.append(from_unit)
    
    # If the previous to_unit is valid for this category, select it
    if st.session_state.to_unit in unit_categories[selected_category]:
        default_index = to_options.index(st.session_state.to_unit) if st.session_state.to_unit in to_options else 0
    else:
        default_index = 0
    
    to_unit = st.selectbox(
        "To Unit:", 
        to_options,
        index=default_index
    )
    st.session_state.to_unit = to_unit

# Function to get conversational response from Hugging Face
def get_conversion_response(value, from_unit, to_unit, category, model, api_key):
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are a helpful and friendly unit converter assistant. 
    Please convert {value} {from_unit} to {to_unit} in the category of {category}.
    Respond in a conversational tone as if speaking to a friend. 
    Include the numeric result and a brief explanation of how the conversion works.
    """
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 150,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response_json = response.json()
        
        if isinstance(response_json, list):
            result_text = response_json[0].get("generated_text", "")
        elif isinstance(response_json, dict):
            result_text = response_json.get("generated_text", "")
        else:
            result_text = str(response_json)
            
        return result_text
    
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Convert button
if st.button("Convert", type="primary", use_container_width=True):
    if value is not None and from_unit and to_unit:
        # Create the query string for history
        query = f"{value} {from_unit} to {to_unit}"
        
        with st.spinner("Getting your conversion..."):
            response = get_conversion_response(value, from_unit, to_unit, selected_category, selected_model, api_key)
            
            # Display result in a nice box
            st.markdown("### Conversion Result")
            st.info(response)
            
            # Store in history
            if 'conversion_history' not in st.session_state:
                st.session_state.conversion_history = []
                
            history_entry = f"{query} → {response[:100]}..." if len(response) > 100 else response
            if history_entry not in st.session_state.conversion_history:
                st.session_state.conversion_history.insert(0, history_entry)
                if len(st.session_state.conversion_history) > 5:
                    st.session_state.conversion_history.pop()
    else:
        st.warning("Please enter a value and select both units for conversion.")

# Display conversion history
if 'conversion_history' in st.session_state and st.session_state.conversion_history:
    st.markdown("### Recent Conversions")
    for entry in st.session_state.conversion_history:
        st.markdown(f"- {entry}")

# Footer
st.markdown("---")
st.markdown("Developed by Shahzain Ali")