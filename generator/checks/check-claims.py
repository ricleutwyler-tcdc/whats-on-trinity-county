#!/usr/bin/env python3
"""
Flag assertions about a subject's INTERNAL operations that nobody confirmed.

Anything observable from outside — a website, public pricing, filings, published
material — is fair game. Anything about what the subject does, doesn't do, has,
hasn't done, keeps in their files, or is currently working on is not, unless they
told us. Those claims read as authoritative and are the fastest way to lose a
client's trust.

Usage:
    python3 check-claims.py [path ...]

Paths may be files, directories, or globs. Directories are walked for .md, .js,
.py, .txt and .html. With no arguments it scans the current directory.

Exit code 1 if anything is flagged, so it can gate a build.

When something is flagged, the fix is almost always to DELETE the claim, not to
add hedging around it. Hedged speculation is still speculation.
"""
import re, sys, os, glob

EXTS = ('.md', '.js', '.py', '.txt', '.html', '.json')

# Observable-from-outside topics. A match whose surrounding context mentions one of
# these is usually a fair claim about public material rather than internal operations.
ALLOWED_CONTEXT = [
    'website', 'site says', 'homepage', 'landing page', 'title tag',
    'meta description', 'google business profile', 'google listing',
    'facebook page', 'linkedin page', 'public filing', 'published',
    'press release', 'annual report', 'no analytics', 'privacy policy',
]

PATTERNS = [
    # claims about what they are or aren't pursuing
    (r"\bisn'?t being (worked|pursued|used|done)\b", "claims to know what they are or aren't pursuing"),
    (r"\bunworked\b|\buntapped\b(?! market)", "claims to know what they are or aren't pursuing"),
    (r"\byou'?re not (working|doing|pursuing|calling|using|selling)\b", "claims to know current activity"),
    (r"\bthey'?re not (working|doing|pursuing|calling|using|selling)\b", "claims to know current activity"),

    # claims about history
    (r"\byou'?ve never\b|\bthey'?ve never\b", "claims to know their history"),
    (r"\byou haven'?t (worked|tried|done|called|built|pursued|contacted|used)\b",
     "claims to know what they haven't done"),
    (r"\b(you|they) (have|has) never (called|worked|tried|pursued|contacted|sold|used)\b",
     "claims to know their history"),
    (r"\bnobody has (ever )?(called|worked|used|pursued|tried)\b", "claims to know their history"),
    (r"\bhas (never|not) been (done|tried|worked|pursued)\b", "claims to know their history"),

    # claims about internal records, systems and staffing
    (r"\b(customer|patient|client) files?\b", "assumes what their records contain"),
    (r"\balready in (your|his|her|their|the) files\b", "assumes what their records contain"),
    (r"\b(has|have) no (process|system|records|CRM|database|pipeline|team)\b",
     "claims to know their internal systems"),
    (r"\b(your|their) (sales )?(reps?|team|staff)\b(?= (are|is|don'?t|doesn'?t|never))",
     "assumes how they are staffed"),

    # claims about money
    (r"\bnear[- ]pure margin\b|\bhigh[- ]margin\b|\bcheap to deliver\b",
     "claims to know their margins"),
    (r"\bcosts? (you|them) (almost )?nothing\b", "claims to know their costs"),
    (r"\b(your|their) (true |real )?(cost|margin|overhead) (is|are)\b",
     "claims to know their costs"),
    (r"\bis running as if\b", "infers internal strategy from outside"),

    # grading the business rather than describing observable facts
    (r"\b(business|company) (isn'?t|is not) the problem\b", "grades the business"),
    (r"\byou'?ve got a (good|solid|real|great) business\b", "grades the business"),
    (r"\bthe business is (sound|solid|healthy|fine)\b", "grades the business"),
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


def context(text, m, width=110):
    a = max(0, m.start() - width); b = min(len(text), m.end() + width)
    return ' '.join(text[a:b].split())


def main():
    files = gather(sys.argv[1:])
    if not files:
        print("No files to scan."); return 0

    hits = 0
    for f in files:
        try:
            text = open(f, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        for pat, why in PATTERNS:
            for m in re.finditer(pat, text, re.I):
                snippet = context(text, m)
                low = snippet.lower()
                if any(a in low for a in ALLOWED_CONTEXT) and 'file' not in m.group(0).lower():
                    continue
                line = text[:m.start()].count('\n') + 1
                hits += 1
                print(f"\n  {f}:{line}")
                print(f"    problem : {why}")
                print(f"    matched : \"{m.group(0)}\"")
                print(f"    context : ...{snippet}...")

    print()
    if hits:
        print(f"{hits} claim(s) about internal operations found — cut them, don't caveat them.")
        return 1
    print(f"Scanned {len(files)} file(s). No unsupported claims about internal operations.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
