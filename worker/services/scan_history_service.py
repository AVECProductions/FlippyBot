from datetime import datetime
from typing import Dict, Any, Optional
from django.utils import timezone

# Worker version: use absolute import (no relative ..models available here)
from apps.scanners.models import ScanHistory


class ScanHistoryService:
    """Service for managing scan history records."""

    @classmethod
    def create_scan_record(
        cls,
        scan_type: str,
        started_at: datetime,
        randomized: bool = False,
        interval_minutes: Optional[int] = None
    ) -> ScanHistory:
        """Create a new scan history record."""
        return ScanHistory.objects.create(
            scan_type=scan_type,
            status='success',  # Will be updated when scan completes
            started_at=started_at,
            completed_at=started_at,  # Will be updated when scan completes
            randomized=randomized,
            interval_minutes=interval_minutes
        )

    @classmethod
    def update_scan_success(
        cls,
        scan_record: ScanHistory,
        completed_at: datetime,
        stats: Dict[str, Any]
    ) -> ScanHistory:
        """Update scan record with successful completion data."""
        duration = (completed_at - scan_record.started_at).total_seconds()

        scan_record.status = 'success'
        scan_record.completed_at = completed_at
        scan_record.duration_seconds = duration
        scan_record.scanners_processed = stats.get('scanners_processed', 0)
        scan_record.total_listings_found = stats.get('listings_searched', 0)
        scan_record.new_listings_added = stats.get('new_listings_added', 0)
        scan_record.watchlist_items_added = stats.get('watchlist_items', 0)
        scan_record.error_count = 0
        scan_record.error_message = None

        scan_record.save()
        return scan_record

    @classmethod
    def update_scan_error(
        cls,
        scan_record: ScanHistory,
        completed_at: datetime,
        error_message: str,
        stats: Optional[Dict[str, Any]] = None
    ) -> ScanHistory:
        """Update scan record with error information."""
        duration = (completed_at - scan_record.started_at).total_seconds()

        scan_record.status = 'error'
        scan_record.completed_at = completed_at
        scan_record.duration_seconds = duration
        scan_record.error_message = error_message
        scan_record.error_count = 1

        # Update stats if available (partial success)
        if stats:
            scan_record.status = 'partial'
            scan_record.scanners_processed = stats.get('scanners_processed', 0)
            scan_record.total_listings_found = stats.get('listings_searched', 0)
            scan_record.new_listings_added = stats.get('new_listings_added', 0)
            scan_record.watchlist_items_added = stats.get('watchlist_items', 0)

        scan_record.save()
        return scan_record

    @classmethod
    def get_recent_scans(cls, limit: int = 10) -> list:
        """Get recent scan history records."""
        return list(ScanHistory.objects.all()[:limit])

    @classmethod
    def get_latest_scan(cls) -> Optional[ScanHistory]:
        """Get the most recent scan record."""
        return ScanHistory.objects.first()

    @classmethod
    def get_scan_stats_summary(cls) -> Dict[str, Any]:
        """Get summary statistics for recent scans."""
        recent_scans = ScanHistory.objects.all()[:10]

        if not recent_scans:
            return {
                'total_scans': 0,
                'successful_scans': 0,
                'failed_scans': 0,
                'latest_scan': None,
                'total_listings_found': 0,
                'total_watchlist_items': 0
            }

        successful_scans = [s for s in recent_scans if s.status == 'success']
        failed_scans = [s for s in recent_scans if s.status == 'error']

        latest_scan_data = None
        if recent_scans:
            latest = recent_scans[0]
            latest_scan_data = {
                'id': latest.id,
                'scan_type': latest.scan_type,
                'status': latest.status,
                'started_at': latest.started_at.isoformat(),
                'completed_at': latest.completed_at.isoformat(),
                'duration_seconds': latest.duration_seconds,
                'scanners_processed': latest.scanners_processed,
                'total_listings_found': latest.total_listings_found,
                'new_listings_added': latest.new_listings_added,
                'watchlist_items_added': latest.watchlist_items_added,
                'error_message': latest.error_message,
                'randomized': latest.randomized,
                'interval_minutes': latest.interval_minutes
            }

        return {
            'total_scans': len(recent_scans),
            'successful_scans': len(successful_scans),
            'failed_scans': len(failed_scans),
            'latest_scan': latest_scan_data,
            'total_listings_found': sum(s.total_listings_found for s in recent_scans),
            'total_watchlist_items': sum(s.watchlist_items_added for s in recent_scans)
        }
