from typing import Dict, List, Optional, Any
from django.db.models import Q, QuerySet
from django.core.paginator import Paginator
from ..models import Listing


class ListingService:
    """Service class for listing-related business logic."""
    
    @staticmethod
    def get_filtered_listings(
        page: int = 1, 
        limit: int = 20, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get paginated and filtered listings."""
        if filters is None:
            filters = {}
        
        queryset = Listing.objects.all().order_by('-created_at')
        
        # Apply filters
        queryset = ListingService._apply_filters(queryset, filters)
        
        # Paginate
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        return {
            'results': list(page_obj),
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    @staticmethod
    def _apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply various filters to the listing queryset."""

        # Agent filter — resolve to scanner_ids via the ActiveScanner→Agent FK
        if agent_slug := filters.get('agent_slug'):
            from apps.scanners.models import ActiveScanner
            scanner_ids = list(
                ActiveScanner.objects.filter(agent__slug=agent_slug)
                .values_list('id', flat=True)
            )
            queryset = queryset.filter(scanner_id__in=scanner_ids)

        # Scanner filter
        if scanner_id := filters.get('scanner_id'):
            try:
                queryset = queryset.filter(scanner_id=int(scanner_id))
            except (ValueError, TypeError):
                pass



        # Search location filter
        if search_location := filters.get('search_location'):
            queryset = queryset.filter(search_location=search_location)

        # Distance filter
        if max_distance := filters.get('max_distance'):
            if str(max_distance).isdigit():
                queryset = queryset.filter(distance__lte=int(max_distance))

        # Price filters
        if min_price := filters.get('min_price'):
            queryset = ListingService._apply_price_filter(queryset, min_price, 'min')

        if max_price := filters.get('max_price'):
            queryset = ListingService._apply_price_filter(queryset, max_price, 'max')

        # Watchlist filter
        if filters.get('watchlist'):
            queryset = queryset.filter(watchlist=True)

        # Interesting only — listings the triage pass flagged as worth investigating
        if filters.get('interesting_only'):
            queryset = queryset.filter(triage_interesting=True)

        # Notify only — listings the deep analysis rated as truly good deals
        if filters.get('notify_only'):
            queryset = queryset.filter(investigation_result='notify')

        return queryset
    
    @staticmethod
    def _apply_price_filter(queryset: QuerySet, price_value: Any, filter_type: str) -> QuerySet:
        """Apply price filtering logic."""
        try:
            price_float = float(price_value)
            
            # Basic price filtering - can be enhanced later
            if filter_type == 'min':
                # Filter for listings with numeric prices >= min_price
                queryset = queryset.filter(price__regex=r'[$]?[0-9]+')
                # Additional logic for proper price comparison can be added here
                
            elif filter_type == 'max':
                # Filter for listings with numeric prices <= max_price
                queryset = queryset.filter(price__regex=r'[$]?[0-9]+')
                # Additional logic for proper price comparison can be added here
                
        except (ValueError, TypeError):
            # If price is not valid, ignore filter
            pass
            
        return queryset
    
    @staticmethod
    def get_filter_options() -> Dict[str, Any]:
        """Get available filter options from existing listings."""
        from apps.scanners.models import Agent, ActiveScanner

        # Get unique search locations
        search_locations = set(
            Listing.objects.values_list('search_location', flat=True)
            .exclude(search_location__isnull=True)
            .exclude(search_location='')
        )

        # Agents that have at least one scanner with listings
        scanner_ids_with_listings = set(
            Listing.objects.exclude(scanner_id__isnull=True)
            .values_list('scanner_id', flat=True)
            .distinct()
        )
        agents = list(
            Agent.objects.filter(
                enabled=True,
                scanners__id__in=scanner_ids_with_listings,
            )
            .distinct()
            .values('slug', 'name')
        )

        # Scanners that have listings
        scanners = list(
            ActiveScanner.objects.filter(id__in=scanner_ids_with_listings)
            .select_related('agent')
            .values('id', 'query', 'agent__slug')
        )

        return {
            'search_locations': sorted(list(search_locations)),
            'agents': agents,
            'scanners': [
                {'id': s['id'], 'query': s['query'], 'agent_slug': s['agent__slug']}
                for s in scanners
            ],
        }
    
    @staticmethod
    def toggle_watchlist(listing_id: int, user_id: Optional[int] = None) -> Optional[Listing]:
        """Toggle watchlist status for a listing."""
        try:
            listing = Listing.objects.get(listing_idx=listing_id)
            listing.watchlist = not listing.watchlist
            listing.save()
            return listing
        except Listing.DoesNotExist:
            return None
    
    @staticmethod
    def create_listing(listing_data: Dict[str, Any]) -> Listing:
        """Create a new listing."""
        return Listing.objects.create(**listing_data)
    
    @staticmethod
    def get_recent_listings(limit: int = 10) -> List[Listing]:
        """Get most recent listings."""
        return list(Listing.objects.order_by('-created_at')[:limit])

