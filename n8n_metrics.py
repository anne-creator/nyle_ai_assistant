"""
n8n Code Node - Metrics Analyzer
CRITICAL: n8n requires return [{"json": {...}}] format, NOT plain strings!
"""
import requests

# Config
BASE_URL = "https://api0.dev.nyle.ai/math/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2MTgwNDQ4LCJpYXQiOjE3NjYxNzY4NDgsImp0aSI6ImI4ZWRhYTAzMjQ2YzRiMDA5NWIzZGZmNzQzMjEzNjBhIiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwic2NvcGVzIjoiIiwiYXVkIjpbImFwaSJdLCJpc3MiOiJueWxlLmFpIn0.ejrZH91O6w9KxLCSAZEzB13N7cRkx-NWeHNW7QtaTt8"

ENDPOINTS = {
    "sales": "/math/total/sales",
    "tacos": "/math/total/tacos",
    "acos": "/math/ads/acos",
    "profit": "/math/cfo/net-profit"
}

def fetch(metric, d1, d2, asin=None):
    """Fetch single metric"""
    params = {"timespan": "day", "date_start": d1, "date_end": d2}
    if asin: params["asin"] = asin
    r = requests.get(f"{BASE_URL}{ENDPOINTS[metric]}", params=params, 
                     headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
    return r.json() if r.ok else {"error": r.status_code}

def run(d1, d2, asin=None):
    """
    Main function for n8n
    
    TOKEN EFFICIENCY NOTES:
    - Removed decorative lines (====, ----) = saves ~200 tokens
    - Removed bullet points (•) = saves ~50 tokens  
    - Shortened keys (total_sales→s, net_profit→p) = saves ~30% tokens
    - Compact single-line format = saves ~100 tokens
    - No redundant labels/headers = saves ~150 tokens
    
    Total savings: ~40-50% fewer tokens for same data!
    """
    # Fetch all metrics
    data = {m: fetch(m, d1, d2, asin) for m in ENDPOINTS}
    
    sales = data["sales"].get("data", [])
    if not sales:
        # n8n format: must be list of dicts with "json" key
        return [{"json": {"error": "No data", "period": f"{d1} to {d2}"}}]
    
    # Build compact daily records
    # Short keys: d=date, s=sales, p=profit, t=tacos, a=acos, f=forecast
    days = []
    for i, s in enumerate(sales):
        days.append({
            "d": s.get("period_start", "")[:10],  # date only, no time
            "s": round(s.get("value", 0), 0),      # sales (rounded to int saves tokens)
            "p": round(data["profit"].get("data", [{}])[i].get("value", 0) if i < len(data["profit"].get("data", [])) else 0, 0),
            "t": round(data["tacos"].get("data", [{}])[i].get("value", 0) * 100 if i < len(data["tacos"].get("data", [])) else 0, 1),  # as %
            "a": round(data["acos"].get("data", [{}])[i].get("value", 0) * 100 if i < len(data["acos"].get("data", [])) else 0, 1),   # as %
            "f": 1 if s.get("is_forecast") else 0  # 1/0 instead of true/false
        })
    
    # Compact summary stats
    sv = [d["s"] for d in days]
    pv = [d["p"] for d in days]
    tv = [d["t"] for d in days]
    av = [d["a"] for d in days]
    
    # Compact text format for LLM (token-efficient)
    # Format: date|sales|profit|tacos%|acos%
    lines = [f"{d['d']}|${int(d['s']):,}|${int(d['p']):,}|{d['t']}%|{d['a']}%" for d in days]
    
    # n8n REQUIRES this exact format
    return [{"json": {
        "period": f"{d1} to {d2}",
        "days": len(days),
        "data": days,
        "stats": {
            "sales": {"sum": sum(sv), "avg": sum(sv)//len(sv), "max": max(sv), "min": min(sv)},
            "profit": {"sum": sum(pv), "avg": sum(pv)//len(pv)},
            "tacos_avg": round(sum(tv)/len(tv), 1),
            "acos_avg": round(sum(av)/len(av), 1)
        },
        # Compact text for LLM prompt (one line per day)
        "text": f"Metrics {d1} to {d2} ({len(days)} days):\n" + "\n".join(lines)
    }}]


# ============================================================================
# For CLI testing (not used in n8n)
# ============================================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python n8n_metrics.py <date_start> <date_end> [asin]")
        sys.exit(1)
    
    result = run(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    
    import json
    print(json.dumps(result, indent=2))


