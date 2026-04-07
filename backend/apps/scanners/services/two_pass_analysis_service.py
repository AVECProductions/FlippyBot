"""
Two-Pass Analysis Service.

Simplified pipeline where the same specialist agent handles both:
1. Pass 1: Triage - which listings are interesting?
2. Pass 2: Deep Analysis - should we notify the user?

No routing, no separate triage agent - just the scanner's specialist agent.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from asgiref.sync import sync_to_async
from django.db import transaction

from apps.scanners.models import ActiveScanner, ScanBatch, LLMUsage
from apps.listings.models import Listing
from .agents import get_agent
from .llm_analysis_service import LLMAnalysisService

logger = logging.getLogger(__name__)


class TwoPassAnalysisService:
    """
    Orchestrates the two-pass AI analysis pipeline.
    
    Flow:
    1. Get the specialist agent for this scanner
    2. Pass 1: Triage batch - agent quickly scans all listings
    3. Pass 2: Deep analysis - agent analyzes interesting listings in depth
    4. Track token usage and save results
    """
    
    def __init__(self):
        """Initialize the service."""
        self.llm_service = LLMAnalysisService()  # For detail fetching
    
    async def process_scanner_batch(
        self, 
        scanner: ActiveScanner, 
        listings: List[Listing],
        scan_batch: Optional[ScanBatch] = None,
        triage_only: bool = False
    ) -> Dict[str, Any]:
        """
        Process a batch of listings for a scanner using two-pass analysis.
        
        Args:
            scanner: The ActiveScanner instance
            listings: List of Listing objects to analyze
            scan_batch: Optional ScanBatch for tracking
            triage_only: If True, only run Pass 1 (triage), skip Pass 2
        
        Returns:
            Dictionary with results and statistics
        """
        if not listings:
            return {
                'success': True,
                'message': 'No listings to process',
                'stats': {
                    'total_listings': 0,
                    'triaged_interesting': 0,
                    'deep_analyzed': 0,
                    'notifications': 0,
                    'total_tokens': 0,
                    'estimated_cost_usd': 0
                }
            }
        
        try:
            # Get the specialist agent for this scanner
            # Prefer the agent FK, fall back to agent_type string
            agent_slug = await sync_to_async(lambda: scanner.agent.slug if scanner.agent_id else scanner.agent_type)()
            agent = await sync_to_async(get_agent)(agent_slug)
            logger.info(
                f"Processing {len(listings)} listings with {agent.agent_type} agent "
                f"for scanner: {scanner.query}"
            )
            
            # PASS 1: TRIAGE
            logger.info("=== PASS 1: TRIAGE ===")
            triage_results = await self._triage_pass(agent, listings, scan_batch)
            
            # Filter interesting listings
            interesting = [
                (listings[r['listing_idx']], r) 
                for r in triage_results 
                if r.get('interesting', False)
            ]
            
            logger.info(
                f"Triage complete: {len(interesting)}/{len(listings)} listings interesting "
                f"(tokens: {triage_results[0].get('token_usage', {}).get('total_tokens', 0) if triage_results else 0})"
            )
            
            # Save triage results to listings
            await self._save_triage_results(listings, triage_results)
            
            # If triage_only mode, stop here
            if triage_only:
                logger.info("Triage-only mode: skipping deep analysis")
                stats = await self._compile_statistics(
                    total_listings=len(listings),
                    triaged_interesting=len(interesting),
                    deep_analyzed=0,
                    notifications=0,
                    scan_batch=scan_batch
                )
                return {
                    'success': True,
                    'message': f'Triaged {len(listings)} listings: {len(interesting)} marked for investigation',
                    'stats': stats,
                    'triage_only': True
                }
            
            # PASS 2: DEEP ANALYSIS
            logger.info(f"=== PASS 2: DEEP ANALYSIS ({len(interesting)} listings) ===")
            analysis_results = []
            notifications = []
            
            for listing, triage_result in interesting:
                try:
                    # Fetch full details + images
                    details = await self._fetch_listing_details(listing.url)
                    
                    if details['status'] != 'success':
                        logger.warning(f"Failed to fetch details for {listing.title}: {details.get('error')}")
                        continue
                    
                    # Prepare listing data
                    listing_data = {
                        'title': listing.title or 'No title',
                        'price': listing.price or 'No price',
                        'location': listing.location or 'No location',
                        'url': listing.url,
                        'description': details.get('description', '')
                    }
                    
                    # Deep analysis with same agent
                    analysis = await sync_to_async(agent.analyze)(
                        listing_data=listing_data,
                        images=details.get('image_bytes', [])
                    )
                    
                    analysis_results.append((listing, analysis))
                    
                    # Save analysis to listing
                    await self._save_analysis(listing, triage_result, analysis, scan_batch)
                    
                    # Track token usage
                    if analysis.get('token_usage'):
                        await self._track_token_usage(
                            agent_type=agent.agent_type,
                            call_type='analyze',
                            token_usage=analysis['token_usage'],
                            listing=listing,
                            scan_batch=scan_batch
                        )
                    
                    # Queue notification if recommended
                    if analysis.get('recommendation') == 'NOTIFY':
                        notifications.append((listing, analysis))
                        logger.info(
                            f"✓ NOTIFY: {listing.title} "
                            f"(confidence: {analysis.get('confidence')}%)"
                        )
                    else:
                        logger.info(
                            f"- IGNORE: {listing.title} "
                            f"(confidence: {analysis.get('confidence')}%)"
                        )
                    
                except Exception as e:
                    logger.error(f"Error analyzing listing {listing.listing_idx}: {e}")
                    continue
            
            # Compile statistics
            stats = await self._compile_statistics(
                total_listings=len(listings),
                triaged_interesting=len(interesting),
                deep_analyzed=len(analysis_results),
                notifications=len(notifications),
                scan_batch=scan_batch
            )
            
            return {
                'success': True,
                'message': f'Processed {len(listings)} listings: {len(interesting)} interesting, {len(notifications)} notifications',
                'stats': stats,
                'notifications': [
                    {
                        'listing_id': listing.listing_idx,
                        'title': listing.title,
                        'url': listing.url,
                        'confidence': analysis.get('confidence'),
                        'summary': analysis.get('summary')
                    }
                    for listing, analysis in notifications
                ]
            }
            
        except NotImplementedError as e:
            # Agent is a stub
            logger.error(f"Agent not implemented: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': {
                    'total_listings': len(listings),
                    'triaged_interesting': 0,
                    'deep_analyzed': 0,
                    'notifications': 0
                }
            }
        except Exception as e:
            logger.error(f"Error in two-pass analysis: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}',
                'stats': {
                    'total_listings': len(listings),
                    'triaged_interesting': 0,
                    'deep_analyzed': 0,
                    'notifications': 0
                }
            }
    
    async def _triage_pass(
        self, 
        agent, 
        listings: List[Listing],
        scan_batch: Optional[ScanBatch] = None
    ) -> List[Dict[str, Any]]:
        """Execute the triage pass."""
        # Prepare listings for triage (basic metadata only)
        triage_input = [
            {
                'idx': i,
                'title': listing.title or 'No title',
                'price': listing.price or 'No price',
                'location': listing.location or 'No location',
                'thumbnail_url': listing.img
            }
            for i, listing in enumerate(listings)
        ]
        
        # Call agent triage
        triage_results = await sync_to_async(agent.triage_batch)(triage_input)
        
        # Track token usage for triage
        if triage_results and len(triage_results) > 0:
            # Token usage is typically included in the first result or separately
            # For now, we'll need to update the agent to return token usage
            pass
        
        return triage_results
    
    async def _save_triage_results(
        self,
        listings: List[Listing],
        triage_results: List[Dict[str, Any]]
    ):
        """Save triage results to listings."""
        def _save():
            saved_count = 0
            for result in triage_results:
                try:
                    idx = result.get('listing_idx')
                    if idx is None:
                        logger.warning(f"Triage result missing listing_idx: {result}")
                        continue
                    
                    if not (0 <= idx < len(listings)):
                        logger.warning(f"Triage result idx {idx} out of range (0-{len(listings)-1})")
                        continue
                    
                    listing = listings[idx]
                    listing.triage_interesting = result.get('interesting', False)
                    listing.triage_confidence = result.get('confidence', 0)
                    listing.triage_reason = result.get('reason', '')
                    listing.save(update_fields=['triage_interesting', 'triage_confidence', 'triage_reason'])
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving triage result for idx {idx}: {e}")
                    continue
            
            logger.info(f"Saved triage results for {saved_count}/{len(triage_results)} listings")
        
        await sync_to_async(_save)()
    
    async def _fetch_listing_details(self, url: str) -> Dict[str, Any]:
        """Fetch full listing details and images."""
        # Reuse the existing detail fetching logic from LLMAnalysisService
        return await sync_to_async(self.llm_service._extract_full_details)(url)
    
    async def _save_analysis(
        self,
        listing: Listing,
        triage_result: Dict[str, Any],
        analysis: Dict[str, Any],
        scan_batch: Optional[ScanBatch] = None
    ):
        """Save analysis results to the listing."""
        def _save():
            # Update triage fields
            listing.triage_interesting = triage_result.get('interesting', False)
            listing.triage_confidence = triage_result.get('confidence', 0)
            listing.triage_reason = triage_result.get('reason', '')
            
            # Update investigation status
            listing.investigation_completed = True
            listing.investigation_result = analysis.get('recommendation', 'analyzed').lower()
            
            # Store full analysis in metadata
            listing.analysis_metadata = analysis
            
            listing.save()
        
        await sync_to_async(_save)()
    
    async def _track_token_usage(
        self,
        agent_type: str,
        call_type: str,
        token_usage: Dict[str, Any],
        listing: Optional[Listing] = None,
        scan_batch: Optional[ScanBatch] = None
    ):
        """Track token usage in the database."""
        def _create_usage():
            LLMUsage.objects.create(
                scan_batch=scan_batch,
                listing=listing,
                agent_type=agent_type,
                call_type=call_type,
                model_name=token_usage.get('model', 'unknown'),
                prompt_tokens=token_usage.get('prompt_tokens', 0),
                completion_tokens=token_usage.get('completion_tokens', 0),
                total_tokens=token_usage.get('total_tokens', 0)
                # estimated_cost_usd is calculated automatically in model save()
            )
        
        await sync_to_async(_create_usage)()
    
    async def _compile_statistics(
        self,
        total_listings: int,
        triaged_interesting: int,
        deep_analyzed: int,
        notifications: int,
        scan_batch: Optional[ScanBatch] = None
    ) -> Dict[str, Any]:
        """Compile statistics including token usage."""
        def _get_stats():
            if not scan_batch:
                return {
                    'total_listings': total_listings,
                    'triaged_interesting': triaged_interesting,
                    'deep_analyzed': deep_analyzed,
                    'notifications': notifications,
                    'total_tokens': 0,
                    'estimated_cost_usd': 0
                }
            
            # Get token usage for this scan batch
            usage_records = LLMUsage.objects.filter(scan_batch=scan_batch)
            
            total_tokens = sum(u.total_tokens for u in usage_records)
            total_cost = sum(u.estimated_cost_usd for u in usage_records)
            
            return {
                'total_listings': total_listings,
                'triaged_interesting': triaged_interesting,
                'deep_analyzed': deep_analyzed,
                'notifications': notifications,
                'total_tokens': total_tokens,
                'estimated_cost_usd': float(total_cost),
                'triage_calls': usage_records.filter(call_type='triage').count(),
                'analyze_calls': usage_records.filter(call_type='analyze').count()
            }
        
        return await sync_to_async(_get_stats)()
    
    async def rerun_triage(
        self,
        scan_batch: ScanBatch
    ) -> Dict[str, Any]:
        """
        Re-run AI triage on all listings from a scan batch.
        Useful for testing prompt changes or re-evaluating listings.
        
        Args:
            scan_batch: The ScanBatch to re-triage
        
        Returns:
            Dictionary with results and statistics
        """
        try:
            # Get all listings from this scan batch
            listings = await sync_to_async(list)(
                Listing.objects.filter(scan_identifier=scan_batch.scan_id)
            )
            
            if not listings:
                return {
                    'success': False,
                    'error': 'No listings found for this scan batch',
                    'stats': {}
                }
            
            # Get the scanner for the first listing (assuming single scanner per batch)
            first_listing = listings[0]
            scanner = await sync_to_async(ActiveScanner.objects.get)(
                id=first_listing.scanner_id
            )
            
            # Get the specialist agent
            agent_slug = await sync_to_async(lambda: scanner.agent.slug if scanner.agent_id else scanner.agent_type)()
            agent = await sync_to_async(get_agent)(agent_slug)
            logger.info(
                f"Re-running triage on {len(listings)} listings with {agent.agent_type} agent"
            )
            
            # Run triage
            triage_results = await self._triage_pass(agent, listings, scan_batch)
            
            # Save results
            await self._save_triage_results(listings, triage_results)
            
            # Count interesting listings
            interesting_count = sum(1 for r in triage_results if r.get('interesting', False))
            
            # Update scan batch
            def _update_batch():
                scan_batch.investigation_marked = interesting_count
                scan_batch.save(update_fields=['investigation_marked'])
            
            await sync_to_async(_update_batch)()
            
            logger.info(f"Triage re-run complete: {interesting_count}/{len(listings)} interesting")
            
            return {
                'success': True,
                'message': f'Triage re-run complete: {interesting_count} interesting',
                'stats': {
                    'total_listings': len(listings),
                    'triaged_interesting': interesting_count,
                }
            }
            
        except Exception as e:
            logger.error(f"Error re-running triage: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'stats': {}
            }
    
    async def analyze_selected_listings(
        self,
        listing_ids: List[int],
        scanner: Optional[ActiveScanner] = None,
        scan_batch: Optional[ScanBatch] = None
    ) -> Dict[str, Any]:
        """
        Run deep analysis on manually selected listings.
        
        IMPORTANT: Listings may come from different scanners/agents.
        We must group them by scanner and use the correct agent for each group.
        
        Args:
            listing_ids: List of listing IDs to analyze
            scanner: Optional scanner (if provided, used for all - only use for single-scanner batches)
            scan_batch: Optional scan batch for tracking
        
        Returns:
            Dictionary with results
        """
        def _get_listings():
            return list(Listing.objects.filter(listing_idx__in=listing_ids))
        
        listings = await sync_to_async(_get_listings)()
        
        if not listings:
            return {
                'success': False,
                'error': 'No valid listings found',
                'analyzed': 0
            }
        
        # Group listings by scanner_id to use the correct agent for each
        def _get_scanners_for_listings():
            scanner_ids = set(l.scanner_id for l in listings if l.scanner_id)
            scanners = ActiveScanner.objects.filter(id__in=scanner_ids)
            return {s.id: s for s in scanners}
        
        scanners_map = await sync_to_async(_get_scanners_for_listings)()
        
        # Group listings by scanner
        listings_by_scanner = {}
        for listing in listings:
            scanner_id = listing.scanner_id
            if scanner_id not in listings_by_scanner:
                listings_by_scanner[scanner_id] = []
            listings_by_scanner[scanner_id].append(listing)
        
        logger.info(
            f"Processing {len(listings)} listings across {len(listings_by_scanner)} scanner(s)"
        )
        
        # Process each scanner's listings with the correct agent
        all_analysis_results = []
        all_notifications = []
        
        for scanner_id, scanner_listings in listings_by_scanner.items():
            scanner_obj = scanners_map.get(scanner_id)
            
            if not scanner_obj:
                logger.warning(f"No scanner found for scanner_id {scanner_id}, skipping {len(scanner_listings)} listings")
                continue
            
            try:
                # Get the correct specialist agent for this scanner
                agent_slug = await sync_to_async(lambda: scanner_obj.agent.slug if scanner_obj.agent_id else scanner_obj.agent_type)()
                agent = await sync_to_async(get_agent)(agent_slug)
                logger.info(
                    f"Running deep analysis on {len(scanner_listings)} listings "
                    f"with {agent.agent_type} agent (scanner: {scanner_obj.query})"
                )
                
                # Analyze each listing with the correct agent
                for listing in scanner_listings:
                    try:
                        # Fetch full details + images
                        details = await self._fetch_listing_details(listing.url)
                        
                        if details['status'] != 'success':
                            logger.warning(f"Failed to fetch details for {listing.title}")
                            continue
                        
                        # Prepare listing data
                        listing_data = {
                            'title': listing.title or 'No title',
                            'price': listing.price or 'No price',
                            'location': listing.location or 'No location',
                            'url': listing.url,
                            'description': details.get('description', '')
                        }
                        
                        # Deep analysis with the CORRECT agent
                        analysis = await sync_to_async(agent.analyze)(
                            listing_data=listing_data,
                            images=details.get('image_bytes', [])
                        )
                        
                        all_analysis_results.append((listing, analysis))
                        
                        # Save analysis
                        triage_result = {
                            'interesting': listing.triage_interesting or False,
                            'confidence': listing.triage_confidence or 0,
                            'reason': listing.triage_reason or 'Manual selection'
                        }
                        await self._save_analysis(listing, triage_result, analysis, scan_batch)
                        
                        # Track tokens
                        if analysis.get('token_usage'):
                            await self._track_token_usage(
                                agent_type=agent.agent_type,
                                call_type='analyze',
                                token_usage=analysis['token_usage'],
                                listing=listing,
                                scan_batch=scan_batch
                            )
                        
                        # Check if notification recommended
                        if analysis.get('recommendation') == 'NOTIFY':
                            all_notifications.append((listing, analysis))
                            logger.info(f"✓ NOTIFY ({agent.agent_type}): {listing.title}")
                        
                    except Exception as e:
                        logger.error(f"Error analyzing listing {listing.listing_idx}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error getting agent for scanner {scanner_id}: {e}")
                continue
        
        return {
            'success': True,
            'analyzed': len(all_analysis_results),
            'notifications': len(all_notifications),
            'results': [
                {
                    'listing_id': listing.listing_idx,
                    'title': listing.title,
                    'recommendation': analysis.get('recommendation'),
                    'confidence': analysis.get('confidence'),
                    'summary': analysis.get('summary')
                }
                for listing, analysis in all_analysis_results
            ]
        }
