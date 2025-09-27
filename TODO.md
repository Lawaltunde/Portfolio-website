# Project TODO

A phased roadmap of pending work. Completed items have been removed from this list.

## Feature 1 — Contact & Admin Communications (Core)

- [ ] Phase 0: Secrets and environment setup
  - [ ] Add `.env.example` with SMTP variables: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `EMAIL_TO`
  - [ ] Ensure `.env` is git-ignored (already covered by `.gitignore`)

- [ ] Phase 1: Email-only contact flow
  - [ ] Send contact form submissions to Gmail via SMTP (App Password)
  - [ ] (Optional) Send auto-acknowledgement email to the sender

- [ ] Phase 2: Admin reply UX
  - [ ] Add "Reply via email" action in the admin dashboard (mailto: link or SMTP send)
  - [ ] Remove/disable `/create_admin` route after first use

- [ ] Phase 3: Spam protection
  - [ ] Add a honeypot field to the contact form
  - [ ] Add basic IP rate limiting for the submit route
  - [ ] (Optional) Integrate reCAPTCHA v2/v3 later

- [ ] Phase 4: Validation & resilience
  - [ ] Validate/sanitize `user_name`, `email`, `subject`, and `message`
  - [ ] Graceful error handling/logging if email sending fails

- [ ] Phase 5: Consistency & documentation
  - [ ] Align route to `/submitted_form` across code and templates
  - [ ] Update README with Gmail App Password steps, env variables, and run instructions

## Feature 2 — Email polish (Optional)
- [ ] Phase 6: Email templates
  - [ ] Use simple HTML templates for notifications and acknowledgements

## Feature 3 — Cloud Backend (Backlog)
- [ ] Phase 7: Supabase migration (messages/users)
  - [ ] Point SQLAlchemy URI to Supabase Postgres
  - [ ] Migrate any existing local data if needed
  - [ ] Verify admin login/messages flow remains intact

## Feature 4 — Blog (Backlog)
- [ ] Phase 8: Blog section + CRUD
  - [ ] Public blog listing and post pages
  - [ ] Admin create/edit/delete posts
  - [ ] Basic SEO (titles, meta, slugs)

## Feature 5 — Portfolio UX Enhancements (Backlog)
- [ ] Phase 9: Downloadable resume button/file
- [ ] Phase 10: Dark/light mode toggle with preference persistence
- [ ] Phase 11: Project filtering/search (client-side; keep project data static)

## Feature 6 — Growth & Localization (Backlog)
- [ ] Phase 12: Testimonials/newsletter
  - [ ] Static testimonials or simple submission form
  - [ ] Newsletter signup (provider optional later)
- [ ] Phase 13: Multilingual support (i18n-ready templates, language switcher)

---
Notes:
- Keep project data static (images in `static/`, links point to GitHub) unless we explicitly change course.
- Use environment variables for all secrets; never commit `.env`.
- When a phase is completed, remove it from this file to keep TODO current.
