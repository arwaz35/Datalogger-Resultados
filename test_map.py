import sys
import os
import pandas as pd

sys.path.append(r"C:\Users\micha\OneDrive\Proyectos Incol\Datalogger\Programa Resultados")
from plotter import Plotter

df = pd.DataFrame({
    'Latitud': [4.7110, 4.7111, 4.7112],
    'Longitud': [-74.0721, -74.0722, -74.0723]
})

print("Testing simple route...")
res = Plotter.plot_gps_route_simple(df, title="Test", distance_m=100)
if res is None:
    print("Failed: Returned None")
else:
    print("Success: returning BytesIO")
    print(len(res.getvalue()))
