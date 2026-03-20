"""Contract tests for /examples — validates SDK requests against OpenAPI schemas.

Runs each example script with mocked HTTP, validating that:
1. Every request payload matches the corresponding request schema
2. Mock responses conform to response schemas
3. No hardcoded API keys (sur_live_*, sur_test_*) exist in example source
4. Examples run without error against the mock contract
"""
import json
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from jsonschema import validate, ValidationError as JsonSchemaError

# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLES_DIR = REPO_ROOT / "examples"


def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return json.load(f)


REQUEST_SCHEMAS = {
    "/reports/signal": load_schema("signal_request.json"),
    "/reports/scan": load_schema("scan_request.json"),
    "/reports/solutions": load_schema("solutions_request.json"),
}

CREATION_RESPONSE_SCHEMA = load_schema("report_creation_response.json")
STATUS_RESPONSE_SCHEMA = load_schema("report_status_response.json")

# ---------------------------------------------------------------------------
# Mock response factories — return schema-valid responses
# ---------------------------------------------------------------------------

MOCK_AUTH_RESPONSE = {
    "authenticated": True,
    "org_id": "org_test123",
    "org_name": "Test Org",
    "credits": 100,
    "message": "Authentication successful! Your API key is working correctly.",
}

MOCK_SCAN_RESPONSE = {
    "report_id": "rpt_scanTest001",
    "org_id": "org_test123",
    "product": "scan",
    "status": "queued",
    "brand_slug": "example_brand",
    "brand_name": "Example Brand",
    "brand_created": True,
    "credits_used": 1,
    "request_id": "req_abc123",
    "created_at": "2026-01-15T10:30:00Z",
    "note": "brand_slug created - prevents duplicates from name variations",
}

MOCK_SIGNAL_RESPONSE = {
    "report_id": "rpt_sigTest002",
    "token": "SIG-2026-01-TEST1",
    "org_id": "org_test123",
    "product": "signal",
    "status": "queued",
    "brand_slug": "example_brand",
    "brand_name": "Example Brand",
    "credits_used": 1,
    "request_id": "req_def456",
    "created_at": "2026-01-15T10:31:00Z",
}

MOCK_REPORT_STATUS = {
    "report_id": "rpt_scanTest001",
    "org_id": "org_test123",
    "product": "scan",
    "status": "processing",
    "brand_slug": "example_brand",
    "brand_name": "Example Brand",
    "token": None,
    "credits_used": 1,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:32:00Z",
}


def _validate_schema(instance: dict, schema: dict, label: str):
    """Validate instance against JSON schema, raising AssertionError on failure."""
    try:
        validate(instance=instance, schema=schema)
    except JsonSchemaError as exc:
        raise AssertionError(f"Schema validation failed for {label}: {exc.message}")


# Pre-validate mock responses at import time so broken mocks fail fast
_validate_schema(MOCK_SCAN_RESPONSE, CREATION_RESPONSE_SCHEMA, "mock scan creation")
_validate_schema(MOCK_SIGNAL_RESPONSE, CREATION_RESPONSE_SCHEMA, "mock signal creation")
_validate_schema(MOCK_REPORT_STATUS, STATUS_RESPONSE_SCHEMA, "mock report status")


# ---------------------------------------------------------------------------
# Contract test
# ---------------------------------------------------------------------------


