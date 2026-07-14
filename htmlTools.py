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
