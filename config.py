import os
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st

# ✅ Load environment variables locally (optional .env support)
load_dotenv()

# ✅ Get API key securely
# Streamlit Cloud → from st.secrets
# Local → from .env or system environment variable
GEMINI_API_KEY = (
    st.secrets.get("GOOGLE_API_KEY")  # Use Streamlit secret if available
    or os.getenv("GOOGLE_API_KEY")    # Otherwise check local .env
)

if not GEMINI_API_KEY:
    raise ValueError("❌ Google API Key is missing! Please set GOOGLE_API_KEY in Streamlit Secrets or .env file.")

# ✅ Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Initialize Gemini model
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Gemini model: {e}")

# ✅ Function to generate AI responses
def generate_ai_response(prompt: str) -> str:
    """
    Generate AI response using Google Gemini.
    Automatically handles invalid input or model errors.
    """
    if not prompt.strip():
        return "⚠️ Please provide a valid prompt."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error generating response: {e}"
