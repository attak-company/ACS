import google.generativeai as genai
import os
from dotenv import load_dotenv

def list_models():
    load_dotenv()
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found in .env")
        return
    
    genai.configure(api_key=api_key)
    print("Listing available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}, Display Name: {m.display_name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == '__main__':
    list_models()
