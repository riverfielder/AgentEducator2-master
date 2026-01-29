<template>
  <div>
    <!-- 课程选择区域 -->
    <v-row>
      <v-col cols="12" md="3">
        <v-select
          v-model="selectedCourse"
          :items="courseOptions"
          item-title="name"
          item-value="id"
          label="选择课程"
          variant="outlined"
          density="comfortable"
          hide-details
          class="rounded-lg"
        >
          <template v-slot:prepend>
            <v-icon color="#6f23d1">mdi-book-open-variant</v-icon>
          </template>
        </v-select>
      </v-col>
    </v-row>

    <!-- 课程详情展示区域 -->
    <v-card v-if="courseDetail" class="mb-4 pa-4">
      <div class="text-h6 mb-2">{{ courseDetail.name }}</div>
      <div class="mb-2">{{ parsedCourseDescription }}</div>
      <div class="mb-2">授课人：{{ courseDetail.teacherInfo?.name || '未知' }}</div>
      <div class="mb-2">学时：{{ courseDetail.hours || '-' }}</div>
      <div class="mb-2">学期：{{ courseDetail.semester || '-' }}</div>
    </v-card>

    <!-- 新增：知识点列表标题 -->
    <div v-if="selectedCourse">
      <div class="text-h5 font-weight-bold mb-4" style="color:#6f23d1;">知识点列表</div>
      <v-row>
        <!-- 左侧知识节点树 -->
        <v-col cols="12" md="10">
          <v-data-table
            :headers="tableHeaders"
            :items="filteredKnowledgeTree"
            item-key="id"
            show-expand
            class="elevation-1"
            :expanded.sync="expandedNodes"
            :page.sync="pagination.page"
            :items-per-page="pagination.itemsPerPage"
            :items-per-page-options="pagination.itemsPerPageOptions"
            :show-first-last-page="pagination.showFirstLastPage"
            :prev-icon="pagination.prevIcon"
            :next-icon="pagination.nextIcon"
            :first-icon="pagination.firstIcon"
            :last-icon="pagination.lastIcon"
            :page-text="pagination.pageText"
            items-per-page-text="每页条数："
            @update:expanded="onExpandedChange"
          >
            <template #data-table-expand="{ item, isExpanded, toggleExpand }">
              <span
                @click.stop="toggleExpand()"
                style="cursor:pointer;display:inline-flex;align-items:center;"
              >
                <v-icon>
                  {{ isExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                </v-icon>
              </span>
            </template>

            <template #item.name="{ item }">
              <span>{{ item.name }}</span>
            </template>

            <template #item.category="{ item }">
              <span>{{ categoryMap[item.category] || item.category }}</span>
            </template>

            <template #item.description="{ item }">
              <span>{{ item.description || '-' }}</span>
            </template>

            <template #item.actions="{ item }">
              <v-btn
                v-if="shouldShowTeacherButton"
                color="primary"
                size="small"
                variant="outlined"
                prepend-icon="mdi-chart-line"
                @click="goToTeacherDetail(item.id)"
              >
                详情
              </v-btn>
            </template>

           <template #expanded-row="{ item }">
  <div>
    <!-- 一级知识点的展示方式 -->
    <div v-if="categoryMap[item.category] === '一级知识点'">
      <div v-if="getRelationGroups(item).contains.length">
        <strong>包含的二级知识点：</strong>
        <v-list dense>
          <v-list-item 
            v-for="child in getRelationGroups(item).contains" 
            :key="child.id"
          >
            <v-list-item-title>{{ child.name }}</v-list-item-title>
            <v-list-item-subtitle>
              描述：{{ child.description || '-' }}
              <span v-if="child.relationDesc">（{{ child.relationDesc }}）</span>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </div>
      
      <div v-if="getRelationGroups(item).related.length">
        <strong>相关知识点：</strong>
        <v-list dense>
          <v-list-item 
            v-for="child in getRelationGroups(item).related" 
            :key="child.id"
          >
            <v-list-item-title>{{ child.name }}</v-list-item-title>
            <v-list-item-subtitle>
              描述：{{ child.description || '-' }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </div>
    </div>
    
    <!-- 二级知识点的展示方式 -->
    <div v-else-if="categoryMap[item.category] === '二级知识点'">
      <div v-if="getRelationGroups(item).contains.length">
        <strong>包含的三级知识点：</strong>
        <v-list dense>
          <v-list-item 
            v-for="child in getRelationGroups(item).contains" 
            :key="child.id"
          >
            <v-list-item-title>{{ child.name }}</v-list-item-title>
            <v-list-item-subtitle>
              描述：{{ child.description || '-' }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </div>
    </div>
    
    <!-- 默认展示方式 -->
    <div v-else>
      <!-- 保留原有的关系展示逻辑 -->
      <div v-if="getRelationGroups(item).prerequisite.length">
        <strong>前置关系：</strong>
        <v-list dense>
          <v-list-item 
            v-for="child in getRelationGroups(item).prerequisite" 
            :key="child.id"
          >
            <v-list-item-title>{{ child.name }}</v-list-item-title>
            <v-list-item-subtitle>
              描述：{{ child.description || '-' }}
              <span v-if="child.relationDesc">（{{ child.relationDesc }}）</span>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </div>
      
      <!-- 其他关系展示... -->
    </div>
    
    <!-- 新增：关联文档展示 -->
    <div v-if="item.documentIds && item.documentIds.length">
      <strong>关联文档：</strong>
      <v-list dense>
        <v-list-item 
          v-for="doc in item.documentIds" 
          :key="doc.id"
        >
          <v-list-item-title>{{ doc.title }}</v-list-item-title>
          <v-list-item-subtitle>
            类型：{{ doc.type || '-' }}
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </div>
    
    <div 
      v-if="!getRelationGroups(item).prerequisite.length && 
           !getRelationGroups(item).contains.length && 
           !getRelationGroups(item).related.length &&
           (!item.documentIds || !item.documentIds.length)" 
      class="text-grey"
    >
      无相关信息
    </div>
  </div>
</template>
          </v-data-table>
        </v-col>

        <!-- 右侧搜索栏 -->
        <v-col cols="12" md="2">
          <v-text-field
            v-model="searchKeyword"
            label="搜索知识节点"
            prepend-inner-icon="mdi-magnify"
            dense
            clearable
          />
          <!-- <v-switch
            v-model="debugMode"
            label="调试模式"
            color="primary"
          ></v-switch> -->
        </v-col>
      </v-row>
    </div>

    <!-- 未选课程提示 -->
    <div v-else class="text-center text-grey pa-8">
      <v-icon size="40" color="grey">mdi-information-outline</v-icon>
      <div class="mt-2">请先选择课程后再查看知识节点</div>
    </div>
  </div>
</template>

<script>
import courseService from '../api/courseService'
import knowledgeMapService from '../api/knowledgeMapService'
import { parseCourseDescription } from '../utils/courseUtils'
import { useRouter, useRoute } from 'vue-router'

export default {
  props: {
    isTeacher: {
      type: Boolean,
      default: false
    },
    courseId: {
      type: String,
      default: null
    }
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    return { router, route }
  },

  data() {
    return {
      selectedCourse: null,
      courseOptions: [],
      courseDetail: null,
      knowledgeNodes: [],
      knowledgeLinks: [],
      searchKeyword: '',
      expandedNodes: [],
      debugMode: false,
      categoryMap: {
        core_concept: '一级知识点',
        main_module: '二级知识点',
        specific_point: '三级知识点'
      },
      tableHeaders: [
        { title: '名称', key: 'name', align: 'start', sortable: true },
        { title: '类别', key: 'category', align: 'start', sortable: true },
        { title: '详情', key: 'description', align: 'start', sortable: false },
        { title: '', key: 'actions', align: 'center', sortable: false, width: '120px' }
      ],
      pagination: {
        page: 1,
        itemsPerPage: 10,
        itemsPerPageOptions: [10, 20, 50, 100],
        showFirstLastPage: true,
        prevIcon: 'mdi-chevron-left',
        nextIcon: 'mdi-chevron-right',
        firstIcon: 'mdi-page-first',
        lastIcon: 'mdi-page-last',
        pageText: '{0}-{1} 条，共 {2} 条',
      }
    }
  },

  computed: {
    // 判断是否应该显示教师详情按钮
    shouldShowTeacherButton() {
      // 只有在教师身份且不在学生端知识图谱页面时才显示
      return this.isTeacher 
    },
    
    filteredKnowledgeTree() {
      // 只展示未被其他节点包含的一级知识点
      let nodes = this.knowledgeNodes;
      // 找出所有被包含的一级知识点id（只要有任何节点通过包含关系指向该一级知识点，都不展示在主表格）
      const containedCoreIds = new Set(
        this.knowledgeLinks
          .filter(link => {
            // 只考虑包含关系
            if (!(link.type === 'contains' || link.type === '包含关系')) return false;
            const targetNode = nodes.find(n => String(n.id) === String(link.target));
            const targetCat = targetNode && (typeof targetNode.category === 'number'
              ? (['core_concept', 'main_module', 'specific_point'][targetNode.category] || targetNode.category)
              : targetNode.category);
            return this.categoryMap[targetCat] === '一级知识点';
          })
          .map(link => String(link.target))
      );
      // 只保留未被包含的一级知识点
      let coreNodes = nodes.filter(n => {
        const category = typeof n.category === 'number'
          ? (['core_concept', 'main_module', 'specific_point'][n.category] || n.category)
          : n.category;
        return this.categoryMap[category] === '一级知识点' && !containedCoreIds.has(String(n.id));
      });
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase();
        coreNodes = coreNodes.filter(n =>
          n.name.toLowerCase().includes(keyword) ||
          (n.description && n.description.toLowerCase().includes(keyword))
        );
      }
      // 增加 canExpand 字段，只有有包含关系指向下级才可展开
      return coreNodes.map(n => {
        const hasContains = this.knowledgeLinks.some(link =>
          (link.type === 'contains' || link.type === '包含关系') && String(link.source) === String(n.id)
        );
        return {
          ...n,
          id: String(n.id),
          category: typeof n.category === 'number'
            ? (['core_concept', 'main_module', 'specific_point'][n.category] || n.category)
            : n.category,
          canExpand: hasContains
        };
      });
    },
    parsedCourseDescription() {
      const desc = this.courseDetail && this.courseDetail.description;
      const descObj = parseCourseDescription(desc);
      return descObj.description || desc;
    }
  },

  watch: {
    selectedCourse(newVal) {
      if (newVal && newVal !== 'all') {
        this.fetchCourseDetail(newVal)
        this.fetchKnowledgeNodes(newVal)
      } else if (newVal === 'all') {
        this.courseDetail = null
        this.fetchAllKnowledgeNodes()
      } else {
        this.courseDetail = null
        this.knowledgeNodes = []
        this.knowledgeLinks = []
      }
    }
  },

  methods: {
    async fetchCourses() {
      try {
        const res = await courseService.getCourses()
        if (res.data.code === 200) {
          this.courseOptions = res.data.data.list.map(course => ({
            id: course.id,
            name: course.name
          }))
          // 如果有传入的 courseId，则设置为默认选中的课程
          if (this.courseId) {
            this.selectedCourse = this.courseId
          }
        }
      } catch (error) {
        console.error('获取课程列表失败:', error)
      }
    },

    async fetchCourseDetail(courseId) {
      try {
        const res = await courseService.getCourseDetails(courseId)
        if (res.data.code === 200) {
          this.courseDetail = res.data.data
        }
      } catch (error) {
        console.error('获取课程详情失败:', error)
      }
    },

    async fetchKnowledgeNodes(courseId) {
      try {
        const res = await knowledgeMapService.getCourseKnowledgeGraph(courseId)
        if (res.data.code === 200 && res.data.data) {
          this.processGraphData(res.data.data)
        }
      } catch (error) {
        console.error('获取知识节点失败:', error)
        this.knowledgeNodes = []
        this.knowledgeLinks = []
      }
    },

    async fetchAllKnowledgeNodes() {
      try {
        const allData = await Promise.all(
          this.courseOptions.map(course => 
            knowledgeMapService.getCourseKnowledgeGraph(course.id)
          )
        )
        
        const combined = {
          nodes: [],
          links: []
        }
        
        allData.forEach(res => {
          if (res.data.code === 200 && res.data.data) {
            combined.nodes.push(...res.data.data.nodes || [])
            combined.links.push(...res.data.data.links || [])
          }
        })
        
        this.processGraphData(combined)
      } catch (error) {
        console.error('获取全部知识节点失败:', error)
        this.knowledgeNodes = []
        this.knowledgeLinks = []
      }
    },

    processGraphData(graphData) {
      // 处理节点
      const nodes = (graphData.nodes || []).map(n => { 
        let desc = n.description;
        // 尝试解析description为json
        const descObj = parseCourseDescription(desc);
        desc = descObj.description || desc;
        return {
          ...n, 
          id: String(n.id),
          description: desc
        }
      })
      
      // 处理边
      const links = (graphData.links || []).map(l => ({
        ...l,
        source: String(l.source),
        target: String(l.target)
      }))
      
      // 自动补全缺失的节点
      const nodeIdSet = new Set(nodes.map(n => n.id))
      links.forEach(link => {
        if (!nodeIdSet.has(link.source)) {
          nodes.push({ id: link.source, name: '未知节点', description: '' })
          nodeIdSet.add(link.source)
        }
        if (!nodeIdSet.has(link.target)) {
          nodes.push({ id: link.target, name: '未知节点', description: '' })
          nodeIdSet.add(link.target)
        }
      })
      
      this.knowledgeNodes = nodes
      this.knowledgeLinks = links
      
      console.log('处理后的图数据:', {
        nodes: this.knowledgeNodes,
        links: this.knowledgeLinks
      })
    },

    getRelatedLinks(nodeId) {
      const id = String(nodeId)
      return this.knowledgeLinks.filter(link => 
        String(link.source) === id || String(link.target) === id
      )
    },

    getRelationGroups(item) {
  const id = String(item.id);
  const groups = {
    prerequisite: [],
    contains: [],
    related: []
  };

  // 获取当前节点的类别
  const currentCategory = this.categoryMap[item.category] || item.category;

  this.knowledgeLinks.forEach(link => {
    // 只处理当前节点作为source的边
    if (String(link.source) !== id) return;

    const targetNode = this.knowledgeNodes.find(n => String(n.id) === String(link.target)) || {
      id: String(link.target),
      name: '未知节点',
      description: ''
    };

    const targetCategory = this.categoryMap[targetNode.category] || targetNode.category;

    // 排除下级为一级知识点的节点
    if (targetCategory === '一级知识点') return;

    // 按照层级关系智能分类
    if (currentCategory === '一级知识点' && targetCategory === '二级知识点') {
      groups.contains.push({
        ...targetNode,
        relationDesc: '属于一级知识点下的二级知识点'
      });
    } 
    else if (currentCategory === '二级知识点' && targetCategory === '三级知识点') {
      groups.contains.push({
        ...targetNode,
        relationDesc: '属于二级知识点下的三级知识点'
      });
    }
    else if (currentCategory === '一级知识点' && targetCategory === '三级知识点') {
      groups.related.push({
        ...targetNode,
        relationDesc: '与一级知识点直接相关的知识点'
      });
    }
    else {
      // 保留原始关系类型的处理
      const type = String(link.type || link.relation_type || link.relationType || '')
        .toLowerCase()
        .replace(/_/g, '');
      
      if (type.includes('prerequisite') || type.includes('前置')) {
        groups.prerequisite.push({
          ...targetNode,
          relationDesc: link.description || link.relation_desc || ''
        });
      } 
      else if (type.includes('contains') || type.includes('包含')) {
        groups.contains.push({
          ...targetNode,
          relationDesc: link.description || link.relation_desc || ''
        });
      } 
      else if (type.includes('related') || type.includes('相关')) {
        groups.related.push({
          ...targetNode,
          relationDesc: link.description || link.relation_desc || ''
        });
      }
    }
  });

  // 对包含关系按类别排序：二级知识点优先，然后是三级知识点
  groups.contains.sort((a, b) => {
    const categoryOrder = {
      '二级知识点': 1,
      '三级知识点': 2
    };
    const aCat = this.categoryMap[a.category] || a.category;
    const bCat = this.categoryMap[b.category] || b.category;
    return (categoryOrder[aCat] || 3) - (categoryOrder[bCat] || 3);
  });

  return groups;
},

    onExpandedChange(expanded) {
      this.expandedNodes = expanded.map(id => String(id))
      if (this.expandedNodes.length) {
        const lastId = this.expandedNodes[this.expandedNodes.length - 1]
        const item = this.knowledgeNodes.find(n => String(n.id) === lastId)
        if (item) {
          console.log('当前展开节点关系:', {
            node: item,
            relations: this.getRelationGroups(item)
          })
        }
      }
    },

    goToTeacherDetail(keywordId) {
      this.router.push({
        name: 'TeacherKnowledgeDetail',
        params: { id: keywordId }
      })
    }
  },

  mounted() {
    this.fetchCourses()
  }
}
</script>

<style scoped>
.debug-info {
  background-color: #f5f5f5;
  padding: 8px;
  margin-bottom: 12px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}
/* 展开区域样式 */
.expanded-content {
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* 关系标题样式 */
.relation-title {
  font-weight: 600;
  color: #6f23d1;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #e0e0e0;
}

/* 列表项样式 */
.relation-item {
  transition: background-color 0.3s;
  border-radius: 4px;
}

.relation-item:hover {
  background-color: #f0f2f5;
}

/* 空状态提示 */
.empty-hint {
  color: #9e9e9e;
  font-style: italic;
  padding: 8px 0;
}
</style>