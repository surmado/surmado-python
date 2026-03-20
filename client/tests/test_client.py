"""Extensive unit tests for the Surmado Python SDK."""
import json
import os
import time
import unittest
from unittest.mock import patch, MagicMock, call
import requests as requests_lib

from surmado import (
    Surmado,
    SurmadoError,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    __version__,
)


# =============================================================================
# Exception Hierarchy
# =============================================================================


class TestExceptionHierarchy(unittest.TestCase):
    """Verify that all custom exceptions inherit from SurmadoError."""

    def test_authentication_error_is_surmado_error(self):
        self.assertTrue(issubclass(AuthenticationError, SurmadoError))

    def test_insufficient_credits_is_surmado_error(self):
        self.assertTrue(issubclass(InsufficientCreditsError, SurmadoError))

    def test_not_found_is_surmado_error(self):
        self.assertTrue(issubclass(NotFoundError, SurmadoError))

    def test_validation_error_is_surmado_error(self):
        self.assertTrue(issubclass(ValidationError, SurmadoError))

    def test_rate_limit_error_is_surmado_error(self):
        self.assertTrue(issubclass(RateLimitError, SurmadoError))

    def test_surmado_error_is_exception(self):
        self.assertTrue(issubclass(SurmadoError, Exception))


class TestExceptionAttributes(unittest.TestCase):
    """Verify exception attributes (status_code, response, message)."""

    def test_surmado_error_with_all_attrs(self):
        err = SurmadoError("boom", status_code=500, response={"error": "boom"})
        self.assertEqual(str(err), "boom")
        self.assertEqual(err.status_code, 500)
        self.assertEqual(err.response, {"error": "boom"})

    def test_surmado_error_defaults(self):
        err = SurmadoError("simple")
        self.assertEqual(str(err), "simple")
        self.assertIsNone(err.status_code)
        self.assertIsNone(err.response)

    def test_auth_error_attrs(self):
        err = AuthenticationError("bad key", status_code=401, response={"detail": "Unauthorized"})
        self.assertEqual(err.status_code, 401)
        self.assertEqual(err.response["detail"], "Unauthorized")

    def test_catch_specific_and_base(self):
        """Can catch subclass via base SurmadoError."""
        with self.assertRaises(SurmadoError):
            raise AuthenticationError("test")

    def test_catch_specific_directly(self):
        with self.assertRaises(AuthenticationError):
            raise AuthenticationError("test")


# =============================================================================
# Client Initialization
# =============================================================================


class TestClientInit(unittest.TestCase):
    """Test client initialization."""

    def test_init_with_api_key(self):
        client = Surmado(api_key="sur_test_abc123")
        self.assertEqual(client.api_key, "sur_test_abc123")

    @patch.dict(os.environ, {"SURMADO_API_KEY": "sur_test_from_env"})
    def test_init_from_env(self):
        client = Surmado()
        self.assertEqual(client.api_key, "sur_test_from_env")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_key_raises(self):
        with self.assertRaises(AuthenticationError):
            Surmado()

    def test_init_empty_string_raises(self):
        with self.assertRaises(AuthenticationError):
            Surmado(api_key="")

    def test_default_base_url(self):
        client = Surmado(api_key="sur_test_x")
        self.assertEqual(client.base_url, "https://api.surmado.com/v1")

    def test_custom_base_url(self):
        client = Surmado(api_key="sur_test_x", base_url="http://localhost:8000")
        self.assertEqual(client.base_url, "http://localhost:8000")

    def test_default_timeout(self):
        client = Surmado(api_key="sur_test_x")
        self.assertEqual(client.timeout, 30)

    def test_custom_timeout(self):
        client = Surmado(api_key="sur_test_x", timeout=60)
        self.assertEqual(client.timeout, 60)

    @patch.dict(os.environ, {"SURMADO_API_KEY": "sur_env_key"})
    def test_explicit_key_overrides_env(self):
        client = Surmado(api_key="sur_explicit_key")
        self.assertEqual(client.api_key, "sur_explicit_key")

    def test_base_url_trailing_slash_preserved(self):
        client = Surmado(api_key="sur_test_x", base_url="http://localhost:8000/")
        self.assertEqual(client.base_url, "http://localhost:8000/")

    def test_timeout_zero(self):
        client = Surmado(api_key="sur_test_x", timeout=0)
        self.assertEqual(client.timeout, 0)


# =============================================================================
# URL Normalization
# =============================================================================


class TestUrlNormalization(unittest.TestCase):
    """Test _normalize_url behavior."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    def test_adds_https(self):
        self.assertEqual(self.client._normalize_url("example.com"), "https://example.com")

    def test_preserves_https(self):
        self.assertEqual(self.client._normalize_url("https://example.com"), "https://example.com")

    def test_preserves_http(self):
        self.assertEqual(self.client._normalize_url("http://example.com"), "http://example.com")

    def test_none_returns_none(self):
        self.assertIsNone(self.client._normalize_url(None))

    def test_empty_string(self):
        self.assertEqual(self.client._normalize_url(""), "")

    def test_subdomain(self):
        self.assertEqual(self.client._normalize_url("sub.example.com"), "https://sub.example.com")

    def test_with_path(self):
        self.assertEqual(self.client._normalize_url("example.com/path"), "https://example.com/path")

    def test_with_port(self):
        self.assertEqual(self.client._normalize_url("example.com:8080"), "https://example.com:8080")

    def test_https_with_path(self):
        self.assertEqual(
            self.client._normalize_url("https://example.com/path?q=1"),
            "https://example.com/path?q=1"
        )


# =============================================================================
# Headers
# =============================================================================


class TestHeaders(unittest.TestCase):
    """Test request headers."""

    def test_headers_include_api_key(self):
        client = Surmado(api_key="sur_test_mykey")
        headers = client._headers()
        self.assertEqual(headers["X-API-Key"], "sur_test_mykey")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_headers_user_agent_version(self):
        client = Surmado(api_key="sur_test_x")
        headers = client._headers()
        self.assertEqual(headers["User-Agent"], f"surmado-python/{__version__}")

    def test_headers_user_agent_matches_version(self):
        client = Surmado(api_key="sur_test_x")
        headers = client._headers()
        self.assertIn("0.3.1", headers["User-Agent"])

    def test_headers_has_three_keys(self):
        client = Surmado(api_key="sur_test_x")
        headers = client._headers()
        self.assertEqual(len(headers), 3)


# =============================================================================
# Error Extraction
# =============================================================================


class TestErrorExtraction(unittest.TestCase):
    """Test _extract_error_message handles all API response formats."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    def test_canonical_format(self):
        data = {"detail": {"error": {"code": "insufficient_credits", "message": "Not enough credits"}}}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "Not enough credits")

    def test_detail_with_message(self):
        data = {"detail": {"message": "Some error"}}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "Some error")

    def test_detail_as_string(self):
        data = {"detail": "Validation failed: email is required"}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "Validation failed: email is required")

    def test_top_level_message(self):
        data = {"message": "Server error"}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "Server error")

    def test_top_level_error(self):
        data = {"error": "Something went wrong"}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "Something went wrong")

    def test_fallback(self):
        data = {}
        self.assertEqual(self.client._extract_error_message(data, "my fallback"), "my fallback")

    def test_canonical_takes_priority_over_top_level(self):
        data = {
            "detail": {"error": {"code": "x", "message": "canonical msg"}},
            "message": "top level msg",
        }
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "canonical msg")

    def test_detail_message_takes_priority_over_top_level(self):
        data = {
            "detail": {"message": "detail msg"},
            "message": "top level msg",
        }
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "detail msg")

    def test_detail_string_takes_priority_over_top_level(self):
        data = {
            "detail": "detail string",
            "message": "top level msg",
        }
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "detail string")

    def test_detail_dict_without_error_or_message(self):
        data = {"detail": {"something_else": "value"}}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "fallback")

    def test_detail_dict_with_error_but_no_message(self):
        data = {"detail": {"error": {"code": "x"}}}
        # error dict exists but no "message" key → falls through
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "fallback")

    def test_detail_list_falls_through(self):
        data = {"detail": [{"msg": "field required"}]}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "fallback")

    def test_message_preferred_over_error_at_top_level(self):
        data = {"message": "msg", "error": "err"}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "msg")

    def test_top_level_error_when_no_message(self):
        data = {"error": "only error"}
        self.assertEqual(self.client._extract_error_message(data, "fallback"), "only error")


