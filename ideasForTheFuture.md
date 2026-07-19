# ideas for the future

(A) Python development

(B) Map functionality

(C) What AI suggested

(D) Ideas what to ask the AI

Chapters possibly divided into: 

* essential
* nice to have
* really not essential but worth mentioning
* possible trouble noticed by AI
* done


---


## (A) Python development
### essential

Python code most urgent:

* the geocodeCache.csv is written but then in a later run never used?

### nice to have
To execute each python file standalone, add a `if __name__ == "__main__":`

* loggingTools.py = not yet done at all
* importICS.py = done. But main() looks like redundant code?
* geocode.py = not yet done at all
* geocodeCache.py = best to just import, and let it handle by `geocode.py --> main()` 
* htmlTools.py = half done, but still only tests `build_controls_block()`
* pipelineTools.py = no. Would probably result in circular imports?

### really not essential but worth mentioning

Add CLI entrypoint, use argparse so users can override config without editing files:

* --config config.toml
* --from 2026-01-01 --to 2026-12-31 (optional override)
* --skip-geocode (debug fast)
* --output-dir outputs

`load_config_and_init_logging("outputs")` should not be called with "outputs" but read from TOML

geocodeCredentials.toml could be left out completely, no API key needed

instead of the injection (`build_controls_block(), write_map_html()`) move that code into mapTemplate.html and mapScripts.js ?

### possible trouble noticed by AI

* `importICS.py` #CAREFUL: right now total\_\in\_source = len(list(cal.events)) iterates events once; if you notice weird behavior, switch to just using len(cal.events) (depending on the ics library object type).


### Done, hooray

* Done: do not skip silently, e.g. third event in test-ICS has no LOCATION: entry
* Done: all text fields in CSV in "..." quotes please, to avoid comma-related issues

---

## (B) Map functionality

### essential

Functionality:

* all done, thanks.

Layout:

* all done, thanks.

New data (needs to be passed via python to .json too):

* description of event = from ICS pass through: `DESCRIPTION:` content
  * if there are URLs in it, make clickable
  * show description only after expanding a triangle "description" button
  * see "[User prompt 9 of 13 - 18/07/2026](AI/duck.ai_2026-07-18_04-07-04_UI-improvements-part-2_and_passing-through-more-data.md)" to "User prompt 13 of 13 - 18/07/2026"
  * postponed, as normalization of the odd ICS DESCRIPTION formatting might take time.

### nice to have

Searchability:

* Allow search in name, location, description, uid, etc.

All points:

* sidebar with all events
  * sortable by date or name
  * clicking an event there, centers the map on that event map point

Select points, then:

* select mode, finish, process
* show 'distance as the crow flies' between 2 points
* sum up distances of sequence of points

Question: Why "Location: Berlin, Germany" versus "Geocoder: Berlin, Germany" always identical?

### More data passed through, then:

* whole ICS object per point (load and parse in JS later??)
  * then possible: Select a couple of points, generate subset-ICS file for download.
  * perhaps there is a JS parser library for ICS too?

### Fun stuff, really not essential, but worth mentioning:

Add UI controls: dropdown: “All / Country DE / AT / …"

Export GeoJSON (so can be used elsewhere): `outputs/map.geojson`

### Done, hooray

Done:
  
* Done: Marker overlap (two events, same location) was resolved by Leaflet. Hooray.
* Done: prepopulate date fields with largest date intervall. Was already done in existing code. Hooray.
* Done: put date chooser in top right, currently overlaps with map +/- buttons

* Date range chooser does not work (perfectly) yet:
  * With a shorter range, e.g. dateFrom,dateTo same day, and press "Apply" no redraw happens. Button not connected?
  * The status sentence ("Showing 4 event(s)") should become ("Showing 2 of 4 event(s)")
  * New button "Show All" takes the largest occuring date intervall, and populates the date fields, and presses "Apply"


# (C) What AI suggested

* see [User prompt 1 of 16 - 14/07/2026](https://github.com/drandreaskrueger/ics2map/blob/main/AI/duck.ai_2026-07-14_22-46-34_patch-errors-and-make-it-work_HOORAY.md)
  * and ask the same question again, now

# (D) Ideas what to ask the AI

* please read all *.md files in https://github.com/drandreaskrueger/ics2map/tree/main/AI 
  * and analyze our conversation
    * why was the refactoring so tedious?
    * feels as if writing all from scratch, in better initial architecture planning, would have taken less time?
  * what do you suggest to add to my "coding-principles.md" ?

* please read the https://github.com/drandreaskrueger/ics2map/blob/main/AI/coding-principles.md
  * streamline it; without dropping any aspect, use less words
  * re-sort it; give it a better structure and sequence
  * what invisible assumption do you spot, that I could write explicitly?
  * where are inner inconsistencies or contradictions?

* dateFrom AND dateTo = attempt 1 had already succeeded, but browser cache had hidden that.

