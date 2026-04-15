from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import time
import logging
from datetime import datetime
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Weather App", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"],
    registry=registry,
)
WEATHER_FETCH_COUNT = Counter(
    "weather_fetches_total",
    "Total weather API calls",
    ["city", "status"],
    registry=registry,
)
APP_INFO = Gauge(
    "app_info",
    "Application metadata",
    ["version", "environment"],
    registry=registry,
)
APP_INFO.labels(version="1.0.0", environment=os.getenv("ENVIRONMENT", "production")).set(1)

API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
APP_START_TIME = time.time()
weather_history: list[dict] = []


def get_recommendation(description: str, temp: float) -> str:
    desc = description.lower()
    if "rain" in desc or "drizzle" in desc:
        return "Carry an umbrella today."
    if "snow" in desc:
        return "Wear warm layers and be cautious of slippery roads."
    if "clear" in desc and temp > 30:
        return "Wear sunglasses and apply sunscreen."
    if "cloud" in desc:
        return "It might be a gloomy day, but a good time for outdoor walks."
    if temp < 15:
        return "Its chilly - layer up!"
    return "Looks like a good day. Enjoy!"


@app.get("/health")
def health():
    REQUEST_COUNT.labels(method="GET", endpoint="/health", status_code=200).inc()
    return {"status": "ok", "uptime_seconds": round(time.time() - APP_START_TIME, 1)}


@app.get("/ready")
def ready():
    if not API_KEY:
        raise HTTPException(status_code=503, detail="API key not configured")
    REQUEST_COUNT.labels(method="GET", endpoint="/ready", status_code=200).inc()
    return {"status": "ready"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return PlainTextResponse(
        generate_latest(registry), media_type=CONTENT_TYPE_LATEST
    )


@app.get("/weather/{city}")
async def get_weather(city: str):
    start = time.time()
    if not API_KEY:
        raise HTTPException(status_code=500, detail="OPENWEATHER_API_KEY not set")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                BASE_URL,
                params={"q": city, "appid": API_KEY, "units": "metric"},
            )
        if resp.status_code == 404:
            WEATHER_FETCH_COUNT.labels(city=city, status="not_found").inc()
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        if resp.status_code != 200:
            WEATHER_FETCH_COUNT.labels(city=city, status="api_error").inc()
            raise HTTPException(status_code=502, detail="Weather API error")

        data = resp.json()
        temp        = data["main"]["temp"]
        humidity    = data["main"]["humidity"]
        wind_speed  = data["wind"]["speed"]
        description = data["weather"][0]["description"]
        recommendation = get_recommendation(description, temp)

        record = {
            "city": city,
            "temperature": round(temp, 2),
            "humidity": humidity,
            "wind_speed": round(wind_speed, 2),
            "weather_description": description,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat(),
        }
        weather_history.append(record)
        if len(weather_history) > 100:
            weather_history.pop(0)

        WEATHER_FETCH_COUNT.labels(city=city, status="success").inc()
        logger.info(f"Weather fetched for {city}: {temp}C, {description}")
        return record

    except HTTPException:
        raise
    except Exception as e:
        WEATHER_FETCH_COUNT.labels(city=city, status="error").inc()
        logger.error(f"Error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        REQUEST_LATENCY.labels(endpoint="/weather").observe(time.time() - start)
        REQUEST_COUNT.labels(method="GET", endpoint="/weather", status_code=200).inc()


@app.get("/history")
def get_history():
    REQUEST_COUNT.labels(method="GET", endpoint="/history", status_code=200).inc()
    return {"count": len(weather_history), "records": weather_history[-20:]}


@app.get("/", response_class=HTMLResponse)
def index():
    REQUEST_COUNT.labels(method="GET", endpoint="/", status_code=200).inc()
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Weather App</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
    }
    .card {
      background: white; border-radius: 20px; padding: 40px;
      width: 420px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    h1 { text-align: center; margin-bottom: 24px; color: #333; font-size: 24px; }
    input {
      width: 100%; padding: 12px 16px; border: 2px solid #e2e8f0;
      border-radius: 10px; font-size: 16px; margin-bottom: 12px; outline: none;
    }
    input:focus { border-color: #667eea; }
    button {
      width: 100%; padding: 12px; background: #667eea; color: white;
      border: none; border-radius: 10px; font-size: 16px; cursor: pointer;
    }
    button:hover { background: #5a67d8; }
    #result { margin-top: 24px; }
    .weather-box {
      background: #f7fafc; border-radius: 12px; padding: 20px; margin-top: 12px;
    }
    .city-name { font-size: 20px; font-weight: 700; color: #2d3748; margin-bottom: 12px; }
    .row { display: flex; justify-content: space-between; margin: 6px 0; }
    .label { color: #718096; font-size: 14px; }
    .value { font-weight: 600; color: #2d3748; }
    .recommendation {
      margin-top: 16px; padding: 12px; background: #ebf4ff;
      border-radius: 8px; font-size: 14px; color: #2b6cb0;
    }
    .error { color: #e53e3e; margin-top: 12px; font-size: 14px; }
  </style>
</head>
<body>
<div class="card">
  <h1>Weather App</h1>
  <input id="city" type="text" placeholder="Enter city name (e.g. Chennai)" />
  <button onclick="getWeather()">Get Weather</button>
  <div id="result"></div>
</div>
<script>
async function getWeather() {
  const city = document.getElementById("city").value.trim();
  if (!city) return;
  const res = document.getElementById("result");
  res.innerHTML = "<p style=color:#718096;margin-top:12px>Loading...</p>";
  try {
    const r = await fetch("/weather/" + encodeURIComponent(city));
    if (!r.ok) {
      const err = await r.json();
      res.innerHTML = "<p class=error>Error: " + (err.detail || "Unknown error") + "</p>";
      return;
    }
    const d = await r.json();
    res.innerHTML =
      "<div class=weather-box>" +
      "<div class=city-name> " + d.city + "</div>" +
      "<div class=row><span class=label>Temperature</span><span class=value>" + d.temperature + "&deg;C</span></div>" +
      "<div class=row><span class=label>Humidity</span><span class=value>" + d.humidity + "%</span></div>" +
      "<div class=row><span class=label>Wind Speed</span><span class=value>" + d.wind_speed + " m/s</span></div>" +
      "<div class=row><span class=label>Condition</span><span class=value>" + d.weather_description + "</span></div>" +
      "<div class=recommendation>" + d.recommendation + "</div>" +
      "</div>";
  } catch(e) {
    res.innerHTML = "<p class=error>Network error. Try again.</p>";
  }
}
document.getElementById("city").addEventListener("keypress", function(e) {
  if (e.key === "Enter") getWeather();
});
</script>
</body>
</html>
""")
