"""
Shared views for notification testing and management.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .services import NotificationService
import logging


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok'})

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Change to IsAuthenticated in production
def test_notifications(request):
    """
    Test notification channels with sample data.
    
    Body can contain:
    {
        "channels": ["email"],  # Optional: specific channels to test
        "send_sample": true     # Optional: send sample notification instead of just testing config
    }
    """
    try:
        notification_service = NotificationService()
        channels = request.data.get('channels', None)
        send_sample = request.data.get('send_sample', False)
        
        if send_sample:
            # Send sample notification
            sample_items = [
                {
                    'scanner': 'Test Scanner in Test City',
                    'title': 'Sample Test Listing - iPhone 15 Pro',
                    'location': 'Test Location, CO',
                    'price': '$999',
                    'img': 'https://via.placeholder.com/150x150.png?text=Test+Image',
                    'url': 'https://facebook.com/marketplace/test'
                },
                {
                    'scanner': 'Test Scanner in Test City',
                    'title': 'Another Test Item - MacBook Pro',
                    'location': 'Another Location, CO',
                    'price': '$1,299',
                    'img': 'https://via.placeholder.com/150x150.png?text=Test+Image+2',
                    'url': 'https://facebook.com/marketplace/test2'
                }
            ]
            
            results = notification_service.notify_new_watchlist_items(sample_items, channels)
            return Response({
                'success': True,
                'message': 'Sample notification sent',
                'results': results,
                'items_sent': len(sample_items)
            })
        else:
            # Just test configuration
            results = notification_service.test_notification_channels(channels)
            return Response({
                'success': True,
                'message': 'Notification channel tests completed',
                'results': results,
                'available_channels': notification_service.get_available_channels()
            })
            
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Change to IsAuthenticated in production
def notification_status(request):
    """Get status of notification channels."""
    try:
        notification_service = NotificationService()
        available_channels = notification_service.get_available_channels()
        
        channel_status = {}
        for channel in available_channels:
            channel_status[channel] = notification_service.is_channel_enabled(channel)
        
        return Response({
            'success': True,
            'available_channels': available_channels,
            'channel_status': channel_status
        })
        
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
