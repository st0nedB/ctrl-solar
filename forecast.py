from datetime import datetime, timedelta
from ctrlsolar.panels.panels import OpenMeteoForecast, SolarPanel 


date = (datetime.now().date() - timedelta(days=2)).strftime('%Y-%m-%d')
print(date)

forecast = OpenMeteoForecast(
    latitude=47.833301,
    longitude=12.977702,
    timezone="Europe/Berlin",
)
df = forecast.get_forecast(date)

panels = [
    SolarPanel(
        surface_tilt=67.5, 
        surface_azimuth=90,
        panel_area=1.762*1.134,
        panel_efficiency=0.22,
    ),
    SolarPanel(
        surface_tilt=67.5, 
        surface_azimuth=90,
        panel_area=1.762*1.134,
        panel_efficiency=0.22,
    ),
    SolarPanel(
        surface_tilt=67.5, 
        surface_azimuth=90,
        panel_area=1.762*1.134,
        panel_efficiency=0.22,
    ),
    SolarPanel(
        surface_tilt=67.5, 
        surface_azimuth=180,
        panel_area=1.762*1.134,
        panel_efficiency=0.22,
    ),
]
p_dc = [panel.predict_production(df) for panel in panels]
print(f"Total Power: {sum(p_dc):.2f}")