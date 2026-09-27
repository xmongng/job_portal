# Lấy thời gian UTC hiện tại để lọc các tin tuyển dụng chưa hết hạn.
from datetime import UTC, datetime

# ID của bảng jobs dùng kiểu UUID.
from uuid import UUID

# APIRouter gom các endpoint liên quan đến tin tuyển dụng.
from fastapi import APIRouter

# BaseModel xác định cấu trúc JSON trả về.
from pydantic import BaseModel

# select xây dựng câu truy vấn SQLAlchemy.
from sqlalchemy import select

# FastAPI cấp và đóng database session cho từng request.
from app.api.dependencies.database import DatabaseSession

# Hai model đại diện cho bảng companies và jobs.
from app.infrastructure.persistence.models.companies import Company
from app.infrastructure.persistence.models.jobs import Job

# Đặt đường dẫn chung /api/jobs và nhóm Jobs trong trang /docs.
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


# Dữ liệu tóm tắt của một tin tuyển dụng được trả cho client.
class JobSummary(BaseModel):
    # Khóa chính của tin tuyển dụng.
    id: UUID

    # Tên vị trí tuyển dụng.
    title: str

    # Tên công ty đăng tin.
    company_name: str


# Đăng ký endpoint GET /api/jobs, trả về danh sách JobSummary.
@router.get("", response_model=list[JobSummary])
def list_jobs(db: DatabaseSession) -> list[JobSummary]:
    # Tạo truy vấn chỉ lấy ba cột cần trả về.
    statement = (
        select(Job.id, Job.title, Company.name.label("company_name"))
        # Ghép jobs với companies qua khóa ngoại company_id.
        .join(Company, Job.company_id == Company.id)
        # Chỉ hiển thị tin đã đăng, còn hạn và thuộc công ty hợp lệ.
        .where(
            Job.status == "PUBLISHED",
            Job.deadline > datetime.now(UTC),
            Company.verification_status == "VERIFIED",
            Company.status == "ACTIVE",
        )
        # Giới hạn số bản ghi trả về trong phiên bản đầu tiên.
        .limit(20)
    )

    # Gửi truy vấn tới PostgreSQL rồi lấy toàn bộ kết quả trong giới hạn trên.
    rows = db.execute(statement).all()

    # Chuyển từng dòng truy vấn thành cấu trúc JSON đã khai báo.
    return [
        JobSummary(id=row.id, title=row.title, company_name=row.company_name)
        for row in rows
    ]
