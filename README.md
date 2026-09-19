# Kuchipudi Academy — website, student portal & admin portal

A Streamlit application for a classical Kuchipudi dance school: a public website,
a student portal, and an admin portal that controls every part of both.

All data lives as JSON inside this **private** repository (`data/`), written
through the GitHub Contents API — so nothing is lost when Streamlit Cloud
restarts the app, and every change is a commit you can look back through.

---

## What's in it

**Public website**

- Hero home page with live counts, why-us cards, guru introduction, upcoming events, testimonials
- About — the form's history and the first-year syllabus
- Classes — batches, levels, timings, seats and a fee table
- Videos — publicly visible practice clips (YouTube / Drive / Instagram / mp4)
- Gallery — photographs and Instagram reels
- Events — upcoming and past performances
- Contact — details plus an enquiry form that lands in the admin portal
- Register — online enrolment; the student picks their own portal password

**Student portal** (`Student` tab)

- Attendance percentage, class-by-class record
- Fee status, history and outstanding balance
- Practice videos filtered to their batch or level
- Announcements from the guru
- Profile and self-service password change

**Admin portal** (`Admin` tab) — everything is editable here

| Tab | What it does |
|---|---|
| Dashboard | Students, pending registrations, fees collected/outstanding, enquiries, per-batch counts |
| Registrations | Approve (creates the student + login) or reject, assign to a batch |
| Students | Search, filter, add, edit, reset passwords, deactivate, delete, CSV export |
| Batches | Create/edit/delete batches, timings, seats, fees |
| Attendance | Mark a whole batch for a date, per-student summary, CSV export |
| Fees | Generate a month's invoices per batch, mark paid, one-off charges, CSV export |
| Videos | Add links, set public or batch/level-restricted, live preview |
| Gallery | Image URLs and captions |
| Events | Performances with dates, venues, publish toggle |
| Testimonials | Quotes with publish toggle |
| Announcements | Messages to all students or a single batch, pinning |
| Enquiries | Website enquiries, mark handled, CSV export |
| Site content | Academy name, colours, hero text, guru bio, why-us cards, contact details, social links, fee visibility, registration open/closed |
| Settings | Change admin password, storage status, full JSON backup and restore |

---

## First login

```
username: admin
password: kuchipudi@2026
```

Change it immediately under **Settings → Change admin password**. You can also set
a break-glass password in secrets under `[admin] password`.

---

## Deploying on Streamlit Community Cloud

1. Push this repo (private is fine — Streamlit Cloud can deploy private repos).
2. Go to <https://share.streamlit.io> → **Create app** → pick this repo,
   branch `main`, main file `app.py`.
3. Under **Advanced settings → Secrets**, paste:

```toml
[github]
token  = "github_pat_..."          # fine-grained PAT, Contents: Read & write, this repo only
repo   = "your-username/your-repo"
branch = "main"

[admin]
password = "a-long-password-you-choose"
```

4. Deploy. The app seeds `data/*.json` on first run.

Without the `[github]` secrets the app still runs, but writes go to local files
that Streamlit Cloud wipes on restart — so set them before real use.

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` if you want
local runs to read and write the repo instead of local files.

---

## Layout

```
app.py                  router, navigation, bootstrap
lib/store.py            GitHub-backed JSON store (+ local fallback)
lib/auth.py             PBKDF2 password hashing, admin & student sessions
lib/ui.py               theme, CSS, shared components
lib/seed.py             default content, seeded on first run
views/public.py         public website pages
views/student.py        student portal
views/admin.py          admin portal
data/*.json             the database
```

## Notes on data

- Passwords are stored as PBKDF2-SHA256 hashes, never in plain text.
- Because the repo is private, `data/` is private too — keep it that way.
- **Settings → Download full data backup** gives you a single JSON of everything.
