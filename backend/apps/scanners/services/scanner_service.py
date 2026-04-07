from typing import List, Optional
from django.db import transaction
from ..models import ActiveScanner, Location, ScannerLocationMapping


class ScannerService:
    """Service class for scanner-related business logic."""
    
    @staticmethod
    def create_scanner_with_locations(scanner_data: dict, location_ids: List[int]) -> ActiveScanner:
        """Create a new scanner and associate it with locations."""
        with transaction.atomic():
            # Create the scanner
            scanner = ActiveScanner.objects.create(**scanner_data)
            
            # Create location mappings
            for location_id in location_ids:
                try:
                    location = Location.objects.get(id=location_id)
                    ScannerLocationMapping.objects.create(
                        scanner=scanner,
                        location=location,
                        is_active=True
                    )
                except Location.DoesNotExist:
                    continue
            
            return scanner
    
    @staticmethod
    def update_scanner_locations(scanner: ActiveScanner, location_ids: List[int]) -> ActiveScanner:
        """Update scanner location mappings."""
        with transaction.atomic():
            # Deactivate all existing mappings
            ScannerLocationMapping.objects.filter(scanner=scanner).update(is_active=False)
            
            # Create or activate mappings for the provided location_ids
            for location_id in location_ids:
                try:
                    location = Location.objects.get(id=location_id)
                    mapping, created = ScannerLocationMapping.objects.get_or_create(
                        scanner=scanner,
                        location=location,
                        defaults={'is_active': True}
                    )
                    if not created:
                        mapping.is_active = True
                        mapping.save()
                except Location.DoesNotExist:
                    continue
            
            return scanner
    
    @staticmethod
    def get_scanner_locations(scanner_id: int) -> List[ScannerLocationMapping]:
        """Get all active location mappings for a scanner."""
        return ScannerLocationMapping.objects.filter(
            scanner_id=scanner_id, 
            is_active=True
        ).select_related('location')
    
    @staticmethod
    def toggle_scanner_status(scanner_id: int) -> Optional[ActiveScanner]:
        """Toggle scanner status between running and stopped."""
        try:
            scanner = ActiveScanner.objects.get(id=scanner_id)
            scanner.status = 'running' if scanner.status == 'stopped' else 'stopped'
            scanner.save()
            return scanner
        except ActiveScanner.DoesNotExist:
            return None
    
    @staticmethod
    def get_active_scanners() -> List[ActiveScanner]:
        """Get all scanners with status 'running'."""
        return ActiveScanner.objects.filter(status='running').prefetch_related('locations')
    
    @staticmethod
    def create_location(name: str, marketplace_url_slug: str) -> Location:
        """Create a new location."""
        return Location.objects.create(
            name=name,
            marketplace_url_slug=marketplace_url_slug
        )

