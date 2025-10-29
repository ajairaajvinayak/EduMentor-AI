import os
import google.generativeai as genai
from dotenv import load_dotenv

# ✅ Load environment variables (if .env file exists)
load_dotenv()

# ✅ Set your Gemini API key
# Use environment variable if available, otherwise fallback to the direct key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GEMINI_API_KEY:
    raise ValueError("❌ Google API Key is missing! Please set GOOGLE_API_KEY in your environment or .env file.")

# ✅ Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Initialize the Gemini model (2.5 Flash is fast & cost-efficient)
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Gemini model: {e}")

# ✅ Optional helper: Generate AI responses safely
def generate_ai_response(prompt: str) -> str:
    """
    Safely generate content from the Gemini model.
    Handles empty input and model errors gracefully.
    """
    if not prompt.strip():
        return "⚠️ Please provide a valid prompt."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error generating response: {e}"

