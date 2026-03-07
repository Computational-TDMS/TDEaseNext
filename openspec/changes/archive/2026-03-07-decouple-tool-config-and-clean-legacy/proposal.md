## Why

Tool definitions currently contain environment-specific absolute paths and there are overlapping legacy registry/adapter code paths that increase maintenance risk. This limits portability across dev/staging/prod and makes production rollout brittle.

## What Changes

- Introduce environment-agnostic tool resolution with profile-based overrides.
- Remove or deprecate legacy duplicate registry/adapter paths that are not used by the active execution stack.
- Add validation that blocks non-portable absolute path patterns in shared tool configs.
- Update operational docs for profile configuration and migration.

## Capabilities

### New Capabilities
- `environment-agnostic-tool-configuration`: Portable tool configuration with profile-based resolution and legacy path cleanup.

### Modified Capabilities
- None.

## Impact

- `config/tools/*.json` conventions and tool-loading services.
- Legacy registry/adapter modules and dependency wiring.
- Deployment configuration docs and environment setup procedures.
