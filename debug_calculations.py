import pandas as pd
import os
import sys

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyzer import parse_csv, convert_units, extract_acceleration_events, refine_acceleration_start, calculate_acceleration_metrics

def generate_verification_table():
    input_file = r"c:\Users\Daniel\OneDrive\Proyectos Incol\Datalogger\Resultados\050.csv"
    output_file = r"c:\Users\Daniel\OneDrive\Proyectos Incol\Datalogger\Resultados\verification_050.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return

    print(f"Reading {input_file}...")
    df = parse_csv(input_file)
    df = convert_units(df)
    
    print("Extracting acceleration events...")
    # target_speed=80 as per acceleration test
    raw_events = extract_acceleration_events(df, target_speed=80)
    
    print(f"Found {len(raw_events)} raw events.")
    
    valid_events = []
    for i, evt_df in enumerate(raw_events):
        start_idx = refine_acceleration_start(evt_df)
        metrics = calculate_acceleration_metrics(evt_df, start_idx, target_speed=80)
        
        if metrics:
            valid_events.append({
                'df': evt_df,
                'metrics': metrics,
                'start_idx': start_idx
            })
            
    if not valid_events:
        print("No valid acceleration events found.")
        return

    # Find best event (min distance)
    best_event = min(valid_events, key=lambda x: x['metrics']['dist_m'])
    print(f"Best event distance: {best_event['metrics']['dist_m']:.2f} m")
    
    # Process best event for verification table
    evt_df = best_event['df']
    start_idx = best_event['metrics']['start_idx']
    end_idx = best_event['metrics']['end_idx']
    
    print(f"Best Event Start Index: {start_idx}")
    print(f"Best Event End Index: {end_idx}")
    
    # Slice strictly from start to end (inclusive)
    try:
        # Get integer locations within the event dataframe
        # Note: refine_acceleration_start returns an index LABEL
        start_pos = evt_df.index.get_loc(start_idx)
        end_pos = evt_df.index.get_loc(end_idx)
        
        # Slicing with iloc is exclusive at the end, so +1
        final_slice = evt_df.iloc[start_pos : end_pos + 1].copy()
        
    except Exception as e:
        print(f"Error slicing event: {e}")
        return
    
    # Columns checking
    if 'Accel_X_ms2' not in final_slice.columns:
        # Fallback if convert_units didn't work as expected or column missing
        if 'Accel_X' in final_slice.columns:
            final_slice['Accel_X_ms2'] = final_slice['Accel_X'] * 9.80665
        else:
            print("Error: Accel_X column missing.")
            return

    # Calculate Cumulative Average Formula
    # This is the pandas expanding mean: sum(0..i) / count(0..i)
    final_slice['Promedio_Acumulado_ms2'] = final_slice['Accel_X_ms2'].expanding().mean()
    
    # Add Time axis (relative seconds)
    # 10Hz sample rate assumed (0.1s)
    # Reset index to 0..N
    final_slice = final_slice.reset_index(drop=True)
    final_slice['Time_s'] = final_slice.index * 0.1
    
    # Select output columns
    # We want: Time_s, Velocidad_GPS, Accel_X (raw), Accel_X_ms2 (converted), Promedio_Acumulado_ms2
    cols = ['Time_s', 'Velocidad_GPS', 'Accel_X', 'Accel_X_ms2', 'Promedio_Acumulado_ms2']
    
    # Ensure columns exist
    output_df = final_slice[cols].copy()
    
    print(f"Writing verification table to {output_file}...")
    output_df.to_csv(output_file, index=False, float_format="%.5f")
    print("Done.")

if __name__ == "__main__":
    generate_verification_table()
