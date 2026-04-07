from django.db import models
from django.utils.text import slugify


class Agent(models.Model):
    """
    Database-driven AI specialist agent.
    
    Each agent has domain-specific prompts for triage (Pass 1) and deep analysis (Pass 2).
    Users can create, edit, and manage agents through the UI.
    System agents (is_system=True) are seeded from the original hardcoded agents.
    """
    name = models.CharField(max_length=200, help_text="Display name, e.g. 'Ski Equipment Specialist'")
    slug = models.SlugField(max_length=100, unique=True, help_text="Unique identifier, e.g. 'skis'")
    description = models.TextField(blank=True, help_text="Shown in the UI agent card")
    icon = models.CharField(max_length=10, default='', blank=True, help_text="Optional icon for the agent")
    
    # The core prompts (what makes each agent unique)
    triage_prompt = models.TextField(help_text="System prompt for Pass 1 (triage)")
    analysis_prompt = models.TextField(help_text="System prompt for Pass 2 (deep analysis)")
    
    # Model configuration
    triage_model = models.CharField(max_length=100, default='gemini-2.5-pro')
    analysis_model = models.CharField(max_length=100, default='gemini-2.5-pro')
    
    # Status
    enabled = models.BooleanField(default=True, help_text="Whether this agent is active")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agents'
        ordering = ['name']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
    
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Location(models.Model):
    """Model representing marketplace locations for scanning."""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    marketplace_url_slug = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'locations'
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
    
    def __str__(self):
        return self.name


class ActiveScanner(models.Model):
    """Model representing active marketplace scanners."""
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100, help_text="User's custom category label")
    query = models.CharField(max_length=255)
    locations = models.ManyToManyField(
        Location, 
        through='ScannerLocationMapping', 
        related_name='scanners'
    )
    status = models.CharField(max_length=20, default='stopped')
    
    # Product category for category-specific filtering
    CATEGORY_CHOICES = [
        ('vehicles', 'Vehicles'),
        ('skis', 'Skis & Snowboards'),
        ('general', 'General'),
        ('ai_beta', 'AI Analysis (Beta)'),
    ]
    product_category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general',
        help_text="Product category for category-specific filtering"
    )
    
    # Agent - links scanner to a specialist agent
    agent = models.ForeignKey(
        'Agent',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scanners',
        help_text="Specialist agent for AI-driven analysis"
    )
    
    # Legacy agent_type field - kept for backward compatibility during migration
    # NOTE: choices removed to support dynamic user-created agents
    agent_type = models.CharField(
        max_length=100,
        default='',
        blank=True,
        help_text="Agent slug string. Synced with agent FK for backward compatibility."
    )
    
    # ═══════════════ UNIVERSAL FILTERS ═══════════════
    # These apply to ALL categories
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Minimum price filter"
    )
    max_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, 
        help_text="Maximum price filter for good deals"
    )
    max_distance = models.IntegerField(
        null=True, blank=True,
        help_text="Maximum distance from search location in miles"
    )
    
    # ═══════════════ CATEGORY-SPECIFIC FILTERS ═══════════════
    # Stored as JSON for flexibility - each category has its own schema
    category_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Category-specific filter criteria stored as JSON"
    )
    # Example for vehicles: {"max_mileage": 100000, "min_year": 2015, "max_year": 2024}
    # Example for skis: {"min_length_cm": 170, "max_length_cm": 180, "width_mm": 95}
    
    # DEPRECATED: Keep for backward compatibility, but use category_filters going forward
    max_mileage = models.IntegerField(
        null=True, blank=True,
        help_text="DEPRECATED: Use category_filters.max_mileage instead"
    )
    
    # ═══════════════ NOTIFICATION SETTINGS ═══════════════
    # Per-scanner email recipients for notifications
    notification_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="List of email addresses to notify when this scanner finds deals"
    )
    # Example: ["friend@utah.com", "me@massachusetts.com"]

    class Meta:
        db_table = 'active_scanners'
        verbose_name = 'Active Scanner'
        verbose_name_plural = 'Active Scanners'

    def __str__(self):
        # Get the first location name if available
        location_name = self.locations.first().name if self.locations.exists() else 'multiple locations'
        return f"{self.query} in {location_name}"


