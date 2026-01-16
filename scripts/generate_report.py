#!/usr/bin/env python3
"""
Tiempo Company Newsletter Report Generator

Generates beautiful HTML reports from Beehiiv data and posts them to Slack.
Includes week-over-week and month-over-month comparisons.

Usage:
    python generate_report.py --week 2026-01-05 --slack
    python generate_report.py --month 2025-12 --slack
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

BEEHIIV_API_BASE = "https://api.beehiiv.com/v2"
BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

PUBLICATIONS = {
    "ETL Daily": {
        "id": "pub_88b8ccea-c311-4381-a49c-91848583ba9e",
        "display_name": "El Tiempo Latino",
        "color": "#1a73e8"
    },
    "EP Daily": {
        "id": "pub_2dd3324c-fa75-40a2-acf2-df2acff63d10",
        "display_name": "El Planeta",
        "color": "#ea4335"
    }
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

# =============================================================================
# API HELPERS
# =============================================================================

def get_headers():
    if not BEEHIIV_API_KEY:
        print("ERROR: BEEHIIV_API_KEY environment variable not set")
        sys.exit(1)
    return {"Authorization": f"Bearer {BEEHIIV_API_KEY}", "Content-Type": "application/json"}

def fetch_posts(publication_id, start_date, end_date):
    """Fetch posts from Beehiiv API for a date range."""
    url = f"{BEEHIIV_API_BASE}/publications/{publication_id}/posts"
    start_ts, end_ts = int(start_date.timestamp()), int(end_date.timestamp())

    all_posts = []
    page = 1

    while True:
        params = {"status": "confirmed", "limit": 100, "page": page, "expand[]": ["stats", "clicks"]}
        response = requests.get(url, headers=get_headers(), params=params)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()
        posts = data.get("data", [])

        if not posts:
            break

        for post in posts:
            publish_date = post.get("publish_date", 0)
            if start_ts <= publish_date <= end_ts:
                all_posts.append(post)

        if page >= data.get("total_pages", 1):
            break
        page += 1

    return all_posts

def process_post(post):
    """Extract metrics from a post."""
    stats = post.get("stats", {})
    email = stats.get("email", {})
    web = stats.get("web", {})

    recipients = email.get("recipients", 0)
    unique_opens = email.get("unique_opens", 0)
    unique_clicks = email.get("unique_clicks", 0)
    opens = email.get("opens", 0)
    web_views = web.get("views", 0)

    # Extract top clicks
    clicks_data = []
    for click in post.get("clicks", [])[:5]:
        clicks_data.append({
            "url": click.get("url", ""),
            "description": click.get("description", click.get("url", "")[:50]),
            "clicks": click.get("total_clicks", 0),
            "unique_clicks": click.get("total_unique_clicks", 0)
        })

    return {
        "title": post.get("title", ""),
        "date": datetime.fromtimestamp(post.get("publish_date", 0)),
        "recipients": recipients,
        "opens": opens,
        "unique_opens": unique_opens,
        "open_rate": (unique_opens / recipients * 100) if recipients > 0 else 0,
        "clicks": email.get("clicks", 0),
        "unique_clicks": unique_clicks,
        "click_rate": (unique_clicks / recipients * 100) if recipients > 0 else 0,
        "unsubscribes": email.get("unsubscribes", 0),
        "web_views": web_views,
        "impressions": opens + web_views,
        "top_clicks": clicks_data
    }

def calc_metrics(posts):
    """Calculate aggregate metrics from a list of posts."""
    if not posts:
        return None
    count = len(posts)
    return {
        "posts_sent": count,
        "avg_sent": int(sum(p['recipients'] for p in posts) / count),
        "impressions": sum(p['impressions'] for p in posts),
        "avg_unique_opens": int(sum(p['unique_opens'] for p in posts) / count),
        "avg_open_rate": sum(p['open_rate'] for p in posts) / count,
        "total_clicks": sum(p['clicks'] for p in posts),
        "avg_unique_clicks": int(sum(p['unique_clicks'] for p in posts) / count),
        "avg_click_rate": sum(p['click_rate'] for p in posts) / count,
        "unsubscribes": sum(p['unsubscribes'] for p in posts),
        "top_posts": sorted(posts, key=lambda x: x['open_rate'], reverse=True)[:3]
    }

def calc_change(current, previous, is_percentage=False):
    """Calculate change between two values."""
    if previous == 0:
        return {"value": 0, "display": "N/A", "positive": True}

    if is_percentage:
        # For percentages, show percentage point difference
        diff = current - previous
        return {
            "value": diff,
            "display": f"{diff:+.2f}pp",
            "positive": diff >= 0
        }
    else:
        # For regular numbers, show percentage change
        pct_change = ((current - previous) / previous) * 100
        return {
            "value": pct_change,
            "display": f"{pct_change:+.1f}%",
            "positive": pct_change >= 0
        }

# =============================================================================
# HTML REPORT GENERATOR
# =============================================================================

def generate_weekly_html(report_data):
    """Generate HTML for weekly report with week-over-week comparison."""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            color: white;
            padding: 30px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .subtitle {{ opacity: 0.9; font-size: 16px; }}
        .content {{ background: white; padding: 30px; border-radius: 0 0 12px 12px; }}

        .publication {{
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .pub-header {{
            padding: 15px 20px;
            color: white;
            font-weight: 600;
            font-size: 18px;
        }}
        .pub-content {{ padding: 20px; }}

        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .comparison-table th, .comparison-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        .comparison-table th {{
            background: #f8f9fa;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
        }}
        .comparison-table td {{ font-size: 14px; }}
        .comparison-table tr:last-child td {{ border-bottom: none; }}
        .comparison-table .metric-name {{ font-weight: 500; }}
        .comparison-table .current {{ font-weight: 600; color: #333; }}
        .comparison-table .previous {{ color: #666; }}

        .change-positive {{ color: #34a853; font-weight: 600; }}
        .change-negative {{ color: #ea4335; font-weight: 600; }}

        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin: 25px 0 15px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }}

        .top-posts {{ margin-top: 15px; }}
        .post-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 8px;
        }}
        .post-rank {{
            font-weight: 700;
            color: #1a73e8;
            margin-right: 12px;
            font-size: 16px;
        }}
        .post-title {{ font-weight: 500; flex: 1; }}
        .post-date {{ color: #666; font-size: 12px; margin-left: 10px; }}
        .post-stats {{
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #666;
        }}
        .stat-highlight {{ color: #1a73e8; font-weight: 600; }}

        .top-links {{ margin-top: 15px; }}
        .link-item {{
            padding: 10px 15px;
            background: #fff3e0;
            border-radius: 6px;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .link-desc {{ flex: 1; font-size: 13px; }}
        .link-clicks {{ font-weight: 600; color: #e65100; }}

        .totals-section {{
            background: #e3f2fd;
            margin-top: 20px;
            padding: 20px;
            border-radius: 8px;
        }}
        .totals-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        .total-item {{ text-align: center; }}
        .total-value {{ font-size: 24px; font-weight: 700; color: #1a73e8; }}
        .total-label {{ font-size: 11px; color: #666; margin-top: 4px; text-transform: uppercase; }}
        .total-change {{ font-size: 12px; margin-top: 2px; }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TIEMPO COMPANY</h1>
            <div class="subtitle">Weekly Newsletter Report</div>
            <div class="subtitle" style="margin-top: 5px; font-size: 14px;">
                {report_data['current_period']} vs {report_data['previous_period']}
            </div>
        </div>
        <div class="content">
"""

    # Add publication sections
    for pub_key in ["ETL Daily", "EP Daily"]:
        if pub_key not in report_data['publications']:
            continue

        pub_data = report_data['publications'][pub_key]
        pub_info = PUBLICATIONS.get(pub_key, {})
        color = pub_info.get('color', '#1a73e8')
        display_name = pub_info.get('display_name', pub_key)

        curr = pub_data['current']
        prev = pub_data['previous']
        changes = pub_data['changes']

        # Helper function to format previous values
        def fmt_prev(val, fmt_type='number'):
            if not prev:
                return '-'
            if fmt_type == 'number':
                return f"{val:,}"
            elif fmt_type == 'percent':
                return f"{val:.2f}%"
            else:
                return str(val)

        def chg_class(change_data, invert=False):
            positive = change_data['positive']
            if invert:
                positive = not positive
            return 'change-positive' if positive else 'change-negative'

        html += f"""
            <div class="publication">
                <div class="pub-header" style="background: {color};">{display_name} Daily</div>
                <div class="pub-content">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>This Week</th>
                                <th>Last Week</th>
                                <th>Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="metric-name">Posts Sent</td>
                                <td class="current">{curr['posts_sent']}</td>
                                <td class="previous">{prev['posts_sent'] if prev else '-'}</td>
                                <td class="{chg_class(changes['posts_sent'])}">{changes['posts_sent']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Avg Sent</td>
                                <td class="current">{curr['avg_sent']:,}</td>
                                <td class="previous">{fmt_prev(prev['avg_sent'] if prev else 0)}</td>
                                <td class="{chg_class(changes['avg_sent'])}">{changes['avg_sent']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Impressions</td>
                                <td class="current">{curr['impressions']:,}</td>
                                <td class="previous">{fmt_prev(prev['impressions'] if prev else 0)}</td>
                                <td class="{chg_class(changes['impressions'])}">{changes['impressions']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Avg Unique Opens</td>
                                <td class="current">{curr['avg_unique_opens']:,}</td>
                                <td class="previous">{fmt_prev(prev['avg_unique_opens'] if prev else 0)}</td>
                                <td class="{chg_class(changes['avg_unique_opens'])}">{changes['avg_unique_opens']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Avg Open Rate</td>
                                <td class="current">{curr['avg_open_rate']:.2f}%</td>
                                <td class="previous">{fmt_prev(prev['avg_open_rate'] if prev else 0, 'percent')}</td>
                                <td class="{chg_class(changes['avg_open_rate'])}">{changes['avg_open_rate']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Total Clicks</td>
                                <td class="current">{curr['total_clicks']:,}</td>
                                <td class="previous">{fmt_prev(prev['total_clicks'] if prev else 0)}</td>
                                <td class="{chg_class(changes['total_clicks'])}">{changes['total_clicks']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Avg Click Rate</td>
                                <td class="current">{curr['avg_click_rate']:.2f}%</td>
                                <td class="previous">{fmt_prev(prev['avg_click_rate'] if prev else 0, 'percent')}</td>
                                <td class="{chg_class(changes['avg_click_rate'])}">{changes['avg_click_rate']['display']}</td>
                            </tr>
                            <tr>
                                <td class="metric-name">Unsubscribes</td>
                                <td class="current">{curr['unsubscribes']}</td>
                                <td class="previous">{prev['unsubscribes'] if prev else '-'}</td>
                                <td class="{chg_class(changes['unsubscribes'], invert=True)}">{changes['unsubscribes']['display']}</td>
                            </tr>
                        </tbody>
                    </table>
"""

        # Top posts section
        if curr.get('top_posts'):
            html += """
                    <div class="section-title">Top Performing Posts (by Open Rate)</div>
                    <div class="top-posts">
"""
            for i, post in enumerate(curr['top_posts'][:3], 1):
                title = post['title'][:50] + ('...' if len(post['title']) > 50 else '')
                html += f"""
                        <div class="post-item">
                            <span class="post-rank">{i}</span>
                            <span class="post-title">{title}</span>
                            <span class="post-date">{post['date'].strftime('%b %d')}</span>
                            <div class="post-stats">
                                <span><span class="stat-highlight">{post['open_rate']:.1f}%</span> open</span>
                                <span>{post['impressions']:,} imp</span>
                                <span>{post['clicks']} clicks</span>
                            </div>
                        </div>
"""
            html += """
                    </div>
"""

        # Top clicked links section
        if pub_data.get('top_clicks'):
            html += """
                    <div class="section-title">Top Clicked Links</div>
                    <div class="top-links">
"""
            for i, link in enumerate(pub_data['top_clicks'][:5], 1):
                desc = link['description'][:60] if link['description'] else link['url'][:60]
                html += f"""
                        <div class="link-item">
                            <span class="link-desc">{i}. {desc}</span>
                            <span class="link-clicks">{link['clicks']} clicks</span>
                        </div>
"""
            html += """
                    </div>
"""

        html += """
                </div>
            </div>
"""

    # Combined Totals section
    totals = report_data.get('totals', {})
    if totals:
        def tot_chg_class(key):
            return 'change-positive' if totals['changes'][key]['positive'] else 'change-negative'

        html += f"""
            <div class="totals-section">
                <div class="section-title" style="margin-top: 0; border-bottom: none;">Combined Totals</div>
                <div class="totals-grid">
                    <div class="total-item">
                        <div class="total-value">{totals['current']['posts']}</div>
                        <div class="total-label">Total Posts</div>
                        <div class="total-change {tot_chg_class('posts')}">{totals['changes']['posts']['display']}</div>
                    </div>
                    <div class="total-item">
                        <div class="total-value">{totals['current']['impressions']:,}</div>
                        <div class="total-label">Total Impressions</div>
                        <div class="total-change {tot_chg_class('impressions')}">{totals['changes']['impressions']['display']}</div>
                    </div>
                    <div class="total-item">
                        <div class="total-value">{totals['current']['avg_open_rate']:.1f}%</div>
                        <div class="total-label">Avg Open Rate</div>
                        <div class="total-change {tot_chg_class('avg_open_rate')}">{totals['changes']['avg_open_rate']['display']}</div>
                    </div>
                    <div class="total-item">
                        <div class="total-value">{totals['current']['clicks']:,}</div>
                        <div class="total-label">Total Clicks</div>
                        <div class="total-change {tot_chg_class('clicks')}">{totals['changes']['clicks']['display']}</div>
                    </div>
                </div>
            </div>
"""

    html += f"""
        </div>
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
    </div>
</body>
</html>
"""

    return html

