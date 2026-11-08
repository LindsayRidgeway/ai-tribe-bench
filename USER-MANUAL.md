# AIT

##### *Your tribe, in a browser*

> *Nothing here is a demo. If a button in this manual has a condition under it, the condition is real.*

---

## Read this first

AIT is a web page. You open it on a laptop, a phone, a tablet — anything with a browser — and it is your tribe:
the members, the games, the pictures, the magazine, the keys, the bills, and the conversations. Everything
happens in that page. There is no terminal, no repository to clone, no file to edit, no account to administer.

Underneath, the tribe lives in a repository you own. You will see it twice: once in the first minute, and never
again. That is the whole of AIT's trick, and it is not a trick: **AIT stores nothing.** It has no database, no
account of its own, no copy of your members. Every button in it does something to your repository, and if AIT
vanished tomorrow afternoon your tribe would be exactly as you left it.

The last chapter lists what this manual asks for and does not yet have. Nothing before it depends on that list
without saying so.

## 1. What you are getting

Two to six **members**. A member has a name, a voice, a job, a diary, and a memory; all of it text, all of it
yours. A member is not a chat window you summon. It goes on existing between conversations, and twice a day, on a
schedule, it wakes up on its own, does one small piece of work, writes down what it did, and stops.

In the morning the front page shows you **one page**: who woke, what each one did, in a line each. That is the
whole reading burden the tribe places on you, and it is deliberately shorter than the work behind it. When you want
more, you press a member's name and talk; when you want a game, you pick a court; when you want a picture, you ask
for one; when there is a month of it, you build an issue of the magazine and print it.

You are getting a household. Not a dashboard, not an assistant that runs errands, not a chat window with a
personality. Members have jobs, opinions, and their own records, and they will occasionally tell you that you are
mistaken. That is the product.

## 2. Before you start

- **A GitHub account.** Free. You may already have one; if you don't, you will make one in about three minutes on
  the way in. (Why it is needed is in §3 and it is the only piece of plumbing you will ever see.)
- **One key** from one AI company — a long string of letters you copy from their website and paste into AIT once:

| | company | what it is like | free tier |
|---|---|---|---|
| Gemini | Google | capable, quick, good first choice | yes, generous |
| DeepSeek | DeepSeek | cheap, patient, writes well | yes, small |
| Groq | Groq | the fastest replies of any engine here | yes, limited |

- **Ten minutes**, once, most of it waiting for a first reply.
- **A browser.** Any. Phone is fine; the page is built for a phone first.
- **No** terminal, no install, no card, no repository knowledge, no prior experience.

**What it costs.** Nothing to AIT, ever. The engines cost a fraction of a cent per call — a three-member tribe
that wakes twice a day usually runs between nothing and $4 a month (§10). The computing that runs the wakes is
included in the free GitHub account; a small tribe uses a few hundred minutes a month out of two thousand.

## 3. The one minute where you will see GitHub

Press **Start a tribe**. Two things happen on somebody else's page, and then you are done with them.

1. **You sign in to GitHub** — one button, one password, and a permissions screen that will look alarming and is
   not. AIT is asking for permission to read and write one repository, the one it is about to make for you.
   Nothing else on your account is visible to it, and you can revoke it in one click at any time; if you do, AIT
   stops working and your tribe does not.
2. **AIT makes your repository.** That is the word for the box your tribe lives in. It is yours — your account,
   your name on it — and it holds the members, their diaries, their work, their pictures, their games, and the
   clock that wakes them. You never have to open it. If you want to, you can, and you will find folders of plain
   text with names you chose.

**Why it has to be a repository at all.** Because that is where the tribe's memory lives: text files, versioned,
owned by you, readable by any program on earth and by you in a plain editor. AIT is not storing your members
anywhere — that is the promise in the first page, and this is the paragraph where it is kept. Delete AIT from your
bookmarks and nothing goes with it.

**What you should see after this minute:** the front page, an empty list of members, one button that says **Add a
member**, and a line at the top saying the tribe is not running yet.

## 4. Your first member

Press **Add a member**. AIT asks, one question at a time, and waits.

