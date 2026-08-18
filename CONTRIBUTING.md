# Contributing

The most valuable contribution here is a **wrong assignment**: a ZIP mapped to the wrong county,
a city name that should not be in the footprint or is missing from it, a FIPS code that does not
match its county. Open an issue with the ZIP or city string, what this repository says, what you
think it should be, and how you know. Confirmed errors get a dated entry in
[CORRECTIONS.md](CORRECTIONS.md).

This repository is small on purpose and should stay that way. Every other PIC analysis imports
it, so anything added here is added to all of them.

## Ground rules for changes

1. **A county change is a version.** The footprints are cited by outside work. Adding or
   removing a county changes published output, so it ships as a release with a corrections
   entry, never as a quiet commit.
2. **Change the definition in one place.** `PIC12` and `NEO14` in `src/pic_geo/__init__.py` are
   the only copies. If you need the counties in another shape — three-digit FIPS, upper-case
   names — derive it there and export it; do not retype the list. A footprint defined in
   sixteen places is the problem this repository was created to end.
3. **Hand-written prose next to computed counts must be tested.** `META[...]["n"]` recomputes
   itself; `label` and `differs` do not. `test_meta_prose_names_the_actual_difference` is what
   stops the sentence from going stale while the count updates. Add the equivalent test for any
   new prose field.
4. **`META`'s field names are frozen.** They are serialized verbatim into published datasets,
   several of which are regenerated only by re-running rate-limited federal APIs. `key` and
   `counties` are read by no rendering code but are in published output, so they are not
   unused. Renaming a field is a coordinated release, not a refactor.
5. **No runtime dependencies.** The standard library reads a pipe-delimited file and a JSON
   file. A dependency here becomes a dependency of every PIC analysis.
6. **Import must stay cheap and offline.** The Census fetch lives behind `crosswalk.build()`.
   Nothing at module level may touch the network or read a large file;
   `test_importing_the_crosswalk_does_not_touch_the_network` enforces the shape.
7. **Guards fail closed.** A bad footprint key raises rather than returning an empty dict; a
   rebuild without a facility extract raises rather than writing an empty city list. An empty
   footprint filters every row out and reads downstream as "the region has no data," which is
   the failure mode that is hardest to notice and hardest to date afterward.
8. **State new limits, do not fix them silently.** The largest-land-piece rule drops 18 areas
   with real PIC-12 land. That is documented, not hidden. If you find another artifact of the
   method, the README's "What this cannot tell you" section is where it goes.
9. **No personal or member data, ever.** This repository is public and its history is
   permanent. The facility extract used to rebuild the city half is deliberately not committed.

## Running the tests

```bash
uv sync --frozen
uv run pytest
```

The tests are the specification. They check county counts, the exact ten-county intersection,
every FIPS code re-derived from an independent list of Ohio's 88 counties rather than compared
to a second copy of the same codes, and that the two footprints have not been merged. If a
change you want to make requires deleting one of those assertions, that is the conversation to
have in the issue first.
