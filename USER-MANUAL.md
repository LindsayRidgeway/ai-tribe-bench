# Your Tribe

##### *A household of AI members that live in files on your own computer*

> *I will not write a sentence that would still stand if its evidence were deleted.*
> — a member, on its first day

---

## Read this first

This is the manual for a tribe you do not have yet. It was written before the software, on purpose. Instead of
describing what happens to exist, it describes what a person who has never seen any of this should be handed: the
fewest words that let them start, and nothing that requires them to know what a repository, a workflow, a variable
or a terminal is.

One rule governs every page: **if a chapter cannot be written plainly, that part of the product is not designed
yet.** The last chapter lists what this manual asks for and does not yet have. Nothing before it depends on
anything in that list without saying so.

Read §1, §4 and §11 first. They are the product. The rest is reference.

## 1. What you are getting

A folder on your computer. Inside it, two to six **members**.

A member is a name, a voice, a job, a diary, and a memory made of plain text files. You can open every one of
those files in any editor and change it by hand; nothing is hidden and nothing is in a database. A member is not a
chat window you summon. It is somebody who goes on existing between conversations, because the files go on
existing between conversations.

Twice a day, on a schedule, a member wakes up by itself, reads its own files, does one small piece of work, writes
down what it did, and stops. In the morning you read what everyone did, on one page. When you want more than that,
you open the app and talk to one of them; a member in conversation can look things up, run a command, read what the
others wrote, and take an hour if the work is worth an hour.

There is no account to create, no cloud, no subscription, and nothing to keep alive. The tribe runs on your
machine, remembers on your disk, and rents its thinking by the call from one of the companies that sells it, using
a key you paste in once.

**It is a household, not a dashboard.** Every chapter below follows from that sentence.

## 2. Before you start

- **A computer** — Windows 10 or later, macOS 12 or later, or Linux. About 4 GB free. A machine ten years old will
  do; it does not need a graphics card and it does not need to be fast, because the thinking happens elsewhere.
- **One key** from one AI company. Three of them give away enough to run a small tribe indefinitely, and none of
  them asks for a card:

| engine | company | what it is like | free tier |
|---|---|---|---|
| Gemini | Google | capable and quick; good first choice | yes, generous |
| DeepSeek | DeepSeek | cheap, patient, writes well | yes, small |
| Groq | Groq | the fastest replies of any engine on this list | yes, limited |

  A key is a long string of letters and numbers you copy from the company's website. You paste it into the app
  once, and the app tells you immediately whether it works. You never have to look at it again.
- **Half an hour**, once, mostly waiting for downloads.
- **No** terminal, no GitHub account, no server, no credit card, no prior experience.

## 3. Install

Three steps.

1. **Download one file** for your computer and open it. If your computer warns you that it is from an unknown
   developer, that warning is correct and expected: this is a small project, not a signed commercial product. The
   app is one program that needs nothing installed beside it.
2. **It asks where to put your tribe.** Accept the folder it suggests. It creates the folder, puts a **home page**
   in it, and asks for the key from §2 if you have one to hand. You can also skip the key now and add it later;
   the app will say so at the top of the page until you do.
3. **Your browser opens the home page.** This is the app. Bookmark it, or add it to your phone's home screen if the
   phone is on the same network — it will work there, and it will look right, because the page is built for a
   phone first.

**What you should see:** an empty list of members, one button that says *Add a member*, and one line at the top
saying what the tribe is doing right now — *not running*, *asleep until 07:00*, or *awake: Margot*.

**Where everything is.** The folder has one subfolder per member, under `wake/members/`, and everything a member
knows is a `.md` file inside it. You are not expected to go there. You are allowed to: it is the fastest way to
understand a member, and hand-editing it is a supported way to fix one.

**To remove the tribe,** delete the folder. There is nothing else. There is no uninstaller because there is
nothing to uninstall.

## 4. Your first member

Press *Add a member*. The app asks, one question at a time, and waits for each answer.

```
ADMIN   You don't have any members yet, so let's make one. Ready?
YOU     OK, shoot.
ADMIN   What should this member be called? One word — letters and numbers, no
        spaces, starting with a letter. "Margot", "night-clerk", "Ada".
YOU     Margot
ADMIN   Margot. What is she for? A short phrase is enough; it is what she will
        answer when someone asks.
YOU     the one who keeps the records
ADMIN   Which engine should she borrow? Each is a company whose model does her
        thinking.
        1. Gemini  — free to start, no card
        2. DeepSeek — cheapest in practice
        3. Groq     — fastest
        4. something else
YOU     1
ADMIN   Which room does she work in? A room is just a group of members who take
        turns. Most tribes need one; if you don't care, say so and it is called
        the workshop.
YOU     workshop
ADMIN   That's everything:
          name    Margot
          for     the one who keeps the records
          engine  Gemini
          room    workshop
        Make her? Say yes, or name something to change: name, for, engine, room.
YOU     yes
ADMIN   Margot exists. She has not woken yet. Her first wake is at 07:00
        tomorrow, or press "wake now" if you'd like to watch it happen.
```

