from django.core.management.base import BaseCommand
from apps.scanners.services.scanner_execution_service import ScannerExecutionService


class Command(BaseCommand):
    """Management command that delegates to ScannerExecutionService."""
    
    help = 'Runs the FlippyBot scanner - thin wrapper around ScannerExecutionService'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=20,
            help='Interval between scans in minutes (default: 20)',
        )
        parser.add_argument(
            '--single-run',
            action='store_true',
            help='Run once and exit instead of continuous scanning',
        )
        parser.add_argument(
            '--randomize',
            action='store_true',
            help='Randomize scanner execution order',
        )

    def handle(self, *args, **options):
        """Handle command execution by delegating to service layer."""
        interval_minutes = options['interval']
        single_run = options['single_run']
        randomize = options['randomize']

        self.stdout.write(
            self.style.SUCCESS(f'Starting FlippyBot scanner (interval: {interval_minutes} minutes)')
        )

        try:
            if single_run:
                result = ScannerExecutionService.run_single_scan(randomize)
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(result['message']))
                else:
                    self.stdout.write(self.style.ERROR(result['message']))
            else:
                # Start continuous scanning - this will run until interrupted
                result = ScannerExecutionService.start_continuous_scanning(interval_minutes, randomize)
                self.stdout.write(self.style.SUCCESS(result['message']))
                
                # Keep the command alive while scanning runs
                try:
                    import time
                    while True:
                        time.sleep(1)
                        status = ScannerExecutionService.get_scanning_status()
                        if not status['running']:
                            break
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("Stopping scanner..."))
                    stop_result = ScannerExecutionService.stop_continuous_scanning()
                    self.stdout.write(self.style.SUCCESS(stop_result['message']))
                    
        except PermissionError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except RuntimeError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
