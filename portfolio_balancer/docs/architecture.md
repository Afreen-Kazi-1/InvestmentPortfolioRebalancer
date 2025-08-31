# Architecture

## Market Data Service

The market data service is responsible for fetching and caching market data from external providers.

### Components

- **Scheduler**: A scheduled job that runs daily to refresh the market data.
- **Price Service**: A service that fetches data from `yfinance` for stocks/ETFs and CoinGecko for cryptocurrencies.
- **Database**: A database to store the historical price data and the latest prices.

### Diagram

```mermaid
graph TD
    subgraph "User"
        A[User Portfolio]
    end

    subgraph "Application"
        B[API]
        C[Scheduler]
        D[Price Service]
        E[Database]
    end

    subgraph "External Providers"
        F[yfinance]
        G[CoinGecko]
    end

    A --> B
    C --> D
    D --> F
    D --> G
    D --> E
    B --> E