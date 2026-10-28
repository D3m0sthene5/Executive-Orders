# Owner decision: pushes must not wait on the pipeline (2026-10-28)

Given by the owner, Danny, to Claude on 2026-10-28: he wants to be able to add any single thing to GitHub
without it taking 45 minutes every time because every part of the project is re-checked.

Carried out the same day in PR #68:

- A push starts a run only when it changes a job's own folder or the runner, and runs only the edited job,
  with nothing downstream. Uploads, claims, notes, research files and rulings start no jobs on push.
- A sweep every three hours on `main` runs the jobs whose `triggers.txt` patterns match paths changed since
  the previous sweep, plus their consumers; web-search jobs that run only as consumers get 12 requests.
- The daily run (09:17 UTC) and manual runs are unchanged.
- Road tests run once per change (pull requests and pushes to main), not twice per pull-request commit.

Consequence: derived outputs such as the readiness tracker update within about three hours of a change, or at
once if someone starts the job by hand. The 2026-10-20 continuous-run rule that a coordinator must not push while
"Run jobs" is in progress matters far less, because pushes no longer start long runs. No codebook, status or
count changes. Certified: 0.
