#!/usr/bin/env python3
"""
Tiempo Company Newsletter Report Automation Script

This script pulls newsletter data from Beehiiv API and generates
weekly and monthly reports for El Tiempo Latino and El Planeta.

Requirements:
    pip install requests python-dateutil

Usage:
    python newsletter_report.py --week 2026-01-05
    python newsletter_report.py --month 2025-12
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

# Beehiiv API Configuration
BEEHIIV_API_BASE = "https://api.beehiiv.com/v2"
BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY", "")

# Publication IDs
PUBLICATIONS = {
    "ETL Daily": "pub_88b8ccea-c311-4381-a49c-91848583ba9e",
    "EP Daily": "pub_2dd3324c-fa75-40a2-acf2-df2acff63d10"
}

# Output directories
OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(OUTPUT_DIR, "templates")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")

# =============================================================================
# API HELPERS
# =============================================================================

def get_headers():
    """Get API headers with authentication."""
    if not BEEHIIV_API_KEY:
        print("ERROR: BEEHIIV_API_KEY environment variable not set")
        print("Set it with: export BEEHIIV_API_KEY='your_api_key'")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {BEEHIIV_API_KEY}",
        "Content-Type": "application/json"
    }

def fetch_posts(publication_id, start_date, end_date, expand=None):
    """
    Fetch posts from Beehiiv API for a given date range.

    Args:
        publication_id: The Beehiiv publication ID
        start_date: Start date (datetime object)
        end_date: End date (datetime object)
        expand: Optional list of fields to expand (e.g., ['stats', 'clicks'])

    Returns:
        List of post objects
    """
    url = f"{BEEHIIV_API_BASE}/publications/{publication_id}/posts"

    # Convert dates to Unix timestamps
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())

    params = {
        "status": "confirmed",
        "limit": 100
    }

    if expand:
        params["expand[]"] = expand

    all_posts = []
    page = 1

    while True:
        params["page"] = page
        response = requests.get(url, headers=get_headers(), params=params)

        if response.status_code != 200:
            print(f"Error fetching posts: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        posts = data.get("data", [])

        if not posts:
            break

        # Filter posts by date range
        for post in posts:
            publish_date = post.get("publish_date", 0)
            if start_ts <= publish_date <= end_ts:
                all_posts.append(post)

        # Check if there are more pages
        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1

    return all_posts

def fetch_post_stats(publication_id, post_id):
    """Fetch detailed stats for a single post."""
    url = f"{BEEHIIV_API_BASE}/publications/{publication_id}/posts/{post_id}"
    params = {"expand[]": ["stats", "clicks"]}

    response = requests.get(url, headers=get_headers(), params=params)

    if response.status_code != 200:
        print(f"Error fetching post stats: {response.status_code}")
        return None

    return response.json().get("data", {})

# =============================================================================
# DATA PROCESSING
# =============================================================================

def process_post_data(post, publication_name):
    """
    Process a single post into the report format.

    Returns:
        dict with post metrics
    """
    stats = post.get("stats", {})
    email_stats = stats.get("email", {})
    web_stats = stats.get("web", {})

    # Extract metrics
    recipients = email_stats.get("recipients", 0)
    opens = email_stats.get("opens", 0)
    unique_opens = email_stats.get("unique_opens", 0)
    clicks = email_stats.get("clicks", 0)
    unique_clicks = email_stats.get("unique_clicks", 0)
    unsubscribes = email_stats.get("unsubscribes", 0)
    web_views = web_stats.get("views", 0)

    # Calculate rates
    open_rate = (unique_opens / recipients * 100) if recipients > 0 else 0
    click_rate = (unique_clicks / recipients * 100) if recipients > 0 else 0

    # Calculate impressions (opens + web_views)
    impressions = opens + web_views

    # Parse publish date
    publish_ts = post.get("publish_date", 0)
    publish_date = datetime.fromtimestamp(publish_ts)

    return {
        "publication": publication_name,
        "post_id": post.get("id", ""),
        "title": post.get("title", ""),
        "date": publish_date.strftime("%Y-%m-%d"),
        "month": publish_date.strftime("%Y-%m"),
        "recipients": recipients,
        "opens": opens,
        "unique_opens": unique_opens,
        "open_rate": round(open_rate, 2),
        "clicks": clicks,
        "unique_clicks": unique_clicks,
        "click_rate": round(click_rate, 2),
        "unsubscribes": unsubscribes,
        "web_views": web_views,
        "impressions": impressions
    }

def process_clicks_data(post, publication_name):
    """
    Process click data from a post.

    Returns:
        List of click objects
    """
    clicks_data = []
    post_clicks = post.get("clicks", [])

    for click in post_clicks:
        clicks_data.append({
            "publication": publication_name,
            "post_title": post.get("title", ""),
            "link_url": click.get("url", ""),
            "link_description": click.get("description", click.get("url", "")[:50]),
            "clicks": click.get("total_clicks", 0),
            "unique_clicks": click.get("total_unique_clicks", 0)
        })

    return clicks_data

# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_weekly_report(start_date, end_date=None):
    """
    Generate weekly report data for both publications.

    Args:
        start_date: Week start date (datetime or string YYYY-MM-DD)
        end_date: Week end date (optional, defaults to start_date + 6 days)
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

    if end_date is None:
        end_date = start_date + timedelta(days=6)
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Set end_date to end of day
    end_date = end_date.replace(hour=23, minute=59, second=59)

    print(f"\n{'='*60}")
    print(f"GENERATING WEEKLY REPORT")
    print(f"Week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")

    all_posts = []
    all_clicks = []

    for pub_name, pub_id in PUBLICATIONS.items():
        print(f"Fetching data for {pub_name}...")
        posts = fetch_posts(pub_id, start_date, end_date, expand=["stats", "clicks"])
        print(f"  Found {len(posts)} posts")

        for post in posts:
            post_data = process_post_data(post, pub_name)
            all_posts.append(post_data)

            clicks_data = process_clicks_data(post, pub_name)
            all_clicks.extend(clicks_data)

    # Sort posts by date
    all_posts.sort(key=lambda x: x["date"])

    # Sort clicks by total clicks (descending)
    all_clicks.sort(key=lambda x: x["clicks"], reverse=True)

    # Generate CSV files
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Weekly raw data
    weekly_csv = os.path.join(REPORTS_DIR, "weekly_raw_data.csv")
    write_posts_csv(all_posts, weekly_csv, include_month=False)
    print(f"\nWritten: {weekly_csv}")

    # Clicks data
    clicks_csv = os.path.join(REPORTS_DIR, "weekly_clicks_data.csv")
    write_clicks_csv(all_clicks, clicks_csv)
    print(f"Written: {clicks_csv}")

    # Generate summary report
    print_weekly_summary(all_posts, all_clicks, start_date, end_date)

    return all_posts, all_clicks

