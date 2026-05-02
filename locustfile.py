from __future__ import annotations

import os
import secrets
import uuid

from locust import HttpUser, between, constant_pacing, task
from locust.exception import StopUser


TRUTHY = {"1", "true", "yes", "y", "on"}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in TRUTHY


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def parse_statuses(value: str, default: set[int]) -> set[int]:
    if not value:
        return default

    statuses = set()
    for raw_status in value.split(","):
        raw_status = raw_status.strip()
        if not raw_status:
            continue
        try:
            statuses.add(int(raw_status))
        except ValueError:
            continue

    return statuses or default


STRICT_SECURITY_EXPECTATIONS = env_bool("STRICT_SECURITY_EXPECTATIONS", True)
WRITE_TESTS = env_bool("LOCUST_WRITE_TESTS", False)
BRUTE_FORCE_ATTEMPTS = env_int("BRUTE_FORCE_ATTEMPTS", 12)
RATE_LIMIT_BURST = env_int("RATE_LIMIT_BURST", 30)
MAX_RESPONSE_MS = env_int("MAX_RESPONSE_MS", 1500)
BLOCK_STATUSES = parse_statuses(os.getenv("RATE_LIMIT_STATUSES", ""), {429})

SECURITY_PROBE_EMAIL = os.getenv("SECURITY_PROBE_EMAIL", "zaproxy@example.com")
AUTH_EMAIL = os.getenv("LOCUST_EMAIL")
AUTH_SECRET = os.getenv("LOCUST_PASSWORD")
BAD_LOGIN_SECRET = os.getenv(
    "LOCUST_BAD_LOGIN_SECRET",
    "bad-login-" + secrets.token_urlsafe(12),
)


class SecurityAssertionsMixin:
    """Shared response checks for performance and security controls."""

    host = os.getenv("LOCUST_HOST", "http://127.0.0.1:8000")

    def security_header_issues(self, response) -> list[str]:
        issues = []
        headers = response.headers
        csp = headers.get("Content-Security-Policy", "")
        server = headers.get("Server", "")

        if not csp:
            issues.append("missing Content-Security-Policy header")
        else:
            if "unsafe-inline" in csp:
                issues.append("CSP still allows unsafe-inline")
            if "form-action" not in csp:
                issues.append("CSP is missing form-action")
            if "script-src" not in csp:
                issues.append("CSP is missing script-src")
            if "style-src" not in csp:
                issues.append("CSP is missing style-src")

        if headers.get("X-Content-Type-Options", "").lower() != "nosniff":
            issues.append("missing or weak X-Content-Type-Options")

        if headers.get("X-Frame-Options", "").upper() != "DENY":
            issues.append("missing or weak X-Frame-Options")

        if not headers.get("Referrer-Policy"):
            issues.append("missing Referrer-Policy")

        if "WSGIServer" in server or "CPython" in server:
            issues.append("Server header leaks implementation/version details")

        return issues

    def performance_issues(self, response) -> list[str]:
        elapsed = getattr(response, "elapsed", None)
        if not elapsed:
            return []

        elapsed_ms = elapsed.total_seconds() * 1000
        if elapsed_ms > MAX_RESPONSE_MS:
            return [f"response took {elapsed_ms:.0f}ms, limit is {MAX_RESPONSE_MS}ms"]
        return []

    def validate_response(
        self,
        response,
        expected_statuses: set[int],
        *,
        check_headers: bool = True,
        extra_issues: list[str] | None = None,
    ) -> None:
        issues = []

        if response.status_code not in expected_statuses:
            issues.append(
                f"unexpected status {response.status_code}, expected "
                f"{sorted(expected_statuses)}"
            )

        issues.extend(self.performance_issues(response))

        if check_headers:
            issues.extend(self.security_header_issues(response))

        if extra_issues:
            issues.extend(extra_issues)

        if issues:
            response.failure("; ".join(issues))
        else:
            response.success()

    def get_json_value(self, response, key: str) -> str | None:
        try:
            data = response.json()
        except ValueError:
            return None

        value = data.get(key)
        if isinstance(value, str):
            return value
        return None


