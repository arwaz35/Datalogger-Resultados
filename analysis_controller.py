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

    def evaluate_data(self, inputs, moto_info, comments, env_conditions=None):

        """
        inputs: List of dicts [{'filepath': str, 'pilot': str, 'weight': str}]
        env_conditions: dict with keys 'temp_amb', 'humidity', 'temp_ground', 'wind_speed', 'wind_dir'
        Returns: success_bool, data_to_preview_or_error_msg
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
                lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'
                export_event_to_csv(event_obj, self.output_dir, moto_info, lugar_name, test_name="Frenado")
        
        # 2. Group strictly by 40 and 60 km/h
        grouped_events = {40: [], 60: []}
        
        for ev in all_events:
            g = ev['metrics'].get('group', 0)
            if g in [40, 60]:
                grouped_events[g].append(ev)
            else:
                pass # Discard outlier speeds
                
        if not grouped_events[40] and not grouped_events[60]:
            return False, "No se encontraron eventos válidos en los rangos de 40 km/h o 60 km/h."
            
        # Select best 3 per group
        best_events_per_group = {}
        for g in [40, 60]:
            if grouped_events[g]:
                sorted_by_dist = sorted(grouped_events[g], key=lambda x: x['metrics']['dist_m'])
                best_events_per_group[g] = sorted_by_dist[:3]
            else:
                best_events_per_group[g] = []
                
        # --- RANKING LOGIC ---
        ranking_entries = []
        if len(inputs) >= 3:
            for g in [40, 60]:
                if best_events_per_group[g]:
                    best_evt = best_events_per_group[g][0]
                    try:
                        moto_w = float(moto_info.get('Peso (Kg)', 0))
                        pilot_w = float(best_evt['weight'])
                        total_w = moto_w + pilot_w
                    except:
                        total_w = 0
                        
                    entry = {
                        'fecha': pd.Timestamp.now().strftime("%Y-%m-%d"),
                        'target_speed': g,
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
                    ranking_entries.append(entry)
                    
        # --- EXTRACCIÓN DE CONTEXTO GLOBAL ---
        from analyzer import get_gps_context
        contexto_gps = {}
        img_buf_gps_main = None
        
        combined_top_events = []
        for g in [40, 60]:
            if best_events_per_group[g]:
                combined_top_events.extend(best_events_per_group[g])
                
        if combined_top_events:
            abs_best = sorted(combined_top_events, key=lambda x: x['metrics']['dist_m'])[0]
            contexto_gps = get_gps_context(abs_best['df'])
            dist_total = contexto_gps.get('distancia_m', 0.0)
            img_buf_gps_main = Plotter.plot_gps_route_simple(abs_best['df'], title=None, distance_m=dist_total)
            
        # --- PREVIEW SECTIONS PREPARATION ---
        sections = []
        
        # --- HOJA 2: Resumen Combinado ---
        table_data_combined = [['Evento', 'Grupo', 'V. Inicial (km/h)', 'V. Final (km/h)', 'Tiempo (s)', 'Distancia (m)', 'Acel Prom (m/s²)', 'Top RPM']]
        
        for g in [40, 60]:
            if best_events_per_group[g]:
                for i, ev in enumerate(best_events_per_group[g]):
                    m = ev['metrics']
                    row = [
                        f"{ev['pilot']} ({i+1})",
                        f"{g} km/h",
                        f"{m['v_start']:.2f}",
                        "0.00",
                        f"{m['time_s']:.2f}",
                        f"{m['dist_m']:.2f}",
                        f"{m['avg_acc']:.2f}",
                        f"{int(m.get('top_rpm', 0))}"
                    ]
                    table_data_combined.append(row)
                    
        if combined_top_events:
            img_buf_combined = Plotter.plot_speed_vs_time(combined_top_events, "Comparativa Velocidad vs Tiempo (Todos los mejores)", figsize=(15, 8))
            
            sections.append({
                "title": "Resumen de Frenado - (Top 3 de 40 km/h y 60 km/h)",
                "images": [img_buf_combined.getvalue() if hasattr(img_buf_combined, 'getvalue') else img_buf_combined],
                "table_data": table_data_combined
            })
        
        # --- HOJA 3,4...: Detalles de Mejor Evento (40 y 60) ---
        for g in [40, 60]:
            if best_events_per_group[g]:
                global_best = best_events_per_group[g][0]
                
                # Mapa individual
                img_buf_gps = Plotter.plot_gps_heatmap(global_best, f"Ruta GPS (Mejor {g} km/h)")
                if img_buf_gps:
                    sections.append({
                        "title": "Ubicación de la prueba",
                        "images": [img_buf_gps.getvalue() if hasattr(img_buf_gps, 'getvalue') else img_buf_gps],
                        "table_data": None
                    })
                
                # Gráficas
                img_buf_v = Plotter.plot_speed_vs_time([global_best], f"Velocidad vs Tiempo (Mejor {g} km/h)")
                img_buf_rpm = None
                if 'RPM' in global_best['df'].columns:
                    img_buf_rpm = Plotter.plot_rpm_vs_time(global_best, f"RPM vs Tiempo (Mejor {g} km/h)")
                img_buf_acc = Plotter.plot_accel_vs_time(global_best, f"Aceleración vs Tiempo (Mejor {g} km/h)")
                
                m = global_best['metrics']
                single_table = [
                    ['V. Inicial (km/h)', 'V. Final (km/h)', 'Tiempo (s)', 'Distancia (m)', 'Acel Prom (m/s²)', 'Top RPM'],
                    [f"{m['v_start']:.2f}", "0.00", f"{m['time_s']:.2f}", f"{m['dist_m']:.2f}", f"{m['avg_acc']:.2f}", f"{int(m.get('top_rpm', 0))}"]
                ]
                
                images = []
                images.append(img_buf_v.getvalue() if hasattr(img_buf_v, 'getvalue') else img_buf_v)
                if img_buf_rpm:
                    images.append(img_buf_rpm.getvalue() if hasattr(img_buf_rpm, 'getvalue') else img_buf_rpm)
                images.append(img_buf_acc.getvalue() if hasattr(img_buf_acc, 'getvalue') else img_buf_acc)
                
                sections.append({
                    "title": f"Gráficas del Mejor Evento a {g} km/h ({global_best['pilot']})",
                    "images": images,
                    "table_data": single_table
                })

        # Save the dataset for the PDF generation
        preview_data = {
            "type": "braking",
            "moto_info": moto_info,
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "ranking_entries": ranking_entries,
            "contexto_gps": contexto_gps,
            "context_map": img_buf_gps_main.getvalue() if (img_buf_gps_main and hasattr(img_buf_gps_main, 'getvalue')) else img_buf_gps_main
        }
        
        return True, preview_data

    def generate_pdf(self, preview_data):
        """
        Generates the PDF based on the preview data prepared by evaluate tools.
        """
        moto_info = preview_data['moto_info']
        inputs = preview_data['inputs']
        comments = preview_data['comments']
        env_conditions = preview_data['env_conditions']
        sections = preview_data['sections']
        
        tipo_prueba_map = {
            'braking': 'Frenado',
            'acceleration': 'Aceleracion',
            'climbing': 'Ascenso',
            'recovery': 'Recuperacion',
            'top_speed': 'Velocidad_Maxima'
        }
        prueba_name = tipo_prueba_map.get(preview_data['type'], 'Prueba')
        
        def clean(s): return "".join([c for c in str(s) if c.isalnum() or c in (' ', '-', '_')]).strip()
        moto_str = clean(moto_info.get('Nombre Comercial', 'Moto'))
        modelo_str = clean(moto_info.get('Código Modelo', 'Modelo'))
        
        # We will collect pilots next, so wait to build filename
        
        filepath = "" # Placeholder
        
        pilots_info = []
        seen_pilots = set()
        for inp in inputs:
            if inp['pilot'] not in seen_pilots:
                pilots_info.append({'name': inp['pilot'], 'weight': inp['weight'], 'altura': inp.get('altura', '0')})
                seen_pilots.add(inp['pilot'])
                
        lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'
        lugar_str = clean(lugar_name)
        fecha_str = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prueba_name}_{moto_str}_{modelo_str}_{lugar_str}_{fecha_str}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        reporter = PDFReporter(filepath)
                
        contexto_gps = preview_data.get('contexto_gps')
        context_map = preview_data.get('context_map')
        
        # Depending on test type, pass the mapped name to formatting logic
        reporter.add_header(
            moto_info, 
            pilots_info, 
            comments, 
            env_conditions, 
            test_type=prueba_name, 
            contexto_gps=contexto_gps, 
            context_map=context_map
        )
        
        for sec in sections:
            reporter.add_page_break()
                
            reporter.add_section(sec['title'])
            
            for img_item in sec.get('images', []):
                # Import io locally for reading bytes
                import io
                # Check if img_item is a dict or raw bytes
                if isinstance(img_item, dict):
                    reporter.add_image(io.BytesIO(img_item['bytes']), space_after=img_item.get('space_after', 12))
                else:
                    reporter.add_image(io.BytesIO(img_item))
                
            if sec.get('table_data'):
                # Pop the header if present to pass separately or pass together
                table = sec['table_data']
                reporter.add_table(table)
                
        success = reporter.build()
        
        if success and preview_data.get('ranking_entries'):
            from data_manager import DataManager
            dm = DataManager()
            for entry in preview_data['ranking_entries']:
                dm.add_ranking_entry(entry)

        return success, filepath

    def evaluate_acceleration_0_80(self, inputs, moto_info, comments, env_conditions=None):
        """
        Processes Acceleration 0-80 km/h test.
        inputs: List of dicts (usually single file)
        Returns: success_bool, data_to_preview_or_error_msg
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
                    lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'
                    export_event_to_csv(event_obj, self.output_dir, moto_info, lugar_name, test_name="Aceleracion")
        
        if not all_events:
            return False, "No se encontraron eventos válidos de Aceleración 0-80 km/h."
            
        # 2. Sort by Best (Minimum Distance)
        # Requirement: "el mejor evento se debe evaluar la menor distancia"
        all_events.sort(key=lambda x: x['metrics']['dist_m'])
        
        # Select top 3
        top_3_events = all_events[:3]
        best_event = all_events[0]
        
        # --- EXTRACCIÓN DE CONTEXTO GLOBAL ---
        from analyzer import get_gps_context
        contexto_gps = get_gps_context(best_event['df'])
        dist_total = contexto_gps.get('distancia_m', 0.0)
        img_buf_gps_main = Plotter.plot_gps_route_simple(best_event['df'], title="Trazado de la Pista", distance_m=dist_total)
        
        # --- PREVIEW SECTIONS PREPARATION ---
        sections = []
        
        # Summary 3 Best Events (Hoja 2)
        img_buf = Plotter.plot_acceleration_comparison(top_3_events, "Comparativa: Velocidad vs Tiempo (Top 3)", figsize=(15, 8))
        
        table_data_summary = [['Evento', 'V. Inicial (km/h)', 'V. Final (km/h)', 'Tiempo (s)', 'Distancia (m)', 'Acel Prom (m/s²)', 'Top RPM']]
        for i, ev in enumerate(top_3_events):
            m = ev['metrics']
            row = [
                f"Evento {ev['id']} ({ev['pilot']})",
                f"{m.get('v_start', 0.0):.2f}",
                f"{m.get('v_final', 80.0):.2f}",
                f"{m['time_s']:.2f}",
                f"{m['dist_m']:.2f}",
                f"{m['avg_acc']:.2f}",
                f"{int(m.get('top_rpm', 0))}"
            ]
            table_data_summary.append(row)
            
        sections.append({
            "title": "Aceleración 0-80 km/h - Resumen 3 Mejores",
            "images": [{'bytes': img_buf.getvalue() if hasattr(img_buf, 'getvalue') else img_buf}],
            "table_data": table_data_summary
        })
        
        # Best Event Details Mapa (Hoja 3)
        img_detail_gps = Plotter.plot_gps_heatmap(best_event, "Ruta GPS (Mejor Evento)")
        if img_detail_gps:
            sections.append({
                "title": "Ubicación de la prueba",
                "images": [{'bytes': img_detail_gps.getvalue() if hasattr(img_detail_gps, 'getvalue') else img_detail_gps}],
                "table_data": None
            })
            
        # Best Event Details Gráficas (Hoja 4)
        img_detail_v = Plotter.plot_acceleration_detailed(best_event, "Análisis Detallado: Velocidad vs Tiempo")
        img_detail_a = Plotter.plot_accel_vs_time(best_event, "Aceleración Promedio vs Tiempo", benchmarks=[0, 20, 40, 60, 80])
        img_detail_rpm = Plotter.plot_rpm_vs_time(best_event, "RPM vs Tiempo", benchmarks=[0, 20, 40, 60, 80])
        
        table_segments = [
            ["Tramo (km/h)", "Tiempo (s)", "Distancia (m)", "Acel Prom (m/s²)", "Top RPM"]
        ]
        
        df = best_event['df']
        start_idx = best_event['metrics']['start_idx']
        try:
            start_pos = df.index.get_loc(start_idx)
        except:
            start_pos = 0
            
        sub = df.iloc[start_pos:]
        
        benchmarks = [0, 20, 40, 60, 80]
        for idx_b in range(len(benchmarks)-1):
            v1 = benchmarks[idx_b]
            v2 = benchmarks[idx_b+1]
            
            if v1 == 0:
                s_idx = sub.index[0]
            else:
                c1 = sub[sub['Velocidad_GPS'] >= v1]
                if c1.empty: continue
                s_idx = c1.index[0]
                
            sub2 = sub.loc[s_idx:]
            c2 = sub2[sub2['Velocidad_GPS'] >= v2]
            if c2.empty: continue
            e_idx = c2.index[0]
            
            seg_slice = df.loc[s_idx:e_idx]
            t_seg = (df.index.get_loc(e_idx) - df.index.get_loc(s_idx)) * 0.1
            d_start = df.loc[s_idx, 'Distancia'] if 'Distancia' in df else 0
            d_end = df.loc[e_idx, 'Distancia'] if 'Distancia' in df else 0
            d_seg = max(0, d_end - d_start)
            a_seg = seg_slice['Accel_X_ms2'].mean() if 'Accel_X_ms2' in seg_slice else 0
            rpm_seg = seg_slice['RPM'].max() if 'RPM' in seg_slice else 0
            
            table_segments.append([
                f"{v1}-{v2}", f"{t_seg:.2f}", f"{d_seg:.2f}", f"{a_seg:.2f}", f"{int(rpm_seg)}"
            ])
            
        images_detalle = []
        images_detalle.append({'bytes': img_detail_v.getvalue() if hasattr(img_detail_v, 'getvalue') else img_detail_v})
        images_detalle.append({'bytes': img_detail_rpm.getvalue() if hasattr(img_detail_rpm, 'getvalue') else img_detail_rpm, 'space_after': 25})
        images_detalle.append({'bytes': img_detail_a.getvalue() if hasattr(img_detail_a, 'getvalue') else img_detail_a, 'space_after': 30})
        
        sections.append({
            "title": f"Hoja 4: Gráficas Mejor Evento - Evento {best_event['id']} ({best_event['pilot']})",
            "images": images_detalle,
            "table_data": table_segments
        })
        
        # Se removieron los gráficos de tramos detallados a petición del usuario.
        
        preview_data = {
            "type": "acceleration",
            "moto_info": moto_info,
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "contexto_gps": contexto_gps,
            "context_map": img_buf_gps_main.getvalue() if (img_buf_gps_main and hasattr(img_buf_gps_main, 'getvalue')) else img_buf_gps_main,
            
            # Additional elements for Excel Generation
            "top_3_events": top_3_events,
            "best_event_segments": table_segments[1:], # skip header
            "img_combined": img_buf.getvalue() if hasattr(img_buf, 'getvalue') else img_buf,
            "img_detail_v": img_detail_v.getvalue() if hasattr(img_detail_v, 'getvalue') else img_detail_v,
            "img_detail_a": img_detail_a.getvalue() if hasattr(img_detail_a, 'getvalue') else img_detail_a,
            "img_detail_rpm": img_detail_rpm.getvalue() if hasattr(img_detail_rpm, 'getvalue') else img_detail_rpm,
            "img_detail_gps": img_detail_gps.getvalue() if (img_detail_gps and hasattr(img_detail_gps, 'getvalue')) else img_detail_gps
        }
        
        return True, preview_data

    # Use the general generate_pdf which handles all basic preview types that are unified
    # But acceleration uses specific sub-headers and formats in its native execution. 
    # Since generate_pdf uses the sections generically (just dumping images and tables), we can reuse it!

    def evaluate_climbing(self, solo_data, passenger_data, moto_info, comments, env_conditions=None):
        """
        Processes Climbing/Ascent Test (0-70m).
        Returns: success_bool, data_to_preview_or_error_msg
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
                        lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'
                        export_event_to_csv({
                            'df': evt_df, 
                            'metrics': metrics, 
                            'pilot': inp_data['pilot'],
                            'weight': inp_data['weight']
                        }, self.output_dir, moto_info, lugar_name, test_name="Ascenso")
                        
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
             
        # --- EXTRACCIÓN DE CONTEXTO GLOBAL ---
        from analyzer import get_gps_context
        contexto_gps = {}
        img_buf_gps_main = None
        
        if combined_best:
            abs_best = sorted(combined_best, key=lambda x: x['metrics']['v_final'], reverse=True)[0]
            contexto_gps = get_gps_context(abs_best['df'])
            dist_total = contexto_gps.get('distancia_m', 0.0)
            img_buf_gps_main = Plotter.plot_gps_route_simple(abs_best['df'], title="Trazado de la Pista", distance_m=dist_total)
             
        # --- PREVIEW SECTIONS PREPARATION ---
        sections = []
        
        # --- Hoja 2: Resumen Combinado ---
        img_buf1 = Plotter.plot_speed_vs_time(combined_best, "Comparativa Velocidad vs Tiempo", figsize=(15, 8))
        
        table_data_combined = [['Evento', 'V. Inicial (km/h)', 'V. Final (km/h)', 'Tiempo (s)', 'Distancia (m)', 'Acel Prom (m/s²)', 'Top RPM']]
        for ev in combined_best:
            m = ev['metrics']
            row = [
                f"{ev['pilot']} ({ev['id']})",
                f"{m.get('v_start', 0.0):.2f}",
                f"{m['v_final']:.2f}",
                f"{m['time_s']:.2f}",
                "70.00",
                f"{m['avg_acc']:.2f}",
                f"{int(m['top_rpm'])}"
            ]
            table_data_combined.append(row)
            
        sections.append({
            "title": "Ascenso 0-70m - Resumen Mejores Eventos",
            "images": [{'bytes': img_buf1.getvalue() if hasattr(img_buf1, 'getvalue') else img_buf1}],
            "table_data": table_data_combined
        })
        
        # --- Detalles de Mejor Evento Solo ---
        if best_solo:
            bs = best_solo[0]
            # Hoja impar: Mapa GPS
            img_gps = Plotter.plot_gps_heatmap(bs, "Ruta GPS (Mejor Evento Solo)")
            if img_gps:
                sections.append({
                    "title": "Ubicación de la prueba",
                    "images": [{'bytes': img_gps.getvalue() if hasattr(img_gps, 'getvalue') else img_gps}],
                    "table_data": None
                })
                
            # Hoja par: Gráficas Individuales
            img_bs1 = Plotter.plot_climbing_detailed(bs, "Velocidad vs Tiempo (Detalle)")
            img_rpm = Plotter.plot_rpm_vs_time(bs, "RPM vs Tiempo", markers=bs['metrics'].get('markers'))
            img_acc = Plotter.plot_accel_vs_time(bs, "Aceleración vs Tiempo", markers=bs['metrics'].get('markers'))
            
            m = bs['metrics']
            t2 = [
                ['V. Inicial (km/h)', 'V. Final (km/h)', 'Tiempo (s)', 'Distancia (m)', 'Acel Prom (m/s²)', 'Top RPM'],
                [f"{m.get('v_start', 0.0):.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}", "70.00", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]
            ]
            
            images_detalle = []
            images_detalle.append({'bytes': img_bs1.getvalue() if hasattr(img_bs1, 'getvalue') else img_bs1})
            images_detalle.append({'bytes': img_rpm.getvalue() if hasattr(img_rpm, 'getvalue') else img_rpm, 'space_after': 25})
            images_detalle.append({'bytes': img_acc.getvalue() if hasattr(img_acc, 'getvalue') else img_acc, 'space_after': 30})
                
            sections.append({
                "title": f"Gráficas Mejor Evento Solo ({bs['pilot']})",
                "images": images_detalle,
                "table_data": t2
            })

        # --- Detalles de Mejor Evento Pasajero ---
        if best_pass:
            bp = best_pass[0]
            # Hoja impar: Mapa GPS
            img_gps_p = Plotter.plot_gps_heatmap(bp, "Ruta GPS (Mejor Evento Pasajero)")
            if img_gps_p:
                sections.append({
                    "title": "Ubicación de la prueba",
                    "images": [{'bytes': img_gps_p.getvalue() if hasattr(img_gps_p, 'getvalue') else img_gps_p}],
                    "table_data": None
                })
                
            # Hoja par: Gráficas Individuales
            img_bp1 = Plotter.plot_climbing_detailed(bp, "Velocidad vs Tiempo (Detalle)")
            img_rpm_p = Plotter.plot_rpm_vs_time(bp, "RPM vs Tiempo", markers=bp['metrics'].get('markers'))
            img_acc_p = Plotter.plot_accel_vs_time(bp, "Aceleración vs Tiempo", markers=bp['metrics'].get('markers'))
            
            m = bp['metrics']
            t3 = [
                ['V. Inicial (km/h)', 'V. Final (km/h)', 'Tiempo (s)', 'Distancia (m)', 'Acel Prom (m/s²)', 'Top RPM'],
                [f"{m.get('v_start', 0.0):.2f}", f"{m['v_final']:.2f}", f"{m['time_s']:.2f}", "70.00", f"{m['avg_acc']:.2f}", f"{int(m['top_rpm'])}"]
            ]
            
            images_detalle = []
            images_detalle.append({'bytes': img_bp1.getvalue() if hasattr(img_bp1, 'getvalue') else img_bp1})
            images_detalle.append({'bytes': img_rpm_p.getvalue() if hasattr(img_rpm_p, 'getvalue') else img_rpm_p, 'space_after': 25})
            images_detalle.append({'bytes': img_acc_p.getvalue() if hasattr(img_acc_p, 'getvalue') else img_acc_p, 'space_after': 30})
                
            sections.append({
                "title": f"Gráficas Mejor Evento Pasajero ({bp['pilot']})",
                "images": images_detalle,
                "table_data": t3
            })
            
        inputs = []
        if solo_data: inputs.append({'pilot': f"Solo: {solo_data['pilot']}", 'weight': solo_data['weight']})
        if passenger_data: inputs.append({'pilot': f"Pass: {passenger_data['pilot']} + {passenger_data.get('passenger', '')}", 'weight': passenger_data['weight']})

        preview_data = {
            "type": "climbing",
            "moto_info": moto_info,
            "inputs": inputs,
            "comments": comments,
            "env_conditions": env_conditions,
            "sections": sections,
            "contexto_gps": contexto_gps,
            "context_map": img_buf_gps_main.getvalue() if (img_buf_gps_main and hasattr(img_buf_gps_main, 'getvalue')) else img_buf_gps_main
        }
        
        return True, preview_data

    def evaluate_recovery(self, data, moto_data, comments, env_conditions):
        """
        Process Recovery Test (Single File).
        Returns: success_bool, data_to_preview_or_error_msg
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
                
            # Export CSV for the best events (like other modules do)
            from analyzer import export_event_to_csv
            lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'
            
            for g, be in best_events.items():
                # Construct event object for CSV export
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
                    'weight': weight
                }
                export_event_to_csv(valid_evt, self.output_dir, moto_data, lugar_name, test_name="Recuperacion")
                
            # --- EXTRACCIÓN DE CONTEXTO GLOBAL ---
            from analyzer import get_gps_context
            contexto_gps = {}
            img_buf_gps_main = None
            
            # Reconstruct into standard format for plotter
            plot_input = []
            sorted_groups = sorted(best_events.keys())
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
                
            if plot_input:
                abs_best = sorted(plot_input, key=lambda x: x['metrics']['dist_m'])[0]
                contexto_gps = get_gps_context(abs_best['df'])
                dist_total = contexto_gps.get('distancia_m', 0.0)
                img_buf_gps_main = Plotter.plot_gps_route_simple(abs_best['df'], title="Trazado de la Pista", distance_m=dist_total)
                
            # --- PREVIEW SECTIONS PREPARATION ---
            sections = []
            
            # --- Combined Page (Hoja 2) ---
            img_buf = Plotter.plot_speed_vs_time(plot_input, "Comparativa Velocidad vs Tiempo", figsize=(15, 8))
            
            table_data = [["Evento", "V. Inicial (km/h)", "V. Final (km/h)", "Tiempo (s)", "Distancia (m)", "Acel Prom (m/s²)", "Top RPM"]]
            for g in sorted_groups:
                be = best_events[g]
                table_data.append([
                    f"Inicio {g} km/h",
                    f"{be['v_start']:.2f}",
                    f"{be['v_final']:.2f}",
                    f"{be['time_s']:.2f}",
                    f"{be['dist_m']:.2f}",
                    f"{be['avg_acc']:.2f}",
                    f"{int(be['top_rpm'])}"
                ])
                
            sections.append({
                "title": "Recuperación - Resumen Mejores Eventos",
                "images": [{'bytes': img_buf.getvalue() if hasattr(img_buf, 'getvalue') else img_buf}],
                "table_data": table_data
            })
            
            # --- Detailed Pages (Hoja 3, 4, etc) ---
            for g in sorted_groups:
                be = best_events[g]
                valid_evt = {
                    'df': be['df'],
                    'metrics': be
                }
                
                # Page impar (Mapa)
                img_gps = Plotter.plot_gps_heatmap(valid_evt, f"Ruta GPS - Grupo {g}")
                if img_gps:
                    sections.append({
                        "title": "Ubicación de la prueba",
                        "images": [{'bytes': img_gps.getvalue() if hasattr(img_gps, 'getvalue') else img_gps}],
                        "table_data": None
                    })
                
                # Page par (Gráficas)
                img1 = Plotter.plot_speed_vs_time([valid_evt], f"Velocidad - Grupo {g}")
                img_rpm = None
                if 'RPM' in be['df'].columns:
                     img_rpm = Plotter.plot_rpm_vs_time(valid_evt, f"RPM - Grupo {g}")
                     
                img_acc = Plotter.plot_accel_vs_time(valid_evt, f"Aceleración - Grupo {g}")
                
                stats = [
                    ["V. Inicial (km/h)", "V. Final (km/h)", "Tiempo (s)", "Distancia (m)", "Acel Prom (m/s²)", "Top RPM"],
                    [
                        f"{be['v_start']:.2f}",
                        f"{be['v_final']:.2f}",
                        f"{be['time_s']:.2f}",
                        f"{be['dist_m']:.2f}",
                        f"{be['avg_acc']:.2f}",
                        f"{int(be['top_rpm'])}"
                    ]
                ]
                
                images_detalle = []
                images_detalle.append({'bytes': img1.getvalue() if hasattr(img1, 'getvalue') else img1})
                if img_rpm:
                    images_detalle.append({'bytes': img_rpm.getvalue() if hasattr(img_rpm, 'getvalue') else img_rpm, 'space_after': 25})
                images_detalle.append({'bytes': img_acc.getvalue() if hasattr(img_acc, 'getvalue') else img_acc, 'space_after': 30})
                
                sections.append({
                    "title": f"Gráficas Detalle: Inicio ~{g} km/h ({pilot})",
                    "images": images_detalle,
                    "table_data": stats
                })

            preview_data = {
                "type": "recovery",
                "moto_info": moto_data,
                "inputs": [data], # unified array pattern
                "comments": comments,
                "env_conditions": env_conditions,
                "sections": sections,
                "contexto_gps": contexto_gps,
                "context_map": img_buf_gps_main.getvalue() if (img_buf_gps_main and hasattr(img_buf_gps_main, 'getvalue')) else img_buf_gps_main
            }
            
            return True, preview_data
            
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error en control: {str(e)}"

    def evaluate_top_speed(self, data, moto_data, comments, env_conditions):
        """
        Process Top Speed Test (Single File).
        Returns: success_bool, data_to_preview_or_error_msg
        """
        try:
            from analyzer import extract_top_speed_events, calculate_top_speed_metrics, export_event_to_csv
            
            filepath = data['filepath']
            pilot = data['pilot']
            weight = data['weight']
            
            df = parse_csv(filepath)
            df = convert_units(df)
            
            raw_events = extract_top_speed_events(df, target_distance=200)
            
            if not raw_events:
                return False, "No se encontraron eventos de Velocidad Máxima válidos (Pulsador=100 -> 200m)."
                
            valid_events = []
            for i, evt_df in enumerate(raw_events):
                m = calculate_top_speed_metrics(evt_df)
                if m:
                    valid_events.append({
                        'df': evt_df,
                        'metrics': m,
                        'pilot': pilot,
                        'weight': weight,
                        'id': i+1
                    })
            
            if not valid_events:
                return False, "No se pudieron calcular métricas válidas."
                
            # Sort by best (Highest V. Maxima)
            valid_events.sort(key=lambda x: x['metrics']['v_max'], reverse=True)
            best_event = valid_events[0]
            top_3_events = valid_events[:3]
            
            # Export CSV for the best event
            lugar_name = env_conditions.get('lugar', {}).get('Nombre', 'SinLugar') if env_conditions else 'SinLugar'
            export_event_to_csv(best_event, self.output_dir, moto_data, lugar_name, test_name="Velocidad_Maxima")
            
            # --- EXTRACCIÓN DE CONTEXTO GLOBAL ---
            from analyzer import get_gps_context
            contexto_gps = get_gps_context(best_event['df'])
            dist_total = contexto_gps.get('distancia_m', 0.0)
            img_buf_gps_main = Plotter.plot_gps_route_simple(best_event['df'], title="Trazado de la Pista", distance_m=dist_total)
            
            # --- PREVIEW SECTIONS PREPARATION ---
            sections = []
            
            # Comparative Graph for Top 3 Events
            img_buf = Plotter.plot_speed_vs_time(top_3_events, "Comparativa Velocidad - Mejores Eventos", figsize=(15, 8))
            
            # Standard Metrics Table
            m = best_event['metrics']
            stats = [
                ["V. Inicial (km/h)", "V. Final (km/h)", "Tiempo (s)", "Distancia (m)", "Acel Prom (m/s²)", "Top RPM"],
                [
                    f"{m['v_start']:.2f}",
                    f"{m['v_final']:.2f}",
                    f"{m['time_s']:.2f}",
                    f"{m['dist_m']:.2f}",
                    f"{m['avg_acc']:.2f}",
                    f"{int(m['top_rpm'])}"
                ]
            ]
            
            # Additional detail metric just for top speed explicitly
            stats_extra = [
                ["Velocidad Máxima Alcanzada"],
                [f"{m['v_max']:.2f} km/h"]
            ]
            
            img_v = Plotter.plot_speed_vs_time([best_event], "Velocidad vs Tiempo (Velocidad Máxima)", figsize=(15, 8))
            
            img_rpm = None
            if 'RPM' in best_event['df'].columns:
                 img_rpm = Plotter.plot_rpm_vs_time(best_event, "RPM vs Tiempo")

            img_acc = Plotter.plot_accel_vs_time(best_event, "Aceleración vs Tiempo")
            
            # Hoja 2: Resumen V Max
            sections.append({
                "title": f"Velocidad Máxima - Métrica Principal ({pilot})",
                "images": [{'bytes': img_v.getvalue() if hasattr(img_v, 'getvalue') else img_v}],
                "table_data": stats_extra
            })
            
            # Hoja 3: Mapa GPS
            img_gps = Plotter.plot_gps_heatmap(best_event, "Ruta GPS (Velocidad Máxima)")
            if img_gps:
                sections.append({
                    "title": "Ubicación de la prueba",
                    "images": [img_gps.getvalue() if hasattr(img_gps, 'getvalue') else img_gps],
                    "table_data": None
                })
            
            # Hoja 4: Gráficas detalladas
            images = []
            if img_rpm:
                images.append(img_rpm.getvalue() if hasattr(img_rpm, 'getvalue') else img_rpm)
            images.append(img_acc.getvalue() if hasattr(img_acc, 'getvalue') else img_acc)
            
            sections.append({
                "title": f"Hoja 4: Gráficas Secundarias",
                "images": images,
                "table_data": stats
            })

            preview_data = {
                "type": "top_speed",
                "moto_info": moto_data,
                "inputs": [data],
                "comments": comments,
                "env_conditions": env_conditions,
                "sections": sections,
                "contexto_gps": contexto_gps,
                "context_map": img_buf_gps_main.getvalue() if (img_buf_gps_main and hasattr(img_buf_gps_main, 'getvalue')) else img_buf_gps_main,
                "top_events": top_3_events,
                "img_combined": img_buf.getvalue() if hasattr(img_buf, 'getvalue') else img_buf,
                "img_detail_gps": img_gps.getvalue() if (img_gps and hasattr(img_gps, 'getvalue')) else img_gps,
                "img_detail_v": img_v.getvalue() if hasattr(img_v, 'getvalue') else img_v,
                "img_detail_a": img_acc.getvalue() if hasattr(img_acc, 'getvalue') else img_acc,
                "img_detail_rpm": img_rpm.getvalue() if (img_rpm and hasattr(img_rpm, 'getvalue')) else img_rpm
            }
            
            return True, preview_data
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error en control: {str(e)}"

