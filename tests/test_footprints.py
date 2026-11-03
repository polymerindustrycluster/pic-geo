"""Tests for the footprint definitions and the crosswalk they gate.

These are invariant tests, not smoke tests. Each one names a specific way this data has gone
wrong or could go wrong, and fails on that. The two worth understanding before editing:

  - `test_ohio_fips_codes_are_derivable_independently` rebuilds all 16 FIPS codes from a list
    of Ohio's 88 county NAMES rather than comparing them to a copy of the same codes. Checking
    codes against codes you typed twice proves you can type. This proves the code attached to
    each name is the code the Census assigns to that name.
  - `test_the_two_footprints_must_never_be_merged` is the guard against the failure that
    prompted this repository. It fails if the footprints are ever quietly made identical, made
    to nest, or given prose that no longer matches the actual difference between them.
"""

import ast
import json
import pathlib

import pytest

import pic_geo
from pic_geo import crosswalk

# ---------------------------------------------------------------------------------------
# Counts and membership
# ---------------------------------------------------------------------------------------


def test_footprint_sizes():
    assert len(pic_geo.PIC12) == 12
    assert len(pic_geo.NEO14) == 14
    # The published serialization carries the count. It is computed, but consumers embed it
    # into datasets that outlive this process, so it is pinned here too.
    assert pic_geo.META["pic12"]["n"] == 12
    assert pic_geo.META["neo14"]["n"] == 14


def test_shared_set_is_exactly_ten_counties():
    assert len(pic_geo.SHARED) == 10
    assert set(pic_geo.META["shared"]) == {
        "Cuyahoga", "Geauga", "Lake", "Lorain", "Mahoning",
        "Medina", "Portage", "Stark", "Summit", "Wayne",
    }
    # The module docstring states the number in prose. Prose does not recompute, so if the
    # county lists ever change this test is what stops the sentence from going stale silently.
    assert "share only 10" in pic_geo.__doc__


def test_pic12_excludes_the_four_north_central_counties():
    for name in ("Crawford", "Huron", "Richland", "Tuscarawas"):
        assert name not in pic_geo.PIC12.values()
        assert name in pic_geo.NEO14.values()


def test_neo14_excludes_ashtabula_and_trumbull():
    for name in ("Ashtabula", "Trumbull"):
        assert name not in pic_geo.NEO14.values()
        assert name in pic_geo.PIC12.values()


# ---------------------------------------------------------------------------------------
# FIPS integrity
# ---------------------------------------------------------------------------------------

# Ohio's 88 counties in alphabetical order. County FIPS codes are assigned alphabetically
# within a state, so the nth county's code is 2n-1 — which makes this NAME list an independent
# check on every code in the module, rather than a second copy of the codes.
OHIO_COUNTIES_ALPHABETICAL = """
Adams Allen Ashland Ashtabula Athens Auglaize Belmont Brown Butler Carroll
Champaign Clark Clermont Clinton Columbiana Coshocton Crawford Cuyahoga Darke Defiance
Delaware Erie Fairfield Fayette Franklin Fulton Gallia Geauga Greene Guernsey
Hamilton Hancock Hardin Harrison Henry Highland Hocking Holmes Huron Jackson
Jefferson Knox Lake Lawrence Licking Logan Lorain Lucas Madison Mahoning
Marion Medina Meigs Mercer Miami Monroe Montgomery Morgan Morrow Muskingum
Noble Ottawa Paulding Perry Pickaway Pike Portage Preble Putnam Richland
Ross Sandusky Scioto Seneca Shelby Stark Summit Trumbull Tuscarawas Union
VanWert Vinton Warren Washington Wayne Williams Wood Wyandot
""".split()

OHIO_FIPS_BY_NAME = {
    name: f"39{2 * rank - 1:03d}"
    for rank, name in enumerate(OHIO_COUNTIES_ALPHABETICAL, start=1)
}


def test_ohio_reference_table_is_well_formed():
    # If this fails, the reference list is wrong and every test using it is worthless.
    assert len(OHIO_COUNTIES_ALPHABETICAL) == 88
    assert OHIO_COUNTIES_ALPHABETICAL == sorted(OHIO_COUNTIES_ALPHABETICAL)
    assert OHIO_FIPS_BY_NAME["Adams"] == "39001"
    assert OHIO_FIPS_BY_NAME["Wyandot"] == "39175"


