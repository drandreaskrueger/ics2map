# ideas for the future

(A) Python development

(B) Map functionality

all divided into: 

* essential
* nice to have
* really not essential but worth mentioning
* possible trouble noticed by AI
* done


---


## (A) Python development
### essential

Python code most urgent:

* all done, thanks!

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

### possible trouble noticed by AI

* `importICS.py` #CAREFUL: right now total\_\in\_source = len(list(cal.events)) iterates events once; if you notice weird behavior, switch to just using len(cal.events) (depending on the ics library object type).


### Done, hooray

* Done: do not skip silently, e.g. third event in test-ICS has no LOCATION: entry
* Done: all text fields in CSV in "..." quotes please, to avoid comma-related issues

---

## (B) Map functionality

### essential

Functionality:

* Date range chooser does not work (perfectly) yet:
  * With a shorter range, e.g. dateFrom,dateTo same day, and press "Apply" no redraw happens. Button not connected?
  * The status sentence ("Showing 4 event(s)") should become ("Showing 2 of 4 event(s)")
  * New button "Show All" takes the largest occuring date intervall, and populates the date fields, and presses "Apply"

Layout:

* put date chooser in top right, currently overlaps with map +/- buttons

New data (needs to be passed via python to .json too):

* dateFrom AND dateTo 

* description of event = from ICS pass through: `DESCRIPTION:` content
  * if there are URLs in it, make clickable
  * show description only after expanding a triangle "description" button



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

### Fun stuff, really not essential, but worth mentioning:

Add UI controls: dropdown: “All / Country DE / AT / …"

Export GeoJSON (so can be used elsewhere): `outputs/map.geojson`

### Done, hooray

Done:
  
* Done: Marker overlap (two events, same location) was resolved by Leaflet. Hooray.
* Done: prepopulate date fields with largest date intervall. Was already done in existing code. Hooray.
