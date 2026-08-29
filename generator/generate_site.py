#!/usr/bin/env python3
"""
Trinity County "What's On" — weekly site generator.
Input : Wayne Agner's "TC Calendar of Events" plain-text (the .txt attachment).
Output: the brand-2.0 index.html for the rolling ~2-week window.

Usage: python3 generate_site.py <calendar.txt> <template.html> <out.html> [YYYY-MM-DD anchor]
If anchor omitted, it is parsed from the calendar header ("... 8-07-26").
Editorial note: auto-curation is mechanical (category/audience/featured by keyword rules;
weather is always "forecast closer to the date"). Solid, but not hand-tuned.
"""
import sys, re, datetime, json, html

MONTHS = {'jan':1,'feb':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,
          'jul':7,'july':7,'aug':8,'sep':9,'sept':9,'oct':10,'nov':11,'dec':12}
WD = {'monday':0,'tuesday':1,'wednesday':2,'thursday':3,'friday':4,'saturday':5,'sunday':6}
ORD = {'first':1,'second':2,'third':3,'fourth':4}
DOW_ABBR = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

J = "https://www.trinityjournal.com/calendar/"

# category -> (label, icon, gradient[2.0])
CAT = {
 'music':   ("Music","music",["#14564D","#0E3E37"]),
 'livemusic':("Live Music","livemusic",["#D6603A","#C0562F"]),
 'rodeo':   ("Rodeo","rodeo",["#C0562F","#6b3418"]),
 'arts':    ("Arts","arts",["#C0562F","#7A3F20"]),
 'community':("Community","coffee",["#D6603A","#8a4b1e"]),
 'market':  ("Market","market",["#4E9E92","#14564D"]),
 'sports':  ("Sports","trophy",["#14564D","#1E7A6E"]),
 'family':  ("Family","family",["#2E8E90","#14564D"]),
 'dance':   ("Dance","music",["#C0562F","#6B3418"]),
 'cars':    ("Cars","cars",["#2E8E90","#1E7A6E"]),
 'festival':("Festival","sun",["#1E7A6E","#14564D"]),
 'games':   ("Games","chess",["#5a6b62","#2c3a32"]),
 'bingo':   ("Bingo","grid",["#2E8E90","#14564D"]),
 'golf':    ("Golf","golf",["#14564D","#1E7A6E"]),
}
def classify(title, detail):
    t = (title+" "+detail).lower()
    def has(*ks): return any(k in t for k in ks)
    if has('chamber music','symphony','concert','planets','matinee') and not has('brewery'): return 'music'
    if has('rodeo','bull-a-rama','gymkhana','barrel race'): return 'rodeo'
    if has('art walk','artists in action','mosaic','art & craft','art and craft','festival of light'): return 'arts'
    if has('brewery','brewing','live at the brewery','band','singer','songwriter','sleepbomb','blacksage','whiskey kronic','dyar','heart & soul','tommy b','karaoke') and has('brewery','brewing','band','music','live','pm','p.m','cover'): return 'livemusic'
    if has('festival','peddlers','bigfoot','hmong new year','summer festival','music festival','salmon meets harvest','good times fair'): return 'festival'
    if has('children','kids','youth','business fair'): return 'family'
    if has('line dancing'): return 'dance'
    if has('cruisers','coffee and classics','classic','fly-in','show'): return 'cars'
    if has('craft fair','swap meet','yard sale','market','peddlers'): return 'market'
    if has('tournament','big ball','softball','bike race','mountain bike','witch brigade','homecoming'): return 'sports'
    if has('breakfast','dinner','soup kitchen','pancake','senior center','vfw','banquet','auction','grange'): return 'community'
    if has('bingo'): return 'bingo'
    if has('chess'): return 'games'
    if has('live music','music'): return 'livemusic'
    return 'community'

