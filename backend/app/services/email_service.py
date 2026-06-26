import smtplib
import secrets
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.settings = get_settings()

    def generate_reset_code(self) -> str:
        return str(secrets.randbelow(1000000)).zfill(6)

    def send_password_reset_email(self, email: str, nickname: str, code: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
            msg["To"] = email
            msg["Subject"] = "EduBuddy 密码重置"

            body = (
                f"尊敬的 {nickname}，\n\n"
                f"您正在重置 EduBuddy 账户密码。\n\n"
                f"您的验证码：{code}\n\n"
                f"此验证码在 15 分钟内有效。\n\n"
                f"⚠️ 安全提示：如果这不是您的操作，请立即忽略此邮件。\n\n"
                f"— EduBuddy 团队"
            )
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.sendmail(self.settings.smtp_from_email, email, msg.as_string())

            return True
        except Exception as e:
            logging.error(f"Failed to send password reset email to {email}: {e}")
            return False


email_service = EmailService()
