# Cardinality Audit Summary

- Protocol: blind direct-visual inspection of the supplied images only.
- Scope: cardinality checks only; strict `unclear=fail`.
- Coverage: 93/93 cases in frozen input order; 269/269 checks per method.
- Validation: no missing or duplicate case IDs; every expected cardinality check appears exactly once for both methods.

| Method | Passed checks | Check accuracy | All-cardinality cases | Case rate |
|---|---:|---:|---:|---:|
| FLUX | 249/269 | 92.57% | 77/93 | 82.80% |
| SDXL | 184/269 | 68.40% | 42/93 | 45.16% |

Failure rule: missing objects, duplicate/extra instances, and visually ambiguous instances are all scored `no`.
