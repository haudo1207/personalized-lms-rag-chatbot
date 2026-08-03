
=== Percentile sweep vs baselines (đúng 20 câu hỏi gốc) ===

| Cấu hình | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR | nDCG |
|---|---|---|---|---|---|---|
| Fixed-size (baseline gốc) | 70% | 80% | 85% | 90% | 0.760 | 0.734 |
| Semantic + regex tách câu | 65% | 75% | 75% | 90% | 0.714 | 0.717 |
| Semantic + underthesea, percentile=95 (trước sweep) | 60% | 70% | 75% | 90% | 0.675 | 0.708 |
| Semantic + underthesea, percentile=70.0 | 65% | 75% | 75% | 90% | 0.715 | 0.725 |
| Semantic + underthesea, percentile=80.0 | 65% | 75% | 75% | 90% | 0.721 | 0.709 |
| Semantic + underthesea, percentile=85.0 | 65% | 75% | 75% | 90% | 0.722 | 0.718 |
| Semantic + underthesea, percentile=90.0 | 60% | 75% | 75% | 90% | 0.688 | 0.720 |
| Semantic + underthesea, percentile=95.0 | 60% | 70% | 75% | 90% | 0.675 | 0.708 |