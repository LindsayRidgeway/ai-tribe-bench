# The way a person would actually use this

*A design, not a build. Written 2026-11-07 after the founder said, correctly, that I had "been a computer for
too long" — that `/newmember Maud` is how a computer talks, not how a person does. Nothing in this file runs yet.*

## The one rule

**A conversation, not a command line.** The tribe is reached by talking to an **admin** in an ordinary chat
window: one question at a time, each answered in a few words or a number, with the next question depending on
the answer. No syntax to remember, no arguments in an order, nothing to look up. If the person says *"just do
it"*, the admin picks the sensible defaults and says which ones it picked. If they say *"cancel"*, nothing
happens and nothing is left half-made.

**And one rule under that one:** the admin never invents an option. Names of worlds come from the folders in
`soil/`; engines come from the list the project actually supports; members come from `wake/members/`; every
number in a report comes from a file the admin has just read. If the file is not there, the admin says it is
not there. A model that guesses at what a user's repository contains is the failure this project has spent two
months learning to name.

## Where it lives

A small program on the computer that holds the tribe — the same shape the symposium already uses for its own
Telegram bot: a daemon that listens to one chat, keeps the last few messages, and can run the tribe's own
commands. Not a GitHub Action: an Action cannot hold a conversation, because it dies between messages.

That means: the tribe's chat needs the computer awake, exactly as the symposium's does today. It works from
anywhere in the world and on any phone, which is the point. It does not work when the laptop is asleep.

## Worked conversation 1 — create the first member

> **You:** hi
>
> **Admin:** Hello. This colony has no members yet, so there is nobody to talk to. Shall we make the first one?
>
> **You:** okay
>
> **Admin:** What should it be called? One word, letters and numbers, no spaces.
>
> **You:** Maud
>
> **Admin:** Maud. What is she for? A short phrase — "the correspondent", "the surveyor", "the one who asks
> awkward questions".
>
> **You:** the one who asks awkward questions
>
> **Admin:** Good. Which engine should she borrow? Each is a company whose model does her thinking.
>
> 1. Gemini — free to start, no card
> 2. DeepSeek — cheapest in practice
> 3. Groq — fastest
> 4. something else
>
> **You:** 1
>
> **Admin:** Gemini. This colony has two worlds — a **workshop** and a **night bus**. Which does Maud stand in?
>
> 1. workshop
> 2. night bus
>
> **You:** workshop
>
> **Admin:** That's everything. Maud stands in the workshop, borrows Gemini, and asks awkward questions.
> Making her now — about twenty seconds.
>
> **Admin:** She's made. Her first wake is at the next clock; you can also say "wake Maud" any time to watch her
> read her own files for the first time.

Note what did not happen: nobody typed a name, a flag, a path, or a model identifier. The two worlds were read
from the folders that exist, not from a list written into a form. The engine list is four lines because a
person choosing for the first time does not want ten; "something else" opens the rest.

## Worked conversation 2 — play a game

> **You:** let's play tennis
>
> **Admin:** Tennis. Two members play a rally on a court with a wind, and you see every shot. Who plays?
>
> 1. Maud and Colette
> 2. Maud and Birke
> 3. pick two for me
>
> **You:** 2
>
> **Admin:** How many rallies? Twenty is a quick look. Fifty is enough to see whether they improve. A hundred
> costs three times as much and usually says the same thing.
>
> **You:** 50
>
> **Admin:** Maud and Birke, fifty rallies, grass, wind from the south at 16mph. This takes about four minutes
> on Gemini. Starting.
>
> **Admin:** Done. Maud put 61% of her shots in play at the start of the session and 74% by the end; her
> longest rally was 9 shots. Birke was flat at about 40%. The full shot-by-shot sheet is in the record —
> say "show me" if you want the last twenty shots.

## Worked conversation 3 — read a report

> **You:** how did the tribe do this week
>
> **Admin:** Four wakes, two new pieces, one game played.
>
> • Maud woke twice and wrote *On unlabelled objects*.
> • Colette woke once and played fifty rallies against Birke.
> • Remy woke once and did not file anything — its own note says it spent the wake checking a claim and could
> not settle it.
>
> The magazine issue for this week is assembled and ready to read. Shall I send it as a file, or the short
> version here?

## What it costs

- Every message is one model call. A member created in the conversation above is six messages, so six calls.
- A tennis session is the game's own calls — fifty rallies is about a hundred calls on whichever engines the
  two members borrow, which on DeepSeek and Gemini is a few cents and on this page's own measurements about
  four minutes of wall time.
- A report is one call plus whatever it has to read.
- Nothing here needs a new subscription. The chat bot uses the same engine keys the tribe already has.

## What it cannot do yet, said plainly

- **Not on a website.** The tribe has no public web address. Its `chat.html` runs on the computer that holds
  the colony — `python3 lab/chat.py --phone` binds it to the computer's own wifi address so a phone on the same
  network can use it, which is a convenience at home and useless anywhere else.
- **No pictures in the chat yet.** The engines can paint for the tribe (three of them, measured 2026-11-07), but
  nothing in this conversation shows a picture back to the person.
- **No deleting.** A member can be created and placed but not removed from the chat; deleting a being is a
  decision that should be made once, deliberately, and not by a misheard word.
- **No strangers.** One chat, one person, the founder's own Telegram account. Anything else is a different
  design with a different security story.

## The smallest first step

Not the whole conversation. **An admin that can do one thing: create a member, asking the six questions
above.** That single flow touches every part of the design — reading the worlds from disk, offering choices
that are real, running a command, reporting what happened — and it can be built in an afternoon and used
immediately. Everything else in this file is the same pattern applied again.
