# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-06

### BREAKING CHANGES

**Package renamed from `dakora` to `promptlightning`**

This major version includes a complete rebrand of the project. All references to "Dakora" have been replaced with "PromptLightning" throughout the codebase, documentation, and examples.

#### Migration Guide

1. **Update package installation:**
   ```bash
   pip uninstall dakora
   pip install promptlightning
   ```

2. **Update imports in your code:**
   ```python
   # Before
   from dakora import Vault

   # After
   from promptlightning import Vault
   ```

3. **Rename configuration files:**
   ```bash
   mv dakora.yaml promptlightning.yaml
   ```

4. **Update CLI commands:**
   ```bash
   # Before
   dakora init
   dakora playground

   # After
   promptlightning init
   promptlightning playground
   ```

5. **Update database paths (if using logging):**
   Configuration file should reference `promptlightning.db` instead of `dakora.db`

### Changed
- Package name: `dakora` → `promptlightning`
- Python module: `dakora` → `promptlightning`
- CLI command: `dakora` → `promptlightning`
- Config file: `dakora.yaml` → `promptlightning.yaml`
- Default database: `dakora.db` → `promptlightning.db`
- Documentation URLs updated to reflect new branding
- All examples updated with new package name

### Notes
- Functionality remains identical to v1.0.2
- No API changes beyond naming
- All features, templates, and workflows work exactly the same way

## [1.0.2] - 2025-09-30

### Fixed
- Misleading error messages when running playground from PyPI installs ([#3](https://github.com/bogdan-pistol/dakora/issues/3))
- CLI now correctly detects pre-built UI and shows success message instead of "UI build failed"

## [1.0.1] - 2025-09-30

### Fixed
- Playground UI now builds fresh from source during releases, preventing stale assets ([#1](https://github.com/bogdan-pistol/dakora/issues/1))
- Release workflow now includes smoke tests to verify playground functionality before PyPI publication

### Changed
- Playground built assets are no longer tracked in git, only the directory structure (via `.gitkeep`)
- PyPI releases now include pre-built playground UI for out-of-the-box functionality
- Updated documentation to clarify installation requirements for playground feature

### Added
- Automated UI build step in release workflow
- Smoke test validation for playground server and API endpoints before release
- Hatchling configuration to properly package playground assets

## [1.0.0] - 2025-09-29

### Added
- Initial stable release
- Interactive web playground for template development
- Type-safe prompt templates with Pydantic validation
- File-based template management with YAML definitions
- Hot-reload support for development workflows
- Jinja2 templating with custom filters (`default`, `yaml`)
- Semantic versioning for templates
- Optional execution logging to SQLite
- CLI interface with commands: `init`, `list`, `get`, `bump`, `watch`, `playground`
- Thread-safe caching for production use
- FastAPI-based playground server with REST API
- Modern React UI built with shadcn/ui components
- Support for input types: string, number, boolean, array<string>, object
- Template registry pattern with local filesystem implementation
- Comprehensive test suite (unit, integration, performance)

[1.0.2]: https://github.com/bogdan-pistol/dakora/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/bogdan-pistol/dakora/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/bogdan-pistol/dakora/releases/tag/v1.0.0