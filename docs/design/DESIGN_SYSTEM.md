# Design System

## Core palette

| Token | Value | Usage |
|---|---|---|
| Primary | `#2563EB` | Primary action, link, active icon |
| Primary hover | `#1D4ED8` | Hover/active state |
| Accent | `#10B981` | Positive action |
| Page background | `#F8FAFC` | App background |
| Surface | `#FFFFFF` | Card, modal, table |
| Border | `#E2E8F0` | Divider and input border |
| Text | `#0F172A` | Primary content |
| Muted text | `#64748B` | Supporting content |

## Status colors

| Status | Background | Text |
|---|---|---|
| Draft/Closed/Withdrawn | `#F1F5F9` | `#64748B` |
| Pending/Screening | `#FEF3C7` | `#B45309` |
| Published/Applied | `#EFF6FF` | `#1D4ED8` |
| Rejected | `#FEE2E2` | `#B91C1C` |
| Interview | `#EDE9FE` | `#6D28D9` |
| Offer | `#CCFBF1` | `#0F766E` |
| Hired/Accepted | `#ECFDF5` | `#047857` |

Typography dùng Inter; spacing theo thang 4px; radius 8/12/16px; shadow card nhẹ. Token được khai báo một lần bằng Tailwind CSS 4 trong stylesheet và export lại qua `src/theme/tokens.ts` khi TypeScript cần dùng trực tiếp.
