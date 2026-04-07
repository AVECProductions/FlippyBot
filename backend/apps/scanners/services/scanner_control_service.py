import os
from typing import Dict, Any
from django.conf import settings
from .scanner_execution_service import ScannerExecutionService
from .scan_history_service import ScanHistoryService


class ScannerControlService:
    """Service class for high-level scanner control operations."""
    
    @classmethod
    def is_local_mode(cls) -> bool:
        """Check if Playwright scanning is enabled on this machine."""
        return getattr(settings, 'ENABLE_SCANNER', False)
    
    @classmethod
    def start_scanner(cls, interval: int = 20, randomize: bool = True) -> Dict[str, Any]:
        """Start continuous scanner."""
        return ScannerExecutionService.start_continuous_scanning(interval, randomize)
    
    @classmethod
    def stop_scanner(cls) -> Dict[str, Any]:
        """Stop continuous scanner."""
        return ScannerExecutionService.stop_continuous_scanning()
    
    @classmethod
    def get_scanner_status(cls) -> Dict[str, Any]:
        """Get scanner status."""
        return ScannerExecutionService.get_scanning_status()
    
    @classmethod
    def run_single_scan(cls, randomize: bool = True) -> Dict[str, Any]:
        """Run a single scan."""
        return ScannerExecutionService.run_single_scan(randomize)
    
    @classmethod
    def get_scan_history(cls) -> Dict[str, Any]:
        """Get recent scan history."""
        if not cls.is_local_mode():
            raise PermissionError('Scanner history is only available in local development mode.')
        
        recent_scans = ScanHistoryService.get_recent_scans(limit=10)
        stats_summary = ScanHistoryService.get_scan_stats_summary()
        
        return {
            'recent_scans': [
                {
                    'id': scan.id,
                    'scan_type': scan.scan_type,
                    'status': scan.status,
                    'started_at': scan.started_at.isoformat(),
                    'completed_at': scan.completed_at.isoformat(),
                    'duration_seconds': scan.duration_seconds,
                    'scanners_processed': scan.scanners_processed,
                    'total_listings_found': scan.total_listings_found,
                    'new_listings_added': scan.new_listings_added,
                    'watchlist_items_added': scan.watchlist_items_added,
                    'error_message': scan.error_message,
                    'randomized': scan.randomized,
                    'interval_minutes': scan.interval_minutes
                }
                for scan in recent_scans
            ],
            'summary': stats_summary
        }
