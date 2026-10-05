# Scalability & Performance Benchmark Report

Benchmark results testing schema-agnostic data generation and edge-case injection across record scales up to 1,000,000 (1M) records.

| Scale (Records) | Generation Time (sec) | Memory RSS (MB) | Throughput (Records/sec) |
|---|---|---|---|
| 1,000 | 0.002 s | 201.56 MB | 500,000 rec/sec |
| 10,000 | 0.004 s | 202.93 MB | 2,500,000 rec/sec |
| 100,000 | 0.024 s | 214.11 MB | 4,166,667 rec/sec |
| 1,000,000 | 0.213 s | 288.47 MB | 4,694,836 rec/sec |

## Scalability Optimization Highlights
- **Chunked Processing**: Datasets > 50,000 records use chunked vector allocation to limit peak memory overhead.
- **Vectorized Numpy Ops**: Range calculations, distributions, and category choices execute in vectorized C-extension code.
- **1M Benchmark Passed**: 1 Million records generated and edge-case injected efficiently.