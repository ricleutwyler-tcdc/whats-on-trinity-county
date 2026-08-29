#!/usr/bin/env python3
"""Post-process generated index.html: apply hand-curation overrides to the EVENTS block.
Matches each event object by a unique title substring and rewrites specific fields.
Fully auditable — every change is a keyed override below."""
import re, sys

def esc(s):  # JS double-quoted string
    return s.replace('\\','\\\\').replace('"','\\"')

# key substring -> {field: value}
# fields: title, cat(=(label,icon,g0,g1)), for(list), feat(bool), where, desc, map
OV = {
 # ---- weekly ----
 'title:"Weaverville Farmers Market"': {
    'season':'through mid-October' },
 'title:"Chess enthusiasts meet': {
    'title':'Chess Club' },
 'title:"Bingo 6 p.m. every Saturday"': {
    'title':'Bingo' },
 'title:"Karaoke", where:"Coffee Creek': {
    'where':'Coffee Creek Country Store, Trinity Center',
    'map':'Coffee Creek Country Store, Trinity Center, CA' },
 # ---- dated ----
 'Douglas City Fire Belles Summer Bake Sale': {
    'title':'Douglas City Fire Belles Summer Bake Sale',
    'desc':"Homemade treats for a good cause — the Fire Belles' summer bake sale at the Douglas City Fire Hall, 9 a.m. to noon.",
    'where':'Douglas City Fire Hall, Steiner Flat Road',
    'map':'Douglas City Fire Hall, Steiner Flat Road, Trinity County, CA' },
 'David Becker will be performing': {
    'title':'David Becker: "Planets"',
    'desc':'Grammy- and Emmy-nominated guitarist David Becker brings his acclaimed "Planets" show to the Performing Arts Center. $20 general, $15 student/senior.' },
 'Roaring Twenties Ladies Banquet': {
    'title':'Women for Wildlife: Roaring Twenties Ladies Banquet',
    'desc':"The Rocky Mountain Elk Foundation's Roaring Twenties fundraiser — dinner, auctions, and raffles at the Trinity Alps Restaurant & Lounge. Doors at 5 p.m., $45.",
    'for':['visitor','local'] },
 'Members-Only Karaoke Night': {
    'title':'Trinity Players Members-Only Karaoke Night',
    'desc':'A members-only karaoke night for Trinity Players at the Performing Arts Center — free for members.',
    'for':['local'],
    'where':'Trinity Alps Performing Arts Center, 30 Arbuckle Ct., Weaverville',
    'map':'Trinity Alps Performing Arts Center, Weaverville, CA' },
 'Ruth Lake Summer Festival': {
    'title':'31st annual Ruth Lake Summer Festival',
    'desc':'A full weekend at Ruth Lake — music, camping, fishing, vendor booths, food, and a Dutch raffle. Breakfast both mornings, 9 to 11 a.m.',
    'where':'Ruth Recreation Campground',
    'map':'Ruth Recreation Campground, Trinity County, CA' },
 'Hyampom Good Times Fair': {
    'desc':"A day in Hyampom — live music, raffle, silent art auction, kids' activities, local food and craft vendors, and a benefit dinner for the community hall." },
 'title:"Monthly Art Walk"': {
    'where':'Downtown Weaverville',
    'map':'Main Street, Weaverville, CA' },
 'Roderick/Hayfork Senior Center breakfast': {
    'where':'Roderick/Hayfork Senior Center, Hayfork',
    'map':'Roderick/Hayfork Senior Center, Hayfork, CA' },
 'Trinity Center Volunteer Fire Department Auxiliary pancake breakfast': {
    'desc':"The Volunteer Fire Department Auxiliary's pancake breakfast at the IOOF Hall. $13 adults, $7 kids 6–10, free for 5 and under." },
 'Community breakfast sponsored by the Six Rivers': {
    'where':'Ruth Lake CSD Community Hall, Mad River',
    'map':'Ruth Lake CSD Community Hall, Mad River, CA' },
 'High Country Cruisers Coffee and Classics': {
    'where':'Main St., Weaverville',
    'map':'Main Street, Weaverville, CA' },
 'Rupert Wates': {
    'desc':'UK-born singer-songwriter Rupert Wates plays a Sunday matinee at the Performing Arts Center. $20 general, $15 student/senior.' },
 'Trinity Lake Lions Club annual Fly-In BBQ': {
    'cat':('Cars','cars','#2E8E90','#1E7A6E'),
    'desc':"The Lions Club's annual Fly-In BBQ across from the Scott Museum — barbecued tri-tip and chicken, a show 'n' shine, live music from the Bohemian Muse Band, and local vendors.",
    'for':['visitor','local','family'],
    'feat':True,
    'where':'Scott Museum, Trinity Center',
    'map':'Scott Museum, Trinity Center, CA' },
 'Fall Countywide Yard Sale': {
    'desc':"The Journal's countywide fall yard sale — maps and listings in the Sept. 9 issue." },
 'Patriots Day Bunco': {
    'desc':'A bunco night hosted by the Junction City Fire Jills. $15 buy-in at the Community Center.' },
 'Artists in Action': {
    'desc':'Artists at work along Main Street — live music and hands-on art, 11 a.m. to 4 p.m.',
    'for':['visitor','local','family'],
    'where':'Main Street, Weaverville',
    'map':'Main Street, Weaverville, CA' },
 'Craft Fair and Swap Meet at the Hayfork VFW Hall': {
    'where':'Hayfork VFW Hall, Hayfork',
    'map':'Hayfork VFW Hall, Hayfork, CA' },
}

