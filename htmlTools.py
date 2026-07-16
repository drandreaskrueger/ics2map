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
<div>
<label>From</label><input id="fromDate" type="date" />
</div>
<div style="margin-top:6px;">
<label>To</label><input id="toDate" type="date" />
</div>
<button id="applyBtn" type="button">Apply</button>
<div id="status" style="margin-top:6px; color:#444;"></div>
</div>
"""


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
