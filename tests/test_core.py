"""Tests for keepomize core functionality."""

import base64
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from keepomize.core import KEEPER_URI_PATTERN, process_secret, resolve_keeper_uri


class TestKeeperUriPattern:
    """Test the Keeper URI pattern matching."""

    def test_valid_keeper_uri(self):
        """Test that valid Keeper URIs match the pattern."""
        valid_uris = [
            "keeper://ABC123/field/password",
            "keeper://MySQL Database/field/password",
            "keeper://API Keys/field/api_key",
            "keeper://Contact/field/name[first]",
            "keeper://Record/custom_field/phone[1][number]",
            "keeper://My Record With Spaces/field/login",
            "keeper://Record/file/certificate.pem",
            "keeper://Complex Record/field/data[0]",
        ]

        for uri in valid_uris:
            assert KEEPER_URI_PATTERN.match(uri) is not None

    def test_invalid_keeper_uri(self):
        """Test that invalid URIs don't match the pattern."""
        invalid_uris = [
            "keeper://",  # Empty path
            "notkeeper://ABC123/field/password",  # Wrong protocol
            "keeper:/ABC123/field/password",  # Missing second slash
            "regular-string-value",  # Not a URI at all
            "http://example.com",  # Different protocol
        ]

        for uri in invalid_uris:
            assert KEEPER_URI_PATTERN.match(uri) is None


