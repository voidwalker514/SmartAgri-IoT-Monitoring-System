"""
========================================================
Interactive Web Dashboard — Plotly Dash
========================================================
Launches a real-time IoT monitoring dashboard at:
  http://127.0.0.1:8050

Features:
  - Live-updating sensor gauges
  - Real-time sensor trend charts
  - Pump status indicator
  - Alert panel
  - Scenario selector for simulation
  - Dark theme with modern UI

Run with:
  python dashboard/app.py
  or
  python main.py --dashboard
========================================================
"""

import os
import sys
import json
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from python_simulation.sensor_simulator import SensorSimulator
from python_simulation.alert_engine     import AlertEngine
from python_simulation.pump_controller  import PumpController

# ── Global state (shared across callbacks) ───────────────────────────────────
simulator   = SensorSimulator()
alert_engine = AlertEngine()
pump_ctrl   = PumpController()

# Circular buffer: last 60 readings
MAX_READINGS = 60
readings_buffer: list = []

# ── App setup ─────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap",
    ],
    title="🌱 Smart Agriculture IoT Dashboard",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "IoT Smart Agriculture Monitoring Dashboard — real-time sensor data, alerts, and irrigation control"},
    ],
)

# ── Color palette ─────────────────────────────────────────────────────────────
COLORS = {
    "bg":        "#0D1117",
    "card":      "#161B22",
    "border":    "#30363D",
    "green":     "#39D353",
    "yellow":    "#FFA657",
    "red":       "#F85149",
    "blue":      "#58A6FF",
    "cyan":      "#39C5CF",
    "purple":    "#BC8CFF",
    "text":      "#E6EDF3",
    "subtext":   "#8B949E",
}

SENSOR_COLORS = {
    "soil_moisture":   COLORS["green"],
    "temperature":     COLORS["red"],
    "humidity":        COLORS["blue"],
    "light_intensity": COLORS["yellow"],
    "water_level":     COLORS["cyan"],
}

# ── Helper functions ──────────────────────────────────────────────────────────

def make_gauge(value: float, title: str, unit: str,
               lo: float, hi: float, color: str,
               warn_lo: float = None, warn_hi: float = None) -> go.Figure:
    """Create a Plotly gauge chart."""
    steps = []
    if warn_lo is not None:
        steps.append({"range": [lo, warn_lo], "color": "rgba(248,81,73,0.2)"})
    if warn_hi is not None:
        steps.append({"range": [warn_hi, hi], "color": "rgba(255,166,87,0.2)"})

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": unit, "font": {"size": 22, "color": color, "family": "Outfit"}},
        title={"text": title, "font": {"size": 14, "color": COLORS["text"], "family": "Outfit"}},
        gauge={
            "axis": {
                "range": [lo, hi],
                "tickcolor": COLORS["subtext"],
                "tickfont": {"size": 10, "color": COLORS["subtext"]},
            },
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": COLORS["card"],
            "borderwidth": 1,
            "bordercolor": COLORS["border"],
            "steps": steps,
            "threshold": {
                "line": {"color": COLORS["red"], "width": 2},
                "thickness": 0.7,
                "value": warn_hi or hi * 0.9,
            },
        },
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor=COLORS["card"],
        font_color=COLORS["text"],
    )
    return fig


def make_trend_chart(readings: list, sensor: str, color: str, unit: str) -> go.Figure:
    """Create a trend line chart for a sensor."""
    if not readings:
        return go.Figure()

    x  = [r.get("reading_id", i) for i, r in enumerate(readings)]
    y  = [r.get(sensor, 0) for r in readings]
    ts = [r.get("timestamp", "") for r in readings]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        line=dict(color=color, width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
        hovertemplate=f"<b>{sensor.replace('_',' ').title()}</b><br>Value: %{{y:.1f}}{unit}<br>Time: %{{text}}<extra></extra>",
        text=ts,
        name=sensor.replace("_", " ").title(),
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=30, r=10, t=10, b=30),
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["bg"],
        font_color=COLORS["text"],
        showlegend=False,
        xaxis=dict(
            showgrid=True, gridcolor="#21262D", gridwidth=1,
            zeroline=False, tickcolor=COLORS["subtext"],
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#21262D", gridwidth=1,
            zeroline=False, tickcolor=COLORS["subtext"],
        ),
    )
    return fig


