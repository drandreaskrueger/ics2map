import os
import tomllib  # Python 3.11+

from loggingTools import Logger

def build_controls_block(enabled: bool) -> str:
    """
    Build the HTML controls block (date range + apply button).
    If disabled, return a hidden status element so JS can still write to #status.
    """
    if not enabled:
        return '<div id="status" style="display:none"></div>'

    return """
    <div id="controls">
      <div class="controls-row">
        <div class="dates-col">
          <div>
            <label>From</label><input id="fromDate" type="date" />
          </div>
          <div style="margin-top:6px;">
            <label>To</label><input id="toDate" type="date" />
          </div>
        </div>
    
        <div class="showall-col">
          <button id="showAllBtn" type="button">Show All</button>
        </div>
      </div>
    
      <div class="actions-row">
        <button id="applyBtn" type="button">Apply</button>
        <div id="status"></div>
      </div>
    </div>
    """



def write_map_html(cfg, output_dir, logger):
    """
    Render map.html using templates/mapTemplate.html and write it into the output directory.
    """
    make_cfg = cfg["makeMap"]
    date_slider = make_cfg.get("dateSlider", "ON") == "ON"

    map_html_path = os.path.join(output_dir, make_cfg.get("mapHtml", "map.html"))
    controls_block = build_controls_block(date_slider)

    maybe_apply_listener = """
const applyBtn = document.getElementById('applyBtn');
if (applyBtn) {
  applyBtn.addEventListener('click', () => {
    const fromVal = document.getElementById('fromDate').value;
    const toVal = document.getElementById('toDate').value;
    
    // console.log("DEBUG: Apply pressed", { fromVal, toVal });  // DEBUG only
    
    renderFiltered(fromVal, toVal);
  });
}

const showAllBtn = document.getElementById("showAllBtn");
if (showAllBtn) {
  showAllBtn.addEventListener("click", () => {
    const uniqueDates = Array.from(new Set((allPoints || []).map(p => p.date).filter(Boolean))).sort();

    if (!uniqueDates.length) {
      console.log("Show All: no dates available");
      return;
    }
    
    // begin DEBUG only
    console.log("DEBUG ShowAll: all uniqueDates (sorted)", uniqueDates);
    const prevFirst = uniqueDates[0];
    const next = new Date(parseYMDToLocalDate(prevFirst).getTime());
    next.setDate(next.getDate() + 1);
    console.log("DEBUG ShowAll: first date + 1 day expected", ymdFromLocalDate(next));
    console.log("DEBUG ShowAll: does set contain expected next?",
      new Set(uniqueDates).has(ymdFromLocalDate(next))
    );
    // end DEBUG only

    const [ bestStart, bestEnd ] = findLargestContiguousDateRun(uniqueDates);

    console.log("DEBUG: Show All pressed", { bestStart, bestEnd });

    const fromEl = document.getElementById("fromDate");
    const toEl = document.getElementById("toDate");
    if (fromEl) fromEl.value = bestStart;
    if (toEl) toEl.value = bestEnd;

    // "and presses Apply"
    renderFiltered(bestStart, bestEnd);
  });
}
"""

    # Marked: could fail if templates/mapTemplate.html missing; log then re-raise.
    try:
        with open("templates/mapTemplate.html", "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        logger.error(f"Failed to read templates/mapTemplate.html: {type(e).__name__}: {e}")
        raise

    html = (
        template
        .replace("__CONTROLS_BLOCK__", controls_block)
        .replace("__MAYBE_APPLY_LISTENER__", maybe_apply_listener)
    )

    with open(map_html_path, "w", encoding="utf-8") as f:
        f.write(html)

def copy_map_assets_to_output_dir(output_dir: str, logger):
    """
    Copy map-related static assets (CSS/JS) into the output directory,
    so outputs/map.html can reference them.
    """
    for asset_name in ["mapScripts.js", "mapStyles.css"]:
        src_path = os.path.join(".", "templates", asset_name)
        dst_path = os.path.join(output_dir, asset_name)
        try:
            with open(src_path, "rb") as fsrc:
                data = fsrc.read()
            with open(dst_path, "wb") as fdst:
                fdst.write(data)
            logger.info(f"Copied asset: {asset_name}")
        except Exception as e:
            logger.error(f"copy_map_assets_to_output_dir failed: {type(e).__name__}: {e}")
            raise


def _load_config():
    with open("config.toml", "rb") as f:
        return tomllib.load(f)


if __name__ == "__main__":
    cfg = _load_config()
    output_dir = cfg["outputDir"]
    os.makedirs(output_dir, exist_ok=True)

    logger = Logger(os.path.join(output_dir, "log.txt"))
    make_cfg = cfg["makeMap"]
    date_slider = make_cfg.get("dateSlider", "ON") == "ON"

    block = build_controls_block(date_slider)
    logger.info(f"Debug htmlTools: built controls block. enabled={date_slider}, len={len(block)}")
    print(block)