def apply_field(obj, field, val):
    if field=='title':
        return re.sub(r'title:"(?:[^"\\]|\\.)*"', 'title:"'+esc(val)+'"', obj, count=1)
    if field=='desc':
        return re.sub(r'desc:"(?:[^"\\]|\\.)*"', 'desc:"'+esc(val)+'"', obj, count=1)
    if field=='where':
        return re.sub(r'where:"(?:[^"\\]|\\.)*"', 'where:"'+esc(val)+'"', obj, count=1)
    if field=='map':
        return re.sub(r'map:"(?:[^"\\]|\\.)*"', 'map:"'+esc(val)+'"', obj, count=1)
    if field=='for':
        return re.sub(r'for:\[[^\]]*\]', 'for:['+','.join('"%s"'%a for a in val)+']', obj, count=1)
    if field=='season':
        return re.sub(r'season:"(?:[^"\\]|\\.)*"', 'season:"'+esc(val)+'"', obj, count=1)
    if field=='cat':
        label,icon,g0,g1=val
        return re.sub(r'cat:"(?:[^"\\]|\\.)*", icon:"[^"]*", grad:\["[^"]*","[^"]*"\]',
                      f'cat:"{esc(label)}", icon:"{icon}", grad:["{g0}","{g1}"]', obj, count=1)
    if field=='feat':
        if 'feat:true' in obj: return obj
        if val:  # insert after the for:[...] segment
            return re.sub(r'(for:\[[^\]]*\])', r'\1, feat:true', obj, count=1)
        return obj
    raise ValueError(field)

def main():
    p=sys.argv[1]
    t=open(p,encoding='utf-8').read()
    m=re.search(r'const EVENTS = \[.*?\n\];',t,re.S)
    block=m.group(0)
    hits={}
    def repl_obj(mo):
        obj=mo.group(0)
        for key,fields in OV.items():
            if key in obj:
                hits[key]=hits.get(key,0)+1
                for f,v in fields.items():
                    obj=apply_field(obj,f,v)
        return obj
    newblock=re.sub(r'\{[^{}]*\}', repl_obj, block)
    t=t.replace(block,newblock)
    open(p,'w',encoding='utf-8').write(t)
    # report
    for key in OV:
        n=hits.get(key,0)
        flag='OK ' if n==1 else ('MISS' if n==0 else 'DUP%d'%n)
        print(f'  [{flag}] {key[:60]}')

if __name__=='__main__':
    main()
