# Performance Test Report

**Timestamp:** 2025-10-01 08:25:09  
**Status:** ❌ FAILED  
**Target:** http://httpbin.org/get  
**Duration:** 5s  
**Concurrency:** 3  

## Test Results

| Metric | Value | Unit |
|--------|-------|------|
| Total Requests | 10 | requests |
| Duration | 10.5 | seconds |
| Throughput | 1.0 | req/sec |
| Error Rate | 100.00 | % |
| P50 Latency | 1694.0 | ms |
| P95 Latency | 5566.5 | ms |
| P99 Latency | 5566.5 | ms |
| CPU Usage | 6.6 | % |

## ❌ SLO Violations

- P50 latency 1694.0ms exceeds threshold 100ms
- P95 latency 5566.5ms exceeds threshold 250ms
- P99 latency 5566.5ms exceeds threshold 400ms
- Error rate 100.00% exceeds threshold 0.5%
- Throughput 1.0 req/sec below threshold 1000 req/sec