def audience(title, detail, cat):
    t=(title+" "+detail).lower()
    def has(*ks): return any(k in t for k in ks)
    aud=set()
    if cat in ('music','livemusic','rodeo','festival','arts') or has('brewery','resort','festival','rodeo','concert','art walk','fly-in','banquet'):
        aud.add('visitor')
    if cat in ('community','sports','dance','games','bingo','market','cars') or has('senior','vfw','church','grange','club','local','tournament','gymkhana','homecoming','soup kitchen','chamber of commerce'):
        aud.add('local')
    if has('children','kids','youth','family','all ages','all-ages','pancake','fair','carol','santa','christmas','fireworks') or cat=='family':
        aud.add('family')
    if has('gymkhana','barrel race'): aud.discard('visitor'); aud.add('local')
    if cat=='community' and has('breakfast','dinner','pancake','fair'): aud.add('family')
    if cat in ('sports','market') and 'family' not in aud: aud.add('family')
    if cat=='family': aud.add('local')
    if not aud: aud.add('local')
    order=['visitor','local','family']
    return [a for a in order if a in aud]

MARQUEE = ('rodeo','art walk','music festival','summer festival','salmon meets harvest',
           'mountain magic','hmong new year','fall into music','bigfoot','peddlers','witch brigade','planets')
def is_featured(title, detail, cat):
    t=(title+" "+detail).lower()
    if any(m in t for m in MARQUEE): return True
    if 'annual' in t and cat in ('festival','rodeo','arts','sports','music'): return True
    return False


# Known-Events Registry (mirrors the Drive rubric). First match wins; order = specific -> general.
# (keywords_any, category, audience, featured, locked_desc_or_None)
REGISTRY = [
 (['drive-through dinner','drive through dinner'],'community',['local','family'],False,"The senior center's monthly drive-through dinner in Hayfork. $15 adult, $7 child."),
 (['senior center breakfast'],'community',['local','family'],False,"The senior center's monthly breakfast in Hayfork. $15 adult, $7 child."),
 (['vfw breakfast'],'community',['local','family'],False,"Third-Saturday breakfasts at both posts — Hayfork ($15) and Weaverville ($12)."),
 (['six rivers'],'community',['local','family'],False,"A hearty community breakfast near Ruth Lake — an easy morning stop if you're down south."),
 (['soup kitchen'],'community',['local'],False,"A free community soup kitchen at the Douglas City Fire Station."),
 (['farmers market'],'market',['visitor','local','family'],False,"Local produce, prepared food, and makers at the Highland Art Center meadow."),
 (['craft fair','swap meet'],'market',['local','family'],False,"Browse, buy, and trade — the monthly craft fair and swap meet at the Hayfork VFW Hall."),
 (['cruisers','coffee and classics'],'cars',['visitor','local','family'],False,"Classic cars and hot rods on Main Street — grab a coffee and admire the chrome."),
 (['fly-in'],'cars',['visitor','local','family'],True,"The Lions Club's annual Fly-In BBQ in Trinity Center — barbecued tri-tip and chicken, a show 'n' shine, live music, and local vendors."),
 (['art walk'],'arts',['visitor','local','family'],True,"Weaverville's signature evening out — new gallery exhibits, receptions, music, and refreshments up and down Main Street."),
 (['line dancing'],'dance',['local','family'],False,"Free, all-ages line dancing — beginning and intermediate instruction."),
 (['chess'],'games',['local','family'],False,"Casual chess for all levels — bring a board or just pull up a chair."),
 (['bingo'],'bingo',['visitor','local','family'],False,"$5 a card for 16 games, cash prizes, up at the Trinity Center KOA."),
 (['members-only karaoke'],'livemusic',['local'],False,"A members-only karaoke night for Trinity Players at the Performing Arts Center — free for members."),
 (['karaoke'],'livemusic',['visitor','local'],False,"Grab the mic — a laid-back night at the Coffee Creek Country Store."),
 (['golf association'],'golf',['local'],False,"Weekly 18-hole tournament, weather permitting — open to any golfer with a handicap."),
 (['gymkhana','barrel race'],'rodeo',['local','family'],False,"Signups at 9, gymkhana at 10, barrel racing to follow — Trinity Horses and Long Ears."),
 (['ruth rodeo'],'rodeo',['visitor','local','family'],True,None),
 (['big ball','tom wakefield'],'sports',['local','family'],True,"An annual weekend of softball in Hayfork — a longtime community tradition."),
 (['business fair'],'family',['local','family'],False,"Young entrepreneurs design, make, and sell their own products — a hands-on kids' market."),
 (['chamber music','performing arts center'],'music',['visitor'],True,None),
 (['mosaic','art & craft','festival of light'],'arts',['visitor','local','family'],False,None),
 (['brewing company','brewery'],'livemusic',['visitor','local'],False,"Live music at Trinity County Brewing — craft beer, food, and a local band. No cover."),
 (['festival','peddlers','bigfoot','hmong new year','salmon meets harvest','good times fair','mountain magic'],'festival',['visitor','local','family'],True,None),
]
def curate(title, detail):
    """Returns (cat, audience, featured, locked_desc_or_None, status).
    status: 'locked' = registry cat+desc; 'cat-only' = registry cat, session writes desc;
            'new' = no registry match, keyword-guessed cat + session should verify + write desc."""
    t=(title+' '+detail).lower()
    for kws,cat,aud,feat,desc in REGISTRY:
        if any(k in t for k in kws):
            return cat, list(aud), feat, desc, ('locked' if desc else 'cat-only')
    cat=classify(title,detail)
    return cat, audience(title,detail,cat), is_featured(title,detail,cat), None, 'new'

