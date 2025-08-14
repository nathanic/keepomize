"""Tests for keepomize CLI functionality."""

from unittest.mock import MagicMock, patch

import pytest

from keepomize.cli import main


class TestCliMain:
    """Test the main CLI function."""

    @patch("sys.argv", ["keepomize"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_secret")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_processes_secrets(
        self, mock_stdout, mock_stdin, mock_process_secret, mock_yaml
    ):
        """Test that main processes Secret documents correctly."""
        # Setup mock YAML input
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": "test-secret"},
                "stringData": {"password": "keeper://ABC123/field/password"},
            },
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "test-config"},
                "data": {"config": "value"},
            },
        ]

        main()

        # Verify that process_secret was called only for the Secret
        mock_process_secret.assert_called_once()
        mock_yaml_instance.dump_all.assert_called_once()

    @patch("sys.argv", ["keepomize"])
    @patch("keepomize.cli.YAML")
    @patch("sys.stdin")
    @patch("sys.stderr")
    def test_main_yaml_parse_error(self, mock_stderr, mock_stdin, mock_yaml):
        """Test that main handles YAML parsing errors gracefully."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.side_effect = Exception("YAML parse error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("sys.argv", ["keepomize"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_secret")
    @patch("sys.stdin")
    @patch("sys.stderr")
    def test_main_process_secret_error(
        self, mock_stderr, mock_stdin, mock_process_secret, mock_yaml
    ):
        """Test that main handles process_secret errors gracefully."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": "test-secret"},
                "stringData": {"password": "keeper://ABC123/field/password"},
            }
        ]

        mock_process_secret.side_effect = Exception("Process error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("sys.argv", ["keepomize"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_secret")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_handles_none_documents(
        self, mock_stdout, mock_stdin, mock_process_secret, mock_yaml
    ):
        """Test that main handles None documents in the YAML stream."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            None,
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": "test-secret"},
                "stringData": {"password": "keeper://ABC123/field/password"},
            },
            None,
        ]

        main()

        # Should only process the non-None Secret document
        mock_process_secret.assert_called_once()
        mock_yaml_instance.dump_all.assert_called_once()

    @patch("sys.argv", ["keepomize"])
    @patch("keepomize.cli.YAML")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_ignores_non_secrets(self, mock_stdout, mock_stdin, mock_yaml):
        """Test that main ignores non-Secret documents."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "test-config"},
                "data": {"config": "value"},
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "test-deployment"},
                "spec": {"replicas": 1},
            },
        ]

        with patch("keepomize.cli.process_secret") as mock_process_secret:
            main()

            # Should not process any documents
            mock_process_secret.assert_not_called()
            mock_yaml_instance.dump_all.assert_called_once()

    @patch("sys.argv", ["keepomize", "--version"])
    def test_main_version_flag(self):
        """Test that --version flag works correctly."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with code 0 for --version
        assert exc_info.value.code == 0

    @patch("sys.argv", ["keepomize", "--all"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_document")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_all_flag_processes_all_documents(
        self, mock_stdout, mock_stdin, mock_process_document, mock_yaml
    ):
        """Test that --all flag processes all documents."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "test-config"},
                "data": {"password": "keeper://ABC123/field/password"},
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "test-deployment"},
                "spec": {"replicas": 1},
            },
        ]

        main()

        # Verify that process_document was called for both documents
        assert mock_process_document.call_count == 2
        mock_yaml_instance.dump_all.assert_called_once()

    @patch("sys.argv", ["keepomize", "--all"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_document")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_all_flag_does_not_call_process_secret(
        self, mock_stdout, mock_stdin, mock_process_document, mock_yaml
    ):
        """Test that --all flag uses process_document, not process_secret."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": "test-secret"},
                "stringData": {"password": "keeper://ABC123/field/password"},
            }
        ]

        with patch("keepomize.cli.process_secret") as mock_process_secret:
            main()

            # With --all flag, should use process_document even for Secrets
            mock_process_document.assert_called_once()
            mock_process_secret.assert_not_called()

    @patch("sys.argv", ["keepomize"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_secret")
    @patch("keepomize.cli.process_document")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_default_behavior_only_processes_secrets(
        self, mock_stdout, mock_stdin, mock_process_document, mock_process_secret, mock_yaml
    ):
        """Test that default behavior (no --all) only processes Secrets."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": "test-secret"},
                "stringData": {"password": "keeper://ABC123/field/password"},
            },
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "test-config"},
                "data": {"password": "keeper://ABC123/field/password"},
            },
        ]

        main()

        # Should only process the Secret, not the ConfigMap
        mock_process_secret.assert_called_once()
        mock_process_document.assert_not_called()
        mock_yaml_instance.dump_all.assert_called_once()

    @patch("sys.argv", ["keepomize", "--all"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_document")
    @patch("sys.stdin")
    @patch("sys.stderr")
    def test_main_all_flag_handles_process_error(
        self, mock_stderr, mock_stdin, mock_process_document, mock_yaml
    ):
        """Test that --all flag handles process_document errors gracefully."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "test-config"},
                "data": {"password": "keeper://ABC123/field/password"},
            }
        ]

        mock_process_document.side_effect = Exception("Process error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("sys.argv", ["keepomize", "--all"])
    @patch("keepomize.cli.YAML")
    @patch("keepomize.cli.process_document")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_main_all_flag_handles_none_documents(
        self, mock_stdout, mock_stdin, mock_process_document, mock_yaml
    ):
        """Test that --all flag handles None documents correctly."""
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        mock_yaml_instance.load_all.return_value = [
            None,
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "test-config"},
                "data": {"password": "keeper://ABC123/field/password"},
            },
            None,
        ]

        main()

        # Should only process the non-None ConfigMap document
        mock_process_document.assert_called_once()
        mock_yaml_instance.dump_all.assert_called_once()