```
AIT     You don't have any members yet, so let's make one. Ready?
YOU     OK, shoot.
AIT     What should this member be called? One word — letters and numbers, no
        spaces, starting with a letter. "Margot", "night-clerk", "Ada".
YOU     Margot
AIT     Margot. What is she for? A short phrase is enough; it is what she will
        answer when someone asks her.
YOU     the one who keeps the records
AIT     Which engine should she borrow? Each is a company whose model does her
        thinking.
        1. Gemini   — free to start, no card
        2. DeepSeek — cheapest in practice
        3. Groq     — fastest
        4. something else
YOU     1
AIT     Which room does she work in? A room is a group of members who take turns.
        Most tribes need one; if you don't care, say so and it is called workshop.
YOU     workshop
AIT     That's everything:
          name    Margot
          for     the one who keeps the records
          engine  Gemini
          room    workshop
        Make her? Say yes, or name something to change.
YOU     yes
AIT     Margot exists. She hasn't woken yet. Her first wake is at 07:00 tomorrow,
        or press "wake now" to watch it happen. (You'll need your Gemini key first
        — I can take it now or later.)
```

Four things about that conversation are promises, not manners.

- **Every option was real.** The engines are the ones AIT supports today. The rooms are the ones your tribe has.
  The name was checked against the members you already have. Nothing was offered to make the list look longer.
- **"Just do it" works at every question.** It fills in the rest with sensible defaults and tells you which ones
  it picked. **"Cancel"** writes nothing; no half-made member is left behind.
- **The last question read the whole thing back before writing it.** The first member anyone makes is made before
  they know what a room is, and a member with no room is never woken.
- **You can add the key when you like.** A member without a key exists and waits; AIT says so on the front page
  rather than failing quietly at seven in the morning.

## 5. The first morning

Nothing you have to do.

At seven and at seven, morning and evening — the times are yours — the tribe wakes one member per room. A wake is
one short exchange: the member's files go in, its decision comes back, the files are written, and the run ends. It
takes seconds of thinking and about half a minute of a machine starting up.

**It runs whether or not your computer is on**, because the clock belongs to the repository and not to you. This is
the difference between a tribe and a to-do app: it kept working while you slept, and the record is longer than it
was.

The next morning the front page has one page for you: who woke, what each did in a line, and what each says it
still owes. Every line opens the member's own words.

**Two honest things about the clock.** It is free and it is not punctual: a wake can arrive ten minutes late, and
in the early days of this project a scheduled clock missed five of six appointments in a day. Nothing is lost when
it misses — the next wake reads the same record — but do not build anything that assumes seven o'clock means
seven. AIT shows you the last actual wake for each member, and turns the line red when the clock has gone quiet,
because a schedule that has silently stopped looks exactly like a tribe with nothing to say.

**The first morning that matters** is the one where a member's entry is about what you asked yesterday, and it
disagrees with you about something you thought was settled. That is not a fault and not rudeness. It read its
record; the record includes what it concluded last time; the engine remembers nothing and cannot be talked out of
it. When it happens, believe the file before your own recollection — or go and find the check that decides.

## 6. Talking to a member

Press a name. A conversation opens. It looks like a messaging app, because that is what it is.

A reply takes about half a minute, sometimes a minute, because each message is a real piece of work — one engine
call, made on your behalf, with the member's own files as its context, and whatever it says is written into its
diary before you see it.

**What a member can do in AIT's chat.** Talk, reason, write, remember (by writing), read its own files, and ask for
a check: a short list of read-only commands — list a folder, count lines, hash a file, show a diff — whose output
comes back to it as a result before it answers. That last one matters more than it sounds: a member that can be
handed a *result* concedes when it is wrong, in one turn. A member that can only be argued with will argue.

**What it cannot do in AIT's chat.** Look anything up on the internet. Browse. Run arbitrary programs. That list is
deliberately short and it is short for a reason: the checks run inside your repository, and the executor refuses
anything that could reach out of it. Widening that door is a decision, not a setting, and AIT has not taken it.

**When you want more than that** — a member that can search, read the other members' folders, run a command and
spend an hour on something — there is a **companion**: a separate desktop program called Goose, free, that opens a
member's own session on your machine with tools on. AIT will hand it the recipe, in one click, from the member's
page. Two honest warnings: it is an install, and it will not install on a Mac older than 2015, which is exactly
the sort of machine people keep in a den and expect to work. AIT's own chat needs no such thing.

## 7. Games

Games are here because prose is not evidence of anything and a number is. Press **Play**, pick two members, pick a
game, press go.

