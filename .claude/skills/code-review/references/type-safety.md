# Type Safety Checklist

## Type Correctness
- `any` type used where a specific type is possible
- Type assertions (`as`, `!`) without runtime validation
- `unknown` not narrowed before use
- Implicit `any` from missing type annotations (in strict mode)
- Generic types defaulting to `any` instead of constrained types

## Null Safety
- Optional chaining (`?.`) missing where value can be null/undefined
- Nullish coalescing (`??`) confused with OR (`||`) for falsy values
- Non-null assertions (`!`) without guarantees
- Missing null checks after operations that can return null (`.find()`, `.get()`, map lookup)
- Optional fields accessed without checking existence

## Type Narrowing
- Type guards that don't actually narrow correctly
- Missing discriminated union checks (unhandled union members)
- `instanceof` checks that break across module boundaries
- Switch/match on union types without exhaustiveness check

## Schema & Validation
- API response data used without runtime validation
- Form input assumed to match expected types
- Environment variables used without parsing/validation
- JSON.parse results used without type checking
- External data (files, databases) consumed without schema validation

## Generic & Inference Issues
- Overly broad generic constraints
- Lost type inference from intermediate `any` casts
- Incorrect variance in generic types (covariance vs contravariance)
- Missing readonly modifiers on data that shouldn't be mutated