def nth_weekday(year, month, wd, n):
    d=datetime.date(year,month,1)
    offset=(wd-d.weekday())%7
    day=1+offset+(n-1)*7
    try: return datetime.date(year,month,day)
    except ValueError: return None

def clean(s):
    s=re.sub(r'\s+',' ',s).strip().rstrip('.').strip()
    return s

def esc(s):  # for JS string literal inside double quotes
    return s.replace('\\','\\\\').replace('"','\\"')

TIME_RE=re.compile(r'(\d{1,2}(?::\d{2})?)\s*(?:to|-|–|—)?\s*(\d{1,2}(?::\d{2})?)?\s*([ap]\.?m\.?)',re.I)
def fmt_time(detail):
    m=TIME_RE.search(detail)
    if not m: return ''
    a,b,ap=m.group(1),m.group(2),m.group(3).replace('.','').upper()
    if b: return f"{a}–{b} {ap}"
    return f"{a} {ap}"

def extract_where(detail):
    # prefer "at the X, addr" / "at X"
    m=re.search(r'\bat (?:the )?([A-Z][^.;]+)',detail)
    if m:
        w=m.group(1)
    else:
        # fallback: a chunk that looks like a place (Capitalized words + address)
        m2=re.search(r'([A-Z][A-Za-z\'&/ ]+(?:Hall|Center|Field|Grounds|Saloon|Store|Market|Church|Park|Fairgrounds|Resort|Brewing|Brewery|Theatre|Meadow|Arena|Museum|Cafe|Course|Pavilion)[^.;]*)',detail)
        w=m2.group(1) if m2 else ''
    w=re.sub(r'\b(?:Info|Contact|Email|Call|Tickets|Signups?)\b.*$','',w,flags=re.I)
    w=re.sub(r'\b\d{3}[-.]\d{3}[-.]\d{4}\b.*$','',w)
    return clean(w)[:90]

def make_desc(title, detail):
    # Mechanical placeholder only. The weekly runbook requires the agent to rewrite
    # every NEW / cat-only description in editorial voice; this just has to be a safe,
    # complete sentence if one ever slips through.
    d=re.sub(r'\b\S+@\S+\b','',detail)          # emails
    d=re.sub(r'\b\d{3}[-.]\d{3}[-.]\d{4}\b','',d) # phones
    d=re.sub(r'\b(Info|Contact|Email|Call|Reserve|Signups?)\b.*?(?=(\.|$))','',d,flags=re.I)
    d=clean(d)
    if len(d)>200: d=d[:197].rsplit(' ',1)[0]+'…'
    return d or title

