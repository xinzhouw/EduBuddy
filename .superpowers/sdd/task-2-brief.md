# Task 2: 创建 i18n 配置文件

## 文件修改

**Files:**
- Create: `frontend/src/i18n/index.ts`
- Create: `frontend/src/i18n/locales/zh.json`
- Create: `frontend/src/i18n/locales/en.json`

## Interfaces

**Produces:** 
- `export const i18n` - createI18n 实例，用于 main.ts 注册
- `i18n.global.locale.value` - 当前语言（'zh'|'en'）
- `i18n.global.t(key)` - 翻译函数

## 任务描述

创建 vue-i18n 的配置和翻译文件。这是多语言系统的核心。

### 全局约束
- vue-i18n 使用 Composition API 模式（`legacy: false`）
- 所有翻译文件采用 JSON 格式，嵌套结构，keys 为英文小写
- 语言参数统一使用 `'zh'` 和 `'en'`

### 创建的文件详情

#### `frontend/src/i18n/index.ts`

```typescript
import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

export const i18n = createI18n({
  legacy: false,  // Composition API 模式
  locale: 'zh',   // 默认语言
  fallbackLocale: 'zh',
  messages: {
    zh,
    en
  }
})

export default i18n
```

#### `frontend/src/i18n/locales/zh.json` - 中文翻译（P0 内容）

包含以下分类（嵌套 JSON）：
- common: 通用文本（是/否/确定等）
- auth: 认证相关（登录/注册/邮箱/密码等）
- navigation: 导航菜单（仪表板/笔记/作业等）
- error: 错误消息（网络错误/服务器错误等）

具体内容见下面的代码块。

#### `frontend/src/i18n/locales/en.json` - 英文翻译（同结构）

完全相同的结构，所有 values 翻译为英文。

## 实现步骤

1. 创建 `frontend/src/i18n/` 目录和 `locales/` 子目录
2. 创建 `index.ts` 文件，导入 JSON 文件并配置 i18n
3. 创建 `zh.json` 和 `en.json` 翻译文件（P0 内容：auth/navigation/common/error）
4. 验证 JSON 格式正确（npm 脚本或 node -e 验证）
5. 提交所有文件到 git

## 验证方式

```bash
# 验证 JSON 格式
node -e "console.log(JSON.parse(require('fs').readFileSync('frontend/src/i18n/locales/zh.json')))"
```

Expected: 无 JSON 解析错误，能显示对象结构

## 报告位置

完成后写报告到 `/home/xinzhouw/src/EduBuddy/.superpowers/sdd/task-2-report.md`

包含：
- 创建的文件列表
- JSON 验证结果
- commit ID
- 任何观察或问题
