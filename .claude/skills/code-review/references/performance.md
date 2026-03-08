# Performance Checklist

## Database & Queries
- N+1 query patterns (queries inside loops)
- Missing database indexes for frequent query patterns
- SELECT * instead of selecting needed columns
- Unbounded queries without LIMIT
- Missing pagination for large result sets
- Unnecessary eager loading or missing necessary eager loading
- Transaction scope too broad (holding locks unnecessarily)

## Memory
- Memory leaks: growing collections never cleared, event listeners never removed
- Large objects held in closures unnecessarily
- Unbounded caches without eviction policy
- Loading entire large files/datasets into memory
- String concatenation in loops (use StringBuilder/join instead)
- Circular references preventing garbage collection

## Algorithmic
- O(n²) or worse when O(n) or O(n log n) is possible
- Redundant computations inside loops (move invariants outside)
- Missing memoization for expensive repeated calculations
- Sequential operations that could be parallelized
- Unnecessary sorting or repeated sorting of same data

## Network & I/O
- Sequential API calls that could be parallelized (`Promise.all`, `asyncio.gather`)
- Missing request batching (many small requests instead of one batch)
- Large payloads without compression or pagination
- Missing caching for frequently accessed, rarely changing data
- Polling when webhooks/subscriptions are available
- Missing timeout on external requests

## Frontend Rendering
- Unnecessary re-renders (missing `useMemo`, `useCallback`, `React.memo`)
- Large bundle size (unused imports, missing code splitting)
- Layout thrashing (reading then writing DOM in loops)
- Missing virtualization for long lists
- Blocking the main thread with heavy computation
- Unoptimized images (missing lazy loading, oversized assets)
- Missing debounce/throttle on frequent events (scroll, resize, input)

## Async & Concurrency
- Blocking operations on main/event loop thread
- Missing connection pooling for database/HTTP connections
- Thread-unsafe operations in concurrent context
- Deadlock potential from lock ordering
- Missing backpressure handling for streams/queues
