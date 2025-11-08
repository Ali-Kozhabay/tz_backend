import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

from jinja2 import Environment, PackageLoader, select_autoescape

from app.core.config import get_settings

env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(["html", "txt"]),
)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    return env.get_template(template_name).render(**context)


def send_email(to_email: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user or "noreply@example.com"
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user and settings.smtp_pass:
            smtp.login(settings.smtp_user, settings.smtp_pass)
        smtp.sendmail(msg["From"], [to_email], msg.as_string())
