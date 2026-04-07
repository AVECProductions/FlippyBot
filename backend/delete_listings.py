#!/usr/bin/env python
"""
Delete listings from the database to allow re-discovery.

Usage:
    python delete_listings.py [number_to_delete]
    
Example:
    python delete_listings.py 100    # Delete last 100 listings
    python delete_listings.py 500    # Delete last 500 listings
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from apps.listings.models import Listing

# Get number of listings to delete from command line argument
try:
    num_to_delete = int(sys.argv[1]) if len(sys.argv) > 1 else 100
except ValueError:
    print("Error: Please provide a valid number")
    print("Usage: python delete_listings.py [number]")
    sys.exit(1)

if num_to_delete <= 0:
    print("Error: Number must be greater than 0")
    sys.exit(1)

# Get the last N listings (most recent first)
listings_to_delete = list(Listing.objects.order_by('-created_at')[:num_to_delete])

if not listings_to_delete:
    print("No listings found to delete.")
    sys.exit(0)

print(f"Found {len(listings_to_delete)} listing(s) to delete:\n")

# Show summary by scanner
from collections import Counter
scanner_counts = Counter(listing.scanner_id for listing in listings_to_delete)

for scanner_id, count in scanner_counts.items():
    print(f"  - Scanner {scanner_id}: {count} listings")

print(f"\nTotal: {len(listings_to_delete)} listings")
print(f"Date range: {listings_to_delete[-1].created_at} to {listings_to_delete[0].created_at}\n")

# Show a few examples
print("Examples:")
for listing in listings_to_delete[:5]:
    print(f"  - ${listing.price or '?'} - {listing.title[:50]}...")

if len(listings_to_delete) > 5:
    print(f"  ... and {len(listings_to_delete) - 5} more")
print()

# Confirm deletion
response = input(f"Delete these {len(listings_to_delete)} listing(s)? [y/N]: ")
if response.lower() != 'y':
    print("Cancelled.")
    sys.exit(0)

# Delete them
count = Listing.objects.filter(
    listing_idx__in=[listing.listing_idx for listing in listings_to_delete]
).delete()

print(f"\n✅ Total deleted: {count[0]} listing(s)")
print(f"✅ Breakdown: {count[1]}")
print("✅ Next scan will discover these as 'new' listings and run AI triage!")