# ── Layout ────────────────────────────────────────────────────────────────────

CARD_STYLE = {
    "backgroundColor": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "10px",
    "padding": "16px",
    "marginBottom": "16px",
}

def status_badge(text: str, color: str):
    return html.Span(
        text,
        style={
            "backgroundColor": color,
            "color": "white",
            "padding": "4px 12px",
            "borderRadius": "20px",
            "fontSize": "12px",
            "fontWeight": "600",
            "letterSpacing": "0.5px",
        }
    )


app.layout = html.Div(
    style={
        "backgroundColor": COLORS["bg"],
        "minHeight": "100vh",
        "fontFamily": "'Outfit', sans-serif",
        "color": COLORS["text"],
        "padding": "24px",
    },
    children=[
        # ── Header ─────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H1(
                    "🌱 Smart Agriculture IoT Monitor",
                    style={"margin": "0", "fontSize": "26px", "fontWeight": "700",
                           "background": f"linear-gradient(135deg, {COLORS['green']}, {COLORS['cyan']})",
                           "WebkitBackgroundClip": "text", "WebkitTextFillColor": "transparent"},
                ),
                html.P("Real-time sensor monitoring, alert detection & irrigation control",
                       style={"margin": "4px 0 0 0", "color": COLORS["subtext"], "fontSize": "13px"}),
            ]),
            html.Div([
                html.Span("⏱ ", style={"color": COLORS["subtext"]}),
                html.Span(id="clock-display",
                          style={"color": COLORS["text"], "fontWeight": "600", "fontSize": "14px"}),
                html.Span(" | Scenario: ", style={"color": COLORS["subtext"], "marginLeft": "16px"}),
                dcc.Dropdown(
                    id="scenario-selector",
                    options=[
                        {"label": "🎲 Random",       "value": "random"},
                        {"label": "🌿 Normal Farm",   "value": "normal"},
                        {"label": "🏜️ Dry Soil",      "value": "dry_soil"},
                        {"label": "🌡️ High Temp",     "value": "high_temp"},
                        {"label": "💧 Low Water",     "value": "low_water"},
                        {"label": "🌙 Night Mode",    "value": "night"},
                        {"label": "🌧️ Rainy Season",  "value": "rainy"},
                    ],
                    value="random",
                    clearable=False,
                    style={"width": "180px", "fontSize": "13px",
                           "backgroundColor": COLORS["card"],
                           "color": COLORS["text"]},
                ),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center", "marginBottom": "20px",
            "padding": "16px 20px",
            "backgroundColor": COLORS["card"],
            "borderRadius": "12px",
            "border": f"1px solid {COLORS['border']}",
        }),

        # ── System Status Bar ───────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("System Status: ", style={"color": COLORS["subtext"]}),
                html.Span(id="system-status-badge"),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
            html.Div([
                html.Span("Pump: ", style={"color": COLORS["subtext"]}),
                html.Span(id="pump-status-badge"),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
            html.Div([
                html.Span("Readings: ", style={"color": COLORS["subtext"]}),
                html.Span(id="reading-count",
                          style={"color": COLORS["text"], "fontWeight": "600"}),
            ]),
            html.Div([
                html.Span("Alerts: ", style={"color": COLORS["subtext"]}),
                html.Span(id="alert-count",
                          style={"color": COLORS["red"], "fontWeight": "600"}),
            ]),
        ], style={
            "display": "flex", "gap": "32px", "alignItems": "center",
            "padding": "12px 20px",
            "backgroundColor": COLORS["card"],
            "borderRadius": "10px",
            "border": f"1px solid {COLORS['border']}",
            "marginBottom": "20px",
        }),

        # ── Gauge Row ───────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(dcc.Graph(id="gauge-moisture",  config={"displayModeBar": False}), md=2, sm=6),
            dbc.Col(dcc.Graph(id="gauge-temp",      config={"displayModeBar": False}), md=2, sm=6),
            dbc.Col(dcc.Graph(id="gauge-humidity",  config={"displayModeBar": False}), md=2, sm=6),
            dbc.Col(dcc.Graph(id="gauge-light",     config={"displayModeBar": False}), md=3, sm=6),
            dbc.Col(dcc.Graph(id="gauge-water",     config={"displayModeBar": False}), md=3, sm=6),
        ], className="mb-3"),

        # ── Trend Charts + Alert Panel ──────────────────────────────────
        dbc.Row([
            # Trend Charts (left)
            dbc.Col([
                html.Div([
                    html.H5("📈 Sensor Trends", style={"margin": "0 0 12px 0", "fontWeight": "600",
                                                        "color": COLORS["text"]}),
                    html.Div([
                        html.Div([
                            html.P("Soil Moisture %", style={"margin": "0 0 4px 0", "fontSize": "12px",
                                                              "color": COLORS["green"]}),
                            dcc.Graph(id="trend-moisture", config={"displayModeBar": False}),
                        ]),
                        html.Div([
                            html.P("Temperature °C", style={"margin": "8px 0 4px 0", "fontSize": "12px",
                                                             "color": COLORS["red"]}),
                            dcc.Graph(id="trend-temp",    config={"displayModeBar": False}),
                        ]),
                        html.Div([
                            html.P("Humidity %", style={"margin": "8px 0 4px 0", "fontSize": "12px",
                                                        "color": COLORS["blue"]}),
                            dcc.Graph(id="trend-humidity", config={"displayModeBar": False}),
                        ]),
                    ]),
                ], style=CARD_STYLE),
            ], md=8),

            # Alert Panel (right)
            dbc.Col([
                html.Div([
                    html.H5("🚨 Live Alerts", style={"margin": "0 0 12px 0", "fontWeight": "600",
                                                      "color": COLORS["text"]}),
                    html.Div(id="alert-panel",
                             style={"maxHeight": "480px", "overflowY": "auto"}),
                ], style=CARD_STYLE),
            ], md=4),
        ]),

        # ── Water & Light Trends ────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P("💧 Water Level %", style={"margin": "0 0 4px 0", "fontSize": "12px",
                                                       "color": COLORS["cyan"]}),
                    dcc.Graph(id="trend-water", config={"displayModeBar": False}),
                ], style=CARD_STYLE),
            ], md=6),
            dbc.Col([
                html.Div([
                    html.P("☀️ Light Intensity (lux)", style={"margin": "0 0 4px 0", "fontSize": "12px",
                                                               "color": COLORS["yellow"]}),
                    dcc.Graph(id="trend-light", config={"displayModeBar": False}),
                ], style=CARD_STYLE),
            ], md=6),
        ]),

        # ── Latest Reading Data Table ───────────────────────────────────
        html.Div([
            html.H5("📋 Latest Readings", style={"margin": "0 0 12px 0",
                                                   "fontWeight": "600", "color": COLORS["text"]}),
            html.Div(id="data-table"),
        ], style=CARD_STYLE),

        # ── Interval timer ──────────────────────────────────────────────
        dcc.Interval(id="interval-update", interval=2000, n_intervals=0),  # 2s refresh
        dcc.Store(id="readings-store", data=[]),
        dcc.Store(id="total-alerts-store", data=0),
    ],
)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("clock-display", "children"),
    Input("interval-update", "n_intervals"),
)
def update_clock(n):
    return datetime.now().strftime("%Y-%m-%d  %H:%M:%S")


