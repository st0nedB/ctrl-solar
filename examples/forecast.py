from ctrlsolar.panels import OpenMeteoForecast, Panel


def main() -> None:
    forecast = OpenMeteoForecast(
        latitude=47.833301,
        longitude=12.977702,
        timezone="Europe/Berlin",
    )

    panels = [
        Panel(
            forecast=forecast,
            tilt=67.5,
            azimuth=90,
            area=1.762 * 1.134,
            efficiency=0.22,
        ),
        Panel(
            forecast=forecast,
            tilt=67.5,
            azimuth=90,
            area=1.762 * 1.134,
            efficiency=0.22,
        ),
        Panel(
            forecast=forecast,
            tilt=67.5,
            azimuth=90,
            area=1.762 * 1.134,
            efficiency=0.22,
        ),
        Panel(
            forecast=forecast,
            tilt=67.5,
            azimuth=180,
            area=1.762 * 1.134,
            efficiency=0.22,
        ),
    ]

    total_power = sum(
        float(panel.predicted_production_by_hour.values.sum()) for panel in panels
    )
    print(f"Estimated daily production: {1e-3 * total_power:.2f} kWh")


if __name__ == "__main__":
    main()
