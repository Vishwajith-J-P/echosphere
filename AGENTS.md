Before implementing any feature:

1. Read docs/product/project_requirement_document.md for product requirements.
2. Read docs/technical/technical_requirement_document.md for technical constraints.
3. Read docs/product/app_flow.md for user flow.
4. Read docs/product/ui_ux_brief.md for interface requirements.
5. Read docs/technical/backend_schema.md before modifying data structures.
6. Read docs/execution/features.md to determine what already exists.
7. Read docs/decisions.md before changing architecture.
8. Read docs/execution/tech_debt.md before refactoring known issues.
9. Read docs/product/safety_policy.md for conversational or escalation behavior.
10. Read docs/technical/agora_integration.md before modifying the voice path.
11. Read docs/execution/traceability.md and docs/execution/test_plan.md for required verification.


During implementation:
- Follow existing architectural patterns.
- Do not duplicate existing features.
- Do not implement unapproved product scope.


After implementation:
- Update docs/execution/features.md.
- Update docs/technical/backend_schema.md if the schema changed.
- Update docs/decisions.md for significant architectural decisions.
- Update docs/execution/tech_debt.md when intentional compromises are introduced.
- Update relevant acceptance criteria.
- Update docs/execution/traceability.md when requirements, features, or tests change.