@pytest.mark.parametrize("footprint_key", pic_geo.FOOTPRINTS)
def test_ohio_fips_codes_are_derivable_independently(footprint_key):
    for fips, name in pic_geo.counties(footprint_key).items():
        expected = OHIO_FIPS_BY_NAME.get(name.replace(" ", ""))
        assert expected is not None, f"{name!r} is not an Ohio county"
        assert fips == expected, f"{name} is {expected}, not {fips}"


@pytest.mark.parametrize("footprint_key", pic_geo.FOOTPRINTS)
def test_every_fips_is_five_digits_in_ohio(footprint_key):
    for fips in pic_geo.counties(footprint_key):
        assert isinstance(fips, str)
        assert len(fips) == 5
        assert fips.isdigit()
        assert fips.startswith("39"), "state prefix 39 is Ohio; nothing else belongs here"
        assert int(fips[2:]) % 2 == 1, "county codes are odd; an even code is a typo"
        assert 1 <= int(fips[2:]) <= 175


def test_no_duplicate_fips_in_the_source_literals():
    """A duplicate key in a dict literal is silently discarded, so a dict cannot show it.

    Reading the source is the only way to catch `"39151": "Stark", "39151": "Summit"`, which
    would leave a 12-county footprint holding 11 counties and no error anywhere.
    """
    source = pathlib.Path(pic_geo.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    seen = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in ("PIC12", "NEO14"):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        keys = [k.value for k in node.value.keys]
        assert len(keys) == len(set(keys)), f"duplicate FIPS key in {target.id}: {keys}"
        seen[target.id] = keys
    assert set(seen) == {"PIC12", "NEO14"}, "could not find both literals to check"
    assert len(seen["PIC12"]) == 12
    assert len(seen["NEO14"]) == 14
    # Names too: the same county under two codes is the mirror of the same code twice.
    for key in pic_geo.FOOTPRINTS:
        names = list(pic_geo.counties(key).values())
        assert len(names) == len(set(names))


def test_pic12_is_sorted_by_fips():
    # NEO-14 is deliberately unsorted, to stay diffable against the vault's own list. PIC-12
    # has no such excuse, and an ordered list is the one that survives visual review.
    assert list(pic_geo.PIC12) == sorted(pic_geo.PIC12)


# ---------------------------------------------------------------------------------------
# The merge guard
# ---------------------------------------------------------------------------------------


def test_the_two_footprints_must_never_be_merged():
    """The footprints partially overlap. They do not nest, and they never reconcile.

    This fails if someone "harmonizes" them — makes them equal, makes one a superset of the
    other, or collapses one into the other. All three would make published PIC-12 figures
    silently comparable with published NEO-14 figures, which they are not: a sum across the
    two double-counts ten counties and omits none of the six that are unique to one side.
    """
    pic, neo = set(pic_geo.PIC12), set(pic_geo.NEO14)

    assert pic != neo, "the footprints have been made identical; they are different by design"
    assert not pic.issubset(neo), "PIC-12 must not nest inside NEO-14"
    assert not neo.issubset(pic), "NEO-14 must not nest inside PIC-12"
    assert pic & neo, "the footprints must still overlap; no overlap means one was replaced"

    assert set(pic_geo.PIC12_ONLY.values()) == {"Ashtabula", "Trumbull"}
    assert set(pic_geo.NEO14_ONLY.values()) == {"Crawford", "Huron", "Richland", "Tuscarawas"}
    assert len(pic | neo) == 16
    assert len(pic_geo.SHARED) + len(pic_geo.PIC12_ONLY) + len(pic_geo.NEO14_ONLY) == 16


def test_meta_prose_names_the_actual_difference():
    """`differs` is hand-written text next to computed counts — the classic drift trap.

    `n` updates itself when a county is added. The sentence does not. This asserts the
    sentence still names exactly the counties the set difference actually contains.
    """
    for name in pic_geo.NEO14_ONLY.values():
        assert name in pic_geo.META["pic12"]["differs"]
    for name in pic_geo.PIC12_ONLY.values():
        assert name in pic_geo.META["neo14"]["differs"]
    # And nothing more: a county named in the prose that is not in the difference is just as
    # wrong as one missing from it.
    for name in pic_geo.PIC12.values():
        if name not in pic_geo.PIC12_ONLY.values():
            assert name not in pic_geo.META["neo14"]["differs"]
    for name in pic_geo.NEO14.values():
        if name not in pic_geo.NEO14_ONLY.values():
            assert name not in pic_geo.META["pic12"]["differs"]


def test_meta_prose_states_both_directions_of_the_difference():
    """Each footprint's `differs` must name what it lacks AND what it has that the other lacks.

    Until v1.0.1 PIC-12's sentence named only the four counties NEO-14 adds, so a reader who
    added four to twelve got sixteen under a label that says fourteen. Both sentences must
    carry the full symmetric difference and the shared count.
    """
    both = set(pic_geo.PIC12_ONLY.values()) | set(pic_geo.NEO14_ONLY.values())
    shared_words = {10: "ten"}[len(pic_geo.SHARED)]
    for key in ("pic12", "neo14"):  # PIC-18's sentence is about PIC-18; tested separately below
        prose = pic_geo.META[key]["differs"]
        for name in both:
            assert name in prose, f"{key} differs omits {name}"
        assert f"share {shared_words} counties" in prose


def test_meta_serialization_contract_is_intact():
    """META is embedded verbatim in published datasets. Its field names are frozen."""
    for key in pic_geo.FOOTPRINTS:
        block = pic_geo.META[key]
        assert set(block) == {"key", "n", "label", "counties", "note", "differs"}
        assert block["key"] == key
        assert isinstance(block["n"], int), "a non-int n disables downstream prose checks"
        assert block["counties"] == sorted(pic_geo.counties(key).values())
        assert block["note"] and block["differs"]
    assert pic_geo.META["pic12"]["label"] == "PIC-12"
    assert pic_geo.META["neo14"]["label"] == "NEO-14"
    # "shared" is a bare list, not a footprint block. That asymmetry is load-bearing for
    # already-published output, so it is pinned rather than quietly fixed.
    assert isinstance(pic_geo.META["shared"], list)
    assert pic_geo.META["pic18"]["label"] == "PIC-18"
    assert pic_geo.META["teamneo14"]["label"] == "Team NEO-14"
    assert set(pic_geo.META) == {"pic12", "neo14", "pic18", "teamneo14", "shared"}


def test_footprint_accessors_refuse_bad_keys():
    with pytest.raises(KeyError):
        pic_geo.footprint("shared")          # a list of names, not a footprint
    with pytest.raises(KeyError):
        pic_geo.footprint("neo-14")          # the label, not the key
    with pytest.raises(KeyError):
        pic_geo.counties("NEO14")
    with pytest.raises(TypeError):
        pic_geo.in_footprint(39007)          # int() eats the leading zero on other counties
    assert pic_geo.in_footprint("39007") is True
    assert pic_geo.in_footprint("39033") is False
    assert pic_geo.in_footprint("39033", "neo14") is True


def test_derived_shapes_agree_with_the_definitions():
    assert pic_geo.PIC12_FIPS == frozenset(pic_geo.PIC12)
    assert pic_geo.PIC12_NAMES == frozenset(pic_geo.PIC12.values())
    assert pic_geo.PIC12_NAMES_UPPER == frozenset(n.upper() for n in pic_geo.PIC12.values())
    assert len(pic_geo.PIC12_FIPS3) == 12, "3-digit codes must not collide"
    assert pic_geo.PIC12_FIPS3["007"] == "Ashtabula"
    assert all(len(k) == 3 for k in pic_geo.PIC12_FIPS3)
    assert len(pic_geo.NEO14_FIPS3) == 14


# ---------------------------------------------------------------------------------------
# The crosswalk
# ---------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def geo():
    return crosswalk.load_geo()


def test_every_crosswalk_zip_resolves_to_a_pic12_county(geo):
    assert geo["zips"], "an empty ZIP lookup matches nothing and reads as an empty region"
    for code, county in geo["zips"].items():
        assert len(code) == 5 and code.isdigit(), f"{code!r} is not a 5-digit ZIP"
        assert county in pic_geo.PIC12_NAMES, f"{code} -> {county!r}, not a PIC-12 county"


def test_every_crosswalk_city_resolves_to_a_pic12_county(geo):
    assert geo["cities"], "an empty city lookup silently drops every city-only source"
    for name, county in geo["cities"].items():
        assert county in pic_geo.PIC12_NAMES, f"{name!r} -> {county!r}, not a PIC-12 county"


def test_crosswalk_counties_are_the_canonical_pic12(geo):
    """The shipped file carries its own copy of the footprint. It must equal the definition.

    Two copies of the county list inside one repository whose purpose is a single definition
    is the most embarrassing failure available here, so it is checked rather than trusted.
    """
    assert geo["meta"]["counties"] == pic_geo.PIC12


def test_crosswalk_counts_match_its_own_contents(geo):
    assert geo["meta"]["n_zips"] == len(geo["zips"]) == 261
    assert geo["meta"]["n_cities"] == len(geo["cities"]) == 614
    assert len(geo["rejected_cities"]) == 49
    assert set(geo) == {"meta", "zips", "cities", "rejected_cities"}


def test_crosswalk_covers_every_pic12_county(geo):
    # A county with no ZIPs at all would mean the footprint is being filtered somewhere.
    assert set(geo["zips"].values()) == set(pic_geo.PIC12_NAMES)
    assert set(geo["cities"].values()) == set(pic_geo.PIC12_NAMES)


def test_no_zip_or_city_appears_in_two_counties(geo):
    # Each key maps to one county by construction (largest land piece / plurality). If that
    # ever became a list, downstream sums would double-count.
    for lookup in ("zips", "cities"):
        for value in geo[lookup].values():
            assert isinstance(value, str)


def test_the_defect_this_crosswalk_fixed_stays_fixed(geo):
    """The far-away Ohio towns stay out; the genuine PIC-12 namesakes stay in.

    COLUMBUS and FRANKLIN entered the footprint through unreliable facility county fields.
    CLINTON, GREEN, NEWTON FALLS, JEFFERSON, MADISON and TROY are real PIC-12 towns that
    share a name with an Ohio town elsewhere, and a blanket name ban would have lost them.
    SPRINGFIELD and OAKWOOD are the subtle case: both names are genuinely in the footprint,
    and the old defect was the distant places wearing them, not the names.
    """
    for name in ("COLUMBUS", "FRANKLIN"):
        assert name not in geo["cities"], f"{name} is back in the footprint"
        assert name in geo["rejected_cities"]
    for name, county in (("CLINTON", "Summit"), ("GREEN", "Summit"),
                         ("NEWTON FALLS", "Trumbull"), ("JEFFERSON", "Ashtabula"),
                         ("MADISON", "Lake"), ("TROY", "Geauga"),
                         ("SPRINGFIELD", "Mahoning"), ("OAKWOOD", "Cuyahoga")):
        assert geo["cities"].get(name) == county


def test_rejection_reasons_are_readable_and_below_the_threshold(geo):
    for name, reason in geo["rejected_cities"].items():
        assert reason.endswith("facilities on PIC-12 ZIPs"), reason
        inside, total = (int(x) for x in reason.split()[0].split("/"))
        assert total > 0
        assert inside / total < 0.5, f"{name} was rejected at {reason}, above the threshold"


def test_lookup_helpers():
    assert pic_geo.county_of_zip("44685") == "Summit"          # 51.6% Summit land, the closest call
    assert pic_geo.county_of_zip("44685-1234") == "Summit"     # ZIP+4 is tolerated
    assert pic_geo.county_of_zip("43229") is None              # Columbus, Franklin County
    assert pic_geo.county_of_zip("43229", "outside") == "outside"
    assert pic_geo.county_of_city("akron") == "Summit"         # case-insensitive
    assert pic_geo.county_of_city("Columbus") is None


def test_shipped_file_is_valid_json_and_utf8():
    # The product of this repository is a data file. If it does not parse, nothing else matters.
    with open(crosswalk.geo_path(), encoding="utf-8") as fh:
        assert json.load(fh)["meta"]["n_zips"] == 261


def test_importing_the_crosswalk_does_not_touch_the_network():
    """Import must stay cheap. The 6.5 MB fetch lives behind `build()` and nowhere else."""
    source = pathlib.Path(crosswalk.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        # Module-level statements may be imports, constants, defs, or the __main__ guard.
        assert isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign,
                                 ast.FunctionDef, ast.If, ast.Expr)), ast.dump(node)[:80]