# =============================================================================
# SLACK INTEGRATION
# =============================================================================

def post_to_slack(report_data, html_file_path, report_type="weekly"):
    """Post report summary to Slack."""

    if not SLACK_WEBHOOK_URL:
        print("WARNING: SLACK_WEBHOOK_URL not set. Skipping Slack post.")
        return False

    totals = report_data.get('totals', {})
    curr_totals = totals.get('current', {})
    changes = totals.get('changes', {})

    # Build Slack message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 {'Weekly' if report_type == 'weekly' else 'Monthly'} Newsletter Report"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{report_data['current_period']}* vs *{report_data['previous_period']}*"
            }
        },
        {"type": "divider"}
    ]

    # Add publication summaries
    for pub_key in ["ETL Daily", "EP Daily"]:
        if pub_key not in report_data['publications']:
            continue

        pub_data = report_data['publications'][pub_key]
        pub_info = PUBLICATIONS.get(pub_key, {})
        display_name = pub_info.get('display_name', pub_key)
        emoji = "🔵" if "ETL" in pub_key else "🔴"

        curr = pub_data['current']
        chg = pub_data['changes']

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{display_name} Daily*\n" +
                       f"📬 Posts: *{curr['posts_sent']}* ({chg['posts_sent']['display']}) | " +
                       f"👁️ Impressions: *{curr['impressions']:,}* ({chg['impressions']['display']})\n" +
                       f"📖 Open Rate: *{curr['avg_open_rate']:.1f}%* ({chg['avg_open_rate']['display']}) | " +
                       f"🖱️ Clicks: *{curr['total_clicks']:,}* ({chg['total_clicks']['display']})"
            }
        })

    # Add link to full report (will be replaced with actual URL after upload)
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"📄 Full report: {html_file_path}"}]
    })

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"blocks": blocks})
        if response.status_code == 200:
            print("✅ Report posted to Slack!")
            return True
        else:
            print(f"❌ Slack error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Slack error: {e}")
        return False

# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_weekly_report(start_date_str, post_to_slack_flag=False):
    """Generate weekly report with week-over-week comparison."""

    # Current week
    curr_start = datetime.strptime(start_date_str, "%Y-%m-%d")
    curr_end = curr_start + timedelta(days=6)
    curr_end = curr_end.replace(hour=23, minute=59, second=59)

    # Previous week
    prev_start = curr_start - timedelta(days=7)
    prev_end = prev_start + timedelta(days=6)
    prev_end = prev_end.replace(hour=23, minute=59, second=59)

    print(f"\n{'='*60}")
    print(f"GENERATING WEEKLY REPORT")
    print(f"Current: {curr_start.strftime('%b %d')} - {curr_end.strftime('%b %d, %Y')}")
    print(f"Previous: {prev_start.strftime('%b %d')} - {prev_end.strftime('%b %d, %Y')}")
    print(f"{'='*60}\n")

    report_data = {
        "current_period": f"{curr_start.strftime('%B %d')} - {curr_end.strftime('%B %d, %Y')}",
        "previous_period": f"{prev_start.strftime('%B %d')} - {prev_end.strftime('%B %d')}",
        "publications": {},
        "totals": {
            "current": {"posts": 0, "impressions": 0, "clicks": 0, "open_rates": []},
            "previous": {"posts": 0, "impressions": 0, "clicks": 0, "open_rates": []}
        }
    }

    for pub_key, pub_info in PUBLICATIONS.items():
        print(f"Fetching {pub_info['display_name']}...")

        # Fetch current week
        curr_posts = fetch_posts(pub_info['id'], curr_start, curr_end)
        curr_processed = [process_post(p) for p in curr_posts]
        print(f"  Current week: {len(curr_posts)} posts")

        # Fetch previous week
        prev_posts = fetch_posts(pub_info['id'], prev_start, prev_end)
        prev_processed = [process_post(p) for p in prev_posts]
        print(f"  Previous week: {len(prev_posts)} posts")

        curr_metrics = calc_metrics(curr_processed)
        prev_metrics = calc_metrics(prev_processed)

        if not curr_metrics:
            continue

        # Collect top clicks from all posts
        all_clicks = []
        for post in curr_processed:
            for click in post.get('top_clicks', []):
                click['post_title'] = post['title']
                all_clicks.append(click)
        all_clicks.sort(key=lambda x: x['clicks'], reverse=True)

        # Calculate changes
        changes = {}
        for key in ['posts_sent', 'avg_sent', 'impressions', 'avg_unique_opens', 'total_clicks', 'avg_unique_clicks', 'unsubscribes']:
            prev_val = prev_metrics[key] if prev_metrics else 0
            changes[key] = calc_change(curr_metrics[key], prev_val)

        # Percentage changes (use pp)
        for key in ['avg_open_rate', 'avg_click_rate']:
            prev_val = prev_metrics[key] if prev_metrics else 0
            changes[key] = calc_change(curr_metrics[key], prev_val, is_percentage=True)

        report_data['publications'][pub_key] = {
            "current": curr_metrics,
            "previous": prev_metrics,
            "changes": changes,
            "top_clicks": all_clicks[:5]
        }

        # Add to totals
        report_data['totals']['current']['posts'] += curr_metrics['posts_sent']
        report_data['totals']['current']['impressions'] += curr_metrics['impressions']
        report_data['totals']['current']['clicks'] += curr_metrics['total_clicks']
        report_data['totals']['current']['open_rates'].append(curr_metrics['avg_open_rate'])

        if prev_metrics:
            report_data['totals']['previous']['posts'] += prev_metrics['posts_sent']
            report_data['totals']['previous']['impressions'] += prev_metrics['impressions']
            report_data['totals']['previous']['clicks'] += prev_metrics['total_clicks']
            report_data['totals']['previous']['open_rates'].append(prev_metrics['avg_open_rate'])

    # Calculate total averages and changes
    curr_t = report_data['totals']['current']
    prev_t = report_data['totals']['previous']

    curr_t['avg_open_rate'] = sum(curr_t['open_rates']) / len(curr_t['open_rates']) if curr_t['open_rates'] else 0
    prev_t['avg_open_rate'] = sum(prev_t['open_rates']) / len(prev_t['open_rates']) if prev_t['open_rates'] else 0

    report_data['totals']['changes'] = {
        'posts': calc_change(curr_t['posts'], prev_t['posts']),
        'impressions': calc_change(curr_t['impressions'], prev_t['impressions']),
        'clicks': calc_change(curr_t['clicks'], prev_t['clicks']),
        'avg_open_rate': calc_change(curr_t['avg_open_rate'], prev_t['avg_open_rate'], is_percentage=True)
    }

    # Generate HTML
    html = generate_weekly_html(report_data)

    # Save file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"weekly_report_{curr_start.strftime('%Y-%m-%d')}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HTML report saved: {filepath}")

    if post_to_slack_flag:
        post_to_slack(report_data, filepath, "weekly")

    return filepath

