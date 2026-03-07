## 1. Secure Launch Path

- [x] 1.1 Implement argument-vector subprocess launch as default execution mode.
- [x] 1.2 Remove or isolate shell-string launch from common local executor paths.
- [x] 1.3 Add pre-launch validation for executable resolution and workspace boundaries.

## 2. Error Handling Hardening

- [x] 2.1 Introduce execution error mapping to stable external error codes/messages.
- [x] 2.2 Redact raw exception details from global/public API responses.
- [x] 2.3 Add correlation identifiers linking API errors to internal logs.

## 3. Security Regression Coverage

- [x] 3.1 Add tests for command-injection payload literals.
- [x] 3.2 Add tests for path traversal and invalid workspace launch rejection.
- [x] 3.3 Add platform-specific quoting tests for Windows and non-Windows behavior.
