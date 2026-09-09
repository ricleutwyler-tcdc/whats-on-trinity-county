#!/usr/bin/env python3
"""
Flag phrasing that doesn't sound like Ric.

Patterns match CONSTRUCTIONS, not literal strings. An earlier version matched
literal phrases and let "the question isn't how to X. It's how to Y" walk straight
past a rule written specifically to catch that flip.

Usage:
    python3 check-voice.py [path ...]

Paths may be files, directories, or globs. Directories are walked for .md, .js,
.py, .txt and .html. With no arguments it scans the current directory.

Exit code 1 if anything is flagged, so it can gate a build.

ON FALSE POSITIVES: narrow the pattern or add the phrase to ALLOW_CONTEXT. Do not
delete the rule, and do not rewrite correct prose to satisfy a bad pattern. A plain
contrastive clause ("general information, not medical advice") is ordinary English
and is deliberately not flagged — an over-broad version of the appositive rule once
flagged twenty of those, and applying them all would have flattened good writing.
Over-correcting is its own failure.
"""
import re, sys, os, glob

EXTS = ('.md', '.js', '.py', '.txt', '.html')

# Files whose audience is a third party being instructed (how-to copy, driver-facing
# or customer-facing instructions) may legitimately use the imperative. Add path
# fragments here to exempt them from the "directive" rules only.
ALLOW_DIRECTIVE_PATHS = ()

# Exact context substrings that are fine as written.
ALLOW_CONTEXT = ()

