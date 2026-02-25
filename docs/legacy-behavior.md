# pretalx-hitlax legacy behavior contract

This document captures observed legacy behavior from code/templates in `main`.
Target: preserve behavior while rewriting for current pretalx APIs.

## Plugin metadata
- Python package: `pretalx_hitalx`
- Entry point: `pretalx.plugin -> pretalx_hitalx=pretalx_hitalx:PretalxPluginMeta`
- App config: `pretalx_hitalx.apps.PluginApp`
- Version in code: `0.0.11`

## Data model

### ExpenseItem
Fields:
- `speaker` (FK -> `pretalx.person.User`, cascade, `related_name="expenses"`)
- `description` (text, required)
- `amount` (decimal, 2 places)
- `reference` (URL, optional)
- `notes` (text, optional)
- `paid` (bool, default `False`)

Behavior:
- Uses `LogMixin`, logs actions on create/edit/paid-toggle.

### Tour
Fields:
- `event` (FK -> `pretalx.event.Event`)
- `description` (text, required)
- `departure_time` (datetime, required)
- `start_location` (text, required)
- `type` (`SHUTTLE` or `BASSLINER`)
- `passengers` (M2M -> `SpeakerProfile`)

## URLs and views
Base prefix: `orga/event/<event>/...`

### Expenses / Speakers
- `/speakers-by-expense/` -> `SpeakerList` (`speakers_by_expense.view`)
- `/speakers/<speaker_id>/expenses/` -> `SpeakerExpenseList` (`expenses.view`)
- `/speakers/<speaker_id>/expenses/new` -> `SpeakerExpenseDetail` (`expenses.create`)
- `/speakers/<speaker_id>/expense/<pk>` -> `SpeakerExpenseDetail` (`expense.view`)
- `/speakers/<speaker_id>/expense/<pk>/mark` -> `MarkExpenseView` (`expense.mark`)
- `/speakers/<pk>/tours/` -> `SpeakerTourManagement` (`speaker_tours.view`)

### Tours
- `/tours/` -> `TourListView` (`tours.view`)
- `/tours/new` -> `TourDetailView` (`tour.create`)
- `/tours/<pk>` -> `TourDetailView` (`tour.view`)
- `/tours/<pk>/delete` -> `TourDeleteView` (`tour.delete`)
- `/tours/export` -> `ShuttleView` (`tours.export`)

## Permissions and access
- Most orga pages rely on `orga.view_speaker`, `orga.change_speaker`, `orga.view_speakers`.
- Paid status toggle is shown if user can `orga.change_speaker`.
- Shuttle export view allows access only if user belongs to team named exactly `shuttle`.

## Navigation hooks
Signal: `pretalx.orga.signals.nav_event`
Adds 3 entries:
1. Speaker expenses -> `speakers_by_expense.view`
2. Tours -> `tours.view`
3. Tours export -> `tours.export`

Active state currently depends on `resolve(request.path_info)` namespace/url_name matching.

## UI behavior contract

### Speaker list (`speakers.html`)
Columns:
- Name
- Expenses (Paid / Total) using template filters
- Tours count (links to speaker tours management)

Includes search + speaker filter form.

### Expense list (`speaker_expenses.html`)
- Add expense button
- List rows with description, amount, paid state icon
- Inline paid/unpaid toggle form posts to `expense.mark`

### Expense detail (`speaker_expense.html`)
- Form fields: speaker (read-only), description, amount, paid (read-only), reference, notes
- Activity log section below form

### Speaker tours (`speaker_tours.html`)
- Multi-select tours for one speaker profile
- Save writes M2M assignment

### Tour list (`tours.html`)
- Filter by `type`
- Add/Edit/Delete buttons
- Columns: type, description, location, datetime, actions

### Tour detail (`tour.html`)
- Form includes passengers multiselect and datetime picker styling

### Tour export (`tours_export.html`)
- Minimal HTML page (no orga base layout)
- Lists tours chronologically with passenger names

## Logging contract
Action types emitted:
- `pretalx_hitalx.expense_item.create`
- `pretalx_hitalx.expense_item.edit`
- `pretalx_hitalx.expense_item.mark`

Display mapping provided via `activitylog_display` signal receiver.

## Known fragile points for rewrite
- Orga base templates and block names changed over pretalx releases.
- nav entry active-state logic tied to historical resolver naming.
- Tour passenger queryset currently scoped with `django_scopes` + `Event` initial value assumptions.
- Setup/build currently calls Django management command during package build (`setup.py` custom build), which is brittle in modern PEP517 isolation.
