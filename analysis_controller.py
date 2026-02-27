import os
import pandas as pd
from analyzer import parse_csv, extract_events, convert_units, refine_start_point, calculate_metrics, export_event_to_csv, extract_climbing_events, calculate_climbing_metrics, extract_recovery_events, calculate_recovery_metrics
from plotter import Plotter
from reporter import PDFReporter
from reportlab.lib.units import inch

class AnalysisController:
    def __init__(self, output_dir="Resultados"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_data(self, inputs, moto_info, comments, env_conditions=None):

        """
        inputs: List of dicts [{'filepath': str, 'pilot': str, 'weight': str}]
        env_conditions: dict with keys 'temp_amb', 'humidity', 'temp_ground', 'wind_speed', 'wind_dir'
        """
        all_events = []
        
        # 1. Parse and Extract
        for inp in inputs:
            df = parse_csv(inp['filepath'])
            df = convert_units(df)
            raw_events = extract_events(df)
            
            for evt_df in raw_events:
                # Refine start
                start_idx = refine_start_point(evt_df)
                
                # We need end_idx. The extract_events gave us a rough cut.
                # Let's recalculate precise stop (speed ~ 0) *after* the start.
                # Actually extract_events already tried to cut 1s after stop.
                # Let's check where speed drops to 0 relative to start.
                
                # Recalculate precise stop (speed ~ 0) *after* the start
                # Use a fresh search from start_idx
                try:
                    start_loc = evt_df.index.get_loc(start_idx)
                    sub_df = evt_df.iloc[start_loc:]
                    
                    # New Logic: First point < 1.0 km/h
                    stops = sub_df.index[sub_df['Velocidad_GPS'] < 1.0].tolist()
                    
                    if stops:
                         stop_idx = stops[0]
                         # Requirement: "toma un dato despues de ese punto"
                         # We need to find the location in the ORIGINAL dataframe to get the next one safely
                         stop_loc_global = evt_df.index.get_loc(stop_idx)
                         
                         if stop_loc_global + 1 < len(evt_df):
                             end_idx = evt_df.index[stop_loc_global + 1]
                         else:
                             end_idx = stop_idx
                    else:
                         end_idx = evt_df.index[-1]
                except:
                    end_idx = evt_df.index[-1]
                
                # CROP THE DATAFRAME
                # Requirement: 1 second before Start, 1 second after Stop.
                
                try:
                    s_loc = evt_df.index.get_loc(start_idx)
                    e_loc = evt_df.index.get_loc(end_idx)
                    
                    crop_start_loc = max(0, s_loc - 10) # 1s before
                    crop_end_loc = min(len(evt_df), e_loc + 11) # 1s after (inclusive slice so +11? loc slice is inclusive. iloc is exclusive on end)
                    
                    # Using iloc for cleaner slicing
                    final_df = evt_df.iloc[crop_start_loc:crop_end_loc].copy()
                    
                    # Update metrics to use this new cropped DF
                    # We need to make sure start_idx and end_idx are still valid labels in final_df (they are)
                    
                    metrics = calculate_metrics(final_df, start_idx, end_idx)
                    
                    # Extract Approach Phase (from crop start to start_idx)
                    # We want to check stability in the 1s before braking
                    # In final_df, this is from index 0 to WHERE start_idx is.
                    new_start_loc = final_df.index.get_loc(start_idx)
                    approach_slice = final_df.iloc[:new_start_loc+1] # Include start point? user said "before point zero". Let's include it to be safe or just up to it. "ese segundo antes del punto cero".
                    approach_speeds = approach_slice['Velocidad_GPS']

                    # Update event object
                    evt_df = final_df
                    
                except Exception as e:
                    print(f"Error cropping: {e}")
                    # Fallback to original
                    metrics = calculate_metrics(evt_df, start_idx, end_idx)
                    approach_speeds = pd.Series([evt_df.loc[start_idx, 'Velocidad_GPS']]) if start_idx in evt_df.index else pd.Series([0])

                # Determine "Target Speed" for classification
                # Use Speed at start_idx
                if start_idx in evt_df.index:
                    initial_speed = evt_df.loc[start_idx, 'Velocidad_GPS']
                else:
                    initial_speed = 0

                event_obj = {
                    'df': evt_df,
                    'metrics': metrics,
                    'pilot': inp['pilot'],
                    'initial_speed': initial_speed,
                    'approach_speeds': approach_speeds, # Store for grouping validation
                    'weight': inp['weight']
                }
                
                all_events.append(event_obj)
                
                # Export individual CSV
                export_event_to_csv(event_obj, self.output_dir, moto_info, inp['pilot'])
        
        # 2. Group by Speed Range (40, 60, etc.)
        # Logic: "toma la velocidad inicial y un rango de mas o menos 8km/h"
        # New Logic: Validate that approach speed stays within range
        
        grouped_events = {} # { nominal_speed: [events] }
        TOLERANCE = 8
        
        processed_indices = set()
        for i, ev in enumerate(all_events):
            if i in processed_indices: continue
            
            ref_speed = ev['initial_speed']
            
            # Check if this seed event ITSELF is valid? 
            # We assume the seed defines the group. 
            # But let's check if the seed's own approach was stable relative to its OWN start speed?
            # Or just relative to the nominal group it forms?
            # Let's assume the seed is valid enough to start a group.
            
            cluster = [ev]
            processed_indices.add(i)
            
        # 2. Group by Speed Range using Nearest Nominal (Rounded to 10)
        # Logic: Segment tests into buckets like 30, 40, 60 based on proximity.
        # Then validate consistency within that target bucket.
        
        grouped_events = {} # { nominal_speed: [events] }
        TOLERANCE = 8
        
        for ev in all_events:
            # 1. Determine Nominal Target Speed
            # Rounding to nearest 10: 31->30, 39->40.
            # This ensures hard separation between 30 and 40 tests.
            initial_speed = ev['initial_speed']
            nominal = int(round(initial_speed / 10.0) * 10)
            
            # 2. Validate Consistency
            # Check if the event actually belongs to this nominal group significantly
            # and if the approach was stable relative to this TARGET.
            
            # Check range [Nominal - 8, Nominal + 8]
            lower_bound = nominal - TOLERANCE
            upper_bound = nominal + TOLERANCE
            
            # A. Is the start speed within tolerance? (Usually yes by rounding, unless tolerance < 5)
            if not (lower_bound <= initial_speed <= upper_bound):
                continue # Discard outlier (e.g. 49 km/h -> 50 nominal. If tolerance 8, [42, 58]. 49 ok. 
                         # What if 44? 44->40. [32, 48]. 44 ok.
                         # What if super outlier?)
            
            # B. Check Approach Stability against the NOMINAL target
            # Ensure the rider was aiming for 'nominal' and held it steady.
            app_min = ev['approach_speeds'].min()
            app_max = ev['approach_speeds'].max()
            
            if (app_min >= lower_bound) and (app_max <= upper_bound):
                if nominal not in grouped_events:
                    grouped_events[nominal] = []
                grouped_events[nominal].append(ev)
            else:
                # Event discarded because approach was too unstable or out of target range
                # print(f"Discarding event aiming for {nominal}: Unstable approach [{app_min:.1f}, {app_max:.1f}]")
                pass
            
        # 3. Generate Report
        filename = f"{moto_info.get('Nombre Comercial', 'Reporte')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        reporter = PDFReporter(filepath)
        
        # Get unique pilots info
        pilots_info = []
        seen_pilots = set()
        for inp in inputs:
            if inp['pilot'] not in seen_pilots:
                pilots_info.append({'name': inp['pilot'], 'weight': inp['weight']})
                seen_pilots.add(inp['pilot'])
                
        reporter.add_header(moto_info, pilots_info, comments, env_conditions)
        
        sorted_speeds = sorted(grouped_events.keys())
        
        # --- RANKING LOGIC ---
        # Requirement: Save ranking only if 3 files (inputs) are processed
        if len(inputs) >= 3:
            # We need to extract best event for 40km/h and 60km/h
            from data_manager import DataManager
            dm = DataManager()
            
            # Helper to find best event in a nominal group
            def get_best_event(nominal_speed):
                if nominal_speed in grouped_events:
                    events = grouped_events[nominal_speed]
                    if events:
                        # Best is min distance
                        return min(events, key=lambda x: x['metrics']['dist_m'])
                return None

            # Process 40 and 60
            for target_speed in [40, 60]:
                best_evt = get_best_event(target_speed)
                if best_evt:
                    # Construct Entry
                    # "Fecha, Nombre Comercial, Código Modelo, Placa, Peso Moto, Piloto, Peso Piloto, Env Conditions, Results"
                    
                    # Calculate Total Weight
                    try:
                        moto_w = float(moto_info.get('Peso (Kg)', 0))
                        pilot_w = float(best_evt['weight'])
                        total_w = moto_w + pilot_w
                    except:
                        total_w = 0
                        
                    entry = {
                        'fecha': pd.Timestamp.now().strftime("%Y-%m-%d"),
                        'target_speed': target_speed,
                        'moto_nombre': moto_info.get('Nombre Comercial', ''),
                        'moto_codigo': moto_info.get('Código Modelo', ''),
                        'moto_placa': moto_info.get('Placa', ''),
                        'moto_peso': moto_info.get('Peso (Kg)', ''),
                        'piloto': best_evt['pilot'],
                        'piloto_peso': best_evt['weight'],
                        'peso_total': total_w,
                        'env': env_conditions if env_conditions else {},
                        'metrics': {
                            'dist_m': best_evt['metrics']['dist_m'],
                            'time_s': best_evt['metrics']['time_s'],
                            'avg_acc': best_evt['metrics']['avg_acc'],
                            'initial_speed': best_evt['initial_speed']
                        }
                    }
                    dm.add_ranking_entry(entry)

        for speed in sorted_speeds:
            events = grouped_events[speed]
            if not events: continue
            
            reporter.add_section(f"Análisis de Frenado - {speed} km/h")
            
            # Filter best events based on Distance (metrics['dist_m'])
            # Logic varies by number of inputs (pilots/files)
            
            # If 1 file (single pilot logic):
            # "Se realiza una grafica tipo 1 de los 3 mejores eventos... las 3 primeras con la menor distancia"
            # If multiple files (multi pilot logic):
            # "con el mejor evento de cada piloto"
            
            num_files = len(inputs)
            
            selected_events_for_combined = []
            
            if num_files == 1:
                # Top 3 total
                sorted_by_dist = sorted(events, key=lambda x: x['metrics']['dist_m'])
                selected_events_for_combined = sorted_by_dist[:3]
            else:
                # Best per pilot
                # Group by pilot
                pilot_map = {}
                for e in events:
                    p = e['pilot']
                    if p not in pilot_map: pilot_map[p] = []
                    pilot_map[p].append(e)
                
                for p, p_events in pilot_map.items():
                    best = min(p_events, key=lambda x: x['metrics']['dist_m'])
                    selected_events_for_combined.append(best)
            
            # Generated Combined Plot (Type 1)
            img_buf = Plotter.plot_speed_vs_time(selected_events_for_combined, f"Velocidad vs Tiempo ({speed} km/h)")
            reporter.add_image(img_buf)
            
            # Table Summary for Combined
            table_data = [['Evento', 'Distancia (m)', 'Tiempo (s)', 'Acel Prom (m/s²)']]
            for i, ev in enumerate(selected_events_for_combined):
                m = ev['metrics']
                row = [
                    f"Evento {i+1} ({ev['pilot']})",
                    f"{m['dist_m']:.2f}",
                    f"{m['time_s']:.2f}",
                    f"{m['avg_acc']:.2f}"
                ]
                table_data.append(row)
            reporter.add_table(table_data)
            
            reporter.add_page_break()
            
            # Individual Best Event Analysis
            # "Luego se realiza una grafica tipo 1 de la mejor de las pruebas y abajo ... una grafica tipo 2"
            # For 1 file: Best of the top 3 (which is index 0 of sorted)
            # For 2+ files: "Grafica tipo 1 con el mejor de todos los eventos de los pilotos" -> Global best
            
            global_best = min(events, key=lambda x: x['metrics']['dist_m'])
            
            reporter.add_section(f"Mejor Evento Global ({speed} km/h) - {global_best['pilot']}")
            
            # Type 1 for Single
            img_buf1 = Plotter.plot_speed_vs_time([global_best], "Velocidad vs Tiempo (Mejor Evento)")
            reporter.add_image(img_buf1)
            
            # Type 2 for Single
            img_buf2 = Plotter.plot_accel_vs_time(global_best, "Aceleración vs Tiempo")
            reporter.add_image(img_buf2, height=2.5*inch)
            
            # Summary Table for this single event
            m = global_best['metrics']
            single_table = [
                ['Métrica', 'Valor'],
                ['Distancia Total', f"{m['dist_m']:.2f} m"],
                ['Tiempo Frenado', f"{m['time_s']:.2f} s"],
                ['Aceleración Prom', f"{m['avg_acc']:.2f} m/s²"],
                ['Velocidad Inicial', f"{global_best['initial_speed']:.2f} km/h"]
            ]
            reporter.add_table(single_table)
            
            reporter.add_page_break()
            
        success = reporter.build()
        if success:
             # Open folder?
             pass
        return success, filepath

    def process_acceleration_0_80(self, inputs, moto_info, comments, env_conditions=None):
        """
        Processes Acceleration 0-80 km/h test.
        inputs: List of dicts (usually single file)
        """
        from analyzer import extract_acceleration_events, refine_acceleration_start, calculate_acceleration_metrics, export_event_to_csv
        
        all_events = []
        
        # 1. Parse and Extract
        for inp in inputs:
            df = parse_csv(inp['filepath'])
            df = convert_units(df)
            
            # Extract candidates (0-80)
            raw_events = extract_acceleration_events(df, target_speed=80)
            
            for i, evt_df in enumerate(raw_events):
                # Refine start
                start_idx = refine_acceleration_start(evt_df)
                
                # Calculate metrics (0-80)
                metrics = calculate_acceleration_metrics(evt_df, start_idx, target_speed=80)
                
                if metrics:
                    # Create Event Object
                    event_obj = {
                        'df': evt_df,
                        'metrics': metrics,
                        'pilot': inp['pilot'],
                        'weight': inp['weight'],
                        'id': i+1
                    }
                    all_events.append(event_obj)
                    
                    # Export individual CSV
                    export_event_to_csv(event_obj, self.output_dir, moto_info, f"{inp['pilot']}_Accel_0_80_{i+1}")
        
        if not all_events:
            return False, "No se encontraron eventos válidos de Aceleración 0-80 km/h."
            
        # 2. Sort by Best (Minimum Distance)
        # Requirement: "el mejor evento se debe evaluar la menor distancia"
        all_events.sort(key=lambda x: x['metrics']['dist_m'])
        
        # Select top 3
        top_3_events = all_events[:3]
        best_event = all_events[0]
        
        # 3. Generate Report
        filename = f"Accel_0_80_{moto_info.get('Nombre Comercial', 'Moto')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        reporter = PDFReporter(filepath)
        
        # Header
        pilots_info = [{'name': inputs[0]['pilot'], 'weight': inputs[0]['weight']}]
        reporter.add_header(moto_info, pilots_info, comments, env_conditions, title="Prueba de Aceleración 0 - 80 km/h")
        
        reporter.add_section("Resumen: 3 Mejores Eventos")
        
        # Combined Graph (Speed vs Time)
        # Need to implement plot_acceleration_0_80_combined in Plotter
        # For now, reuse plot_speed_vs_time but maybe custom?
        # Requirement: "etiquetas... linea cero velocidad inicial... linea final tiempo, vel final, acel prom, dist"
        img_buf = Plotter.plot_acceleration_comparison(top_3_events, "Comparativa: Velocidad vs Tiempo (Top 3)")
        reporter.add_image(img_buf)
        
        # Summary Table
        table_data = [['Evento', 'Distancia (m)', 'Top RPM', 'Tiempo (s)', 'Acel Prom (m/s²)', 'Vel Final (km/h)']]
        for i, ev in enumerate(top_3_events):
            m = ev['metrics']
            row = [
                f"Evento {ev['id']} ({ev['pilot']})",
                f"{m['dist_m']:.2f}",
                f"{int(m.get('top_rpm', 0))}",
                f"{m['time_s']:.2f}",
                f"{m['avg_acc']:.2f}",
                f"{m['v_final']:.2f}"
            ]
            table_data.append(row)
        reporter.add_table(table_data)
        
        reporter.add_page_break()
        
        # 4. Detailed Analysis of Best Event
        reporter.add_section(f"Mejor Evento: Evento {best_event['id']} ({best_event['pilot']})")
        
        # Detailed Graph 1: Speed vs Time with markers 0, 20, 40, 60, 80
        img_detail_v = Plotter.plot_acceleration_detailed(best_event, "Análisis Detallado: Velocidad vs Tiempo")
        reporter.add_image(img_detail_v)
        
        # Detailed Graph 2: Accel vs Time
        img_detail_a = Plotter.plot_accel_vs_time(best_event, "Aceleración Promedio vs Tiempo", benchmarks=[0, 20, 40, 60, 80])
        
        # Detailed Graph 3: RPM vs Time
        img_detail_rpm = Plotter.plot_rpm_vs_time(best_event, "RPM vs Tiempo", benchmarks=[0, 20, 40, 60, 80])
        
        # Reorder: Vel -> RPM -> Accel -> Table
        # We already added Vel. Now add RPM, then Accel.
        # Use height=2.3*inch to match aspect ratio of (12, 3.5) approx
        reporter.add_image(img_detail_rpm, height=1.9*inch)
        reporter.add_image(img_detail_a, height=1.9*inch)
        
        # Detailed Metrics Table (Segments)
        # We need to calculate checks for 0-20, 20-40, 40-60, 60-80
        # Calculate these on the fly or in analyzer
        
        # Segment Analysis Helper
        from analyzer import calculate_acceleration_metrics
        segments = [(0,20), (20,40), (40,60), (60,80)]
        seg_metrics = []
        
        # For segment calculation, we need start/end of that specific segment
        # We can reuse calculate_acceleration_metrics but need to find new start/end indices relative to the event
        
        # Find 0 start
        base_start = best_event['metrics']['start_idx']
        
        table_segments = [['Segmento', 'Tiempo (s)', 'Top RPM', 'Distancia (m)', 'Acel Prom (m/s²)']]
        
        for v1, v2 in segments:
            # Find index where speed >= v1 (start of seg)
            # Find index where speed >= v2 (end of seg)
            df = best_event['df']
            
            # Start search from base_start
            sub = df.loc[base_start:]
            
            # Find v1
            if v1 == 0:
                s_idx = base_start
            else:
                s_candidates = sub[sub['Velocidad_GPS'] >= v1]
                if s_candidates.empty: continue
                s_idx = s_candidates.index[0]
                
            # Find v2
            # search from s_idx
            sub2 = df.loc[s_idx:]
            e_candidates = sub2[sub2['Velocidad_GPS'] >= v2]
            if e_candidates.empty: continue
            e_idx = e_candidates.index[0]
            
            # Calc metrics
            # calc from s_idx to e_idx
            
            # Time
            t = (df.index.get_loc(e_idx) - df.index.get_loc(s_idx)) * 0.1
            
            # Dist
            if 'Distancia' in df.columns:
                d = df.loc[e_idx, 'Distancia'] - df.loc[s_idx, 'Distancia']
            else:
                d = 0 # fallback ignored for now
                
            # Accel (Sensor Average)
            seg_slice = df.loc[s_idx:e_idx]
            if 'Accel_X_ms2' in seg_slice.columns:
                a = seg_slice['Accel_X_ms2'].mean()
            else:
                # Fallback to GPS
                if t > 0:
                    a = ((v2/3.6) - (v1/3.6)) / t
                else:
                    a = 0
            
            # Top RPM in Segment
            # Slice from s_idx to e_idx
            # Need strict slice
            seg_slice = df.loc[s_idx:e_idx]
            if 'RPM' in seg_slice.columns:
                top_r = seg_slice['RPM'].max()
            else:
                top_r = 0
                
            table_segments.append([
                f"{v1}-{v2} km/h",
                f"{t:.2f}",
                f"{int(top_r)}",
                f"{d:.2f}",
                f"{a:.2f}"
            ])
            
        reporter.add_table(table_segments)
        
        # 5. 4-Graph Grid (Segment Graphs)
        # Requirement: "graficas pequeñas, que quepan 4 por hoja... 0-20, 20-40..."
        # We need to generate 4 plots and put them in a grid.
        # Plotter needs a method to generate a figure we can save to image.
        
        reporter.add_page_break()
        reporter.add_section("Análisis por Tramos: 0 - 40 km/h")
        img_seg1 = Plotter.plot_segment_group(best_event, [(0,20), (20,40)], "Tramos 0-20 y 20-40 km/h")
        reporter.add_image(img_seg1)
        
        reporter.add_page_break()
        reporter.add_section("Análisis por Tramos: 40 - 80 km/h")
        img_seg2 = Plotter.plot_segment_group(best_event, [(40,60), (60,80)], "Tramos 40-60 y 60-80 km/h")
        reporter.add_image(img_seg2)
        
        success = reporter.build()
        return success, filepath

    def process_climbing(self, solo_data, passenger_data, moto_info, comments, env_conditions=None):
        """
        Processes Climbing/Ascent Test (0-70m).
        """
        from analyzer import extract_climbing_events, calculate_climbing_metrics, export_event_to_csv, convert_units, parse_csv
        
        # Helper to process a single input dict
        def process_input(inp_data, suffix):
            if not inp_data: return []
            
            try:
                df = parse_csv(inp_data['filepath'])
                df = convert_units(df)
                
                raw_events = extract_climbing_events(df, target_distance=70)
                
                processed = []
                for i, evt_df in enumerate(raw_events):
                    metrics = calculate_climbing_metrics(evt_df)
                    if metrics:
                        processed.append({
                            'df': evt_df,
                            'metrics': metrics,
                            'pilot': inp_data['pilot'],
                            'weight': inp_data['weight'],
                            'type': inp_data['type'],
                            'id': f"{suffix}_{i+1}"
                        })
                        
                        # Export CSV
                        export_event_to_csv({
                            'df': evt_df, 
                            'metrics': metrics, 
                            'pilot': inp_data['pilot'],
                            'weight': inp_data['weight']
                        }, self.output_dir, moto_info, f"{inp_data['pilot']}_Ascenso_{suffix}_{i+1}")
                        
                return processed
            except Exception as e:
                print(f"Error processing input {suffix}: {e}")
                return []

        # 1. Process Data
        solo_events = process_input(solo_data, "Solo")
        passenger_events = process_input(passenger_data, "Pasajero")
        
        if not solo_events and not passenger_events:
            return False, "No se encontraron eventos válidos de Ascenso (0-70m)."
            
        # 2. Select Best Events (Max Final Speed)
        # Requirement: "Para determinar el mejor evento, se califica la velocidad final mas alta"
        
        solo_events.sort(key=lambda x: x['metrics']['v_final'], reverse=True)
        passenger_events.sort(key=lambda x: x['metrics']['v_final'], reverse=True)
        
        best_solo = solo_events[:2] # Top 2
        best_pass = passenger_events[:2] # Top 2
        
        combined_best = best_solo + best_pass
        
        if not combined_best:
             return False, "No valid events found after filtering."
             
        # 3. Generate Report
        filename = f"Ascenso_0_70_{moto_info.get('Nombre Comercial', 'Moto')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        reporter = PDFReporter(filepath)
        
        # Header inputs info
        pilots_info = []
        if solo_data: pilots_info.append({'name': f"Solo: {solo_data['pilot']}", 'weight': solo_data['weight']})
        if passenger_data: pilots_info.append({'name': f"Pass: {passenger_data['pilot']} + {passenger_data['passenger']}", 'weight': passenger_data['weight']})
        
        reporter.add_header(moto_info, pilots_info, comments, env_conditions, title="Prueba de Ascenso (0 - 70m)")
        
        # --- Page 1: Combined ---
        reporter.add_section("Resumen: Mejores Eventos (Solo vs Pasajero)")
        
        # Combined Graph (Speed vs Time)
        # Reuse standard plot but maybe customize title
        img_buf1 = Plotter.plot_speed_vs_time(combined_best, "Comparativa Velocidad vs Tiempo")
        reporter.add_image(img_buf1)
        
        # Summary Table
        table_data = [['Evento', 'Tiempo (s)', 'Vel Final (km/h)', 'Top RPM', 'Acel Prom (m/s²)']]
        for ev in combined_best:
            m = ev['metrics']
            row = [
                f"{ev['pilot']} ({ev['id']})",
                f"{m['time_s']:.2f}",
                f"{m['v_final']:.2f}",
                f"{int(m['top_rpm'])}",
                f"{m['avg_acc']:.2f}"
            ]
            table_data.append(row)
        reporter.add_table(table_data)
        
        # --- Page 2: Best Solo Detail ---
        if best_solo:
            reporter.add_page_break()
            bs = best_solo[0]
            reporter.add_section(f"Mejor Evento Solo - {bs['pilot']}")
            
            # Big Speed Graph
            # We need a new plotter function that handles the markers at 10,30,50,70m
            # Let's call it plot_climbing_detailed
            img_bs1 = Plotter.plot_climbing_detailed(bs, "Velocidad vs Tiempo (Detalle)")
            reporter.add_image(img_bs1)
            
            # Small Graphs (RPM, Accel)
            # Layout: Side by Side? Or Top/Bottom? "grafica de velocidad ... y de tamaño reducido las de RPM y aceleracion"
            # Let's put them below
            
            img_rpm = Plotter.plot_rpm_vs_time(bs, "RPM vs Tiempo", markers=bs['metrics'].get('markers'))
            img_acc = Plotter.plot_accel_vs_time(bs, "Aceleración vs Tiempo", markers=bs['metrics'].get('markers'))
            
            # Add images with reduced height?
            # Creating a grid for them might be better
            # Or just add them sequentially with specific height
            # Add images with reduced height
            reporter.add_image(img_rpm, height=1.9*inch)
            reporter.add_image(img_acc, height=1.9*inch)
            
            # Summary Table (Page 2)
            # "evento, tiempo, velocidad, top rpm y aceleracion promedio"
            m = bs['metrics']
            t2 = [
                ['Tiempo 0-70m', 'Velocidad Final', 'Top RPM', 'Aceleración Prom'],
                [f"{m['time_s']:.2f} s", f"{m['v_final']:.2f} km/h", f"{int(m['top_rpm'])}", f"{m['avg_acc']:.2f} m/s²"]
            ]
            reporter.add_table(t2)

        # --- Page 3: Best Passenger Detail ---
        if best_pass:
            reporter.add_page_break()
            bp = best_pass[0]
            reporter.add_section(f"Mejor Evento Pasajero - {bp['pilot']}")
            
            img_bp1 = Plotter.plot_climbing_detailed(bp, "Velocidad vs Tiempo (Detalle)")
            reporter.add_image(img_bp1)
            
            img_rpm_p = Plotter.plot_rpm_vs_time(bp, "RPM vs Tiempo", markers=bp['metrics'].get('markers'))
            img_acc_p = Plotter.plot_accel_vs_time(bp, "Aceleración vs Tiempo", markers=bp['metrics'].get('markers'))
            
            reporter.add_image(img_rpm_p, height=1.9*inch)
            reporter.add_image(img_acc_p, height=1.9*inch)
            
            m = bp['metrics']
            t3 = [
                ['Tiempo 0-70m', 'Velocidad Final', 'Top RPM', 'Aceleración Prom'],
                [f"{m['time_s']:.2f} s", f"{m['v_final']:.2f} km/h", f"{int(m['top_rpm'])}", f"{m['avg_acc']:.2f} m/s²"]
            ]
            reporter.add_table(t3)
            
        success = reporter.build()
        return success, filepath

    def process_recovery(self, data, moto_data, comments, env_conditions):
        """
        Process Recovery Test (Single File).
        Groups: 30, 40, 50 km/h.
        Best: Min Distance to 80 km/h.
        """
        try:
            filepath = data['filepath']
            pilot = data['pilot']
            weight = data['weight']
            
            # Parse
            df = parse_csv(filepath)
            df = convert_units(df)
            
            # Extract
            raw_events = extract_recovery_events(df, target_speed=80)
            
            if not raw_events:
                return False, "No se encontraron eventos de recuperación válidos (Pulsador=100 -> 80km/h)."
                
            # Metrics & Grouping
            grouped_events = {} # {30: [metrics, ...], 40: ...}
            
            for evt_df in raw_events:
                m = calculate_recovery_metrics(evt_df)
                if m:
                    g = m['group']
                    if g not in grouped_events: grouped_events[g] = []
                    
                    # Add df to metrics for easy access
                    m['df'] = evt_df
                    grouped_events[g].append(m)
            
            if not grouped_events:
                return False, "No se pudieron calcular métricas válidas."
                
            # Select Best per Group (Min Distance)
            best_events = {}
            for g, events in grouped_events.items():
                # Sort by dist_m
                sorted_events = sorted(events, key=lambda x: x['dist_m'])
                best_events[g] = sorted_events[0]
                
            # Reporting
            pdf_name = f"Reporte_Recuperacion_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(self.output_dir, pdf_name)
            
            reporter = PDFReporter(pdf_path)
            
            # Cover
            # Construct pilots_info list for add_header
            pilots_info = [{'name': pilot, 'weight': weight}]
            
            reporter.add_header(moto_data, pilots_info, comments, env_conditions, title="Reporte de Prueba de Recuperación")
            
            # Summary Page (Combined Graph)
            reporter.add_section("Resumen de Recuperación (Mejores Eventos)")
            
            # Combined Plot
            # Create list of DFs for plotting
            plot_events = []
            legends = []
            
            sorted_groups = sorted(best_events.keys())
            
            for g in sorted_groups:
                be = best_events[g]
                plot_events.append({'df': be['df'], 'label': f"Inicio {g} km/h"})
                legends.append(f"Inicio {g} km/h")
            
            # Reconstruct into standard format for plotter
            plot_input = []
            for g in sorted_groups:
                be = best_events[g]
                valid_evt = {
                    'df': be['df'],
                    'metrics': {
                        'start_idx': be['start_idx'],
                        'end_idx': be['end_idx'],
                        'time_s': be['time_s'],
                        'dist_m': be['dist_m'],
                        'avg_acc': be['avg_acc']
                    },
                    'pilot': pilot,
                    'file_type': f"Start {g}km/h"
                }
                plot_input.append(valid_evt)
            
            # Plot 1: Combined Speed
            img_buf = Plotter.plot_speed_vs_time(plot_input, "Comparativa Velocidad vs Tiempo")
            reporter.add_image(img_buf, height=3.5*inch)
            
            # Summary Table
            table_data = [["Evento", "Tiempo (s)", "Distancia (m)", "Top RPM", "V. Inicial (km/h)", "V. Final (km/h)", "Acel Prom (m/s²)"]]
            for g in sorted_groups:
                be = best_events[g]
                table_data.append([
                    f"Inicio {g} km/h",
                    f"{be['time_s']:.2f}",
                    f"{be['dist_m']:.2f}",
                    f"{int(be['top_rpm'])}",
                    f"{be['v_start']:.2f}",
                    f"{be['v_final']:.2f}",
                    f"{be['avg_acc']:.2f}"
                ])
            reporter.add_table(table_data)
            
            reporter.add_page_break()
            
            # Detailed Pages
            for g in sorted_groups:
                be = best_events[g]
                reporter.add_section(f"Detalle: Inicio ~{g} km/h")
                
                valid_evt = {
                    'df': be['df'],
                    'metrics': be
                }
                
                # Speed
                img1 = Plotter.plot_speed_vs_time([valid_evt], f"Velocidad - Grupo {g}")
                reporter.add_image(img1, height=3*inch)
                
                # RPM
                if 'RPM' in be['df'].columns:
                     img_rpm = Plotter.plot_rpm_vs_time(valid_evt, f"RPM - Grupo {g}")
                     reporter.add_image(img_rpm, height=2.6*inch)

                # Accel
                img_acc = Plotter.plot_accel_vs_time(valid_evt, f"Aceleración - Grupo {g}")
                reporter.add_image(img_acc, height=2.6*inch) # Explicit height!
                
                # Stats Table
                # Stats Table
                stats = [
                    ["Tiempo 0-80", "Distancia", "V. Inicial", "V. Final", "Acel Prom", "RPM Max"],
                    [
                        f"{be['time_s']:.2f} s",
                        f"{be['dist_m']:.2f} m",
                        f"{be['v_start']:.2f} km/h",
                        f"{be['v_final']:.2f} km/h",
                        f"{be['avg_acc']:.2f} m/s²",
                        f"{be['top_rpm']:.0f}"
                    ]
                ]
                reporter.add_table(stats)
                reporter.add_page_break()
                
            reporter.build()
            return True, f"Reporte generado: {pdf_path}"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error en control: {str(e)}"
