# Data folder

| File | What it is |
|---|---|
| `dummy_survey_data.csv` | **DUMMY DATA.** 15 rows invented by hand by the team only to test the app. Not collected from any student, not a research result. All IDs start with `DUMMY_`, and the app shows a red warning when it detects them. |
| `survey_template.csv` | Empty template with the required header. |
| `survey_data.csv` | Survey responses, anonymised as `R01`–`R20` (n = 20). R06–R20 rated fatigue on a 1–5 scale; converted to 1–10 with `1 + (x − 1) × 9/4` (1 → 1, 3 → 5.5, 5 → 10). Extra column `group` is left empty; the app ignores it. |

## Column definitions (must match the survey questions)

| Column | Meaning | Allowed range |
|---|---|---|
| `student_id` | Anonymous code (e.g. `R01`). **Never use NIM or names.** | text |
| `sleep_hours` | Average sleep per day over the last 7 days (hours) | 0-12 |
| `outstanding_assignments` | Number of unfinished assignments due within the next 7 days | 0-15 |
| `screen_time_hours` | Average **non-academic** screen time per day over the last 7 days (entertainment, social media, games) | 0-16 |
| `meals_per_day` | Average number of main meals per day over the last 7 days | 0-6 |
| `self_reported_fatigue` | "How tired have you felt this week?" 1 = not tired at all, 10 = extremely tired | 1-10 |

Rows with missing values or values outside these ranges are dropped by the app and reported (never silently changed).