PATTERNS = [
    # ---- the "not X, it's Y" flip, in all its forms ----
    (r"\b(isn'?t|aren'?t|wasn'?t|'?s not|is not)\b[^.;?!]{3,60}[,;—-]+\s*(it'?s|that'?s|they'?re|it is)\b",
     "\"not X, it's Y\" flip", re.I),
    (r"\b(isn'?t|aren'?t|is not|'?s not)\b[^.;?!]{3,80}[.?!]\s+(It'?s|That'?s|They'?re|It is)\b",
     "\"not X, it's Y\" flip across sentences", 0),
    # NOTE: a plain contrastive clause is ordinary English and is NOT flagged.
    # Only the rhetorical punchline forms are.
    (r"(?<=[.!?])\s+Not [\"'a-z][^.?!]{2,60}[.?!]", "\"Not X\" used as a punchline beat", 0),
    (r"\b(isn'?t|aren'?t) what [^.?!]{3,60}[.?!]\s+\w[^.?!]{2,60}\bis\.", "\"isn't what X. Y is.\" flip", 0),
    (r"did(n'?t| not) \w+ because [^.;?!]{3,70}[.?!]\s+(They|He|She|It)\b[^.;?!]{0,25}because",
     "\"not because X, because Y\" flip", 0),
    (r"\bnot (because|about|that) [^.;?!]{3,60},? but\b", "\"not X but Y\" flip", re.I),
    (r"\bless an? [^.;?!]{3,40} than an? \b", "\"less X than Y\" flip", re.I),

    # ---- consultant vocabulary ----
    (r"\bleverag(e|ing|ed)\b", "consultant word", re.I),
    (r"\bmoving forward\b", "consultant filler", re.I),
    (r"\bat the end of the day\b", "filler", re.I),
    (r"\bwork the problem\b", "jargon", re.I),
    (r"\bdeep dive\b|\bdouble[- ]click\b|\bcircle back\b", "consultant jargon", re.I),
    (r"\bnatural candidates?\b|\badjacent opportunit", "stock phrase", re.I),
    (r"\bbroader direction\b|\bhard to replicate\b", "stock phrase", re.I),
    (r"\bthe work that carries the value\b|\bruns through our doors\b", "stock phrase", re.I),
    (r"\btable stakes\b|\bmove the needle\b|\bsweet spot\b", "consultant cliche", re.I),
    (r"\bstrategic (imperative|priority|lever)\b|\bkey learnings?\b", "consultant register", re.I),
    (r"\bthe real (question|issue|problem|opportunity) (is|isn'?t)\b", "consultant setup", re.I),
    (r"\bwhat this really means\b|\bhere'?s the thing\b", "consultant setup", re.I),
    (r"\bwedge product\b|\bearned media\b|\bwhite[- ]space\b", "jargon a non-marketer won't parse", re.I),

    # ---- writerly / self-important framing ----
    (r"\bmy read on\b|\bmy take on\b", "self-important framing", re.I),
    (r"\bworth sitting with\b|\bthe part that stings\b", "writerly filler", re.I),
    (r"\bI want (these|this|that|it) in front of you\b", "writerly framing", re.I),
    (r"\brather than (hidden|buried|swept)\b", "writerly framing", re.I),
    (r"\bwhich surprised me\b|\bI thought this would be\b", "narrating own reaction", re.I),
    (r"\bmatters more than it sounds\b|\bmore important than it looks\b",
     "tells the reader he underrates it", re.I),
    (r"\bthe (biggest|single most important) (idea|thing) (in here|in this)\b",
     "announces its own importance", re.I),
    (r"\bthe highest[- ]value (sequence|section|change|item)\b", "announces its own importance", re.I),

    # ---- ranking the correspondent's contribution for them ----
    # Added 4 Sep 2026. Ric had already banned this in the skill file
    # ("Ranking his correspondent's answer for them") and it went out anyway,
    # because nothing here could see it: "the monthly office hours are the most
    # useful thing anyone has told me in two weeks of doing this."
    (r"\bthe (single )?most (useful|valuable|important|helpful|interesting) "
     r"thing (anyone|anybody|any \w+)\b", "ranks the correspondent's answer for them", re.I),
    (r"\bthe best (thing|answer|reply|news|part) (anyone|anybody|I'?ve)\b",
     "ranks the correspondent's answer for them", re.I),
    (r"\bthe first [a-z ]{3,40} I'?ve been able to\b",
     "superlative about our own work", re.I),
    (r"\bin \w{2,12} of doing this\b", "narrating how long we've been at it", re.I),

    # ---- claiming Ric personally holds or remembers something ----
    # Added 4 Sep 2026. "it stays out of the listing and in my head" was written
    # in Ric's voice and is not true: the record is in a file he did not write
    # and does not carry. Never put the sender's memory or interior state in a
    # sentence he will send. Say where the thing actually is, or say nothing.
    (r"\bin my head\b", "claims Ric is holding it in memory — it is in a file", re.I),
    (r"\bI'?ll (remember|keep (it|that|this) in mind|bear (it|that) in mind|"
     r"hold onto (it|that))\b", "claims Ric will personally remember it", re.I),
    (r"\b(stays|stayed|staying) with me\b|\bsticks with me\b",
     "claims Ric's interior state", re.I),

    # ---- unprovable claims about the world, in our own voice ----
    # Added 8 Sep 2026. A launch post said "Most of it is hard to find, and some
    # of it never gets found." Ric: "example of saying things you shouldn't."
    # Nobody measured either half. The site's whole promise is that it prints
    # only what can be checked; the post introducing it has to keep the same
    # promise. Say what the site does, not what the world is like.
    (r"\b(never|rarely|seldom) gets? (found|seen|used|heard about|noticed)\b",
     "unprovable claim about what happens in the world", re.I),
    (r"\b(most|much) of (it|them|this) (is|are) (hard|difficult|impossible) to find\b",
     "unprovable claim about how hard something is to find", re.I),
    (r"\b(most|many) (people|owners|businesses) (don'?t|never) know\b",
     "unprovable claim about what people know", re.I),
    (r"\bworth my knowing\b", "self-narrating, and claims his attention", re.I),

    # ---- praise that carries no information ----
    # Added 4 Sep 2026 with the two above. The common shape of every flourish
    # Ric has cut: a sentence whose only content is how good he thinks
    # something is. If a sentence carries no fact, no ask and no plain thanks,
    # it should not be in a message going out over his name.
    (r"\b(invaluable|incredibly helpful|so helpful|hugely helpful|"
     r"tremendously|fantastic|amazing|wonderful|brilliant)\b",
     "opinion adjective doing the work of a fact", re.I),
    (r"\bI can'?t tell you how\b|\bmeans a (lot|great deal) to\b",
     "effusive filler", re.I),
    (r"\b(really|truly|genuinely|incredibly|extremely) (useful|helpful|good|"
     r"important|valuable)\b", "intensifier propping up an opinion", re.I),
    (r"\bexactly (what|the) [a-z ]{2,30} (needed|wanted|was after)\b",
     "tells them how well they did", re.I),

    # ---- idiom that is not his ----
    # Added 5 Sep 2026. "I took your steer" went into a draft to Shasta
    # College; Ric: "this does not sound like me". Clipped British-register
    # idiom. Plain alternative: "we did it the way you suggested".
    (r"\btook your steer\b|\byour steer\b", "idiom that is not Ric's", re.I),
    (r"\bduly noted\b|\bnoted with thanks\b|\bpoint taken\b",
     "stock acknowledgement, not his register", re.I),

    # ---- pointing at a thing instead of naming it ----
    # Added 5 Sep 2026. "Alex — we did it the way you suggested." Ric: 'we did
    # "what"?' The recipient does not have our context, so a pronoun whose noun
    # is not in the same sentence makes them guess. These are the shapes it
    # takes most often; the general rule is in the gate's closing checklist,
    # because not every case is pattern-shaped.
    (r"\bwe (did|fixed|changed|handled|sorted|updated|redid) (it|that|this)\b",
     "pronoun with no antecedent — name what changed", re.I),
    (r"\b(it'?s|that'?s|this is) (done|sorted|handled|taken care of|all set)\b",
     "pronoun with no antecedent — name what is done", re.I),
    (r"\bwe took care of (it|that|this)\b",
     "pronoun with no antecedent — name what was done", re.I),
    (r"\bmade (the|that) change\b|\bmade the update\b",
     "which change? name it", re.I),
    (r"\bas (discussed|mentioned|agreed)\b(?! (below|above|in))",
     "assumes the reader remembers — say the thing", re.I),

    # ---- claiming Claude's work in Ric's first person ----
    # Added 5 Sep 2026, and it was already rule 9 of delivering-work-to-ric
    # before it shipped anyway: first person is for what Ric personally does;
    # research, harvesting, building and drafting are Claude's and get credited
    # to Claude, or to "we" for a decision TCDC made. Ric edited "I found it on
    # the Business Training Center\'s Eventbrite while I was pulling your class
    # schedule" to "Claude found it ... while it was pulling", and has asked
    # for this more than once.
    (r"\bI (found|pulled|checked|searched|scraped|harvested|compiled|verified|"
     r"cross-checked|built|generated|drafted|crawled) \b",
     "did Ric do this, or Claude? credit Claude, or say we", re.I),
    (r"\bI (couldn'?t|could not|was unable to) (find|see|locate|track down)\b",
     "Claude searched, not Ric — say Claude, or we", re.I),
    (r"\bwhile I was (pulling|checking|reading|searching|going through)\b",
     "Claude did this, not Ric", re.I),

    # ---- salesy ----
    (r"\ban easy yes\b|\bthe real money is\b|\bdwarfs\b", "salesy line", re.I),
    (r"\bno[- ]brainer\b|\blow[- ]hanging fruit\b", "salesy cliche", re.I),
    (r"\bbest[- ]in[- ]class\b|\bworld[- ]class\b|\bgame[- ]chang", "puffery", re.I),
    (r"\bbetter than anything you can buy\b|\breplaces months of\b", "salesy overreach", re.I),

    # ---- directing rather than offering ----
    (r"If you'?d rather not\b", "presumes he's declining", re.I),
    (r"\bYou need to\b|\bYou must\b|\bYou should really\b", "directive", re.I),
    (r"\bmake sure you\b", "directive", re.I),
    (r"\bwritten properly\b|\bdone properly\b|\bproper(ly)? (privacy|legal|policy)\b",
     "implies their version would be improper", re.I),

    # ---- overclaiming absence ----
    (r"[Tt]here'?s no [a-z ]{3,30} anywhere\b", "overclaims absence — say what wasn't found", 0),
    (r"\bNot on any page\b|\bNothing at all\b", "repeats the point for emphasis", 0),

    # ---- narrating our editorial decisions to the recipient ----
    # Added 5 Sep 2026. Ric cut this whole paragraph out of the Quintin reply
    # before sending it:
    #
    #   "Two things I didn't publish. That you're an office of one until
    #    October — that's staffing rather than services, and it won't be true
    #    in a month. And the resource guide you attached, because it's your
    #    document and we'd rather send people to you than reproduce it."
    #
    # Three failures in one paragraph, and the third is the general one.
    # It tells the recipient what we considered and rejected — a list of
    # non-events he did not ask for and cannot act on. It also explains our
    # editorial policy to a man who attached a file to be helpful, when the
    # answer to that is thanks. And it restates a reading of his own situation
    # that he had already corrected once.
    #
    # An email to an organization reports what is on the site, asks for what
    # we need, and thanks them. Our internal reasoning is ours.
    (r"\b(I|[Ww]e) (didn'?t|did not|chose not to|decided not to|"
     r"deliberately didn'?t) (publish|include|use|add|list|run)\b",
     "the recipient does not need a list of what we left out", re.I),
    (r"\b(Two|Three|Four|A couple of) things (I|we) (didn'?t|did not|left off|"
     r"left out|held back)\b",
     "narrating our editorial decisions — report what IS there", re.I),
    (r"\bwe'?d rather (send|point|direct|refer)\b",
     "explains our policy to someone who did not ask", re.I),
    (r"\bbecause it'?s your (document|file|guide|material|content)\b",
     "explains our policy to someone who did not ask", re.I),
    (r"\bthat'?s\s+(staffing|internal|process|policy)\s+rather than\b",
     "telling the recipient what their own situation means", re.I),

    # ---- all-caps callout labels — case-sensitive by design ----
    (r"^\*\*[A-Z][A-Z0-9 —:-]{9,}\*\*", "all-caps callout label", 0),
]


