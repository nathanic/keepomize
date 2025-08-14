# Claude Context for Keepomize Project

## Project Overview
Keepomize is a Python CLI tool that filters Kubernetes manifests to resolve Keeper URIs in Secret resources (or all documents with `--all` flag) using the `ksm` command-line tool. It's designed to work in pipelines after Kustomize.

**Author**: Nathan Stien (nathanism@gmail.com)  
**GitHub**: nathanic/keepomize  
**Current Version**: 0.1.3-dev

## Project Structure
```
keepomize/
├── src/keepomize/
│   ├── __init__.py          # Package initialization
│   ├── core.py              # Core URI resolution logic
│   └── cli.py               # Command-line interface with argparse
├── tests/                   # Comprehensive pytest test suite (96% coverage)
├── .github/workflows/       # CI/CD for testing and PyPI publishing
├── pyproject.toml          # uv project configuration with setuptools
├── README.md               # Complete documentation
└── CLAUDE.md               # This file
```

## Key Implementation Details

### Core Functionality (`src/keepomize/core.py`)
- **resolve_keeper_uri()**: Uses `ksm secret notation <uri>` command (elegant approach)
- **process_secret()**: Processes Kubernetes Secret manifests, resolving Keeper URIs in stringData and data fields
- **process_document()**: Processes any document type, recursively resolving Keeper URIs in all string values (used with `--all` flag)
- **KEEPER_URI_PATTERN**: Simple regex `^keeper://(.+)$` that supports full Keeper notation
- **Environment Variables**: ksm subprocess inherits full environment (preserves HOME, SSL_CERT_FILE, proxy settings, etc.)

### CLI Interface (`src/keepomize/cli.py`)
- Uses argparse with comprehensive --help documentation
- Includes Keeper notation examples and links to official docs
- Processes YAML from stdin, outputs to stdout (filter pattern)
- Uses ruamel.yaml for better formatting preservation
- **--all flag**: Process all documents, not just Kubernetes Secrets

### Keeper Notation Support
Supports full Keeper notation syntax:
```
keeper://<TITLE|UID>/<selector>/<parameters>[[predicate1][predicate2]]
```
Examples:
- `keeper://MySQL Database/field/password`
- `keeper://Contact/field/name[first]`
- `keeper://Record/custom_field/phone[1][number]`

## Development Setup
- **Package Manager**: uv (modern Python packaging)
- **Build System**: setuptools with src-layout
- **Testing**: pytest with 35 tests, 96% coverage
- **Code Quality**: ruff (linting), mypy (type checking)
- **Installation**: `pipx install -e .` for development (editable install)

## Testing Commands
```bash
uv run pytest                    # Run all tests
uv run pytest --cov=keepomize   # Run with coverage
uv run ruff check .              # Lint code
uv run mypy src/keepomize        # Type check
```

## Usage Patterns
```bash
# Basic usage (processes only Secret resources)
kustomize build overlays/prod | keepomize | kubectl apply -f -

# Process all documents for Keeper URIs
kustomize build overlays/prod | keepomize --all | kubectl apply -f -

# With OpenShift
kustomize build overlays/prod | keepomize | oc apply -f -
kustomize build overlays/prod | keepomize --all | oc apply -f -

# Help
keepomize --help
```

## CI/CD Configuration
- **GitHub Actions**: Configured for Python 3.8-3.12 testing
- **PyPI Publishing**: Automated on git tags (v*)
- **Environment Variables**: KSM_CONFIG, KSM_TOKEN, etc. automatically passed through

## Key Decisions Made
1. **ksm Integration**: Uses `ksm secret notation` command (not `ksm exec`) for cleaner implementation
2. **Regex Pattern**: Simplified to `^keeper://(.+)$` to support full Keeper notation complexity
3. **Error Handling**: Defers URI validation to ksm tool (authoritative source)
4. **Environment Variables**: Inherits full environment for compatibility (HOME, SSL_CERT_FILE, proxy settings, etc.)
5. **Build System**: Switched from hatchling to setuptools for better uv compatibility
6. **Test Configuration**: Added `pythonpath = ["src"]` to pytest config for src-layout

## Important Notes
- Project is ready for PyPI deployment
- All tests pass, comprehensive coverage
- Documentation includes official Keeper notation links
- CLI provides helpful examples and error messages
- Code is clean, well-typed, and follows Python best practices

