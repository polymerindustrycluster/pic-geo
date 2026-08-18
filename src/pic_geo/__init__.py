"""The two Northeast Ohio county footprints the Polymer Industry Cluster measures against.

DECISION (2026-08-14). Analyses built on FEDERAL data use PIC-12, so their figures reconcile
with the cluster-health dashboard. Analyses built on the PIC company vault stay on NEO-14,
because that is how company records are tagged. Every published page states which one it used.

The two share only 10 of their counties. Numbers computed on one do not reconcile with numbers
computed on the other, and must never be presented as if they do. There is no arithmetic that
converts between them: PIC-12 is not a subset of NEO-14 and NEO-14 is not a subset of PIC-12.
PIC-12 alone holds Ashtabula and Trumbull; NEO-14 alone holds Crawford, Huron, Richland and
Tuscarawas. Adding a PIC-12 total to a NEO-14 total double-counts ten counties and omits six.

NEO-14 IS A GEOGRAPHICALLY MISLEADING NAME and outside readers get it wrong in both
directions. It is larger by count (14 against 12) but it is NOT the bigger northeast-Ohio set:
it drops Ashtabula and Trumbull, which are unambiguously northeast Ohio, and it picks up
Crawford (Bucyrus) and Richland (Mansfield), which are north-central Ohio some 60 to 90 miles
from Cleveland. Read the lists, not the label.

NEITHER FOOTPRINT IS A CENSUS-DEFINED REGION. PIC-12 is not the Cleveland-Akron-Canton CSA,
not a union of metropolitan statistical areas, and not a JobsOhio or ODOT region. Carroll
County (39019), for instance, sits in the Canton-Massillon MSA and in neither footprint.
Substituting a standard Census geography "for convenience" produces numbers that silently
fail to reconcile with everything published against these definitions.

PROVENANCE, STATED HONESTLY. PIC-12 is the footprint PIC's cluster-health dashboard reports
against; NEO-14 is the set the PIC company vault tags companies with. Both are organizational
decisions recorded here, not derivations from a public source, and neither is independently
verifiable from outside PIC. What IS verifiable from outside, and is tested in this
repository, is that all 16 distinct FIPS codes below are correct Ohio county codes attached
to the correct county names.
"""

# The definitions. Copied from the internal build tree, then checked code-by-code against the
# official Ohio county FIPS list; `tests/test_footprints.py` re-checks the structure on every
# run. PIC-12 is ordered by ascending FIPS. NEO-14 is deliberately left in the order the vault
# supplied it, so a diff against the vault's own list stays readable.
PIC12 = {
    "39007": "Ashtabula", "39035": "Cuyahoga", "39055": "Geauga", "39085": "Lake",
    "39093": "Lorain", "39099": "Mahoning", "39103": "Medina", "39133": "Portage",
    "39151": "Stark", "39153": "Summit", "39155": "Trumbull", "39169": "Wayne",
}
NEO14 = {
    "39153": "Summit", "39035": "Cuyahoga", "39133": "Portage", "39151": "Stark",
    "39055": "Geauga", "39085": "Lake", "39093": "Lorain", "39103": "Medina",
    "39077": "Huron", "39099": "Mahoning", "39169": "Wayne", "39157": "Tuscarawas",
    "39139": "Richland", "39033": "Crawford",
}

SHARED = set(PIC12) & set(NEO14)

# The two difference sets, as symbols rather than as prose. They were previously carried in
# `META[...]["differs"]` sentences and hardcoded a third time in a fetch script, so a county
# change had to be made in three places and only one of them would fail if it was missed.
PIC12_ONLY = {f: PIC12[f] for f in PIC12 if f not in NEO14}
NEO14_ONLY = {f: NEO14[f] for f in NEO14 if f not in PIC12}

