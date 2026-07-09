# Task 18 测试报告：前端多语言基础功能

**日期**: 2026-07-09  
**测试方式**: 静态代码分析（无浏览器，通过构建验证和代码审查）  
**结论**: 基础设施正确，但 UI 覆盖范围不足

---

## 测试环境

- **前端**: Vue 3 + Vite + vue-i18n 9.14.5 + Pinia
- **构建结果**: `npm run build` 成功，零 TypeScript 错误
- **语言文件**: `zh.json` 和 `en.json` 均 97 行，结构一致

---

## 各项测试结果

### 1. 启动开发服务器

**结果: PASS**  
`npm run build` 构建成功，无编译错误或类型错误。`vue-i18n@9.14.5` 已正确安装并注册到 Vue 应用（`main.ts` 中 `app.use(i18n)`）。

---

### 2. 检查初始语言（应为中文）

**结果: PASS**

初始化逻辑正确：
- `i18n/index.ts`: `locale: 'zh'`（硬编码默认值）
- `stores/language.ts`: `currentLanguage` 默认为 `'zh'`
- `App.vue` `onMounted`: 调用 `langStore.initLanguage()`，若 localStorage 无记录则回退到 `'zh'`，然后执行 `locale.value = langStore.currentLanguage`

---

### 3. 测试语言切换（UI 立即响应，无刷新）

**结果: PARTIAL FAIL**

**机制正确**（切换逻辑本身无误）：
- `LanguageSwitcher.vue` 的 `handleSwitch` 方法：先调用 `langStore.setLanguage(newLang)`（保存到 localStorage），再执行 `locale.value = newLang`（响应式更新 i18n locale）
- 语言切换按钮标签本身会立即从"中文"切换为"English"（无刷新）

**覆盖范围严重不足**（这是核心问题）：

| 组件 | 使用 `t()` 翻译？ |
|------|-----------------|
| `LanguageSwitcher.vue` | 是（仅按钮标签） |
| `App.vue` | 否（只获取 locale 引用） |
| `AppHeader.vue` | 否（`pageTitles` 全部为硬编码中文） |
| `AppSidebar.vue` | 否（导航菜单标签全部为硬编码中文） |
| `AppBottomNav.vue` | 否 |
| `views/` 下所有 Vue 组件 | 无一使用 `useI18n()` 或 `t()` |

**实际效果**：切换到 English 后，只有顶部语言按钮标签变为"English"，其余所有 UI 文字（导航菜单、页面标题、按钮文字等）仍为中文。翻译键（如 `t('navigation.ai_chat')`）虽然在 `zh.json` / `en.json` 中已定义，但没有任何组件实际调用这些键。

**`zh.json` / `en.json` 已定义但未使用的翻译分组**：
- `common.*`（28 个键）
- `auth.*`（22 个键）  
- `navigation.*`（14 个键）
- `error.*`（14 个键）

---

### 4. 测试 localStorage 保存

**结果: PASS**

`stores/language.ts` 中 `setLanguage()` 方法：
```ts
localStorage.setItem('language', lang)
```
键名为 `'language'`，值为 `'zh'` 或 `'en'`。逻辑正确，每次切换都会同步写入。

---

### 5. 测试刷新后语言选择被保留

**结果: PASS（机制正确，但视觉无变化）**

`App.vue` `onMounted` 中：
```ts
await langStore.initLanguage()   // 从 localStorage 读取
locale.value = langStore.currentLanguage  // 恢复 i18n locale
```
`stores/language.ts` 的 `initLanguage()`：
```ts
const saved = localStorage.getItem('language') as 'zh' | 'en' | null
currentLanguage.value = saved || 'zh'
```
刷新后语言状态可以正确恢复。语言按钮标签会保持正确状态（English/中文）。但由于组件未使用翻译键，页面内容视觉上无法区分两种语言。

---

## 总体评估

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 基础设施配置 | PASS | vue-i18n 安装、注册、Pinia store 均正确 |
| 默认中文 | PASS | 硬编码默认值 + localStorage 回退 |
| 切换响应性（机制） | PASS | locale.value 响应式更新正确 |
| 切换后 UI 变化（内容） | FAIL | 无组件使用 t() — UI 实际不变 |
| localStorage 写入 | PASS | setLanguage 正确写入 |
| 刷新保留（机制） | PASS | initLanguage 正确读取 localStorage |
| 构建无错误 | PASS | TypeScript 零错误 |

---

## 根本原因

多语言基础设施（`i18n/index.ts`、`stores/language.ts`、`LanguageSwitcher.vue`、`zh.json`、`en.json`）已完整实现，但**各 UI 组件均使用硬编码中文字符串，而非 `t()` 翻译键**。

需要完成的工作是将组件中的硬编码文字替换为 `t('namespace.key')` 调用（Task 2–17 中每个功能模块分别完成）。

---

## 建议

以 `AppHeader.vue` 中的 `pageTitles` 为例，修改方式如下：

```ts
// 当前（硬编码）
const pageTitles: Record<string, string> = {
  '/ai': 'AI 问答',
  '/notes': '我的笔记',
  ...
}

// 应改为（使用 t()）
const { t } = useI18n()
const pageTitles = computed(() => ({
  '/ai': t('navigation.ai_chat'),
  '/notes': t('navigation.notes'),
  ...
}))
```

这一模式需要在所有视图和组件中统一应用。