## Recent Improvements
- Added full Keeper notation support with realistic examples
- Implemented full environment inheritance for ksm subprocess compatibility
- Added comprehensive --help with examples and documentation links
- Switched to elegant `ksm secret notation` command
- Fixed pytest configuration for src-layout projects
- Added proper .gitignore and removed debug output

## Future Work - Priority Roadmap

### Architecture Philosophy
**Maintain Filter Pattern**: Continue with the current `kustomize build | keepomize | kubectl apply` pattern. Kustomize plugin integration is NOT recommended due to plugin system immaturity, security concerns, and deployment complexity. The filter pattern aligns with Unix philosophy and modern DevOps practices.

### High Priority (Immediate)
1. **Critical Bug Fixes**
   - **✅ Fix trailing newline handling**: Implemented robust line ending stripping from `ksm` output (affects both stringData and base64-encoded data fields)
   - **✅ Fix environment variable passing**: Implemented full environment inheritance (preserves HOME, SSL_CERT_FILE, proxy settings needed by ksm)

2. **Essential Features**
   - Add `--validate` flag to check URI syntax without resolution
   - Add `--dry-run` flag to show what would be resolved without actual resolution
   - Add `--debug`/`--verbose` flag for detailed resolution logging

3. **Better Error Context**
   - Include document names and line numbers in error messages
   - Provide clearer feedback for common URI syntax issues
   - Better handling of ksm command failures with actionable suggestions

4. **Integration Documentation**
   - Comprehensive ArgoCD build hook examples
   - GitLab CI pipeline integration patterns  
   - External Secrets Operator compatibility guide
   - Helm template integration examples

### Medium Priority (Next Release)
1. **Configuration Support**
   - Support `~/.keepomize.yaml` for default settings
   - Allow per-project `.keepomize.yaml` configuration
   - Configuration for default KSM settings and options

2. **Advanced Processing Control**
   - Support `keepomize.io/` annotations for per-Secret processing control
   - Add `--include`/`--exclude` patterns for selective Secret processing
   - Handle binary/file fields from Keeper appropriately (detect `file` selector, handle base64 encoding)

3. **Developer Experience**
   - Shell completion scripts for bash/zsh
   - Better pipeline integration tooling
   - Improved CLI help and error messages

### Low Priority (Future Versions)
1. **Format & Extensibility**
   - JSON input/output support if requested
   - Extensible resolver architecture for other secret backends

2. **Ecosystem Integration**
   - **Containerized KRM Function**: Package keepomize + ksm in minimal OCI image for `kustomize fn eval` usage
   - Create reusable kustomize components for common keepomize patterns
   - Monitor kustomize plugin ecosystem maturity for future consideration
   - Integration with other secret management tools

### Architecture Integration Suggestions
1. **Pipeline Tooling**: Focus on making the filter pattern more powerful rather than pursuing complex integrations
2. **Observability**: Better logging, metrics, and debugging capabilities for production use
3. **CI/CD Optimization**: Tools and examples for common continuous deployment patterns
4. **Security Hardening**: Enhanced validation and safer secret handling practices

## New Features (v0.1.3-dev)
- **✅ --all flag**: Added `--all` CLI flag to process all documents, not just Secrets
- **✅ Universal processing**: New `process_document()` function recursively processes any document type
- **✅ Comprehensive testing**: Added 11 new tests covering the --all flag functionality
- **✅ Updated documentation**: CLI help and examples updated to show both processing modes

## Recently Fixed Issues (v0.1.2)
- **✅ Trailing newlines**: Fixed robust line ending stripping from ksm output  
- **✅ Environment isolation**: Fixed by implementing full environment inheritance
- **✅ KSM timeout protection**: Added configurable timeout for ksm subprocess calls (KEEPOMIZE_KSM_TIMEOUT env var, default 30s)
- **✅ Version management**: Removed version duplication by using single source of truth in pyproject.toml with importlib.metadata
- **✅ CLI improvements**: Added --version flag and improved help documentation with environment variable info

### Future Considerations
- Monitor for new Keeper notation features
- Watch for ksm command updates or new subcommands
- Keep an eye on kustomize plugin ecosystem maturation
- Maintain focus on core secret resolution functionality - avoid feature creep