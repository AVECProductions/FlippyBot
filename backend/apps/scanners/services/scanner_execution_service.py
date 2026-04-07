import os
import sys
import time
import random
import logging
import threading
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any

from .flippy_scanner_service import FlippyScannerOrchestrator
from .scan_history_service import ScanHistoryService


class ScannerExecutionService:
    """Service for executing the actual scanning logic."""
    
    _scanning_thread: Optional[threading.Thread] = None
    _stop_scanning = False
    
    @classmethod
    def is_local_mode_enabled(cls) -> bool:
        """Check if Playwright scanning is enabled on this machine."""
        return getattr(settings, 'ENABLE_SCANNER', False)
    
    @classmethod
    def setup_logging(cls):
        """Configure logging for scanner operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler("scanner.log", encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True
        )
    
    @classmethod
    def run_single_scan(cls, randomize: bool = False) -> Dict[str, Any]:
        """Execute a single scan operation."""
        if not cls.is_local_mode_enabled():
            raise PermissionError('Scanner can only be run in local development mode.')
        
        cls.setup_logging()
        
        # Create scan history record
        started_at = timezone.now()
        scan_record = ScanHistoryService.create_scan_record(
            scan_type='single',
            started_at=started_at,
            randomized=randomize
        )
        
        completed_at = None
        result = None
        
        try:
            logging.info("Starting single scan...")
            
            # Use our new scanner service
            orchestrator = FlippyScannerOrchestrator()
            result = orchestrator.run_all_scanners(randomize=randomize, single_run=True)
            
            completed_at = timezone.now()
            
            if result['success']:
                logging.info(f"Scan completed: {result['message']}")
                logging.info(f"Stats: {result['stats']}")
                
                # Update scan record with success
                ScanHistoryService.update_scan_success(
                    scan_record, completed_at, result['stats']
                )
                
                return {
                    'success': True,
                    'message': result['message'],
                    'stats': result['stats'],
                    'timestamp': completed_at.isoformat()
                }
            else:
                logging.error(f"Scan failed: {result['message']}")
                
                # Update scan record with error
                ScanHistoryService.update_scan_error(
                    scan_record, completed_at, result['message']
                )
                
                return {
                    'success': False,
                    'message': result['message'],
                    'timestamp': completed_at.isoformat()
                }
            
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            logging.error(error_msg)
            
            if completed_at is None:
                completed_at = timezone.now()
            
            ScanHistoryService.update_scan_error(
                scan_record, completed_at, error_msg
            )
            
            return {
                'success': False,
                'message': error_msg,
                'timestamp': completed_at.isoformat()
            }
        
        finally:
            # Ensure scan record is updated even if there was an unexpected interruption
            if completed_at is None:
                completed_at = timezone.now()
                error_msg = "Scan was interrupted unexpectedly"
                logging.warning(error_msg)
                
                try:
                    ScanHistoryService.update_scan_error(
                        scan_record, completed_at, error_msg
                    )
                except Exception as cleanup_error:
                    logging.error(f"Failed to update scan record during cleanup: {cleanup_error}")
    
    @classmethod
    def start_continuous_scanning(cls, interval_minutes: int = 20, randomize: bool = False) -> Dict[str, Any]:
        """Start continuous scanning in a background thread."""
        if not cls.is_local_mode_enabled():
            raise PermissionError('Scanner can only be started in local development mode.')
        
        if cls._scanning_thread and cls._scanning_thread.is_alive():
            raise RuntimeError('Scanner is already running')
        
        cls._stop_scanning = False
        cls._scanning_thread = threading.Thread(
            target=cls._continuous_scan_worker,
            args=(interval_minutes, randomize),
            daemon=True
        )
        cls._scanning_thread.start()
        
        return {
            'success': True,
            'message': f'Continuous scanning started with {interval_minutes} minute intervals',
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def stop_continuous_scanning(cls) -> Dict[str, Any]:
        """Stop continuous scanning."""
        if not cls._scanning_thread or not cls._scanning_thread.is_alive():
            raise RuntimeError('Scanner is not running')
        
        cls._stop_scanning = True
        # Give it a moment to stop gracefully
        cls._scanning_thread.join(timeout=5)
        
        return {
            'success': True,
            'message': 'Continuous scanning stopped',
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def get_scanning_status(cls) -> Dict[str, Any]:
        """Get current scanning status."""
        is_running = cls._scanning_thread and cls._scanning_thread.is_alive()
        
        return {
            'available': cls.is_local_mode_enabled(),
            'running': is_running,
            'thread_id': cls._scanning_thread.ident if is_running else None,
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def _continuous_scan_worker(cls, interval_minutes: int, randomize: bool):
        """Worker function for continuous scanning thread."""
        cls.setup_logging()
        consecutive_errors = 0
        
        try:
            # Initialize our scanner orchestrator
            orchestrator = FlippyScannerOrchestrator()
            
            while not cls._stop_scanning:
                # Create scan history record for each continuous scan
                started_at = timezone.now()
                scan_record = ScanHistoryService.create_scan_record(
                    scan_type='continuous',
                    started_at=started_at,
                    randomized=randomize,
                    interval_minutes=interval_minutes
                )
                
                try:
                    logging.info(f"Starting scan at {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Use our new scanner service
                    result = orchestrator.run_all_scanners(randomize=randomize, single_run=False)
                    
                    completed_at = timezone.now()
                    
                    if result['success']:
                        logging.info(f"Scan completed: {result['message']}")
                        logging.info(f"Stats: {result['stats']}")
                        consecutive_errors = 0
                        
                        # Update scan record with success
                        ScanHistoryService.update_scan_success(
                            scan_record, completed_at, result['stats']
                        )
                    else:
                        consecutive_errors += 1
                        logging.error(f"Scan failed: {result['message']}")
                        
                        # Update scan record with error
                        ScanHistoryService.update_scan_error(
                            scan_record, completed_at, result['message']
                        )
                    
                except Exception as e:
                    consecutive_errors += 1
                    error_msg = f"Scan error: {str(e)}"
                    logging.error(error_msg)
                    
                    completed_at = timezone.now()
                    ScanHistoryService.update_scan_error(
                        scan_record, completed_at, error_msg
                    )
                
                if cls._stop_scanning:
                    break
                
                # Calculate delay with randomization and backoff
                delay_seconds = cls._calculate_delay(interval_minutes, consecutive_errors)
                next_run = datetime.now() + timedelta(seconds=delay_seconds)
                logging.info(f"Next scan scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep in chunks to allow for responsive stopping
                cls._interruptible_sleep(delay_seconds)
                
        except Exception as e:
            logging.error(f"Continuous scanning error: {str(e)}")
        finally:
            logging.info("Continuous scanning stopped")
    
    @classmethod
    def _calculate_delay(cls, interval_minutes: int, consecutive_errors: int) -> int:
        """Calculate delay between scans with randomization and backoff."""
        base_delay_seconds = interval_minutes * 60
        random_variance = random.randint(-300, 300)  # ±5 minutes
        delay_seconds = max(300, base_delay_seconds + random_variance)  # Minimum 5 minutes
        
        # Apply exponential backoff for consecutive errors
        if consecutive_errors > 0:
            backoff_multiplier = min(2 ** consecutive_errors, 4)
            delay_seconds *= backoff_multiplier
            logging.warning(f"Applying {backoff_multiplier}x backoff due to {consecutive_errors} consecutive errors")
        
        return delay_seconds
    
    @classmethod
    def _interruptible_sleep(cls, total_seconds: int):
        """Sleep in chunks to allow for responsive interruption."""
        chunk_size = 30  # seconds
        for _ in range(total_seconds // chunk_size):
            if cls._stop_scanning:
                break
            time.sleep(chunk_size)
        
        if not cls._stop_scanning:
            time.sleep(total_seconds % chunk_size)
    
# Removed _import_scanner_module as we now use our service directly