# The serialization contract. These blocks are embedded verbatim into every published dataset
# so a reader can tell which footprint produced the numbers in front of them. `key` and
# `counties` are read by no rendering code, but they ARE in the published JSON that outside
# parties cite, so they are not "unused fields" and must not be pruned. Field names and
# `label` values are frozen: renaming one requires regenerating every published dataset
# through rate-limited federal APIs.
#
# NOTE ON SHAPE — `META["pic12"]` and `META["neo14"]` are six-field dicts; `META["shared"]` is
# a bare list of county names. Naive iteration (`for k, v in META.items(): v["label"]`) raises
# TypeError on the "shared" key. Use `footprint()` or `FOOTPRINTS` instead of iterating META.
META = {
    "pic12": {"key": "pic12", "n": len(PIC12), "label": "PIC-12",
              "counties": sorted(PIC12.values()),
              "note": "PIC's official 12-county footprint, matching the cluster-health "
                      "dashboard. Chosen for federal-data pages so figures reconcile.",
              "differs": "Excludes Crawford, Huron, Richland and Tuscarawas, which the "
                         "vault's NEO-14 includes."},
    "neo14": {"key": "neo14", "n": len(NEO14), "label": "NEO-14",
              "counties": sorted(NEO14.values()),
              "note": "The 14-county set the GAC-PIC vault tags companies against. Kept "
                      "for vault-sourced pages because company records carry this flag.",
              "differs": "Excludes Ashtabula and Trumbull, which PIC-12 includes."},
    "shared": sorted(PIC12[c] for c in SHARED),
}

#: The two real footprint keys, for safe iteration over META. "shared" is not a footprint.
FOOTPRINTS = ("pic12", "neo14")

# Derived shapes. Consuming scripts need county identifiers in several forms — three-digit
# FIPS for the Census API, upper-case names for EPA extracts, title-case names for IPEDS.
# Every one of those was being re-derived inline or, worse, retyped as a fresh literal, which
# is how a footprint ends up defined in sixteen places. They are computed here so a county
# change is a one-line change.
PIC12_FIPS = frozenset(PIC12)                                    # {"39007", ...}
PIC12_FIPS3 = {f[2:]: n for f, n in PIC12.items()}               # {"007": "Ashtabula", ...}
PIC12_NAMES = frozenset(PIC12.values())                          # {"Ashtabula", ...}
PIC12_NAMES_UPPER = frozenset(n.upper() for n in PIC12.values())  # {"ASHTABULA", ...}

NEO14_FIPS = frozenset(NEO14)
NEO14_FIPS3 = {f[2:]: n for f, n in NEO14.items()}
NEO14_NAMES = frozenset(NEO14.values())
NEO14_NAMES_UPPER = frozenset(n.upper() for n in NEO14.values())

__version__ = "1.0.0"

__all__ = [
    "PIC12", "NEO14", "SHARED", "META", "FOOTPRINTS",
    "PIC12_ONLY", "NEO14_ONLY",
    "PIC12_FIPS", "PIC12_FIPS3", "PIC12_NAMES", "PIC12_NAMES_UPPER",
    "NEO14_FIPS", "NEO14_FIPS3", "NEO14_NAMES", "NEO14_NAMES_UPPER",
    "counties", "footprint", "in_footprint",
    "county_of_zip", "county_of_city", "load_geo", "zips", "cities", "rejected_cities",
    "__version__",
]


def counties(key="pic12"):
    """Return the {FIPS: county name} mapping for one footprint.

    Takes "pic12" or "neo14". Refuses anything else rather than returning an empty dict,
    because a silent empty footprint filters every row out and reads downstream as "the
    region has no data" instead of as an error.
    """
    if key == "pic12":
        return dict(PIC12)
    if key == "neo14":
        return dict(NEO14)
    raise KeyError(f"unknown footprint {key!r}; expected one of {FOOTPRINTS}")


def footprint(key="pic12"):
    """Return the six-field META block for one footprint, ready to embed in output metadata.

    Use this rather than `META[key]`: it rejects "shared", which is a list of county names
    and not a footprint, and which raises TypeError one line later if a caller treats the
    value as a dict.
    """
    if key not in FOOTPRINTS:
        raise KeyError(f"unknown footprint {key!r}; expected one of {FOOTPRINTS}. "
                       f'META["shared"] is a list of county names, not a footprint.')
    return dict(META[key])


def in_footprint(fips, key="pic12"):
    """True if a 5-digit county FIPS code is in the named footprint.

    Accepts a string. An int is rejected because "39007" cannot survive int() and back —
    leading zeros in FIPS codes are the oldest bug in county data.
    """
    if not isinstance(fips, str):
        raise TypeError(f"FIPS codes are strings, not {type(fips).__name__}; "
                        f"an int loses the leading zero in codes like 39007")
    return fips in counties(key)


# The ZIP and city crosswalk lives in its own module because it carries a data file and a
# fetch path. Re-exported here so that the common case is one import.
from .crosswalk import (  # noqa: E402  (definitions above must exist first)
    cities,
    county_of_city,
    county_of_zip,
    load_geo,
    rejected_cities,
    zips,
)
