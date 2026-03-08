# Test Coverage Checklist

## Missing Tests
- New public functions/methods without corresponding tests
- New API endpoints without integration tests
- Bug fixes without regression tests
- Complex conditional logic without branch coverage
- Error paths and exception handling not tested
- Edge cases identified in code but not in tests

## Test Quality
- Tests that always pass (no meaningful assertions)
- Tests asserting implementation details instead of behavior
- Brittle tests depending on execution order or timing
- Missing assertions (test runs code but doesn't verify results)
- Overly broad assertions (`toBeTruthy()` when specific value expected)
- Tests that duplicate other tests without adding value

## Test Design
- Missing arrange/act/assert (or given/when/then) structure
- Test names that don't describe the scenario and expected outcome
- Shared mutable state between tests
- Missing test isolation (tests depending on other tests)
- Hardcoded test data that obscures the test's intent
- Missing negative tests (what should NOT happen)

## Coverage Gaps
- Happy path tested but error paths missing
- Boundary values not tested (0, 1, max, empty, null)
- Concurrency scenarios not tested
- Integration points tested only with mocks (no integration tests)
- Configuration changes not covered by tests
