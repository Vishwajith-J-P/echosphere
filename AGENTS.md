Before implementing any feature:

1. Read product/product_requirement_document.md for product requirements.
2. Read technical/technical_requirement_document.md for technical constraints.
3. Read product/app_flow.md for user flow.
4. Read product/ui_ux_brief.md for interface requirements.
5. Read technical/backend_schema.md before modifying data structures.
6. Read execution/features.md to determine what already exists.
7. Read decisions.md before changing architecture.
8. Read execution/tech_debt.md before refactoring known issues.
9. Read product/safety_policy.md for conversational or escalation behavior.
10. Read technical/agora_integration.md before modifying the voice path.
11. Read execution/traceability.md and execution/test_plan.md for required verification.


During implementation:
- Follow existing architectural patterns.
- Do not duplicate existing features.
- Do not implement unapproved product scope.


After implementation:
- Update execution/features.md.
- Update technical/backend_schema.md if the schema changed.
- Update decisions.md for significant architectural decisions.
- Update execution/tech_debt.md when intentional compromises are introduced.
- Update relevant acceptance criteria.
- Update execution/traceability.md when requirements, features, or tests change.