def test_contact_is_one_overridable_constant_with_no_baked_in_address(monkeypatch):
    """No published default contact, and one place to set one.

    A default would be either somebody's personal inbox or a mailbox nobody reads. The
    User-Agent still identifies the tool, so an unset contact degrades politely instead of
    lying about who is calling.
    """
    importlib = __import__("importlib")
    assert crosswalk.CONTACT == "", "no contact address may be baked into a public repository"
    assert "@" not in crosswalk.UA["User-Agent"]
    assert crosswalk.UA["User-Agent"].startswith("pic-geo/")

    monkeypatch.setenv("PIC_CONTACT", "maintainer@example.org")  # RFC 2606 reserved domain
    reloaded = importlib.reload(crosswalk)
    try:
        assert reloaded.CONTACT == "maintainer@example.org"
        assert "maintainer@example.org" in reloaded.UA["User-Agent"]
    finally:
        monkeypatch.delenv("PIC_CONTACT")
        importlib.reload(crosswalk)


# ---------------------------------------------------------------------------------------
# Canonical-copy guard.
#
# evidence-room vendors a copy of these definitions as _data/build/footprints.py so its
# fetch scripts run from a clone with no extra install. That is deliberate. What must
# NEVER happen is the two copies drifting apart while both claim to be the footprint.
# This test finds the sibling checkout when it is present (a developer machine, or a CI
# job that clones both) and asserts byte-for-byte agreement on the four exported objects.
# When the sibling is absent it skips rather than fails — absence is not divergence.
# ---------------------------------------------------------------------------------------
def test_vendored_copy_in_evidence_room_has_not_drifted():
    import importlib.util
    import os
    import pytest

    candidates = [
        os.environ.get("PIC_EVIDENCE_ROOM"),
        os.path.join(os.path.dirname(__file__), "..", "..", "evidence-room"),
    ]
    root = next((c for c in candidates if c and os.path.isdir(c)), None)
    if root is None:
        pytest.skip("evidence-room checkout not found; set PIC_EVIDENCE_ROOM to check")
    path = os.path.join(root, "_data", "build", "footprints.py")
    if not os.path.exists(path):
        pytest.skip(f"no vendored footprints.py at {path}")

    spec = importlib.util.spec_from_file_location("vendored_footprints", path)
    vendored = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vendored)

    import pic_geo
    assert vendored.PIC12 == pic_geo.PIC12, "evidence-room's PIC12 has drifted from pic-geo"
    assert vendored.NEO14 == pic_geo.NEO14, "evidence-room's NEO14 has drifted from pic-geo"
    assert vendored.SHARED == pic_geo.SHARED
    assert vendored.PIC18 == pic_geo.PIC18, "evidence-room's PIC18 has drifted from pic-geo"
    assert vendored.META == pic_geo.META, "evidence-room's META has drifted from pic-geo"
    if hasattr(vendored, "TEAMNEO14"):
        assert vendored.TEAMNEO14 == pic_geo.TEAMNEO14, "evidence-room's TEAMNEO14 has drifted"


