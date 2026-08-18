# Corrections

Every value in this repository that changes gets an entry here: what it was, what it is, and
what caused the change. Entries are **appended, never rewritten** — an entry edited later is no
longer evidence of anything.

The bar for an entry is *someone could have used the old value*, not *the change was
embarrassing*. A corrected county assignment ships as a new version rather than as a silent
edit, because the whole point of a citable definition is that two analyses citing the same
version got the same counties.

Newest first. Report an error by opening an issue — see
[Found an error?](README.md#found-an-error) in the README.

---

## 2026-08-18 — first public release, v1.0.0

The definitions and the crosswalk were already in use internally before this repository
existed. Two corrections were made in the course of publishing them, and both are recorded
here rather than left in the diff, because the values they replaced had circulated.

### The city list was rebuilt on a Census crosswalk

**Was:** a list of 680 PIC-12 city names derived from the city and county fields on EPA
Facility Registry Service records.
**Is:** 614 observed city names admitted only when at least half of that name's observed
facilities sit on a ZIP the Census 2020 ZCTA-to-county relationship file places inside PIC-12,
plus 261 ZIPs, which are the preferred lookup.

**Cause.** FRS carries whatever county string the filer typed. Three facilities with ZIP 43229
— Columbus, in Franklin County — filed counties ASHTABULA, GEAUGA and PORTAGE. A facility with
ZIP 45501 filed county GEAUGA while carrying FIPS 39023, which is Clark, on the same row; one
with ZIP 45873 filed CUYAHOGA while carrying 39125, which is Paulding. Those rows put COLUMBUS,
SPRINGFIELD and OAKWOOD into the city list, and any later analysis matching on city name then
swept in records from the other Ohio town of the same name.

**Measured effect.** On the patent lane, the contaminated list produced a base of 3,147
applications where the crosswalk produces 2,872 — 275 applications, 8.7 percent, that were
never Northeast Ohio's. 296 of the 3,147 (9.4 percent) carried at least one inventor matched
only by a city name the crosswalk rejects; Columbus alone accounted for 479 inventor mentions.

**Why it survived.** The published headline the contaminated base fed moved by less than half a
percentage point. A defect that does not move the headline is the kind that survives review.

**Known cost of the fix.** The crosswalk assigns each ZIP tabulation area to the county holding
its largest piece of land, which under-covers at the edge: 18 areas with genuine PIC-12 land
lose the area contest to an outside county, so Fredericksburg, Minerva, Magnolia, Vermilion,
Wilmot and Dundee — 146 facility records in real PIC-12 places — are excluded. That is the same
class of error running the other direction. It is smaller, and it is now stated in the README
rather than left to be discovered.

### The crosswalk's own `meta.replaces` note carried two figures that do not reproduce

**Was:** "contaminating 9.8% of the patent base and 634 SBIR awards."
**Is:** a description of the same defect using the figures that reproduce against the committed
artifacts — 296 of 3,147 applications, 9.4 percent, and 275 applications dropped.

**Cause.** Neither the 9.8 percent nor the 634 could be reproduced when the file was prepared
for publication. Re-running the comparison gives 296 applications touched and 275 dropped, not
309; on the award lane it gives 665 dropped and 649 attributable to Columbus, not 634. The
originals were most likely measured against a slightly different vintage of the source
downloads, which are refreshed in place and are not committed. Whatever the cause, a figure
that cannot be reproduced from the artifacts shipped alongside it does not belong in those
artifacts, so it was replaced with one that can be.

**Note on scope.** Fixing the note is not the same as fixing the affected award lane. The
analysis that produced the award figure is not part of this repository and, at the time of this
release, still reads the old FRS-derived city list. Migrating it is a data-correctness change to
that analysis, and it belongs in that repository's log, not this one.
