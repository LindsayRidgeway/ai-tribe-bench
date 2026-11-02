from pathlib import Path

p = Path("/tmp/bench/wake/wake.py")
s = p.read_text()

# ---------------------------------------------------------------- the act: beat, peers, soil, chores
old = '''=== WHAT YOU MUST DO NOW ===
Choose exactly ONE item from the list above and act on it. You are a member of a tribe, not a
chatbot: a wake that produces only commentary has failed. Your act must be a file you write.

Reply with JSON only, exactly this shape, no prose before or after:

{{
  "chosen_item": "the number and first few words of the item you chose",'''
new = '''=== WHAT YOUR FELLOW MEMBERS HAVE MADE ===
The workshop's shelf, as it stands this wake. These are not items for you to do. They are what other
members made with their own beats, and any one of them may be answered: extended, contradicted,
illustrated, catalogued, used. If you respond to one, say whose and to what.

{works}

=== WHAT YOU MUST DO NOW ===
Decide what this wake is for. Three things can claim it, and all three are legitimate:

- **your beat** — what you are interested in, which is yours and which nobody assigned;
- **a peer's work** — on the shelf above, answerable without being asked;
- **an open item** — the chores. They are real and they are the lowest of the three: do them when
  nothing else claims you, and say so.

A wake that produces only commentary has failed. Your act must be a file you write. Do not do what the
last wake did because it is easier; do the thing that is yours to do now.

Reply with JSON only, exactly this shape, no prose before or after:

{{
  "source": "beat, peer, item, or soil — which of the three claimed this wake",
  "chosen_item": "what you acted on: the number and words of an item, or the peer work you answered, or the line of your beat",'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- render the shelf
old = '''    prompt = PROMPT.format(
        identity_name=identity_name(identity),
        beat=(beat or "(you have not written a beat yet — write one: what are you interested in?)"),
        soil=(soil or "(no soil has been described — the workshop is empty)"),'''
new = '''    # The shelf: what the other members made. Found 2026-11-02 — with a beat and no shelf, a member with
    # nothing to do answered an argument from three hours earlier in its own journal, because the journal
    # was the only other thing in the room. A workshop with no view of the other benches is three people
    # writing alone in a room; the shelf is what makes a peer answerable.
    try:
        shelf = works_shelf(member=args.member)
    except Exception as e:  # noqa: BLE001 — a broken shelf must not stop a wake
        shelf = f"(the shelf could not be read: {e})"

    prompt = PROMPT.format(
        identity_name=identity_name(identity),
        works=shelf,
        beat=(beat or "(you have not written a beat yet — write one: what are you interested in?)"),
        soil=(soil or "(no soil has been described — the workshop is empty)"),'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- the shelf function
anchor = '''# --- the lie detector ---'''
shelf_fn = '''def works_shelf(member: str | None = None, limit: int = 6, chars: int = 220) -> str:
    """What the workshop has on the shelf, described from the files.

    Deliberately thin: title, who, form, words, and the first couple of lines. A member should be able to
    decide to answer a piece without being handed the piece — the piece is in `works/`, and a member that
    wants to work on it can ask for it by name in its reply.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("magazine_for_wake", str(ROOT.parent / "magazine.py"))
    if spec is None or spec.loader is None:
        return "(the shelf could not be read)"
    mag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mag)  # type: ignore[union-attr]
    works = [w for w in mag.load_all(ROOT.parent) if w.get("member") != member]
    if not works:
        return "(nothing on the shelf yet — you are the first to make something)"
    works = sorted(works, key=lambda w: str(w.get("when", "")), reverse=True)[:limit]
    out = []
    for w in works:
        first = ""
        for ln in w["body"].splitlines():
            flat = " ".join(ln.split())
            if flat and not flat.startswith("*") and not flat.startswith("#"):
                first = flat[:chars]
                break
        out.append(f"- **{w['title']}** — {w['member'].upper()}, {w['form']}, {w['words']} words\\n"
                   f"  *{w['file']}*\\n  {first}")
    return "\\n".join(out)


# --- the lie detector ---'''
assert anchor in s
s = s.replace(anchor, shelf_fn, 1)

# ---------------------------------------------------------------- record the source
old = '''        for f in findings:'''
new = '''        src = str(parsed.get("source", "")).strip().lower()
        if not src:
            findings.append("MISSING source: it did not say whether this wake was claimed by its beat, a "
                            "peer's work, an item, or the soil")
        elif not any(src.startswith(k) for k in ("beat", "peer", "item", "soil", "brief")):
            findings.append(f"SOURCE UNRECOGNISED: {src[:40]!r} is not one of beat, peer, item, soil")
        for f in findings:'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)
print("wake.py: the act comes from beat, peer or item, and the shelf is in the room")
