import pandas as pd
import numpy as np
import os

# Constants
G_TO_MS2 = 9.80665

def parse_csv(filepath):
    """
    Parses the CSV file, automatically detecting the separator.
    Returns a pandas DataFrame.
    """
    try:
        # Try reading with comma separator first
        df = pd.read_csv(filepath, sep=',')
        if len(df.columns) < 2:
            # If it fails to parse correctly (too few columns), try semicolon
            df = pd.read_csv(filepath, sep=';')
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error reading CSV {filepath}: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def extract_events(df):
    """
    Extracts braking events based on Pulsador == 100.
    Returns a list of DataFrames, each representing an event.
    Events capture 1s before trigger to 1s after speed becomes 0.
    Assumes 10Hz sampling rate (0.1s per sample).
    """
    events = []
    
    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        print("Required columns 'Pulsador' or 'Velocidad_GPS' missing.")
        return events

    # Find indices where Pulsador is 100
    trigger_indices = df.index[df['Pulsador'] == 100].tolist()
    
    # Filter to group consecutive 100s as a single event trigger?
    # Requirement: "Si encuentra varios 100... analiza como eventos independientes"
    # But typically a button press might span multiple samples. 
    # Let's assume distinct press events. For now, we take every instance.
    # If consecutive 100s are part of the same press, we should debounce/group.
    # Ref: "analiza esto como eventos independientes" usually implies separate tests.
    # However, if I hold the button for 0.5s (5 samples), I get 5 triggers. 
    # I should likely group consecutive 100s and take the first one as the trigger.
    
    grouped_triggers = []
    if trigger_indices:
        current_group_start = trigger_indices[0]
        prev_idx = trigger_indices[0]
        
        for idx in trigger_indices[1:]:
            if idx > prev_idx + 10: # Assuming at least 1 second gap between distinct events
                grouped_triggers.append(current_group_start)
                current_group_start = idx
            prev_idx = idx
        grouped_triggers.append(current_group_start)

    for start_idx in grouped_triggers:
        # 1. Start point: 3 seconds before trigger (30 samples) to ensure we capture the start
        slice_start = max(0, start_idx - 30)
        
        # 2. End point: 1 second after speed becomes 0
        # Look ahead from trigger
        msg_end_idx = len(df) - 1
        
        # Check speed from trigger onwards
        sub_df = df.iloc[start_idx:]
        
        # Find first point where speed is close to 0 (e.g. < 0.5 km/h)
        # Using a small threshold because GPS speed might jitter
        stop_indices = sub_df.index[sub_df['Velocidad_GPS'] < 0.5].tolist()
        
        if stop_indices:
            # First time it stops after trigger
            actual_stop_idx = stop_indices[0]
            slice_end = min(len(df), actual_stop_idx + 10) # +1 sec (10 samples)
        else:
            # If never stops, take a reasonable max duration or till end
            slice_end = min(len(df), start_idx + 200) # Max 20s if no stop detected
            
        event_df = df.iloc[slice_start:slice_end].copy()
        
        # Validate event has enough data and speed drops
        if not event_df.empty:
             events.append(event_df)
             
    return events

def convert_units(df):
    """
    Converts acceleration columns from G to m/s^2.
    """
    if 'Accel_X' in df.columns:
        df['Accel_X_ms2'] = df['Accel_X'] * G_TO_MS2
    if 'Accel_Y' in df.columns:
        df['Accel_Y_ms2'] = df['Accel_Y'] * G_TO_MS2
        
    return df