class TestResolveKeeperUri:
    """Test the resolve_keeper_uri function."""

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_success(self, mock_run, mock_which):
        """Test successful resolution of a Keeper URI."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value"
        mock_run.return_value = mock_result

        result = resolve_keeper_uri("keeper://MySQL Database/field/password")

        assert result == "resolved-secret-value"
        mock_which.assert_called_once_with("ksm")
        mock_run.assert_called_once()

    @patch("keepomize.core.shutil.which")
    def test_resolve_keeper_uri_ksm_not_found(self, mock_which):
        """Test error when ksm is not found in PATH."""
        mock_which.return_value = None

        with pytest.raises(FileNotFoundError, match="ksm command not found in PATH"):
            resolve_keeper_uri("keeper://MySQL Database/field/password")

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_subprocess_error(self, mock_run, mock_which):
        """Test error when ksm subprocess fails."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_run.side_effect = subprocess.CalledProcessError(1, "ksm")

        with pytest.raises(subprocess.CalledProcessError):
            resolve_keeper_uri("keeper://MySQL Database/field/password")

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    @patch.dict(
        os.environ,
        {
            "KSM_CONFIG": "/path/to/config",
            "KSM_TOKEN": "secret123",
            "OTHER_VAR": "should_be_inherited",
        },
    )
    def test_resolve_keeper_uri_inherits_full_environment(self, mock_run, mock_which):
        """Test that full environment is inherited by ksm subprocess."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value"
        mock_run.return_value = mock_result

        resolve_keeper_uri("keeper://MySQL Database/field/password")

        # Verify that subprocess.run was called without custom env parameter
        call_args = mock_run.call_args
        assert "env" not in call_args.kwargs  # No custom env should be passed

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_strips_trailing_newline(self, mock_run, mock_which):
        """Test that trailing newlines are stripped from ksm output."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value\n"
        mock_run.return_value = mock_result

        result = resolve_keeper_uri("keeper://MySQL Database/field/password")

        assert result == "resolved-secret-value"

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_strips_all_trailing_newlines(
        self, mock_run, mock_which
    ):
        """Test that all trailing newlines are stripped."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value\n\n\n"
        mock_run.return_value = mock_result

        result = resolve_keeper_uri("keeper://MySQL Database/field/password")

        assert result == "resolved-secret-value"

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_preserves_internal_newlines(self, mock_run, mock_which):
        """Test that internal newlines are preserved."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "line1\nline2\nline3\n"
        mock_run.return_value = mock_result

        result = resolve_keeper_uri("keeper://MySQL Database/field/multiline")

        assert result == "line1\nline2\nline3"

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_no_trailing_newline(self, mock_run, mock_which):
        """Test handling when ksm output has no trailing newline."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value"
        mock_run.return_value = mock_result

        result = resolve_keeper_uri("keeper://MySQL Database/field/password")

        assert result == "resolved-secret-value"

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_strips_crlf_line_endings(self, mock_run, mock_which):
        """Test that Windows-style CRLF line endings are stripped."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value\r\n"
        mock_run.return_value = mock_result

        result = resolve_keeper_uri("keeper://MySQL Database/field/password")

        assert result == "resolved-secret-value"

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    @patch.dict(os.environ, {"KEEPOMIZE_KSM_TIMEOUT": "15"})
    def test_resolve_keeper_uri_custom_timeout(self, mock_run, mock_which):
        """Test that custom timeout from environment variable is used."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-value\n"
        mock_run.return_value = mock_result

        resolve_keeper_uri("keeper://MySQL Database/field/password")

        mock_run.assert_called_once_with(
            [
                "/usr/local/bin/ksm",
                "secret",
                "notation",
                "keeper://MySQL Database/field/password",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15.0,
        )

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    @patch.dict(os.environ, {"KEEPOMIZE_KSM_TIMEOUT": "invalid"})
    def test_resolve_keeper_uri_invalid_timeout_uses_default(
        self, mock_run, mock_which
    ):
        """Test that invalid timeout value falls back to default."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-value\n"
        mock_run.return_value = mock_result

        resolve_keeper_uri("keeper://MySQL Database/field/password")

        mock_run.assert_called_once_with(
            [
                "/usr/local/bin/ksm",
                "secret",
                "notation",
                "keeper://MySQL Database/field/password",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30.0,
        )

    @patch("keepomize.core.shutil.which")
    @patch("keepomize.core.subprocess.run")
    def test_resolve_keeper_uri_timeout_error(self, mock_run, mock_which, capsys):
        """Test handling of timeout error."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_run.side_effect = subprocess.TimeoutExpired(["ksm"], 30)

        with pytest.raises(subprocess.TimeoutExpired):
            resolve_keeper_uri("keeper://MySQL Database/field/password")

        captured = capsys.readouterr()
        assert "timed out after 30.0 seconds" in captured.err
        assert "KEEPOMIZE_KSM_TIMEOUT" in captured.err


class TestProcessSecret:
    """Test the process_secret function."""

    @patch("keepomize.core.resolve_keeper_uri")
    def test_process_secret_stringdata(self, mock_resolve):
        """Test processing Secret with stringData containing Keeper URIs."""
        mock_resolve.return_value = "resolved-value"

        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "stringData": {
                "password": "keeper://MySQL Database/field/password",
                "regular-key": "regular-value",
            },
        }

        result = process_secret(doc)

        assert result["stringData"]["password"] == "resolved-value"
        assert result["stringData"]["regular-key"] == "regular-value"
        mock_resolve.assert_called_once_with("keeper://MySQL Database/field/password")

    @patch("keepomize.core.resolve_keeper_uri")
    def test_process_secret_data(self, mock_resolve):
        """Test processing Secret with data containing Keeper URIs."""
        mock_resolve.return_value = "resolved-value"

        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "data": {
                "token": "keeper://Auth Service/field/token",
                "regular-key": "cmVndWxhci12YWx1ZQ==",  # base64 encoded "regular-value"
            },
        }

        result = process_secret(doc)

        expected_encoded = base64.b64encode(b"resolved-value").decode("ascii")
        assert result["data"]["token"] == expected_encoded
        assert result["data"]["regular-key"] == "cmVndWxhci12YWx1ZQ=="
        mock_resolve.assert_called_once_with("keeper://Auth Service/field/token")

    @patch("keepomize.core.resolve_keeper_uri")
    def test_process_secret_no_keeper_uris(self, mock_resolve):
        """Test processing Secret with no Keeper URIs."""
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "stringData": {"password": "regular-password"},
            "data": {"token": "cmVndWxhci10b2tlbg=="},
        }

        result = process_secret(doc)

        assert result == doc
        mock_resolve.assert_not_called()

    def test_process_secret_empty_secret(self):
        """Test processing empty Secret."""
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
        }

        result = process_secret(doc)

        assert result == doc

    @patch("keepomize.core.resolve_keeper_uri")
    def test_process_secret_mixed_values(self, mock_resolve):
        """Test processing Secret with mixed Keeper URIs and regular values."""
        mock_resolve.side_effect = ["resolved-password", "resolved-token"]

        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "stringData": {
                "password": "keeper://MySQL Database/field/password",
                "username": "regular-username",
            },
            "data": {
                "token": "keeper://Auth Service/field/token",
                "config": "Y29uZmlnLXZhbHVl",
            },
        }

        result = process_secret(doc)

        assert result["stringData"]["password"] == "resolved-password"
        assert result["stringData"]["username"] == "regular-username"

        expected_token = base64.b64encode(b"resolved-token").decode("ascii")
        assert result["data"]["token"] == expected_token
        assert result["data"]["config"] == "Y29uZmlnLXZhbHVl"

        assert mock_resolve.call_count == 2