# ---------------------------------------------------------------------------------------
# PIC-18 (v1.1.0, owner ruling 2026-11-03)
# ---------------------------------------------------------------------------------------

TEAM_NEO = {"Ashland", "Cuyahoga", "Erie", "Geauga", "Huron", "Lake", "Lorain", "Medina", "Portage",
            "Richland", "Stark", "Summit", "Tuscarawas", "Wayne"}
LAKE_TO_RIVER = {"Ashtabula", "Columbiana", "Mahoning", "Trumbull"}


def test_pic18_is_exactly_the_two_jobsohio_regions():
    """PIC-18's public definition: JobsOhio Team NEO (14) plus Lake to River (4), read from
    jobsohio.com/ohio-regional-network on 2026-11-03. Retyped here as names, so a FIPS typo in
    the module cannot pass by agreeing with itself."""
    assert set(pic_geo.PIC18.values()) == TEAM_NEO | LAKE_TO_RIVER
    assert len(pic_geo.PIC18) == 18 and pic_geo.META["pic18"]["n"] == 18
    assert {pic_geo.PIC18[f] for f, r in pic_geo.JOBSOHIO_REGION.items() if r == "Team NEO"} == TEAM_NEO
    assert {pic_geo.PIC18[f] for f, r in pic_geo.JOBSOHIO_REGION.items() if r == "Lake to River"} == LAKE_TO_RIVER
    assert set(pic_geo.JOBSOHIO_REGION) == set(pic_geo.PIC18)