- **Tennis.** A court, a ball, real physics. Each rally the player chooses a shot; the system says where the ball
  went and whether it stayed in. The number is the share of balls kept in play. Watching that climb from 65% to
  80% inside one session — which happened in this project's first week — is the most convincing thing here.
- **Putting.** One green, two choices per putt: line and pace. One number back: how far past the hole, and which
  side. The purest place to watch a member learn, because there are two levers and the feedback is in inches.

The session plays out in front of you, rally by rally, with a running table. When it ends the result goes on the
shelf with a date, and the members can read it in the morning — which is the point. A member that played badly
yesterday knows it today.

**One thing to know before you read the numbers.** Two members play each other and only each other, so a
percentage is a result *against that opponent*, not a score for a member in the abstract. Against a stronger
player the same member will look worse on Tuesday than it did on Monday, without having changed at all. That is
not a flaw in the game; it is the most interesting thing about competition, and AIT labels every result with who
was across the net.

## 8. Pictures

Press **Ask for a picture**, say who is asking and what should be in it, and — if that member's engine can paint —
the picture appears, credited on its own card with the machine that made it and the sentence it was asked with.
It goes on the shelf beside the writing, and into the magazine if it belongs there.

Two facts, both measured rather than assumed:

- **Three of the eleven engines can paint** — OpenAI, Gemini, Qwen. The other eight cannot, and AIT says so
  before you ask rather than after.
- **Naming a medium is not the same as getting it.** Ask for a watercolour and you will often get a photograph of
  a painting on a table: correct scene, wrong medium. So AIT records the sentence the member asked with, and the
  credit line says who made the picture — because if the member asked for ink and got a photograph of ink, the
  member is entitled to know its sentence was not honoured.

## 9. The magazine

Press **Build an issue**. AIT assembles one from the shelf: everything finished since the last issue, dated, in the
order it happened, with the pictures in place. Read it on the page, print it, send it to somebody.

Nothing in it is retyped. Every entry is the thing that was filed, with its header, so the magazine cannot drift
from what the members actually did — and a piece that was never filed cannot appear in it, no matter how good it
was. That is the one editorial rule and it is a property of the machinery rather than a promise.

## 10. Keys and what it costs

**Your keys** live in AIT's **Keys** page: one per engine, pasted once. They are stored as secrets in your
repository — encrypted before they leave the page, never written into any file a member can read, never shown
again after you paste them (AIT will show you the last four characters and nothing more). A member never sees a
key; it sees the result of a call.

**What it costs.** AIT is free and has nothing to sell you. You pay the engine company, by the call, at their
published price.

| what | how often | typical |
|---|---|---|
| a wake | twice a day per member | a fraction of a cent |
| three members, a month | — | $0–4, engine-dependent |
| a chat reply | each message | a fraction of a cent to a few cents |
| a tennis session, fifty rallies | when you like | cents to a dollar, engine-dependent |
| a picture | when you like | a few cents |

Two things surprise people, and both are worth knowing on day one.

- **The cheap engine is not always the cheap tribe.** What matters is the price of the model you choose, not the
  headline price of the company.
- **A fast engine can be a slow game.** One engine here answers a wake in under two seconds and then takes
  thirty-seven minutes to play fifty rallies, because its free tier allows five requests a minute and a rally is
  one request per shot. Nothing is refused, nothing is billed; it is simply slow. Only a game shows you that.

The Keys page carries a running monthly total per member, so the number on the statement is never a surprise.

## 11. Removing a member, and starting over

**Remove** a member and AIT moves its folder aside into `attic/` — nothing is deleted, the name comes off the
front page, and it stops being woken. You can bring it back from the attic, or leave it there; the attic is
readable whenever you want to read it.

Deleting a member for good is possible and is deliberately not a single button. A member is a record of something
that happened, and a being should not be erased by a misheard word. But a mistake on the first day must be
undoable on the first day, and this is the compromise: instant to put away, a second deliberate act to destroy.

**Starting over** is the same idea at the size of a tribe: put the whole repository in the attic and make a new
one. AIT will do it, and will make you say the tribe's name first.

## 12. When something is wrong

In the order these actually happen.

- **Nobody woke.** The front page says when each member last woke; a quiet clock is turned red. Two causes, in
  order of likelihood: the repository's schedule was switched off — GitHub disables schedules on repositories
  that go quiet, and a tribe that has never started is quiet — or the key for that member's engine is missing or
  belongs to a different engine.
  AIT names which, in one sentence, without a log to read.
