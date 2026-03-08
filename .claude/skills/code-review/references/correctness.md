# Correctness Checklist

## Logic Errors
- Off-by-one errors in loops, slicing, pagination
- Incorrect boolean logic (De Morgan's law violations, short-circuit misuse)
- Wrong comparison operators (`==` vs `===`, `<` vs `<=`)
- Unreachable code or dead branches
- Missing `break`/`return` in switch/match statements

## Error Handling
- Unhandled exceptions or rejected promises
- Empty catch blocks that swallow errors silently
- Missing error propagation (errors caught but not re-thrown or logged)
- Incorrect error types thrown or caught
- Missing cleanup in error paths (resources, transactions, locks)

## Edge Cases
- Null/undefined/nil not handled before access
- Empty collections (arrays, maps) not checked
- Division by zero
- Integer overflow/underflow
- Empty string vs null distinction
- Concurrent access without synchronization

## State Management
- Race conditions in async/parallel code
- Stale closures capturing outdated state
- Mutations of shared state without protection
- Missing state reset after operations
- Inconsistent state between related variables

## Data Integrity
- Type coercion leading to unexpected results
- Floating-point comparison without epsilon
- Date/timezone handling errors
- Character encoding issues (UTF-8 assumptions)
- Missing data validation at boundaries

## Control Flow
- Infinite loops without exit conditions
- Missing await on async operations
- Callback vs Promise mixing
- Event listener leaks (added but never removed)
- Recursive functions without base case or depth limit