def test_pic18_contains_pic12_and_names_what_it_adds():
    assert set(pic_geo.PIC12) < set(pic_geo.PIC18), "PIC-18 must contain PIC-12"
    added = {"Ashland", "Columbiana", "Erie", "Huron", "Richland", "Tuscarawas"}
    assert set(pic_geo.PIC18_ADDED_TO_PIC12.values()) == added
    prose = pic_geo.META["pic18"]["differs"]
    for name in added:
        assert name in prose
    # against NEO-14: names what PIC-18 adds and what it leaves out, and the shared count
    neo = set(pic_geo.NEO14.values())
    for name in set(pic_geo.PIC18.values()) - neo:
        assert name in prose, f"pic18 differs omits {name}"
    for name in neo - set(pic_geo.PIC18.values()):
        assert name in prose, f"pic18 differs omits {name}"
    assert len(set(pic_geo.PIC18) & set(pic_geo.NEO14)) == 13
    assert "share thirteen counties" in prose


def test_pic18_is_sorted_by_fips_and_shapes_agree():
    assert list(pic_geo.PIC18) == sorted(pic_geo.PIC18)
    assert pic_geo.PIC18_FIPS == frozenset(pic_geo.PIC18)
    assert len(pic_geo.PIC18_FIPS3) == 18 and pic_geo.PIC18_FIPS3["005"] == "Ashland"
    assert pic_geo.PIC18_NAMES_UPPER == frozenset(n.upper() for n in pic_geo.PIC18.values())
    assert pic_geo.in_footprint("39157", "pic18") is True     # Tuscarawas
    assert pic_geo.in_footprint("39033", "pic18") is False    # Crawford: NEO-14 only
    assert pic_geo.in_footprint("39019", "pic18") is False    # Carroll: in none of the three


