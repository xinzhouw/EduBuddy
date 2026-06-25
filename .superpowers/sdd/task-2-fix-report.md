# Task 2 Fix Report — Auth Endpoint Security Fixes

## Status: COMPLETE ✅

## Problems Fixed

### 问题 1: 旧端点 `PUT /password` 绕过密码强度检查
- **文件**: `backend/app/routers/auth.py`
- **删除行**: 原第 134-140 行（整个 `PUT /password` 端点）
- **原因**: 该端点无密码强度校验，且旧密码验证失败返回 400 而非正确的 401；
  `POST /change-password` 已完全替代其功能

### 问题 2: 相同密码检查顺序不合理
- **文件**: `backend/app/routers/auth.py`
- **修改行**: 原第 119-125 行（`POST /change-password` 内部检查顺序）
- **修复**: 将"相同密码检查"从强度检查之后移至其之前
- **修复后顺序**:
  1. 验证旧密码（返回 401）
  2. 检查新旧密码是否相同（返回 400）
  3. 检查新密码强度（返回 400）
  4. 更新密码

## 修改摘要

文件 `backend/app/routers/auth.py`：
- 净删除 9 行（13 删除，4 新增 = 净 -9 行）
- 删除整个 `PUT /password` 函数（7 行含空行）
- 调换 2 个检查块的位置（代码量不变，仅顺序变化）

## 测试命令与结果

```
cd /home/xinzhouw/src/EduBuddy/backend
venv/bin/pytest tests/test_auth.py tests/test_password_validator.py -v
```

结果：**25 passed, 0 failed** (3.40s)

```
tests/test_auth.py::TestPasswordValidateEndpoint::test_validate_weak_password PASSED
tests/test_auth.py::TestPasswordValidateEndpoint::test_validate_strong_password PASSED
tests/test_auth.py::TestRegisterWithPasswordValidation::test_register_weak_password PASSED
tests/test_auth.py::TestRegisterWithPasswordValidation::test_register_strong_password_success PASSED
tests/test_auth.py::TestChangePasswordEndpoint::test_change_password_wrong_old_password PASSED
tests/test_auth.py::TestChangePasswordEndpoint::test_change_password_weak_new_password PASSED
tests/test_auth.py::TestChangePasswordEndpoint::test_change_password_same_as_old PASSED
tests/test_auth.py::TestChangePasswordEndpoint::test_change_password_success PASSED
tests/test_password_validator.py::TestPasswordValidator::... (17 tests) PASSED
```

## 提交哈希

`7dd84bd` — fix(auth): 删除旧 PUT /password 端点并修正密码检查顺序
