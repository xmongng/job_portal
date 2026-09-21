"""Nơi đăng ký tập trung tất cả SQLAlchemy model.

Mỗi model mới phải được import tại đây để Alembic nhìn thấy metadata của bảng.
Ví dụ sau khi tạo user.py: ``from .user import User as User``.
"""
