# ideas for the future

## Python development
### essential

Python code most urgent:

* do not skip silently, e.g. third event in test-ICS has no LOCATION: entry
* all text fields in CSV in "..." quotes please, to avoid comma-related issues 

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

geocodeCredentials.toml could be left out completely, no API key needed

## map functionality

### essential

Functionality:

* Marker overlap (two events, same location) - how to resolve?
* prepopulate date fields with largest date intervall

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

### More data passed through, then:

* whole ICS object per point (load and parse in JS later??)
  * then possible: Select a couple of points, generate subset-ICS file for download.

### Fun stuff, really not essential, but worth mentioning:

Add UI controls: dropdown: “All / Country DE / AT / …"

Export GeoJSON (so can be used elsewhere): `outputs/map.geojson`