def generate_monthly_report(month, compare_month=None):
    """
    Generate monthly report with comparison to previous month.

    Args:
        month: Current month (string YYYY-MM)
        compare_month: Previous month for comparison (optional)
    """
    # Parse month
    current_date = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    current_start = current_date
    current_end = (current_date + relativedelta(months=1)) - timedelta(seconds=1)

    # Previous month
    if compare_month:
        prev_date = datetime.strptime(f"{compare_month}-01", "%Y-%m-%d")
    else:
        prev_date = current_date - relativedelta(months=1)
    prev_start = prev_date
    prev_end = (prev_date + relativedelta(months=1)) - timedelta(seconds=1)

    print(f"\n{'='*60}")
    print(f"GENERATING MONTHLY REPORT")
    print(f"Current Month: {current_start.strftime('%B %Y')}")
    print(f"Compare Month: {prev_start.strftime('%B %Y')}")
    print(f"{'='*60}\n")

    all_posts = []

    for pub_name, pub_id in PUBLICATIONS.items():
        print(f"Fetching data for {pub_name}...")

        # Current month
        print(f"  {current_start.strftime('%B %Y')}...")
        current_posts = fetch_posts(pub_id, current_start, current_end, expand=["stats"])
        print(f"    Found {len(current_posts)} posts")

        for post in current_posts:
            post_data = process_post_data(post, pub_name)
            all_posts.append(post_data)

        # Previous month
        print(f"  {prev_start.strftime('%B %Y')}...")
        prev_posts = fetch_posts(pub_id, prev_start, prev_end, expand=["stats"])
        print(f"    Found {len(prev_posts)} posts")

        for post in prev_posts:
            post_data = process_post_data(post, pub_name)
            all_posts.append(post_data)

    # Sort posts by date
    all_posts.sort(key=lambda x: (x["publication"], x["date"]))

    # Generate CSV file
    os.makedirs(REPORTS_DIR, exist_ok=True)

    monthly_csv = os.path.join(REPORTS_DIR, "monthly_raw_data.csv")
    write_posts_csv(all_posts, monthly_csv, include_month=True)
    print(f"\nWritten: {monthly_csv}")

    # Generate summary report
    print_monthly_summary(all_posts, current_start, prev_start)

    return all_posts

