| Cấu hình | HitRate@1 | HitRate@3 | HitRate@5 | HitRate@10 | Recall@10 | MRR@10 | Precision@3 | nDCG@10 | Latency mean/median/p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|
| Dense (vector only) | 26.0% | 36.0% (95% CI 24-50%) | 42.0% | 54.0% | 32.3% | 0.333 | 0.253 | 0.378 | 42 / 36 / 77 |
| Hybrid (vector + BM25 + RRF) | 36.0% | 66.0% (95% CI 52-78%) | 80.0% | 94.0% | 66.1% | 0.555 | 0.453 | 0.639 | 51 / 46 / 116 |
| Hybrid + Reranker | 70.0% | 84.0% (95% CI 72-92%) | 84.0% | 94.0% | 66.1% | 0.777 | 0.453 | 0.797 | 583 / 559 / 793 |
| Hybrid + Reranker + Multi-Query | 66.0% | 78.0% (95% CI 65-87%) | 80.0% | 84.0% | 60.1% | 0.726 | 0.440 | 0.736 | 6880 / 6646 / 9816 |
| Hybrid + Reranker + Query Decomposition | 70.0% | 84.0% (95% CI 72-92%) | 84.0% | 94.0% | 65.7% | 0.777 | 0.447 | 0.799 | 3441 / 2577 / 6831 |
| Hybrid + Reranker + On-demand routing (auto QD + auto MQ) | 70.0% | 84.0% (95% CI 72-92%) | 86.0% | 90.0% | 64.5% | 0.773 | 0.440 | 0.785 | 2997 / 591 / 8419 |

split=all. n = 50 of 50 questions have gold labels (metrics computed on the 50 with labels). Chunk size 700/overlap 100. Commit `78cb6bd`. Corpus: 2 document(s), 579 chunk(s). BM25 index build (one-off, excluded from latency): 210 ms.