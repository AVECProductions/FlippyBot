from rest_framework import serializers
from .models import Listing, Keyword


class ListingSerializer(serializers.ModelSerializer):
    """Serializer for Listing model."""
    
    class Meta:
        model = Listing
        fields = [
            'listing_idx', 'price', 'title', 'location', 'description', 
            'distance', 'url', 'img', 'query', 'search_title', 
            'scanner_id', 'search_location', 'watchlist', 'created_at',
            # Phase 2 fields
            'scan_identifier', 'needs_investigation', 'investigation_completed',
            'investigation_result', 'full_description', 'additional_images',
            'seller_info', 'analysis_metadata',
            # AI Triage fields (Pass 1 results)
            'triage_interesting', 'triage_confidence', 'triage_reason'
        ]
        read_only_fields = ['listing_idx', 'created_at']


class KeywordSerializer(serializers.ModelSerializer):
    """Serializer for Keyword model."""
    
    class Meta:
        model = Keyword
        fields = ['id', 'keyword', 'filterID']


class KeywordBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk keyword updates."""
    scannerId = serializers.IntegerField()
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        allow_empty=True
    )
