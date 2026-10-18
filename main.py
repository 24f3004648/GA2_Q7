import hmac
from collections import defaultdict

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

API_KEY = "ak_san8tlpy3pnjyq1qkadtwcwl"
EMAIL = "24f3004648@ds.study.iitm.ac.in"

app = FastAPI()

# Browser checks come from the exam page, so allow any origin. Auth is by API
# key (not cookies), so a wildcard is safe here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
    allow_credentials=False,
)


def aggregate(events):
    users = set()
    positive_by_user = defaultdict(float)
    revenue = 0.0
    for ev in events:
        user = ev.get("user")
        users.add(user)
        try:
            amount = float(ev.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
        if amount > 0:
            revenue += amount
            positive_by_user[user] += amount
    top_user = max(positive_by_user, key=positive_by_user.get) if positive_by_user else None
    return {
        "email": EMAIL,
        "total_events": len(events),
        "unique_users": len(users),
        "revenue": round(revenue, 6),
        "top_user": top_user,
    }


@app.post("/analytics")
async def analytics(request: Request, x_api_key: str = Header(default=None)):
    if x_api_key is None or not hmac.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON body")
    events = body.get("events") if isinstance(body, dict) else None
    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="events must be a list")
    events = [e for e in events if isinstance(e, dict)]
    return aggregate(events)


@app.get("/")
def root():
    return {"status": "ok"}
