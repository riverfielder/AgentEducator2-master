# 知识点掌握度计算优化方案

## 问题背景

原有的 `statistics.py` 中的 `get_course_knowledge_mastery` 接口存在性能问题：
- 使用双重循环：外层遍历知识点，内层遍历学生
- 每次调用 `calculate_mastery_level` 都会创建新的数据库会话
- 没有充分利用批量查询和缓存机制
- 时间复杂度为 O(n*m)，其中 n 为知识点数量，m 为学生数量

## 优化方案

### 1. 新增批量计算方法

在 `MasteryCalculator` 类中新增了 `batch_calculate_course_mastery` 方法：

```python
def batch_calculate_course_mastery(self, student_ids: List[str], keyword_ids: List[str], 
                                  force_recalculate: bool = False) -> Dict[str, Dict[str, Dict]]:
```

**核心优化点：**
- **批量数据库查询**：一次性查询所有学生和知识点的现有掌握度记录
- **智能缓存利用**：优先使用缓存中的新鲜数据，减少重复计算
- **依赖图复用**：知识点依赖图只构建一次，所有学生共享
- **批量处理**：对每个学生使用现有的 `batch_calculate_mastery` 方法

### 2. 优化 statistics.py 接口

修改了 `get_course_knowledge_mastery` 接口的实现：

**原有逻辑：**
```python
for keyword_id in course_keyword_ids:
    for student_id in student_ids:
        mastery_data = mastery_calculator.calculate_mastery_level(...)
```

**优化后逻辑：**
```python
# 一次性批量计算所有学生对所有知识点的掌握度
batch_results = mastery_calculator.batch_calculate_course_mastery(
    student_ids=student_ids_str,
    keyword_ids=course_keyword_ids_str,
    force_recalculate=False
)

# 处理批量结果，计算统计信息
for keyword_id in course_keyword_ids:
    # 从批量结果中提取数据
```

### 3. 容错机制

添加了完善的容错机制：
- 如果批量计算失败，自动回退到原有的逐个计算方法
- 保证接口的稳定性和可靠性

## 性能提升

### 时间复杂度优化
- **原有**：O(n*m) - 每个知识点每个学生都需要单独计算
- **优化后**：O(n+m) - 批量查询 + 批量计算

### 数据库查询优化
- **原有**：最多 n*m 次数据库查询
- **优化后**：1次批量查询现有记录 + 必要的计算查询

### 缓存利用率提升
- 批量检查缓存状态，避免重复计算已缓存的数据
- 使用扩展缓存策略，延长批量计算结果的缓存时间

## 使用示例

### 直接使用批量计算方法

```python
from services.mastery_calculator import MasteryCalculator

mastery_calculator = MasteryCalculator()

# 批量计算多个学生对多个知识点的掌握度
results = mastery_calculator.batch_calculate_course_mastery(
    student_ids=['student1', 'student2', 'student3'],
    keyword_ids=['keyword1', 'keyword2', 'keyword3'],
    force_recalculate=False
)

# 结果格式：{student_id: {keyword_id: mastery_data}}
for student_id, student_results in results.items():
    for keyword_id, mastery_data in student_results.items():
        mastery_level = mastery_data['mastery_level']
        print(f"学生 {student_id} 对知识点 {keyword_id} 的掌握度: {mastery_level}")
```

### 在统计接口中的应用

优化后的 `GET /api/statistics/knowledge-mastery/<course_id>` 接口：
- 自动使用批量计算方法
- 提供相同的返回格式
- 显著提升响应速度

## 兼容性

- 保持了原有接口的返回格式不变
- 新增的方法不影响现有功能
- 提供了完整的容错机制

## 监控和日志

新增了详细的日志记录：
- 批量计算的执行情况
- 缓存命中率统计
- 性能指标监控

```
[INFO] Batch course mastery calculation completed: students=50, keywords=20
[DEBUG] Calculated mastery for student student1: cached=15, calculated=5
```

## 后续优化建议

1. **Redis 缓存预热**：可以考虑在课程开始时预计算所有学生的掌握度
2. **异步计算**：对于大量学生的课程，可以考虑异步批量计算
3. **增量更新**：当学生有新的学习活动时，只更新相关的掌握度数据
4. **分页处理**：对于超大规模的课程，可以考虑分页批量处理

## 测试建议

建议在以下场景下测试优化效果：
- 小规模课程（10个学生，5个知识点）
- 中等规模课程（50个学生，20个知识点）
- 大规模课程（200个学生，50个知识点）

通过对比优化前后的响应时间和数据库查询次数来验证优化效果。