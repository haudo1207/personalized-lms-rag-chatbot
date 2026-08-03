
=== Overlap sentences sweep vs baselines (percentile=85, đúng 20 câu hỏi gốc) ===

| Cấu hình | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR | nDCG |
|---|---|---|---|---|---|---|
| Fixed-size (baseline gốc) | 70% | 80% | 85% | 90% | 0.760 | 0.734 |
| Semantic p=85, overlap=0 (trước sweep) | 65% | 75% | 75% | 90% | 0.722 | 0.718 |
| Semantic p=85, overlap_sentences=0 | 65% | 75% | 75% | 90% | 0.722 | 0.718 |
| Semantic p=85, overlap_sentences=1 | 60% | 70% | 75% | 90% | 0.676 | 0.693 |
| Semantic p=85, overlap_sentences=2 | 50% | 75% | 75% | 90% | 0.623 | 0.672 |
| Semantic p=85, overlap_sentences=3 | 60% | 70% | 75% | 85% | 0.661 | 0.681 |