# G2P Survey

`g2p_survey` extends Odoo's native Survey module for Enderase online and offline form workflows.

It does not create a separate survey engine. Odoo's own `survey.survey`, `survey.question`, `survey.question.answer`, `survey.user_input`, and `survey.user_input.line` remain the canonical models.

## What This Module Adds

- ODK Central server configuration records (with chatter for notes/attachments)
- ODK staff user and ODK Collect app user provisioning
- ODK Collect device configuration QR code for app users
- App user revoke (token invalidation) and lifecycle state
- ODK form assignment to users
- ODK XLSForm generation from native Odoo Survey questions (converted to an XForm by ODK Central)
- Push/publish native Odoo surveys to ODK Central
- Import ODK submissions back into native Odoo Survey participations
- Import submission media attachments (photos, signatures, audio) as `ir.attachment`
- Scheduled ODK submission sync via cron
- Keeps the native Survey app visible (re-enables the menu that `g2p_registry` hides)
- Source and ODK metadata on native survey responses
- `Powered by Enderase` branding on the public Odoo survey form

## Dependencies

`g2p_survey` depends on:

- `mail`
- `survey`
- `g2p_registry_base`
- `g2p_registry` (defines the menu-hiding hook this module overrides)
- Python package `requests`

The `survey` addon depends on Odoo's `gamification` addon. Neither is vendored in
this repository anymore: the OpenG2P base image strips both out of Odoo core, so
`../odoo/Dockerfile` copies them back in from the official `odoo:17.0` image. They
stay stock Odoo, and only `g2p_survey` lives in the repository.

## Data Model

Native Odoo Survey remains the source of truth.

| Concern | Model |
| --- | --- |
| Survey/form definition | `survey.survey` |
| Survey questions | `survey.question` |
| Choice labels such as Member or Beneficiary | `survey.question.answer` |
| A submitted response/participation | `survey.user_input` |
| Individual answer rows | `survey.user_input.line` |
| ODK Central server configuration | `g2p.survey.odk.server` |
| ODK users/app users | `g2p.survey.odk.user` |

Imported ODK records are saved as `survey.user_input` records with:

- `g2p_response_source = odk`
- `g2p_odk_instance_id`
- `g2p_odk_submitter_id`
- `g2p_odk_device_id`
- raw submission metadata
- raw XML payload

Each answer is saved through Odoo's native survey answer API. For example, if an imported ODK submission selects both `Member` and `Beneficiary`, the result is two native `survey.user_input.line` records linked to the corresponding `survey.question.answer` records.

ODK duplicate imports are blocked by a unique constraint on:

```text
survey_id + g2p_odk_instance_id
```

## Menus

`g2p_registry` force-hides the native Survey app menu on every module
install/upgrade. `g2p_survey` re-enables it (see `models/ir_module.py`), so the
Survey app stays at the top level and `g2p_survey` only nests an ODK submenu:

- `Surveys / Surveys`
- `Surveys / Participations`
- `Surveys / Questions & Answers`
- `Surveys / ODK Integration / ODK Users`
- `Surveys / ODK Integration / ODK Servers`

Because the un-hiding lives here, the native Survey menu is only visible while
`g2p_survey` is installed.

## Online Odoo Forms

Create and publish forms using the normal Odoo Survey UI.

The public form route is Odoo's native route:

```text
/survey/start/<survey_access_token>
```

Online responses created from that route are native `survey.user_input` records with:

```text
g2p_response_source = odoo
```

The public survey footer is customized to show:

```text
Powered by Enderase
```

## ODK Central Setup

Create an ODK Central server record from:

```text
Enderase Registry / Configuration / Survey / ODK Servers
```

Required fields:

| Field | Meaning |
| --- | --- |
| Name | Local display name |
| Base URL | ODK Central URL, for example `https://central.example.org` |
| API Email | ODK Central staff user email |
| API Password | ODK Central staff user password |
| Default Project ID | ODK Central project ID, usually `1` for the first project |
| Verify SSL | Enable for normal HTTPS deployments |

Use `Test Connection` to verify the credentials.

## Survey Delivery Mode

Open a native Odoo survey and use the `ODK` tab.

Delivery modes:

| Mode | Meaning |
| --- | --- |
| Odoo Online | Serve only through native Odoo Survey |
| ODK Offline | Push to ODK for offline collection |
| Online and ODK | Serve through Odoo and ODK |

