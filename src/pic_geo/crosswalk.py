"""ZIP-to-county and city-to-county lookup for the PIC-12 footprint.

WHY THIS FILE EXISTS, AND WHAT IT REPLACES. An earlier version of this lookup derived its city
names from the city/county pairs on EPA Facility Registry Service (FRS) records. FRS carries
whatever county string the filer typed, and it is wrong often enough to reach published
numbers. Three contradictions from a single FRS extract, each a real row:

  - A facility with ZIP 43229 — Columbus, in Franklin County — filed with county "ASHTABULA".
    Two more 43229 facilities filed "GEAUGA" and "PORTAGE".
  - A facility with ZIP 45501 — Springfield, in Clark County — filed county "GEAUGA" while
    the FIPS code on the same row read 39023, which IS Clark. The row disagreed with itself.
  - A facility with ZIP 45873 — Oakwood, in Paulding County — filed county "CUYAHOGA" with
    FIPS 39125 on the same row, which IS Paulding.

Those rows put COLUMBUS, SPRINGFIELD and OAKWOOD into a PIC-12 city list, and matching later
sources on city NAME then swept in every record from the other Ohio town of the same name.
Measured on the patent lane: the contaminated list produced a base of 3,147 applications where
the authoritative crosswalk produces 2,872 — 275 applications, 8.7 percent, that were never
Northeast Ohio's. 296 of the 3,147 (9.4 percent) carried at least one inventor matched only by
a city name this crosswalk rejects, Columbus alone accounting for 479 inventor mentions.

BLANKET-EXCLUDING AMBIGUOUS NAMES IS ALSO WRONG. Clinton, Green, Newton Falls, Jefferson,
Madison and Troy are all genuine PIC-12 towns that share a name with an Ohio town elsewhere.
So are Springfield and Oakwood — the defect was never those names, it was the far-away places
wearing them. The only correct fix is an authoritative ZIP-to-county crosswalk, which is what
this builds and what this repository ships.

SOURCE. The Census 2020 ZCTA-to-county relationship file, pipe-delimited, 47,863 data rows
covering 33,791 ZCTAs nationally. It is public domain. It is 6.5 MB and is NOT committed here;
`build()` fetches and caches it, and the derived output is what ships.

A ZCTA CAN STRADDLE COUNTY LINES, and 73 of the 261 admitted ones do. `AREALAND_PART` gives
the land area of each ZCTA-county piece, so each ZCTA is assigned to the county holding its
LARGEST piece. Assigning to every county it touches double-counts; assigning to none drops it.
The margin can be thin: ZCTA 44685 (Uniontown) is 51.6 percent Summit land and 48.4 percent
Stark, and is recorded as Summit.

THE SAME RULE UNDER-COVERS AT THE EDGE, AND THAT IS A REAL LIMITATION. 18 ZCTAs hold genuine
PIC-12 land but lose the area contest to a county outside the footprint, so they are absent
from `zips()` entirely. Two are close: 44627 Fredericksburg is 60,084,588 m2 Wayne against
62,890,289 m2 Holmes, and 44657 Minerva is 56,859,340 m2 Stark against 59,665,738 m2 Carroll.
Both fall outside. This is the same class of error as the FRS defect above, running the other
direction, and it is smaller and disclosed rather than large and silent.

A ZCTA IS NOT A ZIP CODE. The crosswalk covers ZCTAs, which are Census tabulation areas built
from residential mail delivery. PO-box-only, firm/unique and very small ZIPs have no ZCTA and
therefore no row at any margin. Verified absent from the source file: 44636 (Kidron, Wayne
County), 44416 (Ellsworth, Mahoning), 44033 (East Claridon, Geauga), 44422 (Greenford,
Mahoning), 44088 (Unionville, Ashtabula), 44316 (a small Akron ZIP), and the Akron PO box
ranges 44309 and 44398. A record carrying one of those ZIPs falls outside the footprint
with no warning. Check for that case; do not assume a miss means "not in the region".

WHAT A CITY NAME IS AND IS NOT. City is a POSTAL name, not a jurisdiction — mail addressed to
"Akron" reaches several townships and touches more than one county's edge. City matching is
offered only because some sources (USPTO inventor residences) carry no ZIP at all. PREFER
`county_of_zip()` WHEREVER A ZIP EXISTS.
"""

