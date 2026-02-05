# PPTPreview 组件

完整的 PPT 幻灯片预览组件，支持导航、缩放、全屏、自动播放等功能。

## 组件结构

```
components/
├── PPTPreview.vue              # 主预览组件
├── PPTPreview.example.vue      # 使用示例
└── ppt/
    ├── SlideThumbnail.vue      # 缩略图组件
    ├── SlideNavigation.vue     # 导航控制组件
    └── SlideContent.vue        # 内容渲染组件
```

## 功能特性

### 核心功能
- ✅ 幻灯片导航（上一页/下一页/点击跳转）
- ✅ 缩放控制（放大/缩小/重置）
- ✅ 全屏模式
- ✅ 键盘快捷键支持
- ✅ 自动播放模式
- ✅ 缩略图导航
- ✅ 演讲者备注显示

### 布局支持
- `default` - 默认垂直列表布局
- `two-columns` - 两栏布局
- `image-text` - 图文布局
- `title-center` - 标题居中布局
- `timeline` - 时间线布局

## 使用方法

### 基础用法

```vue
<template>
  <PPTPreview :slides="slides" />
</template>

<script setup lang="ts">
import PPTPreview from '@/components/PPTPreview.vue'
import type { PPTSlide } from '@/types/lesson'

const slides: PPTSlide[] = [
  {
    slide_number: 1,
    title: '幻灯片标题',
    content: ['内容1', '内容2', '内容3'],
    notes: '演讲者备注',
    layout: 'default'
  }
]
</script>
```

### 完整配置

```vue
<template>
  <PPTPreview
    :slides="slides"
    title="我的教案"
    lesson-id="lesson-123"
    :autoplay="true"
    :autoplay-interval="5000"
    :show-keyboard-hints="true"
    :initial-show-thumbnails="true"
    @change="handleChange"
    @fullscreen-change="handleFullscreenChange"
    @export="handleExport"
  />
</template>
```

### 使用 ref 控制

```vue
<template>
  <PPTPreview ref="previewRef" :slides="slides" />
  <el-button @click="goToSlide(2)">跳转到第3页</el-button>
</template>

<script setup lang="ts">
const previewRef = ref<InstanceType<typeof PPTPreview>>()

const goToSlide = (index: number) => {
  previewRef.value?.goToSlide(index)
}
</script>
```

## Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| slides | `PPTSlide[]` | - | 幻灯片数据（必填） |
| title | `string` | - | 预览标题 |
| lessonId | `string` | - | 教案ID（用于导出等操作） |
| autoplay | `boolean` | `false` | 是否启用自动播放 |
| autoplayInterval | `number` | `5000` | 自动播放间隔（毫秒） |
| showKeyboardHints | `boolean` | `true` | 是否显示键盘快捷键提示 |
| initialShowThumbnails | `boolean` | `true` | 初始是否显示缩略图 |

## Events

| 事件 | 参数 | 说明 |
|------|------|------|
| change | `(slide: PPTSlide, index: number)` | 幻灯片切换时触发 |
| fullscreen-change | `(isFullscreen: boolean)` | 全屏状态变化时触发 |
| export | `(slide: PPTSlide)` | 导出当前幻灯片时触发 |

## 暴露方法

通过 ref 可以调用以下方法：

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| previous | - | `void` | 上一页 |
| next | - | `void` | 下一页 |
| goToSlide | `index: number` | `void` | 跳转到指定页 |
| zoomIn | - | `void` | 放大 |
| zoomOut | - | `void` | 缩小 |
| resetZoom | - | `void` | 重置缩放 |
| toggleFullscreen | - | `void` | 切换全屏 |
| togglePlay | - | `void` | 切换自动播放 |

## 键盘快捷键

| 按键 | 功能 |
|------|------|
| `←` / `→` | 上一页 / 下一页 |
| `+` / `-` | 放大 / 缩小 |
| `0` | 重置缩放 |
| `F` | 切换全屏 |
| `T` | 切换缩略图 |
| `N` | 切换备注 |
| `Home` | 第一页 |
| `End` | 最后一页 |
| `Esc` | 退出全屏 |

## 数据类型

```typescript
interface PPTSlide {
  slide_number: number      // 幻灯片编号
  title: string             // 标题
  content: string[]         // 内容列表
  notes?: string            // 演讲者备注（可选）
  layout: string            // 布局类型
}
```

## 在现有页面中集成

### LessonsView.vue 集成示例

```vue
<template>
  <!-- 在抽屉中添加 PPT 预览标签页 -->
  <el-drawer v-model="showDetailDrawer" size="70%">
    <el-tabs v-model="activeTab">
      <!-- 现有标签页... -->

      <!-- 新增 PPT 预览标签页 -->
      <el-tab-pane label="PPT 预览" name="ppt">
        <PPTPreview
          v-if="currentLesson?.ppt_outline"
          :slides="currentLesson.ppt_outline"
          :title="currentLesson.title"
          :lesson-id="currentLesson.id"
        />
        <el-empty v-else description="暂无 PPT 内容" />
      </el-tab-pane>
    </el-tabs>
  </el-drawer>
</template>

<script setup lang="ts">
import PPTPreview from '@/components/PPTPreview.vue'
import type { LessonPlan } from '@/types/lesson'

const activeTab = ref('ppt')
</script>
```

## 样式自定义

组件使用了 scoped 样式，如需自定义样式，可以使用深度选择器：

```vue
<style>
/* 修改幻灯片背景色 */
.ppt-preview .slide-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 修改缩略图宽度 */
.ppt-preview .thumbnail-sidebar {
  width: 250px;
}
</style>
```

## 依赖

- Vue 3
- Element Plus
- @element-plus/icons-vue

## 注意事项

1. **全屏兼容性**：全屏功能需要浏览器支持 Fullscreen API
2. **键盘事件**：组件会监听全局键盘事件，在组件卸载时会自动清理
3. **响应式**：组件已做响应式适配，支持移动端显示
4. **导出功能**：导出功能需要配合后端 API 实现
