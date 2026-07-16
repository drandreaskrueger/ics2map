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
    
    # TODO: replace the above with:
    # create_map_html_with_assets(...)
    

    logger.info("Pipeline complete")
    print(load_aggregates_snapshot(agg))
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()
