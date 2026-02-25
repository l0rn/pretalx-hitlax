# Rewrite plan for current pretalx

Target runtime baseline: `pretalx 2025.2.x` (currently installed: 2025.2.2)

## Strategy
1. Keep feature parity with `docs/legacy-behavior.md`.
2. Rewrite integration points first (signals, URLs, templates, permissions).
3. Then port business behavior (expenses/tours/logging/export).
4. Add regression tests before polishing UI.

## Work packages

## WP1: Packaging + bootstrap cleanup
- Remove/replace build-time `compilemessages` hook in `setup.py`.
- Ensure editable install works with default PEP517 build isolation.
- Keep entry point stable unless explicit rename is desired.

Deliverable:
- installable plugin on current pretalx with `pip install -e .` (no special flags)

## WP2: Skeleton integration on current pretalx
- Verify `AppConfig` + plugin metadata loading.
- Re-register nav hooks and confirm 3 menu entries.
- Create placeholder views/templates for all legacy routes.

Deliverable:
- all routes resolve and render in orga UI

## WP3: Expenses module parity
- Port models/forms/views/templates and permission checks.
- Re-implement paid/unpaid toggle.
- Re-implement activity logging and display labels.

Deliverable:
- end-to-end expense flow works from speaker list

## WP4: Tours module parity
- Port tour CRUD and speaker-tour assignment.
- Keep tour types (`SHUTTLE`, `BASSLINER`) and filter behavior.
- Port shuttle export page with team-based gate.

Deliverable:
- end-to-end tours flow + export

## WP5: Tests
- URL/view smoke tests (all named routes)
- permission tests (view vs change speaker)
- expense create/edit/mark logging tests
- tour CRUD + export access tests

Deliverable:
- repeatable test suite guarding regressions

## WP6: Dev environment docs
- Add reproducible local dev setup for current pretalx.
- Optional docker-compose profile for no-host-deps startup.

Deliverable:
- concise README quickstart

## Notes on legacy comparison environment
Legacy pretalx runtime setup is partially blocked in this host due to missing build dependencies for old wheels (gcc/zlib/freetype toolchain path). Workaround options:
- add system build deps and pin old python/pip stack, or
- run legacy compare in docker image with compatible base, or
- continue behavior-contract approach from code/templates (already captured).