@app.callback(
    Output("readings-store",      "data"),
    Output("total-alerts-store",  "data"),
    Output("gauge-moisture",      "figure"),
    Output("gauge-temp",          "figure"),
    Output("gauge-humidity",      "figure"),
    Output("gauge-light",         "figure"),
    Output("gauge-water",         "figure"),
    Output("trend-moisture",      "figure"),
    Output("trend-temp",          "figure"),
    Output("trend-humidity",      "figure"),
    Output("trend-water",         "figure"),
    Output("trend-light",         "figure"),
    Output("alert-panel",         "children"),
    Output("system-status-badge", "children"),
    Output("pump-status-badge",   "children"),
    Output("reading-count",       "children"),
    Output("alert-count",         "children"),
    Output("data-table",          "children"),
    Input("interval-update",  "n_intervals"),
    State("scenario-selector","value"),
    State("readings-store",   "data"),
    State("total-alerts-store","data"),
)
def update_dashboard(n_intervals, scenario, stored_readings, total_alerts):
    # Generate new reading
    reading = simulator.get_reading(scenario=scenario)
    alerts_list = alert_engine.check(reading)
    pump_on = pump_ctrl.decide(reading)
    reading["pump_status"] = "ON" if pump_on else "OFF"
    reading["alerts"] = alerts_list

    # Update circular buffer
    stored_readings.append(reading)
    if len(stored_readings) > MAX_READINGS:
        stored_readings = stored_readings[-MAX_READINGS:]

    total_alerts += len(alerts_list)

    # ── Values ─────────────────────────────────────────────────────
    sm  = reading["soil_moisture"]
    tp  = reading["temperature"]
    hm  = reading["humidity"]
    li  = reading["light_intensity"]
    wl  = reading["water_level"]

    # ── Gauges ─────────────────────────────────────────────────────
    g_moisture = make_gauge(sm,   "Soil Moisture",   "%",    0, 100,   COLORS["green"],  warn_lo=25, warn_hi=85)
    g_temp     = make_gauge(tp,   "Temperature",     "°C",   0, 60,    COLORS["red"],    warn_lo=10, warn_hi=38)
    g_humidity = make_gauge(hm,   "Humidity",        "%",    0, 100,   COLORS["blue"],   warn_lo=30, warn_hi=90)
    g_light    = make_gauge(li,   "Light Intensity", " lux", 0, 100000,COLORS["yellow"], warn_lo=500,warn_hi=80000)
    g_water    = make_gauge(wl,   "Water Level",     "%",    0, 100,   COLORS["cyan"],   warn_lo=20, warn_hi=98)

    # ── Trend Charts ───────────────────────────────────────────────
    t_moisture = make_trend_chart(stored_readings, "soil_moisture",   COLORS["green"],  "%")
    t_temp     = make_trend_chart(stored_readings, "temperature",     COLORS["red"],    "°C")
    t_humidity = make_trend_chart(stored_readings, "humidity",        COLORS["blue"],   "%")
    t_water    = make_trend_chart(stored_readings, "water_level",     COLORS["cyan"],   "%")
    t_light    = make_trend_chart(stored_readings, "light_intensity", COLORS["yellow"], " lux")

    # ── Alert Panel ────────────────────────────────────────────────
    alert_items = []
    if alerts_list:
        for alert in reversed(alerts_list):
            is_critical = "CRITICAL" in alert
            bg = "rgba(248,81,73,0.15)" if is_critical else "rgba(255,166,87,0.12)"
            border = COLORS["red"] if is_critical else COLORS["yellow"]
            alert_items.append(html.Div(
                alert,
                style={
                    "padding": "10px 14px",
                    "marginBottom": "8px",
                    "borderRadius": "8px",
                    "backgroundColor": bg,
                    "borderLeft": f"3px solid {border}",
                    "fontSize": "12px",
                    "lineHeight": "1.5",
                    "color": COLORS["text"],
                },
            ))
    else:
        alert_items.append(html.Div(
            "✅ All sensors within safe range",
            style={"color": COLORS["green"], "fontSize": "13px",
                   "padding": "12px", "textAlign": "center"},
        ))

    # ── Status badges ──────────────────────────────────────────────
    system_status = alert_engine.get_system_status(reading)
    status_color  = {"CRITICAL": COLORS["red"], "WARNING": COLORS["yellow"], "OK": COLORS["green"]}
    sys_badge     = status_badge(system_status, status_color.get(system_status, COLORS["green"]))

    pump_color = COLORS["green"] if pump_on else COLORS["subtext"]
    pump_badge = status_badge("💧 ON — Irrigating" if pump_on else "🔴 OFF — Standby", pump_color)

    # ── Data table ─────────────────────────────────────────────────
    table_data = [
        {"Sensor": "🌱 Soil Moisture", "Value": f"{sm:.1f}%",         "Status": "OK" if 25 <= sm <= 85 else "⚠"},
        {"Sensor": "🌡️ Temperature",   "Value": f"{tp:.1f}°C",         "Status": "OK" if 10 <= tp <= 38 else "⚠"},
        {"Sensor": "💧 Humidity",       "Value": f"{hm:.1f}%",         "Status": "OK" if 30 <= hm <= 90 else "⚠"},
        {"Sensor": "☀️ Light",          "Value": f"{li:.0f} lux",      "Status": "OK" if 500 <= li <= 80000 else "⚠"},
        {"Sensor": "🪣 Water Level",    "Value": f"{wl:.1f}%",         "Status": "OK" if wl >= 20 else "⚠"},
        {"Sensor": "⚙️ Pump",           "Value": "ON" if pump_on else "OFF", "Status": "Running" if pump_on else "Standby"},
        {"Sensor": "📍 Scenario",       "Value": reading.get("scenario","—"),  "Status": "—"},
        {"Sensor": "🕐 Timestamp",      "Value": reading.get("timestamp","—"), "Status": "—"},
    ]

    rows = [
        html.Tr([
            html.Th("Sensor",  style={"padding": "8px 12px", "color": COLORS["subtext"]}),
            html.Th("Value",   style={"padding": "8px 12px", "color": COLORS["subtext"]}),
            html.Th("Status",  style={"padding": "8px 12px", "color": COLORS["subtext"]}),
        ], style={"borderBottom": f"1px solid {COLORS['border']}"}),
        *[
            html.Tr([
                html.Td(r["Sensor"], style={"padding": "8px 12px"}),
                html.Td(r["Value"],  style={"padding": "8px 12px", "fontWeight": "600",
                                             "color": COLORS["green"] if r["Status"] == "OK" else COLORS["yellow"] if "⚠" in r["Status"] else COLORS["text"]}),
                html.Td(r["Status"], style={"padding": "8px 12px", "fontSize": "12px",
                                             "color": COLORS["green"] if r["Status"] == "OK" else COLORS["red"] if "⚠" in r["Status"] else COLORS["subtext"]}),
            ]) for r in table_data
        ],
    ]

    table = html.Table(
        rows,
        style={"width": "100%", "borderCollapse": "collapse", "fontSize": "13px"},
    )

    return (
        stored_readings, total_alerts,
        g_moisture, g_temp, g_humidity, g_light, g_water,
        t_moisture, t_temp, t_humidity, t_water, t_light,
        alert_items, sys_badge, pump_badge,
        str(len(stored_readings)), str(total_alerts),
        table,
    )


def run_dashboard(debug: bool = False, port: int = 8050):
    """Launch the Dash dashboard server."""
    print(f"\n{'='*55}")
    print("  🌱 Smart Agriculture IoT Dashboard")
    print(f"{'='*55}")
    print(f"  Open browser at: http://127.0.0.1:{port}")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=debug, port=port, host="127.0.0.1")


if __name__ == "__main__":
    run_dashboard(debug=True)
