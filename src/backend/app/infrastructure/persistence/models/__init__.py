"""Đăng ký model để Alembic nhìn thấy mọi bảng trong Base.metadata.

Khi thêm class mới vào một module, import class đó tại đây trước khi sinh migration.
Không import module chưa có model để tránh tạo migration rỗng.
"""

from .applicants import Applicant as Applicant
from .applicants import ApplicantEducation as ApplicantEducation
from .applicants import ApplicantExperience as ApplicantExperience
from .applicants import ApplicantSkill as ApplicantSkill
from .catalog import JobCategory as JobCategory
from .catalog import Location as Location
from .catalog import Skill as Skill
from .companies import Company as Company
from .companies import CompanyInvitation as CompanyInvitation
from .companies import CompanyMembership as CompanyMembership
from .identity import AccountToken as AccountToken
from .identity import AuthSession as AuthSession
from .identity import User as User
