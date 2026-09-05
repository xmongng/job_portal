# Contributing

## Branches and commits

- Tạo branch từ `main`: `feature/<scope>`, `fix/<scope>`, `docs/<scope>`.
- Commit theo Conventional Commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Không commit secret, file `.env`, CV thật hoặc dữ liệu cá nhân.

## Pull request checklist

- [ ] Thay đổi đúng phạm vi một feature.
- [ ] Business rule có test.
- [ ] Migration có khả năng rollback.
- [ ] API contract và Postman collection được cập nhật.
- [ ] UI dùng design tokens, không hard-code màu trạng thái.
- [ ] Build, lint và test đều pass.
