# Task 22: 在所有组件中替换硬编码文本为 i18n 调用

## 任务描述

在前端所有 .vue 和 .ts 组件中，将硬编码的中文文本替换为 `$t('key')` i18n 调用。

## 优先级顺序

1. **关键组件**（立即替换）
   - `views/auth/*` - 登录/注册页面
   - `components/layout/*` - 导航、菜单
   - 主页面骨架

2. **主要功能页面**（逐个替换）
   - `views/DashboardView.vue`
   - `views/notes/*`
   - `views/homework/*`
   - `views/ai/*` (AI 聊天)
   - `views/quiz/*`
   - `views/wrongBook/*`

3. **次要页面**（最后替换）
   - 设置、个人资料等

## 实现步骤

1. 逐个打开 .vue 文件
2. 找出所有硬编码中文文本
3. 为每个文本在 zh.json 中检查是否已有对应 key
4. 在模板中将 `文本` 替换为 `{{ $t('key') }}`
5. 在 script 中如需使用则用 `const msg = i18n.global.t('key')`
6. 逐个提交每个关键组件的修改

## 验证

修改后检查是否仍有硬编码中文：
```bash
grep -r "[一-鿿]" src/views src/components --include="*.vue" | grep -v "$t" | wc -l
```

结果应趋近于 0。

## 报告位置

完成后报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-22-i18n-report.md`

包含：
- 修改的文件清单
- 替换的文本数量
- 验证结果（硬编码文本数）
- 各项 commits
