"""
Quick script to list available Gemini models.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path setup
from google import genai

def list_available_models():
    """List all available Gemini models."""
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("[ERROR] No API key found!")
        return
    
    print("=" * 70)
    print("AVAILABLE GEMINI MODELS")
    print("=" * 70)
    print(f"[OK] API key found: {api_key[:10]}...{api_key[-5:]}\n")
    
    try:
        client = genai.Client(api_key=api_key)
        
        print("[INFO] Fetching model list...\n")
        
        # List all models
        models = client.models.list()
        
        print(f"Found {len(list(models))} models:\n")
        
        # List again since we consumed the iterator
        models = client.models.list()
        
        for model in models:
            print(f"  - {model.name}")
            if hasattr(model, 'display_name'):
                print(f"    Display Name: {model.display_name}")
            if hasattr(model, 'description'):
                print(f"    Description: {model.description[:100]}...")
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Supported Methods: {model.supported_generation_methods}")
            print()
        
        print("=" * 70)
        print("[SUCCESS] Model list retrieved successfully")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    list_available_models()
