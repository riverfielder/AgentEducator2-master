
class KnowledgeGraphService:
    def create_entity(self, entity_name):
        if not entity_name:
            return False
        if entity_name == "conflict":
            # 模拟冲突合并
            return "merged"
        return True