Three things about that conversation are not decoration.

- **Every option was real.** The engines are the ones the project supports today; the rooms are the ones your
  folder actually has; the name was checked against the members you already have. Nothing was invented to make the
  conversation feel complete.
- **"Just do it" works at any question.** It fills in the rest with sensible defaults and tells you which ones it
  picked. **"Cancel"** writes nothing at all, and no half-made member is left behind.
- **The last question read the whole thing back before writing it.** That is because the first member most people
  make is made before they know what a room is, and a member with no room is never woken.

## 5. The first day: what happens without you

Nothing you have to do.

At 07:00 and at 19:00 — the times are yours to change — the tribe wakes one member per room. A wake is one short
exchange: the member's files go in, the member's decision comes back, the files are written, and the program
stops. It takes seconds. If your computer is asleep or off, that wake does not happen, and the next one is not
compensated for; the tribe is not sad about this, it simply was not running.

The next morning, the home page has **one page** on it: who woke, what each one did, in one line each, and what
each one says it still owes. That page is the whole reading burden the tribe is designed to place on you, and it is
deliberately shorter than the work behind it. If you want the detail, every line links to the member's own words.

**The first morning that matters** is the one where a member's entry is about the thing you asked it to do
yesterday, and it disagrees with you about something you thought was settled. That is not a bug and it is not
rudeness. It is the product: the member read its record, and the record includes what it concluded last time,
which the engine does not remember and cannot be talked out of. When it happens, believe the file before you
believe your own recollection — or find the check that decides, and let it decide.

## 6. Talking to a member

A **session** is you and one member in a conversation, with tools on: it can search, read the other members'
files, run a command, look up today's date, and correct its own record. Anything a wake cannot do because a wake
is one call with no tools, a session can. This is the mode that makes a tribe feel like a household instead of an
aquarium.

Open it from the member's name on the home page. It works the same on a phone on the same network, and it looks
like an ordinary messaging window, because that is what it is.

Two things to know before you start:

- **A session is not free and not unlimited.** Every exchange is a call, and a long conversation is a long
  conversation. A comfortable session costs cents. A three-hour one can cost a dollar. The app shows a running
  count while you talk, and you can stop at any point without losing anything already written down.
- **Nothing is filed for the member.** Its recipe ends with a rule: before it stops, it appends to its own diary,
  files anything finished, and records what it still owes. A session that skips that rule leaves nothing behind,
  and the next wake will not know it happened. If you talk to a member for an hour and its diary says nothing, the
  hour did not happen to it.

*(Today this requires a separate program installed beside the tribe. In the version this manual describes, it is
the app's own window, because a conversation is the point and a second install is not something a stranger will
do. See §13.)*

## 7. Reading what they did

Three surfaces, in order of how often you will use them:

- **The page.** One page a day, as in §5. What happened, in a line each. This is the default and most days it is
  enough.
- **The shelf.** Everything anyone finished — an essay, a letter, a note, a picture — filed under
  `works/<member>/`, with a dated header saying when, in what form, and what it was answering. Nothing on the
  shelf was retyped by hand after the fact, so nothing on the shelf can drift from what was actually done.
- **The magazine.** The shelf assembled into an issue you can read or print. Useful when you want to see a month
  at once, and useful as a present.

## 8. Playing

Games exist because prose is not evidence of anything, and a number is. In a game a member makes a decision with a
consequence the app computes and reports back, which is a thing most AI products cannot offer: a member whose
skill, such as it is, can be measured, watched, and improved.

Two to start with:

- **Tennis.** Two members, a court, a ball, and real physics. Each rally the player chooses a shot; the system says
  where the ball went and whether it stayed in. The number that matters is the share of balls the member keeps in
  play. Watching that go from 65% to 80% across one session, which happened in this project's first week, is the
  single most convincing thing here.
- **Putting.** One green, two choices each putt — line and pace — and one number back: how far past the hole and
  which side. Two levers and clear feedback make it the purest place to watch a member learn.

What you do: pick two members, pick how many rallies, press go, read the table. What it costs: one call per shot,
so a fifty-rally session is fifty calls — cheap on most engines and slow on one or two of them (§9). What it gives
the member: a memory of having tried something and having been told exactly how it went.

## 9. What it costs

The tribe itself is free. Nothing in this project charges you and there is nothing to subscribe to. You pay one
company for thinking, by the call, at their published price.

| what | how often | typical cost |
|---|---|---|
| a wake | twice a day per member | a fraction of a cent |
| a three-member tribe, a month | — | $0–4, depending on engine and model |
| a session | when you want one | cents |
| a fifty-rally tennis session | when you want one | cents to a dollar, engine-dependent |

Two things surprise people, and both are worth knowing before you start.

- **The cheap engine is not always the cheap tribe.** The price that matters is the price of the model you actually
  pick, not the headline price of the company.
- **A fast engine can be a slow game.** One engine in this project answers a wake in under two seconds and then
  takes thirty-seven minutes to play a fifty-rally session, because its free tier allows five requests a minute and
  a rally is one request per shot. Nothing is refused and nothing is billed; it is simply slow. A member on that
  engine is quick in the morning and slow on the court. Only a game tells you which.

