# Tiempo Company Newsletter Reports

Automated newsletter reporting for El Tiempo Latino and El Planeta.

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/fortega/tiempocompany/reporting
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Required: Beehiiv API key
export BEEHIIV_API_KEY='your_beehiiv_api_key'

# Optional: Slack webhook for posting reports
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

### 3. Generate Reports

**Weekly Report:**
```bash
python scripts/generate_report.py --week 2026-01-05
```

**Weekly Report + Post to Slack:**
```bash
python scripts/generate_report.py --week 2026-01-05 --slack
```

**Monthly Report with Comparison:**
```bash
python scripts/generate_report.py --month 2025-12 --compare 2025-11 --slack
```

## Output

Reports are saved to the `reports/` folder as HTML files:
- `reports/weekly_report_2026-01-05.html`
- `reports/monthly_report_2025-12.html`

## Setting Up Slack Webhook

1. Go to https://api.slack.com/apps
2. Create a new app (or use existing)
3. Enable "Incoming Webhooks"
4. Add a webhook to your desired channel
5. Copy the webhook URL and set it as `SLACK_WEBHOOK_URL`

## Automating Reports (Optional)

To run reports automatically every Monday at 9am:

**On Mac/Linux (cron):**
```bash
crontab -e
# Add this line:
0 9 * * 1 cd /Users/fortega/tiempocompany/reporting && /usr/bin/python3 scripts/generate_report.py --week $(date -v-7d +\%Y-\%m-\%d) --slack
```

## Files

```
reporting/
├── scripts/
│   ├── generate_report.py    # Main report generator (HTML + Slack)
│   └── newsletter_report.py  # CSV data exporter (for Google Sheets)
├── reports/                  # Generated reports go here
├── templates/                # Sample data and documentation
├── requirements.txt
└── README.md
```

## Publications

- **El Tiempo Latino Daily** (ETL) - Washington DC area
- **El Planeta Daily** (EP) - Boston area
