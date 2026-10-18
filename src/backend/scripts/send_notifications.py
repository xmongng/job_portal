"""Send one batch of committed notifications to optional local SMTP; retry on next run.
Run from backend: python scripts/send_notifications.py. Delivery is at least once.
"""

import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.infrastructure.persistence import stores
from app.infrastructure.persistence.database import SessionLocal


def main() -> None:
    settings = get_settings()
    if not settings.smtp_enabled:
        print("SMTP disabled; in-app notifications are already available.")
        return
    with SessionLocal.begin() as db:
        rows = stores.many(db, "claim_notification_emails", limit=50)
        for row in rows:
            error = None
            if not row.email.endswith(".invalid"):
                try:
                    message = EmailMessage()
                    message["From"] = settings.smtp_from
                    message["To"] = row.email
                    message["Subject"] = row.title
                    message.set_content(row.body)
                    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
                        smtp.send_message(message)
                except (OSError, smtplib.SMTPException):
                    error = "SMTP delivery failed"
            stores.execute(db, "record_notification_email_attempt", id=row.id, error=error)
    print("Processed", len(rows), "committed notifications")


if __name__ == "__main__":
    main()