def parse(cal_text):
    lines=[l.rstrip() for l in cal_text.splitlines()]
    # header date
    anchor=None
    m=re.search(r'(\d{1,2})-(\d{1,2})-(\d{2})',lines[0]) if lines else None
    if m: anchor=datetime.date(2000+int(m.group(3)),int(m.group(1)),int(m.group(2)))
    section=None; year=2026; weekly=[]; recurring=[]; dated=[]
    for l in lines:
        s=l.strip()
        if not s: continue
        low=s.lower()
        if low in ('weekly','twice-monthly','monthly','calendar'): section=low; continue
        if low.startswith('get your event') or s.startswith('#'): section='end'; continue
        if s=='2027': year=2027; continue
        if section=='end': continue
        if section in ('weekly','twice-monthly','monthly'):
            if not s.startswith('*'): continue
            item=s[1:].strip()
            title=clean(item.split(',')[0])
            if section=='weekly':
                weekly.append((title,item))
            else:
                recurring.append((title,item))
        elif section=='calendar':
            m=re.match(r'([A-Za-z]+)\.?\s+(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?:\s*(.*)',s)
            if not m: continue
            mo=MONTHS.get(m.group(1).lower()[:4].rstrip('.')) or MONTHS.get(m.group(1).lower()[:3])
            if not mo: continue
            d1=int(m.group(2)); d2=int(m.group(3)) if m.group(3) else None
            rest=m.group(4).strip()
            if rest.isupper():  # holiday line e.g. THANKSGIVING
                continue
            title=clean(rest.split(',')[0].split('.')[0])
            try: sd=datetime.date(year,mo,d1)
            except ValueError: continue
            ed=None
            if d2:
                try: ed=datetime.date(year,mo,d2)
                except ValueError: ed=None
            dated.append(dict(date=sd,end=ed,title=title,detail=rest))
    return anchor,weekly,recurring,dated

def expand_recurring(recurring, ws, we):
    out=[]
    months=set()
    d=ws
    while d<=we:
        months.add((d.year,d.month)); d+=datetime.timedelta(days=1)
    for title,item in recurring:
        low=item.lower()
        ords=[ORD[o] for o in ORD if re.search(r'\b'+o+r'\b',low)]
        wd=None
        for name,idx in WD.items():
            if name in low or name[:-1]+'s' in low or (name+'s') in low: wd=idx
        if wd is None or not ords: continue
        for (yy,mm) in months:
            for n in ords:
                dt=nth_weekday(yy,mm,wd,n)
                if dt and ws<=dt<=we:
                    out.append(dict(date=dt,end=None,title=title,detail=item))
    return out

def daylabel(ev):
    sd=ev['date']; ed=ev.get('end')
    tm=fmt_time(ev['detail'])
    if ed and ed!=sd:
        return f"{DOW_ABBR[sd.weekday()]}–{DOW_ABBR[ed.weekday()]} · {sd.strftime('%b')} {sd.day}–{ed.day}"
    base=f"{DOW_ABBR[sd.weekday()]} · {sd.strftime('%b')} {sd.day}"
    return base+(f" · {tm}" if tm else "")

def ev_obj(ev):
    cat,aud,feat,desc,status=curate(ev['title'],ev['detail'])
    ev['_status']=status
    label,icon,grad=CAT[cat]
    where=extract_where(ev['detail']) or "Trinity County"
    if desc is None: desc=make_desc(ev['title'],ev['detail'])
    fields=[f'date:"{ev["date"].isoformat()}"']
    fields.append('for:['+','.join('"%s"'%a for a in aud)+']')
    if feat: fields.append('feat:true')
    fields.append(f'dayLabel:"{esc(daylabel(ev))}"')
    fields.append(f'cat:"{esc(label)}", icon:"{icon}", grad:["{grad[0]}","{grad[1]}"], title:"{esc(ev["title"])}"')
    fields.append(f'where:"{esc(where)}"')
    fields.append(f'desc:"{esc(desc)}"')
    fields.append(f'wx:null, info:J, map:"{esc(where)}, Trinity County, CA"')
    return "  { "+", ".join(fields)+" }"

