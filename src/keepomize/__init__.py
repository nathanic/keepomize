"""
Keepomize - Resolve Keeper URIs in Kubernetes Secret manifests.

A filter for Kubernetes manifests that resolves Keeper URIs in Secret resources
using the ksm command-line tool.
"""

from .core import process_secret, resolve_keeper_uri

__all__ = ["resolve_keeper_uri", "process_secret"]