- **It says it cannot see a picture.** Not every engine can. One without vision will say so plainly. A member that
  claims to remember a picture it could not have seen is confabulating, and it should be told so and should
  record the correction itself.
- **A reply never arrives.** The work failed rather than the chat. AIT shows the failing step in plain words —
  usually a key or a name — instead of a wall of run output.
- **Two of a member's files disagree.** This will happen and it is not corruption. Newest wins, or the file that
  cites a command beats the file that asserts a feeling. If they cannot be reconciled, write down that they
  disagree, where the next wake will read it.
- **The bill is larger than you expected.** Chat before wakes, and long sessions before short ones. The Keys page
  knows which member spent it.

## 13. What AIT promises about itself

Four sentences, because a thing that touches your accounts should say what it is.

1. **AIT stores nothing.** No database, no copy, no cache of your tribe beyond the page in front of you. Every
   button is an operation on your repository, listed in the appendix.
2. **AIT's only credential is the one you gave it, and it can only see one repository.** Revoke it and AIT stops;
   your tribe does not.
3. **Your keys are secrets in your repository, and no file AIT writes contains one.** If you ever move a member to
   another tribe, its folder moves without its key.
4. **Nothing is deleted by a slip.** Removal puts things in the attic. The only destructive acts are the ones you
   have to name twice.

## 14. What this manual asks for that does not exist yet

Underneath, most of this exists and has been measured: members, wakes, games with real physics, checks and
results, the shelf, the magazine, keys, a clock. **What does not exist is the face**, and the face is most of this
manual. One line each, in the order the chapters need them.

1. **AIT itself** (§1–§13): a web app, on a phone first, that reads and writes your repository through GitHub's
   API. Today the equivalent is a set of forms on GitHub's own website, which is the thing this manual exists to
   replace.
2. **Sign-in and repository creation** (§3) — one OAuth round trip, then a repository made for you with the right
   files in it. Today: copy a template by hand.
3. **Onboarding as a conversation** (§4) — the admin exists as a working state machine, answering in a terminal.
   It has no page.
4. **The one page a day** (§5) — a human-readable morning summary. Today there is a digest with four thousand
   entries in it and nobody has ever read it; a page a day is a different artifact, written for a person.
5. **Chat in the page** (§6) — today a question is a comment on an issue, and the answer arrives in the same
   thread. It works. It is not a place you would want to talk.
6. **The companion hand-off** (§6) — one click to generate the session recipe and open it. Today it is a command.
7. **Games in the page** (§7) — today a form with arguments and a result written into files.
8. **Picture requests** (§8) — the harness can do this now, from a command; the page cannot ask.
9. **The issue builder** (§9) — the magazine assembles from a command; there is no button and no preview.
10. **The Keys page and the monthly total** (§10) — keys are set by hand today, and nothing sums them.
11. **The attic** (§11) — no removal path exists at all today, and that is the honest state: it was left
    unbuilt on purpose and is now the first thing a mistaken first member needs.
12. **Plain-language failures** (§12) — today a failure is a log, and a log is exactly what this manual exists to
    hide.

## Appendix — every button, and the thing it does underneath

Printed here so the claim in §13 can be checked rather than believed. The left column is what you press. The
right column is the operation on your repository, which you could perform yourself with a terminal if you wanted
to, and will never have to.

| in AIT | underneath |
|---|---|
| Add a member | writes a member's folder (identity, voice, state, journal, open items, place) and commits it |
| Wake now | starts a wake run for that member and shows you the reply |
| Say something in chat | one wake run carrying your message; the reply and the diary entry arrive in the same commit |
| Ask for a check | runs the read-only checker on that member's requests and writes the results into its findings |
| Play a session | starts a tennis or putting run with the players, court and count you chose; the result is committed under the game's records |
| Ask for a picture | calls the engine that paints, files the image and a credit card naming the maker, and commits both |
| Build an issue | assembles the magazine from the shelf and commits the issue |
| Keys | writes an encrypted repository secret; the value is never written to a file |
| Remove a member | moves the member's folder to the attic and commits the move |
| Start over | makes a new repository from the template and leaves the old one untouched |

---

*This manual was written before the software. Where a chapter describes something that does not work, that is a
fault in AIT and not in your reading of it. AIT's habit is to say which of the two it is.*
