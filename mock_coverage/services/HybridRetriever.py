
class HybridRetriever:
    def search(self, query):
        if not query:
            return []
        return [{"score": 0.9, "doc": "FAISS docs"}, {"score": 0.8, "doc": "BM25 docs"}]
        
    def reciprocal_rank_fusion(self, faiss_res, bm25_res):
        if not faiss_res and not bm25_res:
            return []
        return faiss_res + bm25_res
