# Tiempo Company Newsletter Reports - Google Sheets Template

## Google Sheets URL

**Spreadsheet:** https://docs.google.com/spreadsheets/d/1XpXZmC1TRcd2QdJqPd_deDUnKULtWVDNzM6WFNDkHjo/

## Using the Python Script

### Prerequisites

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Beehiiv API key:
   ```bash
   export BEEHIIV_API_KEY='your_api_key_here'
   ```

### Generate Weekly Report

```bash
# Generate report for week of January 5, 2026
python scripts/newsletter_report.py --week 2026-01-05
```

This will create:
- `reports/weekly_raw_data.csv` - Import into Raw_Data_Weekly tab
- `reports/weekly_clicks_data.csv` - Import into Raw_Data_Clicks tab

### Generate Monthly Report

```bash
# Generate December 2025 vs November 2025 comparison
python scripts/newsletter_report.py --month 2025-12 --compare 2025-11
```

This will create:
- `reports/monthly_raw_data.csv` - Import into Raw_Data_Monthly tab

### Importing Data to Google Sheets

1. Open the Google Sheet
2. Go to the appropriate tab (e.g., Raw_Data_Weekly)
3. File > Import > Upload the CSV file
4. Choose "Replace current sheet" or "Replace data at selected cell"
5. The report tabs will automatically update with new calculations

---

## Sheet Structure

Create a Google Sheet with the following tabs:

### Tab 1: `Raw_Data_Weekly`
Import `weekly_raw_data.csv` - This is where the Python script will write data.

| Column | Header | Description |
|--------|--------|-------------|
| A | publication | ETL Daily or EP Daily |
| B | post_id | Unique post identifier |
| C | title | Post title |
| D | date | Publication date (YYYY-MM-DD) |
| E | recipients | Number of emails sent |
| F | opens | Total opens |
| G | unique_opens | Unique opens |
| H | open_rate | Open rate % |
| I | clicks | Total clicks |
| J | unique_clicks | Unique clicks |
| K | click_rate | Click rate % |
| L | unsubscribes | Unsubscribes |
| M | web_views | Web page views |
| N | impressions | opens + web_views |

---

### Tab 2: `Raw_Data_Clicks`
Import `weekly_clicks_data.csv`

| Column | Header |
|--------|--------|
| A | publication |
| B | post_title |
| C | link_url |
| D | link_description |
| E | clicks |
| F | unique_clicks |

---

### Tab 3: `Raw_Data_Monthly`
Import `monthly_raw_data.csv` - Historical data for month-over-month.

Same structure as Raw_Data_Weekly plus:
| Column | Header |
|--------|--------|
| E | month | Month (YYYY-MM format) |

---

### Tab 4: `Weekly_Report`
This is the formatted report view.

#### Cell Layout:

**Row 1-3: Header**
```
A1: TIEMPO COMPANY - WEEKLY NEWSLETTER REPORT
A2: Week of
B2: [Formula: =TEXT(MIN(Raw_Data_Weekly!D:D),"MMMM D") & " - " & TEXT(MAX(Raw_Data_Weekly!D:D),"MMMM D, YYYY")]
```

**Row 5-15: Summary Table**
```
     A                          B                    C                    D
5    Metric                     El Tiempo Latino     El Planeta           TOTAL
6    Posts Sent                 [formula]            [formula]            [formula]
7    Avg Sent                   [formula]            [formula]            -
8    Impressions                [formula]            [formula]            [formula]
9    Avg Unique Opens           [formula]            [formula]            -
10   Avg Open Rate              [formula]            [formula]            [formula]
11   Total Clicks               [formula]            [formula]            [formula]
12   Avg Unique Clicks          [formula]            [formula]            -
13   Avg Click Rate             [formula]            [formula]            [formula]
14   Unsubscribes               [formula]            [formula]            [formula]
```

#### Formulas for Summary Table:

**ETL Column (B):**
```
B6:  =COUNTIF(Raw_Data_Weekly!A:A,"ETL Daily")
B7:  =ROUND(AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!E:E),0)
B8:  =SUMIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!N:N)
B9:  =ROUND(AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!G:G),0)
B10: =TEXT(AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!H:H),"0.00") & "%"
B11: =SUMIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!I:I)
B12: =ROUND(AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!J:J),0)
B13: =TEXT(AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!K:K),"0.00") & "%"
B14: =SUMIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!L:L)
```

**EP Column (C):**
```
C6:  =COUNTIF(Raw_Data_Weekly!A:A,"EP Daily")
C7:  =ROUND(AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!E:E),0)
C8:  =SUMIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!N:N)
C9:  =ROUND(AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!G:G),0)
C10: =TEXT(AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!H:H),"0.00") & "%"
C11: =SUMIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!I:I)
C12: =ROUND(AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!J:J),0)
C13: =TEXT(AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!K:K),"0.00") & "%"
C14: =SUMIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!L:L)
```

