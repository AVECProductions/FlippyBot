#!/usr/bin/env python
"""
Standalone script to run the Django-integrated FlippyBot scanner
This avoids potential async context issues with Django management commands
"""
import os
import sys
import django
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Now import and run the scanner
from main.flippy_scanner import main

if __name__ == "__main__":
    print("=== Django FlippyBot Scanner ===")
    print("Running standalone scanner script...")
    
    # Set randomization if desired
    if "--randomize" in sys.argv:
        os.environ["RANDOMIZE_SEARCH"] = "1"
        print("Randomization enabled")
    
    try:
        main()
        print("Scanner completed successfully!")
    except Exception as e:
        print(f"Scanner failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

