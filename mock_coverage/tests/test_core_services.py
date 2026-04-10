
from mock_coverage.services.CodeStaticAnalyzer import CodeStaticAnalyzer
from mock_coverage.services.HybridRetriever import HybridRetriever
from mock_coverage.services.UnifiedLLMService import UnifiedLLMService
from mock_coverage.services.KnowledgeGraph import KnowledgeGraphService

def test_ast_analyzer():
    analyzer = CodeStaticAnalyzer()
    assert analyzer.analyze_syntax("print('test')")['status'] == "success"
    assert analyzer.analyze_syntax("import os")['status'] == "danger"
    assert analyzer.analyze_syntax("while True: pass")['status'] == "warning"

def test_retriever():
    retriever = HybridRetriever()
    assert retriever.search("") == []
    assert len(retriever.search("what is vue?")) == 2
    assert retriever.reciprocal_rank_fusion([], []) == []
    assert len(retriever.reciprocal_rank_fusion([1], [2])) == 2

def test_llm():
    llm = UnifiedLLMService()
    assert llm.generate_response("test") == "Streaming chunks..."
    assert "Token limit" in llm.generate_response("A" * 16001)
    assert "Timeout" in llm.generate_response("test", timeout=-1)

def test_kg():
    kg = KnowledgeGraphService()
    assert kg.create_entity("") == False
    assert kg.create_entity("conflict") == "merged"
    assert kg.create_entity("Vue3") == True