# weekly-strip constant: the At-the-Movies card (site fixture, not from Wayne)
ATMOVIES=('  { date:"__WSAT__", weekly:true, season:"year-round", for:["visitor","local","family"], '
 'dayLabel:"Weekly · Fri–Sun showings", cat:"Movies", icon:"film", grad:["#14564D","#0E3E37"], '
 'title:"At the Movies · The Trinity Theatre", where:"The Trinity Theatre, Main St., Weaverville", '
 'desc:"First‑run films at Weaverville\'s restored 1939 Trinity Theatre — a This is Trinity landmark.", '
 'wx:null, info:"https://www.trinityjournal.com/calendar/", map:"Trinity Theatre, Main Street, Weaverville, CA 96093" }')

# Clean display titles for the stable weekly fixtures (raw lines are run-on sentences).
WEEKLY_TITLE=[('chess','Chess Club'),('bingo','Bingo'),('karaoke','Saturday Karaoke'),
              ('farmers market','Weaverville Farmers Market'),
              ('golf association','Trinity Alps Golf Association')]
def weekly_obj(title,item,wsat):
    cat,aud,feat,rdesc,status=curate(title,item); label,icon,grad=CAT[cat]
    tl=title.lower()
    for k,nt in WEEKLY_TITLE:
        if k in tl: title=nt; break
    # day + time
    low=item.lower(); dayname=None
    for name,idx in WD.items():
        if name in low: dayname=name.capitalize()+'s'
    tm=fmt_time(item)
    sched="Weekly"+((" · "+dayname) if dayname else "")+((" · "+tm) if tm else "")
    where=extract_where(item) or "Trinity County"
    desc=rdesc or make_desc(title,item)
    season=""
    ms=re.search(r'through ([A-Za-z]+\.? ?\d{0,2}|mid-[A-Za-z]+)',item,re.I)
    if ms: season="through "+clean(ms.group(1))
    elif re.search(r'[A-Z][a-z]+\.? ?\d{1,2}\s*[-–]\s*[A-Z][a-z]+',item): season="seasonal"
    fields=[f'date:"{wsat}"','weekly:true']
    if season: fields.append(f'season:"{esc(season)}"')
    fields.append('for:['+','.join('"%s"'%a for a in aud)+']')
    fields.append(f'dayLabel:"{esc(sched)}"')
    fields.append(f'cat:"{esc(label)}", icon:"{icon}", grad:["{grad[0]}","{grad[1]}"], title:"{esc(title)}"')
    fields.append(f'where:"{esc(where)}"')
    fields.append(f'desc:"{esc(desc)}"')
    fields.append(f'wx:null, info:J, map:"{esc(where)}, Trinity County, CA"')
    return "  { "+", ".join(fields)+" }"

def horizon_cards(dated, we):
    fut=[e for e in dated if e['date']>we]
    fut.sort(key=lambda e:e['date'])
    picks=[e for e in fut if is_featured(e['title'],e['detail'],classify(e['title'],e['detail']))
           or any(k in e['title'].lower() for k in ('festival','annual','christmas','new year','homecoming','fair'))]
    picks=picks[:9]
    cards=[]
    for e in picks:
        sd=e['date']; ed=e.get('end')
        day=str(sd.day)+("–%d"%ed.day if ed and ed!=sd else "")
        where=extract_where(e['detail']) or "Trinity County"
        cards.append(f'      <div class="hz-card"><div class="hz-when"><div class="hz-mo">{sd.strftime("%b")}</div>'
                     f'<div class="hz-day">{day}</div></div><div class="hz-body">'
                     f'<div class="hz-title">{html.escape(e["title"])}</div>'
                     f'<div class="hz-where">{html.escape(where)}</div></div></div>')
    return "\n".join(cards)

