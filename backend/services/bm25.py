import math
import re
import unicodedata

def _normalize_and_tokenize(text: str) -> list[str]:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("đ", "d")
    words = re.findall(r"\b\w+\b", text)
    return words

class BM25:
    def __init__(self, corpus: list[dict], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.corpus_size = len(corpus)
        
        self.doc_tokens = [_normalize_and_tokenize(str(doc.get("text", ""))) for doc in corpus]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 0
        
        self.df = {}
        for tokens in self.doc_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1
                
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

        self.doc_tfs = []
        for tokens in self.doc_tokens:
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.doc_tfs.append(tf)

    def score(self, query: str) -> list[tuple[dict, float]]:
        query_tokens = _normalize_and_tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            doc_len = self.doc_lens[idx]
            tf = self.doc_tfs[idx]

            score = 0.0
            for term in query_tokens:
                if term not in self.idf:
                    continue
                term_tf = tf.get(term, 0)
                numerator = term_tf * (self.k1 + 1)
                denominator = term_tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += self.idf[term] * (numerator / denominator)
                
            scores.append((doc, score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