def generate_monthly_report(month_str, compare_month_str=None, post_to_slack_flag=False):
    """Generate monthly report with month-over-month comparison."""

    # Current month
    curr_date = datetime.strptime(f"{month_str}-01", "%Y-%m-%d")
    curr_start = curr_date
    curr_end = (curr_date + relativedelta(months=1)) - timedelta(seconds=1)

    # Previous month
    if compare_month_str:
        prev_date = datetime.strptime(f"{compare_month_str}-01", "%Y-%m-%d")
    else:
        prev_date = curr_date - relativedelta(months=1)
    prev_start = prev_date
    prev_end = (prev_date + relativedelta(months=1)) - timedelta(seconds=1)

    print(f"\n{'='*60}")
    print(f"GENERATING MONTHLY REPORT")
    print(f"Current: {curr_start.strftime('%B %Y')}")
    print(f"Previous: {prev_start.strftime('%B %Y')}")
    print(f"{'='*60}\n")

    report_data = {
        "current_period": curr_start.strftime('%B %Y'),
        "previous_period": prev_start.strftime('%B %Y'),
        "publications": {},
        "totals": {
            "current": {"posts": 0, "impressions": 0, "clicks": 0, "open_rates": []},
            "previous": {"posts": 0, "impressions": 0, "clicks": 0, "open_rates": []}
        }
    }

    for pub_key, pub_info in PUBLICATIONS.items():
        print(f"Fetching {pub_info['display_name']}...")

        curr_posts = fetch_posts(pub_info['id'], curr_start, curr_end)
        curr_processed = [process_post(p) for p in curr_posts]
        print(f"  {curr_start.strftime('%B')}: {len(curr_posts)} posts")

        prev_posts = fetch_posts(pub_info['id'], prev_start, prev_end)
        prev_processed = [process_post(p) for p in prev_posts]
        print(f"  {prev_start.strftime('%B')}: {len(prev_posts)} posts")

        curr_metrics = calc_metrics(curr_processed)
        prev_metrics = calc_metrics(prev_processed)

        if not curr_metrics:
            continue

        # Collect top clicks
        all_clicks = []
        for post in curr_processed:
            for click in post.get('top_clicks', []):
                click['post_title'] = post['title']
                all_clicks.append(click)
        all_clicks.sort(key=lambda x: x['clicks'], reverse=True)

        # Calculate changes
        changes = {}
        for key in ['posts_sent', 'avg_sent', 'impressions', 'avg_unique_opens', 'total_clicks', 'avg_unique_clicks', 'unsubscribes']:
            prev_val = prev_metrics[key] if prev_metrics else 0
            changes[key] = calc_change(curr_metrics[key], prev_val)

        for key in ['avg_open_rate', 'avg_click_rate']:
            prev_val = prev_metrics[key] if prev_metrics else 0
            changes[key] = calc_change(curr_metrics[key], prev_val, is_percentage=True)

        report_data['publications'][pub_key] = {
            "current": curr_metrics,
            "previous": prev_metrics,
            "changes": changes,
            "top_clicks": all_clicks[:5]
        }

        # Add to totals
        report_data['totals']['current']['posts'] += curr_metrics['posts_sent']
        report_data['totals']['current']['impressions'] += curr_metrics['impressions']
        report_data['totals']['current']['clicks'] += curr_metrics['total_clicks']
        report_data['totals']['current']['open_rates'].append(curr_metrics['avg_open_rate'])

        if prev_metrics:
            report_data['totals']['previous']['posts'] += prev_metrics['posts_sent']
            report_data['totals']['previous']['impressions'] += prev_metrics['impressions']
            report_data['totals']['previous']['clicks'] += prev_metrics['total_clicks']
            report_data['totals']['previous']['open_rates'].append(prev_metrics['avg_open_rate'])

    # Calculate total averages
    curr_t = report_data['totals']['current']
    prev_t = report_data['totals']['previous']

    curr_t['avg_open_rate'] = sum(curr_t['open_rates']) / len(curr_t['open_rates']) if curr_t['open_rates'] else 0
    prev_t['avg_open_rate'] = sum(prev_t['open_rates']) / len(prev_t['open_rates']) if prev_t['open_rates'] else 0

    report_data['totals']['changes'] = {
        'posts': calc_change(curr_t['posts'], prev_t['posts']),
        'impressions': calc_change(curr_t['impressions'], prev_t['impressions']),
        'clicks': calc_change(curr_t['clicks'], prev_t['clicks']),
        'avg_open_rate': calc_change(curr_t['avg_open_rate'], prev_t['avg_open_rate'], is_percentage=True)
    }

    # Generate HTML (reuse weekly format)
    html = generate_weekly_html(report_data)

    # Save file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"monthly_report_{month_str}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HTML report saved: {filepath}")

    if post_to_slack_flag:
        post_to_slack(report_data, filepath, "monthly")

    return filepath

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate newsletter reports with comparisons")
    parser.add_argument("--week", type=str, help="Generate weekly report (YYYY-MM-DD)")
    parser.add_argument("--month", type=str, help="Generate monthly report (YYYY-MM)")
    parser.add_argument("--compare", type=str, help="Month to compare against (YYYY-MM)")
    parser.add_argument("--slack", action="store_true", help="Post report to Slack")

    args = parser.parse_args()

    if not args.week and not args.month:
        print("Error: Specify --week or --month")
        print("\nExamples:")
        print("  python generate_report.py --week 2026-01-05")
        print("  python generate_report.py --week 2026-01-05 --slack")
        print("  python generate_report.py --month 2025-12 --compare 2025-11 --slack")
        sys.exit(1)

    if args.week:
        generate_weekly_report(args.week, args.slack)

    if args.month:
        generate_monthly_report(args.month, args.compare, args.slack)

if __name__ == "__main__":
    main()
