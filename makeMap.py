# python makeMap.py

from pipelineTools import (
    load_config_and_init_logging,
    optionally_load_geocode_credentials,
    load_selected_ics_events,
    run_geocoding_and_write_map_data,
    create_map_html_with_assets,   
)

from loggingTools import load_aggregates_snapshot


def main():
    """
    Main pipeline orchestrator (kept short):
    1) load config + init logger (+ agg)
    2) optionally load geocode credentials
    2) load ICS selection
    3) geocode + write mapData.csv
    4) create map.html + copy assets (via create_map_html_with_assets)
    5) log “Pipeline complete”, then print aggregates snapshot + output dir
    """
    cfg, output_dir, logger, agg = load_config_and_init_logging("outputs")

    optionally_load_geocode_credentials(logger)

    events = load_selected_ics_events(cfg, agg, logger)
    
    _ = run_geocoding_and_write_map_data(cfg, events, agg, logger, output_dir)
    
    _ = create_map_html_with_assets(cfg, output_dir, logger)
    
    logger.info("Pipeline complete")
    print(load_aggregates_snapshot(agg))
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()
    