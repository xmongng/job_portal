"""Import toàn bộ 14 model để Alembic nhận đủ metadata."""

from .applicants import Applicant as Applicant
from .applicants import ApplicantSkill as ApplicantSkill
from .applications import Application as Application
from .catalog import Skill as Skill
from .companies import Company as Company
from .companies import CompanyMembership as CompanyMembership
from .identity import AuthSession as AuthSession
from .identity import User as User
from .interviews import Interview as Interview
from .jobs import Job as Job
from .jobs import JobSkill as JobSkill
from .offers import Offer as Offer
from .operations import Notification as Notification
from .resumes import Resume as Resume
