"""Đăng ký model để Alembic nhìn thấy mọi bảng trong Base.metadata.

Khi thêm class mới vào một module, import class đó tại đây trước khi sinh migration.
Không import module chưa có model để tránh tạo migration rỗng.
"""

from .ai import AiOperation as AiOperation
from .ai import AiRateWindow as AiRateWindow
from .applicants import Applicant as Applicant
from .applicants import ApplicantEducation as ApplicantEducation
from .applicants import ApplicantExperience as ApplicantExperience
from .applicants import ApplicantSkill as ApplicantSkill
from .applications import Application as Application
from .applications import ApplicationNote as ApplicationNote
from .applications import ApplicationStatusHistory as ApplicationStatusHistory
from .catalog import JobCategory as JobCategory
from .catalog import Location as Location
from .catalog import Skill as Skill
from .companies import Company as Company
from .companies import CompanyInvitation as CompanyInvitation
from .companies import CompanyMembership as CompanyMembership
from .identity import AccountToken as AccountToken
from .identity import AuthSession as AuthSession
from .identity import User as User
from .interviews import Interview as Interview
from .jobs import Job as Job
from .jobs import JobSkill as JobSkill
from .jobs import JobStatusHistory as JobStatusHistory
from .offers import Offer as Offer
from .operations import AuditLog as AuditLog
from .operations import EmailDelivery as EmailDelivery
from .operations import Notification as Notification
from .operations import SecurityRateWindow as SecurityRateWindow
from .resumes import CvDocument as CvDocument
from .resumes import Resume as Resume
