import re

import pytest

from htmlTools import link_urls_in_text_for_html


def _extract_hrefs(html: str) -> set[str]:
    return set(re.findall(r'href="([^"]+)"', html))


@pytest.mark.parametrize(
    "description, expected_hrefs",
    [
        (
            # Example 1 (folding inside URLs: www.goabase.n\net, https:\n//www.instagram.com/...)
            "10. - 14.08.2026 Sizigia Eclipse (own spirit team)\n\n"
            "https://www.goabase.n\n"
            "et/festival/sizigia-eclipse-gathering-2026/115726\n\n"
            "Rotating stage: https:\n"
            "//www.instagram.com/reel/DYe4zctiVU2/\n\n"
            "https://www.instagram.com/p/DYNBWt",
            {
                "https://www.goabase.net/festival/sizigia-eclipse-gathering-2026/115726",
                "https://www.instagram.com/reel/DYe4zctiVU2/",
                "https://www.instagram.com/p/DYNBWt",
            },
        ),
        (
            # Example 2 (lots of folding)
            "2026:\nhttps://www.ravetheplanet.com/en/events/rave-the-planet-parade-2026/\n"
            "\t\n\nForderungen:\nhttps://www.ravetheplanet.com/forderungen/\n\n"
            "April???\nh\n\ttps://www.goabase.net/party/truck-rave-the-planetgoanautika-ostfunk/117439\n"
            "\t\n\n2025:\n\n12.Juli\n\nM-Bia Float https://www.goabase.net/de/party/rave-t"
            "he-planet-m-bia-float-by-intoxication-x-inception/115187\n\n"
            "Goanautika&Ostf"
            "unk Float https://www.goabase.net/de/party/rave-the-planet-goanautika-ostfu"
            "nk-float/115022",
            {
                "https://www.ravetheplanet.com/en/events/rave-the-planet-parade-2026/",
                "https://www.ravetheplanet.com/forderungen/",
                "https://www.goabase.net/party/truck-rave-the-planetgoanautika-ostfunk/117439",
                "https://www.goabase.net/de/party/rave-the-planet-m-bia-float-by-intoxication-x-inception/115187",
                "https://www.goabase.net/de/party/rave-the-planet-goanautika-ostfunk-float/115022",
            },
        ),
        (
            # Example 3 (protocol + newline + path)
            "DESCRIPTION:https://znagathering.com/\n\n"
            "15.-22.Juli 2026\nhttps://www.instagram.com/p/\n"
            "\tDYO6vi8Duof/",
            {
                "https://znagathering.com/",
                "https://www.instagram.com/p/DYO6vi8Duof/",
            },
        ),
        (
            # Example 4 (multiple folded URLs across lines)
            "DESCRIPTION:198€ + 99€ Camping + 22€ early arrival \n\n"
            "https://airbeat-one.de/ \n\n"
            "8.-1"
            "2.7.2026\n9-13.7.2025\n\n"
            "Ticketkombinationen möglich: https://customerservi"
            "ce.airbeat-one.de/hc/de/articles/115004838629-Ticketkombinationen\n\n"
            "Unbedi"
            "ngt Ticketswap Last Minute checken!!",
            {
                "https://airbeat-one.de/",
                "https://customerservice.airbeat-one.de/hc/de/articles/115004838629-Ticketkombinationen",
            },
        ),
    ],
)
def test_link_urls_in_text_for_html_handles_folded_urls(description, expected_hrefs):
    html = link_urls_in_text_for_html(description)

    # Basic safety check: we should not lose href quotes etc.
    hrefs = _extract_hrefs(html)
    assert expected_hrefs.issubset(hrefs)

    # If you want extra strictness, you can also assert there are no raw "https:" fragments left
    # that indicate broken reconstructions.
    # assert "https:\n" not in html