**Total Column (D):**
```
D6:  =B6+C6
D8:  =B8+C8
D10: =TEXT((AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!H:H)+AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!H:H))/2,"0.00") & "%"
D11: =B11+C11
D13: =TEXT((AVERAGEIF(Raw_Data_Weekly!A:A,"ETL Daily",Raw_Data_Weekly!K:K)+AVERAGEIF(Raw_Data_Weekly!A:A,"EP Daily",Raw_Data_Weekly!K:K))/2,"0.00") & "%"
D14: =B14+C14
```

---

**Row 17-27: Top Posts ETL**
```
A17: TOP PERFORMING POSTS - El Tiempo Latino Daily
A18: Rank    B18: Post    C18: Date    D18: Open Rate    E18: Impressions    F18: Clicks
```

Use this formula in A19 (and drag down for rows 19-21):
```
A19: 1
B19: =INDEX(FILTER(Raw_Data_Weekly!C:C,Raw_Data_Weekly!A:A="ETL Daily"),MATCH(LARGE(FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),A19),FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),0))
C19: =INDEX(FILTER(Raw_Data_Weekly!D:D,Raw_Data_Weekly!A:A="ETL Daily"),MATCH(LARGE(FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),A19),FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),0))
D19: =TEXT(LARGE(FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),A19),"0.00") & "%"
E19: =INDEX(FILTER(Raw_Data_Weekly!N:N,Raw_Data_Weekly!A:A="ETL Daily"),MATCH(LARGE(FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),A19),FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),0))
F19: =INDEX(FILTER(Raw_Data_Weekly!I:I,Raw_Data_Weekly!A:A="ETL Daily"),MATCH(LARGE(FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),A19),FILTER(Raw_Data_Weekly!H:H,Raw_Data_Weekly!A:A="ETL Daily"),0))
```

---

**Row 24-30: Top Posts EP**
Same structure, replace "ETL Daily" with "EP Daily"

---

**Row 32-42: Top Clicked Links**
```
A32: TOP CLICKED LINKS - El Tiempo Latino Daily
A33: Rank    B33: Link Description    C33: Source Post    D33: Clicks

A34: 1
B34: =INDEX(FILTER(Raw_Data_Clicks!D:D,Raw_Data_Clicks!A:A="ETL Daily"),MATCH(LARGE(FILTER(Raw_Data_Clicks!E:E,Raw_Data_Clicks!A:A="ETL Daily"),A34),FILTER(Raw_Data_Clicks!E:E,Raw_Data_Clicks!A:A="ETL Daily"),0))
C34: =INDEX(FILTER(Raw_Data_Clicks!B:B,Raw_Data_Clicks!A:A="ETL Daily"),MATCH(LARGE(FILTER(Raw_Data_Clicks!E:E,Raw_Data_Clicks!A:A="ETL Daily"),A34),FILTER(Raw_Data_Clicks!E:E,Raw_Data_Clicks!A:A="ETL Daily"),0))
D34: =LARGE(FILTER(Raw_Data_Clicks!E:E,Raw_Data_Clicks!A:A="ETL Daily"),A34)
```

---

### Tab 5: `Monthly_Report`
Similar structure to Weekly_Report but with month-over-month comparison.

#### Key Formulas for Monthly Comparison:

**Current Month (e.g., December 2025):**
```
=SUMIFS(Raw_Data_Monthly!N:N, Raw_Data_Monthly!A:A,"ETL Daily", Raw_Data_Monthly!E:E,"2025-12")
```

**Previous Month (e.g., November 2025):**
```
=SUMIFS(Raw_Data_Monthly!N:N, Raw_Data_Monthly!A:A,"ETL Daily", Raw_Data_Monthly!E:E,"2025-11")
```

**Percent Change:**
```
=TEXT((CurrentMonth-PreviousMonth)/PreviousMonth,"0.0%")
```

---

### Tab 6: `Config`
Store configuration values:

| A | B |
|---|---|
| Current Week Start | 2026-01-05 |
| Current Week End | 2026-01-11 |
| Current Month | 2025-12 |
| Previous Month | 2025-11 |
| ETL Publication ID | pub_88b8ccea-c311-4381-a49c-91848583ba9e |
| EP Publication ID | pub_2dd3324c-fa75-40a2-acf2-df2acff63d10 |

---

## Formatting Recommendations

### Colors
- Header row: #1a73e8 (blue) with white text
- ETL column: #e8f0fe (light blue)
- EP column: #fce8e6 (light red)
- Positive changes: #34a853 (green)
- Negative changes: #ea4335 (red)
- Warning indicators: #fbbc04 (yellow)

### Conditional Formatting Rules

**For Open Rate cells:**
- Green if >= 45%
- Yellow if 40-45%
- Red if < 40%

**For Change columns:**
- Green if positive
- Red if negative

---

## Quick Import Instructions

1. Create a new Google Sheet
2. Create tabs: `Raw_Data_Weekly`, `Raw_Data_Clicks`, `Raw_Data_Monthly`, `Weekly_Report`, `Monthly_Report`, `Config`
3. In each Raw_Data tab: File > Import > Upload the corresponding CSV
4. Copy the formulas from this guide into the report tabs
5. Apply formatting

---

## Next Steps

The Python automation script will:
1. Pull data from Beehiiv API
2. Generate the CSV files
3. Use Google Sheets API to update the Raw_Data tabs
4. The report tabs will auto-calculate using the formulas
