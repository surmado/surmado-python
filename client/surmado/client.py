"""
Surmado Python Client

Official Python SDK for Surmado - the anti-dashboard marketing intelligence engine.
https://surmado.com
"""
import os
import time
import requests
from typing import Dict, Optional, Any, List

__version__ = "0.3.1"


class SurmadoError(Exception):
    """Base exception for Surmado SDK errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(SurmadoError):
    """Raised when API key is invalid or missing."""
    pass


class InsufficientCreditsError(SurmadoError):
    """Raised when account doesn't have enough credits."""
    pass


class NotFoundError(SurmadoError):
    """Raised when a report or resource is not found."""
    pass


class ValidationError(SurmadoError):
    """Raised when request data is invalid."""
    pass


class RateLimitError(SurmadoError):
    """Raised when rate limit is exceeded (429)."""
    pass


class Surmado:
    """
    Official Surmado API client.

    Args:
        api_key (str): Your Surmado API key  (starts with sur_live_ or sur_test_).
                    If not provided, reads from SURMADO_API_KEY environment variable.
        base_url (str): API base URL. Defaults to https://api.surmado.com/v1.
        timeout (int): Request timeout in seconds. Defaults to 30.

    Example:
        >>> from surmado import Surmado
        >>> client = Surmado()  # reads SURMADO_API_KEY from env
        >>>
        >>> # Full Analysis Bundle (Site Audit + AI Visibility + Strategy)
        >>> result = client.bundle(brand_slug="acme_corp", email="you@acme.com")
        >>> print(result["bundle_id"])
        >>>
        >>> # Or run individual reports
        >>> result = client.signal(
        ...     url="https://example.com",
        ...     brand_name="Example Brand",
        ...     email="you@example.com",
        ...     industry="E-commerce",
        ...     location="United States",
        ...     persona="Small business owners",
        ...     pain_points="Finding reliable vendors",
        ...     brand_details="Affordable solutions",
        ...     direct_competitors="Competitor A, Competitor B"
        ... )
        >>> print(result["report_id"])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("SURMADO_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set SURMADO_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url or "https://api.surmado.com/v1"
        self.timeout = timeout

    # =========================================================================
    # Full Report Methods (all fields provided inline)
    # =========================================================================

    def signal(
        self,
        url: str,
        brand_name: str,
        email: str,
        industry: str,
        location: str,
        persona: str,
        pain_points: str,
        brand_details: str,
        direct_competitors: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run an AI Visibility report.

        Tests how your brand appears across 7 AI platforms:
        ChatGPT, Perplexity, Google Gemini, Claude, Meta AI, Grok, DeepSeek.
        Costs 1 credit.

        Args:
            url: Your website URL to analyze (required)
            brand_name: Your brand name (max 100 chars, required)
            email: Email for notifications (required)
            industry: Your industry/sector (max 200 chars, required)
            location: Primary market location (max 200 chars, required)
            persona: Target customer description (max 800 chars, required)
            pain_points: Problems your product solves as comma-separated string (max 1000 chars, required)
            brand_details: Your brand positioning (max 1200 chars, required)
            direct_competitors: Competitor names as comma-separated string (max 500 chars, required)

        Optional kwargs:
            indirect_competitors: Alternative solutions (max 500 chars)
            keywords: Target keywords as comma-separated string (max 500 chars)
            product: Product/service description (max 1000 chars)
            business_scale: "small", "medium", or "large" (default: "medium")
            webhook_url: URL to receive POST when report completes (HTTPS required)

        Returns:
            Report creation response with report_id, token, and status

        Example:
            >>> result = client.signal(
            ...     url="https://acme.com",
            ...     brand_name="Acme Corp",
            ...     email="you@acme.com",
            ...     industry="B2B SaaS",
            ...     location="United States",
            ...     persona="CTOs at mid-market companies",
            ...     pain_points="Integration challenges, lack of visibility",
            ...     brand_details="Modern, dev-focused tooling",
            ...     direct_competitors="Asana, Monday.com"
            ... )
            >>> print(f"Report ID: {result['report_id']}")
            >>> print(f"Token (save for Solutions): {result['token']}")
        """
        payload = {
            "url": self._normalize_url(url),
            "brand_name": brand_name,
            "email": email,
            "industry": industry,
            "location": location,
            "persona": persona,
            "pain_points": pain_points,
            "brand_details": brand_details,
            "direct_competitors": direct_competitors,
            **kwargs
        }
        return self._post("/reports/signal", payload)

    def scan(
        self,
        url: str,
        brand_name: str,
        email: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a Site Audit report.

        Comprehensive SEO analysis with prioritized recommendations.
        Costs 1 credit.

        Args:
            url: Website URL to audit (required)
            brand_name: Your brand name (max 100 chars, required)
            email: Email for notifications (required)

        Optional kwargs:
            competitor_urls: List of competitor URLs to compare against
            report_style: "executive", "technical", or "comprehensive" (default: "executive")
            webhook_url: URL to receive POST when report completes (HTTPS required)

        Returns:
            Report creation response with report_id and status

        Example:
            >>> result = client.scan(
            ...     url="https://acme.com",
            ...     brand_name="Acme Corp",
            ...     email="you@acme.com",
            ...     competitor_urls=["https://competitor1.com", "https://competitor2.com"]
            ... )
            >>> print(f"Report ID: {result['report_id']}")
        """
        payload = {
            "url": self._normalize_url(url),
            "brand_name": brand_name,
            "email": email,
            **kwargs
        }
        return self._post("/reports/scan", payload)

    def solutions(
        self,
        email: str,
        signal_token: Optional[str] = None,
        scan_token: Optional[str] = None,
        brand_name: Optional[str] = None,
        business_story: Optional[str] = None,
        decision: Optional[str] = None,
        success: Optional[str] = None,
        timeline: Optional[str] = None,
        scale_indicator: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a Strategy report.

        Multi-AI strategic recommendations from 6 specialized agents.
        Costs 1 credit.

        Two modes:
        1. AI Visibility Token Mode (recommended): Pass signal_token from an
           AI Visibility report. Strategy inherits context automatically.
        2. Standalone Mode: Provide all business context fields manually.

        Args:
            email: Email for notifications (required)
            signal_token: Token from an AI Visibility report (Mode 1 - recommended)
            scan_token: Token from a Site Audit report (optional, adds SEO context)
            brand_name: Your brand name (max 100 chars, required for Mode 2)
            business_story: About your business (max 2000 chars, required for Mode 2)
            decision: Key challenge you're facing (max 1500 chars, required for Mode 2)
            success: What success looks like (max 1000 chars, required for Mode 2)
            timeline: Decision timeline (max 200 chars, required for Mode 2)
            scale_indicator: Business scale indicator (max 100 chars, required for Mode 2)

        Optional kwargs (for financial analysis):
            include_financial: True to include financial analysis
            financial_context: Financial situation description (max 1000 chars)
            monthly_revenue: Monthly revenue (max 50 chars)
            monthly_costs: Monthly costs (max 50 chars)
            cash_available: Available cash (max 50 chars)
            webhook_url: URL to receive POST when report completes (HTTPS required)

        Returns:
            Report creation response with report_id and status

        Example (Mode 1 - with AI Visibility token):
            >>> # First run AI Visibility
            >>> signal = client.signal(...)
            >>> # Then run Strategy with the token
            >>> result = client.solutions(
            ...     email="you@acme.com",
            ...     signal_token=signal["token"]
            ... )

        Example (Mode 2 - standalone):
            >>> result = client.solutions(
            ...     email="you@acme.com",
            ...     brand_name="Acme Corp",
            ...     business_story="We're a B2B SaaS company in the project management space...",
            ...     decision="Should we expand to enterprise market?",
            ...     success="$10M ARR in 18 months",
            ...     timeline="Q2 2025",
            ...     scale_indicator="$2M ARR, 20 employees"
            ... )
        """
        payload = {"email": email, **kwargs}

        if signal_token:
            payload["signal_token"] = signal_token
            if scan_token:
                payload["scan_token"] = scan_token
            if brand_name:
                payload["brand_name"] = brand_name
        else:
            # Standalone mode - all fields required
            if not all([brand_name, business_story, decision, success, timeline, scale_indicator]):
                raise ValidationError(
                    "Without signal_token, these fields are required: "
                    "brand_name, business_story, decision, success, timeline, scale_indicator"
                )
            payload.update({
                "brand_name": brand_name,
                "business_story": business_story,
                "decision": decision,
                "success": success,
                "timeline": timeline,
                "scale_indicator": scale_indicator,
            })
            if scan_token:
                payload["scan_token"] = scan_token

        return self._post("/reports/solutions", payload)

    # =========================================================================
    # Bundle (Full Analysis - all 3 reports in one call)
    # =========================================================================

    def bundle(
        self,
        brand_slug: str,
        email: str,
        persona_slug: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run a Full Analysis Bundle (Site Audit + AI Visibility + Strategy).

        Creates all 3 reports in a single call. Site Audit is always included
        automatically — the bundle is all-or-nothing.

        The bundle loads all form data from your stored brand profile,
        so you only need to provide the brand slug and email.

        Flow:
            1. Atomic credit deduction (3 credits upfront)
            2. Site Audit + AI Visibility queued in parallel
            3. Strategy auto-triggered when AI Visibility completes

        Prerequisites:
            - Brand must exist with a complete profile (brand_context with
              website, industry, personas, competitors, etc.)
            - Set up via dashboard wizard or PUT /v1/profiles/{brand_slug}/brand-context

        Args:
            brand_slug: Brand identifier with a complete profile (required)
            email: Contact email for report delivery (required)
            persona_slug: Which persona for AI Visibility (defaults to first persona in profile)
            webhook_url: URL to receive POST when each report completes (HTTPS required)

        Returns:
            Bundle response with:
            - bundle_id: Unique bundle identifier
            - credits_charged: Total credits charged (0 for baseline, 3 for paid)
            - credits_remaining: Credits remaining after charge
            - is_baseline: True if all reports are baseline (free)
            - reports: Dict with scan, signal, solutions — each has report_id and status

        Example:
            >>> result = client.bundle(
            ...     brand_slug="acme_corp",
            ...     email="you@acme.com"
            ... )
            >>> print(f"Bundle ID: {result['bundle_id']}")
            >>> print(f"Credits charged: {result['credits_charged']}")
            >>> for product, info in result["reports"].items():
            ...     print(f"  {product}: {info['report_id']} ({info['status']})")

        Raises:
            NotFoundError: If brand_slug not found or profile incomplete
            InsufficientCreditsError: If account has fewer than 3 credits
        """
        payload = {
            "brand_slug": brand_slug,
            "email": email,
        }
        if persona_slug:
            payload["persona_slug"] = persona_slug
        if webhook_url:
            payload["webhook_url"] = webhook_url
        return self._post("/reports/bundle", payload)

    # =========================================================================
    # Rerun Methods (minimal inputs - uses stored brand context)
    # =========================================================================

    def signal_rerun(
        self,
        brand_slug: str,
        persona_slug: str,
        email: str,
    ) -> Dict[str, Any]:
        """
        Re-run an AI Visibility report with minimal inputs.

        Uses stored brand context - no need to re-enter all fields.
        Ideal for automation (Zapier, Make, n8n) and dashboard "Run Again" flows.
        Costs 1 credit.

        Prerequisites:
            - Brand must exist with populated brand_context
            - Persona must be configured in brand_context.personas

        Args:
            brand_slug: Brand identifier (e.g., "acme_corp")
            persona_slug: Persona identifier from brand settings (e.g., "cto-enterprise")
            email: Email for notifications

        Returns:
            Report creation response with report_id and status

        Example:
            >>> # After setting up brand and personas in dashboard
            >>> result = client.signal_rerun(
            ...     brand_slug="acme_corp",
            ...     persona_slug="cto-enterprise",
            ...     email="you@acme.com"
            ... )
            >>> print(f"Report ID: {result['report_id']}")

        Raises:
            NotFoundError: If brand_slug or persona_slug not found
            ValidationError: If brand_context is incomplete
        """
        payload = {
            "brand_slug": brand_slug,
            "persona_slug": persona_slug,
            "email": email,
        }
        return self._post("/reports/signal/rerun", payload)

    def scan_rerun(
        self,
        brand_slug: str,
        email: str,
    ) -> Dict[str, Any]:
        """
        Re-run a Site Audit report with minimal inputs.

        Uses stored brand context (website URL, competitor URLs).
        Ideal for automation and scheduled SEO monitoring.
        Costs 1 credit.

        Prerequisites:
            - Brand must exist with populated brand_context.website

        Args:
            brand_slug: Brand identifier (e.g., "acme_corp")
            email: Email for notifications

        Returns:
            Report creation response with report_id and status

        Example:
            >>> # After setting up brand in dashboard
            >>> result = client.scan_rerun(
            ...     brand_slug="acme_corp",
            ...     email="you@acme.com"
            ... )
            >>> print(f"Report ID: {result['report_id']}")

        Raises:
            NotFoundError: If brand_slug not found
            ValidationError: If brand_context.website is missing
        """
        payload = {
            "brand_slug": brand_slug,
            "email": email,
        }
        return self._post("/reports/scan/rerun", payload)

    # =========================================================================
    # Report Status & Listing
    # =========================================================================

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """
        Get report status and results.

        Poll this endpoint to check if your report is ready.
        When status is "completed", download URLs will be included.

        Args:
            report_id: The report ID returned from signal(), scan(), or solutions()

        Returns:
            Report status with download URLs when completed:
            - status: "queued", "processing", "completed", or "failed"
            - download_url: Signed PDF URL (expires in 15 minutes)
            - pptx_download_url: Signed PPTX URL (expires in 15 minutes)

        Example:
            >>> report = client.get_report("rpt_abc123")
            >>> if report["status"] == "completed":
            ...     print(f"PDF: {report['download_url']}")
        """
        return self._get(f"/reports/{report_id}")

    def get_report_data(
        self,
        report_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get raw report data with optional field filtering.

        Returns the full report data (metrics, analysis, etc.) as JSON.
        Use the fields parameter to request only specific fields.

        Args:
            report_id: The report ID
            fields: Optional list of field names to return (e.g., ["status", "insights"])

        Returns:
            Raw report data dict (full or filtered)

        Example:
            >>> data = client.get_report_data("rpt_abc123")
            >>> print(data["status"])

            >>> # Get only specific fields
            >>> data = client.get_report_data("rpt_abc123", fields=["status", "insights"])
        """
        endpoint = f"/reports/{report_id}/data"
        if fields:
            endpoint += f"?fields={','.join(fields)}"
        return self._get(endpoint)

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        List all reports for your organization.

        Args:
            page: Page number (1-indexed)
            page_size: Reports per page (max 100)

        Returns:
            Paginated list of reports with download URLs for completed reports

        Example:
            >>> result = client.list_reports(page=1, page_size=10)
            >>> for report in result["reports"]:
            ...     print(f"{report['report_id']}: {report['status']}")
        """
        return self._get(f"/reports?page={page}&page_size={page_size}")

    def wait_for_report(
        self,
        report_id: str,
        timeout_minutes: int = 20,
        poll_interval: int = 30
    ) -> Dict[str, Any]:
        """
        Wait for a report to complete.

        Polls the report status until it's completed, failed, or timeout.

        Args:
            report_id: The report ID to wait for
            timeout_minutes: Maximum time to wait (default 20 minutes)
            poll_interval: Seconds between status checks (default 30)

        Returns:
            Completed report with download URLs

        Raises:
            SurmadoError: If report fails or times out

        Example:
            >>> result = client.signal(...)
            >>> completed = client.wait_for_report(result["report_id"])
            >>> print(f"PDF ready: {completed['download_url']}")
        """
        start = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start < timeout_seconds:
            report = self.get_report(report_id)
            status = report.get("status")

            if status == "completed":
                return report
            elif status == "failed":
                error_msg = report.get("error") or "Report processing failed"
                raise SurmadoError(error_msg, response=report)
            elif status == "cancelled":
                raise SurmadoError("Report was cancelled", response=report)

            time.sleep(poll_interval)

        raise SurmadoError(
            f"Report did not complete within {timeout_minutes} minutes",
            response={"report_id": report_id, "status": "timeout"}
        )

    # =========================================================================
    # Brand Management
    # =========================================================================

    def list_brands(self) -> Dict[str, Any]:
        """
        List all brands for your organization.

        Returns:
            List of brand objects with slugs, names, and metadata

        Example:
            >>> brands = client.list_brands()
            >>> for brand in brands.get("brands", []):
            ...     print(f"{brand['brand_slug']}: {brand['brand_name']}")
        """
        return self._get("/brands")

    def create_brand(
        self,
        brand_name: str,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new brand profile.

        Args:
            brand_name: Brand name (max 100 chars, required)
            website: Brand website URL
            industry: Industry/sector (max 200 chars)

        Returns:
            Created brand object with brand_slug

        Raises:
            ValidationError: If brand already exists (use ensure_brand instead)

        Example:
            >>> brand = client.create_brand(
            ...     brand_name="Acme Corp",
            ...     website="https://acme.com",
            ...     industry="B2B SaaS"
            ... )
            >>> print(f"Created: {brand['brand_slug']}")
        """
        payload = {"brand_name": brand_name, **kwargs}
        if website:
            payload["website"] = self._normalize_url(website)
        if industry:
            payload["industry"] = industry
        return self._post("/brands", payload)

    def ensure_brand(
        self,
        brand_name: str,
        website: Optional[str] = None,
        industry: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a brand if it doesn't exist, or return existing one.

        Unlike create_brand, this never fails with a 409 conflict.

        Args:
            brand_name: Brand name (max 100 chars, required)
            website: Brand website URL
            industry: Industry/sector (max 200 chars)

        Returns:
            Brand object with brand_slug (created or existing)

        Example:
            >>> brand = client.ensure_brand(
            ...     brand_name="Acme Corp",
            ...     website="https://acme.com"
            ... )
            >>> print(f"Slug: {brand['brand_slug']}")
        """
        payload = {"brand_name": brand_name, **kwargs}
        if website:
            payload["website"] = self._normalize_url(website)
        if industry:
            payload["industry"] = industry
        return self._post("/brands/ensure", payload)

    # =========================================================================
    # Utility
    # =========================================================================

    def test_auth(self) -> Dict[str, Any]:
        """
        Test your API key without consuming credits.

        Returns:
            Auth status with org info

        Example:
            >>> result = client.test_auth()
            >>> print(f"Authenticated as: {result.get('org_id')}")
        """
        return self._get("/test-auth")

    # =========================================================================
    # Internal HTTP Methods
    # =========================================================================

    def _normalize_url(self, url: str) -> str:
        """Add https:// if no protocol specified."""
        if url and not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url

    def _headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": f"surmado-python/{__version__}",
        }

    def _post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """Make a POST request."""
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self._headers(),
            timeout=self.timeout
        )
        return self._handle_response(response)

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request."""
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self._headers(),
            timeout=self.timeout
        )
        return self._handle_response(response)

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        response = requests.delete(
            f"{self.base_url}{endpoint}",
            headers=self._headers(),
            timeout=self.timeout
        )
        return self._handle_response(response)

    def _extract_error_message(self, data: dict, fallback: str) -> str:
        """Extract error message from API response.

        Handles the canonical format: {"detail": {"error": {"code": "...", "message": "..."}}}
        Plus legacy/fallback formats.
        """
        detail = data.get("detail")
        if isinstance(detail, dict):
            error_obj = detail.get("error", {})
            if isinstance(error_obj, dict) and "message" in error_obj:
                return error_obj["message"]
            if "message" in detail:
                return detail["message"]
        if isinstance(detail, str):
            return detail
        return data.get("message") or data.get("error") or fallback

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate errors."""
        try:
            data = response.json()
        except ValueError:
            data = {"error": response.text}

        if response.status_code == 401:
            raise AuthenticationError(
                self._extract_error_message(data, "Invalid or missing API key"),
                status_code=401,
                response=data
            )

        if response.status_code == 402:
            raise InsufficientCreditsError(
                self._extract_error_message(data, "Insufficient credits"),
                status_code=402,
                response=data
            )

        if response.status_code == 404:
            raise NotFoundError(
                self._extract_error_message(data, "Resource not found"),
                status_code=404,
                response=data
            )

        if response.status_code == 429:
            raise RateLimitError(
                self._extract_error_message(data, "Rate limit exceeded"),
                status_code=429,
                response=data
            )

        if response.status_code in (400, 422):
            raise ValidationError(
                self._extract_error_message(data, "Invalid request data"),
                status_code=response.status_code,
                response=data
            )

        if response.status_code >= 400:
            raise SurmadoError(
                self._extract_error_message(data, f"API error: {response.status_code}"),
                status_code=response.status_code,
                response=data
            )

        return data
