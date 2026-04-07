"""
Notification orchestration service for FLIPPY.
Coordinates different notification channels (email, SMS, push, etc.).
"""
from typing import List, Dict, Any, Optional
from django.conf import settings
import logging

from .email_service import EmailNotificationService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main notification service that coordinates all notification channels.
    """
    
    def __init__(self):
        """Initialize notification service with available channels."""
        self.email_service = EmailNotificationService()
        self.channels = {
            'email': self.email_service,
            # Future: 'sms': SMSNotificationService(),
            # Future: 'push': PushNotificationService(),
        }
    
    def notify_new_watchlist_items(
        self, 
        watchlist_items: List[Dict[str, Any]], 
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send notifications for new watchlist items across specified channels.
        
        Args:
            watchlist_items: List of new watchlist items to notify about
            channels: List of notification channels to use. If None, uses all available.
            
        Returns:
            Dict mapping channel names to success status
        """
        if not watchlist_items:
            logger.info("No watchlist items to notify about.")
            return {}
        
        # Use all channels if none specified
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        
        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Unknown notification channel: {channel_name}")
                results[channel_name] = False
                continue
            
            try:
                service = self.channels[channel_name]
                
                if channel_name == 'email':
                    success = service.send_watchlist_notification(watchlist_items)
                else:
                    logger.warning(f"Channel {channel_name} not yet implemented")
                    success = False
                
                results[channel_name] = success
                
                if success:
                    logger.info(f"Successfully sent notification via {channel_name}")
                else:
                    logger.error(f"Failed to send notification via {channel_name}")
                    
            except Exception as e:
                logger.error(f"Error sending notification via {channel_name}: {e}")
                results[channel_name] = False
        
        return results
    
    def notify_deep_analysis_results(
        self,
        notify_items: List[Dict[str, Any]],
        channels: Optional[List[str]] = None,
        recipient_emails: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send notifications for AI deep analysis NOTIFY recommendations.
        
        This is called after the two-pass analysis when the AI recommends
        certain listings for notification (high-value deals identified).
        
        Args:
            notify_items: List of dictionaries containing analyzed listing information
                         with AI recommendations, confidence scores, and summaries.
                         Expected keys: listing_id, title, price, location, url, img,
                                       confidence, summary, scanner, analysis
            channels: List of notification channels to use. If None, uses all available.
            recipient_emails: Optional list of email addresses to send notifications to.
                            If not provided, uses the default from environment settings.
            
        Returns:
            Dict mapping channel names to success status
        """
        if not notify_items:
            logger.info("No AI NOTIFY recommendations to send.")
            return {}
        
        # Use all channels if none specified
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        
        recipient_info = f" to {recipient_emails}" if recipient_emails else " (using defaults)"
        logger.info(f"Sending notifications for {len(notify_items)} AI-recommended deals{recipient_info}")
        
        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Unknown notification channel: {channel_name}")
                results[channel_name] = False
                continue
            
            try:
                service = self.channels[channel_name]
                
                if channel_name == 'email':
                    # Use the new deep analysis email method with optional recipients
                    success = service.send_deep_analysis_notification(notify_items, recipient_emails)
                else:
                    logger.warning(f"Channel {channel_name} not yet implemented for deep analysis")
                    success = False
                
                results[channel_name] = success
                
                if success:
                    logger.info(f"Successfully sent deep analysis notification via {channel_name}")
                else:
                    logger.error(f"Failed to send deep analysis notification via {channel_name}")
                    
            except Exception as e:
                logger.error(f"Error sending deep analysis notification via {channel_name}: {e}")
                results[channel_name] = False
        
        return results
    
    def test_notification_channels(self, channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Test notification channels to verify they're working.
        
        Args:
            channels: List of channels to test. If None, tests all available.
            
        Returns:
            Dict mapping channel names to test success status
        """
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        
        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Unknown notification channel: {channel_name}")
                results[channel_name] = False
                continue
            
            try:
                service = self.channels[channel_name]
                
                if channel_name == 'email' and hasattr(service, 'test_email_configuration'):
                    success = service.test_email_configuration()
                else:
                    logger.warning(f"No test method available for channel: {channel_name}")
                    success = False
                
                results[channel_name] = success
                
            except Exception as e:
                logger.error(f"Error testing channel {channel_name}: {e}")
                results[channel_name] = False
        
        return results
    
    def get_available_channels(self) -> List[str]:
        """Get list of available notification channels."""
        return list(self.channels.keys())
    
    def is_channel_enabled(self, channel_name: str) -> bool:
        """Check if a specific notification channel is enabled and configured."""
        if channel_name not in self.channels:
            return False
        
        service = self.channels[channel_name]
        
        # Check if service has an 'enabled' attribute
        if hasattr(service, 'enabled'):
            return service.enabled
        
        return True  # Assume enabled if no explicit check available
