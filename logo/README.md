# The mark

One plate, three members on a shelf, the middle one standing up to speak.

That is the whole idea. A tribe is a shelf of files; a room is three of them; one of them has the floor.
The plate is the part that is not decoration: at 16px, a mark on a ground survives and a mark on nothing
does not, and a ground means the same drawing works in a light tab strip and a dark one. I measured that
on 2026-11-10 by rendering four candidate marks at 16, 24 and 180 pixels on both grounds — dots, a
four-ray spark, a shelf, a ring — and two of the four turned to grey mush at 16. The shelf did not.

| file | what it is for |
|---|---|
| `AIT.svg` | the mark alone, 24×24. The favicon in `ait.html` is this file, inlined as a data URI. |
| `AIT-lockup.svg` | the mark and the wordmark, for a paper ground. |
| `AIT-lockup-reverse.svg` | the same, for an ink ground. |

**The wordmark is live text**, not outlines: `A` in ink, `IT` in the accent, in the app's own serif —
Iowan Old Style on a Mac, Georgia on most other machines. That is the same split the header uses, which
is the point: the logo is not a second identity, it is the header at a larger size. The cost of live text
is that a machine with neither serif falls back to Times. That is acceptable for a page with no database
and no build step; it would not be acceptable on a business card.

**The colours are the app's own** (`--accent: #7a4520`, `--bg: #f7f4ee`), with one exception:
`#d98f5c` in the reverse lockup, because `#7a4520` on an ink ground is very nearly invisible — the same
problem the favicon's plate solves by turning the relationship inside out.

The icon for the two Spotlight shortcuts (`AIT Install`, `AIT Connect`) is the same drawing, compiled to
`.icns` from `AIT.svg`. If the mark ever changes, those have to be rebuilt; nothing regenerates them.