class PublicApiUser(SecurityAssertionsMixin, HttpUser):
    """Concurrent read-heavy traffic against public API surfaces."""

    weight = 5
    wait_time = between(0.2, 1.5)

    @task(8)
    def browse_catalog(self) -> None:
        for url in (
            "/shop/categories/",
            "/shop/item-types/",
            "/shop/sizes/",
            "/shop/ratings/",
            "/shop/colors/",
            "/shop/items/",
            "/shop/hero-sections/",
        ):
            with self.client.get(
                url,
                name="public catalog read",
                catch_response=True,
            ) as response:
                self.validate_response(response, {200, 301, 302, 403, 429})

    @task(2)
    def anonymous_protected_resource_probe(self) -> None:
        for url in ("/shop/cart/", "/shop/orders/", "/accounts/user/profile/"):
            with self.client.get(
                url,
                name="anonymous protected resource",
                catch_response=True,
            ) as response:
                self.validate_response(response, {401, 403, 429})

    @task(1)
    def write_contact_message_when_enabled(self) -> None:
        if not WRITE_TESTS:
            return

        probe_id = uuid.uuid4().hex
        payload = {
            "email": f"locust-{probe_id}@example.com",
            "subject": "Locust security contact probe",
            "details": "Generated by locustfile.py during an approved test run.",
        }

        with self.client.post(
            "/shop/contact/",
            json=payload,
            name="optional contact write",
            catch_response=True,
        ) as response:
            self.validate_response(response, {201, 400, 403, 429})


class AuthenticatedApiUser(SecurityAssertionsMixin, HttpUser):
    """Authenticated API degradation checks using JWT cookie auth."""

    weight = 3 if AUTH_EMAIL and AUTH_SECRET else 0
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        if not AUTH_EMAIL or not AUTH_SECRET:
            raise StopUser(
                "Set LOCUST_EMAIL and LOCUST_PASSWORD to enable authenticated tests."
            )

        with self.client.post(
            "/accounts/user/login/",
            json={"email": AUTH_EMAIL, "password": AUTH_SECRET},
            name="valid login",
            catch_response=True,
        ) as response:
            access_token = self.get_json_value(response, "access_token")
            if response.status_code != 200 or not access_token:
                response.failure("valid login failed or no access_token returned")
                raise StopUser("Valid login failed.")

            self.client.cookies.set("access_token", access_token)
            self.validate_response(response, {200})

    @task(5)
    def authenticated_read_flow(self) -> None:
        for url in (
            "/accounts/user/profile/",
            "/shop/cart/",
            "/shop/orders/",
        ):
            with self.client.get(
                url,
                name="authenticated read",
                catch_response=True,
            ) as response:
                self.validate_response(response, {200, 401, 403, 429})

    @task(2)
    def token_cookie_verification(self) -> None:
        with self.client.post(
            "/accounts/token/verify-access/",
            name="token cookie verification",
            catch_response=True,
        ) as response:
            self.validate_response(response, {200, 401, 403, 429})


