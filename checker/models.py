from django.db import models


class ScanReport(models.Model):
    """Stores the top-level scan run, URLs entered, and summary metrics."""
    privacy_url = models.URLField(max_length=500, blank=True, null=True)
    tos_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Summary counters
    total_checks = models.IntegerField(default=0)
    passed_checks = models.IntegerField(default=0)
    missing_checks = models.IntegerField(default=0)
    review_checks = models.IntegerField(default=0)

    # Scraped page metadata / status
    pp_fetch_status = models.CharField(max_length=50, default="PENDING")
    tos_fetch_status = models.CharField(max_length=50, default="PENDING")
    pp_error_message = models.TextField(blank=True, null=True)
    tos_error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Scan #{self.id} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class ComplianceResult(models.Model):
    """Stores individual rule checks for each scan report."""
    STATUS_PASS = "PASS"
    STATUS_MISSING = "MISSING"
    STATUS_REVIEW = "NEEDS MANUAL REVIEW"

    STATUS_CHOICES = [
        (STATUS_PASS, "PASS"),
        (STATUS_MISSING, "MISSING"),
        (STATUS_REVIEW, "NEEDS MANUAL REVIEW"),
    ]

    DOC_PP = "Privacy Policy"
    DOC_TOS = "Terms of Service"

    DOC_CHOICES = [
        (DOC_PP, "Privacy Policy"),
        (DOC_TOS, "Terms of Service"),
    ]

    report = models.ForeignKey(ScanReport, related_name="results", on_delete=models.CASCADE)
    document_type = models.CharField(max_length=50, choices=DOC_CHOICES)
    rule_id = models.CharField(max_length=100)
    requirement_title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_MISSING)
    evidence_snippet = models.TextField(blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.document_type}] {self.requirement_title}: {self.status}"
