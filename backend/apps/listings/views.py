from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import Listing, Keyword
from .serializers import ListingSerializer, KeywordSerializer
from .services import ListingService

# Note: Keywords are still used for the legacy watchlist system
# The AI agent-based filtering is the primary analysis method


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


class ListingViewSet(viewsets.ModelViewSet):
    """ViewSet for Listing CRUD operations."""
    queryset = Listing.objects.all().order_by('-created_at')
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]  # Change to IsAuthenticated in production
    pagination_class = StandardResultsSetPagination
    
    def list(self, request, *args, **kwargs):
        """List listings with filtering and pagination."""
        # Extract filter parameters
        filters = {
            'search_location': request.query_params.get('search_location'),
            'min_price': request.query_params.get('min_price'),
            'max_price': request.query_params.get('max_price'),
            'max_distance': request.query_params.get('max_distance'),
            'watchlist': request.query_params.get('watchlist'),
            'agent_slug': request.query_params.get('agent_slug'),
            'scanner_id': request.query_params.get('scanner_id'),
            'interesting_only': request.query_params.get('interesting_only'),
            'notify_only': request.query_params.get('notify_only'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Get page parameters
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        
        # Get filtered listings via service
        result = ListingService.get_filtered_listings(page, limit, filters)
        
        # Serialize results
        serializer = self.get_serializer(result['results'], many=True)
        
        return Response({
            'results': serializer.data,
            'count': result['count'],
            'total_pages': result['total_pages'],
            'current_page': result['current_page'],
            'has_next': result['has_next'],
            'has_previous': result['has_previous'],
        })
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """Get available filter options."""
        options = ListingService.get_filter_options()
        return Response(options)
    
    @action(detail=True, methods=['patch'])
    def toggle_watchlist(self, request, pk=None):
        """Toggle watchlist status for a listing."""
        listing = ListingService.toggle_watchlist(int(pk))
        if not listing:
            return Response(
                {'error': 'Listing not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(listing)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='analyze-ai')
    def analyze_ai(self, request, pk=None):
        """
        Analyze a listing with the dynamic AI agent assigned to its scanner.

        Query params:
        - force: Set to 'true' to force re-analysis even if cached result exists
        """
        try:
            listing = self.get_object()
        except:
            return Response(
                {'error': 'Listing not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return cached result unless force=true
        force_reanalysis = request.query_params.get('force', 'false').lower() == 'true'
        if not force_reanalysis and listing.analysis_metadata and listing.analysis_metadata.get('llm_analysis'):
            cached_analysis = listing.analysis_metadata['llm_analysis']
            if not cached_analysis.get('is_mock', False):
                return Response(cached_analysis)

        from apps.scanners.models import ActiveScanner
        from apps.scanners.services.agents import get_agent
        from apps.scanners.services.llm_analysis_service import LLMAnalysisService
        from apps.shared.services.notification_service import NotificationService
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Resolve the agent from the listing's scanner
            scanner = ActiveScanner.objects.filter(id=listing.scanner_id).first()
            if not scanner:
                return Response(
                    {'error': f'Scanner not found for listing (scanner_id={listing.scanner_id})'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            agent_slug = scanner.agent.slug if scanner.agent_id else scanner.agent_type
            agent = get_agent(agent_slug)

            # Scrape full details + images
            llm_service = LLMAnalysisService()
            details = llm_service._extract_full_details(listing.url)

            if details['status'] != 'success':
                return Response(
                    {'error': f'Failed to scrape listing: {details.get("error", details["status"])}'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            listing_data = {
                'title': listing.title or 'No title',
                'price': listing.price or 'No price',
                'location': listing.location or 'No location',
                'url': listing.url,
                'description': details.get('description', '') or listing.description or '',
            }

            # Run deep analysis with the dynamic agent
            result = agent.analyze(
                listing_data=listing_data,
                images=details.get('image_bytes', [])
            )

            # Persist result
            if not listing.analysis_metadata:
                listing.analysis_metadata = {}
            listing.analysis_metadata['llm_analysis'] = result
            listing.save()

            # Send notification if recommended
            if result.get('recommendation') == 'NOTIFY':
                try:
                    notification_service = NotificationService()
                    notification_items = [{
                        'scanner': f"AI Scanner (Confidence: {result.get('confidence', 0)}%)",
                        'title': listing.title,
                        'price': listing.price,
                        'location': listing.location,
                        'img': listing.img,
                        'url': listing.url,
                        'llm_summary': result.get('summary', ''),
                        'llm_positives': result.get('key_takeaways', {}).get('positives', []),
                        'estimated_value': result.get('value_assessment', {}).get('estimated_value', ''),
                        'savings_percent': result.get('value_assessment', {}).get('savings_percent', 0),
                    }]
                    notification_result = notification_service.notify_new_watchlist_items(
                        notification_items,
                        channels=['email']
                    )
                    result['notification_sent'] = notification_result.get('email', False)
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
                    result['notification_sent'] = False
                    result['notification_error'] = str(e)
            else:
                result['notification_sent'] = False

            return Response(result)

        except Exception as e:
            logger.error(f"Error during AI analysis: {e}")
            return Response(
                {
                    'error': 'Analysis failed',
                    'details': str(e),
                    'recommendation': 'IGNORE',
                    'confidence': 0,
                    'summary': 'Analysis encountered an error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='ai-analysis')
    def get_ai_analysis(self, request, pk=None):
        """Get existing AI analysis for a listing."""
        try:
            listing = self.get_object()
        except:
            return Response(
                {'error': 'Listing not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not listing.analysis_metadata or not listing.analysis_metadata.get('llm_analysis'):
            return Response(
                {'error': 'No AI analysis found for this listing'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(listing.analysis_metadata['llm_analysis'])


# Keywords API - used for legacy watchlist system
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_keywords_by_scanner(request):
    """
    Get keywords for a specific scanner.
    Query params: scannerId (required)
    """
    scanner_id = request.query_params.get('scannerId')
    
    if not scanner_id:
        return Response(
            {'error': 'scannerId is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        keywords = Keyword.objects.filter(filterID=int(scanner_id))
        # Return just the keyword strings for simplicity
        keyword_list = [k.keyword for k in keywords if k.keyword]
        return Response(keyword_list)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_keywords(request):
    """
    Bulk update keywords for a scanner.
    Body: { scannerId: int, keywords: string[] }
    """
    from .serializers import KeywordBulkUpdateSerializer
    
    serializer = KeywordBulkUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    scanner_id = serializer.validated_data['scannerId']
    keywords = serializer.validated_data['keywords']
    
    try:
        # Delete existing keywords for this scanner
        Keyword.objects.filter(filterID=scanner_id).delete()
        
        # Create new keywords
        created_keywords = []
        for keyword_text in keywords:
            if keyword_text and keyword_text.strip():
                keyword = Keyword.objects.create(
                    keyword=keyword_text.strip(),
                    filterID=scanner_id
                )
                created_keywords.append(keyword.keyword)
        
        return Response({
            'success': True,
            'message': f'Updated {len(created_keywords)} keywords for scanner {scanner_id}',
            'keywords': created_keywords
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
