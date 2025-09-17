"""News fetcher that returns deterministic stubbed articles."""
from __future__ import annotations


def get_headlines(date_str: str) -> list[dict]:
    """Return a set of mock news headlines for the given date."""
    # Keep the mock data stable for tests yet vary timestamps using the date.
    timestamp = f"{date_str}T08:00:00Z"
    later_timestamp = f"{date_str}T14:00:00Z"

    return [
        {
            "title": "Apple's new AI features drive strong upgrade cycle",
            "url": "https://example.com/apple-upgrade-cycle",
            "source": "Reuters",
            "published_at": timestamp,
            "body": (
                "Apple is rolling out upgraded iPhone and Mac software with on-device"
                " generative AI, which analysts say could sustain record demand for"
                " Apple hardware this holiday season."
            ),
        },
        {
            "title": "Microsoft cloud growth beats expectations in latest quarter",
            "url": "https://example.com/microsoft-cloud-growth",
            "source": "Bloomberg",
            "published_at": later_timestamp,
            "body": (
                "Microsoft reported another quarter of Azure growth that beats Wall"
                " Street expectations as Windows and Teams adoption remains strong among"
                " enterprise clients."
            ),
        },
        {
            "title": "Nvidia GPUs power record data center demand",
            "url": "https://example.com/nvidia-data-center",
            "source": "Financial Times",
            "published_at": timestamp,
            "body": (
                "Cloud providers are racing to secure more Nvidia GPU supply to support"
                " artificial intelligence workloads, keeping Nvidia's data center"
                " revenue at record highs and sustaining strong growth guidance."
            ),
        },
        {
            "title": "Exxon Mobil faces new emissions disclosure lawsuit",
            "url": "https://example.com/exxon-lawsuit",
            "source": "Associated Press",
            "published_at": later_timestamp,
            "body": (
                "Environmental groups filed a lawsuit alleging ExxonMobil misled"
                " investors about long-term emissions impacts, adding legal pressure"
                " and the potential for negative headlines."
            ),
        },
    ]


__all__ = ["get_headlines"]
