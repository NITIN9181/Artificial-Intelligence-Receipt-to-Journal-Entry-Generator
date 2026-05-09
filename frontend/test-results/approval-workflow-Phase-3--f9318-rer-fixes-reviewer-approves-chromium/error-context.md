# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: approval-workflow.spec.ts >> Phase 3 Approval Workflow >> Preparer submits to reviewer, reviewer rejects, preparer fixes, reviewer approves
- Location: tests\e2e\approval-workflow.spec.ts:5:7

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - heading "LedgerFlow" [level=2] [ref=e5]
      - paragraph [ref=e6]: Sign in with your email to continue. We'll send you a magic link. No passwords required.
    - generic [ref=e7]:
      - generic [ref=e9]:
        - generic [ref=e10]: Email address
        - generic [ref=e11]:
          - generic:
            - img
          - textbox "Email address" [ref=e12]:
            - /placeholder: you@company.com
      - button "Send Magic Link" [ref=e14]:
        - generic [ref=e15]:
          - text: Send Magic Link
          - img [ref=e16]
  - region "Notifications alt+T"
  - button "Open Next.js Dev Tools" [ref=e23] [cursor=pointer]:
    - img [ref=e24]
  - alert [ref=e27]
```