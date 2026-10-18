"""Public skills catalogue and authenticated applicant skill selection."""

from fastapi import APIRouter, Query

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import DatabaseSession
from app.api.routes.recruitment import SkillWrite
from app.api.schemas import SkillResponse, SkillsWrite
from app.application.applicants import skills

router = APIRouter(prefix="/api", tags=["Skills"])


# Danh mục skills để applicant/recruiter chọn các ID hợp lệ.
@router.get("/skills", response_model=list[SkillResponse])
def list_skills(
    db: DatabaseSession, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
):
    return skills.list_skills(db, limit=limit, offset=offset)


# Admin thêm skill vào danh mục dùng chung.
@router.post("/skills", response_model=SkillResponse, status_code=201)
def create_skill(payload: SkillWrite, db: DatabaseSession, user: CurrentUser):
    return skills.create_skill(db, actor_id=user.id, name=payload.name)


# Applicant đọc skills của chính mình.
@router.get("/applicants/me/skills", response_model=list[SkillResponse])
def get_my_skills(db: DatabaseSession, user: CurrentUser):
    return skills.get_applicant_skills(db, actor_id=user.id)


# Thay toàn bộ lựa chọn skills trong một transaction; [] xóa mọi lựa chọn.
@router.put("/applicants/me/skills", response_model=list[SkillResponse])
def set_my_skills(payload: SkillsWrite, db: DatabaseSession, user: CurrentUser):
    return skills.set_applicant_skills(db, actor_id=user.id, skills=payload.skill_ids)
