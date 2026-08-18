# pic-geo

The county footprints the Polymer Industry Cluster measures against, and an authoritative
ZIP-to-county crosswalk for the larger of them — published by the Polymer Industry Cluster at
the Greater Akron Chamber so that every analysis of the Northeast Ohio polymer economy, ours
or yours, can agree on which counties it is talking about.

It is deliberately small: two dictionaries, one JSON crosswalk, no runtime dependencies. If
you are reconciling a PIC figure against your own numbers, the answer to "which counties?" is
here, in code, with a version you can cite.

```python
import pic_geo

pic_geo.PIC12                     # {"39007": "Ashtabula", ... } — 12 counties, by FIPS
pic_geo.county_of_zip("44685")    # "Summit"
pic_geo.county_of_zip("43229")    # None — Columbus is not in the footprint
pic_geo.footprint("pic12")        # the metadata block to stamp on your output
```

Install from a tag, so what you cite is what you ran. `v1.0.0` is the first release:

```bash
pip install "pic-geo @ git+https://github.com/polymerindustrycluster/pic-geo@v1.0.0"
```

Until a tag you need exists, `@main` works and is not citable.

## Two footprints, and they never reconcile

PIC carries two county definitions, for a reason that is historical and is not going away:

- **PIC-12** (12 counties) is the official footprint, the one the cluster-health dashboard
  reports against. Analyses built on federal data use it, so their figures reconcile with the
  dashboard.
- **NEO-14** (14 counties) is the set the PIC company vault tags companies with. Analyses
  built on those company records stay on it, because that is how the records are tagged.

**They share only 10 counties, and there is no arithmetic that converts between them.** PIC-12
alone holds Ashtabula and Trumbull. NEO-14 alone holds Crawford, Huron, Richland and
Tuscarawas. Neither contains the other. Adding a PIC-12 total to a NEO-14 total double-counts
ten counties and omits six; treating one as a "regional" version of the other is wrong in both
directions. Any figure quoted from PIC work should name the footprint it came from, and two
figures on different footprints should never be presented as if they compare.

**"NEO-14" is a misleading name and outsiders reliably get it wrong.** It is bigger by count
but it is not the bigger northeast-Ohio set: it drops Ashtabula and Trumbull, which are
unambiguously northeast Ohio, and picks up Crawford (Bucyrus) and Richland (Mansfield), which
are north-central Ohio some 60 to 90 miles from Cleveland. Read the lists, not the label.

**Neither footprint is a Census-defined region.** PIC-12 is not the Cleveland-Akron-Canton CSA,
not a union of metropolitan statistical areas, and not a JobsOhio or ODOT region. Carroll
County, for instance, is in the Canton-Massillon MSA and in neither footprint. Substituting a
standard Census geography because it is easier to pull produces numbers that fail to reconcile
with everything published against these definitions, and fail quietly.

`pic_geo.SHARED` gives the ten shared FIPS codes, `pic_geo.PIC12_ONLY` and
`pic_geo.NEO14_ONLY` the six that are not. `tests/test_footprints.py` fails if the two
footprints are ever made identical, made to nest, or given prose that stops matching the
actual difference between them.

## Why the crosswalk exists, and why you want ours

`data/pic12_geo.json` maps 261 ZIP codes and 614 observed city names to PIC-12 counties. It is
built from the U.S. Census Bureau 2020 ZCTA-to-county relationship file. It exists because the
obvious shortcut — reading the county off the records you already have — produced published
numbers that were wrong.

The earlier version of this lookup took its city names from the city and county fields on EPA
Facility Registry Service records. FRS carries whatever county string the filer typed, and it
is wrong often enough to matter. Three rows from a single extract, each real:

- Three facilities with ZIP **43229** — that is Columbus, in **Franklin County**, three hours
  from Akron — filed their counties as **ASHTABULA**, **GEAUGA** and **PORTAGE**.
- A facility with ZIP **45501** — Springfield, in **Clark County** — filed county **GEAUGA**
  while the FIPS code on the same row read 39023, which *is* Clark. The row contradicted
  itself.
- A facility with ZIP **45873** — Oakwood, in **Paulding County** — filed county **CUYAHOGA**
  with FIPS 39125 on the same row, which *is* Paulding.

Those rows put COLUMBUS, SPRINGFIELD and OAKWOOD into a list of PIC-12 city names. Then every
later analysis that matched on city name — patents, awards, registrations, anything without a
usable ZIP — swept in records from the *other* Ohio town of the same name.

Measured on the patent lane: the contaminated list produced a base of **3,147** applications
where this crosswalk produces **2,872**. That is 275 applications, **8.7 percent**, that were
never Northeast Ohio's. **296 of the 3,147 (9.4 percent)** carried at least one inventor
matched only by a city name this crosswalk rejects, with Columbus alone accounting for 479
inventor mentions. The published headline barely moved, which is exactly why the defect
survived review for as long as it did.

**Banning ambiguous names is not the fix.** Clinton, Green, Newton Falls, Jefferson, Madison
and Troy are all genuine PIC-12 towns that share a name with an Ohio town somewhere else. So
are Springfield and Oakwood — the defect was never those names, it was the distant places
wearing them. A blanket name ban would have thrown away real towns to remove fake ones. The
only correct fix is an authoritative ZIP-to-county crosswalk, which is what this is.

**A ZIP code area can straddle a county line**, and 73 of the 261 here do. Each one is assigned
to the county holding the largest share of its land, because assigning it to every county it
touches double-counts and assigning it to none drops it. The margin can be thin: ZCTA 44685
(Uniontown) is 51.6 percent Summit land and 48.4 percent Stark, and is recorded as Summit.

## What this cannot tell you

Read this section before you use the city list for anything.

