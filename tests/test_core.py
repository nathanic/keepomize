"""Tests for keepomize core functionality."""

import pytest
import base64
import subprocess
import os
from unittest.mock import patch, MagicMock
from keepomize.core import resolve_keeper_uri, process_secret, KEEPER_URI_PATTERN


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
    
    @patch('keepomize.core.shutil.which')
    @patch('keepomize.core.subprocess.run')
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
    
    @patch('keepomize.core.shutil.which')
    def test_resolve_keeper_uri_ksm_not_found(self, mock_which):
        """Test error when ksm is not found in PATH."""
        mock_which.return_value = None
        
        with pytest.raises(FileNotFoundError, match="ksm command not found in PATH"):
            resolve_keeper_uri("keeper://MySQL Database/field/password")
    
    @patch('keepomize.core.shutil.which')
    @patch('keepomize.core.subprocess.run')
    def test_resolve_keeper_uri_subprocess_error(self, mock_run, mock_which):
        """Test error when ksm subprocess fails."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_run.side_effect = subprocess.CalledProcessError(1, "ksm")
        
        with pytest.raises(subprocess.CalledProcessError):
            resolve_keeper_uri("keeper://MySQL Database/field/password")
    
    @patch('keepomize.core.shutil.which')
    @patch('keepomize.core.subprocess.run')
    @patch.dict(os.environ, {'KSM_CONFIG': '/path/to/config', 'KSM_TOKEN': 'secret123', 'OTHER_VAR': 'ignored'})
    def test_resolve_keeper_uri_passes_ksm_env_vars(self, mock_run, mock_which):
        """Test that KSM_* environment variables are passed through."""
        mock_which.return_value = "/usr/local/bin/ksm"
        mock_result = MagicMock()
        mock_result.stdout = "resolved-secret-value"
        mock_run.return_value = mock_result
        
        resolve_keeper_uri("keeper://MySQL Database/field/password")
        
        # Verify that subprocess.run was called with KSM_* env vars
        call_args = mock_run.call_args
        env_passed = call_args.kwargs['env']
        
        assert 'KSM_CONFIG' in env_passed
        assert 'KSM_TOKEN' in env_passed
        assert 'OTHER_VAR' not in env_passed  # Non-KSM vars should not be passed
        assert 'KEEPER_RESOLVE_URI' not in env_passed  # No longer needed with direct notation command
        
        assert env_passed['KSM_CONFIG'] == '/path/to/config'
        assert env_passed['KSM_TOKEN'] == 'secret123'


class TestProcessSecret:
    """Test the process_secret function."""
    
    @patch('keepomize.core.resolve_keeper_uri')
    def test_process_secret_stringdata(self, mock_resolve):
        """Test processing Secret with stringData containing Keeper URIs."""
        mock_resolve.return_value = "resolved-value"
        
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "stringData": {
                "password": "keeper://MySQL Database/field/password",
                "regular-key": "regular-value"
            }
        }
        
        result = process_secret(doc)
        
        assert result["stringData"]["password"] == "resolved-value"
        assert result["stringData"]["regular-key"] == "regular-value"
        mock_resolve.assert_called_once_with("keeper://MySQL Database/field/password")
    
    @patch('keepomize.core.resolve_keeper_uri')
    def test_process_secret_data(self, mock_resolve):
        """Test processing Secret with data containing Keeper URIs."""
        mock_resolve.return_value = "resolved-value"
        
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "data": {
                "token": "keeper://Auth Service/field/token",
                "regular-key": "cmVndWxhci12YWx1ZQ=="  # base64 encoded "regular-value"
            }
        }
        
        result = process_secret(doc)
        
        expected_encoded = base64.b64encode("resolved-value".encode('utf-8')).decode('ascii')
        assert result["data"]["token"] == expected_encoded
        assert result["data"]["regular-key"] == "cmVndWxhci12YWx1ZQ=="
        mock_resolve.assert_called_once_with("keeper://Auth Service/field/token")
    
    @patch('keepomize.core.resolve_keeper_uri')
    def test_process_secret_no_keeper_uris(self, mock_resolve):
        """Test processing Secret with no Keeper URIs."""
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "stringData": {
                "password": "regular-password"
            },
            "data": {
                "token": "cmVndWxhci10b2tlbg=="
            }
        }
        
        result = process_secret(doc)
        
        assert result == doc
        mock_resolve.assert_not_called()
    
    def test_process_secret_empty_secret(self):
        """Test processing empty Secret."""
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"}
        }
        
        result = process_secret(doc)
        
        assert result == doc
    
    @patch('keepomize.core.resolve_keeper_uri')
    def test_process_secret_mixed_values(self, mock_resolve):
        """Test processing Secret with mixed Keeper URIs and regular values."""
        mock_resolve.side_effect = ["resolved-password", "resolved-token"]
        
        doc = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret"},
            "stringData": {
                "password": "keeper://MySQL Database/field/password",
                "username": "regular-username"
            },
            "data": {
                "token": "keeper://Auth Service/field/token",
                "config": "Y29uZmlnLXZhbHVl"
            }
        }
        
        result = process_secret(doc)
        
        assert result["stringData"]["password"] == "resolved-password"
        assert result["stringData"]["username"] == "regular-username"
        
        expected_token = base64.b64encode("resolved-token".encode('utf-8')).decode('ascii')
        assert result["data"]["token"] == expected_token
        assert result["data"]["config"] == "Y29uZmlnLXZhbHVl"
        
        assert mock_resolve.call_count == 2