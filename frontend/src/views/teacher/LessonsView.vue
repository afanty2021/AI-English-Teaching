<template>
  <div class="lessons-page">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>教案管理</h1>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索教案..."
              :prefix-icon="Search"
              clearable
              style="width: 250px"
              @input="handleSearch"
            />
            <el-select v-model="filterLevel" placeholder="筛选难度" clearable style="width: 120px" @change="loadLessons">
              <el-option label="A1" value="A1" />
              <el-option label="A2" value="A2" />
              <el-option label="B1" value="B1" />
              <el-option label="B2" value="B2" />
              <el-option label="C1" value="C1" />
              <el-option label="C2" value="C2" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="goToAIPlanning">AI 生成教案</el-button>
          </div>
        </div>
      </el-header>

      <el-main>
        <!-- 教案列表 -->
        <el-card v-loading="isLoading">
          <el-empty v-if="!isLoading && filteredLessons.length === 0" description="暂无教案">
            <el-button type="primary" @click="goToAIPlanning">使用 AI 生成第一个教案</el-button>
          </el-empty>

          <div v-else class="lessons-grid">
            <div
              v-for="lesson in filteredLessons"
              :key="lesson.id"
              class="lesson-card"
              @click="viewLesson(lesson.id)"
            >
              <div class="card-header">
                <div class="lesson-info">
                  <h3 class="lesson-title">{{ lesson.title }}</h3>
                  <div class="lesson-meta">
                    <el-tag size="small" :type="getLevelType(lesson.level)">{{ lesson.level }}</el-tag>
                    <span class="lesson-duration">{{ lesson.duration }} 分钟</span>
                  </div>
                </div>
                <el-dropdown @command="(cmd: string) => handleAction(cmd, lesson)" @click.stop>
                  <el-button circle :icon="MoreFilled" />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit" :icon="Edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="duplicate" :icon="CopyDocument">复制</el-dropdown-item>
                      <el-dropdown-item command="export" :icon="Download">导出</el-dropdown-item>
                      <el-dropdown-item divided command="delete" :icon="Delete">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <div class="card-body">
                <div class="lesson-topic">
                  <el-icon><Document /></el-icon>
                  <span>{{ lesson.topic || '未设置主题' }}</span>
                </div>

                <div class="lesson-preview">
                  <div class="preview-item">
                    <el-icon><Aim /></el-icon>
                    <span>目标: {{ getObjectivesSummary(lesson) }}</span>
                  </div>
                  <div class="preview-item">
                    <el-icon><Clock /></el-icon>
                    <span>{{ lesson.structure?.length || 0 }} 个环节</span>
                  </div>
                  <div class="preview-item">
                    <el-icon><CollectionTag /></el-icon>
                    <span>{{ getVocabularyCount(lesson) }} 个词汇</span>
                  </div>
                </div>

                <div class="card-footer">
                  <span class="lesson-date">{{ formatDate(lesson.created_at) }}</span>
                  <el-tag size="small" :type="getStatusType(lesson.status)">
                    {{ getStatusText(lesson.status) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>

    <!-- 教案详情抽屉 -->
    <el-drawer
      v-model="showDetailDrawer"
      :title="currentLesson?.title || '教案详情'"
      direction="rtl"
      size="70%"
      @close="handleDrawerClose"
    >
      <div v-if="currentLesson" class="lesson-detail-content">
        <!-- 操作栏 -->
        <div class="detail-actions">
          <el-button :icon="Edit" @click="editLesson">编辑</el-button>
          <!-- TODO: duplicate feature not implemented yet -->
          <!-- <el-button :icon="CopyDocument" @click="duplicateLesson">复制</el-button> -->
          <el-dropdown @command="handleExport" style="display: inline-block">
            <el-button :icon="Download">
              导出 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="word">
                  <el-icon><Document /></el-icon>
                  导出为 Word
                </el-dropdown-item>
                <el-dropdown-item command="pdf">
                  <el-icon><Tickets /></el-icon>
                  导出为 PDF
                </el-dropdown-item>
                <el-dropdown-item command="markdown">
                  <el-icon><DocumentCopy /></el-icon>
                  导出为 Markdown
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button :icon="Delete" type="danger" @click="deleteLesson">删除</el-button>
        </div>

        <!-- 教案内容标签页 -->
        <el-tabs v-model="activeTab" class="lesson-tabs">
          <!-- 概览 -->
          <el-tab-pane label="概览" name="overview">
            <div class="tab-content">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="标题">{{ currentLesson.title }}</el-descriptions-item>
                <el-descriptions-item label="主题">{{ currentLesson.topic }}</el-descriptions-item>
                <el-descriptions-item label="难度">
                  <el-tag :type="getLevelType(currentLesson.level)">{{ currentLesson.level }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="时长">{{ currentLesson.duration }} 分钟</el-descriptions-item>
                <el-descriptions-item label="学生人数">{{ currentLesson.student_count || '未设置' }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ formatDateTime(currentLesson.created_at) }}</el-descriptions-item>
                <el-descriptions-item label="更新时间">{{ formatDateTime(currentLesson.updated_at) }}</el-descriptions-item>
                <el-descriptions-item label="状态" :span="2">
                  <el-tag :type="getStatusType(currentLesson.status)">{{ getStatusText(currentLesson.status) }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>

              <!-- 教学重点 -->
              <div v-if="currentLesson.focus_areas?.length" class="section">
                <h4>教学重点</h4>
                <div class="tags-list">
                  <el-tag
                    v-for="area in currentLesson.focus_areas"
                    :key="area"
                    type="info"
                  >
                    {{ getFocusAreaName(area) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 教学目标 -->
          <el-tab-pane label="教学目标" name="objectives">
            <div class="tab-content">
              <div v-if="currentLesson.objectives">
                <div v-if="currentLesson.objectives.language_knowledge?.length" class="objectives-section">
                  <h4>语言知识</h4>
                  <ul class="objectives-list">
                    <li v-for="(obj, i) in currentLesson.objectives.language_knowledge" :key="i">{{ obj }}</li>
                  </ul>
                </div>

                <div v-if="currentLesson.objectives.language_skills" class="objectives-section">
                  <h4>语言技能</h4>
                  <div v-for="(skills, type) in currentLesson.objectives.language_skills" :key="type" class="skills-group">
                    <div class="skill-type">
                      <span class="skill-label">{{ getSkillTypeName(type) }}:</span>
                      <span class="skill-items">{{ skills.join('、') }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无教学目标数据" />
            </div>
          </el-tab-pane>

          <!-- 核心词汇 -->
          <el-tab-pane label="核心词汇" name="vocabulary">
            <div class="tab-content">
              <div v-if="hasVocabulary(currentLesson)">
                <!-- 名词 -->
                <div v-if="currentLesson.vocabulary?.noun?.length" class="vocab-section">
                  <h4>名词</h4>
                  <el-table :data="currentLesson.vocabulary.noun" size="small">
                    <el-table-column prop="word" label="单词" width="150" />
                    <el-table-column prop="meaning_cn" label="中文含义" />
                    <el-table-column prop="pronunciation" label="发音" />
                    <el-table-column prop="example" label="例句" />
                  </el-table>
                </div>

                <!-- 动词 -->
                <div v-if="currentLesson.vocabulary?.verb?.length" class="vocab-section">
                  <h4>动词</h4>
                  <el-table :data="currentLesson.vocabulary.verb" size="small">
                    <el-table-column prop="word" label="单词" width="150" />
                    <el-table-column prop="meaning_cn" label="中文含义" />
                    <el-table-column prop="pronunciation" label="发音" />
                    <el-table-column prop="example" label="例句" />
                  </el-table>
                </div>

                <!-- 其他词性 -->
                <div v-if="currentLesson.vocabulary?.adjective?.length" class="vocab-section">
                  <h4>形容词</h4>
                  <el-table :data="currentLesson.vocabulary.adjective" size="small">
                    <el-table-column prop="word" label="单词" width="150" />
                    <el-table-column prop="meaning_cn" label="中文含义" />
                    <el-table-column prop="pronunciation" label="发音" />
                    <el-table-column prop="example" label="例句" />
                  </el-table>
                </div>
              </div>
              <el-empty v-else description="暂无词汇数据" />
            </div>
          </el-tab-pane>

          <!-- 语法点 -->
          <el-tab-pane label="语法点" name="grammar">
            <div class="tab-content">
              <div v-if="currentLesson.grammar_points?.length">
                <div
                  v-for="(gp, index) in currentLesson.grammar_points"
                  :key="index"
                  class="grammar-card"
                >
                  <h4>{{ gp.name }}</h4>
                  <p class="grammar-description">{{ gp.description }}</p>
                  <div v-if="gp.rule" class="grammar-rule">
                    <strong>规则：</strong>{{ gp.rule }}
                  </div>
                  <div v-if="gp.examples?.length" class="grammar-examples">
                    <strong>例句：</strong>
                    <ul>
                      <li v-for="(ex, i) in gp.examples" :key="i">{{ ex }}</li>
                    </ul>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无语法点数据" />
            </div>
          </el-tab-pane>

          <!-- 教学流程 -->
          <el-tab-pane label="教学流程" name="structure">
            <div class="tab-content">
              <div v-if="currentLesson.structure?.length">
                <el-timeline class="lesson-timeline">
                  <el-timeline-item
                    v-for="(phase, index) in currentLesson.structure"
                    :key="index"
                    :timestamp="`${phase.duration || 0}分钟`"
                    :icon="getTimelineIcon(index)"
                    placement="top"
                  >
                    <div class="timeline-content">
                      <h4>{{ phase.title }}</h4>
                      <p v-if="phase.description" class="phase-description">{{ phase.description }}</p>

                      <!-- 活动 -->
                      <div v-if="phase.activities?.length" class="phase-activities">
                        <div
                          v-for="(activity, actIndex) in phase.activities"
                          :key="actIndex"
                          class="activity-item"
                        >
                          <el-icon><Operation /></el-icon>
                          <span>{{ activity }}</span>
                        </div>
                      </div>

                      <!-- 提示 -->
                      <div v-if="phase.tips?.length" class="phase-tips">
                        <div
                          v-for="(tip, tipIndex) in phase.tips"
                          :key="tipIndex"
                          class="tip-item"
                        >
                          <el-icon><InfoFilled /></el-icon>
                          <span>{{ tip }}</span>
                        </div>
                      </div>
                    </div>
                  </el-timeline-item>
                </el-timeline>
              </div>
              <el-empty v-else description="暂无教学流程数据" />
            </div>
          </el-tab-pane>

          <!-- 教学材料 -->
          <el-tab-pane label="教学材料" name="materials">
            <div class="tab-content">
              <div v-if="currentLesson.materials?.length">
                <div class="materials-grid">
                  <div
                    v-for="(material, index) in currentLesson.materials"
                    :key="index"
                    class="material-card"
                  >
                    <div class="material-icon">
                      <el-icon :size="32">
                        <component :is="getMaterialIcon(material.type)" />
                      </el-icon>
                    </div>
                    <h4>{{ material.title }}</h4>
                    <p class="material-desc">{{ material.description }}</p>
                    <el-button
                      type="primary"
                      link
                      :icon="Download"
                      @click="downloadMaterial(material)"
                    >
                      下载材料
                    </el-button>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无教学材料">
                <el-button type="primary" :icon="Plus">添加教学材料</el-button>
              </el-empty>
            </div>
          </el-tab-pane>

          <!-- 在线编辑 -->
          <el-tab-pane label="在线编辑" name="edit">
            <div class="tab-content edit-content">
              <div class="edit-toolbar">
                <el-button-group>
                  <el-tooltip content="加粗">
                    <el-button @click="execCommand('bold')">
                      <el-icon><Bold /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="斜体">
                    <el-button @click="execCommand('italic')">
                      <el-icon><Italic /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="下划线">
                    <el-button @click="execCommand('underline')">
                      <el-icon><Underline /></el-icon>
                    </el-button>
                  </el-tooltip>
                </el-button-group>

                <el-divider direction="vertical" />

                <el-button-group>
                  <el-tooltip content="无序列表">
                    <el-button @click="execCommand('insertUnorderedList')">
                      <el-icon><List /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="有序列表">
                    <el-button @click="execCommand('insertOrderedList')">
                      <el-icon><Menu /></el-icon>
                    </el-button>
                  </el-tooltip>
                </el-button-group>

                <el-divider direction="vertical" />

                <el-button-group>
                  <el-tooltip content="标题">
                    <el-button @click="execCommand('formatBlock', 'H1')">
                      <span style="font-size: 14px; font-weight: bold;">H1</span>
                    </el-button>
                  </el-tooltip>
                  <el-button @click="execCommand('formatBlock', 'H2')">
                    <span style="font-size: 14px; font-weight: bold;">H2</span>
                  </el-button>
                  <el-button @click="execCommand('formatBlock', 'H3')">
                    <span style="font-size: 14px; font-weight: bold;">H3</span>
                  </el-button>
                </el-button-group>

                <el-divider direction="vertical" />

                <el-tooltip content="清除格式">
                  <el-button @click="execCommand('removeFormat')">
                    <el-icon><RemoveFormat /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>

              <div
                ref="editorRef"
                class="rich-editor"
                contenteditable="true"
                @input="handleEditorInput"
              ></div>

              <div class="edit-footer">
                <el-button @click="resetEdit">重置</el-button>
                <el-button type="primary" @click="saveEdit" :loading="saving">保存修改</el-button>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>

    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出教案" width="500px">
      <el-form label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFormat">
            <el-radio label="word">Word 文档</el-radio>
            <el-radio label="pdf">PDF 文档</el-radio>
            <el-radio label="markdown">Markdown</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="包含内容">
          <el-checkbox-group v-model="exportSections">
            <el-checkbox label="overview">概览信息</el-checkbox>
            <el-checkbox label="objectives">教学目标</el-checkbox>
            <el-checkbox label="vocabulary">核心词汇</el-checkbox>
            <el-checkbox label="grammar">语法点</el-checkbox>
            <el-checkbox label="structure">教学流程</el-checkbox>
            <el-checkbox label="materials">教学材料</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="doExport" :loading="exporting">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  Plus,
  Edit,
  Delete,
  Download,
  CopyDocument,
  Document,
  Aim,
  Clock,
  CollectionTag,
  MoreFilled,
  ArrowDown,
  Tickets,
  DocumentCopy,
  Operation,
  InfoFilled,
  // Bold, // Not available in @element-plus/icons-vue
  // Italic, // Not available in @element-plus/icons-vue
  // Underline, // Not available in @element-plus/icons-vue
  List,
  Menu,
  // RemoveFormat, // Not available in @element-plus/icons-vue (use Remove or RemoveFilled instead)
  Remove,
  Picture,
  VideoCamera
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getLessonPlans,
  getLessonPlan,
  deleteLessonPlan,
  // duplicateLessonPlan, // TODO: not implemented in API
  updateLessonContent,
  exportLessonPlan,
  getExportUrl,
  exportToMarkdown as apiExportToMarkdown
} from '@/api/lesson'

// 类型定义
interface LessonPlan {
  id: string
  title: string
  topic: string
  level: string
  duration: number
  student_count?: number
  focus_areas?: string[]
  status: 'draft' | 'completed'
  objectives?: {
    language_knowledge?: string[]
    language_skills?: Record<string, string[]>
  }
  vocabulary?: {
    noun?: Array<{ word: string; meaning_cn: string; pronunciation?: string; example?: string }>
    verb?: Array<{ word: string; meaning_cn: string; pronunciation?: string; example?: string }>
    adjective?: Array<{ word: string; meaning_cn: string; pronunciation?: string; example?: string }>
  }
  grammar_points?: Array<{
    name: string
    description: string
    rule?: string
    examples?: string[]
  }>
  structure?: Array<{
    title: string
    duration?: number
    description?: string
    activities?: string[]
    tips?: string[]
  }>
  materials?: Array<{
    type: 'image' | 'video' | 'document' | 'audio'
    title: string
    description: string
    url: string
  }>
  created_at: string
  updated_at: string
}

const router = useRouter()

// 状态
const isLoading = ref(true)
const lessons = ref<LessonPlan[]>([])
const searchQuery = ref('')
const filterLevel = ref('')
const showDetailDrawer = ref(false)
const showExportDialog = ref(false)
const currentLesson = ref<LessonPlan | null>(null)
const activeTab = ref('overview')
const exportFormat = ref('word')
const exportSections = ref(['overview', 'objectives', 'vocabulary', 'grammar', 'structure'])
const exporting = ref(false)
const saving = ref(false)
const editorRef = ref<HTMLElement>()
const editorContent = ref('')

// 计算属性
const filteredLessons = computed(() => {
  let result = lessons.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(l =>
      l.title.toLowerCase().includes(query) ||
      l.topic?.toLowerCase().includes(query)
    )
  }

  if (filterLevel.value) {
    result = result.filter(l => l.level === filterLevel.value)
  }

  return result
})

// 方法
const loadLessons = async () => {
  isLoading.value = true
  try {
    const response = await getLessonPlans({
      page: 1,
      page_size: 100,
      level: filterLevel.value || undefined,
      status: undefined,
      search: searchQuery.value || undefined
    })
    // 将后端响应格式转换为组件使用的格式
    lessons.value = response.lesson_plans.map(plan => ({
      id: plan.id,
      title: plan.title,
      topic: plan.topic,
      level: plan.level,
      duration: plan.duration,
      status: plan.status as 'draft' | 'completed',
      created_at: plan.created_at,
      updated_at: plan.updated_at
    }))
  } catch (error) {
    console.error('加载教案失败:', error)
    ElMessage.error('加载教案失败')
  } finally {
    isLoading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

const viewLesson = async (lessonId: string) => {
  try {
    const response = await getLessonPlan(lessonId)
    // 转换后端响应格式为组件使用的格式
    currentLesson.value = convertToLessonPlan(response.lesson_plan)
    showDetailDrawer.value = true
  } catch (error) {
    console.error('加载教案详情失败:', error)
    ElMessage.error('加载教案详情失败')
  }
}

/**
 * 将后端教案详情转换为组件使用的格式
 */
const convertToLessonPlan = (detail: any): LessonPlan => {
  return {
    id: detail.id,
    title: detail.title,
    topic: detail.topic,
    level: detail.level,
    duration: detail.duration,
    status: detail.status as 'draft' | 'completed',
    objectives: detail.objectives,
    vocabulary: detail.vocabulary,
    grammar_points: detail.grammar_points,
    structure: convertStructureToArray(detail.structure),
    materials: detail.resources ? convertResourcesToMaterials(detail.resources) : undefined,
    created_at: detail.created_at,
    updated_at: detail.updated_at
  }
}

/**
 * 将后端结构格式转换为数组格式
 */
const convertStructureToArray = (structure: any): Array<{
  title: string
  duration?: number
  description?: string
  activities?: string[]
  tips?: string[]
}> => {
  const phases: any[] = []
  if (structure.warm_up) {
    phases.push({ ...structure.warm_up, duration: structure.warm_up.duration })
  }
  if (structure.presentation) {
    phases.push({ ...structure.presentation, duration: structure.presentation.duration })
  }
  structure.practice?.forEach((p: any) => {
    phases.push({ ...p, duration: p.duration })
  })
  if (structure.production) {
    phases.push({ ...structure.production, duration: structure.production.duration })
  }
  if (structure.summary) {
    phases.push({ ...structure.summary, duration: structure.summary.duration })
  }
  if (structure.homework) {
    phases.push({ ...structure.homework, duration: structure.homework.duration })
  }
  return phases
}

/**
 * 将资源转换为材料格式
 */
const convertResourcesToMaterials = (resources: any): Array<{
  type: 'image' | 'video' | 'document' | 'audio'
  title: string
  description: string
  url: string
}> => {
  const materials: any[] = []
  if (resources.images) {
    resources.images.forEach((img: any) => {
      materials.push({
        type: 'image',
        title: img.title || img.name || '图片',
        description: img.description || '',
        url: img.url || ''
      })
    })
  }
  if (resources.videos) {
    resources.videos.forEach((vid: any) => {
      materials.push({
        type: 'video',
        title: vid.title || vid.name || '视频',
        description: vid.description || '',
        url: vid.url || ''
      })
    })
  }
  if (resources.documents) {
    resources.documents.forEach((doc: any) => {
      materials.push({
        type: 'document',
        title: doc.title || doc.name || '文档',
        description: doc.description || '',
        url: doc.url || ''
      })
    })
  }
  if (resources.audio) {
    resources.audio.forEach((aud: any) => {
      materials.push({
        type: 'audio',
        title: aud.title || aud.name || '音频',
        description: aud.description || '',
        url: aud.url || ''
      })
    })
  }
  return materials
}

const editLesson = () => {
  activeTab.value = 'edit'
  // 初始化编辑器内容
  if (currentLesson.value) {
    editorContent.value = generateEditorContent(currentLesson.value)
    if (editorRef.value) {
      editorRef.value.innerHTML = editorContent.value
    }
  }
}

// TODO: duplicateLessonPlan not implemented in API yet
// const duplicateLesson = async () => {
//   if (!currentLesson.value) return
//
//   try {
//     await ElMessageBox.confirm('确定要复制此教案吗？', '确认', {
//       type: 'warning'
//     })
//
//     await duplicateLessonPlan(currentLesson.value.id)
//     ElMessage.success('教案复制成功')
//     showDetailDrawer.value = false
//     await loadLessons()
//   } catch (error) {
//     if (error !== 'cancel') {
//       console.error('复制教案失败:', error)
//       ElMessage.error('复制教案失败')
//     }
//   }
// }

const deleteLesson = async () => {
  if (!currentLesson.value) return

  try {
    await ElMessageBox.confirm('确定要删除此教案吗？删除后无法恢复。', '警告', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })

    await deleteLessonPlan(currentLesson.value.id)
    ElMessage.success('教案已删除')
    showDetailDrawer.value = false
    await loadLessons()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除教案失败:', error)
      ElMessage.error('删除教案失败')
    }
  }
}

const handleAction = (command: string, lesson: LessonPlan) => {
  switch (command) {
    case 'edit':
      currentLesson.value = lesson
      showDetailDrawer.value = true
      setTimeout(() => editLesson(), 300)
      break
    case 'duplicate':
      currentLesson.value = lesson
      // duplicateLesson() // TODO: not implemented in API
      ElMessage.info('复制功能暂未实现')
      break
    case 'export':
      currentLesson.value = lesson
      showExportDialog.value = true
      break
    case 'delete':
      currentLesson.value = lesson
      deleteLesson()
      break
  }
}

const handleExport = async (format: string) => {
  exportFormat.value = format
  await doExport()
}

const doExport = async () => {
  if (!currentLesson.value) return

  exporting.value = true
  try {
    if (exportFormat.value === 'markdown') {
      // Markdown 导出直接在浏览器完成
      await exportToMarkdown(currentLesson.value)
    } else {
      // Word 和 PDF 从后端下载
      const format = exportFormat.value === 'word' ? 'docx' : 'pdf'
      const exportUrl = getExportUrl(currentLesson.value.id, format)

      // 使用 fetch 下载文件
      const response = await fetch(exportUrl, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      })

      if (!response.ok) {
        throw new Error('导出失败')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${currentLesson.value.title}.${format}`
      link.click()
      URL.revokeObjectURL(url)
    }

    showExportDialog.value = false
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const exportToWord = async (lesson: LessonPlan) => {
  const exportUrl = getExportUrl(lesson.id, 'docx')
  const link = document.createElement('a')
  link.href = exportUrl
  link.download = `${lesson.title}.docx`
  link.click()
  ElMessage.success('Word 导出成功')
}

const exportToPDF = async (lesson: LessonPlan) => {
  const exportUrl = getExportUrl(lesson.id, 'pdf')
  const link = document.createElement('a')
  link.href = exportUrl
  link.download = `${lesson.title}.pdf`
  link.click()
  ElMessage.success('PDF 导出成功')
}

const exportToMarkdown = async (lesson: LessonPlan) => {
  const markdown = await apiExportToMarkdown(lesson)
  const blob = new Blob([markdown], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${lesson.title}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('Markdown 导出成功')
}

// 编辑器功能
const execCommand = (command: string, value?: string) => {
  document.execCommand(command, false, value)
}

const handleEditorInput = () => {
  if (editorRef.value) {
    editorContent.value = editorRef.value.innerHTML
  }
}

const resetEdit = () => {
  if (currentLesson.value) {
    editorContent.value = generateEditorContent(currentLesson.value)
    if (editorRef.value) {
      editorRef.value.innerHTML = editorContent.value
    }
  }
}

const saveEdit = async () => {
  if (!currentLesson.value) return

  saving.value = true
  try {
    // 将编辑器内容保存为 HTML
    const content = editorRef.value?.innerHTML || ''
    await updateLessonContent(currentLesson.value.id, content)
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDrawerClose = () => {
  activeTab.value = 'overview'
  currentLesson.value = null
}

const goToAIPlanning = () => {
  router.push('/teacher/ai-planning')
}

// 辅助函数
const getLevelType = (level: string) => {
  const types: Record<string, any> = {
    'A1': 'danger',
    'A2': 'warning',
    'B1': 'primary',
    'B2': 'success',
    'C1': 'info',
    'C2': ''
  }
  return types[level] || 'info'
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    'draft': 'info',
    'completed': 'success'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'draft': '草稿',
    'completed': '已完成'
  }
  return texts[status] || status
}

const getFocusAreaName = (area: string) => {
  const names: Record<string, string> = {
    'speaking': '口语',
    'listening': '听力',
    'reading': '阅读',
    'writing': '写作',
    'grammar': '语法',
    'vocabulary': '词汇'
  }
  return names[area] || area
}

const getSkillTypeName = (type: string) => {
  const names: Record<string, string> = {
    'speaking': '口语',
    'listening': '听力',
    'reading': '阅读',
    'writing': '写作'
  }
  return names[type] || type
}

const getObjectivesSummary = (lesson: LessonPlan) => {
  if (!lesson.objectives) return '未设置'
  const parts: string[] = []
  if (lesson.objectives.language_knowledge?.length) parts.push('语言知识')
  if (lesson.objectives.language_skills) parts.push('语言技能')
  return parts.join('、') || '未设置'
}

const getVocabularyCount = (lesson: LessonPlan) => {
  let count = 0
  if (lesson.vocabulary?.noun) count += lesson.vocabulary.noun.length
  if (lesson.vocabulary?.verb) count += lesson.vocabulary.verb.length
  if (lesson.vocabulary?.adjective) count += lesson.vocabulary.adjective.length
  return count
}

const hasVocabulary = (lesson: LessonPlan) => {
  return getVocabularyCount(lesson) > 0
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const getTimelineIcon = (index: number) => {
  const icons = ['Clock', 'Edit', 'Check', 'Finished']
  return icons[index % icons.length]
}

const getMaterialIcon = (type: string) => {
  const icons: Record<string, any> = {
    'image': Picture,
    'video': VideoCamera,
    'document': Document,
    'audio': VideoCamera
  }
  return icons[type] || Document
}

const downloadMaterial = (material: any) => {
  // TODO: 下载材料
  ElMessage.info('下载功能开发中...')
}

// 辅助函数：生成语法点HTML
const formatGrammarPoint = (gp: any): string => {
  let result = `<h3>${gp.name}</h3><p>${gp.description}</p>`
  if (gp.rule) {
    result += `<p><strong>规则：</strong>${gp.rule}</p>`
  }
  return result
}

// 辅助函数：生成教学流程HTML
const formatStructurePhase = (phase: any, i: number): string => {
  return `<h3>${i + 1}. ${phase.title} (${phase.duration || 0}分钟)</h3><p>${phase.description || ''}</p>`
}

const generateEditorContent = (lesson: LessonPlan) => {
  return `
    <h1>${lesson.title}</h1>
    <p><strong>主题：</strong>${lesson.topic || '未设置'}</p>
    <p><strong>级别：</strong>${lesson.level}</p>
    <p><strong>时长：</strong>${lesson.duration} 分钟</p>

    <h2>教学目标</h2>
    ${lesson.objectives?.language_knowledge?.map(obj => `<p>• ${obj}</p>`).join('') || ''}
    ${lesson.objectives?.language_skills ? Object.entries(lesson.objectives.language_skills).map(([type, skills]) =>
      `<p><strong>${getSkillTypeName(type)}：</strong>${skills.join('、')}</p>`
    ).join('') : ''}

    <h2>核心词汇</h2>
    ${lesson.vocabulary?.noun?.map(v => `<p>• <strong>${v.word}</strong>: ${v.meaning_cn}</p>`).join('') || ''}

    <h2>语法点</h2>
    ${lesson.grammar_points?.map(gp => formatGrammarPoint(gp)).join('') || ''}

    <h2>教学流程</h2>
    ${lesson.structure?.map((phase, i) => formatStructurePhase(phase, i)).join('') || ''}
  `
}

onMounted(() => {
  loadLessons()
})
</script>

<style scoped>
.lessons-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.el-main {
  padding: 20px;
}

/* 教案网格 */
.lessons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.lesson-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.lesson-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.lesson-info {
  flex: 1;
}

.lesson-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.lesson-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.lesson-duration {
  font-size: 14px;
  color: #909399;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lesson-topic {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  font-size: 14px;
  color: #606266;
}

.lesson-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.lesson-date {
  font-size: 12px;
  color: #909399;
}

/* 详情抽屉 */
.lesson-detail-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-actions {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.lesson-tabs {
  flex: 1;
  overflow: hidden;
}

.tab-content {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.section {
  margin-bottom: 24px;
}

.section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.objectives-section {
  margin-bottom: 24px;
}

.objectives-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
  color: #606266;
}

.skills-group {
  margin: 12px 0;
  padding: 12px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
}

.skill-label {
  font-weight: 600;
  color: #409eff;
  margin-right: 8px;
}

.vocab-section {
  margin-bottom: 24px;
}

.vocab-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.grammar-card {
  padding: 16px;
  background: var(--el-fill-color-blank);
  border-radius: 8px;
  margin-bottom: 16px;
}

.grammar-card h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.grammar-description {
  color: #606266;
  line-height: 1.6;
}

.grammar-rule {
  margin: 8px 0;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  font-size: 14px;
}

.grammar-examples {
  margin: 12px 0 0 0;
  padding-left: 20px;
}

.lesson-timeline {
  padding-left: 20px;
}

.timeline-content {
  padding: 12px 0;
}

.timeline-content h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.phase-description {
  color: #606266;
  line-height: 1.6;
}

.phase-activities {
  margin: 12px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 4px;
  font-size: 13px;
}

.phase-tips {
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 12px;
  background: var(--el-color-warning-light-9);
  border-radius: 4px;
  font-size: 13px;
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.material-card {
  padding: 16px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  text-align: center;
}

.material-icon {
  margin-bottom: 12px;
}

.material-card h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.material-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
  min-height: 40px;
}

/* 编辑器 */
.edit-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.edit-toolbar {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.rich-editor {
  flex: 1;
  padding: 20px;
  background: white;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
}

.rich-editor:focus {
  outline: none;
}

.rich-editor h1 {
  font-size: 24px;
  margin: 16px 0;
}

.rich-editor h2 {
  font-size: 20px;
  margin: 14px 0;
}

.rich-editor h3 {
  font-size: 18px;
  margin: 12px 0;
}

.rich-editor p {
  margin: 8px 0;
}

.rich-editor ul,
.rich-editor ol {
  margin: 8px 0;
  padding-left: 24px;
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

@media (max-width: 768px) {
  .lessons-grid {
    grid-template-columns: 1fr;
  }

  .header-actions {
    flex-direction: column;
    width: 100%;
  }

  .header-actions .el-input,
  .header-actions .el-select {
    width: 100% !important;
  }
}
</style>