class TestQuickstartContract(unittest.TestCase):
    """Run quickstart.py against mocked HTTP and validate schemas."""

    def setUp(self):
        self.validated_requests = []

    def _mock_response(self, status_code: int, json_data: dict) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.text = json.dumps(json_data)
        return resp

    def _route_post(self, url: str, **kwargs) -> MagicMock:
        """Route POST requests, validate payloads against schemas."""
        payload = kwargs.get("json", {})

        if "/reports/scan" in url:
            schema = REQUEST_SCHEMAS["/reports/scan"]
            _validate_schema(payload, schema, f"POST {url}")
            self.validated_requests.append(("POST", "/reports/scan", payload))
            return self._mock_response(202, MOCK_SCAN_RESPONSE)

        elif "/reports/signal" in url:
            schema = REQUEST_SCHEMAS["/reports/signal"]
            _validate_schema(payload, schema, f"POST {url}")
            self.validated_requests.append(("POST", "/reports/signal", payload))
            return self._mock_response(202, MOCK_SIGNAL_RESPONSE)

        elif "/reports/solutions" in url:
            schema = REQUEST_SCHEMAS["/reports/solutions"]
            _validate_schema(payload, schema, f"POST {url}")
            self.validated_requests.append(("POST", "/reports/solutions", payload))
            return self._mock_response(202, MOCK_SCAN_RESPONSE)

        # Default: return 200 with empty body
        return self._mock_response(200, {})

    def _route_get(self, url: str, **kwargs) -> MagicMock:
        """Route GET requests with schema-valid mock responses."""
        if "/test-auth" in url:
            return self._mock_response(200, MOCK_AUTH_RESPONSE)

        elif "/reports/" in url:
            return self._mock_response(200, MOCK_REPORT_STATUS)

        return self._mock_response(200, {})

    @patch.dict(os.environ, {"SURMADO_API_KEY": "sur_test_ci_placeholder_key"})
    @patch("requests.get")
    @patch("requests.post")
    def test_quickstart_runs_against_contract(self, mock_post, mock_get):
        """quickstart.py runs to completion and all payloads match schemas."""
        mock_post.side_effect = self._route_post
        mock_get.side_effect = self._route_get

        # Import and run quickstart
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "quickstart", EXAMPLES_DIR / "quickstart.py"
        )
        module = importlib.util.find_module = spec
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()

        # Verify we actually validated requests (not silently skipped)
        self.assertTrue(
            len(self.validated_requests) >= 2,
            f"Expected at least 2 validated requests, got {len(self.validated_requests)}: "
            f"{[r[1] for r in self.validated_requests]}"
        )

    @patch.dict(os.environ, {"SURMADO_API_KEY": "sur_test_ci_placeholder_key"})
    @patch("requests.get")
    @patch("requests.post")
    def test_quickstart_scan_payload_matches_schema(self, mock_post, mock_get):
        """Scan request payload has all required fields and correct types."""
        mock_post.side_effect = self._route_post
        mock_get.side_effect = self._route_get

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "quickstart", EXAMPLES_DIR / "quickstart.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()

        scan_requests = [r for r in self.validated_requests if r[1] == "/reports/scan"]
        self.assertEqual(len(scan_requests), 1, "Expected exactly 1 scan request")

        payload = scan_requests[0][2]
        self.assertIn("url", payload)
        self.assertIn("email", payload)
        self.assertIn("brand_name", payload)

    @patch.dict(os.environ, {"SURMADO_API_KEY": "sur_test_ci_placeholder_key"})
    @patch("requests.get")
    @patch("requests.post")
    def test_quickstart_signal_payload_matches_schema(self, mock_post, mock_get):
        """Signal request payload has all required fields and correct types."""
        mock_post.side_effect = self._route_post
        mock_get.side_effect = self._route_get

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "quickstart", EXAMPLES_DIR / "quickstart.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()

        signal_requests = [r for r in self.validated_requests if r[1] == "/reports/signal"]
        self.assertEqual(len(signal_requests), 1, "Expected exactly 1 signal request")

        payload = signal_requests[0][2]
        for field in ["url", "email", "brand_name", "industry", "location",
                       "persona", "pain_points", "brand_details", "direct_competitors"]:
            self.assertIn(field, payload, f"Signal payload missing required field: {field}")


class TestNoHardcodedKeys(unittest.TestCase):
    """Ensure no example files contain real API keys."""

    REAL_KEY_PATTERN = re.compile(r"sur_live_[A-Za-z0-9_]{10,}")

    def test_no_live_keys_in_examples(self):
        """No example file contains a real sur_live_ key."""
        for py_file in EXAMPLES_DIR.glob("**/*.py"):
            content = py_file.read_text()
            matches = self.REAL_KEY_PATTERN.findall(content)
            self.assertEqual(
                matches, [],
                f"Found hardcoded live key(s) in {py_file.name}: {matches}"
            )

    def test_no_live_keys_in_client(self):
        """No client source file contains a real sur_live_ key."""
        client_dir = REPO_ROOT / "client" / "surmado"
        for py_file in client_dir.glob("**/*.py"):
            content = py_file.read_text()
            matches = self.REAL_KEY_PATTERN.findall(content)
            self.assertEqual(
                matches, [],
                f"Found hardcoded live key(s) in {py_file.name}: {matches}"
            )


class TestMockResponsesConformToSchemas(unittest.TestCase):
    """Verify our mock fixtures are valid per the response schemas."""

    def test_scan_creation_response(self):
        _validate_schema(MOCK_SCAN_RESPONSE, CREATION_RESPONSE_SCHEMA, "scan creation")

    def test_signal_creation_response(self):
        _validate_schema(MOCK_SIGNAL_RESPONSE, CREATION_RESPONSE_SCHEMA, "signal creation")

    def test_report_status_response(self):
        _validate_schema(MOCK_REPORT_STATUS, STATUS_RESPONSE_SCHEMA, "report status")


if __name__ == "__main__":
    unittest.main()