Set:

- Delivery Mode
- ODK Server
- ODK Project ID, if different from the server default

## Push A Survey To ODK

On the survey form, click:

```text
Push to ODK
```

The module:

0. Resolves the target ODK project: a valid **ODK Project ID** is used as-is; otherwise, if **ODK Project Name** is set, a project with that name is reused or created on ODK Central (and its ID is stored back on the survey); otherwise the ODK server's default project is used.
1. Reads native Odoo Survey questions and their **ODK / XLSForm** configuration.
2. Builds an **XLSForm** (`.xlsx`) definition with `survey`, `choices`, and `settings` sheets.
3. Uploads it as a draft to ODK Central, which converts the XLSForm to an XForm server-side via pyxform.
4. Publishes the form.
5. Stores the ODK form ID, version, state, publish timestamp, last push time, and last error on the survey. The XLSForm itself is generated in memory from the questions on every push and is never stored/attached on the survey.

The generated ODK form ID defaults to:

```text
survey_<odoo_survey_id>_<slugified_survey_title>
```

If the survey has already been pushed, later pushes create a draft on the existing ODK form and publish it.

## ODK / XLSForm Question Configuration

Each survey question has an **ODK / XLSForm** tab that drives how it is emitted into
the generated XLSForm. The survey configuration is the single source of truth — no
file is uploaded.

| Field | XLSForm effect |
| --- | --- |
| `ODK Field Name` | `survey.name` (and the submission node name). Defaults to an auto slug. Use short snake_case, e.g. `admin_region`. |
| `ODK Appearance` | `survey.appearance` (e.g. `minimal`, `multiline`). |
| `ODK Relevant` | `survey.relevant` (e.g. `${occupation_profession}='other'`). |
| `ODK Constraint` / `ODK Constraint Message` | `survey.constraint` / `constraint_message`. |

### Choices from a model (dynamic, by code)

For `simple_choice` / `multiple_choice` questions, set **ODK Choice Model** to build
the choice list directly from an Odoo model **at push time** (so the form always
reflects current lookup records):

- `ODK Choice Value Field` (default `code`) → the choice `name` (stored value).
- `ODK Choice Label Field` (default `name`) → the choice `label` (display text).
- `ODK Choice Domain` / `ODK Choice Order` → optional filter/order of the records.

Because the value is the record **code**, imported submissions map straight back to
the source records by code (see `g2p_enderase_youth_registry`).

### Cascading selects

To make a select depend on a parent select (e.g. Region → Zone → Woreda), set on the
child question:

- `ODK Choice Filter Parent` → the parent question's ODK field name (e.g. `admin_region`).
- `ODK Choice Filter Column` → the extra choices-sheet column holding the parent code (e.g. `region_code`).
- `ODK Choice Parent Path` → dotted path on the choice model to that code (e.g. `region_id.code`).

This emits `choice_filter: <column>=${<parent>}` on the child and populates the
column for every choice row, so ODK Collect filters the child list by the parent
selection.

## Supported Question Types

| Odoo Survey Type | ODK Type | Import Behavior |
| --- | --- | --- |
| `char_box` | `string` input | saved as text answer |
| `text_box` | `string` input | saved as free text answer |
| `numerical_box` | `decimal` input | saved as numeric answer |
| `date` | `date` input | saved as date answer |
| `datetime` | `dateTime` input | saved as datetime answer |
| `simple_choice` | `select1` | saved as one suggested answer line (model-backed choices are read from the submission XML by code instead) |
| `multiple_choice` | `select` | saved as one answer line per selected option (model-backed choices are read from the submission XML by code instead) |

Unsupported for ODK export:

- `matrix`

Matrix questions can still be used online in Odoo Survey, but `Push to ODK` will stop with a clear error if the survey contains matrix questions.

## Choice Mapping

Choice values in ODK are generated from the native `survey.question.answer` records:

```text
a_<answer_id>_<slugified_answer_value>
```

This stable value lets imports map ODK answers back to native Odoo suggested answers. Avoid deleting and recreating choice answers after pushing a survey to ODK; if you change choices, push the survey again so ODK has the matching form version.

## Import ODK Submissions

On the survey form, click:

```text
Import ODK Submissions
```

The module:

1. Lists submissions from ODK Central for the pushed form.
2. Skips deleted submissions.
3. Skips submissions whose `instanceId` already exists in Odoo for that survey.
4. Fetches each submission XML.
5. Parses ODK XML values by generated question name.
6. Creates a native `survey.user_input` response.
7. Saves all answers as native `survey.user_input.line` records.
8. Stores raw ODK metadata and XML for auditability.

The import is efficient: existing submissions are looked up in a single query, and
only genuinely new submissions trigger an XML/attachment download.

Imported responses appear in:

```text
Surveys / Participations
```

Use the search filters:

- `Odoo Online`
- `ODK Offline`
- group by `Source`

### Submission Media Attachments

If a submission includes media (photos, signatures, audio), each file is downloaded
from ODK Central and stored as an `ir.attachment` linked to the `survey.user_input`
response. The response form shows an `ODK Media` smart button to open them.

### Scheduled Sync

A disabled cron `ODK: Import Survey Submissions` is included. Enable it under
`Settings / Technical / Scheduled Actions` to periodically import submissions for
every survey whose delivery mode is `ODK Offline` or `Online and ODK` and that has
been pushed. It calls `survey.survey._g2p_cron_import_odk_submissions()`.

## ODK Users

Create ODK users from:

```text
Enderase Registry / ODK Users
```

User types:

| Type | Use |
| --- | --- |
| Staff User | Creates or updates an ODK Central staff account using email/password |
| ODK Collect App User | Creates an app user token for ODK Collect field devices |

Workflow:

1. Create the ODK user record.
2. Select the ODK server.
3. Select allowed surveys.
4. Click `Create in ODK`.
5. Click `Assign Survey Access`.

### ODK Collect QR Code

For `ODK Collect App User` records that have been created in ODK, the form shows
an `ODK Collect Setup` section with:

- `ODK Collect Server URL` — the token-scoped URL (`<base>/v1/key/<token>/projects/<id>`).
- `ODK Collect QR` — a QR code that encodes zlib-compressed, base64-encoded ODK
  Collect settings.

On the device, open ODK Collect and choose `Configure via QR code`, then scan the
QR to auto-configure the server URL for that app user. No manual token entry is
needed.

### Revoking App Users

Click `Revoke App User` on an app user to invalidate its ODK Collect token in ODK
Central. The record moves to the `Revoked` state and its token is cleared. Each
lifecycle action is logged in the record chatter.

## Branding

The public survey layout inherits native `survey.layout` and replaces Odoo's promotion block with:

```html
Powered by <span>Enderase</span>
```

The survey navigation button remains in the same native Odoo footer block.

## Docker Compose

`survey` and `gamification` are baked into the image from official Odoo (see
`../odoo/Dockerfile`); only `g2p_survey` is mounted:

```yaml
- ./g2p_survey:/opt/odoo/customaddons/g2p_survey:ro
```

The registry Odoo service installs and updates:

```text
g2p_enderase_youth_registry,g2p_ati_embed,gamification,survey,g2p_survey,enderase_theme
```

After changing this addon, update it (bind mount picks up file changes; restart to
reload the running registry):

```bash
docker compose restart odoo
# or, to force a module upgrade:
docker exec enderase-odoo odoo -d enderase -u g2p_survey --stop-after-init && docker compose restart odoo
```

## Verification

Static checks:

```bash
python3 -c "import ast, pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('g2p_survey').rglob('*.py')]"
python3 -c "import pathlib, xml.etree.ElementTree as ET; [ET.parse(p) for p in pathlib.Path('g2p_survey').rglob('*.xml')]"
docker compose config
```

Runtime checks:

```bash
docker compose ps
curl -sSI http://localhost:8069/web/health
```

Inside Odoo, confirm these modules are installed:

```text
gamification
survey
g2p_survey
```

## Known Limits

- ODK Central credentials must be configured before push/import can be tested end to end.
- Matrix questions are not exported to ODK yet.
- Submission listing uses the ODK Central REST endpoint (all submissions, metadata
  only); very large forms may benefit from an OData cursor in the future.
- The generated XLSForm follows the native Odoo question set (text, decimal, date/dateTime, select_one, select_multiple) plus per-question ODK configuration: model-backed choices (by code), cascading selects (`choice_filter`), `relevant`, `constraint`, and `appearance`. Question groups and multilingual labels are not emitted yet.
