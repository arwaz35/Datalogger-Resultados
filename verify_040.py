import sys
import pandas as pd
import os

# Add project path
project_path = r'c:\Users\micha\OneDrive\Proyectos Incol\Datalogger\Programa Resultados'
sys.path.append(project_path)
import analyzer

filepath = r'c:\Users\micha\OneDrive\Proyectos Incol\Datalogger\Resultados\040.csv'
df = analyzer.parse_csv(filepath)
events = analyzer.extract_events(df)

best_event = None
min_dist = float('inf')

print(f"Found {len(events)} events.")

for i, evt in enumerate(events):
    # 1. Refine start
    start_idx = analyzer.refine_start_point(evt)
    
    # 2. Find end (speed < 1 km/h) - logic from analysis_controller.py
    try:
        start_loc = evt.index.get_loc(start_idx)
        sub_df = evt.iloc[start_loc:]
        
        stops = sub_df.index[sub_df['Velocidad_GPS'] < 1.0].tolist()
        
        if stops:
             stop_idx = stops[0]
             stop_loc_global = evt.index.get_loc(stop_idx)
             
             if stop_loc_global + 1 < len(evt):
                 end_idx = evt.index[stop_loc_global + 1]
             else:
                 end_idx = stop_idx
        else:
             end_idx = evt.index[-1]
    except Exception as e:
        print(f"Error finding end: {e}")
        end_idx = evt.index[-1]

    # 3. Calculate metrics
    metrics = analyzer.calculate_metrics(evt, start_idx, end_idx)
    
    # 4. Filter for ~40km/h
    init_speed = evt.loc[start_idx, 'Velocidad_GPS']
    
    # Determine Nominal Speed (logic from controller)
    if abs(init_speed - 40) < abs(init_speed - 60):
        nominal = 40
    else:
        nominal = 60
        
    if nominal == 40:
        dist = metrics['dist_m']
        print(f"Event {i}: Speed={init_speed:.2f}, Dist={dist:.2f}")
        if dist < min_dist:
            min_dist = dist
            best_event = {
                'start_lines_idx': start_idx, # DataFrame index
                'end_lines_idx': end_idx,
                'init_speed': init_speed,
                'dist_start': evt.loc[start_idx, 'Distancia'] if 'Distancia' in evt else 0,
                'dist_end': evt.loc[end_idx, 'Distancia'] if 'Distancia' in evt else 0,
                'dist_total': dist
            }

if best_event:
    # CSV Line Number = Index + 2 (Header is line 1, Index 0 is line 2)
    start_line = best_event['start_lines_idx'] + 2
    end_line = best_event['end_lines_idx'] + 2
    
    print("\n--- BEST 40km/h EVENT FOUND ---")
    print(f"Start Line: {start_line}")
    print(f"End Line: {end_line}")
    print(f"Initial Speed: {best_event['init_speed']:.2f} km/h")
    print(f"Start Distance (raw): {best_event['dist_start']:.3f} m")
    print(f"End Distance (raw): {best_event['dist_end']:.3f} m")
    print(f"Braking Distance (calc): {best_event['dist_total']:.2f} m")
else:
    print("No 40km/h events found.")
