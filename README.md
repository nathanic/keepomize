# Keepomize

A filter for Kubernetes manifests that resolves Keeper URIs in Secret resources (or all documents with `--all` flag) using the `ksm` command-line tool.

## Overview

Keepomize is designed to work in a pipeline after Kustomize to resolve Keeper URIs in Kubernetes manifests. By default, it processes only Secret resources, but with the `--all` flag it can process any document type. It reads a multi-document YAML stream from stdin and replaces Keeper URIs (`keeper://RECORDID/fieldspec`) by resolving them through `ksm`.

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
# Process only Secret resources (default behavior)
kustomize build overlays/production | keepomize | kubectl apply -f -

# Process all documents for Keeper URIs
kustomize build overlays/production | keepomize --all | kubectl apply -f -

# Use with kustomize and oc (OpenShift)
kustomize build overlays/production | keepomize | oc apply -f -
kustomize build overlays/production | keepomize --all | oc apply -f -
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

### Example with --all flag

Before processing (mixed document types):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secrets
stringData:
  database-password: keeper://MySQL Database/field/password
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database-url: keeper://MySQL Database/field/url
  regular-setting: some-value
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: API_KEY
          value: keeper://API Keys/field/token
        - name: DEBUG
          value: "true"
```

After processing with `keepomize --all`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secrets
stringData:
  database-password: my-actual-password
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database-url: mysql://localhost:3306/mydb
  regular-setting: some-value
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: API_KEY
          value: sk-1234567890abcdef
        - name: DEBUG
          value: "true"
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

### Processing modes

#### Default mode (Secrets only)
By default, keepomize processes only Kubernetes Secret resources:
1. **Input**: Reads multi-document YAML from stdin
2. **Processing**: 
   - Identifies Kubernetes Secret resources (where `kind: Secret`)
   - Scans `stringData` and `data` fields for Keeper URIs
   - Resolves URIs using `ksm secret notation` command
   - For `data` fields, base64 encodes the resolved values
3. **Output**: Writes the modified YAML to stdout

#### Universal mode (`--all` flag)
With the `--all` flag, keepomize processes all document types:
1. **Input**: Reads multi-document YAML from stdin
2. **Processing**: 
   - Processes all documents (ConfigMaps, Deployments, etc.)
   - Recursively scans all string values for Keeper URIs
   - Resolves URIs using `ksm secret notation` command
   - Replaces only exact Keeper URI matches
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
- Preserve all non-Secret resources unchanged (unless using `--all` flag)

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

### 0.1.3-dev

- **New Features**:
  - Added `--all` flag to process all documents, not just Kubernetes Secrets
  - New `process_document()` function for universal document processing
  - Recursive processing of all string values in any document type
- **Testing**: Added 11 new tests for `--all` flag functionality (35 total tests, 96% coverage)
- **Documentation**: Updated CLI help and examples to show both processing modes

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