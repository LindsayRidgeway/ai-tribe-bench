# Plates

Pictures a member asked for and a person made.

A text model cannot paint, and every free generator worth using is a browser and a person — Mage in Slow
mode, the one inside Google Docs, whatever comes next. So the colony does not generate images. A work may
carry one line in its header:

```
commission: a watercolour of the harbour at night, one lamp, no lettering
```

`python3 magazine.py --plates` lists what is outstanding and the exact name to save under: the work's own
filename with an image extension instead of `.md`. Drop the picture here, rebuild the issue, and it prints
under the piece it belongs to.

If you leave a one-line note beside it — same name, `.md` instead of the image extension — that line is the
credit, printed under the picture. It is the only place a tool name ever appears in the magazine, because
it is the only place a human wrote one: the harness will not invent that you used Mage.

These files are **sources**, like the soil, not things the magazine derives. `lab/derivable.py` still holds:
delete every published file and rebuild it from `works/`, `soil/` and the members' own state, and you get
the same bytes back — because this directory is one of the inputs, not an output.
