| Cấu hình | HitRate@1 | HitRate@3 | HitRate@5 | HitRate@10 | Recall@10 | MRR@10 | Precision@3 | nDCG@10 | Latency mean/median/p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|
| Hybrid + Reranker | 72.5% | 87.5% (95% CI 74-94%) | 87.5% | 95.0% | 65.9% | 0.807 | 0.475 | 0.828 | 665 / 662 / 819 |
| Hybrid + Reranker + Multi-Query | 65.0% | 77.5% (95% CI 62-88%) | 80.0% | 82.5% | 55.6% | 0.721 | 0.442 | 0.738 | 7143 / 7205 / 10069 |

split=dev. n = 40 of 40 questions have gold labels (metrics computed on the 40 with labels). Chunk size 700/overlap 100. Commit `0cc1baa`. Corpus: 2 document(s), 579 chunk(s). BM25 index build (one-off, excluded from latency): 106 ms.