import collections
import json
import os
import urllib.request
from pathlib import Path

# How this fetch identifies itself, as ONE constant rather than a string typed into every
# request — the day a contact has to change should not be a repository-wide sweep.
#
# Census and the other federal data hosts run "polite pools": send a real contact and you get
# the higher rate limit and a warning email instead of a silent ban. There is deliberately no
# address baked in here. A published default would either be an individual's inbox, which does
# not belong in a public repository, or a mailbox nobody reads — and an address that bounces is
# worse than none, because the polite pools use it to tell you that you are doing something
# wrong. Set PIC_CONTACT to a monitored mailbox if you are going to fetch more than once; a
# single 6.5 MB download of a static file does not need it.
CONTACT = os.environ.get("PIC_CONTACT", "")
UA = {"User-Agent": f"pic-geo/1.0 ({CONTACT})" if CONTACT else "pic-geo/1.0"}

REL_URL = ("https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
           "tab20_zcta520_county20_natl.txt")

_HERE = Path(__file__).resolve().parent
_GEO = None  # loaded once, on first use


def geo_path():
    """Where `pic12_geo.json` is on this installation.

    An installed wheel carries it as package data; a source checkout has it at `data/` in the
    repository root. Both are checked rather than assuming which kind of tree this is.
    """
    packaged = _HERE / "data" / "pic12_geo.json"
    if packaged.exists():
        return packaged
    checkout = _HERE.parents[1] / "data" / "pic12_geo.json"
    if checkout.exists():
        return checkout
    raise FileNotFoundError(
        "pic12_geo.json not found next to the package or at <repo>/data/. It is the shipped "
        "product of this repository; a missing copy means a broken install, not a build step."
    )


def load_geo():
    """Load and cache the full crosswalk file: meta, zips, cities, rejected_cities."""
    global _GEO
    if _GEO is None:
        with open(geo_path(), encoding="utf-8") as fh:
            _GEO = json.load(fh)
    return _GEO


def zips():
    """{5-digit ZIP string: county name} for the 261 PIC-12 ZCTAs. Values are NAMES, not FIPS.

    A county name maps back to a FIPS code through `pic_geo.PIC12`. The authoritative
    direction is ZIP to county; do not read a name here as a jurisdiction boundary.
    """
    return load_geo()["zips"]


def cities():
    """{UPPER-CASE city string: county name} for city-only sources. Read the caveats first.

    A key is a city string exactly as it was observed in the source facility records, so the
    dictionary contains township forms, punctuation and a handful of malformed entries. The
    count of keys is a count of observed STRINGS, not of towns. A value is the PLURALITY
    county among that name's in-footprint observations, so for a name spanning two PIC-12
    counties it is a best guess and can be wrong for an individual record.
    """
    return load_geo()["cities"]


def county_of_zip(code, default=None):
    """County name for a 5-digit ZIP, or `default` if it is not in the PIC-12 footprint.

    Takes the first five characters, so ZIP+4 works. A miss means "no PIC-12 ZCTA", which is
    not the same as "not in Northeast Ohio" — see the PO-box note in the module docstring.
    """
    return zips().get(str(code).strip()[:5], default)


def county_of_city(name, default=None):
    """County name for a city string, or `default`. Case-insensitive. Use ZIPs if you have them.

    City matching exists for sources that carry no ZIP at all. A city is a postal name, and
    coverage here is limited to names observed on regulated facilities: a PIC-12 town with no
    regulated facility has no entry and will read as outside the footprint. That is a
    one-directional undercount, and it is why this is the fallback and not the default.
    """
    return cities().get(str(name).strip().upper(), default)


