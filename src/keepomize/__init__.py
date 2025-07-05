"""
Keepomize - Resolve Keeper URIs in Kubernetes Secret manifests.

A filter for Kubernetes manifests that resolves Keeper URIs in Secret resources
using the ksm command-line tool.
"""

__version__ = "0.1.0"

from .core import resolve_keeper_uri, process_secret

__all__ = ["resolve_keeper_uri", "process_secret"]