# ExecPlans

When writing complex features or significant refactors, use an ExecPlan (as described in .agent/PLANS.md) from design to implementation. Write the ExecPlan in Chinese.

Agents and Subagents should update the ExecPlan as needed during implementation, and keep it up to date. If the plan changes significantly, update the design document as well.

When executing an ExecPlan, completion is not valid until the ExecPlan reflects the actual work and verification results. Before reporting DONE, Agents and Subagents must update or explicitly confirm these sections:

- `Progress`
- `Surprises & Discoveries`
- `Decision Log`, if any implementation decision changed
- `Outcomes & Retrospective`

Subagents must include the following fields in their final status:

- `ExecPlan updated: yes/no`
- `Updated sections: ...`
- `Verification performed: ...`
- `Remaining risks: ...`

If `ExecPlan updated` is `no`, the Subagent must explain why. The main Agent must not accept a DONE status until the ExecPlan has been updated or the omission is explicitly justified.

The main Agent must perform a final ExecPlan sync check before its final response. This check must confirm that completed work is checked off in `Progress`, execution surprises are recorded in `Surprises & Discoveries`, changed decisions are recorded in `Decision Log`, and real test/manual verification results plus remaining risks are recorded in `Outcomes & Retrospective`.

# Git Worktree

When using `git worktree`, place checked-out worktrees under the project `.worktrees/` directory, for example `.worktrees/<branch-name>`, unless the user explicitly asks for a different location.

When working inside a `.worktrees/` checkout, reuse the project's python virtual environment instead of installing a separate one inside the worktree. Do not create or commit python environments under `.worktrees/`.

ExecPlan files follow a frozen/unfrozen split. An ExecPlan that has already been committed is frozen: it is either fully finished or intentionally no longer executable, and only frozen ExecPlans may be checked out into `.worktrees/` with `git worktree add` for historical reference. An ExecPlan that has not yet been committed is unfrozen: it stays only in the project main working tree, is the canonical editable document for the active implementation, and must not be moved into `.worktrees/`. When an unfrozen ExecPlan reaches DoD, commit it first; any remaining follow-up work must be planned in a new ExecPlan rather than editing the frozen one.

# Communication
Use Chinese for communication, code comments, and documentation.
