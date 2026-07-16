import os
import csv
import json

from pipelineTools import (
    load_config_and_init_logging,
    optionally_load_geocode_credentials,
    load_selected_ics_events,
    run_geocoding_and_write_map_data,
)

from loggingTools import load_aggregates_snapshot
from htmlTools import build_controls_block



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
    renderFiltered(fromVal, toVal);
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



def main():
    """
    Main pipeline orchestrator (kept short):
    1) load config + init logger
    2) load ICS selection
    3) geocode + write mapData.csv
    4) write map.html
    5) write logs + aggregates snapshot output
    """
    cfg, output_dir, logger, agg = load_config_and_init_logging("output")

    optionally_load_geocode_credentials(logger)

    events = load_selected_ics_events(cfg, agg, logger)
    _ = run_geocoding_and_write_map_data(cfg, events, agg, logger, output_dir)
    
    copy_map_assets_to_output_dir(output_dir, logger)
    write_map_html(cfg, output_dir, logger)

    logger.info("Pipeline complete")
    print(load_aggregates_snapshot(agg))
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()
