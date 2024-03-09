# TickerTracker

## Code Structure

This code will follow a basic ETL pipeline.

1. The database is queried to figure out what data we need.
2. Data is extracted from the api.
   * If api or extraction error occurs, exception tracker for the data will be increased and the data will be added to the queue.
3. Extracted data is transformed.
    * If data is malformed an exception will be raised that will backpropagate to the extractor.
4. Data is then loaded into the database.

## Data Flow

The flow is as follows:

1. All tickers along with ticker fundamentals are loaded from CSI.
2. Ticker performanceIds are acquired.
3. Ticker securityIds are acquired.

## Data Requirements

| Data Name | Acquisition Location | Required By |
| -------- | ------- | ---- |
| symbol | CSI | Client |
| long_name | CSI | Client |
| exchange | CSI | Code |
| is_active | CSI | Code |
| start_date | CSI | Code |
| end_date | CSI | Code |
| sub_exchange | CSI | Code |
| percent_yield | Get-Quote | Client |
| return_ytd | Trailing | Client |
| return_1m | Trailing | Client |
| return_1y | Trailing | Client |
| return_3y | Trailing | Client |
| return_5y | Trailing | Client |
| return_10y | Trailing | Client |
| return_15y | Trailing | Client 2 |
| category | Trailing | Client |
| fee | Other-Fees | Client |
| number_negative_returns | Get-Returns | Client |
| morningstar_rating | Trailing | Client |
| performance_id | Auto-Complete | Get-Returns |
| security_id | Get-Returns | Trailing, Get-Quote, Other-Fees, Get-Returns |
