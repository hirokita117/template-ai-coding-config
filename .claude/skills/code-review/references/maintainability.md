# Maintainability Checklist

## Naming
- Misleading or ambiguous variable/function names
- Inconsistent naming conventions within the codebase
- Single-letter variables outside of short lambdas or loop indices
- Boolean names that don't read as predicates (`data` vs `isLoaded`)
- Abbreviations that reduce clarity

## Structure & Design
- Functions/methods doing too many things (SRP violation)
- Excessive function length (>50 lines: likely needs decomposition)
- Deep nesting (>3 levels: consider early returns or extraction)
- God classes/modules with too many responsibilities
- Tight coupling between unrelated components
- Duplicated logic that should be extracted (DRY, but avoid premature abstraction)

## Code Smells
- Magic numbers/strings without named constants
- Commented-out code left in place
- TODO/FIXME/HACK without tracking issue
- Boolean parameters that change function behavior (use separate functions or options object)
- Long parameter lists (>4: consider object/struct parameter)
- Feature envy (method uses another object's data more than its own)

## API Design
- Breaking changes to public interfaces without versioning
- Inconsistent error response formats
- Missing input validation at API boundaries
- Overly broad function signatures (accepting `any` or untyped objects)
- Leaking implementation details in public interfaces

## Pattern Consistency
- Deviating from established patterns in the codebase without justification
- Mixing paradigms unnecessarily (e.g., callbacks and promises in same module)
- Inconsistent error handling strategy across similar operations
- New code not following directory/file organization conventions