def test_module_docstring_records_the_pic18_decision():
    assert "DECISION (2026-11-03" in pic_geo.__doc__
    assert "Team NEO" in pic_geo.__doc__ and "Lake to River" in pic_geo.__doc__


def test_pic18_zip_crosswalk_is_consistent_with_pic12():
    """The PIC-18 crosswalk (v1.1.0, ZIP-only) is built by the same largest-land-piece rule, so
    every PIC-12 ZIP must appear in it with the same county, and every PIC-18 county is covered."""
    p12, p18 = crosswalk.zips("pic12"), crosswalk.zips("pic18")
    assert len(p18) > len(p12)
    for z, county in p12.items():
        assert p18.get(z) == county, f"ZIP {z}: PIC-12 says {county}, PIC-18 says {p18.get(z)}"
    assert set(p18.values()) == set(pic_geo.PIC18.values())
    assert crosswalk.load_geo("pic18")["meta"]["footprint"] == "pic18"
    assert crosswalk.county_of_zip("44663", key="pic18") == "Tuscarawas"   # New Philadelphia
    assert crosswalk.county_of_zip("44663") is None                        # not in PIC-12


def test_pic18_city_lookup_refuses_until_rebuilt():
    """PIC-18 ships ZIP-only. A city lookup must fail loudly, not return None for every town,
    which would read as 'no activity in the six added counties'."""
    assert crosswalk.cities("pic18") == {}
    with pytest.raises(LookupError):
        crosswalk.county_of_city("NEW PHILADELPHIA", key="pic18")
    with pytest.raises(KeyError):
        crosswalk.load_geo("neo14")



# ---------------------------------------------------------------------------------------
# Team NEO-14 (v1.2.0): the subtotal that reads against Team NEO's Vibrant Economy Indicators
# ---------------------------------------------------------------------------------------


def test_teamneo14_is_the_team_neo_half_of_pic18():
    assert set(pic_geo.TEAMNEO14.values()) == TEAM_NEO
    assert set(pic_geo.TEAMNEO14) < set(pic_geo.PIC18)
    assert set(pic_geo.PIC18) - set(pic_geo.TEAMNEO14) == {
        f for f, n in pic_geo.PIC18.items() if n in LAKE_TO_RIVER}
    assert pic_geo.counties("teamneo14") == pic_geo.TEAMNEO14
    assert pic_geo.TEAMNEO14_FIPS == frozenset(pic_geo.TEAMNEO14)
    assert len(pic_geo.TEAMNEO14_FIPS3) == 14


def test_teamneo14_is_not_the_vault_neo14():
    """Same count, different counties: the name collision this footprint's label avoids."""
    t, n = set(pic_geo.TEAMNEO14.values()), set(pic_geo.NEO14.values())
    assert t - n == {"Ashland", "Erie"}
    assert n - t == {"Crawford", "Mahoning"}
    assert len(t & n) == 12
    prose = pic_geo.META["teamneo14"]["differs"]
    for name in ("Ashland", "Erie", "Crawford", "Mahoning", "twelve"):
        assert name in prose
    assert pic_geo.META["teamneo14"]["label"] != pic_geo.META["neo14"]["label"]
