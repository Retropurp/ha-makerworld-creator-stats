"""Failure classification must neither guess a ban nor leak response details."""

import unittest
import importlib
import sys
import types
from test_rewards import COMPONENT

package = types.ModuleType("error_test_package")
package.__path__ = [str(COMPONENT)]
sys.modules[package.__name__] = package
errors = importlib.import_module("error_test_package.errors")


class ErrorTests(unittest.TestCase):
    def classify(self, status=403, body=b"", headers=None):
        return errors.classify_denial(status, headers or {}, body, "Kontoprofil")

    def test_explicit_challenge_header(self):
        self.assertIsInstance(self.classify(headers={"CF-Mitigated": "challenge"}), errors.CloudflareError)

    def test_cloudflare_block_html(self):
        self.assertIsInstance(self.classify(body=b"<!DOCTYPE html><title>Attention Required! | Cloudflare</title>"), errors.CloudflareError)

    def test_cloudflare_challenge_path(self):
        self.assertIsInstance(self.classify(body=b'<html><script src="/cdn-cgi/challenge-platform/x"></script>'), errors.CloudflareError)

    def test_cloudflare_server_is_not_a_block_diagnosis(self):
        result = self.classify(headers={"Server": "cloudflare", "CF-Ray": "abcdef"}, body=b'{"error":"forbidden"}')
        self.assertNotIsInstance(result, errors.CloudflareError)
        self.assertIn("The cause is unknown", str(result))

    def test_cloudflare_word_in_json_does_not_prove_a_block(self):
        self.assertNotIsInstance(self.classify(body=b'{"message":"cloudflare"}'), errors.CloudflareError)

    def test_csrf_is_separate_from_cloudflare(self):
        result = self.classify(body=b'{"error":"CSRF error: missing_cookie","reason":"missing_cookie"}')
        self.assertNotIsInstance(result, errors.CloudflareError)
        self.assertIn("CSRF", str(result))

    def test_throttling_remains_distinct(self):
        self.assertIsInstance(self.classify(status=429, body=b"<html>cloudflare"), errors.RateLimitError)

    def test_retry_after_attached_to_denials(self):
        result = self.classify(status=429, headers={"Retry-After": "10000"})
        self.assertEqual(result.retry_after, 10000)
        result = self.classify(headers={"CF-Mitigated": "challenge", "Retry-After": "9000"})
        self.assertEqual(result.retry_after, 9000)

    def test_response_secrets_never_in_error(self):
        result = self.classify(body=b'{"token":"secret-token","email":"private@example.test"}')
        self.assertNotIn("secret-token", str(result))
        self.assertNotIn("private@", str(result))
        self.assertNotIn("private@", repr(result))

    def test_only_prefix_is_inspected(self):
        self.assertNotIsInstance(self.classify(body=b" " * 8192 + b"<html>cloudflare"), errors.CloudflareError)

    def test_invalid_encoding_and_json_are_safe(self):
        self.assertIsInstance(self.classify(body=b"\xff{"), errors.ApiError)
        self.assertIsInstance(self.classify(body=b"[" * 2000), errors.ApiError)


if __name__ == "__main__":
    unittest.main()