# =============================================================================
# Handle Response (status code → exception mapping)
# =============================================================================


class TestHandleResponse(unittest.TestCase):
    """Test _handle_response maps status codes to correct exceptions."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    def _mock_response(self, status_code, body):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = body
        resp.text = json.dumps(body)
        return resp

    # --- Success codes ---

    def test_200_returns_data(self):
        resp = self._mock_response(200, {"report_id": "rpt_123"})
        result = self.client._handle_response(resp)
        self.assertEqual(result["report_id"], "rpt_123")

    def test_201_returns_data(self):
        resp = self._mock_response(201, {"brand_slug": "test"})
        result = self.client._handle_response(resp)
        self.assertEqual(result["brand_slug"], "test")

    def test_202_returns_data(self):
        resp = self._mock_response(202, {"report_id": "rpt_123", "status": "queued"})
        result = self.client._handle_response(resp)
        self.assertEqual(result["status"], "queued")

    def test_204_empty_body(self):
        resp = self._mock_response(204, {})
        result = self.client._handle_response(resp)
        self.assertEqual(result, {})

    # --- Error codes ---

    def test_400_raises_validation_error(self):
        resp = self._mock_response(400, {"detail": {"error": {"code": "invalid", "message": "Bad request"}}})
        with self.assertRaises(ValidationError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Bad request", str(ctx.exception))

    def test_401_raises_auth_error(self):
        resp = self._mock_response(401, {"detail": "Unauthorized"})
        with self.assertRaises(AuthenticationError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Unauthorized", str(ctx.exception))

    def test_402_raises_credits_error(self):
        resp = self._mock_response(402, {"detail": {"error": {"code": "insufficient_credits", "message": "No credits"}}})
        with self.assertRaises(InsufficientCreditsError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertIn("No credits", str(ctx.exception))

    def test_404_raises_not_found(self):
        resp = self._mock_response(404, {"detail": {"error": {"code": "brand_not_found", "message": "Brand not found"}}})
        with self.assertRaises(NotFoundError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_422_raises_validation_error(self):
        resp = self._mock_response(422, {"detail": "Missing required field: email"})
        with self.assertRaises(ValidationError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("Missing required field", str(ctx.exception))

    def test_429_raises_rate_limit(self):
        resp = self._mock_response(429, {"detail": {"error": {"code": "rate_limited", "message": "Too many requests"}}})
        with self.assertRaises(RateLimitError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("Too many requests", str(ctx.exception))

    def test_500_raises_surmado_error(self):
        resp = self._mock_response(500, {"error": "Internal server error"})
        with self.assertRaises(SurmadoError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 500)

    def test_502_raises_surmado_error(self):
        resp = self._mock_response(502, {"error": "Bad Gateway"})
        with self.assertRaises(SurmadoError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 502)

    def test_503_raises_surmado_error(self):
        resp = self._mock_response(503, {"message": "Service Unavailable"})
        with self.assertRaises(SurmadoError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.status_code, 503)

    def test_invalid_json_response(self):
        resp = MagicMock()
        resp.status_code = 500
        resp.json.side_effect = ValueError("No JSON")
        resp.text = "Internal Server Error"
        with self.assertRaises(SurmadoError):
            self.client._handle_response(resp)

    def test_invalid_json_uses_text_as_error(self):
        resp = MagicMock()
        resp.status_code = 500
        resp.json.side_effect = ValueError("No JSON")
        resp.text = "Gateway Timeout"
        with self.assertRaises(SurmadoError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.response, {"error": "Gateway Timeout"})

    def test_error_response_includes_response_data(self):
        body = {"detail": {"error": {"code": "x", "message": "test"}}}
        resp = self._mock_response(401, body)
        with self.assertRaises(AuthenticationError) as ctx:
            self.client._handle_response(resp)
        self.assertEqual(ctx.exception.response, body)

    def test_400_with_empty_body_uses_fallback(self):
        resp = self._mock_response(400, {})
        with self.assertRaises(ValidationError) as ctx:
            self.client._handle_response(resp)
        self.assertIn("Invalid request data", str(ctx.exception))

    def test_401_with_empty_body_uses_fallback(self):
        resp = self._mock_response(401, {})
        with self.assertRaises(AuthenticationError) as ctx:
            self.client._handle_response(resp)
        self.assertIn("Invalid or missing API key", str(ctx.exception))

    def test_402_with_empty_body_uses_fallback(self):
        resp = self._mock_response(402, {})
        with self.assertRaises(InsufficientCreditsError) as ctx:
            self.client._handle_response(resp)
        self.assertIn("Insufficient credits", str(ctx.exception))

    def test_404_with_empty_body_uses_fallback(self):
        resp = self._mock_response(404, {})
        with self.assertRaises(NotFoundError) as ctx:
            self.client._handle_response(resp)
        self.assertIn("Resource not found", str(ctx.exception))

    def test_429_with_empty_body_uses_fallback(self):
        resp = self._mock_response(429, {})
        with self.assertRaises(RateLimitError) as ctx:
            self.client._handle_response(resp)
        self.assertIn("Rate limit exceeded", str(ctx.exception))

    def test_500_with_empty_body_uses_fallback(self):
        resp = self._mock_response(500, {})
        with self.assertRaises(SurmadoError) as ctx:
            self.client._handle_response(resp)
        self.assertIn("API error: 500", str(ctx.exception))


# =============================================================================
# Internal HTTP Methods (_post, _get, _delete)
# =============================================================================


class TestPostMethod(unittest.TestCase):
    """Test _post builds correct requests."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_key", base_url="https://api.test.com/v1")

    @patch("requests.post")
    def test_post_calls_requests(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_post.return_value = mock_resp

        result = self.client._post("/reports/signal", {"url": "https://example.com"})

        mock_post.assert_called_once_with(
            "https://api.test.com/v1/reports/signal",
            json={"url": "https://example.com"},
            headers=self.client._headers(),
            timeout=30,
        )
        self.assertEqual(result, {"ok": True})

    @patch("requests.post")
    def test_post_custom_timeout(self, mock_post):
        client = Surmado(api_key="sur_test_x", timeout=120)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        client._post("/test", {})
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["timeout"], 120)


