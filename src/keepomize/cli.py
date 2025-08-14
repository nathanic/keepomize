"""
Command-line interface for keepomize.
"""

import argparse
import subprocess
import sys
from typing import Any, List

try:
    from importlib.metadata import version as get_version
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import version as get_version  # type: ignore[import-not-found,no-redef]  # noqa: I001

from ruamel.yaml import YAML

from .core import process_secret


def main() -> None:
    """
    Main entry point for the keepomize CLI.

    Reads a multi-document YAML stream from stdin, finds any Kubernetes Secret
    resources, and replaces Keeper URIs in their stringData and data fields
    by resolving them through ksm.
    """
    parser = argparse.ArgumentParser(
        prog="keepomize",
        description="A filter for Kubernetes manifests that resolves Keeper URIs in Secret resources",
        epilog="""
Examples:
  kustomize build overlays/prod | keepomize | kubectl apply -f -
  kustomize build overlays/prod | keepomize | oc apply -f -

Keeper URI format:
  keeper://<TITLE|UID>/<selector>/<parameters>[[predicate1][predicate2]]

  Examples:
    keeper://MySQL Database/field/password
    keeper://API Keys/field/api_key
    keeper://Contact/field/name[first]
    keeper://Record/custom_field/phone[1][number]

Environment variables:
  KEEPOMIZE_KSM_TIMEOUT: Timeout in seconds for ksm commands (default: 30)

For more information about Keeper notation:
https://docs.keeper.io/en/keeperpam/secrets-manager/about/keeper-notation
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", action="version", version=f"keepomize {get_version('keepomize')}"
    )

    parser.parse_args()

    # If we get here, no --help was used, so proceed with normal processing
    # Use ruamel.yaml for better preservation of formatting and comments
    yaml: YAML = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # Avoid line wrapping

    # Load all documents from stdin
    try:
        documents: List[Any] = list(yaml.load_all(sys.stdin))
    except Exception as e:
        print(f"Error: Failed to parse YAML input: {e}", file=sys.stderr)
        sys.exit(1)

    # Process each document
    for i, doc in enumerate(documents):
        if doc is None:
            continue

        # Check if this is a Kubernetes Secret
        if isinstance(doc, dict) and doc.get("kind") == "Secret":
            try:
                process_secret(doc)
            except subprocess.CalledProcessError:
                sys.exit(1)
            except Exception as e:
                print(f"Error processing document {i}: {e}", file=sys.stderr)
                sys.exit(1)

    # Output all documents
    yaml.dump_all(documents, sys.stdout)


if __name__ == "__main__":
    main()
