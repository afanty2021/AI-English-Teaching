<!--
  教案模板卡片组件
  用于在模板库中展示单个模板的信息
-->
<template>
  <div
    class="template-card"
    :class="{ 'is-official': template.is_official }"
    @click="handleCardClick"
  >
    <!-- 官方标记 -->
    <div
      v-if="template.is_official"
      class="official-badge"
    >
      <el-icon><Star /></el-icon>
      <span>官方</span>
    </div>

    <!-- 缩略图区域 -->
    <div class="card-thumbnail">
      <div
        v-if="template.thumbnail_url"
        class="thumbnail-image"
      >
        <img
          :src="template.thumbnail_url"
          :alt="template.name"
        />
      </div>
      <div
        v-else
        class="thumbnail-placeholder"
      >
        <el-icon :size="48">
          <Document />
        </el-icon>
      </div>

      <!-- 悬浮操作按钮 -->
      <div class="card-actions">
        <el-button
          type="primary"
          size="small"
          @click.stop="handleApply"
        >
          <el-icon><Plus /></el-icon>
          应用
        </el-button>
        <el-button
          size="small"
          @click.stop="handlePreview"
        >
          <el-icon><View /></el-icon>
          预览
        </el-button>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="card-body">
      <!-- 标题和分类 -->
      <div class="card-header">
        <h3 class="template-name">
          {{ template.name }}
        </h3>
        <el-tag
          size="small"
          type="info"
        >
          {{ template.category_label }}
        </el-tag>
      </div>

      <!-- 描述 -->
      <p class="template-description">
        {{ template.description }}
      </p>

      <!-- 元信息 -->
      <div class="card-meta">
        <div class="meta-item">
          <el-tag
            size="small"
            :type="getLevelType(template.level)"
          >
            {{ template.level }}
          </el-tag>
          <span class="duration">{{ template.duration }} 分钟</span>
        </div>

        <div class="meta-stats">
          <span
            v-if="template.rating > 0"
            class="rating"
          >
            <el-icon><StarFilled /></el-icon>
            {{ template.rating.toFixed(1) }}
          </span>
          <span class="usage-count">
            <el-icon><User /></el-icon>
            {{ template.usage_count }}
          </span>
        </div>
      </div>
    </div>

    <!-- 更多操作菜单 -->
    <div
      v-if="showMoreMenu"
      class="card-more"
      @click.stop
    >
      <el-dropdown @command="handleMoreAction">
        <el-button
          circle
          :icon="MoreFilled"
          size="small"
        />
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              command="edit"
              :icon="Edit"
            >
              编辑
            </el-dropdown-item>
            <el-dropdown-item
              command="duplicate"
              :icon="CopyDocument"
            >
              复制
            </el-dropdown-item>
            <el-dropdown-item
              command="favorite"
              :icon="isFavorited ? StarFilled : Star"
            >
              {{ isFavorited ? '取消收藏' : '收藏' }}
            </el-dropdown-item>
            <el-dropdown-item
              divided
              command="delete"
              :icon="Delete"
            >
              删除
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TemplateListItem } from '@/types/lessonTemplate'
import {
  Star,
  StarFilled,
  Document,
  Plus,
  View,
  User,
  MoreFilled,
  Edit,
  CopyDocument,
  Delete
} from '@element-plus/icons-vue'

interface Props {
  /** 模板数据 */
  template: TemplateListItem
  /** 是否显示更多菜单 */
  showMoreMenu?: boolean
  /** 是否已收藏 */
  isFavorited?: boolean
}

interface Emits {
  /** 点击卡片 */
  click: []
  /** 应用模板 */
  apply: []
  /** 预览模板 */
  preview: []
  /** 编辑 */
  edit: []
  /** 复制 */
  duplicate: []
  /** 收藏/取消收藏 */
  favorite: []
  /** 删除 */
  delete: []
}

const props = withDefaults(defineProps<Props>(), {
  showMoreMenu: true,
  isFavorited: false
})

const emit = defineEmits<Emits>()

// 获取级别对应的标签类型
const getLevelType = (level: string) => {
  const types: Record<string, any> = {
    A1: 'danger',
    A2: 'warning',
    B1: 'primary',
    B2: 'success',
    C1: 'info',
    C2: ''
  }
  return types[level] || 'info'
}

// 处理卡片点击
const handleCardClick = () => {
  emit('click')
}

// 处理应用
const handleApply = () => {
  emit('apply')
}

// 处理预览
const handlePreview = () => {
  emit('preview')
}

// 处理更多操作
const handleMoreAction = (command: string) => {
  switch (command) {
    case 'edit':
      emit('edit')
      break
    case 'duplicate':
      emit('duplicate')
      break
    case 'favorite':
      emit('favorite')
      break
    case 'delete':
      emit('delete')
      break
  }
}
</script>

<style scoped>
.template-card {
  position: relative;
  background: #fff;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
  border-color: var(--el-color-primary);
}

.template-card.is-official {
  border-color: var(--el-color-warning);
}

/* 官方标记 */
.official-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #fff;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(253, 160, 133, 0.4);
}

/* 缩略图区域 */
.card-thumbnail {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: var(--el-fill-color-light);
  overflow: hidden;
}

.thumbnail-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
}

/* 悬浮操作按钮 */
.card-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.template-card:hover .card-actions {
  opacity: 1;
}

/* 卡片内容 */
.card-body {
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.template-name {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-description {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

/* 元信息 */
.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.meta-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.rating {
  display: flex;
  align-items: center;
  gap: 2px;
  color: #f59e0b;
}

.usage-count {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* 更多操作 */
.card-more {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
}

.card-more .el-button {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .card-actions {
    opacity: 1;
    background: rgba(0, 0, 0, 0.5);
  }

  .template-description {
    -webkit-line-clamp: 1;
  }
}
</style>
