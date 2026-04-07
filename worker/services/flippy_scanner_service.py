"""
FlippyBot Scanner Service - Clean Architecture Implementation
Handles Facebook Marketplace scanning with Django ORM integration
"""
import re
import time
import random
import os
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from playwright.sync_api import sync_playwright, TimeoutError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client

from django.conf import settings
from django.db import transaction

from apps.scanners.models import ActiveScanner, Location, ScannerLocationMapping, ScanBatch, AnalysisProgress
from apps.listings.models import Keyword, Listing
from apps.shared.services import NotificationService


class FlippyScannerService:
    """Service class for FlippyBot scanning operations."""

    def __init__(self):
        self.items_searched = 0

    @staticmethod
    def generate_scan_id():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"scan_{timestamp}_{unique_id}"

    @staticmethod
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
                else:
                    safe_args.append(str(arg).encode('ascii', 'replace').decode('ascii'))
            print(*safe_args, **kwargs)

    @staticmethod
    def find_distance(location_a: str, location_b: str) -> Optional[float]:
        try:
            geolocator = Nominatim(user_agent="flippy_location_finder")
            town1 = geolocator.geocode(location_a)
            town2 = geolocator.geocode(location_b)
            if not town1 or not town2:
                print(f"Could not geocode one of the locations: {location_a}, {location_b}")
                return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

        coord1 = (town1.latitude, town1.longitude)
        coord2 = (town2.latitude, town2.longitude)
        distance = geodesic(coord1, coord2).miles
        return distance

    def get_active_scanners(self) -> List[Dict[str, Any]]:
        scanner_data = []

        active_scanners = ActiveScanner.objects.filter(status='running').prefetch_related(
            'scannerlocationmapping_set__location'
        )

        for scanner in active_scanners:
            location_mappings = scanner.scannerlocationmapping_set.filter(is_active=True)

            if location_mappings.exists():
                scanner_data.append({
                    'id': scanner.id,
                    'category': scanner.category,
                    'query': scanner.query,
                    'status': scanner.status,
                    'locations': [
                        {
                            'mapping_id': mapping.id,
                            'name': mapping.location.name,
                            'marketplace_slug': mapping.location.marketplace_url_slug,
                            'is_active': mapping.is_active
                        }
                        for mapping in location_mappings
                    ]
                })

        return scanner_data


class SearchDataStructure:
    def __init__(self, scanner_id: int, category: str, query: str, location_name: str, marketplace_slug: str = None, scan_identifier: str = None):
        self.scanner_id = scanner_id
        self.category = category
        self.query = query
        self.location_name = location_name
        self.marketplace_slug = marketplace_slug or "coloradosprings"
        self.search_title = category
        self.scan_identifier = scan_identifier


