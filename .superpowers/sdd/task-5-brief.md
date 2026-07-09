# Task 5: 修改 AppHeader 集成语言切换器

## 文件修改

**Files:**
- Modify: `frontend/src/components/layout/AppHeader.vue`

## Interfaces

**Consumes:** 
- `<LanguageSwitcher />` 组件（Task 4 创建）

**Produces:** 
- AppHeader 右侧顶部栏增加语言切换按钮

## 任务描述

在现有的 AppHeader 组件中集成 LanguageSwitcher 组件。

### 实现步骤

1. 在 AppHeader.vue 的 `<script setup>` 中导入 LanguageSwitcher
2. 在模板中，找到头部右侧的操作区域
3. 在该区域内添加 `<LanguageSwitcher />`，通常在用户菜单之前

### 示例位置

如果当前结构是：
```vue
<div class="flex items-center gap-4">
  <!-- 其他操作 -->
  <UserMenu />
</div>
```

改为：
```vue
<div class="flex items-center gap-4">
  <!-- 其他操作 -->
  <LanguageSwitcher />
  <UserMenu />
</div>
```

### 验证方式

编译验证：
```bash
cd frontend && npm run build 2>&1 | grep -E "error|Error" | head -5
```

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-5-i18n-report.md`
