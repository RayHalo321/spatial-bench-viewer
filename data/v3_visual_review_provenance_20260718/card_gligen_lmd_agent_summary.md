# Cardinality Audit Validation Summary

- Scope: strict direct-visual cardinality-only audit for `gligen` and `lmd_plus`.
- Protocol: exactly one required instance per canonical; duplicates, missing objects, partial/ambiguous instances are `no`.
- Input/output cases: 93 / 93 in frozen input order.
- Cardinality checks per method: 269.

| Method | Passed checks | Total checks | Check accuracy | All-cardinality cases | Total cases | Case rate |
|---|---:|---:|---:|---:|---:|---:|
| gligen | 223 | 269 | 82.9% | 66 | 93 | 71.0% |
| lmd_plus | 224 | 269 | 83.3% | 68 | 93 | 73.1% |

- Confidence rows: high=77, medium=14, low=2.
- Validation: every input cardinality check appears exactly once under each method; no extra checks; IDs and row order match input.
