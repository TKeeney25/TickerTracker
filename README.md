# Documentation

## Code Structure

This code will follow a basic ETL pipeline.

1. The database is queried to figure out what data we need.
2. Data is extracted from the api.
   * If api or extraction error occurs, exception tracker for the data will be increased and the data will be added to the queue.
3. Extracted data is transformed.
    * If data is malformed an exception will be raised that will backpropagate to the extractor.
4. Data is then loaded into the database.
    * If data indicates that the fund is bad, then a flag will be raised. This flag is ignored in **FundFinder**.

## Data Requirements

| Data Name               | Acquisition Location  | Required By                                  |
| ----------------------- | --------------------- | -------------------------------------------- |
| symbol                  | CSI                   | FundFinder, TickerTracker                    |
| long_name               | CSI                   | FundFinder, TickerTracker                    |
| exchange                | CSI                   | Code                                         |
| is_active               | CSI                   | Code                                         |
| start_date              | CSI                   | Code                                         |
| end_date                | CSI                   | Code                                         |
| sub_exchange            | CSI                   | Code                                         |
| brokerages              | YH-Get-Summary        | TickerTracker                                |
| percent_yield           | YH-Get-Summary, Get-Quote             | TickerTracker                                |
| return_ytd              | YH-Get-Summary, Trailing              | FundFinder, TickerTracker                    |
| return_1m               | YH-Get-Summary, Trailing              | FundFinder, TickerTracker                    |
| return_1y               | YH-Get-Summary, Trailing              | FundFinder, TickerTracker                    |
| return_3y               | YH-Get-Summary, Trailing              | FundFinder, TickerTracker                    |
| return_5y               | YH-Get-Summary, Trailing              | FundFinder, TickerTracker                    |
| return_10y              | YH-Get-Summary, Trailing              | FundFinder, TickerTracker                    |
| return_15y              | Trailing              | FundFinder                                   |
| return_since_inception  | YH-Get-Summary, Trailing              | FundFinder                                   |
| category                | Get-Returns, Trailing | TickerTracker                                |
| fee                     | YH-Get-Summary, Other-Fees            | TickerTracker                                |
| number_negative_returns | YH-Get-Summary, Get-Returns           | TickerTracker                                |
| morningstar_rating      | Trailing              | FundFinder, TickerTracker                    |
| performance_id          | Auto-Complete         | Get-Security-ID                              |
| security_id             | Get-Security-ID       | Trailing, Get-Quote, Other-Fees, Get-Returns |

## Optimal Data Flow

### TickerTracker

1. CSI
2. Auto-Complete
3. Get-Security-ID
4. Trailing
5. Other-Fees
6. Get-Quote
7. Get-Returns

### FundFinder

1. CSI
2. Auto-Complete
3. Get-Security-ID
4. Trailing

## Notable Functions

### CSI

* Will be ran every time the program is ran. Running it takes very little time.

### Auto-Complete & Get-Security-ID

* Will only be ran for new funds or funds
