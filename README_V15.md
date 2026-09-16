# V15 — Paper Trading + Order Management

Adds the first execution architecture while deliberately keeping live brokerage disabled.

New workspaces:
- Trade Centre: paper order ticket, preview and explicit confirmation.
- Orders: order audit trail and cancellation of open simulated orders.
- Paper Portfolio: simulated cash, positions, mark-to-market and P&L.
- Broker Connections: adapter architecture and production gates.

Design:
Research/technical signals do not directly execute orders. They feed a future order-proposal layer, followed by risk/validation, explicit user confirmation, OMS, and then broker adapters.

Simulator:
- Starts with $100,000 paper cash.
- Market paper orders fill at the latest loaded close.
- Limit/Stop/Stop Limit orders are stored OPEN in V15; automated trigger processing is a later milestone.
- Short selling is disabled.
- Local SQLite storage is suitable for prototype sessions, not durable production persistence on ephemeral cloud hosting.

No live broker credentials, APIs or real-money execution are included in V15.