def main():
    cal=open(sys.argv[1],encoding='utf-8').read()
    tpl=open(sys.argv[2],encoding='utf-8').read()
    out=sys.argv[3]
    anchor,weekly,recurring,dated=parse(cal)
    if len(sys.argv)>4: anchor=datetime.date.fromisoformat(sys.argv[4])
    ws=anchor; we=anchor+datetime.timedelta(days=15)
    # nearest Saturday for weekly card dates (sort anchor)
    wsat=(ws+datetime.timedelta(days=(5-ws.weekday())%7)).isoformat()

    in_window=[e for e in dated if ws<=e['date']<=we]
    in_window+=expand_recurring(recurring,ws,we)
    seen=set(); dedup=[]
    for e in sorted(in_window,key=lambda e:(e['date'],e['title'])):
        k=(e['date'], re.sub(r'[^a-z0-9]','',e['title'].lower())[:22])
        if k in seen: continue
        seen.add(k); dedup.append(e)
    in_window=dedup

    weekly_js=[weekly_obj(t,i,wsat) for (t,i) in weekly]
    weekly_js.append(ATMOVIES.replace("__WSAT__",wsat))
    dated_js=[ev_obj(e) for e in in_window]

    events_block="const EVENTS = [\n  // ----- recurring weekly -----\n"+",\n".join(weekly_js)+",\n  // ----- dated -----\n"+",\n".join(dated_js)+"\n];"
    tpl=re.sub(r'const EVENTS = \[.*?\n\];', lambda m: events_block, tpl, count=1, flags=re.S)

    # horizon strip
    hz=horizon_cards(dated,we)
    tpl=re.sub(r'(<div class="hz-strip">\n).*?(\n    </div>)', lambda m: m.group(1)+hz+m.group(2), tpl, count=1, flags=re.S)

    # header date span / updated / count
    span=f"{DOW_ABBR[ws.weekday()]} {ws.strftime('%b')} {ws.day} – {DOW_ABBR[we.weekday()]} {we.strftime('%b')} {we.day}, {we.year}"
    tpl=re.sub(r'data-icon="calendar">[^<]+<', f'data-icon="calendar">{span}<', tpl, count=1)
    today=datetime.date.today()
    upd=f"Updated {ws.strftime('%b')} {ws.day}, {ws.year}"
    tpl=re.sub(r'data-icon="refresh">[^<]+<', f'data-icon="refresh">{upd}<', tpl, count=1)
    total=len(in_window)+len(weekly_js)
    tpl=re.sub(r'(id="metaCount">)[^<]+<', r'\g<1>'+str(total)+' events<', tpl, count=1)

    # matchWhen windows: weekend = Fri-Sun of anchor week; thisweek = ws..ws+6; nextweek = ws+7..we
    wend=ws+datetime.timedelta(days=(6-ws.weekday()) if ws.weekday()<=6 else 0)
    weekend_start=ws; weekend_end=ws+datetime.timedelta(days=(6-ws.weekday())) if ws.weekday()>=4 else ws+datetime.timedelta(days=(5-ws.weekday()))
    # simpler: weekend = anchor .. anchor+2 ; thisweek = anchor..+6 ; nextweek = anchor+7..we
    wk_end=(ws+datetime.timedelta(days=2)).isoformat()
    tw_end=(ws+datetime.timedelta(days=6)).isoformat()
    nw_start=(ws+datetime.timedelta(days=7)).isoformat()
    tpl=re.sub(r"(whenState==='weekend'\)\s*return e\.date>=')[^']+(' && e\.date<=')[^']+(')",
               rf"\g<1>{ws.isoformat()}\g<2>{wk_end}\g<3>",tpl)
    tpl=re.sub(r"(whenState==='thisweek'\)\s*return e\.date>=')[^']+(' && e\.date<=')[^']+(')",
               rf"\g<1>{ws.isoformat()}\g<2>{tw_end}\g<3>",tpl)
    tpl=re.sub(r"(whenState==='nextweek'\)\s*return e\.date>=')[^']+(' && e\.date<=')[^']+(')",
               rf"\g<1>{nw_start}\g<2>{we.isoformat()}\g<3>",tpl)

    open(out,'w',encoding='utf-8').write(tpl)
    print(f"anchor={anchor} window={ws}..{we}")
    print(f"weekly={len(weekly_js)} dated_in_window={len(in_window)} total={total}")
    print("STATUS legend: [locked]=registry cat+desc  [cat-only]=registry cat, session writes desc  [NEW]=verify cat + write desc")
    for e in in_window:
        c,a,f,d,st=curate(e['title'],e['detail'])
        tag='NEW' if st=='new' else st
        print(f"  {e['date']} [{c:9}] {'*' if f else ' '} {tag:8} {a} {e['title'][:46]}")

if __name__=="__main__":
    main()
