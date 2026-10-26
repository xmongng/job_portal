"""Báo cáo aggregate và CSV; recruiter chỉ xem phạm vi company mình."""

import csv
from io import StringIO
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.common.access import require_company, require_role, row_dict
from app.infrastructure.persistence import stores


# Admin xem toàn hệ thống hoặc company cụ thể; recruiter bắt buộc company_id chính chủ.
def get_report(db: Session, actor_id: UUID, company_id: UUID | None):
    user = stores.one(db, "get_user_by_id", id=actor_id)
    if user.role == "ADMIN":
        require_role(db, actor_id, "ADMIN")
        if company_id is not None and stores.one(db, "get_company_by_id", id=company_id) is None:
            raise HTTPException(404, "Company not found")
    else:
        if company_id is None:
            raise HTTPException(403, "Recruiter must provide their company_id")
        require_company(db, actor_id, company_id, lock=False)
    return {
        "company_id": company_id,
        "counts": row_dict(stores.one(db, "get_portal_counts", company_id=company_id)),
        "jobs": [row_dict(r) for r in stores.many(db, "report_job_status", company_id=company_id)],
        "applications": [
            row_dict(r) for r in stores.many(db, "report_application_status", company_id=company_id)
        ],
    }


# Chỉ export số liệu aggregate; không chứa email/note hoặc nội dung người dùng.
def export_csv(report: dict) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["section", "metric", "total"])
    for name, value in report["counts"].items():
        writer.writerow(["summary", name, value])
    for section in ("jobs", "applications"):
        for item in report[section]:
            writer.writerow([section, item["status"], item["total"]])
    return output.getvalue()