# =============================================================================
# OUTPUT HELPERS
# =============================================================================

def write_posts_csv(posts, filename, include_month=False):
    """Write posts data to CSV file."""
    if include_month:
        fieldnames = [
            "publication", "post_id", "title", "date", "month",
            "recipients", "opens", "unique_opens", "open_rate",
            "clicks", "unique_clicks", "click_rate", "unsubscribes",
            "web_views", "impressions"
        ]
    else:
        fieldnames = [
            "publication", "post_id", "title", "date",
            "recipients", "opens", "unique_opens", "open_rate",
            "clicks", "unique_clicks", "click_rate", "unsubscribes",
            "web_views", "impressions"
        ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(posts)

def write_clicks_csv(clicks, filename):
    """Write clicks data to CSV file."""
    fieldnames = [
        "publication", "post_title", "link_url",
        "link_description", "clicks", "unique_clicks"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clicks)

def print_weekly_summary(posts, clicks, start_date, end_date):
    """Print formatted weekly summary report."""
    print(f"\n{'='*60}")
    print("WEEKLY NEWSLETTER REPORT")
    print(f"Week of {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}")
    print(f"{'='*60}\n")

    for pub_name in PUBLICATIONS.keys():
        pub_posts = [p for p in posts if p["publication"] == pub_name]
        pub_clicks = [c for c in clicks if c["publication"] == pub_name]

        if not pub_posts:
            continue

        # Calculate metrics
        post_count = len(pub_posts)
        avg_sent = sum(p["recipients"] for p in pub_posts) / post_count
        total_impressions = sum(p["impressions"] for p in pub_posts)
        avg_unique_opens = sum(p["unique_opens"] for p in pub_posts) / post_count
        avg_open_rate = sum(p["open_rate"] for p in pub_posts) / post_count
        total_clicks = sum(p["clicks"] for p in pub_posts)
        avg_unique_clicks = sum(p["unique_clicks"] for p in pub_posts) / post_count
        avg_click_rate = sum(p["click_rate"] for p in pub_posts) / post_count
        total_unsubs = sum(p["unsubscribes"] for p in pub_posts)

        display_name = "El Tiempo Latino" if "ETL" in pub_name else "El Planeta"
        print(f"{display_name.upper()} DAILY")
        print("-" * 40)
        print(f"  Posts Sent:        {post_count}")
        print(f"  Avg Sent:          {avg_sent:,.0f}")
        print(f"  Impressions:       {total_impressions:,}")
        print(f"  Avg Unique Opens:  {avg_unique_opens:,.0f}")
        print(f"  Avg Open Rate:     {avg_open_rate:.2f}%")
        print(f"  Total Clicks:      {total_clicks:,}")
        print(f"  Avg Unique Clicks: {avg_unique_clicks:.0f}")
        print(f"  Avg Click Rate:    {avg_click_rate:.2f}%")
        print(f"  Unsubscribes:      {total_unsubs}")

        # Top posts by open rate
        print(f"\n  Top Posts (by Open Rate):")
        top_posts = sorted(pub_posts, key=lambda x: x["open_rate"], reverse=True)[:3]
        for i, post in enumerate(top_posts, 1):
            print(f"    {i}. {post['title'][:40]}")
            print(f"       {post['date']} | {post['open_rate']:.2f}% | {post['impressions']:,} imp | {post['clicks']} clicks")

        # Top links
        if pub_clicks:
            print(f"\n  Top Clicked Links:")
            top_links = sorted(pub_clicks, key=lambda x: x["clicks"], reverse=True)[:3]
            for i, link in enumerate(top_links, 1):
                desc = link["link_description"][:50] if link["link_description"] else link["link_url"][:50]
                print(f"    {i}. {desc}")
                print(f"       {link['clicks']} clicks ({link['unique_clicks']} unique)")

        print()

def print_monthly_summary(posts, current_month, prev_month):
    """Print formatted monthly comparison report."""
    current_month_str = current_month.strftime("%Y-%m")
    prev_month_str = prev_month.strftime("%Y-%m")

    print(f"\n{'='*60}")
    print("MONTHLY NEWSLETTER REPORT")
    print(f"{current_month.strftime('%B %Y')} vs {prev_month.strftime('%B %Y')}")
    print(f"{'='*60}\n")

    for pub_name in PUBLICATIONS.keys():
        current_posts = [p for p in posts if p["publication"] == pub_name and p["month"] == current_month_str]
        prev_posts = [p for p in posts if p["publication"] == pub_name and p["month"] == prev_month_str]

        if not current_posts or not prev_posts:
            continue

        display_name = "El Tiempo Latino" if "ETL" in pub_name else "El Planeta"
        print(f"{display_name.upper()} DAILY")
        print("-" * 60)

        # Calculate metrics for both months
        metrics = []

        def calc_metrics(posts_list):
            count = len(posts_list)
            return {
                "posts": count,
                "impressions": sum(p["impressions"] for p in posts_list),
                "avg_unique_opens": sum(p["unique_opens"] for p in posts_list) / count if count else 0,
                "avg_open_rate": sum(p["open_rate"] for p in posts_list) / count if count else 0,
                "total_clicks": sum(p["clicks"] for p in posts_list),
                "avg_unique_clicks": sum(p["unique_clicks"] for p in posts_list) / count if count else 0,
                "avg_click_rate": sum(p["click_rate"] for p in posts_list) / count if count else 0,
                "unsubscribes": sum(p["unsubscribes"] for p in posts_list)
            }

        curr = calc_metrics(current_posts)
        prev = calc_metrics(prev_posts)

        def fmt_change(curr_val, prev_val, is_pct=False):
            if prev_val == 0:
                return "N/A"
            change = ((curr_val - prev_val) / prev_val) * 100
            sign = "+" if change >= 0 else ""
            if is_pct:
                diff = curr_val - prev_val
                return f"{sign}{diff:.2f}pp"
            return f"{sign}{change:.1f}%"

        print(f"  {'Metric':<20} {current_month.strftime('%b %Y'):>12} {prev_month.strftime('%b %Y'):>12} {'Change':>12}")
        print(f"  {'-'*56}")
        print(f"  {'Posts Sent':<20} {curr['posts']:>12} {prev['posts']:>12} {fmt_change(curr['posts'], prev['posts']):>12}")
        print(f"  {'Impressions':<20} {curr['impressions']:>12,} {prev['impressions']:>12,} {fmt_change(curr['impressions'], prev['impressions']):>12}")
        print(f"  {'Avg Unique Opens':<20} {curr['avg_unique_opens']:>12,.0f} {prev['avg_unique_opens']:>12,.0f} {fmt_change(curr['avg_unique_opens'], prev['avg_unique_opens']):>12}")
        print(f"  {'Avg Open Rate':<20} {curr['avg_open_rate']:>11.2f}% {prev['avg_open_rate']:>11.2f}% {fmt_change(curr['avg_open_rate'], prev['avg_open_rate'], True):>12}")
        print(f"  {'Total Clicks':<20} {curr['total_clicks']:>12,} {prev['total_clicks']:>12,} {fmt_change(curr['total_clicks'], prev['total_clicks']):>12}")
        print(f"  {'Avg Unique Clicks':<20} {curr['avg_unique_clicks']:>12,.0f} {prev['avg_unique_clicks']:>12,.0f} {fmt_change(curr['avg_unique_clicks'], prev['avg_unique_clicks']):>12}")
        print(f"  {'Avg Click Rate':<20} {curr['avg_click_rate']:>11.2f}% {prev['avg_click_rate']:>11.2f}% {fmt_change(curr['avg_click_rate'], prev['avg_click_rate'], True):>12}")
        print(f"  {'Unsubscribes':<20} {curr['unsubscribes']:>12} {prev['unsubscribes']:>12} {fmt_change(curr['unsubscribes'], prev['unsubscribes']):>12}")
        print()

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate newsletter reports from Beehiiv data"
    )

    parser.add_argument(
        "--week",
        type=str,
        help="Generate weekly report starting from this date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--month",
        type=str,
        help="Generate monthly report for this month (YYYY-MM)"
    )

    parser.add_argument(
        "--compare",
        type=str,
        help="Month to compare against for monthly report (YYYY-MM)"
    )

    args = parser.parse_args()

    if not args.week and not args.month:
        print("Error: Please specify --week or --month")
        print("\nExamples:")
        print("  python newsletter_report.py --week 2026-01-05")
        print("  python newsletter_report.py --month 2025-12")
        print("  python newsletter_report.py --month 2025-12 --compare 2025-11")
        sys.exit(1)

    if args.week:
        generate_weekly_report(args.week)

    if args.month:
        generate_monthly_report(args.month, args.compare)

if __name__ == "__main__":
    main()