def refine_start_point(event_df, trigger_time_idx=None):
    """
    Identifies the exact point where braking begins using a robust backwards search.
    Algorithm:
    1. Find the point of maximum deceleration (minimum slope) in the window.
    2. Search backwards from that point until the slope becomes flat or positive.
    3. This identifies the "knee" where speed starts to drop consistently.
    """
    try:
        # Work with a copy to safely calculate gradients
        df = event_df.copy()
        
        # Calculate discrete difference of speed (approx derivative)
        # speed is km/h, convert to rough m/s^2 for thresholding or just keep as delta-speed per sample
        # 1 sample = 0.1s. 
        # delta_V (km/h) per sample.
        df['delta_V'] = df['Velocidad_GPS'].diff().shift(-1) # Forward difference at i is V[i+1] - V[i]
        
        # We expect braking to show negative delta_V.
        
        # Define search window: we care about the transition near the trigger.
        # But since we sliced based on trigger, we utilize the whole event slice 
        # (which is -1s to Stop+1s). The start should be in the earlier part.
        
        # Limit search for "Max Deceleration" to the first part of the event 
        # (e.g., first 3 seconds or until speed drops significantly), 
        # to avoid picking up noise at the very end.
        
        # Find trigger to center the search if possible
        trigger_indices = df.index[df['Pulsador'] == 100].tolist()
        if trigger_indices:
             trigger_pos = df.index.get_loc(trigger_indices[0])
        else:
             trigger_pos = 30 # Default if using the 30 sample buffer
             
        # Search window: 2s before trigger to 2s after trigger
        # We want to find the MAX deceleration (min delta_V) in this window
        s_start = max(0, trigger_pos - 20)
        s_end = min(len(df), trigger_pos + 20)
        
        # 1. Find point of Maximum Deceleration (Minimum delta_V)
        search_slice = df.iloc[s_start:s_end].copy()
        
        if search_slice['delta_V'].isnull().all():
             return event_df.index[0]
             
        # Smooth delta_V slightly to avoid single-point noise? 
        # Maybe rolling mean of 3 samples.
        search_slice['delta_V_smooth'] = search_slice['delta_V'].rolling(window=3, center=True).mean()
        
        # Find min value index (strongest braking)
        min_slope_idx = search_slice['delta_V_smooth'].idxmin() 
        
        # Get integer location of this min slope
        min_slope_loc = df.index.get_loc(min_slope_idx)
        
        # 2. Search Backwards
        # Threshold: When does slope become "flat"?
        # Flat means delta_V is close to 0. Let's say > -0.5 km/h per sample (-5 km/h/s) is "start of braking"
        # Or even stricter: > -0.2.
        # Ideally we want the point JUST BEFORE it drops.
        
        start_loc = 0
        threshold = -0.5 # km/h drop per 0.1s (approx -1.4 m/s^2). 
        # If slope is higher than this (e.g. -0.1, 0, 1.0), we assume we are not braking yet.
        
        for i in range(min_slope_loc, -1, -1):
            val = df['delta_V'].iloc[i] 
            # Note: accessing via iloc on the full df to get values. 
            # We use raw delta_V here or smoothed? Smoothed is better for trend.
            # But we calculated smooth only on slice. Let's calc smooth on full locally if needed.
            # Let's simple use the raw value check or a small window average.
            
            # Simple check: consecutive samples ?
            if val > threshold:
                # We found a point where we are NOT braking significantly.
                # The start of braking is the NEXT point (i+1) where it started dropping.
                start_loc = i + 1
                break
        else:
            # If loop finishes without break, start is 0
            start_loc = 0
            
        # Bounds check
        start_loc = max(0, min(start_loc, len(df)-1))
        
        return df.index[start_loc]

    except Exception as e:
        print(f"Error determining start point: {e}")
        return event_df.index[0]

def calculate_metrics(event_df, start_idx, end_idx):
    """
    Calculates distance, time, and acceleration stats between start and end.
    """
    # Slice exact braking phase
    # end_idx should be where speed is 0
    
    phase_df = event_df.loc[start_idx:end_idx]
    
    if phase_df.empty:
        return {}
    
    # Time
    # Assuming 10Hz, rows * 0.1s
    time_s = len(phase_df) * 0.1
    
    # Distance
    # New Logic: Use 'Distancia' column if available (cumulative)
    # else fallback to integration
    
    if 'Distancia' in phase_df.columns:
        # Distance is cumulative. Delta = End - Start
        start_dist = phase_df.loc[start_idx, 'Distancia']
        end_dist = phase_df.loc[end_idx, 'Distancia']
        dist_m = end_dist - start_dist
        
        # Sanity check: if negative (reset happened) or zero?
        # If reset happened, we might have issues. But usually within a short braking event it's monotonic.
        if dist_m < 0:
             # Fallback
             dist_m = (phase_df['Velocidad_GPS'] / 3.6 * 0.1).sum()
    else:
        # Fallback to integration
        # Dist (m) = Speed (m/s) * time (s)
        # Sum of (Speed_kph / 3.6) * 0.1
        dist_m = (phase_df['Velocidad_GPS'] / 3.6 * 0.1).sum()
    
    # Acceleration
    # Use the converted Accel_X_ms2
    if 'Accel_X_ms2' in phase_df.columns:
        accels = phase_df['Accel_X_ms2'] # Use raw values (should be negative for braking)
        avg_acc = accels.mean()
    else:
        avg_acc = 0
        
    # Agrupar por velocidad inicial (40 o 60 km/h)
    initial_speed = phase_df.loc[start_idx, 'Velocidad_GPS'] if start_idx in phase_df.index else 0
    group = 0
    if 35 <= initial_speed <= 45:
        group = 40
    elif 55 <= initial_speed <= 65:
        group = 60
        
    return {
        'time_s': time_s,
        'dist_m': dist_m,
        'avg_acc': avg_acc, # Now signed and only average
        'start_idx': start_idx,
        'end_idx': end_idx,
        'v_start': initial_speed,
        'group': group
    }