def rejected_cities():
    """{city string: why it was rejected} — a diagnostic ledger, NOT a blocklist to reuse.

    Several entries are real PIC-12 places rejected by the ZCTA-boundary artifact described in
    the module docstring: Vermilion, Minerva and Fredericksburg among them. Reusing this as an
    exclusion list would bake that artifact into a second analysis.
    """
    return load_geo()["rejected_cities"]


# ---------------------------------------------------------------------------------------
# The build. Everything below regenerates data/pic12_geo.json and needs the 6.5 MB Census
# file. Nothing above it touches the network, so importing this module is always cheap.
# ---------------------------------------------------------------------------------------

def fetch_relationship_file(cache_path, force=False):
    """Download the Census relationship file to `cache_path` unless a plausible copy exists.

    The existence-and-size guard is deliberately crude and has a known cost: a corrupt
    download larger than the floor is kept forever, and moving to a future decennial vintage
    means deleting the cache by hand. `force=True` is that hand.
    """
    cache_path = Path(cache_path)
    if not force and cache_path.exists() and cache_path.stat().st_size >= 1_000_000:
        return cache_path
    req = urllib.request.Request(REL_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    if len(data) < 1_000_000:
        raise SystemExit(f"FATAL: got {len(data):,} bytes from Census, expected ~6.5 MB. "
                         f"A short response here is usually an error page, not a file.")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return cache_path


def build_zips(cache_path):
    """{ZIP: county name} for PIC-12, from the cached relationship file.

    One row per ZCTA-county piece. Each ZCTA is kept against the county holding its largest
    `AREALAND_PART`; see the straddle discussion in the module docstring for why one county
    and not all of them.
    """
    from . import PIC12  # imported here so this module has no import-time dependency on it

    best = {}  # zcta -> (county fips, land area of that piece)
    with open(cache_path, encoding="utf-8-sig", errors="replace") as fh:
        header = fh.readline().rstrip("\n").split("|")
        i_zcta = header.index("GEOID_ZCTA5_20")
        i_county = header.index("GEOID_COUNTY_20")
        i_area = header.index("AREALAND_PART")
        for line in fh:
            parts = line.rstrip("\n").split("|")
            if len(parts) <= max(i_zcta, i_county, i_area):
                continue
            zcta = parts[i_zcta].strip()
            county = parts[i_county].strip()
            if not zcta or not county:
                # ~900 rows are county-only records with a blank ZCTA. Not an error.
                continue
            try:
                area = int(parts[i_area].strip() or 0)
            except ValueError:
                area = 0
            if zcta not in best or area > best[zcta][1]:
                best[zcta] = (county, area)

    out = {z: PIC12[c] for z, (c, _) in best.items() if c in PIC12}
    if len(out) < 150:
        raise SystemExit(f"FATAL: only {len(out)} PIC-12 ZCTAs. Expected 261; the relationship "
                         f"file's columns or the county FIPS set is wrong.")
    return dict(sorted(out.items()))


def build_cities(zip_lookup, facility_rows, threshold=0.5):
    """({city: county}, {city: reason}) from city/ZIP observations, judged by the ZIP lookup.

    `facility_rows` is an iterable of mappings with "city" and "postal" keys — EPA FRS
    extracts, in practice. The observations supply which city strings exist and what ZIPs
    they appear with; the crosswalk supplies the truth about which ZIPs are in the footprint.
    Neither is sufficient alone, which is the whole lesson of this file.

    A name is admitted when at least `threshold` of its observed facilities sit on PIC-12
    ZIPs, and is labeled with the plurality county among those. The threshold is a coin flip
    at the margin and is decided by facility COUNTS, not by population or land area.
    """
    obs = collections.defaultdict(lambda: [0, 0, collections.Counter()])
    for row in facility_rows:
        city = (row.get("city") or "").strip().upper()
        code = (row.get("postal") or "").strip()[:5]
        if not city or not code.isdigit() or code == "00000":
            continue
        rec = obs[city]
        rec[1] += 1
        if code in zip_lookup:
            rec[0] += 1
            rec[2][zip_lookup[code]] += 1

    admitted, rejected = {}, {}
    for city, (inside, total, counts) in obs.items():
        if not total:
            continue
        if inside / total >= threshold:
            admitted[city] = counts.most_common(1)[0][0]
        else:
            rejected[city] = f"{inside}/{total} facilities on PIC-12 ZIPs"
    return dict(sorted(admitted.items())), dict(sorted(rejected.items()))


def build(out_path=None, cache_path=None, facilities_path=None, force_fetch=False):
    """Regenerate pic12_geo.json. Returns the dict it wrote.

    `facilities_path` is a JSON file with an "frs" list of facility records, used only for the
    city names. It is NOT part of this repository — the facility extract carries site-level
    records that are not ours to republish. Without it the city half cannot be rebuilt, so
    this raises rather than writing a file with an empty `cities` block: a silently empty city
    list makes every downstream city match miss, which reads as "no activity in the region"
    instead of as a broken build. Pass `facilities_path=False` to accept that explicitly.
    """
    from . import PIC12

    out_path = Path(out_path) if out_path else geo_path()
    cache_path = Path(cache_path) if cache_path else out_path.parent / "_zcta_county.txt"

    fetch_relationship_file(cache_path, force=force_fetch)
    zip_lookup = build_zips(cache_path)

    if facilities_path is False:
        if out_path == geo_path():
            raise SystemExit(
                "FATAL: refusing to overwrite the shipped crosswalk with an empty city list. "
                "A ZIP-only rebuild is a legitimate thing to want — pass out_path to put it "
                "somewhere else and diff it against the shipped file."
            )
        city_lookup, rejected = {}, {}
    else:
        if facilities_path is None:
            raise SystemExit(
                "FATAL: no facility extract given, so the city names cannot be rebuilt. Pass "
                "facilities_path=<file with an 'frs' list>, or facilities_path=False to write "
                "a ZIP-only crosswalk on purpose. Writing an empty city list by accident is "
                "the failure this refuses to commit."
            )
        with open(facilities_path, encoding="utf-8") as fh:
            rows = json.load(fh)["frs"]
        city_lookup, rejected = build_cities(zip_lookup, rows)
        if len(city_lookup) < 400:
            raise SystemExit(f"FATAL: only {len(city_lookup)} city names admitted. Expected "
                             f"~614; the facility extract is truncated or its keys changed.")

    out = {
        "meta": {
            "source": "Census 2020 ZCTA-to-county relationship file; city names cross-checked "
                      "against epa.json facility ZIPs",
            "zcta_straddles_counties": "assigned to the county holding the largest "
                                       "AREALAND_PART; assigning to both double-counts, to "
                                       "neither drops it",
            "city_is_a_postal_name": "not a jurisdiction. Prefer ZIP matching wherever a ZIP "
                                     "exists; city matching exists for sources like USPTO "
                                     "that carry none.",
            "city_rule": "admitted when >=50% of that name's observed facilities sit on "
                         "PIC-12 ZIPs",
            "replaces": "_pic12_cities.json, whose city names came from EPA FRS county fields. "
                        "Those are unreliable: three rows for ZIP 43229 (Columbus, in Franklin "
                        "County) filed counties ASHTABULA, GEAUGA and PORTAGE, which let "
                        "COLUMBUS into the footprint. Matching later sources on city name then "
                        "swept in records from the other Ohio town of the same name — on the "
                        "patent lane the contaminated list produced a base of 3,147 "
                        "applications where this crosswalk produces 2,872, and 296 of those "
                        "3,147 (9.4%) carried at least one inventor matched only by a city "
                        "name this crosswalk rejects.",
            "counties": dict(PIC12),
            "n_zips": len(zip_lookup),
            "n_cities": len(city_lookup),
        },
        "zips": zip_lookup,
        "cities": city_lookup,
        "rejected_cities": rejected,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


if __name__ == "__main__":
    import sys

    facilities = sys.argv[1] if len(sys.argv) > 1 else None
    result = build(facilities_path=facilities)
    print(f"wrote {geo_path()} — {result['meta']['n_zips']:,} ZIPs, "
          f"{result['meta']['n_cities']:,} city names")
