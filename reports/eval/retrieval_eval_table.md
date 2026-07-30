| Cấu hình | HitRate@1 | HitRate@3 | HitRate@5 | HitRate@10 | Recall@10 | MRR@10 | Precision@3 | nDCG@10 | Latency mean/median/p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|
| Dense (vector only) | 45.0% | 50.0% (95% CI 30-70%) | 60.0% | 70.0% | 12.2% | 0.501 | 0.433 | 0.518 | 28 / 25 / 44 |
| Hybrid (vector + BM25 + RRF) | 50.0% | 75.0% (95% CI 53-89%) | 85.0% | 90.0% | 18.9% | 0.644 | 0.650 | 0.657 | 29 / 28 / 44 |
| Hybrid + Reranker | 65.0% | 75.0% (95% CI 53-89%) | 75.0% | 90.0% | 18.9% | 0.714 | 0.650 | 0.717 | 661 / 534 / 1263 |
| Hybrid + Reranker + Multi-Query | 65.0% | 75.0% (95% CI 53-89%) | 80.0% | 85.0% | 21.2% | 0.711 | 0.650 | 0.731 | 6627 / 6317 / 9257 |

n = 20 of 20 questions have gold labels (metrics computed on the 20 with labels). Chunk size 700/overlap 100. Commit `7cebd8f`. Corpus: 1 document(s), 472 chunk(s). BM25 index build (one-off, excluded from latency): 149 ms.