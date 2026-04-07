from rest_framework import serializers
from .models import (
    Agent, ActiveScanner, Location, ScannerLocationMapping, ScanHistory, 
    ScanBatch, AnalysisProgress, SystemTask, ScannerSettings
)


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent model."""
    scanner_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'triage_prompt', 'analysis_prompt',
            'triage_model', 'analysis_model',
            'enabled',
            'created_at', 'updated_at',
            'scanner_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'scanner_count']

    def get_scanner_count(self, obj):
        """Count of scanners using this agent."""
        return obj.scanners.count()
    
    def validate_slug(self, value):
        """Ensure slug is unique and URL-safe."""
        import re
        if not re.match(r'^[a-z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Slug must contain only lowercase letters, numbers, hyphens, and underscores."
            )
        return value


class AgentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for agent list views (no prompt text).
    Used by the frontend to display agent cards without loading large prompts.
    """
    scanner_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'triage_model', 'analysis_model',
            'enabled',
            'created_at', 'updated_at',
            'scanner_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'scanner_count']

    def get_scanner_count(self, obj):
        return obj.scanners.count()


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model."""
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'marketplace_url_slug']


class ScannerLocationMappingSerializer(serializers.ModelSerializer):
    """Serializer for ScannerLocationMapping model."""
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_slug = serializers.CharField(source='location.marketplace_url_slug', read_only=True)
    
    class Meta:
        model = ScannerLocationMapping
        fields = ['id', 'location', 'location_name', 'location_slug', 'is_active']


class ActiveScannerSerializer(serializers.ModelSerializer):
    """Serializer for ActiveScanner model."""
    locations_data = serializers.SerializerMethodField()
    
    # Universal filters
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    max_distance = serializers.IntegerField(required=False, allow_null=True)
    
    # Category filters
    product_category = serializers.ChoiceField(
        choices=ActiveScanner.CATEGORY_CHOICES,
        default='general',
        required=False
    )
    category_filters = serializers.JSONField(default=dict, required=False)
    
    # Agent FK (readable as id, resolved automatically from agent_type)
    agent = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(),
        required=False,
        allow_null=True
    )
    # Agent slug for read convenience (read-only - derived from FK)
    agent_slug = serializers.SerializerMethodField()
    
    # Agent type string - accepts any slug. The validate() method auto-resolves
    # this to the Agent FK. This is the primary input field from the frontend.
    agent_type = serializers.CharField(
        default='',
        required=False,
        allow_blank=True
    )
    
    # Deprecated fields (kept for backward compatibility)
    max_mileage = serializers.IntegerField(required=False, allow_null=True)
    
    # Notification settings
    notification_emails = serializers.JSONField(default=list, required=False)
    
    class Meta:
        model = ActiveScanner
        fields = [
            'id', 'category', 'query', 'status', 
            'product_category', 'category_filters',
            'agent', 'agent_slug', 'agent_type',
            'min_price', 'max_price', 'max_distance', 
            'max_mileage',  # Deprecated but kept for compatibility
            'notification_emails',
            'locations_data'
        ]
    
    def validate_min_price(self, value):
        """Validate min_price field - convert empty strings to None."""
        if value == '' or value == 0:
            return None
        return value
    
    def validate_max_price(self, value):
        """Validate max_price field - convert empty strings to None."""
        if value == '' or value == 0:
            return None
        return value
    
    def validate_max_mileage(self, value):
        """Validate max_mileage field - convert empty strings to None."""
        if value == '' or value == 0:
            return None
        return value
    
    def validate_max_distance(self, value):
        """Validate max_distance field - convert empty strings to None."""
        if value == '' or value == 0:
            return None
        return value
    
    def validate_category_filters(self, value):
        """
        Validate category_filters.
        
        Note: With the AI agent-centric architecture, category_filters are largely 
        deprecated as agents handle all evaluation logic. This validation now just 
        ensures the value is a valid dict.
        """
        if not value:
            return {}
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("category_filters must be a dictionary")
        
        return value
    
    def validate_notification_emails(self, value):
        """
        Validate notification_emails field.
        Ensures it's a list of valid email addresses.
        """
        import re
        
        if not value:
            return []
        
        if not isinstance(value, list):
            raise serializers.ValidationError("notification_emails must be a list")
        
        # Basic email validation pattern
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        validated_emails = []
        for email in value:
            if not isinstance(email, str):
                continue
            email = email.strip().lower()
            if email and email_pattern.match(email):
                validated_emails.append(email)
            elif email:
                raise serializers.ValidationError(f"Invalid email address: {email}")
        
        return validated_emails
        
    def get_agent_slug(self, obj):
        """Return the agent slug from the FK if set, otherwise from agent_type."""
        if obj.agent_id:
            return obj.agent.slug
        return obj.agent_type
    
    def validate(self, attrs):
        """
        Auto-resolve the Agent FK from agent_type.
        
        When agent_type is provided (as a slug string), look up the Agent record
        and set the FK. This keeps agent_type and agent FK in sync.
        """
        # If agent FK is explicitly provided, sync agent_type from it
        if 'agent' in attrs and attrs['agent'] is not None:
            attrs['agent_type'] = attrs['agent'].slug
        # Otherwise, try to resolve agent FK from agent_type string
        elif 'agent_type' in attrs:
            agent_type_val = attrs['agent_type']
            if agent_type_val:
                try:
                    agent_record = Agent.objects.get(slug=agent_type_val)
                    attrs['agent'] = agent_record
                except Agent.DoesNotExist:
                    pass  # Leave agent as None - legacy agents may not exist in DB
        
        return attrs
    
    def get_locations_data(self, obj):
        """Get formatted location data for the scanner."""
        mappings = ScannerLocationMapping.objects.filter(scanner=obj, is_active=True)
        
        return [
            {
                'mapping_id': mapping.id,
                'location': mapping.location.id,
                'location_name': mapping.location.name,
                'marketplace_slug': mapping.location.marketplace_url_slug,
                'is_active': mapping.is_active
            }
            for mapping in mappings
        ]


class ScanHistorySerializer(serializers.ModelSerializer):
    """Serializer for ScanHistory model."""
    
    class Meta:
        model = ScanHistory
        fields = [
            'id', 'scan_type', 'status', 'scanners_processed', 
            'total_listings_found', 'new_listings_added', 'watchlist_items_added',
            'started_at', 'completed_at', 'duration_seconds', 
            'error_message', 'error_count', 'randomized', 'interval_minutes'
        ]


class AnalysisProgressSerializer(serializers.ModelSerializer):
    """Serializer for AnalysisProgress model."""
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = AnalysisProgress
        fields = [
            'total_items', 'processed_items', 'current_item_title', 
            'current_status', 'estimated_completion', 'last_updated',
            'progress_percentage'
        ]


class ScanBatchSerializer(serializers.ModelSerializer):
    """Serializer for ScanBatch model."""
    progress = AnalysisProgressSerializer(read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanBatch
        fields = [
            'scan_id', 'scan_type', 'started_at', 'completed_at',
            'total_listings_found', 'new_listings_added', 'investigation_marked',
            'analysis_status', 'analysis_started_at', 'analysis_completed_at',
            'progress', 'duration_seconds'
        ]
    
    def get_duration_seconds(self, obj):
        """Calculate scan duration in seconds."""
        if obj.completed_at and obj.started_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class SystemTaskSerializer(serializers.ModelSerializer):
    """Serializer for SystemTask model."""
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    step_display = serializers.CharField(source='get_current_step_display', read_only=True)
    elapsed_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemTask
        fields = [
            'id', 'task_type', 'task_type_display', 'status', 'status_display',
            'current_step', 'step_display', 'progress_percent', 'progress_message',
            'started_at', 'completed_at', 'elapsed_seconds', 'scan_batch_id', 'details'
        ]
    
    def get_elapsed_seconds(self, obj):
        """Calculate elapsed time in seconds."""
        if obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        else:
            from django.utils import timezone
            return (timezone.now() - obj.started_at).total_seconds()


class ScannerSettingsSerializer(serializers.ModelSerializer):
    """Serializer for ScannerSettings model."""
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    can_run_manual = serializers.SerializerMethodField()
    can_enable_auto = serializers.SerializerMethodField()
    time_until_next_scan = serializers.SerializerMethodField()
    
    class Meta:
        model = ScannerSettings
        fields = [
            'id', 'mode', 'mode_display', 'auto_enabled', 'interval_minutes',
            'randomize_order', 'last_scan_at', 'next_scan_at', 'auto_process_pid',
            'can_run_manual', 'can_enable_auto', 'time_until_next_scan'
        ]
    
    def get_can_run_manual(self, obj):
        """Check if manual scan can be run (no task running and not in auto mode)."""
        return not SystemTask.is_busy() and not obj.auto_enabled
    
    def get_can_enable_auto(self, obj):
        """Check if auto mode can be enabled (no task currently running)."""
        return not SystemTask.is_busy()
    
    def get_time_until_next_scan(self, obj):
        """Get seconds until next auto scan."""
        if not obj.auto_enabled or not obj.next_scan_at:
            return None
        from django.utils import timezone
        delta = obj.next_scan_at - timezone.now()
        return max(0, int(delta.total_seconds()))
