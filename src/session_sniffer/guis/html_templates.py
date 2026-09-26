"""GUI-focused multi-line HTML templates.

Keep HTML blobs used for Qt/Rich-text rendering here so non-GUI modules don't depend on GUI styling.
"""

from typing import TYPE_CHECKING

from session_sniffer.constants.local import VERSION
from session_sniffer.constants.standalone import TITLE

if TYPE_CHECKING:
    from session_sniffer.capture.packet_capture import PacketCapture


CAPTURE_STOPPED_HTML = '\n<div style="background: linear-gradient(90deg, #bf616a, #d08770); padding: 10px;\n            margin-top: 10px; border: 2px solid #bf616a; border-radius: 6px;\n            box-shadow: 0px 3px 8px rgba(191, 97, 106, 0.4); text-align: center;">\n    <span style="font-size: 14pt; font-weight: bold; color: #ffeb3b;">CAPTURE ARRÊTÉE</span>\n</div>\n'


GUI_HEADER_HTML_TEMPLATE: str = """
<div style="background: linear-gradient(90deg, #3c244a, #634373); color: white; padding: 15px;
            border: 2px solid #5de8fb; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);">
    <div style="text-align: center;">
        <span style="font-size: 18pt; color: #5de8fb; font-weight: bold;">{title}</span>&nbsp;&nbsp;<span style="font-size: 10pt; color: #aaa">{version}</span>
    </div>
    {stop_status}
</div>
"""


def generate_gui_header_html(*, capture: PacketCapture) -> str:
    """Generate the GUI header HTML based on capture state."""
    stop_status = '' if capture.is_running() else CAPTURE_STOPPED_HTML

    return GUI_HEADER_HTML_TEMPLATE.format(
        title=TITLE,
        version=VERSION,
        stop_status=stop_status,
    )
