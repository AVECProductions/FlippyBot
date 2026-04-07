#!/usr/bin/env python
"""
Delete the last N scan batches from the database.

Usage:
    python delete_scan_batches.py [number_to_delete]
    
Example:
    python delete_scan_batches.py 1    # Delete last 1 batch
    python delete_scan_batches.py 5    # Delete last 5 batches
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from apps.scanners.models import ScanBatch

# Get number of batches to delete from command line argument
try:
    num_to_delete = int(sys.argv[1]) if len(sys.argv) > 1 else 1
except ValueError:
    print("Error: Please provide a valid number")
    print("Usage: python delete_scan_batches.py [number]")
    sys.exit(1)

if num_to_delete <= 0:
    print("Error: Number must be greater than 0")
    sys.exit(1)

# Get the last N scan batches
batches_to_delete = list(ScanBatch.objects.order_by('-started_at')[:num_to_delete])

if not batches_to_delete:
    print("No scan batches found to delete.")
    sys.exit(0)

print(f"Found {len(batches_to_delete)} scan batch(es) to delete:\n")
for batch in batches_to_delete:
    print(f"  - ID: {batch.scan_id}")
    print(f"    Started: {batch.started_at}")
    print(f"    Listings Found: {batch.total_listings_found}")
    print(f"    New Added: {batch.new_listings_added}")
    print(f"    Investigation Marked: {batch.investigation_marked}")
    print()

# Confirm deletion
response = input(f"Delete these {len(batches_to_delete)} scan batch(es)? [y/N]: ")
if response.lower() != 'y':
    print("Cancelled.")
    sys.exit(0)

# Delete them
count = 0
for batch in batches_to_delete:
    scan_id = batch.scan_id
    batch.delete()
    count += 1
    print(f"✓ Deleted scan batch: {scan_id}")

print(f"\n✅ Total deleted: {count} scan batch(es)")
print("✅ The listings from these scans remain in the database.")
