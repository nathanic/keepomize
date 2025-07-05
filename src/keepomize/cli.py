"""
Command-line interface for keepomize.
"""

import sys
import subprocess
from typing import List
from ruamel.yaml import YAML

from .core import process_secret


def main() -> None:
    """
    Main entry point for the keepomize CLI.
    
    Reads a multi-document YAML stream from stdin, finds any Kubernetes Secret
    resources, and replaces Keeper URIs in their stringData and data fields
    by resolving them through ksm.
    """
    # Use ruamel.yaml for better preservation of formatting and comments
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # Avoid line wrapping
    
    # Load all documents from stdin
    try:
        documents = list(yaml.load_all(sys.stdin))
    except Exception as e:
        print(f"Error: Failed to parse YAML input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process each document
    for i, doc in enumerate(documents):
        if doc is None:
            continue
            
        # Check if this is a Kubernetes Secret
        if isinstance(doc, dict) and doc.get('kind') == 'Secret':
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