**Prefer ZIPs. Always, wherever a ZIP exists.** `county_of_zip()` is an authoritative
assignment. `county_of_city()` is a fallback that exists because some sources — USPTO inventor
residences, for one — carry no ZIP at all.

**A city is a postal name, not a jurisdiction.** Mail addressed to "Akron" reaches several
townships and more than one county's edge. A city's county here is the *plurality* county
among that name's observations, so for a name spanning two PIC-12 counties it is a best guess
that can be wrong for an individual record. The 614 keys are a count of distinct observed
*strings*, not of towns: the file contains township forms, punctuation, and a handful of
malformed entries carried through verbatim rather than silently cleaned. Do not quote it as
"614 cities."

**The same largest-land-piece rule under-covers at the edge, and that is a real limitation.**
18 ZCTAs hold genuine PIC-12 land but lose the area contest to a county outside the footprint,
so they are absent from the ZIP lookup entirely. Two are close: 44627 Fredericksburg is
60,084,588 m² Wayne against 62,890,289 m² Holmes, and 44657 Minerva is 56,859,340 m² Stark
against 59,665,738 m² Carroll. Both fall outside. That cascades into the city list, where
Fredericksburg, Minerva, Magnolia, Vermilion, Wilmot and Dundee are all rejected at 0 percent
— 146 facility records in genuine PIC-12 places, excluded. This is the same class of error as
the FRS defect above, running the other direction. It is smaller, and it is disclosed here
rather than left to be found.

**A ZCTA is not a ZIP Code.** The crosswalk covers Census tabulation areas built from
residential mail delivery. PO-box-only, firm, and very small ZIPs have no ZCTA and therefore no
row at any margin. Verified absent from the source file: 44636 (Kidron, Wayne County), 44416
(Ellsworth, Mahoning), 44033 (East Claridon, Geauga), 44422 (Greenford, Mahoning), 44088
(Unionville, Ashtabula), 44316 (a small Akron ZIP), and the Akron PO box ranges 44309 and
44398. A record carrying one of those falls outside the footprint with no warning. If your
data is address-level, check for that case; a miss here is not proof of "not in the region."

**City coverage is biased by the source universe.** A city name is in the file only because a
regulated facility was observed there. A residential or office-only PIC-12 town with no
regulated facility has no entry and will read as outside the footprint. That is a systematic,
one-directional undercount, and it lands hardest on exactly the lane the city list serves —
matching people's home addresses.

**`rejected_cities` is a diagnostic ledger, not a blocklist.** Several entries are real PIC-12
places rejected by the boundary artifact described above. Reusing it as an exclusion list would
bake that artifact into a second analysis.

**Vintage.** This is 2020 ZCTA and 2020 county geography. ZCTA boundaries are redrawn each
decennial and USPS ZIP boundaries change continuously, so a ZIP assigned correctly for a 2020
record may be assigned differently for a 2015 or a 2025 one. The vintage is frozen on purpose
— an assignment that shifts under you is worse than one that is stated and old.

**And the limit no test catches:** the footprints themselves are organizational decisions, not
derivations. That PIC-12 is what the cluster-health dashboard reports against, and that NEO-14
is what the company vault tags against, are recorded here and are not verifiable from outside
PIC. What *is* verifiable, and is tested on every run, is that all 16 FIPS codes are the codes
the Census assigns to those county names.

## Reproduce it

```bash
# the tests are the specification: county counts, the exact ten-county intersection, every
# FIPS code re-derived from an independent list of Ohio's 88 counties, and a guard that fails
# if the two footprints are ever merged
uv sync --frozen
uv run pytest

# rebuild the ZIP half from Census (fetches ~6.5 MB, cached, public domain) and check it
# against the committed file — this should print True
uv run python -c "
from pic_geo import crosswalk
built = crosswalk.build(out_path='rebuilt.json', facilities_path=False)
print(built['zips'] == crosswalk.load_geo()['zips'])
"
```

What is committed: the definitions, the build script, and `data/pic12_geo.json`. What is not:
the 6.5 MB Census relationship file, which is re-fetchable by construction from the URL in
`src/pic_geo/crosswalk.py`, and the facility extract that supplies observed city names, which
is site-level records data that is not ours to republish. So the ZIP half of the crosswalk is
fully rebuildable from a clean clone and the city half is not — `build()` refuses to write a
file with an empty city list rather than producing one that silently matches nothing.

## Found an error?

Open an issue. Errors in this repository are the useful kind: a county assigned to the wrong
ZIP, a city name that should not be in the footprint or is missing from it, a FIPS code that
does not match its name. Give the ZIP or the city string, what this file says, what you think
it should be, and how you know — a Census file, a USPS lookup, a local's knowledge of where the
township line runs.

Use the **Report an error in a published figure** template; its first field asks for a page, so
put `data/pic12_geo.json` or the ZIP itself there. Confirmed errors get a dated entry in
[CORRECTIONS.md](CORRECTIONS.md), and a corrected value ships as a new version rather than as a
silent edit — because the point of this repository is that two analyses citing the same version
got the same counties.

## License

Code: MIT — see [LICENSE](LICENSE).

Documentation and `data/pic12_geo.json`: CC BY 4.0 — see [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0).
Reuse the crosswalk with attribution to the Polymer Industry Cluster. The two licenses are two
files and are never concatenated, because license detectors read one file and report
"unrecognized" on a hybrid.

The upstream Census relationship file the crosswalk is derived from is a work of the U.S.
federal government and is in the public domain; the selection and county-assignment logic
applied to it is ours.

To cite, see [CITATION.cff](CITATION.cff). Cite the version you used. County footprints are
organizational decisions that can change, and the crosswalk is pinned to the 2020 decennial
vintage, so a figure quoted without a version is not reproducible.
