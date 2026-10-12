import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib import messages
from django.db import transaction

from .models import ScanReport, ComplianceResult
from .fetcher import fetch_and_parse_page, is_valid_url
from .compliance_engine import evaluate_privacy_policy, evaluate_terms_of_service


def index_view(request: HttpRequest):
    """Main dashboard page for initiating a compliance scan and viewing recent runs."""
    recent_reports = ScanReport.objects.all()[:8]
    return render(request, "checker/index.html", {
        "recent_reports": recent_reports,
    })


def run_scan_view(request: HttpRequest):
    """Processes the submitted Privacy Policy and Terms of Service URLs."""
    if request.method != "POST":
        return redirect("index")

    privacy_url = request.POST.get("privacy_url", "").strip()
    tos_url = request.POST.get("tos_url", "").strip()

    if not privacy_url and not tos_url:
        messages.error(request, "Please enter at least one URL (Privacy Policy or Terms of Service).")
        return redirect("index")

    # Validate entered URLs format
    if privacy_url and not is_valid_url(privacy_url):
        messages.error(request, "Invalid Privacy Policy URL format. Must start with http:// or https://")
        return redirect("index")

    if tos_url and not is_valid_url(tos_url):
        messages.error(request, "Invalid Terms of Service URL format. Must start with http:// or https://")
        return redirect("index")

    with transaction.atomic():
        report = ScanReport.objects.create(
            privacy_url=privacy_url,
            tos_url=tos_url,
        )

        all_results = []

        # Process Privacy Policy
        if privacy_url:
            pp_data = fetch_and_parse_page(privacy_url)
            if pp_data["success"]:
                report.pp_fetch_status = "SUCCESS"
                pp_checks = evaluate_privacy_policy(pp_data)
                all_results.extend(pp_checks)
            else:
                report.pp_fetch_status = "FAILED"
                report.pp_error_message = pp_data["error"]
                # Mark PP checks as error/missing
                pp_checks = evaluate_privacy_policy({"text": "", "sentences": [], "bold_texts": [], "links": []})
                for c in pp_checks:
                    c["explanation"] = f"Page fetch failed: {pp_data['error']}"
                all_results.extend(pp_checks)

        # Process Terms of Service
        if tos_url:
            tos_data = fetch_and_parse_page(tos_url)
            if tos_data["success"]:
                report.tos_fetch_status = "SUCCESS"
                tos_checks = evaluate_terms_of_service(tos_data)
                all_results.extend(tos_checks)
            else:
                report.tos_fetch_status = "FAILED"
                report.tos_error_message = tos_data["error"]
                tos_checks = evaluate_terms_of_service({"text": "", "sentences": [], "bold_texts": [], "links": []})
                for c in tos_checks:
                    c["explanation"] = f"Page fetch failed: {tos_data['error']}"
                all_results.extend(tos_checks)

        # Save all results to database
        db_instances = [
            ComplianceResult(
                report=report,
                document_type=res["document_type"],
                rule_id=res["rule_id"],
                requirement_title=res["requirement_title"],
                description=res["description"],
                status=res["status"],
                evidence_snippet=res["evidence_snippet"],
                explanation=res["explanation"]
            )
            for res in all_results
        ]
        ComplianceResult.objects.bulk_create(db_instances)

        # Update metrics summary
        report.total_checks = len(all_results)
        report.passed_checks = sum(1 for r in all_results if r["status"] == ComplianceResult.STATUS_PASS)
        report.missing_checks = sum(1 for r in all_results if r["status"] == ComplianceResult.STATUS_MISSING)
        report.review_checks = sum(1 for r in all_results if r["status"] == ComplianceResult.STATUS_REVIEW)
        report.save()

    return redirect("report_detail", report_id=report.id)


def report_detail_view(request: HttpRequest, report_id: int):
    """Detailed compliance report view showing scorecards, snippets, and rule checks."""
    report = get_object_or_404(ScanReport, id=report_id)
    pp_results = report.results.filter(document_type=ComplianceResult.DOC_PP)
    tos_results = report.results.filter(document_type=ComplianceResult.DOC_TOS)

    # Compute percentage score
    pass_pct = int((report.passed_checks / report.total_checks * 100)) if report.total_checks > 0 else 0

    return render(request, "checker/report_detail.html", {
        "report": report,
        "pp_results": pp_results,
        "tos_results": tos_results,
        "pass_pct": pass_pct,
    })


def history_view(request: HttpRequest):
    """View all past scan reports."""
    reports = ScanReport.objects.all()
    return render(request, "checker/history.html", {
        "reports": reports,
    })


def export_csv_view(request: HttpRequest, report_id: int):
    """Generates and downloads a CSV compliance audit report."""
    report = get_object_or_404(ScanReport, id=report_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="a2p_compliance_report_{report.id}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Report ID", report.id])
    writer.writerow(["Scan Timestamp", report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')])
    writer.writerow(["Privacy Policy URL", report.privacy_url or "N/A"])
    writer.writerow(["Terms of Service URL", report.tos_url or "N/A"])
    writer.writerow(["Total Checks", report.total_checks])
    writer.writerow(["Passed Checks", report.passed_checks])
    writer.writerow(["Missing Checks", report.missing_checks])
    writer.writerow(["Manual Review Checks", report.review_checks])
    writer.writerow([])
    writer.writerow(["Document", "Rule ID", "Requirement", "Status", "Evidence Snippet", "Explanation / Notes"])

    for item in report.results.all():
        writer.writerow([
            item.document_type,
            item.rule_id,
            item.requirement_title,
            item.status,
            item.evidence_snippet.replace("\n", " ").strip() if item.evidence_snippet else "None",
            item.explanation.replace("\n", " ").strip() if item.explanation else ""
        ])

    return response


def demo_sample_view(request: HttpRequest):
    """
    Renders built-in test sample pages so users can test compliant and non-compliant
    policies immediately without needing third-party live URLs.
    """
    sample_type = request.GET.get("type", "compliant")
    return render(request, "checker/sample_pages.html", {"sample_type": sample_type})
