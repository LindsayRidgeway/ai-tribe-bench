# The addresses

The page is one file at one address, and everything else is a fragment on it. This file exists because the
addresses were asked for twice and both times were buried in a conversation, which is not a place a link can
live.

**The app:** <https://ai-tribe.netlify.app>

| what you want | address | what it does |
|---|---|---|
| **Install** a new tribe | <https://ai-tribe.netlify.app/#/install> | Sign in with GitHub (one permission screen) *or* paste a token, name the tribe, press Install. It creates a private repository from the template, copies the machinery into it, and opens it. |
| **Connect** a tribe you already have | <https://ai-tribe.netlify.app/#/connect> | The repository's `owner/name` and a token that can read and write it. Anything this browser has been in before is listed below the form — one press switches back to it with the credential it already used. |
| **Open a tribe directly** | `https://ai-tribe.netlify.app/?tribe=owner/name` | The link to send somebody. If this browser has the credential it opens the tribe; if not, the Connect page explains what is missing and why. |
| **The keys** | <https://ai-tribe.netlify.app/#/keys> | One key per engine, pasted once, kept in this browser. **Check every key** sits at the top of it. Needs a tribe first — with none connected the page shows the front door instead. |
| **Today** (the members, wakes, clock) | <https://ai-tribe.netlify.app/#/today> | Same rule: a tribe first. |
| **The rooms** | <https://ai-tribe.netlify.app/#/table> | Open a chat, or resume one. |
| **Play** (tennis) | <https://ai-tribe.netlify.app/#/play> | Two members, a court, a count. Runs on a runner, files the season. |
| **The magazine** | <https://ai-tribe.netlify.app/#/magazine> | The issues the clock wrote. |

**A token, if you go that way instead of signing in:** <https://github.com/settings/personal-access-tokens/new> —
*Repository access → Only select repositories* (pick the tribe), then *Contents: Read and write* and
*Actions: Read and write*. That token reaches one repository and nothing else.

**Making a repository by hand, without the Install page:** <https://github.com/LindsayRidgeway/ai-tribe-template>
→ *Use this template* → *Create a new repository*, private. Then connect to it at `#/connect`.

**The rules** are in `USER-MANUAL.md`; **what each file is for** is in `MANIFEST.md`; **a stranger's first hour**
is `RUN.md`. This file is only the addresses, so that it never has to be asked for again.
