#!/usr/bin/env python
"""
Test script for LLM Analysis Service.

This script tests the LLM analysis functionality by:
1. Checking if the API key is configured
2. Finding a test listing from the database
3. Running the analysis
4. Displaying the results

Usage:
    python test_llm_analysis.py [listing_id]
"""
import os
import sys
import django
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env file FIRST before anything else
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from apps.listings.models import Listing
from apps.scanners.services import get_llm_service


def check_api_key():
    """Check if API key is configured."""
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("[ERROR] No API key found!")
        print("\nPlease add one of the following to your backend/.env file:")
        print("  GEMINI_API_KEY=your_api_key_here")
        print("  OR")
        print("  GOOGLE_API_KEY=your_api_key_here")
        print("\nGet your API key at: https://makersuite.google.com/app/apikey")
        return False
    
    print(f"[OK] API key found: {api_key[:10]}...{api_key[-5:]}")
    return True


def get_test_listing(listing_id=None):
    """Get a listing to test with."""
    if listing_id:
        try:
            listing = Listing.objects.get(listing_idx=listing_id)
            print(f"\n[OK] Found listing {listing_id}: {listing.title}")
            return listing
        except Listing.DoesNotExist:
            print(f"[ERROR] Listing {listing_id} not found")
            return None
    
    # Find any listing with an image
    listings = Listing.objects.exclude(img__isnull=True).exclude(img='')[:5]
    
    if not listings:
        print("[ERROR] No listings found in database")
        print("\nPlease run a scanner first to create some listings.")
        return None
    
    print(f"\n[OK] Found {listings.count()} listings with images")
    print("\nAvailable test listings:")
    for listing in listings:
        print(f"  [{listing.listing_idx}] {listing.title[:60]}... - {listing.price}")
    
    # Use the first one
    listing = listings[0]
    print(f"\n[TEST] Using listing {listing.listing_idx} for test")
    return listing


async def test_analysis(listing):
    """Run the LLM analysis on a listing."""
    print("\n" + "="*70)
    print("RUNNING LLM ANALYSIS")
    print("="*70)
    
    print(f"\nListing Details:")
    print(f"  ID: {listing.listing_idx}")
    print(f"  Title: {listing.title}")
    print(f"  Price: {listing.price}")
    print(f"  Location: {listing.location}")
    print(f"  Image: {listing.img[:50] if listing.img else 'None'}...")
    
    print("\n[AI] Analyzing with LLM...")
    
    try:
        llm_service = get_llm_service()
        result = await llm_service.analyze_listing(listing)
        
        print("\n" + "="*70)
        print("ANALYSIS RESULTS")
        print("="*70)
        
        # Display results
        rec = result.get('recommendation', 'UNKNOWN')
        conf = result.get('confidence', 0)
        
        if rec == 'NOTIFY':
            print(f"\n[NOTIFY] RECOMMENDATION: {rec} (Confidence: {conf}%)")
        else:
            print(f"\n[IGNORE] RECOMMENDATION: {rec} (Confidence: {conf}%)")
        
        print(f"\n[SUMMARY]")
        print(f"   {result.get('summary', 'No summary')}")
        
        # Item identification
        item_id = result.get('item_identification', {})
        print(f"\n[ITEM IDENTIFICATION]")
        print(f"   Brand: {item_id.get('brand', 'Unknown')}")
        print(f"   Model: {item_id.get('model', 'Unknown')}")
        print(f"   Condition: {item_id.get('condition', 'Unknown')}")
        print(f"   Description: {item_id.get('description', 'None')[:100]}...")
        
        # Value assessment
        value = result.get('value_assessment', {})
        print(f"\n[VALUE ASSESSMENT]")
        print(f"   Estimated Value: {value.get('estimated_value', 'Unknown')}")
        print(f"   Savings: {value.get('savings_percent', 0)}%")
        print(f"   Explanation: {value.get('explanation', 'None')[:100]}...")
        
        # Key takeaways
        takeaways = result.get('key_takeaways', {})
        positives = takeaways.get('positives', [])
        negatives = takeaways.get('negatives', [])
        
        if positives:
            print(f"\n[POSITIVES]")
            for p in positives:
                print(f"   - {p}")
        
        if negatives:
            print(f"\n[NEGATIVES]")
            for n in negatives:
                print(f"   - {n}")
        
        # Image analysis
        print(f"\n[IMAGE ANALYSIS]")
        img_analysis = result.get('image_analysis', 'No image analysis')
        print(f"   {img_analysis[:200]}...")
        
        # Red flags
        notes = result.get('notes', {})
        red_flags = notes.get('red_flags', [])
        if red_flags:
            print(f"\n[RED FLAGS]")
            for flag in red_flags:
                print(f"   - {flag}")
        
        print("\n" + "="*70)
        print("[SUCCESS] TEST COMPLETED SUCCESSFULLY")
        print("="*70)
        
        return result
        
    except Exception as e:
        print("\n" + "="*70)
        print("[FAILED] TEST FAILED")
        print("="*70)
        print(f"\nError: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        return None


def main():
    """Main test function."""
    print("="*70)
    print("LLM ANALYSIS SERVICE TEST")
    print("="*70)
    
    # Check API key
    if not check_api_key():
        return
    
    # Get listing ID from command line if provided
    listing_id = None
    if len(sys.argv) > 1:
        try:
            listing_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid listing ID: {sys.argv[1]}")
            return
    
    # Get test listing
    listing = get_test_listing(listing_id)
    if not listing:
        return
    
    # Run analysis
    result = asyncio.run(test_analysis(listing))
    
    if result:
        print("\n[TIP] You can now view this analysis in the UI by:")
        print(f"   1. Going to the listing with ID {listing.listing_idx}")
        print(f"   2. Right-clicking and selecting 'Analyze with AI'")
        print(f"   3. The cached result will be displayed instantly")


if __name__ == '__main__':
    main()
