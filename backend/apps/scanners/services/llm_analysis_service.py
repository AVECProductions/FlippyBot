"""
LLM Analysis Service for marketplace listing analysis.
Handles detail extraction (scraping) from Facebook Marketplace listings via Playwright.
"""
from typing import Dict, Any, List, Optional
import logging
import time
import random
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class LLMAnalysisService:
    """
    Service for extracting full details from Facebook Marketplace listings via Playwright.
    Used by TwoPassAnalysisService and the analyze-listing-url endpoint for scraping.
    """

    def _extract_full_details(self, url: str) -> Dict[str, Any]:
        """
        Extract full description and ALL images from a Facebook Marketplace listing.
        Uses Playwright to scrape the actual listing page.

        Args:
            url: The listing URL

        Returns:
            Dictionary with status, description, and images list
        """
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    ]
                )

                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )

                page = context.new_page()

                # Anti-detection
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                """)

                try:
                    logger.info(f"Navigating to: {url}")
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    time.sleep(random.uniform(2, 4))

                    # Check if listing is available
                    if "unavailable_product=1" in page.url:
                        browser.close()
                        return {'status': 'unavailable', 'error': 'Listing no longer available'}

                    if "facebook.com/login" in page.url:
                        browser.close()
                        return {'status': 'login_required', 'error': 'Login required'}

                    # Extract description
                    description = self._extract_description_from_page(page)

                    # Extract title, price, location from the listing page
                    title = self._extract_title_from_page(page)
                    price = self._extract_price_from_page(page)
                    location = self._extract_location_from_page(page)

                    # Extract ALL images from carousel (URLs only)
                    image_urls = self._extract_images_from_page(page)

                    # Download images directly from Playwright context
                    # This bypasses the 403 errors we get with httpx
                    image_bytes_list = []
                    if image_urls:
                        logger.info(f"Downloading {len(image_urls)} images via Playwright context")
                        for url in image_urls[:5]:  # Limit to 5 images
                            try:
                                img_response = context.request.get(url, timeout=10000)
                                if img_response.status == 200:
                                    image_bytes_list.append(img_response.body())
                                    logger.info(f"Downloaded image {len(image_bytes_list)}/{len(image_urls[:5])}")
                                else:
                                    logger.warning(f"Failed to download image: HTTP {img_response.status}")
                            except Exception as e:
                                logger.warning(f"Error downloading image: {e}")

                    browser.close()

                    return {
                        'status': 'success',
                        'title': title,
                        'price': price,
                        'location': location,
                        'description': description,
                        'images': image_urls,  # Store URLs
                        'image_bytes': image_bytes_list  # Return bytes directly
                    }

                except TimeoutError:
                    browser.close()
                    return {'status': 'timeout', 'error': 'Timeout accessing listing'}
                except Exception as e:
                    browser.close()
                    return {'status': 'error', 'error': f'Error accessing listing: {str(e)}'}

        except Exception as e:
            return {'status': 'failed', 'error': f'Browser error: {str(e)}'}

    def _extract_description_from_page(self, page) -> str:
        """
        Extract description from Facebook Marketplace listing page.
        Uses aria-hidden="false" as stable identifier for visible content.
        """
        try:
            # Strategy 1: CSS selectors for known Facebook structure
            selectors = [
                'div.xz9dl7a div[aria-hidden="false"] span[dir="auto"]',
                'div.xz9dl7a > div[aria-hidden="false"] > span[dir="auto"]',
                'div[aria-hidden="false"] > span[dir="auto"]',
            ]

            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for element in elements:
                        text = element.inner_text()
                        if self._is_valid_description(text):
                            logger.info(f"Found description via selector: {len(text)} characters")
                            return text.strip()
                except Exception:
                    continue

            # Strategy 2: JavaScript extraction
            js_code = """
            () => {
                const visibleElements = document.querySelectorAll('div[aria-hidden="false"]');

                for (const el of visibleElements) {
                    const span = el.querySelector('span[dir="auto"]');
                    if (span) {
                        const text = span.innerText?.trim();
                        if (!text || text.length < 25) continue;

                        const lowerText = text.toLowerCase();
                        if (lowerText === 'details') continue;
                        if (lowerText.startsWith('condition')) continue;
                        if (lowerText.includes('log in') && text.length < 100) continue;
                        if (lowerText.includes('sign up') && text.length < 100) continue;
                        if (lowerText.includes('create new account')) continue;
                        if (lowerText === 'used - good') continue;
                        if (lowerText === 'used - fair') continue;
                        if (lowerText === 'used - excellent') continue;
                        if (lowerText === 'like new') continue;
                        if (lowerText === 'new') continue;

                        const parent = el.closest('div.xz9dl7a');
                        if (parent) {
                            return text;
                        }

                        if (/cm|inch|condition|used|included|good|great|excellent/i.test(text)) {
                            return text;
                        }
                    }
                }
                return null;
            }
            """
            result = page.evaluate(js_code)
            if result and len(result) > 20:
                logger.info(f"Found description via JS: {len(result)} characters")
                return result.strip()

            logger.warning("No description found on page")
            return ''

        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            return ''

    def _is_valid_description(self, text: Optional[str]) -> bool:
        """Check if text looks like a valid product description."""
        if not text:
            return False

        text = text.strip()
        if len(text) < 25:
            return False

        text_lower = text.lower()

        skip_patterns = [
            'log in', 'sign up', 'create new account', 'email or phone',
            'password', 'see more on facebook', 'forgot password',
            'marketplace', 'browse all', 'create new listing',
            'location is approximate'
        ]

        for pattern in skip_patterns:
            if pattern in text_lower and len(text) < 100:
                return False

        if text_lower in ['details', 'condition', 'location', 'description',
                          'used - good', 'used - fair', 'used - excellent',
                          'like new', 'new']:
            return False

        return True

    def _extract_title_from_page(self, page) -> str:
        """Extract the listing title from a Facebook Marketplace detail page."""
        try:
            # Facebook uses an h1 or prominent span for the title
            js_code = """
            () => {
                // Strategy 1: h1 element (common on marketplace listing pages)
                const h1 = document.querySelector('h1');
                if (h1 && h1.innerText.trim().length > 0) return h1.innerText.trim();

                // Strategy 2: The main title span inside the listing content
                const titleSpan = document.querySelector('span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x4zkp8e.x676frb.x1nxh6w3.x1sibtaa.xo1l8bm.xi81zsa.x1yc453h');
                if (titleSpan && titleSpan.innerText.trim().length > 0) return titleSpan.innerText.trim();

                // Strategy 3: Look for prominent text near the top
                const spans = document.querySelectorAll('span[dir="auto"]');
                for (const span of spans) {
                    const text = span.innerText?.trim();
                    if (!text || text.length < 3 || text.length > 300) continue;
                    // Skip prices, locations, generic labels
                    if (/^\\$/.test(text)) continue;
                    if (/^(Details|Description|Condition|Location|Listed|Free|Message)/i.test(text)) continue;
                    // The title is usually one of the first prominent spans
                    const style = window.getComputedStyle(span);
                    const fontSize = parseFloat(style.fontSize);
                    if (fontSize >= 20) return text;
                }
                return '';
            }
            """
            result = page.evaluate(js_code)
            if result:
                logger.info(f"Extracted title: {result[:80]}")
                return result
            return ''
        except Exception as e:
            logger.warning(f"Error extracting title: {e}")
            return ''

    def _extract_price_from_page(self, page) -> str:
        """Extract the listing price from a Facebook Marketplace detail page."""
        try:
            js_code = """
            () => {
                // Look for price pattern ($X,XXX or $X or Free)
                const spans = document.querySelectorAll('span[dir="auto"], span');
                for (const span of spans) {
                    const text = span.innerText?.trim();
                    if (!text) continue;
                    // Match $X, $X,XXX, $X.XX, or "Free"
                    if (/^\\$[\\d,.]+$/.test(text) || text.toLowerCase() === 'free') {
                        return text;
                    }
                }
                return '';
            }
            """
            result = page.evaluate(js_code)
            if result:
                logger.info(f"Extracted price: {result}")
                return result
            return ''
        except Exception as e:
            logger.warning(f"Error extracting price: {e}")
            return ''

    def _extract_location_from_page(self, page) -> str:
        """Extract the listing location from a Facebook Marketplace detail page."""
        try:
            js_code = """
            () => {
                // Location is usually near the price, contains city/state patterns
                const spans = document.querySelectorAll('span[dir="auto"], span');
                for (const span of spans) {
                    const text = span.innerText?.trim();
                    if (!text || text.length < 3 || text.length > 100) continue;
                    // Match "City, ST" or "City, State" patterns
                    if (/^[A-Z][a-zA-Z\\s]+,\\s*[A-Z]{2}$/.test(text)) return text;
                    if (/^[A-Z][a-zA-Z\\s]+,\\s*[A-Z][a-z]+/.test(text)) return text;
                }
                // Fallback: look for "Listed in" pattern
                const allText = document.body.innerText;
                const match = allText.match(/Listed\\s+(?:in|near)\\s+([A-Z][^\\n]{3,40})/);
                if (match) return match[1].trim();
                return '';
            }
            """
            result = page.evaluate(js_code)
            if result:
                logger.info(f"Extracted location: {result}")
                return result
            return ''
        except Exception as e:
            logger.warning(f"Error extracting location: {e}")
            return ''

    def _extract_images_from_page(self, page) -> List[str]:
        """
        Extract ALL image URLs from the Facebook Marketplace listing carousel.

        Uses aria-label="Thumbnail X" to target carousel images specifically.
        Keeps original URLs without modification to avoid Facebook CDN 403 errors.
        """
        try:
            js_code = """
            () => {
                const imageUrls = [];

                // Strategy 1: Find carousel thumbnails by aria-label pattern
                // Facebook uses: <div aria-label="Thumbnail 0">, <div aria-label="Thumbnail 1">, etc.
                const thumbnailDivs = document.querySelectorAll('[aria-label^="Thumbnail"]');

                for (const div of thumbnailDivs) {
                    // Find img tag inside this thumbnail container
                    const img = div.querySelector('img[src*="fbcdn.net"]');
                    if (img && img.src) {
                        // Keep original URL - sizes like s960x960, p720x720 are already good quality
                        // Modifying to "original" causes 403 errors from Facebook CDN
                        imageUrls.push(img.src);
                    }
                }

                // Strategy 2: Fallback - find all product images if carousel not found
                if (imageUrls.length === 0) {
                    const allImages = document.querySelectorAll('img[src*="fbcdn.net"]');

                    for (const img of allImages) {
                        const src = img.src;
                        // Skip small icons and static images
                        if (src && !src.includes('static') && !src.includes('emoji')) {
                            // Only large images (product photos)
                            if (img.naturalWidth > 200 || img.width > 200) {
                                if (!imageUrls.includes(src)) {
                                    imageUrls.push(src);
                                }
                            }
                        }
                    }
                }

                return imageUrls;
            }
            """
            images = page.evaluate(js_code)
            logger.info(f"Found {len(images)} carousel images (using original URLs)")
            return images or []
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []


# Global service instance
_llm_service = None


def get_llm_service() -> LLMAnalysisService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMAnalysisService()
    return _llm_service
