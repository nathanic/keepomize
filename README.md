# Keepomize

A filter for Kubernetes manifests that resolves Keeper URIs in Secret resources using the `ksm` command-line tool.

## Overview

Keepomize is designed to work in a pipeline after Kustomize to resolve Keeper URIs in Kubernetes Secret manifests. It reads a multi-document YAML stream from stdin, finds any Kubernetes Secret resources, and replaces Keeper URIs (`keeper://RECORDID/fieldspec`) in their `stringData` and `data` fields by resolving them through `ksm`.

## Prerequisites

- Python 3.8 or higher
- The `ksm` command-line tool must be installed and available in your PATH
- Access to Keeper secrets that you want to resolve

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
  database-password: keeper://ABC123/field/password
  api-key: keeper://DEF456/field/api_key
data:
  secret-token: keeper://GHI789/field/token  # Will be base64 encoded
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
  api-key: my-actual-api-key
data:
  secret-token: bXktYWN0dWFsLXRva2Vu  # base64 encoded value
```

### Keeper URI format

Keeper URIs follow this format:
```
keeper://RECORD_ID/field/FIELD_NAME
```

Where:
- `RECORD_ID` is the Keeper record identifier
- `FIELD_NAME` is the name of the field containing the secret value

### How it works

1. **Input**: Reads multi-document YAML from stdin
2. **Processing**: 
   - Identifies Kubernetes Secret resources (where `kind: Secret`)
   - Scans `stringData` and `data` fields for Keeper URIs
   - Resolves URIs using `ksm exec` with environment variables
   - For `data` fields, base64 encodes the resolved values
3. **Output**: Writes the modified YAML to stdout

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Deploy with secret resolution
  run: |
    kustomize build overlays/production | keepomize | kubectl apply -f -
  env:
    KEEPER_CONFIG: ${{ secrets.KEEPER_CONFIG }}
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

### 0.1.0

- Initial release
- Support for resolving Keeper URIs in Secret stringData and data fields
- CLI tool with proper error handling
- Full test suite