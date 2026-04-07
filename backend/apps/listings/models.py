from django.db import models


class Listing(models.Model):
    """Model representing marketplace listings found by scanners."""
    listing_idx = models.AutoField(primary_key=True)
    price = models.CharField(max_length=255, null=True)
    title = models.TextField(null=True)
    location = models.CharField(max_length=255, null=True)  # Listing's location (e.g., "Denver, CO")
    description = models.TextField(null=True)
    distance = models.IntegerField(null=True)
    url = models.TextField(null=True)
    img = models.TextField(null=True)
    query = models.CharField(max_length=255, null=True)
    search_title = models.TextField(null=True)
    # Scanner and search location fields
    scanner_id = models.IntegerField(null=True)  # ID of the scanner that found this listing
    search_location = models.CharField(max_length=100, null=True)  # Location where search was performed
    watchlist = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Phase 2: Two-Service Analysis Architecture fields
    scan_identifier = models.CharField(max_length=100, null=True, db_index=True)  # Groups listings by scan batch
    needs_investigation = models.BooleanField(default=False, db_index=True)       # Marked for detailed analysis
    investigation_completed = models.BooleanField(default=False)                 # Analysis completed
    investigation_result = models.CharField(max_length=20, null=True)            # 'notify', 'ignore', 'pending'
    full_description = models.TextField(null=True)                              # Fetched during analysis
    additional_images = models.JSONField(default=list)                          # Extra images from analysis
    seller_info = models.JSONField(default=dict)                               # Seller details
    analysis_metadata = models.JSONField(default=dict)                         # Classification details
    
    # Two-Pass AI Analysis fields
    triage_interesting = models.BooleanField(null=True)  # Pass 1: Is this listing interesting?
    triage_confidence = models.IntegerField(null=True)   # Pass 1: Confidence level (0-100)
    triage_reason = models.TextField(null=True)          # Pass 1: Why interesting or not

    class Meta:
        db_table = 'listings'
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.price}"


class Keyword(models.Model):
    """Model representing keywords associated with scanners for filtering."""
    id = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=255, null=True)
    filterID = models.IntegerField()  # References scanner ID

    class Meta:
        db_table = 'keywords'
        verbose_name = 'Keyword'
        verbose_name_plural = 'Keywords'

    def __str__(self):
        return self.keyword or f"Keyword {self.id}"
