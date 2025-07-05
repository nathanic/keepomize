"""
Core functionality for resolving Keeper URIs in Kubernetes Secret manifests.
"""

import re
import subprocess
import base64
import shutil
import sys
import os
from typing import Dict, Any


# Pattern to match Keeper URIs using Keeper notation
# Matches keeper://<title_or_uid>/<selector>/<parameters>[[predicates]]
# Allows for spaces, special characters, and escaped characters in titles
KEEPER_URI_PATTERN = re.compile(r'^keeper://(.+)$')


def resolve_keeper_uri(uri: str) -> str:
    """
    Resolve a Keeper URI using ksm exec.
    
    Args:
        uri: A Keeper URI using Keeper notation, such as:
             - "keeper://MySQL Database/field/password"
             - "keeper://API Keys/field/api_key"
             - "keeper://Contact/field/name[first]"
             - "keeper://Record/custom_field/phone[1][number]"
        
    Returns:
        The resolved secret value
        
    Raises:
        subprocess.CalledProcessError: If ksm fails to resolve the URI
        FileNotFoundError: If ksm command is not found
    """
    # Find the full path to ksm
    ksm_path = shutil.which("ksm")
    if not ksm_path:
        raise FileNotFoundError("ksm command not found in PATH")
    
    # Use ksm exec with the URI in an environment variable
    env_var = "KEEPER_RESOLVE_URI"
    cmd = [ksm_path, "exec", "--", "bash", "-c", f"echo -n ${env_var}"]
    
    # Pass through KSM_* environment variables along with our URI
    env = {env_var: uri}
    for key, value in os.environ.items():
        if key.startswith("KSM_"):
            env[key] = value
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to resolve Keeper URI '{uri}'", file=sys.stderr)
        print(f"ksm stderr: {e.stderr}", file=sys.stderr)
        raise


def process_secret(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a Kubernetes Secret document, resolving any Keeper URIs.
    
    Args:
        doc: A dict representing a Kubernetes Secret
        
    Returns:
        The modified document
    """
    modified = False
    
    # Process stringData if present
    if 'stringData' in doc:
        for key, value in doc['stringData'].items():
            if isinstance(value, str) and KEEPER_URI_PATTERN.match(value):
                resolved = resolve_keeper_uri(value)
                doc['stringData'][key] = resolved
                modified = True
                #print(f"Resolved keeper URI in stringData.{key}", file=sys.stderr)
    
    # Process data if present (base64 encoded values)
    if 'data' in doc:
        for key, value in doc['data'].items():
            if isinstance(value, str) and KEEPER_URI_PATTERN.match(value):
                # The value is a cleartext Keeper URI that needs to be resolved
                # and then base64 encoded
                resolved = resolve_keeper_uri(value)
                encoded = base64.b64encode(resolved.encode('utf-8')).decode('ascii')
                doc['data'][key] = encoded
                modified = True
                #print(f"Resolved keeper URI in data.{key} (base64 encoded)", file=sys.stderr)
    
    # if modified:
    #     print(f"Processed Secret: {doc.get('metadata', {}).get('name', 'unnamed')}", file=sys.stderr)
    
    return doc
