import pandas as pd
import numpy as np
import random

# Configuration
# INPUT_FILE = r'c:\Users\micha\OneDrive\Proyectos Incol\Datalogger\BackUp\3\Resultados\036.csv'
INPUT_FILE = r'c:\Users\Daniel\OneDrive\Proyectos Incol\Datalogger\Resultados\036.csv'
OUTPUT_FILE = r'c:\Users\Daniel\OneDrive\Proyectos Incol\Datalogger\Programa Resultados\test_data_varied.csv'

def parse_csv(filepath):
    try:
        # Try semicolon first as seen in the snippet
        df = pd.read_csv(filepath, sep=';')
        if len(df.columns) < 2:
            df = pd.read_csv(filepath, sep=',')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_variations():
    df = parse_csv(INPUT_FILE)
    if df is None: return

    # Identify triggers
    triggers = df.index[df['Pulsador'] == 100].tolist()
    
    # Group triggers
    events = []
    if triggers:
        curr = [triggers[0]]
        for i in range(1, len(triggers)):
            if triggers[i] > triggers[i-1] + 10:
                events.append(curr[0]) # Start of event
                curr = [triggers[i]]
            else:
                curr.append(triggers[i])
        events.append(curr[0])

    print(f"Found {len(events)} original events at indices: {events}")

    new_df_parts = []
    last_idx = 0

    # We will reconstruct the file:
    # 1. Keep non-event chunks as is (or slightly noised)
    # 2. Replace events with varied versions

    for start_idx in events:
        # 1. Append data before this event (from last_idx to start_idx - 50)
        # Give some buffer before the event starts to keep context
        pre_event_end = max(last_idx, start_idx - 50)
        
        if pre_event_end > last_idx:
            chunk = df.iloc[last_idx:pre_event_end].copy()
            new_df_parts.append(chunk)
        
        # 2. Extract the event to modify
        # Assuming event length is roughly until speed is 0 + buffer
        # Let's verify end of event
        sub = df.iloc[start_idx:]
        stops = sub.index[sub['Velocidad_GPS'] < 0.5].tolist()
        if stops:
            end_idx = stops[0] + 20 # Buffer after stop
        else:
            end_idx = min(len(df), start_idx + 100)
            
        event_chunk = df.iloc[pre_event_end:end_idx].copy()
        
        # 3. Apply Variation
        # Randomly choose a modification type
        # A: Change Target Speed (Shift speed curve up/down slightly before braking)
        # B: Change Braking Intensity (Scale Accel -> Re-integrate Speed)
        
        variation_type = random.choice(['faster', 'slower', 'harder', 'softer', 'normal'])
        
        print(f"Event at {start_idx}: Applying {variation_type}")
        
        # Simple Logic: Scale Speed and Accel
        if variation_type == 'faster':
            factor = random.uniform(1.05, 1.15) # 5-15% faster
        elif variation_type == 'slower':
            factor = random.uniform(0.85, 0.95) # 5-15% slower
        elif variation_type == 'harder':
            factor = 1.0 # Accel will change
        elif variation_type == 'softer':
            factor = 1.0
        else:
            factor = 1.0
            
        # Apply speed scaling
        event_chunk['Velocidad_GPS'] = event_chunk['Velocidad_GPS'] * factor
        
        # For 'harder' or 'softer', we modify the rate of speed drop
        # This implies changing the 'Time' axis (resampling) or just scaling values artificially 
        # (which might break physics continuity V = at, but for testing checks it's fine)
        
        if variation_type in ['harder', 'softer']:
            # Resample to stretch/compress time
            orig_len = len(event_chunk)
            if variation_type == 'harder':
                new_len = int(orig_len * 0.8) # Shorter time = Harder braking
            else:
                new_len = int(orig_len * 1.2) # Longer time = Softer braking
                
            # Resample indices
            old_indices = np.arange(orig_len)
            new_indices = np.linspace(0, orig_len-1, new_len)
            
            # Interpolate columns
            varied_chunk = pd.DataFrame()
            for col in event_chunk.columns:
                try:
                    if event_chunk[col].dtype in [np.float64, np.int64]:
                        varied_chunk[col] = np.interp(new_indices, old_indices, event_chunk[col])
                    else:
                        # For strings/objects, just fill forward/nearest or take mostly
                        varied_chunk[col] = event_chunk[col].iloc[0] # Placeholder
                except:
                     varied_chunk[col] = event_chunk[col].iloc[0]

            # Fix Pulsador if it got interpolated to weird values
            if 'Pulsador' in varied_chunk.columns:
                varied_chunk['Pulsador'] = np.where(varied_chunk['Pulsador'] > 50, 100, 0)
                
            event_chunk = varied_chunk

        new_df_parts.append(event_chunk)
        last_idx = end_idx

    # Append remaining tail
    if last_idx < len(df):
        new_df_parts.append(df.iloc[last_idx:])

    # Concatenate
    final_df = pd.concat(new_df_parts, ignore_index=True)
 
    # Recalculate 'Hora' or fill dummy if broken? 
    # The program likely doesn't rely strictly on 'Hora' continuity for analysis, mostly index/sampling rate.
    
    final_df.to_csv(OUTPUT_FILE, index=False, sep=';') # Keeping original separator
    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_variations()
