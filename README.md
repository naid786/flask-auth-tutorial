# Flask Auth + Binance Charting & Analytics

Authenticated Flask web app to fetch Binance symbols, persist ticker meta data, request OHLC candles, and render an interactive candlestick chart (Lightweight‑Charts) with custom technical tooling: swing highs/lows, Break of Structure (BOS), and price gaps. Includes user registration/login, SQLite + SQLAlchemy ORM, and Alembic migrations.

---

## ⭐ Features

- User auth (register / login / logout) via Flask-Login & hashed passwords
- Persisted ticker catalogue fetched live from Binance (`/fetch-tickers`)
- Modal workflow to pick symbol + date range presets (1D / 1W / 1M / Custom, current period helper)
- Historical OHLC retrieval from Binance (interval default 15m) with batched API pagination
- Interactive candlestick chart (Lightweight Charts custom web component `candlestick-chart`)
- On‑chart tools:
  - Swing High / Swing Low detection (config interval=2 in analytics code)
  - Break of Structure (BOS) visualization (first close beyond prior swing levels)
  - Gap detection (basic two–bar gap logic) with projected fill end
- REST JSON routes powering JS overlays (`/swings`, `/BOS`, `/getGap`)
- Simple responsive templates (Jinja2) & custom JS drawing helpers
- Alembic migrations + auto timestamps (`created_at`, `updated_at`)

---

## 🗃 Tech Stack

Backend: Flask, Flask-Login, Flask-WTF, Flask-Migrate, SQLAlchemy (SQLite default)  
Data: Requests, Pandas, NumPy  
Chart UI: Lightweight Charts (standalone bundle) + custom web component & helper scripts  
Migrations: Alembic (invoked via Flask-Migrate helpers in `main.py`)

---

## 📁 Key Structure

```text
flask-auth-tutorial/
  main.py                # App factory + routes + models
  dataSource/
   binanceData.py       # Symbol list + OHLC fetchers
  analatics/functions.py # (spelling) pivot, swing, BOS, gap, RSI helpers
  templates/             # Jinja2 templates (auth pages, tickers, chart)
  static/js/             # Chart component & indicator plotting logic
  migrations/            # Alembic migration scripts
  instance/database.db   # SQLite DB (created at runtime)
  requirements.txt
```

---

## ⚙️ Setup

1. Clone repository

  ```bash
  git clone <repo-url>
  cd flask-auth-tutorial
  ```

1. (Recommended) create virtual environment

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  ```

1. Install dependencies

  ```bash
  pip install -r requirements.txt
  ```

1. (Optional) Create a `.env` (Not auto-loaded yet) – you can instead edit `main.py`:

  ```env
  SECRET_KEY=change_me
  SQLALCHEMY_DATABASE_URI=sqlite:///database.db
  ```

1. Initialize database (first time):

  ```bash
  python main.py migrate "initial"
  python main.py upgrade
  ```

  (Or just run once; `db.create_all()` will create tables if missing, but migrations keep schema history.)

1. Run server (debug):

  ```bash
  python main.py
  ```

  Visit: <http://127.0.0.1:5000/>

---

## 🔐 Authentication Flow

- Register (`/register`) -> username uniqueness enforced -> password hashed (Werkzeug)
- Login (`/login`) -> session managed by Flask-Login; protected routes require `@login_required`
- Logout (`/logout`)

---

## 🔄 Data Workflow

1. User logs in
1. Trigger Fetch Symbols: GET `/fetch-tickers` (async wrapper) → stores each trading symbol into `TickerData`
1. Browse Saved: `/saved-tickers` groups symbols by exchange (currently only "Binance")
1. Double‑click a row → modal form → choose period / custom dates
1. Redirect to `/chart?symbol=...&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`
1. Server fetches OHLC candles (batched klines) and returns JSON embedded in the chart component
1. User activates overlays (Swing / BOS / Gap) → component posts structured candle data to backend analytics endpoints

---

## 🔍 Analytics Logic (in `analatics/functions.py`)

- Pivots: Sliding window (interval=2) tests center bar vs neighbors to label swing highs/lows
- BOS: For each swing, finds first candle close beyond the swing extreme (structure break) and draws a horizontal segment between pivot time and break time
- Gaps: Simple detection between prior and next bar extremes (direction aware) + search for fill (price crossing pre-gap reference)
- RSI: Included helper (`calculate_rsi`) not yet wired into UI

To modify sensitivity, adjust `interval` in calls to `getPivots` / `getSwingBreaks`.

---

## 📡 Key Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/` / `/home` | GET | Home dashboard (auth required) |
| `/register` | GET/POST | Create user |
| `/login` | GET/POST | Authenticate user |
| `/logout` | GET | End session |
| `/fetch-tickers` | GET | Pull & store Binance symbols |
| `/saved-tickers` | GET | List stored tickers grouped by exchange |
| `/tickDataForm` | POST | Returns modal form fragment (HTML) |
| `/chart` | GET | Render chart for date range |
| `/swings` | POST | JSON: swing high/low markers |
| `/BOS` | POST | JSON: break of structure lines |
| `/getGap` | POST | JSON: gaps + projected end |

