"""
密码强度验证模块

评分规则（0-100 分）：
- 长度 >=8: +20 | >=12: +30 | >=16: +40
- 包含小写字母 (a-z): +10
- 包含大写字母 (A-Z): +15
- 包含数字 (0-9): +15
- 包含特殊字符: +20

强度等级：
- 有缺陷 → 弱 (WEAK)
- 无缺陷 & score < 60 → 中等 (MEDIUM)
- 无缺陷 & score >= 60 → 强 (STRONG)
"""

import re
from enum import Enum
from typing import List


SPECIAL_CHARS = r"!@#$%^&*()_+\-=\[\]{}`;:'\",./<>?\\|`~"
SPECIAL_CHARS_PATTERN = re.compile(r"[" + SPECIAL_CHARS + r"]")


class PasswordStrength(Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class PasswordValidationResult:
    """密码验证结果"""

    def __init__(self, score: int, strength: PasswordStrength, issues: List[str]):
        self.score = score
        self.strength = strength
        self.issues = issues


def validate_password_strength(password: str) -> PasswordValidationResult:
    """
    验证密码强度并返回评分、强度等级和缺陷列表。

    Args:
        password: 待验证的密码字符串

    Returns:
        PasswordValidationResult 包含 score、strength 和 issues
    """
    issues: List[str] = []
    score = 0

    # 长度检查
    length = len(password)
    if length < 8:
        issues.append("长度不足：密码至少需要 8 个字符")
    elif length >= 16:
        score += 40
    elif length >= 12:
        score += 30
    else:  # 8 <= length < 12
        score += 20

    # 小写字母检查
    if re.search(r"[a-z]", password):
        score += 10
    else:
        issues.append("缺少小写字母：密码需包含至少一个小写字母 (a-z)")

    # 大写字母检查
    if re.search(r"[A-Z]", password):
        score += 15
    else:
        issues.append("缺少大写字母：密码需包含至少一个大写字母 (A-Z)")

    # 数字检查
    if re.search(r"[0-9]", password):
        score += 15
    else:
        issues.append("缺少数字：密码需包含至少一个数字 (0-9)")

    # 特殊字符检查
    if SPECIAL_CHARS_PATTERN.search(password):
        score += 20
    else:
        issues.append("缺少特殊字符：密码需包含至少一个特殊字符 (!@#$%^&*等)")

    # 确定强度等级
    if issues:
        strength = PasswordStrength.WEAK
    elif score >= 60:
        strength = PasswordStrength.STRONG
    else:
        strength = PasswordStrength.MEDIUM

    return PasswordValidationResult(score=score, strength=strength, issues=issues)


def check_password_validity(password: str) -> tuple[bool, str]:
    """
    检查密码是否满足所有要求。

    Args:
        password: 待验证的密码字符串

    Returns:
        (is_valid, message) — is_valid 为 True 表示密码有效，
        message 为空字符串；is_valid 为 False 时 message 包含
        以分号分隔的缺陷描述（多个缺陷时含分号）。
    """
    result = validate_password_strength(password)

    if not result.issues:
        return True, ""

    message = "; ".join(result.issues)
    return False, message
