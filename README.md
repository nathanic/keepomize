# Keepomize

A filter for Kubernetes manifests that resolves Keeper URIs in Secret resources using the `ksm` command-line tool.

## Overview

Keepomize is designed to work in a pipeline after Kustomize to resolve Keeper URIs in Kubernetes Secret manifests. It reads a multi-document YAML stream from stdin, finds any Kubernetes Secret resources, and replaces Keeper URIs (`keeper://RECORDID/fieldspec`) in their `stringData` and `data` fields by resolving them through `ksm`.

## Prerequisites

- Python 3.8 or higher
- The `ksm` command-line tool must be installed and available in your PATH
- Access to Keeper secrets that you want to resolve
- Any `KSM_*` environment variables needed for `ksm` configuration (automatically passed through)

## Installation

### From PyPI

```bash
pip install keepomize
```

### From source

```bash
git clone https://github.com/nathanic/keepomize.git
cd keepomize
uv sync
uv run keepomize --help
```

### Development installation

```bash
git clone https://github.com/nathanic/keepomize.git
cd keepomize
uv sync --dev
```

## Usage

### Basic usage

```bash
# Use with kustomize and kubectl
kustomize build overlays/production | keepomize | kubectl apply -f -

# Use with kustomize and oc (OpenShift)
kustomize build overlays/production | keepomize | oc apply -f -
```

### Example Secret manifest

Before processing:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secrets
  namespace: default
type: Opaque
stringData:
  database-password: keeper://MySQL Database/field/password
  api-key: keeper://API Keys/field/api_key
  username: keeper://MySQL Database/field/login
data:
  secret-token: keeper://Auth Service/field/token  # Will be base64 encoded
```

After processing with keepomize:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secrets
  namespace: default
type: Opaque
stringData:
  database-password: my-actual-password
  api-key: sk-1234567890abcdef
  username: mysql_user
data:
  secret-token: bXktYWN0dWFsLXRva2Vu  # base64 encoded value
```

### Keeper URI format

Keeper URIs use [Keeper notation](https://docs.keeper.io/en/keeperpam/secrets-manager/about/keeper-notation) which follows this format:
```
keeper://<TITLE|UID>/<selector>/<parameters>[[predicate1][predicate2]]
```

Common examples for Kubernetes Secrets:
```
keeper://MySQL Creds/field/password
keeper://API Keys/field/api_key
keeper://Contact/field/name[first]
keeper://Record/custom_field/phone[1][number]
```

Where:
- **First segment**: Record title or unique identifier (UID)
- **Selector**: `field` for standard fields, `custom_field` for custom fields, `file` for files
- **Parameters**: Field name or other identifiers
- **Predicates** (optional): Array indices `[0]` and sub-field access `[property]`

**Note**: Special characters (`/`, `\`, `[`, `]`) in record details must be escaped with backslash.

### How it works

1. **Input**: Reads multi-document YAML from stdin
2. **Processing**: 
   - Identifies Kubernetes Secret resources (where `kind: Secret`)
   - Scans `stringData` and `data` fields for Keeper URIs
   - Resolves URIs using `ksm secret notation` command
   - For `data` fields, base64 encodes the resolved values
3. **Output**: Writes the modified YAML to stdout

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Deploy with secret resolution
  run: |
    kustomize build overlays/production | keepomize | kubectl apply -f -
  env:
    KSM_CONFIG: ${{ secrets.KSM_CONFIG }}
    KSM_TOKEN: ${{ secrets.KSM_TOKEN }}
    # Any KSM_* environment variables are automatically passed to ksm
```

## Error handling

Keepomize will:
- Exit with status code 1 if `ksm` is not found in PATH
- Exit with status code 1 if any Keeper URI fails to resolve
- Print error messages to stderr while preserving stdout for the YAML output
- Preserve all non-Secret resources unchanged

## Development

### Running tests

```bash
uv run pytest
```

### Building for distribution

```bash
uv build
```

### Publishing to PyPI

```bash
uv publish
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Changelog

### 0.1.2

- **Critical Bug Fixes**:
  - Fixed trailing newline handling - ksm output now has trailing newlines stripped to prevent malformed secret values
  - Fixed environment variable inheritance - ksm subprocess now inherits full environment (preserves HOME, SSL_CERT_FILE, proxy settings, etc.)
- **Testing**: Added comprehensive tests for newline handling edge cases and environment inheritance

### 0.1.1

- **Bug Fix**: Fixed CLI argument parsing to restore --help functionality
- **Testing**: Added sys.argv patches to CLI tests for proper argument handling

### 0.1.0

- Initial release
- Support for resolving Keeper URIs in Secret stringData and data fields
- CLI tool with proper error handling
- Full test suite