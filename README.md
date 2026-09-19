# Kuchipudi Academy

A Streamlit site for a classical Kuchipudi dance school: a public website, a
student portal, and a hidden admin console that controls every word of both.

| Who | How they get in | What they can do |
|---|---|---|
| Visitor | Just open the site. No login, ever. | Browse classes, watch videos, register for a batch, send an enquiry |
| Student | Sign in on the **Student** tab once their registration is approved | Attendance, fees, practice videos, announcements |
| Admin | Add `?view=admin` to the URL and enter the password | Edit every word, price, photo and setting; manage students, fees and attendance |

Nothing is hard-coded. Academy name, email, phone, hero text, guru biography,
section headings, syllabus, fee notes and colours are all edited from the admin
console.

## Where the content lives

Content is stored in this same **private** repository, on a separate branch
called `content`:

```
content branch
└── data/
    ├── site.json           name, hero, guru, contact, colours, switches
    ├── batches.json        classes, timings, seats, fees
    ├── students.json       enrolled students (passwords are PBKDF2 hashes)
    ├── registrations.json  pending sign-ups awaiting approval
    ├── attendance.json     per-class attendance
    ├── fees.json           invoices and payments
    ├── videos.json         practice and public videos
    ├── gallery.json        photographs
    ├── events.json         performances
    ├── testimonials.json   quotes
    ├── announcements.json  messages to students
    ├── enquiries.json      contact-form messages
    └── visits.json         website visitor counts
```

Using a separate branch matters. Streamlit Community Cloud watches the branch it
deployed from (`main`), so saving content never reboots the live site. You get a
full version history of every edit for free, and **deleting the `content` branch
erases all stored data in one action while leaving the code untouched**.

The branch is created automatically the first time the app saves anything.

## Setup

### 1. Create a GitHub token

GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
tokens → Generate new token

- Repository access: **Only select repositories** → this repo
- Permissions: Repository permissions → **Contents: Read and write**
- Expiration: whatever you're comfortable replacing

Copy the token — GitHub shows it only once.

### 2. Deploy on Streamlit Community Cloud

Go to <https://share.streamlit.io>, sign in with GitHub, **Create app**, pick
this repo, branch `main`, main file `app.py`. Open **Advanced settings →
Secrets** and paste:

```toml
admin_password = "pick-something-long-and-private"

[github]
token  = "github_pat_…"
owner  = "your-github-username"
repo   = "kuchipudi-academy"
branch = "content"
```

Deploy.

### 3. Fill it in

Open `https://your-app.streamlit.app/?view=admin`, enter the password, and work
through the tabs — **Site content** first, then **Batches**.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Without secrets it runs against a local `local_content/` folder so you can try
it offline. That folder is temporary and gitignored; only the GitHub backend
stores anything permanently.

## Admin console

| Tab | What it does |
|---|---|
| Dashboard | Website visitors (all time, today, 7 and 30 days, daily chart), students, pending registrations, fees collected and outstanding |
| Registrations | Approve — which creates the student and their portal login — or reject |
| Students | Search, add, edit, reset passwords, deactivate, delete, CSV export |
| Batches | Create and edit batches, timings, seats, fees |
| Attendance | Mark a whole batch for a date, per-student summary, CSV export |
| Fees | Generate a month's invoices, mark paid, one-off charges, CSV export |
| Videos | YouTube, Drive, Instagram or mp4 links; public or restricted to a batch/level |
| Gallery / Events / Testimonials / Announcements | Content with publish toggles |
| Enquiries | Contact-form messages, mark handled, CSV export |
| Site content | Every word on the public site, plus colours and switches |
| Settings | Storage status, full JSON backup and restore |

## Security

- The admin password is compared in constant time, is read only from Streamlit
  secrets, locks out for five minutes after five wrong attempts, and the signed-in
  session expires after eight hours.
- The console is not linked from anywhere on the public site.
- Student passwords are stored as PBKDF2-SHA256 hashes, never in plain text.
- All stored content is HTML-escaped before it reaches the page, so a visitor
  cannot inject scripts through the enquiry or registration forms.
- The repository is private, so the `content` branch and every student record on
  it are private too.

## Layout

```
app.py              router, navigation, hidden admin route
lib/store.py        JSON store on the content branch (+ local fallback)
lib/auth.py         admin password, student logins, session expiry
lib/visits.py       visitor counting, buffered
lib/ui.py           theme, CSS, shared components
lib/seed.py         default content, seeded on first run
views/public.py     public website
views/student.py    student portal
views/admin.py      admin console
```
