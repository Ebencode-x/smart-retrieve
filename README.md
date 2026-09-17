# MUST Exam Entry Verification System

An incident-response layer that lets students who have lost or misplaced their physical university ID card still gain verified, secure entry to their exams — without relying on a single gatekeeper, office, or manual process that can create bottlenecks and delays.

---

## The Problem

Every exam season, some students discover — sometimes days in advance, sometimes on the morning of the exam itself — that their physical university ID card is lost or misplaced. Without it, a student who is otherwise fully eligible to sit an exam risks being turned away at the door.

The traditional fallback (report to one specific office, wait for a manual note, hope the right person is at the right gate) does not scale well under real exam-day conditions: queues are already long, gate staff often have no phones or system access, and invigilators are occupied inside the exam room. A single point of failure in this process directly threatens a student's academic progress through no fault of their own.

## What This System Adds

- **A structured reporting channel.** Students register a lost/forgotten ID report against a specific upcoming exam, from their own authenticated account, the moment they realize it's missing — not at the exam room door under pressure.
- **Automatic routing by urgency.** The system calculates, from the time remaining before the exam, which of three verification tiers applies — so early reports get handled the simple, low-tech way (a printed list), and last-minute emergencies get a real-time digital path, without anyone having to decide this manually.
- **A verification method that works without prior knowledge of the student.** Any authorized staff member can confirm a student's identity and eligibility on the spot, even if they've never met that student before, using a time-limited digital pass plus the student's registration details displayed on screen for a visual cross-check.
- **Accountability without heavy-handed enforcement.** Repeat reports are visible to staff, and every report carries a signed declaration — so misuse is discouraged and traceable, without building intrusive AI-based fraud detection that this project's scope doesn't call for.

## What This System Deliberately Does Not Do

- It does not replace the physical ID card as the primary means of identification.
- It does not determine exam *eligibility* (registration status, fees, course enrollment) — that responsibility stays with the university's system of record, SIMS (see below).
- It does not integrate with MUST's official student registry in this version — see **Assumptions and Limitations**.

## Relationship to SIMS

This system is deliberately scoped as a companion to the Smart Inventory Management System (SIMS), not a replacement for it:

- **SIMS is the system of record** — it determines whether a student is eligible to sit a given exam at all (registration, fee clearance, course enrollment).
- **This system is an incident-response layer** — it exists only for the minutes or hours a student has valid entry rights but no physical proof of identity, and lets any authorized staff member verify them on the spot instead of the process depending on one gatekeeper.

## Who Uses It

| Role | What they do |
|------|---------------|
| **Student** | Registers/logs in, reports a lost or forgotten ID against a specific exam, and — if the report falls into the same-day emergency tier — generates a one-time digital Clearance Pass on their phone. |
| **Security / Invigilation staff** | Registers with a shared access code, creates exam records, views the printed exception list for early reports, and verifies same-day digital passes in real time at the point of entry. |

## Core Design: The Three-Tier Verification Model

Verification routing is based on how much time remains before the exam, not on any single hard cutoff:

| Tier | Timing | How it's handled |
|------|--------|-------------------|
| **1** | 48+ hours before the exam | Student appears on a pre-printed exception list per room; gate staff check names by hand — no technology needed at the door. |
| **2** | 24–48 hours before the exam | Same printed exception list, generated up to a defined cutoff time. |
| **3** | Under 24 hours / same-day | Routed to an invigilator or exam coordinator with system access, who verifies the student in real time via a Temporary Digital Exam Clearance Pass. |

Reports are always received and recorded in real time regardless of tier — only the *verification method* changes based on how much time is left before the exam.

## Clearance Pass Verification Flow (Tier 3)

1. The student, logged into their own account, selects their unresolved same-day report and generates a Clearance Pass.
2. The system issues a time-limited TOTP code (valid for 10 minutes) tied to that specific report.
3. The student shows the code on their phone to any staff member with the security role — this is not restricted to one specific invigilator or room.
4. Staff enter the Pass ID and code into the system. On success, the system displays the student's registration number and exam context (course, room, date) so staff can perform a final visual/face-to-face cross-check.
5. The pass is single-use — once verified, it cannot be reused.

## Anti-Fraud and Accountability Measures

Deliberately kept simple, with a human always making the final call rather than the system auto-blocking anyone:

- Reports distinguish **"lost"** (location unknown) from **"forgotten"** (location known, e.g. left at home) — separating genuine loss from casual forgetfulness.
- Every report requires a **signed declaration** confirming its accuracy, with a stated warning that false reports may lead to disciplinary action.
- **Report history is visible to staff** by registration number, so repeat reporters can be flagged for extra scrutiny.
- Students can **self-resolve** their own report once they recover their ID.

## Assumptions and Limitations

- **No live registry integration.** In a production deployment, this system would integrate directly with MUST's official student registry (and with SIMS) to confirm exam eligibility automatically. For this project, verification instead relies on account-login authentication — a student must be logged into their own registered account to report a loss or generate a pass — plus human visual confirmation by staff at the point of verification.
- **Real-world context.** MUST's physical UE (university entry) cards and CA (continuous assessment) card checks remain the primary, established verification layers. This system is designed to supplement them for the specific case of a missing card, not replace them, and assumes a simplified verification model appropriate to a two-week field project scope.
- **Verification is not room-bound.** Any authorized security-role account can verify any student's pass, regardless of which room or exam it relates to. This is intentional — it removes the single-gatekeeper bottleneck that motivated this project — at the cost of not restricting *who specifically* can perform a given verification.

## Technical Stack

| Layer | Technology |
|-------|------------|
| Backend framework | Python — FastAPI |
| ORM / Database access | SQLAlchemy |
| Database | PostgreSQL (hosted on Supabase) |
| Authentication | JWT (python-jose), password hashing via passlib + bcrypt |
| One-time passcodes | TOTP (pyotp), 10-minute validity, single-use |
| Frontend | Plain HTML, CSS, and vanilla JavaScript — no framework, for speed and simplicity |
| Backend + database hosting | Render (free tier) |
| Frontend hosting | Vercel (split from the backend specifically to avoid Render's free-tier cold-start delay affecting the user-facing pages) |

## Project Status

Built as an Industrial Practical Training (IPT) / Field Project at Mbeya University of Science and Technology. Core backend (authentication, reporting, tier computation, exam management, Clearance Pass issuance and verification) and full frontend (registration, login, dashboard, reporting, exam list, exception list, Clearance Pass generation and verification) are complete and verified end-to-end against the live deployment.