class TestGetMethod(unittest.TestCase):
    """Test _get builds correct requests."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_key", base_url="https://api.test.com/v1")

    @patch("requests.get")
    def test_get_calls_requests(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "completed"}
        mock_get.return_value = mock_resp

        result = self.client._get("/reports/rpt_123")

        mock_get.assert_called_once_with(
            "https://api.test.com/v1/reports/rpt_123",
            headers=self.client._headers(),
            timeout=30,
        )
        self.assertEqual(result, {"status": "completed"})


class TestDeleteMethod(unittest.TestCase):
    """Test _delete builds correct requests."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_key", base_url="https://api.test.com/v1")

    @patch("requests.delete")
    def test_delete_calls_requests(self, mock_delete):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"deleted": True}
        mock_delete.return_value = mock_resp

        result = self.client._delete("/brands/test_brand")

        mock_delete.assert_called_once_with(
            "https://api.test.com/v1/brands/test_brand",
            headers=self.client._headers(),
            timeout=30,
        )
        self.assertEqual(result, {"deleted": True})


# =============================================================================
# Signal Method
# =============================================================================


class TestSignalMethod(unittest.TestCase):
    """Test signal() payload construction and behavior."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")
        self.base_args = {
            "url": "https://example.com",
            "brand_name": "Test",
            "email": "test@test.com",
            "industry": "Tech",
            "location": "US",
            "persona": "Devs",
            "pain_points": "Bugs",
            "brand_details": "Good software",
            "direct_competitors": "Other, Co",
        }

    @patch.object(Surmado, "_post")
    def test_signal_payload_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123", "status": "queued"}
        self.client.signal(**self.base_args)
        payload = mock_post.call_args[0][1]
        self.assertNotIn("tier", payload)

    @patch.object(Surmado, "_post")
    def test_signal_endpoint(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal(**self.base_args)
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/reports/signal")

    @patch.object(Surmado, "_post")
    def test_signal_all_required_fields(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal(**self.base_args)
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["url"], "https://example.com")
        self.assertEqual(payload["brand_name"], "Test")
        self.assertEqual(payload["email"], "test@test.com")
        self.assertEqual(payload["industry"], "Tech")
        self.assertEqual(payload["location"], "US")
        self.assertEqual(payload["persona"], "Devs")
        self.assertEqual(payload["pain_points"], "Bugs")
        self.assertEqual(payload["brand_details"], "Good software")
        self.assertEqual(payload["direct_competitors"], "Other, Co")

    @patch.object(Surmado, "_post")
    def test_signal_normalizes_url(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        args = {**self.base_args, "url": "example.com"}
        self.client.signal(**args)
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["url"], "https://example.com")

    @patch.object(Surmado, "_post")
    def test_signal_with_webhook_url(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal(**self.base_args, webhook_url="https://hook.example.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["webhook_url"], "https://hook.example.com")

    @patch.object(Surmado, "_post")
    def test_signal_with_optional_kwargs(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal(
            **self.base_args,
            indirect_competitors="Alt solutions",
            keywords="seo, marketing",
            product="Dashboard tool",
            business_scale="large",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["indirect_competitors"], "Alt solutions")
        self.assertEqual(payload["keywords"], "seo, marketing")
        self.assertEqual(payload["product"], "Dashboard tool")
        self.assertEqual(payload["business_scale"], "large")

    @patch.object(Surmado, "_post")
    def test_signal_returns_response(self, mock_post):
        expected = {"report_id": "rpt_abc", "status": "queued", "credits_used": 2, "token": "tok_xyz"}
        mock_post.return_value = expected
        result = self.client.signal(**self.base_args)
        self.assertEqual(result, expected)


# =============================================================================
# Scan Method
# =============================================================================


class TestScanMethod(unittest.TestCase):
    """Test scan() payload construction and behavior."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_post")
    def test_scan_payload_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123", "status": "queued"}
        self.client.scan(url="example.com", brand_name="Test", email="test@test.com")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("tier", payload)

    @patch.object(Surmado, "_post")
    def test_scan_normalizes_url(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan(url="example.com", brand_name="Test", email="test@test.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["url"], "https://example.com")

    @patch.object(Surmado, "_post")
    def test_scan_endpoint(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan(url="https://example.com", brand_name="Test", email="test@test.com")
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/reports/scan")

    @patch.object(Surmado, "_post")
    def test_scan_with_competitor_urls(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan(
            url="https://example.com",
            brand_name="Test",
            email="test@test.com",
            competitor_urls=["https://comp1.com", "https://comp2.com"],
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["competitor_urls"], ["https://comp1.com", "https://comp2.com"])

    @patch.object(Surmado, "_post")
    def test_scan_with_report_style(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan(
            url="https://example.com",
            brand_name="Test",
            email="test@test.com",
            report_style="technical",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["report_style"], "technical")

    @patch.object(Surmado, "_post")
    def test_scan_with_webhook_url(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan(
            url="https://example.com",
            brand_name="Test",
            email="test@test.com",
            webhook_url="https://hook.example.com",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["webhook_url"], "https://hook.example.com")


# =============================================================================
# Solutions Method
# =============================================================================


class TestSolutionsMethod(unittest.TestCase):
    """Test solutions() mode logic and payload construction."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    # --- Token Mode ---

    @patch.object(Surmado, "_post")
    def test_solutions_signal_token_mode(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123", "status": "queued"}
        self.client.solutions(email="test@test.com", signal_token="tok_abc")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["signal_token"], "tok_abc")
        self.assertEqual(payload["email"], "test@test.com")
        self.assertNotIn("tier", payload)

    @patch.object(Surmado, "_post")
    def test_solutions_token_with_scan_token(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(email="t@t.com", signal_token="tok_sig", scan_token="tok_scan")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["signal_token"], "tok_sig")
        self.assertEqual(payload["scan_token"], "tok_scan")

    @patch.object(Surmado, "_post")
    def test_solutions_token_with_brand_name(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(email="t@t.com", signal_token="tok_sig", brand_name="Acme")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["signal_token"], "tok_sig")
        self.assertEqual(payload["brand_name"], "Acme")

    @patch.object(Surmado, "_post")
    def test_solutions_token_mode_no_standalone_fields(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(email="t@t.com", signal_token="tok_sig")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("business_story", payload)
        self.assertNotIn("decision", payload)
        self.assertNotIn("success", payload)

    # --- Standalone Mode ---

    @patch.object(Surmado, "_post")
    def test_solutions_standalone_mode(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(
            email="t@t.com",
            brand_name="Acme",
            business_story="We do things",
            decision="Expand or not",
            success="$10M ARR",
            timeline="Q2 2025",
            scale_indicator="Small",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["brand_name"], "Acme")
        self.assertEqual(payload["business_story"], "We do things")
        self.assertEqual(payload["decision"], "Expand or not")
        self.assertEqual(payload["success"], "$10M ARR")
        self.assertEqual(payload["timeline"], "Q2 2025")
        self.assertEqual(payload["scale_indicator"], "Small")
        self.assertNotIn("signal_token", payload)

    @patch.object(Surmado, "_post")
    def test_solutions_standalone_with_scan_token(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(
            email="t@t.com",
            brand_name="Acme",
            business_story="Story",
            decision="D",
            success="S",
            timeline="T",
            scale_indicator="SI",
            scan_token="tok_scan",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["scan_token"], "tok_scan")
        self.assertNotIn("signal_token", payload)

    def test_solutions_standalone_missing_brand_name_raises(self):
        with self.assertRaises(ValidationError):
            self.client.solutions(email="t@t.com", brand_name="Test")

    def test_solutions_standalone_missing_business_story_raises(self):
        with self.assertRaises(ValidationError):
            self.client.solutions(
                email="t@t.com",
                brand_name="Test",
                decision="D",
                success="S",
                timeline="T",
                scale_indicator="SI",
            )

    def test_solutions_standalone_missing_decision_raises(self):
        with self.assertRaises(ValidationError):
            self.client.solutions(
                email="t@t.com",
                brand_name="Test",
                business_story="Story",
                success="S",
                timeline="T",
                scale_indicator="SI",
            )

    def test_solutions_standalone_missing_all_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            self.client.solutions(email="t@t.com")
        self.assertIn("brand_name", str(ctx.exception))

    def test_solutions_standalone_missing_success_raises(self):
        with self.assertRaises(ValidationError):
            self.client.solutions(
                email="t@t.com",
                brand_name="Test",
                business_story="Story",
                decision="D",
                timeline="T",
                scale_indicator="SI",
            )

    def test_solutions_standalone_missing_timeline_raises(self):
        with self.assertRaises(ValidationError):
            self.client.solutions(
                email="t@t.com",
                brand_name="Test",
                business_story="Story",
                decision="D",
                success="S",
                scale_indicator="SI",
            )

    def test_solutions_standalone_missing_scale_raises(self):
        with self.assertRaises(ValidationError):
            self.client.solutions(
                email="t@t.com",
                brand_name="Test",
                business_story="Story",
                decision="D",
                success="S",
                timeline="T",
            )

    # --- Financial kwargs ---

    @patch.object(Surmado, "_post")
    def test_solutions_with_financial_kwargs(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(
            email="t@t.com",
            signal_token="tok_sig",
            include_financial="yes",
            financial_context="Growing startup",
            monthly_revenue="$50k",
            monthly_costs="$30k",
            cash_available="$200k",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["include_financial"], "yes")
        self.assertEqual(payload["financial_context"], "Growing startup")
        self.assertEqual(payload["monthly_revenue"], "$50k")
        self.assertEqual(payload["monthly_costs"], "$30k")
        self.assertEqual(payload["cash_available"], "$200k")

    @patch.object(Surmado, "_post")
    def test_solutions_endpoint(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(email="t@t.com", signal_token="tok_sig")
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/reports/solutions")

    @patch.object(Surmado, "_post")
    def test_solutions_with_webhook_url(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(
            email="t@t.com",
            signal_token="tok_sig",
            webhook_url="https://hook.example.com",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["webhook_url"], "https://hook.example.com")


# =============================================================================
# Signal Rerun Method
# =============================================================================


class TestSignalRerunMethod(unittest.TestCase):
    """Test signal_rerun() payload construction."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_post")
    def test_signal_rerun_payload(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123", "status": "queued"}
        self.client.signal_rerun(brand_slug="test_brand", persona_slug="cto", email="test@test.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["brand_slug"], "test_brand")
        self.assertEqual(payload["persona_slug"], "cto")
        self.assertEqual(payload["email"], "test@test.com")

    @patch.object(Surmado, "_post")
    def test_signal_rerun_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal_rerun(brand_slug="b", persona_slug="p", email="e@e.com")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("tier", payload)

    @patch.object(Surmado, "_post")
    def test_signal_rerun_endpoint(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal_rerun(brand_slug="b", persona_slug="p", email="e@e.com")
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/reports/signal/rerun")

    @patch.object(Surmado, "_post")
    def test_signal_rerun_only_three_fields(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal_rerun(brand_slug="b", persona_slug="p", email="e@e.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(len(payload), 3)


# =============================================================================
# Scan Rerun Method
# =============================================================================


class TestScanRerunMethod(unittest.TestCase):
    """Test scan_rerun() payload construction."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_post")
    def test_scan_rerun_payload(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123", "status": "queued"}
        self.client.scan_rerun(brand_slug="test_brand", email="test@test.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["brand_slug"], "test_brand")
        self.assertEqual(payload["email"], "test@test.com")

    @patch.object(Surmado, "_post")
    def test_scan_rerun_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan_rerun(brand_slug="b", email="e@e.com")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("tier", payload)

    @patch.object(Surmado, "_post")
    def test_scan_rerun_endpoint(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan_rerun(brand_slug="b", email="e@e.com")
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/reports/scan/rerun")

    @patch.object(Surmado, "_post")
    def test_scan_rerun_only_two_fields(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan_rerun(brand_slug="b", email="e@e.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(len(payload), 2)


# =============================================================================
# Get Report Method
# =============================================================================


class TestGetReportMethod(unittest.TestCase):
    """Test get_report() calls correct endpoint."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_get")
    def test_get_report_endpoint(self, mock_get):
        mock_get.return_value = {"status": "completed"}
        self.client.get_report("rpt_abc123")
        mock_get.assert_called_once_with("/reports/rpt_abc123")

    @patch.object(Surmado, "_get")
    def test_get_report_returns_response(self, mock_get):
        expected = {"status": "completed", "download_url": "https://cdn.example.com/report.pdf"}
        mock_get.return_value = expected
        result = self.client.get_report("rpt_abc123")
        self.assertEqual(result, expected)


# =============================================================================
# Get Report Data Method
# =============================================================================


class TestGetReportDataMethod(unittest.TestCase):
    """Test get_report_data() with and without field filtering."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_get")
    def test_get_report_data_no_fields(self, mock_get):
        mock_get.return_value = {"status": "completed", "insights": []}
        self.client.get_report_data("rpt_abc123")
        mock_get.assert_called_once_with("/reports/rpt_abc123/data")

    @patch.object(Surmado, "_get")
    def test_get_report_data_with_fields(self, mock_get):
        mock_get.return_value = {"status": "completed"}
        self.client.get_report_data("rpt_abc123", fields=["status", "insights"])
        mock_get.assert_called_once_with("/reports/rpt_abc123/data?fields=status,insights")

    @patch.object(Surmado, "_get")
    def test_get_report_data_single_field(self, mock_get):
        mock_get.return_value = {"status": "completed"}
        self.client.get_report_data("rpt_abc123", fields=["status"])
        mock_get.assert_called_once_with("/reports/rpt_abc123/data?fields=status")

    @patch.object(Surmado, "_get")
    def test_get_report_data_empty_fields_list(self, mock_get):
        mock_get.return_value = {}
        self.client.get_report_data("rpt_abc123", fields=[])
        mock_get.assert_called_once_with("/reports/rpt_abc123/data")

    @patch.object(Surmado, "_get")
    def test_get_report_data_none_fields(self, mock_get):
        mock_get.return_value = {}
        self.client.get_report_data("rpt_abc123", fields=None)
        mock_get.assert_called_once_with("/reports/rpt_abc123/data")


# =============================================================================
# List Reports Method
# =============================================================================


class TestListReportsMethod(unittest.TestCase):
    """Test list_reports() pagination parameters."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_get")
    def test_list_reports_defaults(self, mock_get):
        mock_get.return_value = {"reports": []}
        self.client.list_reports()
        mock_get.assert_called_once_with("/reports?page=1&page_size=50")

    @patch.object(Surmado, "_get")
    def test_list_reports_custom_page(self, mock_get):
        mock_get.return_value = {"reports": []}
        self.client.list_reports(page=3)
        mock_get.assert_called_once_with("/reports?page=3&page_size=50")

    @patch.object(Surmado, "_get")
    def test_list_reports_custom_page_size(self, mock_get):
        mock_get.return_value = {"reports": []}
        self.client.list_reports(page_size=10)
        mock_get.assert_called_once_with("/reports?page=1&page_size=10")

    @patch.object(Surmado, "_get")
    def test_list_reports_both_params(self, mock_get):
        mock_get.return_value = {"reports": []}
        self.client.list_reports(page=2, page_size=25)
        mock_get.assert_called_once_with("/reports?page=2&page_size=25")


# =============================================================================
# Wait For Report Method
# =============================================================================


class TestWaitForReport(unittest.TestCase):
    """Test wait_for_report polling logic."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "get_report")
    def test_returns_on_completed(self, mock_get):
        mock_get.return_value = {"status": "completed", "download_url": "https://example.com/pdf"}
        result = self.client.wait_for_report("rpt_123", timeout_minutes=1, poll_interval=0)
        self.assertEqual(result["status"], "completed")
        mock_get.assert_called_once_with("rpt_123")

    @patch.object(Surmado, "get_report")
    def test_raises_on_failed(self, mock_get):
        mock_get.return_value = {"status": "failed", "error": "Generation failed"}
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_123", timeout_minutes=1, poll_interval=0)
        self.assertIn("Generation failed", str(ctx.exception))

    @patch.object(Surmado, "get_report")
    def test_raises_on_failed_no_error_msg(self, mock_get):
        mock_get.return_value = {"status": "failed"}
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_123", timeout_minutes=1, poll_interval=0)
        self.assertIn("Report processing failed", str(ctx.exception))

    @patch.object(Surmado, "get_report")
    def test_raises_on_cancelled(self, mock_get):
        mock_get.return_value = {"status": "cancelled"}
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_123", timeout_minutes=1, poll_interval=0)
        self.assertIn("cancelled", str(ctx.exception))

    @patch("time.sleep", return_value=None)
    @patch("time.time")
    @patch.object(Surmado, "get_report")
    def test_timeout(self, mock_get, mock_time, mock_sleep):
        mock_get.return_value = {"status": "processing"}
        mock_time.side_effect = [0, 0, 61]
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_123", timeout_minutes=1, poll_interval=1)
        self.assertIn("did not complete", str(ctx.exception))

    @patch("time.sleep", return_value=None)
    @patch("time.time")
    @patch.object(Surmado, "get_report")
    def test_timeout_response_includes_report_id(self, mock_get, mock_time, mock_sleep):
        mock_get.return_value = {"status": "processing"}
        mock_time.side_effect = [0, 0, 61]
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_xyz", timeout_minutes=1, poll_interval=1)
        self.assertEqual(ctx.exception.response["report_id"], "rpt_xyz")
        self.assertEqual(ctx.exception.response["status"], "timeout")

    @patch("time.sleep", return_value=None)
    @patch.object(Surmado, "get_report")
    def test_polls_until_completed(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            {"status": "queued"},
            {"status": "processing"},
            {"status": "completed", "download_url": "https://cdn.example.com/report.pdf"},
        ]
        result = self.client.wait_for_report("rpt_123", timeout_minutes=10, poll_interval=1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep", return_value=None)
    @patch.object(Surmado, "get_report")
    def test_uses_poll_interval(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            {"status": "queued"},
            {"status": "completed"},
        ]
        self.client.wait_for_report("rpt_123", timeout_minutes=10, poll_interval=15)
        mock_sleep.assert_called_once_with(15)

    @patch.object(Surmado, "get_report")
    def test_failed_preserves_response(self, mock_get):
        report = {"status": "failed", "error": "Provider timeout"}
        mock_get.return_value = report
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_123", poll_interval=0)
        self.assertEqual(ctx.exception.response, report)

    @patch.object(Surmado, "get_report")
    def test_cancelled_preserves_response(self, mock_get):
        report = {"status": "cancelled"}
        mock_get.return_value = report
        with self.assertRaises(SurmadoError) as ctx:
            self.client.wait_for_report("rpt_123", poll_interval=0)
        self.assertEqual(ctx.exception.response, report)


# =============================================================================
# Brand Management Methods
# =============================================================================


class TestListBrandsMethod(unittest.TestCase):
    """Test list_brands() calls correct endpoint."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_get")
    def test_list_brands_endpoint(self, mock_get):
        mock_get.return_value = {"brands": []}
        self.client.list_brands()
        mock_get.assert_called_once_with("/brands")

    @patch.object(Surmado, "_get")
    def test_list_brands_returns_data(self, mock_get):
        expected = {"brands": [{"brand_slug": "acme", "brand_name": "Acme Corp"}]}
        mock_get.return_value = expected
        result = self.client.list_brands()
        self.assertEqual(result, expected)


class TestCreateBrandMethod(unittest.TestCase):
    """Test create_brand() payload construction."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_post")
    def test_create_brand_minimal(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme Corp")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["brand_name"], "Acme Corp")
        self.assertNotIn("website", payload)
        self.assertNotIn("industry", payload)

    @patch.object(Surmado, "_post")
    def test_create_brand_with_website(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme Corp", website="acme.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["website"], "https://acme.com")

    @patch.object(Surmado, "_post")
    def test_create_brand_website_normalization(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme", website="https://acme.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["website"], "https://acme.com")

    @patch.object(Surmado, "_post")
    def test_create_brand_with_industry(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme", industry="B2B SaaS")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["industry"], "B2B SaaS")

    @patch.object(Surmado, "_post")
    def test_create_brand_with_all_fields(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme", website="acme.com", industry="Tech")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["brand_name"], "Acme")
        self.assertEqual(payload["website"], "https://acme.com")
        self.assertEqual(payload["industry"], "Tech")

    @patch.object(Surmado, "_post")
    def test_create_brand_with_kwargs(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme", location="US", persona="CTOs")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["location"], "US")
        self.assertEqual(payload["persona"], "CTOs")

    @patch.object(Surmado, "_post")
    def test_create_brand_endpoint(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme")
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/brands")

    @patch.object(Surmado, "_post")
    def test_create_brand_none_website_not_included(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme", website=None)
        payload = mock_post.call_args[0][1]
        self.assertNotIn("website", payload)

    @patch.object(Surmado, "_post")
    def test_create_brand_none_industry_not_included(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.create_brand(brand_name="Acme", industry=None)
        payload = mock_post.call_args[0][1]
        self.assertNotIn("industry", payload)


class TestEnsureBrandMethod(unittest.TestCase):
    """Test ensure_brand() payload construction."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_post")
    def test_ensure_brand_minimal(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.ensure_brand(brand_name="Acme Corp")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["brand_name"], "Acme Corp")

    @patch.object(Surmado, "_post")
    def test_ensure_brand_endpoint(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.ensure_brand(brand_name="Acme")
        endpoint = mock_post.call_args[0][0]
        self.assertEqual(endpoint, "/brands/ensure")

    @patch.object(Surmado, "_post")
    def test_ensure_brand_with_website(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.ensure_brand(brand_name="Acme", website="acme.com")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["website"], "https://acme.com")

    @patch.object(Surmado, "_post")
    def test_ensure_brand_with_industry(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.ensure_brand(brand_name="Acme", industry="SaaS")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["industry"], "SaaS")

    @patch.object(Surmado, "_post")
    def test_ensure_brand_with_kwargs(self, mock_post):
        mock_post.return_value = {"brand_slug": "acme"}
        self.client.ensure_brand(brand_name="Acme", custom_field="value")
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["custom_field"], "value")


# =============================================================================
# Test Auth Method
# =============================================================================


class TestTestAuthMethod(unittest.TestCase):
    """Test test_auth() calls correct endpoint."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_get")
    def test_test_auth_endpoint(self, mock_get):
        mock_get.return_value = {"authenticated": True, "org_id": "org_123"}
        self.client.test_auth()
        mock_get.assert_called_once_with("/test-auth")

    @patch.object(Surmado, "_get")
    def test_test_auth_returns_data(self, mock_get):
        expected = {"authenticated": True, "org_id": "org_123", "credits_remaining": 10}
        mock_get.return_value = expected
        result = self.client.test_auth()
        self.assertEqual(result, expected)


# =============================================================================
# Version
# =============================================================================


class TestVersion(unittest.TestCase):
    """Test version is accessible and correct."""

    def test_version_string(self):
        self.assertEqual(__version__, "0.3.1")

    def test_version_from_client_module(self):
        from surmado.client import __version__ as client_version
        self.assertEqual(client_version, "0.3.1")

    def test_version_matches(self):
        from surmado.client import __version__ as client_version
        self.assertEqual(__version__, client_version)


# =============================================================================
# Module Exports
# =============================================================================


class TestModuleExports(unittest.TestCase):
    """Test that all public classes are exported from the package."""

    def test_surmado_class_exported(self):
        import surmado
        self.assertTrue(hasattr(surmado, "Surmado"))

    def test_all_exceptions_exported(self):
        import surmado
        for cls_name in [
            "SurmadoError",
            "AuthenticationError",
            "InsufficientCreditsError",
            "NotFoundError",
            "ValidationError",
            "RateLimitError",
        ]:
            self.assertTrue(hasattr(surmado, cls_name), f"{cls_name} not exported")

    def test_version_exported(self):
        import surmado
        self.assertTrue(hasattr(surmado, "__version__"))

    def test_all_list(self):
        import surmado
        expected = [
            "Surmado",
            "SurmadoError",
            "AuthenticationError",
            "InsufficientCreditsError",
            "NotFoundError",
            "ValidationError",
            "RateLimitError",
            "__version__",
        ]
        for name in expected:
            self.assertIn(name, surmado.__all__)


# =============================================================================
# Integration-style tests (mocking at requests level)
# =============================================================================


class TestEndToEndSignal(unittest.TestCase):
    """Test signal flow from client method to HTTP request."""

    @patch("requests.post")
    def test_signal_full_flow(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.json.return_value = {
            "report_id": "rpt_abc",
            "status": "queued",
            "credits_used": 2,
            "token": "tok_xyz",
        }
        mock_post.return_value = mock_resp

        client = Surmado(api_key="sur_test_key123")
        result = client.signal(
            url="example.com",
            brand_name="Test Brand",
            email="dev@test.com",
            industry="Technology",
            location="United States",
            persona="Engineering managers",
            pain_points="Slow deployments, poor visibility",
            brand_details="Developer productivity tools",
            direct_competitors="GitLab, GitHub",
        )

        self.assertEqual(result["report_id"], "rpt_abc")
        self.assertEqual(result["token"], "tok_xyz")

        # Verify the actual HTTP call
        call_kwargs = mock_post.call_args
        self.assertEqual(call_kwargs[0][0], "https://api.surmado.com/v1/reports/signal")
        sent_payload = call_kwargs[1]["json"]
        self.assertEqual(sent_payload["url"], "https://example.com")  # normalized
        self.assertEqual(sent_payload["brand_name"], "Test Brand")
        self.assertNotIn("tier", sent_payload)
        headers = call_kwargs[1]["headers"]
        self.assertEqual(headers["X-API-Key"], "sur_test_key123")

    @patch("requests.post")
    def test_signal_401_flow(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"detail": "Invalid API key"}
        mock_resp.text = '{"detail": "Invalid API key"}'
        mock_post.return_value = mock_resp

        client = Surmado(api_key="sur_test_bad_key")
        with self.assertRaises(AuthenticationError) as ctx:
            client.signal(
                url="example.com",
                brand_name="Test",
                email="t@t.com",
                industry="Tech",
                location="US",
                persona="Devs",
                pain_points="Bugs",
                brand_details="Tools",
                direct_competitors="Others",
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid API key", str(ctx.exception))

    @patch("requests.post")
    def test_signal_402_flow(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 402
        mock_resp.json.return_value = {
            "detail": {"error": {"code": "insufficient_credits", "message": "Need 2 credits, have 0"}}
        }
        mock_resp.text = "{}"
        mock_post.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        with self.assertRaises(InsufficientCreditsError) as ctx:
            client.signal(
                url="example.com",
                brand_name="Test",
                email="t@t.com",
                industry="Tech",
                location="US",
                persona="Devs",
                pain_points="Bugs",
                brand_details="Tools",
                direct_competitors="Others",
            )
        self.assertIn("Need 2 credits", str(ctx.exception))


class TestEndToEndScan(unittest.TestCase):
    """Test scan flow from client method to HTTP request."""

    @patch("requests.post")
    def test_scan_full_flow(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.json.return_value = {"report_id": "rpt_scan_1", "status": "queued", "credits_used": 2}
        mock_post.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        result = client.scan(url="mysite.com", brand_name="MySite", email="dev@mysite.com")

        self.assertEqual(result["report_id"], "rpt_scan_1")
        call_kwargs = mock_post.call_args
        sent_payload = call_kwargs[1]["json"]
        self.assertEqual(sent_payload["url"], "https://mysite.com")
        self.assertNotIn("tier", sent_payload)


class TestEndToEndGetReport(unittest.TestCase):
    """Test get_report flow."""

    @patch("requests.get")
    def test_get_report_completed(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "report_id": "rpt_123",
            "status": "completed",
            "download_url": "https://cdn.example.com/report.pdf",
            "pptx_download_url": "https://cdn.example.com/report.pptx",
        }
        mock_get.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        result = client.get_report("rpt_123")

        self.assertEqual(result["status"], "completed")
        self.assertIn("download_url", result)
        self.assertIn("pptx_download_url", result)

    @patch("requests.get")
    def test_get_report_404(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {
            "detail": {"error": {"code": "report_not_found", "message": "Report not found"}}
        }
        mock_resp.text = "{}"
        mock_get.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        with self.assertRaises(NotFoundError):
            client.get_report("rpt_nonexistent")


class TestEndToEndBrands(unittest.TestCase):
    """Test brand management flow."""

    @patch("requests.get")
    def test_list_brands_flow(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "brands": [
                {"brand_slug": "acme", "brand_name": "Acme Corp"},
                {"brand_slug": "test_co", "brand_name": "Test Co"},
            ]
        }
        mock_get.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        result = client.list_brands()
        self.assertEqual(len(result["brands"]), 2)

    @patch("requests.post")
    def test_create_brand_flow(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"brand_slug": "acme_corp", "brand_name": "Acme Corp"}
        mock_post.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        result = client.create_brand(brand_name="Acme Corp", website="acme.com", industry="SaaS")
        self.assertEqual(result["brand_slug"], "acme_corp")

    @patch("requests.post")
    def test_ensure_brand_flow(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"brand_slug": "acme_corp", "created": False}
        mock_post.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        result = client.ensure_brand(brand_name="Acme Corp")
        self.assertEqual(result["brand_slug"], "acme_corp")
        self.assertFalse(result["created"])


class TestEndToEndTestAuth(unittest.TestCase):
    """Test test_auth flow."""

    @patch("requests.get")
    def test_auth_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"authenticated": True, "org_id": "org_abc"}
        mock_get.return_value = mock_resp

        client = Surmado(api_key="sur_test_key")
        result = client.test_auth()
        self.assertTrue(result["authenticated"])

    @patch("requests.get")
    def test_auth_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"detail": "Unauthorized"}
        mock_resp.text = '{"detail": "Unauthorized"}'
        mock_get.return_value = mock_resp

        client = Surmado(api_key="sur_test_bad")
        with self.assertRaises(AuthenticationError):
            client.test_auth()


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases(unittest.TestCase):
    """Miscellaneous edge cases."""

    @patch("requests.post")
    def test_network_error_propagates(self, mock_post):
        mock_post.side_effect = requests_lib.ConnectionError("Connection refused")
        client = Surmado(api_key="sur_test_x")
        with self.assertRaises(requests_lib.ConnectionError):
            client.signal(
                url="example.com",
                brand_name="Test",
                email="t@t.com",
                industry="Tech",
                location="US",
                persona="Devs",
                pain_points="Bugs",
                brand_details="Tools",
                direct_competitors="Others",
            )

    @patch("requests.post")
    def test_timeout_error_propagates(self, mock_post):
        mock_post.side_effect = requests_lib.Timeout("Request timed out")
        client = Surmado(api_key="sur_test_x")
        with self.assertRaises(requests_lib.Timeout):
            client.scan(url="example.com", brand_name="Test", email="t@t.com")

    @patch.object(Surmado, "_post")
    def test_signal_preserves_http_url(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        client = Surmado(api_key="sur_test_x")
        client.signal(
            url="http://internal.example.com",
            brand_name="Test",
            email="t@t.com",
            industry="Tech",
            location="US",
            persona="Devs",
            pain_points="Bugs",
            brand_details="Tools",
            direct_competitors="Others",
        )
        payload = mock_post.call_args[0][1]
        self.assertEqual(payload["url"], "http://internal.example.com")

    @patch.object(Surmado, "_post")
    def test_create_brand_empty_website_string(self, mock_post):
        """Empty string website should not be included (falsy)."""
        mock_post.return_value = {"brand_slug": "test"}
        client = Surmado(api_key="sur_test_x")
        client.create_brand(brand_name="Test", website="")
        payload = mock_post.call_args[0][1]
        # Empty string is falsy, so website should not be added
        self.assertNotIn("website", payload)

    @patch.object(Surmado, "_post")
    def test_create_brand_empty_industry_string(self, mock_post):
        """Empty string industry should not be included (falsy)."""
        mock_post.return_value = {"brand_slug": "test"}
        client = Surmado(api_key="sur_test_x")
        client.create_brand(brand_name="Test", industry="")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("industry", payload)

    def test_multiple_clients_independent(self):
        """Two clients should be independent."""
        client1 = Surmado(api_key="sur_test_key1")
        client2 = Surmado(api_key="sur_test_key2", base_url="http://localhost:8000", timeout=5)
        self.assertEqual(client1.api_key, "sur_test_key1")
        self.assertEqual(client2.api_key, "sur_test_key2")
        self.assertEqual(client1.base_url, "https://api.surmado.com/v1")
        self.assertEqual(client2.base_url, "http://localhost:8000")
        self.assertEqual(client1.timeout, 30)
        self.assertEqual(client2.timeout, 5)


# =============================================================================
# No Tier in Any Method
# =============================================================================


class TestNoTierInAnyPayload(unittest.TestCase):
    """Comprehensive check that no method ever sends a tier field."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_x")

    @patch.object(Surmado, "_post")
    def test_signal_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal(
            url="example.com", brand_name="T", email="e@e.com",
            industry="I", location="L", persona="P",
            pain_points="PP", brand_details="BD", direct_competitors="DC",
        )
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_scan_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan(url="example.com", brand_name="T", email="e@e.com")
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_solutions_token_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(email="e@e.com", signal_token="tok_x")
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_solutions_standalone_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.solutions(
            email="e@e.com", brand_name="T", business_story="BS",
            decision="D", success="S", timeline="TL", scale_indicator="SI",
        )
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_signal_rerun_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.signal_rerun(brand_slug="b", persona_slug="p", email="e@e.com")
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_scan_rerun_no_tier(self, mock_post):
        mock_post.return_value = {"report_id": "rpt_123"}
        self.client.scan_rerun(brand_slug="b", email="e@e.com")
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_create_brand_no_tier(self, mock_post):
        mock_post.return_value = {"brand_slug": "t"}
        self.client.create_brand(brand_name="T")
        self.assertNotIn("tier", mock_post.call_args[0][1])

    @patch.object(Surmado, "_post")
    def test_ensure_brand_no_tier(self, mock_post):
        mock_post.return_value = {"brand_slug": "t"}
        self.client.ensure_brand(brand_name="T")
        self.assertNotIn("tier", mock_post.call_args[0][1])


# =============================================================================
# Bundle Method
# =============================================================================


class TestBundleMethod(unittest.TestCase):
    """Test bundle() method sends correct payloads and handles responses."""

    def setUp(self):
        self.client = Surmado(api_key="sur_test_bundle")

    @patch.object(Surmado, "_post")
    def test_bundle_required_fields_only(self, mock_post):
        mock_post.return_value = {
            "bundle_id": "bnd_abc123",
            "credits_charged": 3,
            "credits_remaining": 47,
            "is_baseline": False,
            "reports": {
                "scan": {"report_id": "rpt_scan_1", "status": "queued"},
                "signal": {"report_id": "rpt_signal_1", "status": "queued"},
                "solutions": {"report_id": "rpt_sol_1", "status": "waiting_on_signal"},
            },
        }
        result = self.client.bundle(brand_slug="acme_corp", email="test@acme.com")
        mock_post.assert_called_once_with("/reports/bundle", {
            "brand_slug": "acme_corp",
            "email": "test@acme.com",
        })
        self.assertEqual(result["bundle_id"], "bnd_abc123")
        self.assertEqual(result["credits_charged"], 3)
        self.assertIn("scan", result["reports"])
        self.assertIn("signal", result["reports"])
        self.assertIn("solutions", result["reports"])

    @patch.object(Surmado, "_post")
    def test_bundle_with_optional_fields(self, mock_post):
        mock_post.return_value = {"bundle_id": "bnd_xyz"}
        self.client.bundle(
            brand_slug="acme_corp",
            email="test@acme.com",
            persona_slug="cto-enterprise",
            webhook_url="https://hooks.example.com/done",
        )
        mock_post.assert_called_once_with("/reports/bundle", {
            "brand_slug": "acme_corp",
            "email": "test@acme.com",
            "persona_slug": "cto-enterprise",
            "webhook_url": "https://hooks.example.com/done",
        })

    @patch.object(Surmado, "_post")
    def test_bundle_omits_none_optional_fields(self, mock_post):
        mock_post.return_value = {"bundle_id": "bnd_xyz"}
        self.client.bundle(brand_slug="acme", email="t@t.com")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("persona_slug", payload)
        self.assertNotIn("webhook_url", payload)

    @patch.object(Surmado, "_post")
    def test_bundle_no_tier_in_payload(self, mock_post):
        mock_post.return_value = {"bundle_id": "bnd_xyz"}
        self.client.bundle(brand_slug="b", email="e@e.com")
        payload = mock_post.call_args[0][1]
        self.assertNotIn("tier", payload)

    @patch.object(Surmado, "_post")
    def test_bundle_baseline_response(self, mock_post):
        mock_post.return_value = {
            "bundle_id": "bnd_baseline",
            "credits_charged": 0,
            "credits_remaining": 50,
            "is_baseline": True,
            "reports": {
                "scan": {"report_id": "rpt_1", "status": "queued"},
                "signal": {"report_id": "rpt_2", "status": "queued"},
                "solutions": {"report_id": "rpt_3", "status": "waiting_on_signal"},
            },
        }
        result = self.client.bundle(brand_slug="new_brand", email="t@t.com")
        self.assertTrue(result["is_baseline"])
        self.assertEqual(result["credits_charged"], 0)

    @patch("requests.post")
    def test_bundle_insufficient_credits_raises(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 402
        mock_resp.json.return_value = {
            "detail": {"error": {"code": "insufficient_credits", "message": "Need 3 credits"}}
        }
        mock_resp.text = "{}"
        mock_post.return_value = mock_resp

        with self.assertRaises(InsufficientCreditsError):
            self.client.bundle(brand_slug="b", email="e@e.com")

    @patch("requests.post")
    def test_bundle_brand_not_found_raises(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {
            "detail": {"error": {"code": "brand_not_found", "message": "Brand not found"}}
        }
        mock_resp.text = "{}"
        mock_post.return_value = mock_resp

        with self.assertRaises(NotFoundError):
            self.client.bundle(brand_slug="nonexistent", email="e@e.com")

    @patch.object(Surmado, "_post")
    def test_bundle_posts_to_correct_endpoint(self, mock_post):
        mock_post.return_value = {"bundle_id": "bnd_xyz"}
        self.client.bundle(brand_slug="b", email="e@e.com")
        self.assertEqual(mock_post.call_args[0][0], "/reports/bundle")

    @patch.object(Surmado, "_post")
    def test_bundle_response_has_all_three_reports(self, mock_post):
        mock_post.return_value = {
            "bundle_id": "bnd_xyz",
            "credits_charged": 3,
            "credits_remaining": 7,
            "is_baseline": False,
            "reports": {
                "scan": {"report_id": "rpt_s1", "status": "queued"},
                "signal": {"report_id": "rpt_s2", "status": "queued"},
                "solutions": {"report_id": "rpt_s3", "status": "waiting_on_signal"},
            },
        }
        result = self.client.bundle(brand_slug="b", email="e@e.com")
        self.assertEqual(len(result["reports"]), 3)
        for key in ("scan", "signal", "solutions"):
            self.assertIn("report_id", result["reports"][key])
            self.assertIn("status", result["reports"][key])


if __name__ == "__main__":
    unittest.main()