class ScannerLocationMapping(models.Model):
    """Through model for scanner-location many-to-many relationship."""
    id = models.AutoField(primary_key=True)
    scanner = models.ForeignKey(ActiveScanner, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'scanner_location_mappings'
        unique_together = ('scanner', 'location')
        verbose_name = 'Scanner Location Mapping'
        verbose_name_plural = 'Scanner Location Mappings'
    
    def __str__(self):
        return f"{self.scanner.query} in {self.location.name}"


class ScanHistory(models.Model):
    """Model to track scan execution history and results."""
    id = models.AutoField(primary_key=True)
    scan_type = models.CharField(
        max_length=20,
        choices=[('single', 'Single Scan'), ('continuous', 'Continuous Scan')],
        default='single'
    )
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('error', 'Error'), ('partial', 'Partial Success')],
        default='success'
    )
    
    # Scan results
    scanners_processed = models.IntegerField(default=0)
    total_listings_found = models.IntegerField(default=0)
    new_listings_added = models.IntegerField(default=0)
    watchlist_items_added = models.IntegerField(default=0)
    
    # Timing information
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    duration_seconds = models.FloatField(default=0.0)
    
    # Error information
    error_message = models.TextField(blank=True, null=True)
    error_count = models.IntegerField(default=0)
    
    # Additional metadata
    randomized = models.BooleanField(default=False)
    interval_minutes = models.IntegerField(blank=True, null=True)  # For continuous scans
    
    class Meta:
        db_table = 'scan_history'
        ordering = ['-started_at']
        verbose_name = 'Scan History'
        verbose_name_plural = 'Scan History'
    
    def __str__(self):
        return f"{self.scan_type.title()} scan at {self.started_at} - {self.status}"


class ScanBatch(models.Model):
    """Model to track scan batches for Phase 2 two-service architecture."""
    scan_id = models.CharField(max_length=100, unique=True, primary_key=True)
    scan_type = models.CharField(
        max_length=20, 
        choices=[('single', 'Single'), ('continuous', 'Continuous')],
        default='single'
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    
    # Scan statistics
    total_listings_found = models.IntegerField(default=0)
    new_listings_added = models.IntegerField(default=0)
    investigation_marked = models.IntegerField(default=0)
    
    # Analysis tracking
    analysis_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ], 
        default='pending'
    )
    analysis_started_at = models.DateTimeField(null=True)
    analysis_completed_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'scan_batches'
        ordering = ['-started_at']
        verbose_name = 'Scan Batch'
        verbose_name_plural = 'Scan Batches'
    
    def __str__(self):
        return f"Scan {self.scan_id} - {self.scan_type} ({self.analysis_status})"