def export_event_to_csv(event, output_dir, moto_info, lugar_name, test_name="Prueba"):
    """
    Exports a single event to a CSV file.
    Format: "(Prueba)_(Motocicleta)_(Codigo Modelo)_(Lugar)_(Fecha).csv"
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        def clean(s): return "".join([c for c in str(s) if c.isalnum() or c in (' ', '-', '_')]).strip()
        
        moto_str = clean(moto_info.get('Nombre Comercial', 'Moto'))
        modelo_str = clean(moto_info.get('Código Modelo', 'Modelo'))
        lugar_str = clean(lugar_name)
        test_str = clean(test_name)
        fecha_str = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"{test_str}_{moto_str}_{modelo_str}_{lugar_str}_{fecha_str}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # If the file exists, maybe we append? Or overwrite? 
        # Usually for a new analysis run, we might want to overwrite or version.
        # Let's assume we append all events from the current session to this file
        
        # But wait, 'event' passed here is a single DataFrame. 
        # If we loop through events, we should probably concatenate them first or append mode.
        
        mode = 'a' if os.path.exists(filepath) else 'w'
        header = not os.path.exists(filepath)
        
        # We might want to add a column for Event ID
        df_export = event['df'].copy()
        
        # Append to CSV
        df_export.to_csv(filepath, index=False, mode=mode, header=header)
        
        return filepath
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return None

def extract_acceleration_events(df, target_speed=80):
    """
    Extracts acceleration events.
    Criteria:
    1. Pulsador == 100 trigger.
    2. Start: Speed ~ 0 and increasing.
    3. End: Speed >= target_speed (default 80 km/h).
    """
    events = []
    
    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    # Find triggers
    trigger_indices = df.index[df['Pulsador'] == 100].tolist()
    
    # Group triggers
    grouped_triggers = []
    if trigger_indices:
        current_group_start = trigger_indices[0]
        prev_idx = trigger_indices[0]
        for idx in trigger_indices[1:]:
            if idx > prev_idx + 10: 
                grouped_triggers.append(current_group_start)
                current_group_start = idx
            prev_idx = idx
        grouped_triggers.append(current_group_start)

    for start_idx in grouped_triggers:
        # Start looking from trigger
        # We need a window where speed goes from ~0 to target_speed
        
        # 1. Define broad window limits
        # Look back 5s for start (speed 0)
        # Look forward 60s for target speed
        
        search_start = max(0, start_idx - 50)
        search_end = min(len(df), start_idx + 600)
        
        # Slice for analysis
        # We need to find the point where speed crosses target_speed
        broad_slice = df.iloc[search_start:search_end]
        
        # Check if target speed is reached
        # We look for the first point >= target_speed AFTER the trigger (or near it)
        # Actually, the trigger might be at start (0 km/h).
        
        # Filter slice from trigger onwards
        post_trigger = df.iloc[start_idx:search_end]
        achieved_target = post_trigger[post_trigger['Velocidad_GPS'] >= target_speed]
        
        if achieved_target.empty:
            continue # Did not reach 80 km/h
            
        target_idx = achieved_target.index[0]
        
        # Define Start
        # We need to find where speed *started* to increase from 0.
        # Look backwards from trigger (or from where speed is low).
        # We assume trigger happens near start.
        
        # We'll refine start later, but for extraction let's take a buffer
        # Buffer: 1s before trigger to 1s after target
        
        slice_start_idx = max(0, start_idx - 20)
        slice_end_idx = min(len(df), df.index.get_loc(target_idx) + 10)
        
        # Correctly map integer loc back to index if needed, or just use slice
        # If we use df.iloc, we need integer positions.
        # target_idx is a label.
        target_loc = df.index.get_loc(target_idx)
        slice_end_loc = min(len(df), target_loc + 11)
        
        event_df = df.iloc[slice_start_idx:slice_end_loc].copy()
        
        if not event_df.empty:
            events.append(event_df)
            
    return events

def refine_acceleration_start(event_df):
    """
    Finds the exact start of acceleration (Speed ~ 0 and derivative positive).
    """
    try:
        # We expect speed to be near 0 at start.
        # Find the last point where speed <= 1 km/h before it shoots up.
        
        # Or find the first point where speed > 0.5 km/h and keeps growing?
        # Let's use a forward search from the beginning of the slice.
        
        # Assume event_df captures a bit before start.
        # Find points where speed is low
        
        low_speed = event_df[event_df['Velocidad_GPS'] < 2.0] # < 2 km/h
        if low_speed.empty:
            return event_df.index[0]
            
        # The start is likely the last point of "low speed" before the run
        # Or the point where acceleration becomes consistently positive.
        
        # Let's take the last point where speed < 1.0 km/h
        starts = event_df.index[event_df['Velocidad_GPS'] < 1.0].tolist()
        if starts:
            # We want the last one before the high speed part
            # Identifying the 'launch'
            return starts[-1]
        
        # Fallback
        return event_df.index[0]
    except Exception as e:
        print(f"Error refining accel start: {e}")
        return event_df.index[0]

def calculate_acceleration_metrics(event_df, start_idx, target_speed=80):
    """
    Calculates metrics for 0-Target run.
    """
    try:
        # Find end index (first point >= target_speed)
        # Search from start_idx onwards
        start_loc = event_df.index.get_loc(start_idx)
        sub_df = event_df.iloc[start_loc:]
        
        targets = sub_df.index[sub_df['Velocidad_GPS'] >= target_speed].tolist()
        if not targets:
            return None # Invalid
            
        end_idx = targets[0]
        
        # Calculate Phase Metrics
        phase = event_df.loc[start_idx:end_idx]
        
        # Time
        time_s = (len(phase) - 1) * 0.1 # Delta time
        
        # Distance
        if 'Distancia' in phase.columns:
            d_start = phase.loc[start_idx, 'Distancia']
            d_end = phase.loc[end_idx, 'Distancia']
            dist_m = d_end - d_start
            if dist_m < 0: dist_m = (phase['Velocidad_GPS'] / 3.6 * 0.1).sum()
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * 0.1).sum()
            
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        else:
            # Fallback if column missing (should not happen if converted)
            v_final_ms = phase.loc[end_idx, 'Velocidad_GPS'] / 3.6
            v_start_ms = phase.loc[start_idx, 'Velocidad_GPS'] / 3.6
            if time_s > 0:
                avg_acc = (v_final_ms - v_start_ms) / time_s
            else:
                avg_acc = 0
            
        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'v_final': phase.loc[end_idx, 'Velocidad_GPS'],
            'top_rpm': phase['RPM'].max() if 'RPM' in phase.columns else 0,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error calculating accel metrics: {e}")
        return None

def extract_climbing_events(df, target_distance=70):
    """
    Extracts climbing events (0 to 70m).
    Criteria:
    1. Pulsador == 100 trigger.
    2. Start: Speed ~ 0.
    3. End: Distance >= 70m from start (using cumulative distance column if reliable, or integration).
    """
    events = []
    
    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    # Find triggers
    trigger_indices = df.index[df['Pulsador'] == 100].tolist()
    
    # Group triggers
    grouped_triggers = []
    if trigger_indices:
        current_group_start = trigger_indices[0]
        prev_idx = trigger_indices[0]
        for idx in trigger_indices[1:]:
            if idx > prev_idx + 10: 
                grouped_triggers.append(current_group_start)
                current_group_start = idx
            prev_idx = idx
        grouped_triggers.append(current_group_start)

    for start_idx in grouped_triggers:
        # 1. Define broad window limits (similar to accel)
        search_start = max(0, start_idx - 50)
        search_end = min(len(df), start_idx + 600) # 60s max
        
        # 2. Refine Start (Speed ~ 0)
        # Use refined start logic from accel
        # Slice around trigger
        slice_around = df.iloc[max(0, start_idx-20):min(len(df), start_idx+20)]
        refined_start = refine_acceleration_start(slice_around) # Reuse this function
        
        # 3. Find End (Distance >= 70m)
        # We need to integrate or use Distance column from refined_start
        
        # Get slice from refined_start onwards
        if refined_start not in df.index: continue
        
        start_loc = df.index.get_loc(refined_start)
        run_slice = df.iloc[start_loc:search_end].copy()
        
        if run_slice.empty: continue
        
        # Calculate Relative Distance
        if 'Distancia' in run_slice.columns:
            d_start = run_slice.iloc[0]['Distancia']
            run_slice['Dist_Rel'] = run_slice['Distancia'] - d_start
        else:
            # Integrate
            run_slice['Dist_Rel'] = (run_slice['Velocidad_GPS'] / 3.6 * 0.1).cumsum()
            
        # Find point where Dist_Rel >= 70
        achieved = run_slice[run_slice['Dist_Rel'] >= target_distance]
        
        if achieved.empty:
            continue # Did not reach 70m
            
        end_idx = achieved.index[0]
        end_loc = df.index.get_loc(end_idx)
        
        # 4. Create Event DF
        # Buffer: 1s before start, 1s after end
        cut_start = max(0, start_loc - 10)
        cut_end = min(len(df), end_loc + 11)
        
        event_df = df.iloc[cut_start:cut_end].copy()
        
        if not event_df.empty:
            # Store metadata about EXACT start/end for metrics
            event_df.attrs['start_idx'] = refined_start
            event_df.attrs['end_idx'] = end_idx
            events.append(event_df)
            
    return events

def calculate_climbing_metrics(event_df, start_idx=None, end_idx=None):
    """
    Calculates metrics for climbing 0-70m.
    Returns standard metrics + markers at 10, 30, 50, 70m.
    """
    try:
        # Use attrs if indices not provided
        if start_idx is None: start_idx = event_df.attrs.get('start_idx')
        if end_idx is None: end_idx = event_df.attrs.get('end_idx')
        
        if start_idx is None or end_idx is None:
            return None
            
        # Slicing
        # Ensure indices exist in this df
        if start_idx not in event_df.index or end_idx not in event_df.index:
            return None
            
        start_loc = event_df.index.get_loc(start_idx)
        end_loc = event_df.index.get_loc(end_idx)
        
        phase = event_df.iloc[start_loc : end_loc+1].copy() # Inclusive
        
        # Metrics
        time_s = (len(phase) - 1) * 0.1
        final_speed = phase.iloc[-1]['Velocidad_GPS']
        top_rpm = phase['RPM'].max() if 'RPM' in phase.columns else 0
        
        # Avg Accel (Sensor)
        avg_acc = 0
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        
        # Dist (should be ~70)
        dist_m = 0
        if 'Distancia' in phase.columns:
            dist_m = phase.iloc[-1]['Distancia'] - phase.iloc[0]['Distancia']
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * 0.1).sum()
            
        # Markers Logic (10, 30, 50, 70)
        # We need to find the indices/times for these distances
        markers = {}
        # Calculate localized cumulative distance
        if 'Distancia' in phase.columns:
            d0 = phase.iloc[0]['Distancia']
            phase['Dist_Rel'] = phase['Distancia'] - d0
        else:
            phase['Dist_Rel'] = (phase['Velocidad_GPS'] / 3.6 * 0.1).cumsum()
            
        for d_target in [10, 30, 50, 70]:
            # Find first point >= d_target
            # We want exact or closest
            # Since 70 is end, it matches end_idx
            
            rows = phase[phase['Dist_Rel'] >= d_target]
            if not rows.empty:
                r = rows.iloc[0]
                # Gather data at this point
                idx = r.name
                
                # Time relative to start
                t_rel = (phase.index.get_loc(idx)) * 0.1
                
                # Accel Cumulative (0 to this point)
                # Slice phase from 0 to current
                sub_phase = phase.loc[:idx].copy()
                if 'Accel_X_ms2' in sub_phase.columns:
                    acc_cum = sub_phase['Accel_X_ms2'].mean()
                else:
                    acc_cum = 0 # Fallback unlikley
                
                markers[d_target] = {
                    'idx': idx,
                    'time': t_rel,
                    'dist': r['Dist_Rel'],
                    'speed': r['Velocidad_GPS'],
                    'acc_cum': acc_cum
                }
        
        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'v_final': final_speed,
            'top_rpm': top_rpm,
            'avg_acc': avg_acc,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'markers': markers
        }
    except Exception as e:
        print(f"Error climbing metrics: {e}")
        return None

def extract_top_speed_events(df, target_distance=200):
    """
    Extracts top speed events (0 to 200m based on trigger).
    Criteria:
    1. Pulsador == 100 trigger.
    2. End: Distance >= 200m from start (using cumulative distance column if reliable, or integration).
    """
    events = []
    
    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    # Find triggers
    trigger_indices = df.index[df['Pulsador'] == 100].tolist()
    
    # Group triggers
    grouped_triggers = []
    if trigger_indices:
        current_group_start = trigger_indices[0]
        prev_idx = trigger_indices[0]
        for idx in trigger_indices[1:]:
            if idx > prev_idx + 10: 
                grouped_triggers.append(current_group_start)
                current_group_start = idx
            prev_idx = idx
        grouped_triggers.append(current_group_start)

    for start_idx in grouped_triggers:
        search_end = min(len(df), start_idx + 1200) # Give it 120s max
        start_loc = df.index.get_loc(start_idx)
        run_slice = df.iloc[start_loc:search_end].copy()
        
        if run_slice.empty: continue
        
        # Calculate Relative Distance
        if 'Distancia' in run_slice.columns:
            d_start = run_slice.iloc[0]['Distancia']
            run_slice['Dist_Rel'] = run_slice['Distancia'] - d_start
        else:
            run_slice['Dist_Rel'] = (run_slice['Velocidad_GPS'] / 3.6 * 0.1).cumsum()
            
        # Find point where Dist_Rel >= target_distance
        achieved = run_slice[run_slice['Dist_Rel'] >= target_distance]
        
        if achieved.empty:
            continue # Did not reach 200m
            
        end_idx = achieved.index[0]
        end_loc = df.index.get_loc(end_idx)
        
        # Create Event DF (add some buffer for plotting if needed, 1s before, 1s after)
        cut_start = max(0, start_loc - 10)
        cut_end = min(len(df), end_loc + 11)
        
        event_df = df.iloc[cut_start:cut_end].copy()
        
        if not event_df.empty:
            event_df.attrs['start_idx'] = start_idx
            event_df.attrs['end_idx'] = end_idx
            events.append(event_df)
            
    return events

def calculate_top_speed_metrics(event_df, start_idx=None, end_idx=None):
    """
    Calculates metrics for top speed (0-200m).
    """
    try:
        if start_idx is None: start_idx = event_df.attrs.get('start_idx')
        if end_idx is None: end_idx = event_df.attrs.get('end_idx')
        
        if start_idx is None or end_idx is None: return None
        if start_idx not in event_df.index or end_idx not in event_df.index: return None
            
        start_loc = event_df.index.get_loc(start_idx)
        end_loc = event_df.index.get_loc(end_idx)
        
        phase = event_df.iloc[start_loc : end_loc+1].copy()
        
        time_s = (len(phase) - 1) * 0.1
        v_start = phase.iloc[0]['Velocidad_GPS']
        v_final = phase.iloc[-1]['Velocidad_GPS']
        v_max = phase['Velocidad_GPS'].max()
        top_rpm = phase['RPM'].max() if 'RPM' in phase.columns else 0
        
        avg_acc = 0
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
        
        dist_m = 0
        if 'Distancia' in phase.columns:
            dist_m = phase.iloc[-1]['Distancia'] - phase.iloc[0]['Distancia']
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * 0.1).sum()
            
        return {
            'time_s': time_s,
            'dist_m': dist_m,
            'v_start': v_start,
            'v_final': v_final,
            'v_max': v_max,
            'top_rpm': top_rpm,
            'avg_acc': avg_acc,
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error top speed metrics: {e}")
        return None

def extract_recovery_events(df, target_speed=80):
    """
    Extracts recovery events (Start V -> 80 km/h).
    Groups:
    - 30 km/h (25 <= V < 35)
    - 40 km/h (35 <= V < 45)
    - 50 km/h (45 <= V < 55)
    Criteria:
    1. Pulsador == 100 trigger.
    2. End: Speed >= 80 km/h.
    """
    events = []
    
    if 'Pulsador' not in df.columns or 'Velocidad_GPS' not in df.columns:
        return events

    # Find triggers
    trigger_indices = df.index[df['Pulsador'] == 100].tolist()
    
    # Group triggers (debounce)
    grouped_triggers = []
    if trigger_indices:
        current_group_start = trigger_indices[0]
        prev_idx = trigger_indices[0]
        for idx in trigger_indices[1:]:
            if idx > prev_idx + 10: 
                grouped_triggers.append(current_group_start)
                current_group_start = idx
            prev_idx = idx
        grouped_triggers.append(current_group_start)

    for start_idx in grouped_triggers:
        # Check Initial Speed at Trigger
        # Triggers often span a few rows. Let's look at the speed AT the trigger start.
        # Or maybe average of trigger window? Let's use start_idx speed.
        
        v_start = df.loc[start_idx, 'Velocidad_GPS']
        
        group = None
        if 25 <= v_start < 35:
            group = 30
        elif 35 <= v_start < 45:
            group = 40
        elif 45 <= v_start < 55:
            group = 50
        
        if group is None:
            continue # Out of range
            
        # Find End (V >= 80)
        # Search forward from start_idx
        search_slice = df.loc[start_idx:]
        achieved = search_slice[search_slice['Velocidad_GPS'] >= target_speed]
        
        if achieved.empty:
            continue
            
        end_idx = achieved.index[0]
        end_loc = df.index.get_loc(end_idx)
        start_loc = df.index.get_loc(start_idx)
        
        # Buffer
        cut_start = max(0, start_loc - 10) # 1s before
        cut_end = min(len(df), end_loc + 11) # 1s after
        
        event_df = df.iloc[cut_start:cut_end].copy()
        
        if not event_df.empty:
            event_df.attrs['start_idx'] = start_idx
            event_df.attrs['end_idx'] = end_idx
            event_df.attrs['group'] = group
            events.append(event_df)
            
    return events

def calculate_recovery_metrics(event_df):
    """
    Calculates metrics for recovery test.
    """
    try:
        start_idx = event_df.attrs.get('start_idx')
        end_idx = event_df.attrs.get('end_idx')
        group = event_df.attrs.get('group')
        
        if start_idx is None or end_idx is None: return None
        if start_idx not in event_df.index or end_idx not in event_df.index: return None
        
        start_loc = event_df.index.get_loc(start_idx)
        end_loc = event_df.index.get_loc(end_idx)
        
        phase = event_df.iloc[start_loc:end_loc+1].copy()
        
        # Metrics
        time_s = (len(phase) - 1) * 0.1
        
        # Distance
        dist_m = 0
        if 'Distancia' in phase.columns:
            dist_m = phase.iloc[-1]['Distancia'] - phase.iloc[0]['Distancia']
        else:
            dist_m = (phase['Velocidad_GPS'] / 3.6 * 0.1).sum()
            
        # Avg Accel
        avg_acc = 0
        if 'Accel_X_ms2' in phase.columns:
            avg_acc = phase['Accel_X_ms2'].mean()
            
        # Top RPM
        top_rpm = phase['RPM'].max() if 'RPM' in phase.columns else 0
        
        return {
            'group': group,
            'time_s': time_s,
            'dist_m': dist_m,
            'avg_acc': avg_acc,
            'top_rpm': top_rpm,
            'v_start': phase.iloc[0]['Velocidad_GPS'],
            'v_final': phase.iloc[-1]['Velocidad_GPS'],
            'start_idx': start_idx,
            'end_idx': end_idx
        }
    except Exception as e:
        print(f"Error recovery metrics: {e}")
        return None

if __name__ == "__main__":
    main_test()