class MarketplaceDealFinder:
    def __init__(self, search_data: SearchDataStructure):
        self.scanner_id = search_data.scanner_id
        self.category = search_data.category
        self.query = search_data.query
        self.location_name = search_data.location_name
        self.marketplace_slug = search_data.marketplace_slug
        self.search_title = search_data.search_title
        self.scan_identifier = search_data.scan_identifier
        self.items_searched = 0

    @staticmethod
    def is_dollar_integer(string: str) -> bool:
        pattern = r'^\$[0-9]{1,3}(?:,[0-9]{3})*$'
        return bool(re.match(pattern, string))

    def get_distance(self, listing_location: str) -> float:
        return 0.0

    def should_investigate_listing(self, title: str, price: str, keywords_by_scanner: Dict) -> bool:
        title_lower = title.lower()
        for scanner_id, keywords in keywords_by_scanner.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return True
        return False

    def scrape_listings(self) -> List[Dict[str, Any]]:
        scraped_listings = []

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    '--window-size=1920,1080',
                ]
            )

            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
            ]

            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(user_agents),
            )

            page = context.new_page()

            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """)

            search_params = {
                'daysSinceListed': '1',
                'deliveryMethod': 'local_pick_up',
                'sortBy': random.choice(['best_match', 'creation_time_descend']),
            }

            search_URL = f'https://www.facebook.com/marketplace/{self.marketplace_slug}/search?'
            search_URL += '&'.join([f"{k}={v}" for k, v in search_params.items()])
            search_URL += f'&query={quote(self.query)}'

            try:
                print(f"Searching URL: {search_URL}")
                print("Visiting Facebook homepage first...")
                page.goto("https://www.facebook.com", wait_until="domcontentloaded")
                time.sleep(random.uniform(2, 4))

                print("Navigating to marketplace...")
                page.goto(search_URL, wait_until="domcontentloaded")
                time.sleep(random.uniform(3, 6))

            except Exception as e:
                print(f"Cannot access URL: {search_URL}. Error: {e}")
                return scraped_listings

            try:
                print("Waiting for listings to load...")
                selectors = [
                    'div[class*="x9f619 x78zum5"]',
                    '[class="xkrivgy x1gryazu x1n2onr6"]',
                ]

                found = False
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        print(f"Found listings with selector: {selector}")
                        found = True
                        break
                    except TimeoutError:
                        continue

                if not found:
                    raise TimeoutError("No listings container found")

                print("Found listings container")
                time.sleep(random.uniform(2, 4))
            except TimeoutError:
                print("No listings found.")
                return scraped_listings

            print("Looking for listing links...")
            listing_selectors = [
                'a[class*="x1i10hfl"][class*="xjbqb8w"][href*="/marketplace/item/"]',
                'a[href*="/marketplace/item/"]',
            ]

            locators = []
            for selector in listing_selectors:
                found = page.query_selector_all(selector)
                print(f"Selector '{selector}': Found {len(found)} links")
                if found:
                    locators = found
                    print(f"Using selector: {selector}")
                    break

            if not locators:
                print("No listing links found")
                return scraped_listings

            print(f"Found {len(locators)} total listing links")
            max_items = min(len(locators), random.randint(10, 20))
            indices = list(range(min(len(locators), max_items)))
            random.shuffle(indices)
            print(f"Will process {max_items} listings in random order")

            for idx in indices:
                element = locators[idx]
                href = element.get_attribute('href')
                if not href:
                    continue

                URL = 'https://www.facebook.com/' + href if not href.startswith('http') else href
                print(f"Processing listing {idx}: {URL}")

                innerText = element.inner_text()
                parts = innerText.split('\n')
                FlippyScannerService.safe_print(f"Raw text parts: {parts}")

                try:
                    if len(parts) < 2:
                        continue

                    if self.is_dollar_integer(parts[0]) and len(parts) > 2 and self.is_dollar_integer(parts[1]):
                        price = parts[0].strip()
                        title = parts[2].strip()
                        location = parts[3].strip() if len(parts) > 3 else ''
                    else:
                        price = parts[0].strip()
                        title = parts[1].strip()
                        location = parts[2].strip() if len(parts) > 2 else ''

                    if not price or not title:
                        continue

                except Exception as e:
                    print(f"Error parsing listing text: {parts}. Error: {e}")
                    continue

                html = element.inner_html()
                soup = BeautifulSoup(html, 'html.parser')
                img_element = soup.find('img')
                img = img_element.get('src') if img_element else ''

                listing_data = {
                    'price': price,
                    'title': title,
                    'location': location,
                    'url': URL,
                    'img': img,
                    'distance': self.get_distance(location) if location else 0,
                    'query': self.query,
                    'search_title': self.search_title,
                    'scanner_id': self.scanner_id,
                    'search_location': self.location_name,
                    'scan_identifier': self.scan_identifier
                }
                scraped_listings.append(listing_data)
                FlippyScannerService.safe_print(f"Collected listing: {price} - {title[:50]}...")

                self.items_searched += 1

            page.close()
            browser.close()

        print(f"Completed scraping. Found {len(scraped_listings)} listings.")
        return scraped_listings

    def process_scraped_listings(self, scraped_listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        watchlist_items = []
        new_listings_count = 0

        if not scraped_listings:
            print("No listings to process.")
            return {'watchlist_items': watchlist_items, 'listings_searched': 0, 'new_listings_added': 0}

        print(f"Processing {len(scraped_listings)} scraped listings...")

        try:
            scanner = ActiveScanner.objects.get(id=self.scanner_id)
            category = scanner.category

            scanner_ids = ActiveScanner.objects.filter(category=category).values_list('id', flat=True)

            keywords_by_scanner = {}
            for scanner_id in scanner_ids:
                keywords = Keyword.objects.filter(filterID=scanner_id).values_list('keyword', flat=True)
                keyword_list = [k.strip().lower() for k in keywords if k]
                if keyword_list:
                    keywords_by_scanner[scanner_id] = keyword_list

        except Exception as e:
            print(f"Error fetching keywords: {e}")
            keywords_by_scanner = {}

        print(f"Available keywords by scanner: {keywords_by_scanner}")

        for listing_data in scraped_listings:
            price = listing_data['price']
            title = listing_data['title']
            url = listing_data['url']
            location = listing_data['location']
            img = listing_data['img']

            try:
                exists = Listing.objects.filter(price=price, title=title, url=url).exists()
            except Exception as e:
                print(f"ERROR checking listing existence: {e}")
                exists = False

            if not exists:
                print("New listing found! Adding to database...")

                needs_investigation = self.should_investigate_listing(title, price, keywords_by_scanner)

                watchlist = False
                matched_scanner_id = None
                title_lower = title.lower()

                for scanner_id, keywords in keywords_by_scanner.items():
                    for keyword in keywords:
                        if keyword in title_lower:
                            watchlist = True
                            matched_scanner_id = scanner_id

                            try:
                                matched_scanner = ActiveScanner.objects.get(id=matched_scanner_id)
                                watchlist_item = {
                                    'scanner': f"{matched_scanner.query} in {self.location_name}",
                                    'title': title,
                                    'location': location,
                                    'price': price,
                                    'img': img,
                                    'url': url
                                }
                                watchlist_items.append(watchlist_item)
                            except ActiveScanner.DoesNotExist:
                                pass
                            break
                    if watchlist:
                        break

                item_scanner_id = matched_scanner_id if matched_scanner_id else self.scanner_id

                try:
                    listing = Listing.objects.create(
                        price=price,
                        title=title,
                        location=location,
                        description=None,
                        distance=listing_data['distance'],
                        url=url,
                        img=img,
                        query=listing_data['query'],
                        search_title=listing_data['search_title'],
                        watchlist=watchlist,
                        scanner_id=item_scanner_id,
                        search_location=listing_data['search_location'],
                        scan_identifier=listing_data['scan_identifier'],
                        needs_investigation=needs_investigation,
                        investigation_completed=False,
                        investigation_result='pending' if needs_investigation else None
                    )
                    FlippyScannerService.safe_print(f"SUCCESS: Created listing ID {listing.listing_idx} - {title} - {price}")
                    new_listings_count += 1
                except Exception as e:
                    print(f"ERROR: Failed to insert listing: {e}")
            else:
                print("Listing already exists, skipping...")

        return {
            'watchlist_items': watchlist_items,
            'listings_searched': len(scraped_listings),
            'new_listings_added': new_listings_count
        }

    def find_deals(self) -> Dict[str, Any]:
        print("Step 1: Scraping listings from Facebook Marketplace...")
        scraped_listings = self.scrape_listings()
        print(f"Step 2: Processing {len(scraped_listings)} scraped listings...")
        return self.process_scraped_listings(scraped_listings)


class FlippyScannerOrchestrator:
    """Main orchestrator service for running all FlippyBot scanning operations."""

    def __init__(self):
        self.scanner_service = FlippyScannerService()
        self.notification_service = NotificationService()

    def run_all_scanners(self, randomize: bool = True, single_run: bool = False) -> Dict[str, Any]:
        from apps.scanners.models import SystemTask, ScannerSettings
        from django.utils import timezone as dj_timezone

        print("Starting FlippyBot scanner orchestration...")

        scan_id = FlippyScannerService.generate_scan_id()
        scan_type = 'single' if single_run else 'continuous'
        print(f"Creating scan batch: {scan_id} ({scan_type})")

        scan_batch = ScanBatch.objects.create(
            scan_id=scan_id,
            scan_type=scan_type,
            started_at=datetime.now()
        )

        task = SystemTask.objects.create(
            task_type='scan',
            status='running',
            current_step='initializing',
            progress_percent=0,
            progress_message=f'Starting {scan_type} scan...',
            scan_batch=scan_batch
        )

        scanners = self.scanner_service.get_active_scanners()

        if not scanners:
            scan_batch.completed_at = datetime.now()
            scan_batch.save()
            task.complete(success=True)

            return {
                'success': False,
                'message': 'No active scanners found.',
                'scan_id': scan_id,
                'stats': {'scanners_processed': 0, 'watchlist_items': 0, 'total_listings': 0}
            }

        task.update_progress('scraping', 10, f'Scraping {len(scanners)} scanners...')

        if randomize:
            random.shuffle(scanners)

        watchlist_items = []
        total_listings_searched = 0
        total_new_listings_added = 0
        total_investigation_marked = 0

        for scanner in scanners:
            scanner_id = scanner['id']
            category = scanner['category']
            query = scanner['query']
            locations = scanner['locations']

            print(f"Running Scanner: {query} with {len(locations)} locations")

            for location in locations:
                location_name = location['name']
                marketplace_slug = location['marketplace_slug']
                print(f"  - Searching in {location_name} ({marketplace_slug})")

                search_struct = SearchDataStructure(
                    scanner_id=scanner_id,
                    category=category,
                    query=query,
                    location_name=location_name,
                    marketplace_slug=marketplace_slug,
                    scan_identifier=scan_id
                )

                finder = MarketplaceDealFinder(search_struct)
                location_result = finder.find_deals()
                watchlist_items.extend(location_result['watchlist_items'])
                total_listings_searched += location_result['listings_searched']
                total_new_listings_added += location_result['new_listings_added']

                if not single_run and len(locations) > 1:
                    delay = random.uniform(15, 30)
                    print(f"    Waiting {delay:.1f} seconds before next location...")
                    time.sleep(delay)

            if not single_run and len(scanners) > 1:
                delay = random.uniform(30, 90)
                print(f"Waiting {delay:.1f} seconds before next scanner...")
                time.sleep(delay)

        print("\nSCAN SUMMARY:")
        print(f"   Total scanners processed: {len(scanners)}")
        print(f"   Total watchlist items found: {len(watchlist_items)}")

        if watchlist_items:
            for item in watchlist_items:
                FlippyScannerService.safe_print(f"   - {item['title']} ({item['price']}) in {item['location']}")
            print("Sending notifications...")
            notification_results = self.notification_service.notify_new_watchlist_items(watchlist_items)
            for channel, success in notification_results.items():
                status = "SUCCESS" if success else "FAILED"
                print(f"   {channel.upper()} notification: {status}")
        else:
            print("   No watchlist items found.")

        # AI Triage (Pass 1)
        print("\n=== AI TRIAGE (Pass 1) ===")
        task.update_progress('triaging', 50, 'Running AI triage on listings...')

        all_notifications = []
        total_triaged = 0

        try:
            import asyncio
            # Worker version: import from worker's own services/
            from services.two_pass_analysis_service import TwoPassAnalysisService

            scan_listings = list(Listing.objects.filter(scan_identifier=scan_id))

            if scan_listings:
                print(f"Found {len(scan_listings)} listings to triage")

                scanner_listings = {}
                for listing in scan_listings:
                    sid = listing.scanner_id
                    if sid not in scanner_listings:
                        scanner_listings[sid] = []
                    scanner_listings[sid].append(listing)

                triage_service = TwoPassAnalysisService()

                for scanner_id, listings in scanner_listings.items():
                    try:
                        scanner_obj = ActiveScanner.objects.get(id=scanner_id)
                        print(f"  Triaging {len(listings)} listings for scanner: {scanner_obj.query}")

                        result = asyncio.run(
                            triage_service.process_scanner_batch(
                                scanner=scanner_obj,
                                listings=listings,
                                scan_batch=scan_batch,
                                triage_only=True
                            )
                        )

                        if result['success']:
                            triaged = result['stats'].get('triaged_interesting', 0)
                            total_triaged += triaged
                            print(f"    ✓ {triaged} marked as interesting")
                        else:
                            print(f"    ✗ Triage failed: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        print(f"    ✗ Error triaging scanner {scanner_id}: {e}")
                        continue

                print(f"✓ AI Triage complete: {total_triaged} listings marked as interesting")

                if total_triaged > 0 and not single_run:
                    print("\n=== DEEP ANALYSIS (Pass 2 - Automatic) ===")
                    task.update_progress('analyzing', 70, f'Deep analyzing {total_triaged} listings...')

                    interesting_listings = list(Listing.objects.filter(
                        scan_identifier=scan_id,
                        triage_interesting=True,
                        investigation_completed=False
                    ))

                    if interesting_listings:
                        interesting_by_scanner = {}
                        for listing in interesting_listings:
                            sid = listing.scanner_id
                            if sid not in interesting_by_scanner:
                                interesting_by_scanner[sid] = []
                            interesting_by_scanner[sid].append(listing)

                        total_analyzed = 0
                        total_notify = 0

                        for scanner_id, listings in interesting_by_scanner.items():
                            try:
                                scanner_obj = ActiveScanner.objects.get(id=scanner_id)
                                listing_ids = [l.listing_idx for l in listings]

                                analysis_result = asyncio.run(
                                    triage_service.analyze_selected_listings(
                                        listing_ids=listing_ids,
                                        scanner=scanner_obj,
                                        scan_batch=scan_batch
                                    )
                                )

                                if analysis_result['success']:
                                    analyzed = analysis_result.get('analyzed', 0)
                                    notify_count = analysis_result.get('notifications', 0)
                                    total_analyzed += analyzed
                                    total_notify += notify_count

                                    scanner_emails = scanner_obj.notification_emails or []

                                    for result_item in analysis_result.get('results', []):
                                        if result_item.get('recommendation') == 'NOTIFY':
                                            try:
                                                listing = Listing.objects.get(listing_idx=result_item['listing_id'])
                                                all_notifications.append({
                                                    'listing_id': listing.listing_idx,
                                                    'title': listing.title,
                                                    'price': listing.price,
                                                    'location': listing.location,
                                                    'url': listing.url,
                                                    'img': listing.img,
                                                    'confidence': result_item.get('confidence', 0),
                                                    'summary': result_item.get('summary', ''),
                                                    'scanner': scanner_obj.query,
                                                    'scanner_id': scanner_obj.id,
                                                    'scanner_emails': scanner_emails,
                                                    'analysis': listing.analysis_metadata
                                                })
                                            except Listing.DoesNotExist:
                                                pass

                            except Exception as e:
                                print(f"    ✗ Error during deep analysis for scanner {scanner_id}: {e}")
                                import traceback
                                traceback.print_exc()
                                continue

                        print(f"✓ Deep Analysis complete: {total_analyzed} analyzed, {total_notify} NOTIFY")
                    else:
                        print("No interesting listings to deep analyze")

                elif total_triaged > 0 and single_run:
                    print(f"\n=== MANUAL SCAN: {total_triaged} listings marked interesting ===")
                    print("Deep analysis skipped for manual scan - select listings to analyze in the UI")
                    task.update_progress('complete', 85, f'{total_triaged} interesting - select for deep analysis')
                else:
                    print("No interesting listings found, skipping deep analysis")
            else:
                print("No listings to triage")

        except Exception as e:
            print(f"✗ Error during AI analysis: {e}")
            import traceback
            traceback.print_exc()

        # Send notifications (continuous scans only)
        if all_notifications and not single_run:
            print(f"\n=== SENDING NOTIFICATIONS ===")
            task.update_progress('notifying', 90, f'Sending {len(all_notifications)} notifications...')

            try:
                notifications_by_scanner = {}
                for notif in all_notifications:
                    sid = notif.get('scanner_id', 0)
                    if sid not in notifications_by_scanner:
                        notifications_by_scanner[sid] = {
                            'emails': notif.get('scanner_emails', []),
                            'scanner_name': notif.get('scanner', 'Unknown'),
                            'items': []
                        }
                    notifications_by_scanner[sid]['items'].append(notif)

                for scanner_id, scanner_data in notifications_by_scanner.items():
                    notification_results = self.notification_service.notify_deep_analysis_results(
                        scanner_data['items'],
                        recipient_emails=scanner_data['emails'] if scanner_data['emails'] else None
                    )
                    for channel, success in notification_results.items():
                        print(f"      {channel.upper()}: {'SUCCESS' if success else 'FAILED'}")

            except Exception as e:
                print(f"✗ Error sending notifications: {e}")
                import traceback
                traceback.print_exc()

        # Finalize scan batch
        try:
            investigation_count = Listing.objects.filter(
                scan_identifier=scan_id,
                triage_interesting=True
            ).count()

            scan_batch.completed_at = datetime.now()
            scan_batch.total_listings_found = total_listings_searched
            scan_batch.new_listings_added = total_new_listings_added
            scan_batch.investigation_marked = investigation_count
            scan_batch.save()

        except Exception as e:
            print(f"Error updating scan batch: {e}")
            investigation_count = 0

        try:
            total_listings = Listing.objects.count()
        except Exception:
            total_listings = 0

        task.update_progress('complete', 100, f'Scan complete: {total_new_listings_added} new, {investigation_count} interesting')
        task.complete(success=True)

        try:
            scanner_settings = ScannerSettings.get_settings()
            scanner_settings.last_scan_at = dj_timezone.now()
            if scanner_settings.auto_enabled:
                scanner_settings.calculate_next_scan()
            scanner_settings.save()
        except Exception as e:
            print(f"Could not update scanner settings: {e}")

        return {
            'success': True,
            'message': f'Scan completed successfully. {len(watchlist_items)} watchlist items found.',
            'scan_id': scan_id,
            'stats': {
                'scanners_processed': len(scanners),
                'watchlist_items': len(watchlist_items),
                'total_listings': total_listings,
                'listings_searched': total_listings_searched,
                'new_listings_added': total_new_listings_added,
                'investigation_marked': investigation_count
            }
        }
