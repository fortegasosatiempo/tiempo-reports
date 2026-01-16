#!/usr/bin/env python3
"""Generate a sample report using local data for testing."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_report import generate_html_report, PUBLICATIONS, OUTPUT_DIR

# Sample data based on the weekly data we pulled earlier
sample_report_data = {
    "title": "Weekly Newsletter Report",
    "date_range": "January 5 - January 11, 2026",
    "publications": {
        "ETL Daily": {
            "posts_sent": 5,
            "avg_sent": 6732,
            "impressions": 22051,
            "avg_unique_opens": 3128,
            "avg_open_rate": 46.47,
            "total_clicks": 330,
            "avg_unique_clicks": 19,
            "avg_click_rate": 0.60,
            "unsubscribes": 9,
            "top_posts": [
                {"title": "SNAP back", "open_rate": 46.85, "impressions": 4419, "clicks": 71},
                {"title": "Empleos down planes up", "open_rate": 46.77, "impressions": 4571, "clicks": 61},
                {"title": "El crimen baja la gripe sube", "open_rate": 46.58, "impressions": 4377, "clicks": 21}
            ]
        },
        "EP Daily": {
            "posts_sent": 5,
            "avg_sent": 6754,
            "impressions": 19908,
            "avg_unique_opens": 2700,
            "avg_open_rate": 39.97,
            "total_clicks": 187,
            "avg_unique_clicks": 30,
            "avg_click_rate": 1.10,
            "unsubscribes": 11,
            "top_posts": [
                {"title": "Cuales son las prioridades de Boston Everett y Chelsea", "open_rate": 40.82, "impressions": 4263, "clicks": 22},
                {"title": "Confiscan el telefono a un observador", "open_rate": 40.45, "impressions": 3878, "clicks": 47},
                {"title": "Se impulsa proyecto para reducir millas", "open_rate": 39.84, "impressions": 3926, "clicks": 28}
            ]
        }
    },
    "totals": {
        "posts": 10,
        "impressions": 41959,
        "clicks": 517,
        "avg_open_rate": 43.22
    }
}

# Generate HTML
html = generate_html_report(sample_report_data, "weekly")

# Save to file
os.makedirs(OUTPUT_DIR, exist_ok=True)
filepath = os.path.join(OUTPUT_DIR, "sample_weekly_report.html")
with open(filepath, 'w') as f:
    f.write(html)

print(f"Sample report generated: {filepath}")