class BruteForceAndRateLimitUser(SecurityAssertionsMixin, HttpUser):
    """Focused probes for brute-force handling and rate-limit enforcement."""

    weight = 1
    wait_time = between(5.0, 10.0)

    @task(4)
    def brute_force_login_probe(self) -> None:
        blocked = False

        for attempt in range(BRUTE_FORCE_ATTEMPTS):
            payload = {
                "email": SECURITY_PROBE_EMAIL,
                "password": BAD_LOGIN_SECRET + str(attempt),
            }
            is_last_attempt = attempt == BRUTE_FORCE_ATTEMPTS - 1

            with self.client.post(
                "/accounts/user/login/",
                json=payload,
                name="brute force login probe",
                catch_response=True,
            ) as response:
                extra_issues = []

                if response.status_code == 200:
                    extra_issues.append("invalid credentials were accepted")

                if response.status_code in BLOCK_STATUSES:
                    blocked = True

                if (
                    STRICT_SECURITY_EXPECTATIONS
                    and is_last_attempt
                    and not blocked
                ):
                    extra_issues.append(
                        "no brute-force block or rate-limit status after "
                        f"{BRUTE_FORCE_ATTEMPTS} invalid login attempts"
                    )

                self.validate_response(
                    response,
                    {400, 401, 403, 429},
                    extra_issues=extra_issues,
                )

    @task(2)
    def login_rate_limit_burst_probe(self) -> None:
        blocked = False

        for request_number in range(RATE_LIMIT_BURST):
            payload = {
                "email": SECURITY_PROBE_EMAIL,
                "password": BAD_LOGIN_SECRET + "-burst-" + str(request_number),
            }
            is_last_request = request_number == RATE_LIMIT_BURST - 1

            with self.client.post(
                "/accounts/user/login/",
                json=payload,
                name="login rate-limit burst",
                catch_response=True,
            ) as response:
                extra_issues = []

                if response.status_code in BLOCK_STATUSES:
                    blocked = True

                if (
                    STRICT_SECURITY_EXPECTATIONS
                    and is_last_request
                    and not blocked
                ):
                    extra_issues.append(
                        "no rate-limit status after "
                        f"{RATE_LIMIT_BURST} rapid login requests"
                    )

                self.validate_response(
                    response,
                    {400, 401, 403, 429},
                    extra_issues=extra_issues,
                )

    @task(1)
    def public_api_rate_limit_burst_probe(self) -> None:
        blocked = False

        for request_number in range(RATE_LIMIT_BURST):
            is_last_request = request_number == RATE_LIMIT_BURST - 1

            with self.client.get(
                "/shop/items/",
                name="public API rate-limit burst",
                catch_response=True,
            ) as response:
                extra_issues = []

                if response.status_code in BLOCK_STATUSES:
                    blocked = True

                if (
                    STRICT_SECURITY_EXPECTATIONS
                    and is_last_request
                    and not blocked
                ):
                    extra_issues.append(
                        "no rate-limit status after "
                        f"{RATE_LIMIT_BURST} rapid public API requests"
                    )

                self.validate_response(
                    response,
                    {200, 403, 429},
                    extra_issues=extra_issues,
                )

    @task(1)
    def password_reset_enumeration_probe(self) -> None:
        missing_email = f"missing-{uuid.uuid4().hex}@example.com"

        with self.client.post(
            "/accounts/password-reset/request/",
            json={"email": missing_email},
            name="password reset enumeration probe",
            catch_response=True,
        ) as response:
            extra_issues = []
            body = response.text.lower()

            if STRICT_SECURITY_EXPECTATIONS and "does not exist" in body:
                extra_issues.append(
                    "password reset response reveals whether an email exists"
                )

            self.validate_response(
                response,
                {200, 400, 403, 429},
                extra_issues=extra_issues,
            )


class SecurityHeaderAndMethodUser(SecurityAssertionsMixin, HttpUser):
    """Header checks, method-tampering probes, and 404 behavior."""

    weight = 1
    wait_time = constant_pacing(2.0)

    @task(3)
    def important_security_headers(self) -> None:
        for method, url in (
            ("GET", "/shop/items/"),
            ("GET", "/admin/"),
            ("POST", "/accounts/logout/"),
            ("DELETE", "/shop/cart/remove/id/"),
        ):
            with self.client.request(
                method,
                url,
                name="security headers on important paths",
                catch_response=True,
            ) as response:
                self.validate_response(
                    response,
                    {200, 301, 302, 400, 401, 403, 404, 405, 429},
                )

    @task(2)
    def method_tampering_probe(self) -> None:
        for method, url in (
            ("DELETE", "/accounts/user/login/"),
            ("PUT", "/accounts/user/register/"),
            ("PATCH", "/shop/items/"),
        ):
            with self.client.request(
                method,
                url,
                name="method tampering probe",
                catch_response=True,
            ) as response:
                self.validate_response(response, {400, 401, 403, 404, 405, 429})