def gather(args):
    out = []
    targets = args or ['.']
    for t in targets:
        if any(ch in t for ch in '*?['):
            out.extend(sorted(glob.glob(t, recursive=True)))
        elif os.path.isdir(t):
            for root, dirs, files in os.walk(t):
                dirs[:] = [d for d in dirs if not d.startswith(('.', 'node_modules', '__pycache__'))]
                out.extend(os.path.join(root, f) for f in sorted(files) if f.endswith(EXTS))
        elif os.path.isfile(t):
            out.append(t)
    seen, uniq = set(), []
    for f in out:
        if f not in seen:
            seen.add(f); uniq.append(f)
    return uniq


def ctx(t, m, w=95):
    a = max(0, m.start() - w); b = min(len(t), m.end() + w)
    return ' '.join(t[a:b].split())


def main():
    files = gather(sys.argv[1:])
    if not files:
        print("No files to scan."); return 0

    hits = 0
    for f in files:
        try:
            t = open(f, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        for pat, why, fl in PATTERNS:
            if 'directive' in why and any(x in f for x in ALLOW_DIRECTIVE_PATHS):
                continue
            for m in re.finditer(pat, t, fl | re.M):
                c = ctx(t, m)
                if any(a in c for a in ALLOW_CONTEXT):
                    continue
                line = t[:m.start()].count('\n') + 1
                hits += 1
                print(f"\n  {f}:{line}")
                print(f"    {why}: \"{m.group(0).strip()[:90]}\"")
                print(f"    ...{c}...")

    print()
    if hits:
        print(f"{hits} phrase(s) to reconsider.")
        return 1
    print(f"Scanned {len(files)} file(s). Reads clean.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
