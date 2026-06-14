"""
========================================================
IoT Smart Agriculture Monitoring System
========================================================
Author      : IoT Agriculture Project
Version     : 1.0.0
Description : Main entry point — runs the full simulation
              pipeline: sensor data → threshold logic →
              alert generation → CSV logging → dashboard.

How to run:
  python main.py              # Full interactive simulation
  python main.py --demo       # Quick 10-reading demo
  python main.py --dashboard  # Launch web dashboard only
========================================================
"""

import argparse
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_banner():
    """Print the project banner."""
    banner = Text()
    banner.append("🌱  IoT-Enabled Smart Agriculture Monitoring System  🌱", style="bold green")
    console.print(Panel(banner, style="green", expand=False))
    console.print("[dim]Version 1.0.0 | Python Simulation Mode[/dim]\n")


def main():
    parser = argparse.ArgumentParser(
        description="IoT Smart Agriculture Monitoring System"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a quick 10-reading demo and exit",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the interactive web dashboard only",
    )
    parser.add_argument(
        "--readings",
        type=int,
        default=50,
        help="Number of sensor readings to simulate (default: 50)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between readings (default: 1.0)",
    )
    args = parser.parse_args()

    print_banner()

    if args.dashboard:
        # Launch only the dashboard
        console.print("[bold cyan]Launching interactive web dashboard...[/bold cyan]")
        from dashboard.app import run_dashboard
        run_dashboard()
        return

    if args.demo:
        # Quick demo mode
        console.print("[bold yellow]Running DEMO mode (10 readings)...[/bold yellow]\n")
        from python_simulation.sensor_simulator import SensorSimulator
        from python_simulation.alert_engine import AlertEngine
        from python_simulation.data_logger import DataLogger

        simulator = SensorSimulator()
        alert_engine = AlertEngine()
        logger = DataLogger()

        for i in range(10):
            reading = simulator.get_reading(scenario="random")
            alerts = alert_engine.check(reading)
            logger.log(reading, alerts)
            console.print(f"[green]Reading {i+1:02d}:[/green] {reading}")
            for alert in alerts:
                console.print(f"  [bold red]⚠ ALERT:[/bold red] {alert}")
            time.sleep(0.3)

        report_path = logger.save()
        console.print(f"\n[bold green]✓ Demo complete! Report saved to:[/bold green] {report_path}")
        return

    # ── Full Simulation Mode ─────────────────────────────────────────
    console.print(
        f"[bold cyan]Starting full simulation:[/bold cyan] "
        f"{args.readings} readings @ {args.interval}s interval\n"
    )

    from python_simulation.sensor_simulator import SensorSimulator
    from python_simulation.alert_engine import AlertEngine
    from python_simulation.data_logger import DataLogger
    from python_simulation.pump_controller import PumpController

    simulator = SensorSimulator()
    alert_engine = AlertEngine()
    logger = DataLogger()
    pump = PumpController()

    try:
        for i in range(args.readings):
            reading = simulator.get_reading(scenario="random")
            alerts = alert_engine.check(reading)
            pump_status = pump.decide(reading)
            logger.log(reading, alerts, pump_status)

            # Console output
            console.print(
                f"[green]#{i+1:03d}[/green] "
                f"Moisture:[cyan]{reading['soil_moisture']:5.1f}%[/cyan] "
                f"Temp:[yellow]{reading['temperature']:5.1f}°C[/yellow] "
                f"Humidity:[blue]{reading['humidity']:5.1f}%[/blue] "
                f"Light:[magenta]{reading['light_intensity']:6.1f}lux[/magenta] "
                f"Water:[white]{reading['water_level']:5.1f}%[/white] "
                f"Pump:[{'bold green' if pump_status else 'bold red'}]{'ON ' if pump_status else 'OFF'}[/{'bold green' if pump_status else 'bold red'}]"
            )
            for alert in alerts:
                console.print(f"  [bold red]⚠  {alert}[/bold red]")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Simulation stopped by user.[/yellow]")

    report_path = logger.save()
    console.print(f"\n[bold green]✓ Simulation complete! Data saved to:[/bold green] {report_path}")
    console.print("[dim]Run [bold]python main.py --dashboard[/bold] to view the dashboard.[/dim]")


if __name__ == "__main__":
    main()
