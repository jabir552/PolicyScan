from django.contrib import admin
from .models import ScanReport, ComplianceResult


class ComplianceResultInline(admin.TabularInline):
    model = ComplianceResult
    extra = 0
    readonly_fields = ('document_type', 'requirement_title', 'status', 'evidence_snippet', 'explanation')
    can_delete = False


@admin.register(ScanReport)
class ScanReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'passed_checks', 'missing_checks', 'review_checks', 'privacy_url', 'tos_url')
    list_filter = ('created_at',)
    search_fields = ('privacy_url', 'tos_url')
    inlines = [ComplianceResultInline]


@admin.register(ComplianceResult)
class ComplianceResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'document_type', 'requirement_title', 'status')
    list_filter = ('document_type', 'status')
    search_fields = ('requirement_title', 'evidence_snippet')
