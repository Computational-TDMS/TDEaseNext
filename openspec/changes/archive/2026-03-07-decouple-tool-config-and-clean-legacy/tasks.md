## 1. Portable Tool Configuration

- [x] 1.1 Implement profile-based executable resolution in authoritative tool registry loading.
- [x] 1.2 Define and enforce precedence rules between base config and profile overrides.
- [x] 1.3 Add validation that rejects non-portable shared absolute paths.

## 2. Legacy Path Cleanup

- [x] 2.1 Inventory and remove or isolate duplicate legacy registry/adapter code paths.
- [x] 2.2 Ensure active execution services use only the authoritative registry implementation.
- [x] 2.3 Add compatibility notes/mapping for any removed legacy behavior.

## 3. Verification and Documentation

- [x] 3.1 Add tests for profile override resolution and fallback behavior.
- [x] 3.2 Add tests proving execution works without deprecated registry coupling.
- [x] 3.3 Update deployment docs with environment profile setup and migration steps.