class AnalysisProgress(models.Model):
    """Model to track real-time progress of detailed analysis."""
    scan_batch = models.OneToOneField(ScanBatch, on_delete=models.CASCADE, related_name='progress')
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    current_item_title = models.CharField(max_length=200, null=True)
    current_status = models.CharField(max_length=50, null=True)  # 'fetching_details', 'classifying', etc.
    estimated_completion = models.DateTimeField(null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analysis_progress'
        verbose_name = 'Analysis Progress'
        verbose_name_plural = 'Analysis Progress'
    
    def __str__(self):
        return f"Analysis progress for {self.scan_batch.scan_id}: {self.processed_items}/{self.total_items}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0
        return round((self.processed_items / self.total_items) * 100, 1)


class SystemTask(models.Model):
    """Track currently running system tasks (scans, analysis, etc.)."""
    
    TASK_TYPES = [
        ('scan', 'Marketplace Scan'),
        ('analysis', 'AI Analysis'),
        ('notification', 'Sending Notifications'),
    ]
    
    TASK_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TASK_STEPS = [
        ('initializing', 'Initializing'),
        ('scraping', 'Scraping Listings'),
        ('saving', 'Saving to Database'),
        ('triaging', 'AI Triage (Pass 1)'),
        ('analyzing', 'Deep Analysis (Pass 2)'),
        ('notifying', 'Sending Notifications'),
        ('complete', 'Complete'),
    ]
    
    id = models.AutoField(primary_key=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')
    current_step = models.CharField(max_length=30, choices=TASK_STEPS, default='initializing')
    
    # Progress tracking
    progress_percent = models.IntegerField(default=0)
    progress_message = models.CharField(max_length=255, blank=True, default='')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    scan_batch = models.ForeignKey('ScanBatch', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Extra details as JSON
    details = models.JSONField(default=dict, blank=True)
    
    # User tracking (for future multi-user support)
    # user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'system_tasks'
        ordering = ['-started_at']
        verbose_name = 'System Task'
        verbose_name_plural = 'System Tasks'
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.status} ({self.current_step})"
    
    @classmethod
    def get_current_task(cls):
        """Get the currently running task, if any."""
        return cls.objects.filter(status='running').first()
    
    @classmethod
    def is_busy(cls):
        """Check if the system is currently busy with a task."""
        return cls.objects.filter(status='running').exists()
    
    @classmethod
    def cleanup_stale_tasks(cls):
        """
        Mark any tasks that have been 'running' for too long as failed.
        This should be called on server startup to clean up orphaned tasks.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Mark tasks running for more than 30 minutes as stale
        stale_threshold = timezone.now() - timedelta(minutes=30)
        stale_tasks = cls.objects.filter(
            status='running',
            started_at__lt=stale_threshold
        )
        
        count = stale_tasks.update(
            status='failed',
            progress_message='Task interrupted (server restart or timeout)',
            completed_at=timezone.now()
        )
        
        if count > 0:
            print(f"Cleaned up {count} stale task(s)")
        
        return count
    
    @classmethod
    def cancel_all_running(cls):
        """Cancel all running tasks. Use with caution."""
        from django.utils import timezone
        
        count = cls.objects.filter(status='running').update(
            status='cancelled',
            progress_message='Task cancelled',
            completed_at=timezone.now()
        )
        return count
    
    def update_progress(self, step: str, percent: int, message: str = ''):
        """Update task progress."""
        self.current_step = step
        self.progress_percent = percent
        self.progress_message = message
        self.save(update_fields=['current_step', 'progress_percent', 'progress_message'])
    
    def complete(self, success: bool = True):
        """Mark task as completed."""
        from django.utils import timezone
        self.status = 'completed' if success else 'failed'
        self.current_step = 'complete'
        self.progress_percent = 100
        self.completed_at = timezone.now()
        self.save()
    
    def fail(self, error_message: str = ''):
        """Mark task as failed."""
        from django.utils import timezone
        self.status = 'failed'
        self.progress_message = error_message
        self.completed_at = timezone.now()
        self.save()


class ScannerSettings(models.Model):
    """Global scanner settings (singleton pattern)."""
    
    MODE_CHOICES = [
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
    ]
    
    id = models.AutoField(primary_key=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='manual')
    
    # Auto mode settings
    auto_enabled = models.BooleanField(default=False)
    interval_minutes = models.IntegerField(default=30)
    randomize_order = models.BooleanField(default=True)
    
    # Timing tracking
    last_scan_at = models.DateTimeField(null=True, blank=True)
    next_scan_at = models.DateTimeField(null=True, blank=True)
    
    # Auto mode process tracking
    auto_process_pid = models.IntegerField(null=True, blank=True)

    # Schedule window — restrict auto scans to specific hours (MST)
    schedule_enabled = models.BooleanField(default=False, help_text="Only run scans within the configured time window")
    schedule_start = models.TimeField(default='23:00:00', help_text="Window open time (America/Denver / MST)")
    schedule_end = models.TimeField(default='06:30:00', help_text="Window close time (America/Denver / MST)")
    schedule_timezone = models.CharField(max_length=50, default='America/Denver', help_text="Timezone for schedule window")

    # User (for future multi-user support)
    # user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'scanner_settings'
        verbose_name = 'Scanner Settings'
        verbose_name_plural = 'Scanner Settings'
    
    def __str__(self):
        return f"Scanner Settings - {self.mode} mode"
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        settings, _ = cls.objects.get_or_create(id=1)
        return settings
    
    def calculate_next_scan(self):
        """Calculate when the next auto scan should run."""
        from django.utils import timezone
        from datetime import timedelta
        if self.auto_enabled and self.last_scan_at:
            self.next_scan_at = self.last_scan_at + timedelta(minutes=self.interval_minutes)
        elif self.auto_enabled:
            self.next_scan_at = timezone.now() + timedelta(minutes=self.interval_minutes)
        else:
            self.next_scan_at = None
        self.save(update_fields=['next_scan_at'])


class WorkerStatus(models.Model):
    """
    Singleton model — the local worker writes a heartbeat here every ~30 seconds.
    The web UI reads this to show "worker online / offline".
    """
    id = models.AutoField(primary_key=True)
    worker_last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    current_task = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = "worker_status"
        verbose_name = "Worker Status"
        verbose_name_plural = "Worker Status"

    def __str__(self):
        status = "online" if self.is_online else "offline"
        return f"Worker {status} (last seen: {self.worker_last_seen})"

    @classmethod
    def _get(cls):
        instance, _ = cls.objects.get_or_create(id=1)
        return instance

    @classmethod
    def ping(cls, task: str = "idle"):
        """Call from the worker every loop iteration to record a heartbeat."""
        from django.utils import timezone
        instance = cls._get()
        instance.worker_last_seen = timezone.now()
        instance.is_online = True
        instance.current_task = task
        instance.save(update_fields=["worker_last_seen", "is_online", "current_task"])

    @classmethod
    def go_offline(cls):
        """Call from the worker on clean shutdown."""
        instance = cls._get()
        instance.is_online = False
        instance.current_task = ""
        instance.save(update_fields=["is_online", "current_task"])


class LLMUsage(models.Model):
    """Track token usage and costs per LLM call."""
    scan_batch = models.ForeignKey(ScanBatch, on_delete=models.CASCADE, null=True, blank=True)
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, null=True, blank=True)
    
    agent_type = models.CharField(max_length=50)  # 'skis', 'vehicles', 'dj_equipment'
    call_type = models.CharField(max_length=20)   # 'triage' or 'analyze'
    model_name = models.CharField(max_length=100)
    
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'llm_usage'
        ordering = ['-created_at']
        verbose_name = 'LLM Usage'
        verbose_name_plural = 'LLM Usage'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['agent_type']),
            models.Index(fields=['scan_batch']),
        ]
    
    def __str__(self):
        return f"{self.agent_type} {self.call_type} - {self.total_tokens} tokens"
    
    def save(self, *args, **kwargs):
        """Calculate estimated cost on save based on Gemini pricing."""
        if self.total_tokens > 0 and self.estimated_cost_usd == 0:
            # Gemini 2.0 Flash pricing (for triage)
            # Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
            # Gemini 2.5 Pro pricing (for analysis)
            # Input: $1.25 per 1M tokens, Output: $10 per 1M tokens
            
            if 'flash' in self.model_name.lower() or '2.0' in self.model_name:
                # Flash model
                input_cost_per_million = 0.075
                output_cost_per_million = 0.30
            else:
                # Pro model (2.5-pro)
                input_cost_per_million = 1.25
                output_cost_per_million = 10.0
            
            input_cost = (self.prompt_tokens / 1_000_000) * input_cost_per_million
            output_cost = (self.completion_tokens / 1_000_000) * output_cost_per_million
            self.estimated_cost_usd = input_cost + output_cost
        
        super().save(*args, **kwargs)