Payloads for POST analytics endpoints expect JSON body:

```json
{ "data": [ {"time": "2025-07-01T00:00:00Z", "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0} ] }
```

Returned structures map directly to plotting helpers in `static/js/candlestick-chart.js`.

---

## 🖥 Chart Interactions (Toolbar Buttons)

- Line: (Placeholder) toggles drawing mode for trendlines
- Swings: Fetch + plot arrows (high = arrowDown above candle, low = arrowUp below)
- BOS: Horizontal lines spanning pivot to first break close (different styling by direction)
- Gap: Highlight gap zones (fill endpoint determined server-side)
- Clear: Clears overlays (handled in custom component)

---

## 🛠 Development Notes

- Spelling: folder `analatics/` (not `analytics/`) – keep consistency or refactor with migration + import changes.
- Consider extracting app factory pattern for testing (currently module-level globals).
- Secret key is hard-coded; move to environment variable for production.
- Add rate limiting if exposing publicly (Binance API + login brute force protection).

---

## 🧪 Testing (Suggested)

Add pytest + factory pattern:

```bash
pip install pytest pytest-flask
```

Example skeleton:

```python
# tests/test_auth.py
from main import app, db, User

def test_register(client):
   resp = client.post('/register', data={"username":"u1","password":"p","password2":"p"}, follow_redirects=True)
   assert resp.status_code == 200
```

---

## 🚀 Extending

| Goal | Hint |
|------|------|
| Add RSI overlay | Compute server side or in JS; extend `/swings` style endpoint |
| Additional intervals | Expose interval select; forward to `fetch_binance_ohlc` |
| Cache OHLC | Store candles by (symbol, interval, date span) in DB or on-disk parquet |
| WebSockets | Stream live klines and update chart incrementally |
| User prefs | New table for default interval / theme |

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty chart | Verify date range & symbol exists; check console for fetch errors |
| Migration mismatch | Delete `instance/database.db` (dev only) then `python main.py upgrade` |
| Import error `analatics` | Ensure path correct or rename folder & update imports |
| Timezone shifts | Binance times are UTC ms; ensure client interprets consistently |

---

## 🔐 Security Considerations

- Do NOT reuse the bundled secret key; replace for any deployed instance
- Enforce HTTPS + secure cookies in production
- Add CSRF protection (Flask-WTF provides token generation; ensure templates include `{{ form.csrf_token }}`)
- Rate limit auth endpoints (e.g., `flask-limiter`)

---

## 📜 License

Add a LICENSE file (MIT recommended). Update this section accordingly.

---

## ✅ Roadmap (Short)

- [ ] Move config to separate `config.py` / environment variables
- [ ] Add pytest suite & CI
- [ ] Parameterize indicator interval from UI
- [ ] Add RSI & Moving Averages overlays
- [ ] Dark mode toggle & persisted user preference
- [ ] Dockerfile / Compose for reproducible deploy

---

## 🙌 Contributing

1. Fork & branch (`feat/your-feature`)
1. Add/update tests
1. Submit PR with concise summary & screenshots if UI changes

---

## 📣 Acknowledgements

- Binance public REST API
- TradingView Lightweight Charts
- Flask ecosystem maintainers

Happy building!
