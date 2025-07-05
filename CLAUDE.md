# Claude Context for Keepomize Project

## Project Overview
Keepomize is a Python CLI tool that filters Kubernetes manifests to resolve Keeper URIs in Secret resources using the `ksm` command-line tool. It's designed to work in pipelines after Kustomize.

**Author**: Nathan Stien (nathanism@gmail.com)  
**GitHub**: nathanic/keepomize  
**Current Version**: 0.1.0

## Project Structure
```
keepomize/
├── src/keepomize/
│   ├── __init__.py          # Package initialization
│   ├── core.py              # Core URI resolution logic
│   └── cli.py               # Command-line interface with argparse
├── tests/                   # Comprehensive pytest test suite (97% coverage)
├── .github/workflows/       # CI/CD for testing and PyPI publishing
├── pyproject.toml          # uv project configuration with setuptools
├── README.md               # Complete documentation
└── CLAUDE.md               # This file
```

## Key Implementation Details

### Core Functionality (`src/keepomize/core.py`)
- **resolve_keeper_uri()**: Uses `ksm secret notation <uri>` command (elegant approach)
- **process_secret()**: Processes Kubernetes Secret manifests, resolving Keeper URIs in stringData and data fields
- **KEEPER_URI_PATTERN**: Simple regex `^keeper://(.+)$` that supports full Keeper notation
- **Environment Variables**: Automatically passes through KSM_* env vars to ksm subprocess

### CLI Interface (`src/keepomize/cli.py`)
- Uses argparse with comprehensive --help documentation
- Includes Keeper notation examples and links to official docs
- Processes YAML from stdin, outputs to stdout (filter pattern)
- Uses ruamel.yaml for better formatting preservation

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
- **Testing**: pytest with 16 tests, 97% coverage
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
# Basic usage
kustomize build overlays/prod | keepomize | kubectl apply -f -

# With OpenShift
kustomize build overlays/prod | keepomize | oc apply -f -

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
4. **Environment Variables**: Only passes KSM_* prefixed vars for security
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
- Implemented KSM_* environment variable passthrough
- Added comprehensive --help with examples and documentation links
- Switched to elegant `ksm secret notation` command
- Fixed pytest configuration for src-layout projects
- Added proper .gitignore and removed debug output

## Future Considerations
- Monitor for new Keeper notation features
- Consider adding verbose/quiet modes if needed
- Watch for ksm command updates or new subcommands