from django.test import TestCase, Client
from django.urls import reverse
from checker.models import ScanReport, ComplianceResult
from checker.compliance_engine import evaluate_privacy_policy, evaluate_terms_of_service


class ComplianceEngineTests(TestCase):
    def test_compliant_privacy_policy(self):
        sample_data = {
            "title": "Privacy Policy",
            "text": (
                "We explain the information we collect and how we use your information. "
                "Mobile information and opt-in consent will not be shared with third parties or affiliates for marketing or promotional purposes. "
                "All the above categories exclude text messaging originator opt-in data and consent; this information won't be shared with any third parties."
            ),
            "sentences": [
                "We explain the information we collect and how we use your information.",
                "Mobile information and opt-in consent will not be shared with third parties or affiliates for marketing or promotional purposes.",
                "All the above categories exclude text messaging originator opt-in data and consent; this information won't be shared with any third parties."
            ],
            "bold_texts": [],
            "links": []
        }
        results = evaluate_privacy_policy(sample_data)
        statuses = [r["status"] for r in results]
        # 2 active PP checks should pass
        self.assertEqual(statuses, ["PASS", "PASS"])

    def test_missing_pp_consent_disclosure(self):
        sample_data = {
            "title": "Bad Policy",
            "text": "We share your info with any advertisers.",
            "sentences": ["We share your info with any advertisers."],
            "bold_texts": [],
            "links": []
        }
        results = evaluate_privacy_policy(sample_data)
        statuses = [r["status"] for r in results]
        self.assertIn("MISSING", statuses)

    def test_compliant_terms_of_service(self):
        sample_data = {
            "title": "Acme SMS Terms",
            "text": (
                "Terms of Service for Acme Corp SMS Program. "
                "You may receive text messages for updates and notifications. "
                "Message and data rates may apply. Message frequency varies. "
                "Contact customer care at support@acme.com or call 1-800-123-4567. "
                "Reply STOP to cancel. Reply HELP for help. "
                "Carriers are not liable for delayed or undelivered messages. "
                "See our Privacy Policy at https://example.com/privacy."
            ),
            "sentences": [
                "Terms of Service for Acme Corp SMS Program.",
                "You may receive text messages for updates and notifications.",
                "Message and data rates may apply.",
                "Message frequency varies.",
                "Contact customer care at support@acme.com.",
                "Reply STOP to cancel.",
                "Reply HELP for help.",
                "Carriers are not liable for delayed or undelivered messages."
            ],
            "bold_texts": ["STOP", "HELP"],
            "links": [{"href": "https://example.com/privacy", "text": "Privacy Policy"}]
        }
        results = evaluate_terms_of_service(sample_data)
        for r in results:
            self.assertEqual(r["status"], "PASS", f"Rule {r['rule_id']} failed: {r['explanation']}")


class ViewsAndWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_page_loads(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PolicyScan")

    def test_demo_sample_page_loads(self):
        response = self.client.get(reverse("demo_sample") + "?type=compliant")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Corp - Privacy Policy")

    def test_csv_export(self):
        report = ScanReport.objects.create(
            privacy_url="https://example.com/privacy",
            tos_url="https://example.com/tos",
            total_checks=2,
            passed_checks=1,
            missing_checks=1,
        )
        ComplianceResult.objects.create(
            report=report,
            document_type="Privacy Policy",
            rule_id="PP-01",
            requirement_title="Data Collection",
            description="Test",
            status="PASS",
            evidence_snippet="Found data collect snippet",
            explanation="Passed"
        )
        response = self.client.get(reverse("export_csv", args=[report.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(b"PP-01", response.content)
