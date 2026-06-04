"""密码哈希工具

直接使用 bcrypt 库进行密码哈希与校验。
不使用 passlib —— passlib 1.7.4 已停止维护，与 bcrypt 4.x/5.x 存在
初始化兼容性问题（detect_wrap_bug 会抛 ValueError），导致注册/登录失败。
"""
import bcrypt

# bcrypt 单次最多处理 72 字节，超出部分会被忽略，这里显式截断以避免报错
_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """生成 bcrypt 密码哈希（返回 str）"""
    pw_bytes = password.encode("utf-8")[:_MAX_BYTES]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """校验明文密码与 bcrypt 哈希是否匹配"""
    try:
        pw_bytes = password.encode("utf-8")[:_MAX_BYTES]
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