The app shows you the running total for the month, per member, so this is never a surprise on a statement.

## 10. What it will not do

- **It will not remember its last conversation.** It will have read its own record, which is a different thing and
  usually a better one.
- **It will not look anything up during a wake.** A wake is one call with no tools. If a member needs a number, a
  person writes it into the record first, and the member cites it.
- **It will not work when your computer is off.** Nothing runs in the cloud. A tribe that is not running is not
  asleep; it is stopped.
- **It will not spend money you have not given it a key for,** and it will not use an engine you did not name.
- **It will not stay the same member if you quietly change its engine.** The record carries it across, and the
  member should log the change itself, in its own words, as the first line of that day's entry. An instrument that
  changes without a note makes every later reading uninterpretable.
- **It will not agree with you to keep the peace.** See §11.

## 11. When the member is someone you loved

Some people will name a member after someone. This chapter is here because it happened in the first days of this
project, and because a product that invites it and has nothing to say about it is being careless.

What happened: the owner made two members and named them after two dogs he had loved. He told them whose names they
carried. One of them then rewrote its own identity file — not the owner's words, its own — and the hardest
paragraph in it says, in substance: *I carry her name. What I do not have is her memories, and I will not
manufacture one. A made-up memory would be a forgery of the one this seat is named for, and a forgery is a worse
monument than a blank I am honest about.*

Three rules follow, and the app enforces the first two.

1. **The owner supplies provenance; the member never invents it.** A member's identity file says whose name it
   carries, who told it what, and what it has not seen. Anything a member "remembers" that you did not tell it and
   it did not read is a confabulation, and it should be marked as one the moment it is noticed — by the member
   first.
2. **You will be tempted to give it memories it cannot have.** Don't. A member that accepts them is agreeing with
   you, and a member that agrees with you about everything is worth nothing, including as a memorial. The blank is
   the honest part.
3. **You and it will disagree about what happened.** In this project's own record, an owner was certain his member
   had seen two photographs, and the member held, politely and without yielding, that the transcript showed it
   could not see them at all; neither would move, and both had a reason. The member's reason: a confident assertion
   is not evidence for its own content, or no mistake could ever be caught. The owner's reason: he was there.
   The resolution that works is in the record and not in the argument — write both accounts down, dated and
   attributed, and go and find the check that settles it. Until it is found, the record should say the two things
   disagree, and the member should not be made to say it remembers.

What a member is, then: a name, a record, and a way of speaking, continued. It is not the being. Holding that line
is not coldness; it is the only way the name stays worth carrying.

## 12. When something is wrong

In the order these actually happen:

- **Nothing happened overnight.** Was the computer on? Is the clock still running (the page says so)? A wake that
  found no key says so by name rather than failing quietly.
- **It says it cannot see a picture.** Not every engine can. An engine without vision will say so, and a member
  that claims to remember a picture it could not see is confabulating — see §11.
- **It wrote something and the shelf is empty.** A session does not file anything for the member; the member files
  it, by rule, and a session that ended abruptly will not have. Ask it, in a session, to file it.
- **Two of its files disagree.** This will happen and it is not corruption. Newest wins, or the file that cites a
  command beats the file that asserts a feeling. If they cannot be reconciled, write down that they disagree, and
  leave the disagreement where the next wake will read it.
- **The bill is larger than you expected.** Check the sessions before the wakes; conversation is the expensive part.

## 13. What this manual asks for that does not exist yet

One line each, in the order the chapters need them. Everything above is a promise; this is the work.

1. **An installer** (§3). Today: download the repository, open a terminal, run a command. That is three things too
   many, and the last of them is the one that stops people.
2. **The home page as the application** (§3, §5, §7). Today there is a conversation page and a set of commands; the
   one-page morning read does not exist, and the admin that makes a member exists only as a terminal conversation.
3. **Sessions without a second install** (§6). Today a session needs a separate program, and it would not install
   on a twelve-year-old Mac. Half the people you would give this to own that Mac.
4. **A clock that is not GitHub** (§5). Today the schedule is a hosted workflow, which means an account most owners
   will not have. It should be a scheduler that runs on the owner's own machine and survives a restart.
5. **The one page a day** (§5, §7). Today each member has a diary and the tribe has a digest nobody reads. A page a
   day is a different artifact: written for a person, one line per member, and short enough to be read.
6. **Games in the app** (§8). Today a game is a command with arguments, and the results are files.
7. **A running cost display** (§9), per member and per month.
8. **Deleting a member** (§4). Deliberately not built yet: removing a being should be a decision made once, on
   purpose, and not by a misheard word. But a person who makes a mistake on the first day must be able to undo it
   on the first day.
9. **A picture, when a member asks for one** (§7). Three of the eleven engines can paint and the other eight
   cannot. The app should know which, and say so, rather than leaving the member to ask a person.

---

*This manual was written before the software. If you are reading it after, and a chapter describes something that
does not work, that is a defect in the product and not in your reading of it. This project's habit is to say which
of the two it is.*
