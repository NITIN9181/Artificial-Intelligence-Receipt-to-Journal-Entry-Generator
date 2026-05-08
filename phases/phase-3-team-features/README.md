# Phase 3 — Team Features (Months 3–6)

## 💰 FREE TIER IMPLEMENTATION

This phase is designed to run at **$0/month** using free-tier services and self-hosted alternatives.

### Free Tier Limits & Workarounds

| Service | Free Tier Limits | Strategy |
|---------|-----------------|----------|
| Supabase Free | 500MB DB, 5GB bandwidth, 50K MAU | Monitor usage; upgrade only if exceeded |
| Ollama (self-hosted) | Unlimited (your hardware) | Use quantized models for efficiency |
| GnuCash | Unlimited, local | Full desktop app with SQLite backend |
| CSV/Excel Export | Unlimited | Universal format, works with any accounting software |

## Prerequisites

- **> 500 receipts/month** OR **> 3 team members** (stay within Supabase Free limits)
- **Supabase Free Tier** — Monitor usage at supabase.com/dashboard
- **Ollama self-hosted** — Already set up in Phase 2, no additional cost
- **GnuCash** (free desktop accounting software) OR use CSV/Excel export for universal compatibility

## Goal

Add user roles, approval workflows, and accounting software integration for team-based accounting operations — all at zero cost.

## Deliverables

- [ ] Role-based access: PREPARER, REVIEWER, ADMIN
- [ ] Approval workflow: Preparer submits → Reviewer approves/rejects with comments
- [ ] GnuCash integration via SQLite export OR universal CSV/Excel export
- [ ] "Export to Accounting Software" button on posted journal entries
