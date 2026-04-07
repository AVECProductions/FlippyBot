from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import models
from .models import (
    Agent, ActiveScanner, Location, ScannerLocationMapping, ScanBatch,
    AnalysisProgress, SystemTask, ScannerSettings, WorkerStatus
)
from .serializers import (
    AgentSerializer,
    AgentListSerializer,
    ActiveScannerSerializer, 
    LocationSerializer, 
    ScannerLocationMappingSerializer,
    ScanBatchSerializer,
    AnalysisProgressSerializer,
    SystemTaskSerializer,
    ScannerSettingsSerializer
)
from .services import ScannerService, ScannerControlService


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


class AgentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Agent CRUD operations.
    
    Endpoints:
        GET    /api/agents/          - List all agents (lightweight, no prompts)
        POST   /api/agents/          - Create a new agent
        GET    /api/agents/{slug}/   - Get agent detail (includes prompts)
        PATCH  /api/agents/{slug}/   - Update agent
        DELETE /api/agents/{slug}/   - Delete agent
    """
    queryset = Agent.objects.all()
    permission_classes = [IsAuthenticated]  # Change to IsAuthenticated in production
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Use lightweight serializer for list, full serializer for detail."""
        if self.action == 'list':
            return AgentListSerializer
        return AgentSerializer
    
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, slug=None):
        """Duplicate an agent (useful as a template for new agents)."""
        source = self.get_object()
        
        # Create a copy with a new slug
        import re
        base_slug = re.sub(r'-copy(-\d+)?$', '', source.slug)
        
        # Find unique slug
        counter = 1
        new_slug = f"{base_slug}-copy"
        while Agent.objects.filter(slug=new_slug).exists():
            new_slug = f"{base_slug}-copy-{counter}"
            counter += 1
        
        new_agent = Agent.objects.create(
            name=f"{source.name} (Copy)",
            slug=new_slug,
            description=source.description,
            icon=source.icon,
            triage_prompt=source.triage_prompt,
            analysis_prompt=source.analysis_prompt,
            triage_model=source.triage_model,
            analysis_model=source.analysis_model,
            enabled=False,  # Start disabled
        )
        
        serializer = AgentSerializer(new_agent)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet for Location CRUD operations."""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]  # Change to IsAuthenticated in production


class ActiveScannerViewSet(viewsets.ModelViewSet):
    """ViewSet for ActiveScanner CRUD operations."""
    queryset = ActiveScanner.objects.all()
    serializer_class = ActiveScannerSerializer
    permission_classes = [IsAuthenticated]  # Change to IsAuthenticated in production
    
    def create(self, request, *args, **kwargs):
        """Create a new scanner with location associations."""
        # Extract location_ids from request data
        location_ids = request.data.pop('location_ids', [])
        
        # Validate input
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create scanner via service
        scanner = ScannerService.create_scanner_with_locations(
            serializer.validated_data, 
            location_ids
        )
        
        # Return response
        return Response(
            ActiveScannerSerializer(scanner).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update scanner and optionally its location associations."""
        # Extract location_ids from request data
        location_ids = request.data.pop('location_ids', None)
        
        # Update the scanner
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Update location mappings if provided
        if location_ids is not None:
            ScannerService.update_scanner_locations(instance, location_ids)
        
        # Return updated scanner
        return Response(ActiveScannerSerializer(instance).data)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle scanner status between running and stopped."""
        scanner = ScannerService.toggle_scanner_status(int(pk))
        if not scanner:
            return Response(
                {'error': 'Scanner not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(ActiveScannerSerializer(scanner).data)


class ScannerLocationMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for ScannerLocationMapping operations."""
    queryset = ScannerLocationMapping.objects.all()
    serializer_class = ScannerLocationMappingSerializer
    permission_classes = [IsAuthenticated]  # Change to IsAuthenticated in production
    
    @action(detail=False, methods=['get'])
    def by_scanner(self, request):
        """Get location mappings by scanner ID."""
        scanner_id = request.query_params.get('scanner_id')
        if not scanner_id:
            return Response(
                {"error": "Scanner ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mappings = ScannerService.get_scanner_locations(int(scanner_id))
        serializer = self.get_serializer(mappings, many=True)
        return Response(serializer.data)


# Scanner Control API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_scanner(request):
    """Enable auto scanning — worker picks up within 30 seconds."""
    from django.utils import timezone
    from datetime import timedelta
    try:
        interval = request.data.get('interval', 20)
        db_settings = ScannerSettings.get_settings()
        db_settings.auto_enabled = True
        db_settings.interval_minutes = interval
        db_settings.next_scan_at = timezone.now()  # immediate — worker picks up within 5s
        db_settings.save()
        return Response({
            'success': True,
            'message': f'Auto scanning enabled (interval: {interval}m). Worker will start within 5 seconds.'
        })
    except Exception as e:
        return Response({'error': f'Failed to start scanner: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_scanner(request):
    """Disable auto scanning — worker stops after current scan completes."""
    try:
        db_settings = ScannerSettings.get_settings()
        db_settings.auto_enabled = False
        db_settings.next_scan_at = None
        db_settings.save()
        return Response({'success': True, 'message': 'Auto scanning disabled.'})
    except Exception as e:
        return Response({'error': f'Failed to stop scanner: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scanner_status(request):
    """Get scanner status — reads WorkerStatus heartbeat and ScannerSettings."""
    from django.utils import timezone as tz
    from datetime import timedelta
    try:
        db_settings = ScannerSettings.get_settings()
        try:
            worker = WorkerStatus.objects.get(id=1)
            # Consider worker online if heartbeat within last 30s (worker pings every 10s)
            online = worker.is_online and worker.worker_last_seen and \
                     (tz.now() - worker.worker_last_seen).total_seconds() < 30
            worker_data = {
                'online': online,
                'last_seen': worker.worker_last_seen,
                'current_task': worker.current_task,
            }
        except WorkerStatus.DoesNotExist:
            worker_data = {'online': False, 'last_seen': None, 'current_task': ''}

        return Response({
            'available': True,
            'running': worker_data['online'],
            'worker': worker_data,
            'auto_enabled': db_settings.auto_enabled,
            'interval_minutes': db_settings.interval_minutes,
            'next_scan_at': db_settings.next_scan_at,
            'last_scan_at': db_settings.last_scan_at,
        })
    except Exception as e:
        return Response({'error': f'Failed to get scanner status: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_single_scan(request):
    """Trigger an immediate scan — sets next_scan_at=now, worker picks up within 30s."""
    from django.utils import timezone
    try:
        db_settings = ScannerSettings.get_settings()
        db_settings.auto_enabled = True
        db_settings.next_scan_at = timezone.now()
        db_settings.save()
        return Response({
            'success': True,
            'message': 'Scan triggered. Worker will start within 30 seconds.'
        })
    except Exception as e:
        return Response({'error': f'Failed to trigger scan: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_history(request):
    """Get recent scan history."""
    try:
        history_data = ScannerControlService.get_scan_history()
        return Response(history_data)
        
    except PermissionError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to read scan history: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_batches_debug(request):
    """Debug endpoint to test scan batches functionality."""
    try:
        from .serializers import ScanBatchSerializer
        batches = ScanBatch.objects.all().order_by('-started_at')[:10]
        serializer = ScanBatchSerializer(batches, many=True)
        return Response({
            'count': batches.count(),
            'results': serializer.data
        })
    except Exception as e:
        return Response(
            {'error': f'Debug error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_batches_list(request):
    """Temporary function-based view to replace the ViewSet."""
    try:
        from .serializers import ScanBatchSerializer
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        
        # Get all batches
        all_batches = ScanBatch.objects.all().order_by('-started_at')
        total_count = all_batches.count()
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        batches = all_batches[start:end]
        
        # Serialize
        serializer = ScanBatchSerializer(batches, many=True)
        
        return Response({
            'count': total_count,
            'next': f'?page={page + 1}&limit={limit}' if end < total_count else None,
            'previous': f'?page={page - 1}&limit={limit}' if page > 1 else None,
            'results': serializer.data
        })
    except Exception as e:
        return Response(
            {'error': f'Scan batches error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_batch_detail(request, scan_id):
    """Get details for a specific scan batch."""
    try:
        from .serializers import ScanBatchSerializer
        batch = ScanBatch.objects.get(scan_id=scan_id)
        serializer = ScanBatchSerializer(batch)
        return Response(serializer.data)
    except ScanBatch.DoesNotExist:
        return Response(
            {'error': 'Scan batch not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Scan batch detail error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_batch_listings(request, scan_id):
    """Get listings for a specific scan batch."""
    try:
        from apps.listings.models import Listing
        from apps.listings.serializers import ListingSerializer
        
        # Verify scan batch exists
        batch = ScanBatch.objects.get(scan_id=scan_id)
        
        # Get pagination and filter parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        filter_type = request.GET.get('filter', 'all')
        
        # Get base listings for this scan
        base_listings = Listing.objects.filter(scan_identifier=scan_id).order_by('-created_at')
        
        # Calculate total counts for each category (before filtering)
        # Count listings with deep analysis (Pass 2) - those with NOTIFY/PASS/IGNORE recommendation
        analyzed_count = base_listings.filter(
            analysis_metadata__recommendation__in=['NOTIFY', 'PASS', 'IGNORE']
        ).count()
        
        # Count NOTIFY recommendations specifically
        notify_count = base_listings.filter(
            analysis_metadata__recommendation='NOTIFY'
        ).count()
        
        total_counts = {
            'all': base_listings.count(),
            'interesting': base_listings.filter(triage_interesting=True).count(),
            'skipped': base_listings.filter(triage_interesting=False).count(),
            'analyzed': analyzed_count,
            'notify': notify_count,
        }
        
        # Apply filter
        if filter_type == 'interesting':
            # Pass 1: Marked interesting but not yet deep analyzed
            filtered_listings = base_listings.filter(triage_interesting=True)
        elif filter_type == 'skipped':
            # Pass 1: Skipped by AI triage
            filtered_listings = base_listings.filter(triage_interesting=False)
        elif filter_type == 'analyzed':
            # Pass 2: Has deep analysis with recommendation
            filtered_listings = base_listings.filter(
                analysis_metadata__recommendation__in=['NOTIFY', 'PASS', 'IGNORE']
            )
        elif filter_type == 'notify':
            # Pass 2: Recommended for notification
            filtered_listings = base_listings.filter(
                analysis_metadata__recommendation='NOTIFY'
            )
        else:
            filtered_listings = base_listings
        
        filtered_count = filtered_listings.count()
        
        # If filtered results are <= limit, return all without pagination
        if filtered_count <= limit:
            listings = filtered_listings
            serializer = ListingSerializer(listings, many=True)
            return Response({
                'count': filtered_count,
                'next': None,
                'previous': None,
                'results': serializer.data,
                'total_counts': total_counts,
                'is_filtered': filter_type != 'all',
                'filter_type': filter_type
            })
        
        # Apply pagination for larger result sets
        start = (page - 1) * limit
        end = start + limit
        listings = filtered_listings[start:end]
        
        # Serialize
        serializer = ListingSerializer(listings, many=True)
        
        return Response({
            'count': filtered_count,
            'next': f'?page={page + 1}&limit={limit}&filter={filter_type}' if end < filtered_count else None,
            'previous': f'?page={page - 1}&limit={limit}&filter={filter_type}' if page > 1 else None,
            'results': serializer.data,
            'total_counts': total_counts,
            'is_filtered': filter_type != 'all',
            'filter_type': filter_type
        })
    except ScanBatch.DoesNotExist:
        return Response(
            {'error': 'Scan batch not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Scan batch listings error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_detailed_analysis(request, scan_id):
    """
    Run detailed AI analysis on a specific scan batch.
    
    This endpoint runs Pass 2 (deep analysis) on all listings in the batch
    that were marked as interesting during triage (Pass 1).
    
    Uses the new AI agent-based TwoPassAnalysisService.
    """
    import asyncio
    from .services.two_pass_analysis_service import TwoPassAnalysisService
    from apps.listings.models import Listing
    
    try:
        # Verify scan batch exists
        batch = ScanBatch.objects.get(scan_id=scan_id)
        
        # Check if analysis is already in progress (with stuck detection)
        if batch.analysis_status == 'in_progress':
            if batch.analysis_started_at:
                from datetime import datetime, timedelta
                # Check if it's been running for more than 30 minutes (likely stuck)
                stuck_threshold = datetime.now() - timedelta(minutes=30)
                if batch.analysis_started_at < stuck_threshold:
                    # Auto-reset stuck analysis
                    batch.analysis_status = 'pending'
                    batch.analysis_started_at = None
                    batch.analysis_completed_at = None
                    batch.save()
                else:
                    return Response(
                        {'error': f'Analysis already in progress (started {batch.analysis_started_at}). Use reset if stuck.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Analysis already in progress for this scan batch'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get listings marked as interesting by triage
        interesting_listings = list(Listing.objects.filter(
            scan_identifier=scan_id,
            triage_interesting=True,
            investigation_completed=False
        ))
        
        if not interesting_listings:
            return Response({
                'success': True,
                'message': 'No listings marked for investigation in this batch',
                'stats': {
                    'total_listings': 0,
                    'analyzed': 0,
                    'notifications': 0
                }
            })
        
        # Get listing IDs for the analysis service
        listing_ids = [l.listing_idx for l in interesting_listings]
        
        # Run AI deep analysis using TwoPassAnalysisService
        analysis_service = TwoPassAnalysisService()
        result = asyncio.run(
            analysis_service.analyze_selected_listings(
                listing_ids=listing_ids,
                scan_batch=batch
            )
        )
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': f"Analyzed {result.get('analyzed', 0)} listings",
                'stats': {
                    'analyzed': result.get('analyzed', 0),
                    'notifications': result.get('notifications', 0),
                    'results': result.get('results', [])
                }
            })
        else:
            return Response(
                {'error': result.get('error', 'Unknown error')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except ScanBatch.DoesNotExist:
        return Response(
            {'error': 'Scan batch not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Analysis error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_analysis_status(request, scan_id):
    """Reset analysis status for a scan batch (useful when analysis gets stuck or for rerunning analysis)."""
    try:
        from .models import AnalysisProgress
        from apps.listings.models import Listing
        
        # Verify scan batch exists
        batch = ScanBatch.objects.get(scan_id=scan_id)
        
        # Reset the scan batch status
        batch.analysis_status = 'pending'
        batch.analysis_started_at = None
        batch.analysis_completed_at = None
        batch.save()
        
        # Reset progress tracking if it exists
        try:
            progress = AnalysisProgress.objects.get(scan_batch=batch)
            progress.processed_items = 0
            progress.current_item_title = ''
            progress.current_status = 'reset'
            progress.save()
        except AnalysisProgress.DoesNotExist:
            pass
        
        # Reset individual listing analysis status to allow reprocessing
        # Only reset items that need investigation to focus on relevant data
        investigation_items = Listing.objects.filter(
            scan_identifier=scan_id,
            needs_investigation=True
        )
        
        reset_count = investigation_items.update(
            investigation_completed=False,
            investigation_result=None,
            analysis_metadata={}  # Clear previous analysis data
        )
        
        return Response({
            'success': True,
            'message': f'Analysis status reset for scan batch {scan_id}. Reset {reset_count} investigation items for reprocessing.'
        })
            
    except ScanBatch.DoesNotExist:
        return Response(
            {'error': 'Scan batch not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Reset error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════
# AI USAGE TRACKING API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usage_overview(request):
    """
    Get aggregate token usage statistics.
    
    Query params:
    - days: Number of days to look back (default: 7)
    - agent_type: Filter by agent type (optional)
    """
    try:
        from .models import LLMUsage
        from django.db.models import Sum, Count, Avg
        from datetime import datetime, timedelta
        
        days = int(request.query_params.get('days', 7))
        agent_type = request.query_params.get('agent_type')
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        usage_query = LLMUsage.objects.filter(created_at__gte=start_date)
        if agent_type:
            usage_query = usage_query.filter(agent_type=agent_type)
        
        # Aggregate statistics
        aggregates = usage_query.aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('estimated_cost_usd'),
            total_calls=Count('id'),
            avg_tokens_per_call=Avg('total_tokens')
        )
        
        # Breakdown by agent type (dynamic - reads from Agent table)
        by_agent = {}
        agent_slugs = Agent.objects.values_list('slug', flat=True)
        for agent_slug in agent_slugs:
            agent_stats = LLMUsage.objects.filter(
                created_at__gte=start_date,
                agent_type=agent_slug
            ).aggregate(
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('estimated_cost_usd'),
                total_calls=Count('id')
            )
            if agent_stats['total_calls'] and agent_stats['total_calls'] > 0:
                by_agent[agent_slug] = {
                    'total_tokens': agent_stats['total_tokens'] or 0,
                    'total_cost_usd': float(agent_stats['total_cost'] or 0),
                    'total_calls': agent_stats['total_calls']
                }
        
        # Breakdown by call type
        by_call_type = {}
        for call_type in ['triage', 'analyze']:
            call_stats = usage_query.filter(call_type=call_type).aggregate(
                total_tokens=Sum('total_tokens'),
                total_cost=Sum('estimated_cost_usd'),
                total_calls=Count('id')
            )
            if call_stats['total_calls'] and call_stats['total_calls'] > 0:
                by_call_type[call_type] = {
                    'total_tokens': call_stats['total_tokens'] or 0,
                    'total_cost_usd': float(call_stats['total_cost'] or 0),
                    'total_calls': call_stats['total_calls']
                }
        
        return Response({
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'totals': {
                'total_tokens': aggregates['total_tokens'] or 0,
                'total_cost_usd': float(aggregates['total_cost'] or 0),
                'total_calls': aggregates['total_calls'] or 0,
                'avg_tokens_per_call': int(aggregates['avg_tokens_per_call'] or 0)
            },
            'by_agent': by_agent,
            'by_call_type': by_call_type
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get usage overview: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_usage(request, scan_id):
    """
    Get token usage for a specific scan batch.
    
    Returns detailed breakdown of all LLM calls for this scan.
    """
    try:
        from .models import LLMUsage
        from django.db.models import Sum, Count
        
        # Verify scan batch exists
        scan_batch = ScanBatch.objects.get(scan_id=scan_id)
        
        # Get all usage records for this scan
        usage_records = LLMUsage.objects.filter(scan_batch=scan_batch)
        
        # Aggregate statistics
        aggregates = usage_records.aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('estimated_cost_usd'),
            total_calls=Count('id'),
            triage_calls=Count('id', filter=models.Q(call_type='triage')),
            analyze_calls=Count('id', filter=models.Q(call_type='analyze'))
        )
        
        # Detailed records
        records = []
        for record in usage_records.order_by('-created_at'):
            records.append({
                'id': record.id,
                'agent_type': record.agent_type,
                'call_type': record.call_type,
                'model_name': record.model_name,
                'total_tokens': record.total_tokens,
                'prompt_tokens': record.prompt_tokens,
                'completion_tokens': record.completion_tokens,
                'estimated_cost_usd': float(record.estimated_cost_usd),
                'created_at': record.created_at.isoformat(),
                'listing_id': record.listing_id if record.listing else None
            })
        
        return Response({
            'scan_id': scan_id,
            'scan_batch': {
                'started_at': scan_batch.started_at.isoformat(),
                'completed_at': scan_batch.completed_at.isoformat() if scan_batch.completed_at else None,
                'total_listings': scan_batch.total_listings_found,
                'analysis_status': scan_batch.analysis_status
            },
            'totals': {
                'total_tokens': aggregates['total_tokens'] or 0,
                'total_cost_usd': float(aggregates['total_cost'] or 0),
                'total_calls': aggregates['total_calls'] or 0,
                'triage_calls': aggregates['triage_calls'] or 0,
                'analyze_calls': aggregates['analyze_calls'] or 0
            },
            'records': records
        })
        
    except ScanBatch.DoesNotExist:
        return Response(
            {'error': 'Scan batch not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to get scan usage: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scanner_agent_info(request, pk):
    """
    Get information about the agent associated with a scanner.
    
    Returns agent type, enabled status, and capabilities.
    """
    try:
        from .services.agents import get_agent
        
        scanner = ActiveScanner.objects.get(id=pk)
        
        # Resolve agent slug (prefer FK, fall back to agent_type)
        agent_slug = scanner.agent.slug if scanner.agent_id else scanner.agent_type
        
        # Get agent info
        agent_info = {
            'scanner_id': scanner.id,
            'scanner_name': f"{scanner.query} in {scanner.locations.first().name if scanner.locations.exists() else 'unknown'}",
            'agent_type': agent_slug,
        }
        
        # Try to instantiate the agent to check if it's enabled
        try:
            agent = get_agent(agent_slug)
            agent_info['enabled'] = agent.enabled
            agent_info['triage_model'] = agent.triage_model
            agent_info['analysis_model'] = agent.analysis_model
            agent_info['status'] = 'active'
        except NotImplementedError as e:
            agent_info['enabled'] = False
            agent_info['status'] = 'stub'
            agent_info['message'] = str(e)
        
        return Response(agent_info)
        
    except ActiveScanner.DoesNotExist:
        return Response(
            {'error': 'Scanner not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to get agent info: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_investigation_status(request):
    """
    Toggle the 'needs investigation' status for a listing.
    
    Allows manual override of AI triage decisions.
    
    Body:
        {
            "listing_id": 123,
            "needs_investigation": true/false
        }
    """
    from apps.listings.models import Listing
    
    listing_id = request.data.get('listing_id')
    needs_investigation = request.data.get('needs_investigation')
    
    if listing_id is None or needs_investigation is None:
        return Response(
            {'error': 'listing_id and needs_investigation are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        listing = Listing.objects.get(id=listing_id)
        listing.triage_interesting = needs_investigation
        listing.save(update_fields=['triage_interesting'])
        
        return Response({
            'success': True,
            'listing_id': listing.id,
            'needs_investigation': listing.triage_interesting,
            'message': f'Listing {"marked" if needs_investigation else "unmarked"} for investigation'
        })
        
    except Listing.DoesNotExist:
        return Response(
            {'error': 'Listing not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to toggle status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_deep_analysis(request):
    """
    Run deep Pass 2 analysis on manually selected listings.
    
    Body:
        {
            "listing_ids": [1, 2, 3],
            "scan_batch_id": "optional_scan_id"
        }
    """
    import asyncio
    from apps.listings.models import Listing
    from .services.two_pass_analysis_service import TwoPassAnalysisService
    from apps.shared.services.notification_service import NotificationService
    
    listing_ids = request.data.get('listing_ids', [])
    scan_batch_id = request.data.get('scan_batch_id')
    
    if not listing_ids:
        return Response(
            {'error': 'listing_ids is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if system is busy
        if SystemTask.is_busy():
            return Response(
                {'error': 'System is busy with another task'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Get scan batch if provided
        scan_batch = None
        if scan_batch_id:
            try:
                scan_batch = ScanBatch.objects.get(scan_id=scan_batch_id)
            except ScanBatch.DoesNotExist:
                pass
        
        # Create task for tracking
        task = SystemTask.objects.create(
            task_type='analysis',
            status='running',
            current_step='analyzing',
            progress_percent=10,
            progress_message=f'Analyzing {len(listing_ids)} listings...',
            scan_batch=scan_batch
        )
        
        try:
            # Run deep analysis
            service = TwoPassAnalysisService()
            
            # Run async function
            result = asyncio.run(service.analyze_selected_listings(
                listing_ids=listing_ids,
                scan_batch=scan_batch
            ))
            
            if result['success']:
                task.update_progress('notifying', 90, f"Sending notifications...")
                
                # Send email notifications for NOTIFY recommendations
                notify_count = result.get('notifications', 0)
                emails_sent = False
                
                if notify_count > 0:
                    try:
                        # Get analyzed listings with NOTIFY recommendation
                        # Note: investigation_result stores 'notify', 'ignore', 'pending'
                        notify_listings = Listing.objects.filter(
                            listing_idx__in=listing_ids,
                            investigation_result__iexact='notify'
                        )
                        
                        # Get scanner objects for these listings
                        scanner_ids = set(l.scanner_id for l in notify_listings if l.scanner_id)
                        scanners_map = {}
                        if scanner_ids:
                            from .models import ActiveScanner
                            scanners = ActiveScanner.objects.filter(id__in=scanner_ids)
                            scanners_map = {s.id: s for s in scanners}
                        
                        # Group by scanner for per-scanner email lists
                        scanner_notifications = {}
                        for listing in notify_listings:
                            scanner_id = listing.scanner_id or 'default'
                            scanner = scanners_map.get(scanner_id)
                            
                            if scanner_id not in scanner_notifications:
                                scanner_notifications[scanner_id] = {
                                    'scanner': scanner,
                                    'listings': []
                                }
                            
                            # Build notification item from analysis_metadata
                            analysis = listing.analysis_metadata or {}
                            
                            # Get image - prefer img field, fallback to additional_images
                            img_url = listing.img
                            if not img_url and listing.additional_images:
                                img_url = listing.additional_images[0] if listing.additional_images else None
                            
                            # Extract confidence and summary from analysis_metadata
                            confidence = analysis.get('confidence', listing.triage_confidence or 0)
                            summary = analysis.get('summary', listing.triage_reason or 'Deal found!')
                            
                            scanner_notifications[scanner_id]['listings'].append({
                                'title': listing.title,
                                'price': listing.price,
                                'location': listing.location,
                                'url': listing.url,
                                'img': img_url,
                                'confidence': confidence,
                                'summary': summary,
                                'scanner': scanner.query if scanner else 'Unknown',
                                'analysis': analysis
                            })
                        
                        # Send notifications grouped by scanner
                        notification_service = NotificationService()
                        for scanner_id, data in scanner_notifications.items():
                            scanner = data['scanner']
                            listings_data = data['listings']
                            
                            # Get scanner's email list (or use default)
                            scanner_emails = None
                            if scanner and hasattr(scanner, 'notification_emails') and scanner.notification_emails:
                                scanner_emails = scanner.notification_emails
                            
                            if listings_data:
                                notification_service.notify_deep_analysis_results(
                                    notify_items=listings_data,
                                    recipient_emails=scanner_emails
                                )
                        
                        emails_sent = True
                        print(f"✓ Sent email notifications for {len(list(notify_listings))} NOTIFY listings")
                        
                    except Exception as e:
                        print(f"⚠️ Failed to send notifications: {e}")
                        import traceback
                        traceback.print_exc()
                        # Don't fail the whole request if notifications fail
                
                task.update_progress('complete', 100, f"{result['analyzed']} analyzed, {notify_count} notify" + (" (emails sent)" if emails_sent else ""))
                task.complete(success=True)
                
                return Response({
                    'success': True,
                    'analyzed': result['analyzed'],
                    'notifications': result['notifications'],
                    'emails_sent': emails_sent,
                    'results': result.get('results', []),
                    'message': f"Analyzed {result['analyzed']} listings" + (f", sent {notify_count} notifications" if emails_sent else "")
                })
            else:
                task.fail(result.get('error', 'Analysis failed'))
                return Response(
                    {'error': result.get('error', 'Analysis failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            task.fail(str(e))
            raise
        
    except Exception as e:
        return Response(
            {'error': f'Failed to run deep analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rerun_triage(request, scan_id):
    """
    Re-run AI triage on all listings from a scan batch.
    Useful for testing prompt changes or re-evaluating listings.
    
    URL: /api/scan-batches/{scan_id}/rerun-triage/
    """
    import asyncio
    from .services.two_pass_analysis_service import TwoPassAnalysisService
    
    try:
        # Get the scan batch
        try:
            scan_batch = ScanBatch.objects.get(scan_id=scan_id)
        except ScanBatch.DoesNotExist:
            return Response(
                {'error': 'Scan batch not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if system is busy
        if SystemTask.is_busy():
            return Response(
                {'error': 'System is busy with another task'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Create task for tracking
        task = SystemTask.objects.create(
            task_type='analysis',
            status='running',
            current_step='triaging',
            progress_percent=10,
            progress_message='Re-running AI triage...',
            scan_batch=scan_batch
        )
        
        try:
            # Run triage
            service = TwoPassAnalysisService()
            result = asyncio.run(service.rerun_triage(scan_batch))
            
            if result['success']:
                task.update_progress('complete', 100, f"{result['stats'].get('triaged_interesting', 0)} marked interesting")
                task.complete(success=True)
                
                return Response({
                    'success': True,
                    'total_listings': result['stats'].get('total_listings', 0),
                    'triaged_interesting': result['stats'].get('triaged_interesting', 0),
                    'message': result.get('message', 'Triage re-run complete')
                })
            else:
                task.fail(result.get('error', 'Triage failed'))
                return Response(
                    {'error': result.get('error', 'Triage re-run failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            task.fail(str(e))
            raise
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to re-run triage: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_scan_notifications(request, scan_id):
    """
    Manually send email notifications for all NOTIFY listings in a scan batch.
    
    URL: /api/scan-batches/{scan_id}/send-notifications/
    """
    from apps.listings.models import Listing
    from apps.shared.services.notification_service import NotificationService
    
    try:
        # Get the scan batch
        try:
            scan_batch = ScanBatch.objects.get(scan_id=scan_id)
        except ScanBatch.DoesNotExist:
            return Response(
                {'error': 'Scan batch not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get listings with NOTIFY recommendation
        notify_listings = Listing.objects.filter(
            scan_identifier=scan_id,
            investigation_result__iexact='notify'
        )
        
        notify_count = notify_listings.count()
        
        if notify_count == 0:
            return Response({
                'success': True,
                'sent': 0,
                'message': 'No NOTIFY listings to send'
            })
        
        # Get scanner objects for these listings
        scanner_ids = set(l.scanner_id for l in notify_listings if l.scanner_id)
        scanners_map = {}
        if scanner_ids:
            scanners = ActiveScanner.objects.filter(id__in=scanner_ids)
            scanners_map = {s.id: s for s in scanners}
        
        # Group by scanner for per-scanner email lists
        scanner_notifications = {}
        for listing in notify_listings:
            scanner_id = listing.scanner_id or 'default'
            scanner = scanners_map.get(scanner_id)
            
            if scanner_id not in scanner_notifications:
                scanner_notifications[scanner_id] = {
                    'scanner': scanner,
                    'listings': []
                }
            
            # Build notification item from analysis_metadata
            analysis = listing.analysis_metadata or {}
            
            # Get image - prefer img field, fallback to additional_images
            img_url = listing.img
            if not img_url and listing.additional_images:
                img_url = listing.additional_images[0] if listing.additional_images else None
            
            # Extract confidence and summary from analysis_metadata
            confidence = analysis.get('confidence', listing.triage_confidence or 0)
            summary = analysis.get('summary', listing.triage_reason or 'Deal found!')
            
            scanner_notifications[scanner_id]['listings'].append({
                'title': listing.title,
                'price': listing.price,
                'location': listing.location,
                'url': listing.url,
                'img': img_url,
                'confidence': confidence,
                'summary': summary,
                'scanner': scanner.query if scanner else 'Unknown',
                'analysis': analysis
            })
        
        # Send notifications grouped by scanner
        notification_service = NotificationService()
        emails_sent = 0
        
        for scanner_id, data in scanner_notifications.items():
            scanner = data['scanner']
            listings_data = data['listings']
            
            # Get scanner's email list (or use default)
            scanner_emails = None
            if scanner and hasattr(scanner, 'notification_emails') and scanner.notification_emails:
                scanner_emails = scanner.notification_emails
            
            if listings_data:
                result = notification_service.notify_deep_analysis_results(
                    notify_items=listings_data,
                    recipient_emails=scanner_emails
                )
                if result.get('email', False):
                    emails_sent += len(listings_data)
        
        print(f"✓ Sent notifications for {emails_sent} NOTIFY listings from scan {scan_id}")
        
        return Response({
            'success': True,
            'sent': emails_sent,
            'total_notify': notify_count,
            'message': f'Sent notifications for {emails_sent} listings'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to send notifications: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TASK STATUS & SCANNER SETTINGS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_task(request):
    """
    Get the currently running system task, if any.
    Used by the header to show global task status.
    
    URL: /api/scanners/task/current/
    """
    try:
        current_task = SystemTask.get_current_task()
        
        if current_task:
            serializer = SystemTaskSerializer(current_task)
            return Response({
                'busy': True,
                'task': serializer.data
            })
        else:
            return Response({
                'busy': False,
                'task': None
            })
            
    except Exception as e:
        return Response(
            {'error': f'Failed to get current task: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_stuck_tasks(request):
    """
    Clear any stuck/stale tasks.
    
    URL: /api/scanners/task/clear/
    """
    try:
        # First try to clean up stale tasks (running > 30 min)
        stale_count = SystemTask.cleanup_stale_tasks()
        
        # If force=true, cancel all running tasks
        force = request.data.get('force', False)
        cancelled_count = 0
        if force:
            cancelled_count = SystemTask.cancel_all_running()
        
        return Response({
            'success': True,
            'stale_cleaned': stale_count,
            'cancelled': cancelled_count,
            'message': f'Cleaned {stale_count} stale, cancelled {cancelled_count} running tasks'
        })
            
    except Exception as e:
        return Response(
            {'error': f'Failed to clear tasks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_history(request):
    """
    Get recent task history.
    
    URL: /api/scanners/task/history/
    """
    try:
        limit = int(request.query_params.get('limit', 10))
        tasks = SystemTask.objects.all()[:limit]
        serializer = SystemTaskSerializer(tasks, many=True)
        return Response({
            'tasks': serializer.data
        })
            
    except Exception as e:
        return Response(
            {'error': f'Failed to get task history: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scanner_settings(request):
    """
    Get scanner settings.
    
    URL: /api/scanners/settings/
    """
    try:
        settings = ScannerSettings.get_settings()
        serializer = ScannerSettingsSerializer(settings)
        return Response(serializer.data)
            
    except Exception as e:
        return Response(
            {'error': f'Failed to get scanner settings: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_scanner_settings(request):
    """
    Update scanner settings.
    
    URL: /api/scanners/settings/
    """
    try:
        settings = ScannerSettings.get_settings()
        
        # Update allowed fields
        if 'interval_minutes' in request.data:
            settings.interval_minutes = request.data['interval_minutes']
        if 'randomize_order' in request.data:
            settings.randomize_order = request.data['randomize_order']
        
        settings.save()
        
        serializer = ScannerSettingsSerializer(settings)
        return Response(serializer.data)
            
    except Exception as e:
        return Response(
            {'error': f'Failed to update scanner settings: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_scanner_mode(request):
    """
    Switch between auto and manual mode.
    
    URL: /api/scanners/settings/mode/
    
    Body: { "mode": "auto" | "manual" }
    """
    try:
        mode = request.data.get('mode')
        
        if mode not in ['auto', 'manual']:
            return Response(
                {'error': 'Mode must be "auto" or "manual"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if system is busy
        if SystemTask.is_busy():
            return Response(
                {'error': 'Cannot change mode while a task is running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settings = ScannerSettings.get_settings()
        settings.mode = mode
        
        if mode == 'manual':
            # Disable auto mode
            settings.auto_enabled = False
            settings.next_scan_at = None
            # Stop the continuous scanner if running
            try:
                ScannerControlService.stop_scanner()
            except:
                pass
        
        settings.save()
        
        serializer = ScannerSettingsSerializer(settings)
        return Response({
            'success': True,
            'message': f'Switched to {mode} mode',
            'settings': serializer.data
        })
            
    except Exception as e:
        return Response(
            {'error': f'Failed to set scanner mode: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_auto_scan(request):
    """
    Enable automatic scanning.
    
    URL: /api/scanners/settings/auto/enable/
    """
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Check if system is busy
        if SystemTask.is_busy():
            return Response(
                {'error': 'Cannot enable auto mode while a task is running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settings = ScannerSettings.get_settings()
        settings.mode = 'auto'
        settings.auto_enabled = True

        # Calculate next scan time — immediate first scan, then interval-based
        interval = request.data.get('interval_minutes', settings.interval_minutes)
        settings.interval_minutes = interval
        settings.next_scan_at = timezone.now()  # immediate — worker picks up within 5s
        
        settings.save()

        serializer = ScannerSettingsSerializer(settings)
        return Response({
            'success': True,
            'message': 'Auto scanning enabled. Worker will pick up shortly.',
            'settings': serializer.data,
        })
            
    except Exception as e:
        return Response(
            {'error': f'Failed to enable auto scan: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_auto_scan(request):
    """
    Disable automatic scanning.
    
    URL: /api/scanners/settings/auto/disable/
    """
    try:
        settings = ScannerSettings.get_settings()
        settings.auto_enabled = False
        settings.next_scan_at = None
        settings.save()

        serializer = ScannerSettingsSerializer(settings)
        return Response({
            'success': True,
            'message': 'Auto scanning disabled. Worker will idle after current scan.',
            'settings': serializer.data,
        })
            
    except Exception as e:
        return Response(
            {'error': f'Failed to disable auto scan: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_manual_scan(request):
    """
    Run a single manual scan (for testing/validation).
    
    URL: /api/scanners/manual-scan/
    
    This is a more controlled version of single-scan that:
    - Checks if system is busy
    - Runs the scan (which creates its own SystemTask)
    - Updates scanner settings with last scan time
    """
    from django.utils import timezone
    
    try:
        settings = ScannerSettings.get_settings()
        
        # Check mode
        if settings.auto_enabled:
            return Response(
                {'error': 'Cannot run manual scan while auto mode is enabled. Disable auto mode first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if busy
        if SystemTask.is_busy():
            current_task = SystemTask.get_current_task()
            return Response({
                'error': 'System is busy with another task',
                'current_task': SystemTaskSerializer(current_task).data if current_task else None
            }, status=status.HTTP_409_CONFLICT)
        
        # Trigger the worker by setting next_scan_at = now
        settings.next_scan_at = timezone.now()
        settings.save()

        return Response({
            'success': True,
            'message': 'Scan triggered. Worker will start within 30 seconds.',
        })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to run manual scan: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AI AGENT BUILDER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_agent_prompt(request):
    """
    Generate triage and analysis prompts from a natural language description.
    
    URL: /api/agents/generate-prompt/
    
    Body:
        {
            "description": "I want to find undervalued vintage guitars..."
        }
    
    Returns:
        {
            "suggested_name": "Vintage Guitar Specialist",
            "suggested_slug": "vintage-guitars",
            "suggested_icon": "🎸",
            "suggested_description": "...",
            "triage_prompt": "...",
            "analysis_prompt": "...",
            "token_usage": { ... }
        }
    """
    from .services.agent_builder_service import AgentBuilderService
    
    description = request.data.get('description')
    if not description:
        return Response(
            {'error': 'description is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        builder = AgentBuilderService()
        result = builder.generate_prompts(description)
        return Response(result)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to generate prompts: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refine_agent_prompt(request):
    """
    Refine existing prompts based on user feedback.
    
    URL: /api/agents/refine-prompt/
    
    Body:
        {
            "current_triage_prompt": "...",
            "current_analysis_prompt": "...",
            "feedback": "Make it more aggressive about flagging deals under $200"
        }
    
    Returns:
        {
            "triage_prompt": "...",
            "analysis_prompt": "...",
            "changes_summary": "...",
            "token_usage": { ... }
        }
    """
    from .services.agent_builder_service import AgentBuilderService
    
    current_triage = request.data.get('current_triage_prompt')
    current_analysis = request.data.get('current_analysis_prompt')
    feedback = request.data.get('feedback')
    
    if not all([current_triage, current_analysis, feedback]):
        return Response(
            {'error': 'current_triage_prompt, current_analysis_prompt, and feedback are all required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        builder = AgentBuilderService()
        result = builder.refine_prompts(current_triage, current_analysis, feedback)
        return Response(result)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to refine prompts: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggest_agent_queries(request, slug):
    """
    Suggest search queries for an agent based on its prompts.
    
    URL: /api/agents/<slug>/suggest-queries/
    
    Returns:
        { "suggestions": ["query1", "query2", "query3"] }
    """
    from .services.agent_builder_service import AgentBuilderService
    
    try:
        builder = AgentBuilderService()
        result = builder.suggest_queries(slug)
        return Response(result)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to suggest queries: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_listing_url(request, slug):
    """
    Scrape a single Facebook Marketplace listing by URL, run agent analysis,
    save the listing, and return the result.
    
    URL: /api/agents/<slug>/analyze-url/
    
    Body:
        { "url": "https://www.facebook.com/marketplace/item/123456/" }
    
    Returns:
        {
            "listing_id": 123,
            "title": "...",
            "price": "...",
            "location": "...",
            "description": "...",
            "images": [...],
            "analysis": { ... }
        }
    """
    import re
    from apps.listings.models import Listing
    from .services.llm_analysis_service import LLMAnalysisService
    from .services.agents import get_agent
    
    url = request.data.get('url', '').strip()
    
    # Validate URL
    if not url:
        return Response(
            {'error': 'URL is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not re.search(r'facebook\.com/marketplace/item/\d+', url):
        return Response(
            {'error': 'URL must be a Facebook Marketplace listing (facebook.com/marketplace/item/...)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify agent exists
    try:
        agent_record = Agent.objects.get(slug=slug, enabled=True)
    except Agent.DoesNotExist:
        return Response(
            {'error': f'Agent "{slug}" not found or disabled'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Step 1: Scrape the listing
        llm_service = LLMAnalysisService()
        details = llm_service._extract_full_details(url)
        
        if details['status'] != 'success':
            return Response(
                {'error': f'Failed to scrape listing: {details.get("error", details["status"])}'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        title = details.get('title', '') or 'Untitled Listing'
        price = details.get('price', '') or 'No price'
        location = details.get('location', '') or 'Unknown'
        description = details.get('description', '')
        image_urls = details.get('images', [])
        image_bytes = details.get('image_bytes', [])
        
        # Step 2: Save listing to database
        listing = Listing.objects.create(
            title=title,
            price=price,
            location=location,
            url=url,
            description=description,
            full_description=description,
            img=image_urls[0] if image_urls else '',
            additional_images=image_urls,
            query='manual-url-analysis',
            search_title='Manual URL Analysis',
            scan_identifier='manual-url-analysis',
            scanner_id=None,
            search_location=location,
            needs_investigation=True,
            investigation_completed=False,
            watchlist=False,
        )
        
        # Step 3: Run agent analysis
        agent = get_agent(slug)
        listing_data = {
            'title': title,
            'price': price,
            'location': location,
            'url': url,
            'description': description,
        }
        
        analysis = agent.analyze(listing_data=listing_data, images=image_bytes)
        
        # Step 4: Save analysis result on the listing
        listing.analysis_metadata = analysis
        listing.investigation_completed = True
        recommendation = analysis.get('recommendation', 'IGNORE')
        listing.investigation_result = recommendation.lower()
        listing.save(update_fields=['analysis_metadata', 'investigation_completed', 'investigation_result'])
        
        return Response({
            'listing_id': listing.listing_idx,
            'title': title,
            'price': price,
            'location': location,
            'description': description[:500] if description else '',
            'images': image_urls,
            'analysis': analysis,
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
