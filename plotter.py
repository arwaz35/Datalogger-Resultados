import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io

class Plotter:
    @staticmethod
    def plot_speed_vs_time(events, title, filename_prefix="plot_speed", figsize=(15, 6)):
        """
        Generates Type 1 graph: Speed vs Time for multiple events.
        Target: Identify braking start (Red Dotted Line) and stop (Red Dotted Line).
        Returns a list of image bytes or paths.
        For report generation, we often return BytesIO objects.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        for i, event in enumerate(events):
            # Normalize time to start at 0 for the braking event
            # event has 'start_idx' which is the detected braking start
            # We need to map this.
            # However, the event df passed here might be the raw cut. 
            # We assume 'events' here is a list of dicts or objects containing the DF and metadata.
            
            # If events is just a list of DataFrames, we plot them raw relative to their cut.
            # But the requirement says "Analyze column Velocidad_GPS vs Time".
            # "Identify exact point where moto starts braking... taking this as time zero".
            
            df = event['df']
            start_idx = event['metrics']['start_idx']
            end_idx = event['metrics']['end_idx']
            
            # Create relative time axis
            # We want start_idx to be t=0
            # Time step is 0.1s
            
            # Indices relative to the DF
            # The DF index might be absolute from original file, so we use reset_index or array pos
            
            # Let's perform a reset index for plotting safety
            df_reset = df.reset_index(drop=True)
            
            # Map absolute indices to relative indices in this new DF
            # We need to find the integer position of start_idx in df
            # This is tricky if start_idx is from original DF.
            # Assumption: metrics['start_idx'] is the index label.
            
            try:
                start_pos = df.index.get_loc(start_idx)
                end_pos = df.index.get_loc(end_idx)
            except KeyError:
                # Fallback if indices don't match (shouldn't happen if logic is consistent)
                start_pos = 0
                end_pos = len(df) - 1

            # Generate time array relative to start_pos
            # t = (index - start_pos) * 0.1
            time_axis = (df_reset.index - start_pos) * 0.1
            
            # Plot Speed
            label = f"Event {i+1} ({event.get('pilot', 'Unknown')})"
            ax.plot(time_axis, df_reset['Velocidad_GPS'], label=label)
            
            # Add markers for this specific event if it's the "Main" one or if requested
            # For the combined plot, complex markers might clog it. 
            # Requirement: "Línea puntuada roja vertical en start y end"
            
            # We can only perform the vertical lines if this is a single event plot 
            # OR if we align all events at t=0 (which we did).
            
            # If we align them, the start line is always at t=0.
            
        ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_')
        
        # for multiple events, end times vary, so we might not draw end lines for all, 
        # or we draw them all.
        if len(events) == 1:
            # Draw end line
             # Re-calculate end time for the single event
            df = events[0]['df']
            start_idx = events[0]['metrics']['start_idx']
            end_idx = events[0]['metrics']['end_idx']
            start_pos = df.index.get_loc(start_idx)
            end_pos = df.index.get_loc(end_idx)
            end_time = (end_pos - start_pos) * 0.1
            ax.axvline(x=end_time, color='#555555', linestyle='--', label='_nolegend_')

            # Annotations on the red lines
            # First line: Speed (Start)
            speed_at_start = df.loc[start_idx, 'Velocidad_GPS']
            # Position slightly above the start point, Horizontal, Boxed like the end label
            ax.text(-0.05, speed_at_start, f"V: {speed_at_start:.1f} km/h", 
                    rotation=0, 
                    verticalalignment='bottom', 
                    horizontalalignment='right',
                    fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

            # Second line: Metrics (End)
            metrics = events[0]['metrics']
            label_text = f"D: {metrics['dist_m']:.2f} m\nT: {metrics['time_s']:.2f} s\nA: {metrics['avg_acc']:.2f} m/s²"
            # Position at the end line, mid-height or top
            # We use a bbox for readability
            y_pos = (df['Velocidad_GPS'].max() + speed_at_start) / 2 # Mid-height of the maneuver
            ax.text(end_time - 0.1, y_pos, label_text, 
                    verticalalignment='center', 
                    horizontalalignment='right',
                    fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Velocidad (km/h)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def plot_rpm_vs_time(event, title, benchmarks=None, markers=None, figsize=(15, 3)):
        """
        Generates RPM vs Time graph.
        """
        df = event['df']
        start_idx = event['metrics']['start_idx']
        
        try:
            start_pos = df.index.get_loc(start_idx)
        except:
             start_pos = 0
             
        df_reset = df.reset_index(drop=True)
        time_axis = (df_reset.index - start_pos) * 0.1
        
        # Reducir la altura a 3 para agrupar en una sola hoja PDF, o ajustable por kwarg
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot RPM
        if 'RPM' in df_reset.columns:
            ax.plot(time_axis, df_reset['RPM'], label='RPM', color='purple', linewidth=1.5)
            
        # Reference Lines (Start and End)
        # Start (0)
        ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_', linewidth=1.5)
        # Label Start RPM
        if 0 <= start_pos < len(df) and 'RPM' in df.columns:
             rpm_val = df.iloc[start_pos]['RPM']
             ax.text(0, rpm_val, f"{int(rpm_val)}", fontsize=9, 
                     verticalalignment='bottom', horizontalalignment='right',
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # End
        if 'end_idx' in event['metrics']:
            end_idx = event['metrics']['end_idx']
            try:
                end_pos = df.index.get_loc(end_idx)
                t_end = (end_pos - start_pos) * 0.1
                ax.axvline(x=t_end, color='#555555', linestyle='--', label='_nolegend_', linewidth=1.5)
                
                # Label End RPM
                if 0 <= end_pos < len(df) and 'RPM' in df.columns:
                    rpm_val = df.iloc[end_pos]['RPM']
                    ax.text(t_end, rpm_val, f"{int(rpm_val)}", fontsize=9, 
                            verticalalignment='bottom', horizontalalignment='right',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            except: pass
        
        # Benchmarks (Optional) - Speed based
        if benchmarks:
            colors = ['#555555'] * len(benchmarks)
            
            # Search relative to start
            try:
                sub = df.iloc[start_pos:]
                for i, bm in enumerate(benchmarks):
                    if bm == 0:
                        candidates = [start_idx]
                    else:
                        candidates = sub[sub['Velocidad_GPS'] >= bm].index.tolist()
                        
                    if candidates:
                        idx = candidates[0]
                        t = (df.index.get_loc(idx) - start_pos) * 0.1
                        ax.axvline(x=t, color=colors[i], linestyle='--', alpha=0.7, linewidth=1.5)
                        
                        # Add RPM Label
                        if 'RPM' in df.columns:
                            rpm_val = df.loc[idx, 'RPM']
                            label_txt = f"{int(rpm_val)}"
                            
                            # Position: intersection point
                            # Add a small offset or just dot?
                            # User asked for "labels... with the same format as speed graph"
                            # Let's put a box near the intersection
                            ax.text(t, rpm_val, label_txt, fontsize=9, 
                                    verticalalignment='bottom', horizontalalignment='right',
                                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            except: pass

        # Markers (Optional) - Distance based (Ascent)
        if markers:
            # markers is dict {10: {'time': ..., ...}}
            sorted_dists = sorted(markers.keys())
            for d in sorted_dists:
                m_data = markers[d]
                t_val = m_data['time']
                
                # Line
                ax.axvline(x=t_val, color='#555555', linestyle='--', alpha=0.7, linewidth=1.5)
                
                # Label (RPM intersection)
                # We need to find the RPM value at this time
                # converting t_val back to index relative to start_pos
                # index_offset = t_val / 0.1
                # abs_index = start_pos + index_offset
                try:
                    rel_idx = int(round(t_val / 0.1))
                    frame_idx = start_pos + rel_idx
                    
                    # Use iloc for position-based access
                    if 0 <= frame_idx < len(df):
                        rpm_val = df.iloc[frame_idx]['RPM'] if 'RPM' in df.columns else 0
                        label_txt = f"{int(rpm_val)}"
                        
                        ax.text(t_val, rpm_val, label_txt, fontsize=9,
                                verticalalignment='bottom', horizontalalignment='right',
                                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                except: pass

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("RPM")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight') # removed dpi=200 to match others
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def plot_accel_vs_time(event, title, benchmarks=None, markers=None, figsize=(15, 3)):
        """
        Generates Type 2: Accel vs Time + Avg Accel.
        Optional benchmarks list [0, 20...].
        """
        df = event['df']
        start_idx = event['metrics']['start_idx']
        end_idx = event['metrics']['end_idx']
        
        try:
            start_pos = df.index.get_loc(start_idx)
        except:
             start_pos = 0
             
        df_reset = df.reset_index(drop=True)
        time_axis = (df_reset.index - start_pos) * 0.1
        
        fig, ax = plt.subplots(figsize=figsize)
        # Use raw values (keep negative if negative)
        df_reset['Accel_X_Plot'] = df_reset['Accel_X_ms2']
        
        time_axis = (df_reset.index - start_pos) * 0.1
        
        # Reducir la altura a 3 para agrupar en una sola hoja PDF
        fig, ax = plt.subplots(figsize=(15, 3))
        
        # Plot Accel X (Original/Raw)
        ax.plot(time_axis, df_reset['Accel_X_Plot'], label='Aceleración (m/s²)', color='blue', linewidth=1.5)
        
        # Plot Cumulative Average
        # Restriction: Only plot valid braking/accel phase (Start to End)
        try:
            end_pos = df.index.get_loc(end_idx)
        except:
            end_pos = len(df) - 1

        braking_slice = df_reset.iloc[start_pos : end_pos + 1].copy()
        braking_slice['Cum_Avg'] = braking_slice['Accel_X_Plot'].expanding().mean()
        
        slice_time_axis = time_axis[start_pos : end_pos + 1]
        ax.plot(slice_time_axis, braking_slice['Cum_Avg'], label='Promedio Acumulado', color='red', linestyle='--', linewidth=1.5)
        
        # Reference Lines (Start and End)
        # Start (0) - Remove label 'Inicio'
        ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_', linewidth=1.5)
        
        # End - Remove label 'Fin'
        t_end = (end_pos - start_pos) * 0.1
        ax.axvline(x=t_end, color='#555555', linestyle='--', label='_nolegend_', linewidth=1.5)
        
        # Benchmarks (Optional)
        if benchmarks:
            colors = ['#555555'] * len(benchmarks)
            
            # Search relative to start
            try:
                sub = df.iloc[start_pos:]
                for i, bm in enumerate(benchmarks):
                    if bm == 0:
                        candidates = [start_idx]
                    else:
                        candidates = sub[sub['Velocidad_GPS'] >= bm].index.tolist()
                        
                    if candidates:
                        idx = candidates[0]
                        t = (df.index.get_loc(idx) - start_pos) * 0.1
                        # Avoid duplicating start/end lines if detected
                        if abs(t) > 0.05 and abs(t - t_end) > 0.05:
                            ax.axvline(x=t, color=colors[i], linestyle='--', alpha=0.7, linewidth=1.5)
            except: pass

        # Markers (Optional) - Distance based
        if markers:
            sorted_dists = sorted(markers.keys())
            for d in sorted_dists:
                m_data = markers[d]
                t_val = m_data['time']
                
                # Line
                # Avoid dupes with end line (70m is likely end)
                if abs(t_val - t_end) > 0.05:
                     ax.axvline(x=t_val, color='#555555', linestyle='--', alpha=0.7, linewidth=1.5)

        # Add single value annotation
        avg_val_metric = event['metrics']['avg_acc']
        ax.text(0.05, 0.95, f"Promedio Global: {avg_val_metric:.2f} m/s²", transform=ax.transAxes, 
                verticalalignment='top', fontsize=12, # Match standard size
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Aceleración (m/s²)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

        ax.set_xlabel("Tiempo (s)", fontsize=10)
        ax.set_ylabel("Aceleración (m/s²)", fontsize=10)
        ax.set_title(title, fontsize=12)
        ax.legend(fontsize=9)
        ax.tick_params(axis='both', which='major', labelsize=9)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def plot_acceleration_comparison(events, title, figsize=(15, 6)):
        """
        Combined Speed vs Time for Acceleration events.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        for i, event in enumerate(events):
            df = event['df']
            start_idx = event['metrics']['start_idx']
            
            try:
                start_pos = df.index.get_loc(start_idx)
            except:
                start_pos = 0
            
            df_reset = df.reset_index(drop=True)
            time_axis = (df_reset.index - start_pos) * 0.1
            
            label = f"Event {event['id']} ({event['pilot']})"
            ax.plot(time_axis, df_reset['Velocidad_GPS'], label=label)
            
        # Draw Start Line (0) and End Markers
        ax.axvline(x=0, color='#555555', linestyle='--', label='_nolegend_')
        
        # Annotate end points
        for ev in events:
            df = ev['df']
            end_idx = ev['metrics']['end_idx']
            start_idx = ev['metrics']['start_idx']
            
            try:
                s = df.index.get_loc(start_idx)
                e = df.index.get_loc(end_idx)
                t_end = (e - s) * 0.1
                v_end = df.loc[end_idx, 'Velocidad_GPS']
                
                # Marker
                # REMOVED PER USER REQUEST
                # ax.plot(t_end, v_end, 'ro')
                
                # Label
                # REMOVED PER USER REQUEST
                # m = ev['metrics']
                # txt = f"t:{m['time_s']:.2f}s\nd:{m['dist_m']:.2f}m"
                # ax.text(t_end, v_end+2, txt, fontsize=9, bbox=dict(facecolor='white', alpha=0.7))
            except: pass

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Velocidad (km/h)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def plot_acceleration_detailed(event, title):
        """
        Detailed Speed vs Time with markers at 0, 20, 40, 60, 80 km/h.
        """
        fig, ax = plt.subplots(figsize=(15, 6))
        
        df = event['df']
        start_idx = event['metrics']['start_idx']
        
        try:
            start_pos = df.index.get_loc(start_idx)
        except:
            start_pos = 0
            
        df_reset = df.reset_index(drop=True)
        time_axis = (df_reset.index - start_pos) * 0.1
        
        ax.plot(time_axis, df_reset['Velocidad_GPS'], label='Velocidad', color='blue')
        
        # Benchmarks
        benchmarks = [0, 20, 40, 60, 80]
        colors = ['#555555', '#555555', '#555555', '#555555', '#555555']
        
        # Determine strict monotonic segments? Or just search first occurence
        # Search relative to start
        sub = df.iloc[start_pos:]
        
        for i, bm in enumerate(benchmarks):
            # Find first point >= bm
            # Allow some tolerance for 0
            if bm == 0:
                candidates = [start_idx] # Start is 0 (or close)
            else:
                candidates = sub[sub['Velocidad_GPS'] >= bm].index.tolist()
                
            if candidates:
                idx = candidates[0]
                # Map to time
                pos = df.index.get_loc(idx)
                t = (pos - start_pos) * 0.1
                v = df.loc[idx, 'Velocidad_GPS']
                
                # Line
                ax.axvline(x=t, color=colors[i], linestyle='--')
                
                # Label
                # Calculate metrics from Previous Benchmark to Current?
                # or from 0?
                # Requirement: "Cada linea debe tener las etiquetas tiempo, velocidad final, aceleracion promedio y la distancia recorrida"
                # Implies Cumulative from Start? Or Segment?
                # "tabla resumen debe contener estos datos Tambien" -> Segment table was requested separately.
                # Let's show Cumulative metrics at each line.
                
                # Calc Cumulative
                # Time
                cum_t = t
                
                # Dist
                d_start = df.loc[start_idx, 'Distancia'] if 'Distancia' in df else 0
                d_curr = df.loc[idx, 'Distancia'] if 'Distancia' in df else 0
                cum_d = d_curr - d_start
                if cum_d < 0: cum_d = 0 # simple fallback
                
                # Accel (Avg from 0 to Current Benchmark)
                # Requirement: Use cumulative average of Accel_X
                # Ensure we take the slice from start_idx up to current idx (inclusive)
                # Note: This is exactly what expanding().mean() does
                slice_0_curr = df.loc[start_idx:idx]
                if 'Accel_X_ms2' in slice_0_curr.columns:
                    cum_a = slice_0_curr['Accel_X_ms2'].mean()
                else:
                    # Fallback to GPS
                    if t > 0:
                        cum_a = (v / 3.6) / t
                    else:
                        cum_a = 0
                    
                label_txt = f"{bm}km/h\nt:{cum_t:.2f}s\nd:{cum_d:.2f}m\na:{cum_a:.2f}m/s²"
                
                # Position text
                y_txt = 10 + (i*15) # Stagger
                ax.text(t + 0.1, y_txt, label_txt, fontsize=9, 
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Velocidad (km/h)")
        ax.set_title(title)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def plot_segment_group(event, segments, title):
        """
        Generates grid for specific segments (e.g. 0-20, 20-40).
        Layout: 
        Row 0: Velocity Plots
        Row 1: Acceleration Plots
        Row 2: Tables
        """
        n_cols = len(segments)
        # Height: Vel (4), Acc (4), Table (2) => 10 per group?
        fig = plt.figure(figsize=(8 * n_cols, 10))
        gs = fig.add_gridspec(3, n_cols, height_ratios=[3, 3, 1], hspace=0.4, wspace=0.3)
        
        df = event['df']
        start_idx = event['metrics']['start_idx']
        base_pos = df.index.get_loc(start_idx)
        df_run = df.iloc[base_pos:]
        
        for col, (v1, v2) in enumerate(segments):
            ax_v = fig.add_subplot(gs[0, col])
            ax_a = fig.add_subplot(gs[1, col])
            ax_t = fig.add_subplot(gs[2, col])
            ax_t.axis('off')
            
            # --- EXTRACT DATA ---
            if v1 == 0:
                s_idx = df_run.index[0]
            else:
                c1 = df_run[df_run['Velocidad_GPS'] >= v1]
                if c1.empty: continue
                s_idx = c1.index[0]
                
            run_2 = df_run.loc[s_idx:]
            c2 = run_2[run_2['Velocidad_GPS'] >= v2]
            if c2.empty: continue
            e_idx = c2.index[0]
            
            s_pos = df.index.get_loc(s_idx)
            e_pos = df.index.get_loc(e_idx)
            vis_s = max(0, s_pos - 2)
            vis_e = min(len(df), e_pos + 3)
            
            seg_df = df.iloc[vis_s : vis_e].copy()
            t_axis = (pd.RangeIndex(start=vis_s, stop=vis_e, step=1) - s_pos) * 0.1
            
            # --- CALCULATE METRICS ---
            t_seg = (e_pos - s_pos) * 0.1
            val_start = df.loc[s_idx, 'Velocidad_GPS']
            val_end = df.loc[e_idx, 'Velocidad_GPS']
            
            # Distance
            d_start = df.loc[s_idx, 'Distancia'] if 'Distancia' in df else 0
            d_end = df.loc[e_idx, 'Distancia'] if 'Distancia' in df else 0
            dist_seg = d_end - d_start
            if dist_seg < 0: dist_seg = 0
            
            # Accel
            # Accel
            acc_slice = df.loc[s_idx:e_idx] # inclusive slice
            if 'Accel_X_ms2' in acc_slice.columns:
                 acc_seg = acc_slice['Accel_X_ms2'].mean()
            else:
                 if t_seg > 0:
                     acc_seg = ((val_end/3.6) - (val_start/3.6)) / t_seg
                 else:
                     acc_seg = 0
            
            # --- PLOT VELOCITY ---
            ax_v.plot(t_axis, seg_df['Velocidad_GPS'], color='blue', label='Velocidad')
            ax_v.set_title(f"Tramo {v1}-{v2} km/h (Velocidad)")
            ax_v.set_ylabel("km/h")
            ax_v.grid(True, linestyle=':', alpha=0.6)
            ax_v.axvline(0, color='#555555', linestyle='--')
            ax_v.axvline(t_seg, color='#555555', linestyle='--')
            
            # --- PLOT ACCEL ---
            acc_col = 'Accel_X_ms2' if 'Accel_X_ms2' in seg_df else 'Accel_X'
            if acc_col in seg_df:
                ax_a.plot(t_axis, seg_df[acc_col], color='orange', label='Aceleración')
            ax_a.set_title(f"Tramo {v1}-{v2} km/h (Aceleración)")
            ax_a.set_ylabel("m/s²")
            ax_a.set_xlabel("Tiempo Relativo (s)")
            ax_a.grid(True, linestyle=':', alpha=0.6)
            ax_a.axvline(0, color='#555555', linestyle='--')
            ax_a.axvline(t_seg, color='#555555', linestyle='--')
            
            # --- TABLE ---
            table_data = [
                ["Métrica", "Valor"],
                ["Tiempo", f"{t_seg:.2f} s"],
                ["Distancia", f"{dist_seg:.2f} m"],
                ["Vel Inicial", f"{val_start:.2f} km/h"],
                ["Vel Final", f"{val_end:.2f} km/h"],
                ["Acel Prom", f"{acc_seg:.2f} m/s²"]
            ]
            
            # Create Table
            tbl = ax_t.table(cellText=table_data, loc='center', cellLoc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1, 1.5)
            
        # Add Main Title
        fig.suptitle(title, fontsize=16)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def plot_climbing_detailed(event, title):
        """
        Plots Speed vs Time for Climbing Event (0-70m).
        Markers at 0, 10, 30, 50, 70m.
        Labels: D, T, V, A.
        """
        df = event['df']
        start_idx = event['metrics']['start_idx']
        markers = event['metrics']['markers'] # Dict {10: {...}, 30: {...}}
        
        # Create fig
        fig, ax = plt.subplots(figsize=(15, 6))
        
        # Relative Time Calculation
        start_pos = df.index.get_loc(start_idx)
        time_axis = (df.reset_index(drop=True).index - start_pos) * 0.1
        
        # Plot Speed
        ax.plot(time_axis, df['Velocidad_GPS'], label="Velocidad", color='blue')
        
        # Start Line (0m)
        ax.axvline(0, color='#555555', linestyle='--', label='_nolegend_')
        
        # Add Markers lines (10, 30, 50, 70)
        # 70 is end_idx usually
        
        # Sort markers by distance
        sorted_dists = sorted(markers.keys())
        
        for d in sorted_dists:
            m_data = markers[d]
            t_val = m_data['time']
            
            # Line
            ax.axvline(t_val, color='#555555', linestyle='--', alpha=0.7)
            
            # Label
            # "distancia, t: xxs, v: xxkm/h, a: xxm/s2"
            label_text = f"D: {d}m\nT: {t_val:.2f}s\nV: {m_data['speed']:.1f}km/h\nA: {m_data['acc_cum']:.2f}m/s²"
            
            # Position
            # Stagger height to avoid overlap
            y_pos = m_data['speed'] + 5
            if d in [30, 70]: y_pos -= 15 # Alternate
            
            ax.text(t_val + 0.1, y_pos, label_text, fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                    verticalalignment='center')
            
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Velocidad (km/h)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf



    @staticmethod
    def plot_gps_heatmap(event, title="Trace GPS (Mapa de Calor de Velocidad)"):
        """
        Generates a Map Heatmap based on Latitude, Longitude, and GPS Speed.
        Uses staticmap to provide a clean offline/online hybrid mapping solution without external browsers.
        Returns bytes buffer containing the image.
        """
        try:
            import socket
            # Quick check for internet connection before trying to download tiles
            try:
                # 1.1.1.1 on port 53 is Cloudflare DNS, usually very reliable and fast
                socket.create_connection(("1.1.1.1", 53), timeout=1)
            except OSError:
                print("No internet connection detected, skipping GPS heatmap generation.")
                return None
                
            # We need staticmap for this
            from staticmap import StaticMap, Line
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
            import numpy as np
            import pandas as pd
            import io

            df = event['df']
            
            # Use start/end bounds if metrics are present, or use the whole df context
            if 'metrics' in event and 'start_idx' in event['metrics']:
                start_idx = event['metrics']['start_idx']
                end_idx = event['metrics'].get('end_idx', df.index[-1])
                try:
                    start_loc = df.index.get_loc(start_idx)
                    end_loc = df.index.get_loc(end_idx)
                    run_df = df.iloc[start_loc:end_loc+1].copy()
                except:
                    run_df = df.copy()
            else:
                run_df = df.copy()

            if run_df.empty:
                return None
                
            # Verify columns exist
            if 'Latitud' not in run_df.columns or 'Longitud' not in run_df.columns or 'Velocidad_GPS' not in run_df.columns:
                return None

            # Clean Lat/Lon which might be stored as European formatted strings or floats
            def clean_coord(val):
                if isinstance(val, str):
                    try:
                        return float(val.replace(',', '.'))
                    except ValueError:
                        return None
                return float(val)

            run_df['Lat'] = run_df['Latitud'].apply(clean_coord)
            run_df['Lon'] = run_df['Longitud'].apply(clean_coord)
            
            # Filter rows with valid coordinates
            valid_df = run_df.dropna(subset=['Lat', 'Lon'])
            # Avoid default 0,0 coords if sensor lost signal
            valid_df = valid_df[(valid_df['Lat'] != 0) & (valid_df['Lon'] != 0)]
            
            if len(valid_df) < 2:
                # Not enough points for a line
                return None
                
            velocities = valid_df['Velocidad_GPS'].values
            lats = valid_df['Lat'].values
            lons = valid_df['Lon'].values
            
            # Create Map Object (width x height) with Satellite + Roads (Hybrid) tiles
            # We use Google Maps Hybrid which provides both imagery and street guides
            url_template = 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}'
            # Padding leaves 50 pixels of "air" around the route so it's beautifully framed
            m = StaticMap(800, 600, padding_x=50, padding_y=50, url_template=url_template)
            
            # --- Auto-Zoom Override ---
            # staticmap by default caps its auto-zoom at 17, which is too far for short tests (e.g., 70m).
            # Google supports up to zoom 20 for satellite imagery. We monkey-patch the 
            # zoom calculation specifically for this map instance to allow zooming up to 20.
            from staticmap.staticmap import _lon_to_x, _lat_to_y
            
            def custom_calculate_zoom():
                for z in range(20, -1, -1):
                    extent = m.determine_extent(zoom=z)
                    width = (_lon_to_x(extent[2], z) - _lon_to_x(extent[0], z)) * m.tile_size
                    if width > (m.width - m.padding[0] * 2): continue
                    height = (_lat_to_y(extent[1], z) - _lat_to_y(extent[3], z)) * m.tile_size
                    if height > (m.height - m.padding[1] * 2): continue
                    return z
                return 0
                
            m._calculate_zoom = custom_calculate_zoom
            
            # Setup ColorMap processing
            # We map speed to a color range (Blue=Cold=Slow, Red=Hot=Fast)
            vmin = np.min(velocities)
            vmax = np.max(velocities)
            if vmax == vmin: vmax = vmin + 1 # avoid zero division
            
            cmap = plt.get_cmap('jet') # Jet produces nice Blue->Green->Yellow->Red
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

            # Build line segments point to point
            for i in range(len(lats) - 1):
                # segment coords (staticmap expects lon, lat)
                p1 = [lons[i], lats[i]]
                p2 = [lons[i+1], lats[i+1]]
                
                # Assign color based on average speed of the segment
                avg_v = (velocities[i] + velocities[i+1]) / 2.0
                rgba = cmap(norm(avg_v))
                color_hex = mcolors.to_hex(rgba, keep_alpha=False)
                
                line = Line([p1, p2], color_hex, 4)
                m.add_line(line)

            # Render Map Image (PIL)
            image = m.render()

            # Now, instead of returning raw PIL, let's wrap it in Matplotlib to add the Colorbar overlay
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.imshow(np.asarray(image))
            ax.axis('off') # Hide Matplotlib axes
            
            # Make room for the colorbar on the right side
            plt.subplots_adjust(right=0.85)
            
            # Title handling
            if title:
                fig.suptitle(title, fontsize=14, fontweight='bold', y=0.92)
            
            # Add Colorbar matched to the norm/cmap
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([]) # Required for older matplotlib versions
            
            # Create a tight axes for the colorbar: [left, bottom, width, height]
            # Moved slightly to the left to avoid clipping the numbers
            # Made it half the height (0.35) and centered vertically (0.325 bottom + 0.35 height / 2) vs old (0.15 bottom + 0.7 height)
            cax = fig.add_axes([0.88, 0.325, 0.03, 0.35]) 
            cbar = fig.colorbar(sm, cax=cax)
            cbar.set_label('Velocidad (km/h)', rotation=270, labelpad=15, fontweight='bold')
            cbar.ax.tick_params(labelsize=10)
            
            # Draw and save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            buf.seek(0)
            
            return buf
            
        except Exception as e:
            print(f"Error generating GPS Heatmap: {e}")
            return None

    @staticmethod
    def plot_gps_route_simple(df, title=None, distance_m=0.0):
        try:
            from staticmap import StaticMap, Line
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
            import numpy as np
            import io
            run_df = df.copy()
            def clean_coord(val):
                if isinstance(val, str):
                    try:
                        return float(val.replace(',', '.'))
                    except ValueError:
                        return None
                return float(val)

            run_df['Lat'] = run_df['Latitud'].apply(clean_coord)
            run_df['Lon'] = run_df['Longitud'].apply(clean_coord)
            
            valid_df = run_df.dropna(subset=['Lat', 'Lon'])
            valid_df = valid_df[(valid_df['Lat'] != 0) & (valid_df['Lon'] != 0)]
            
            if len(valid_df) < 2:
                return None
                
            lats = valid_df['Lat'].values
            lons = valid_df['Lon'].values
            
            url_template = 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}'
            m = StaticMap(800, 400, padding_x=50, padding_y=50, url_template=url_template)
            
            from staticmap.staticmap import _lon_to_x, _lat_to_y
            def custom_calculate_zoom():
                for z in range(20, -1, -1):
                    extent = m.determine_extent(zoom=z)
                    width = (_lon_to_x(extent[2], z) - _lon_to_x(extent[0], z)) * m.tile_size
                    if width > (m.width - m.padding[0] * 2): continue
                    height = (_lat_to_y(extent[1], z) - _lat_to_y(extent[3], z)) * m.tile_size
                    if height > (m.height - m.padding[1] * 2): continue
                    return z
                return 0
                
            m._calculate_zoom = custom_calculate_zoom
            
            # Simple thick blue line without heat
            points = []
            for i in range(len(lats)):
                points.append([lons[i], lats[i]])
                
            line = Line(points, '#1f538d', 10) # Default nice blue, thick
            m.add_line(line)
            
            # Render map
            image = m.render()

            # Matplotlib wrapper to add title, text, and keep SVG proportions
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(np.asarray(image))
            ax.axis('off')
            
            if title:
                fig.suptitle(title, fontsize=14, fontweight='bold', y=0.92)
            
            # Overlay distance text
            if distance_m > 0:
                ax.text(0.05, 0.05, f"Distancia de la prueba: {distance_m:.2f} m", 
                        transform=ax.transAxes, fontsize=14, fontweight='bold',
                        color='white', bbox=dict(facecolor='#1f538d', alpha=0.9, boxstyle='round,pad=0.5'))
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            buf.seek(0)
            
            return buf
            
        except Exception as e:
            print(f"Error generating simple GPS route: {e}")
            return None
