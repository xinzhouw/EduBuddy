# Task 5 完成报告：AppHeader 集成语言切换器

## 状态：完成 ✓

## 修改文件

- `frontend/src/components/layout/AppHeader.vue`

## 变更内容

### 1. 导入 LanguageSwitcher 组件

在 `<script setup>` 中新增导入：

```ts
import LanguageSwitcher from '@/components/layout/LanguageSwitcher.vue'
```

### 2. 模板中插入组件

在右侧工具栏（`<!-- 右侧工具栏 -->`）内，通知按钮之前添加：

```vue
<!-- 语言切换器 -->
<LanguageSwitcher />
```

## 验证结果

```
npm run build → ✓ built in 1.98s（无编译错误）
```

## 位置说明

`<LanguageSwitcher />` 放置在通知按钮之前，位于头部右侧操作区域，符合规范要求。
