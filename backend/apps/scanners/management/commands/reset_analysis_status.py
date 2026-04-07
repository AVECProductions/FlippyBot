"""
Management command to reset stuck analysis statuses.
Useful when analysis gets interrupted by server restarts.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta

from apps.scanners.models import ScanBatch, AnalysisProgress


class Command(BaseCommand):
    help = 'Reset stuck analysis statuses to allow restarting analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scan-id',
            type=str,
            help='Specific scan ID to reset (optional)',
        )
        parser.add_argument(
            '--all-stuck',
            action='store_true',
            help='Reset all batches stuck in "in_progress" status',
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=60,
            help='Reset analyses stuck for more than X minutes (default: 60)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Analysis Status Reset Tool ===')
        )

        if options['scan_id']:
            # Reset specific scan batch
            try:
                scan_batch = ScanBatch.objects.get(scan_id=options['scan_id'])
                self.reset_scan_batch(scan_batch)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Reset analysis status for scan {scan_batch.scan_id}")
                )
            except ScanBatch.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Scan batch {options['scan_id']} not found")
                )
                return

        elif options['all_stuck']:
            # Reset all stuck analyses
            cutoff_time = timezone.now() - timedelta(minutes=options['older_than'])
            
            stuck_batches = ScanBatch.objects.filter(
                analysis_status='in_progress',
                analysis_started_at__lt=cutoff_time
            )
            
            if not stuck_batches.exists():
                self.stdout.write("No stuck analyses found.")
                return
            
            self.stdout.write(f"Found {stuck_batches.count()} stuck analyses:")
            for batch in stuck_batches:
                self.stdout.write(f"  - {batch.scan_id} (started: {batch.analysis_started_at})")
            
            confirm = input(f"\nReset {stuck_batches.count()} stuck analyses? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
            
            for batch in stuck_batches:
                self.reset_scan_batch(batch)
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Reset {stuck_batches.count()} stuck analyses")
            )

        else:
            # Show current status
            self.show_analysis_status(options['older_than'])

    def reset_scan_batch(self, scan_batch):
        """Reset a scan batch's analysis status."""
        # Reset the scan batch status
        scan_batch.analysis_status = 'pending'
        scan_batch.analysis_started_at = None
        scan_batch.analysis_completed_at = None
        scan_batch.save()
        
        # Reset progress tracking if it exists
        try:
            progress = AnalysisProgress.objects.get(scan_batch=scan_batch)
            progress.processed_items = 0
            progress.current_item_title = ''
            progress.current_status = 'reset'
            progress.save()
        except AnalysisProgress.DoesNotExist:
            pass

    def show_analysis_status(self, older_than_minutes):
        """Show current analysis status for all batches."""
        self.stdout.write("\n=== Current Analysis Status ===")
        
        # Recent batches
        recent_batches = ScanBatch.objects.order_by('-started_at')[:10]
        
        if not recent_batches.exists():
            self.stdout.write("No scan batches found.")
            return
        
        cutoff_time = timezone.now() - timedelta(minutes=older_than_minutes)
        
        for batch in recent_batches:
            status_color = self.style.SUCCESS
            if batch.analysis_status == 'in_progress':
                if batch.analysis_started_at and batch.analysis_started_at < cutoff_time:
                    status_color = self.style.ERROR  # Stuck
                else:
                    status_color = self.style.WARNING  # Currently running
            elif batch.analysis_status == 'failed':
                status_color = self.style.ERROR
            
            status_text = f"{batch.scan_id} - {batch.analysis_status}"
            if batch.analysis_started_at:
                status_text += f" (started: {batch.analysis_started_at})"
            
            self.stdout.write(status_color(f"  {status_text}"))
        
        # Show stuck analyses
        stuck_batches = ScanBatch.objects.filter(
            analysis_status='in_progress',
            analysis_started_at__lt=cutoff_time
        )
        
        if stuck_batches.exists():
            self.stdout.write(f"\n⚠️  Found {stuck_batches.count()} analyses stuck for more than {older_than_minutes} minutes")
            self.stdout.write("Use --all-stuck to reset them, or --scan-id <id> to reset a specific one")
        else:
            self.stdout.write(f"\n✓ No analyses stuck for more than {older_than_minutes} minutes")


