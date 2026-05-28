import os
import sys
import subprocess
import re
import numpy as np
import matplotlib
matplotlib.use('Agg') # Ensures thread-safe, headless rendering
import matplotlib.pyplot as plt
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import pyvista as pv
import multiprocessing

MAX_WORKERS = 6

#Generated with the help of AI

def compile_and_run_c():
    compile_cmd = ["gcc", "simulation.c", "functions.c", "RK4integrator.c", "-o", "sim.exe", "-O3", "-lm", "-fopenmp"]
    try:
        subprocess.run(compile_cmd, check=True)
    except subprocess.CalledProcessError:
        print("Failed to compile C code. Ensure gcc is installed and in your PATH.")
        sys.exit(1)
        
    # Dynamically find 'total_sims' from the C source code
    with open("simulation.c", "r") as f:
        match = re.search(r'int\s+total_sims\s*=\s*(\d+);', f.read())
        total_sims = int(match.group(1)) if match else 1
        
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_folder = f"simulation_results/Batch_{timestamp}"
    
    
    for i in range(total_sims):
        os.makedirs(f"{batch_folder}/sim_{i+1}", exist_ok=True)
        
    #C comm via .txt
    with open("batch_path.txt", "w") as f:
        f.write(batch_folder)
        
    # Run cross-platform compatible executable
    exe_name = "sim.exe" if sys.platform == "win32" else "./sim.exe"
    subprocess.run([exe_name], check=True)
    
    return total_sims, batch_folder

def generate_plots(sim_id, batch_folder):
    old_output_folder = f"{batch_folder}/sim_{sim_id}"
    info_path = os.path.join(old_output_folder, f"simulation_info_{sim_id}.txt")
    
    if not os.path.exists(info_path):
        return
        
    # Read the text file C already generated to extract the stats
    with open(info_path, "r") as f:
        content = f.read()
        min_dist_match = re.search(r'Minimum Ship Distance:\s*([0-9]+)', content)
        dv_match = re.search(r'Delta Ship Velocity:\s*([-+]?[0-9]+)', content)
        
        min_dist = min_dist_match.group(1) if min_dist_match else "Unknown"
        delta_v = dv_match.group(1) if dv_match else "Unknown"
        
    # Rename the folder to include the minimum distance and velocity
    min_dist_val = float(min_dist) / 1000.0 if min_dist != "Unknown" else "Unknown"
    new_folder_name = f"sim_{sim_id}_dV{delta_v}_D{min_dist_val}"
    output_folder = os.path.join(batch_folder, new_folder_name)
    os.rename(old_output_folder, output_folder)
    
    bin_path = os.path.join(output_folder, f"simulation_data_{sim_id}.bin")
        
    # Load the flat binary array and reshape into 15 columns
    data = np.fromfile(bin_path, dtype=np.float64).reshape(-1, 15)
    
    time_days = data[:, 0]
    energy = data[:, 1]
    ship_energy = data[:, 2]
    # Reshape the remaining 12 columns into shape (steps, 4 bodies, 3 dimensions [x, y, z])
    history = data[:, 3:].reshape(-1, 4, 3)
    
    # Target max 10,000 points for static plots to render instantly
    plot_skip = max(1, len(time_days) // 10000)
    
    body_names = ["Ship", "Sun", "Venus", "Earth"]
    colors = ['purple', 'gold', 'orange', 'blue']
    
    # =========================================
    # 1. 3D Trajectories Plot
    # =========================================
    plotter = pv.Plotter(window_size=[1000, 1000], off_screen=True)
    plotter.enable_anti_aliasing('msaa')
    plotter.set_background('white')
    max_val = np.max(np.abs(history)) * 1.1
    bounds_mesh = pv.Box(bounds=(-max_val, max_val, -max_val, max_val, -max_val, max_val))
    plotter.add_mesh(bounds_mesh, style='wireframe', color='lightgray', opacity=0.3)
    
    for i, name in enumerate(body_names):
        x, y, z = history[::plot_skip, i, 0], history[::plot_skip, i, 1], history[::plot_skip, i, 2]
        pts = np.column_stack((x, y, z))
        if len(pts) > 1:
            line = pv.PolyData(pts)
            line.lines = np.hstack([[len(pts)], np.arange(len(pts))])
            width = 1 if name == "Ship" else 2
            plotter.add_mesh(line, color=colors[i], line_width=width, label=name)
            
        plotter.add_mesh(pv.Sphere(radius=max_val*0.015, center=pts[-1], theta_resolution=40, phi_resolution=40), color=colors[i])
        
    plotter.add_legend()
    plotter.add_axes()
    plotter.camera_position = 'iso'
    plotter.camera.zoom(1.3)
    
    # Save the static PNG
    plotter.screenshot(os.path.join(output_folder, f"orbit_plot_{sim_id}.png"))
    # Export an interactive HTML file that you can open in any browser!
    plotter.export_html(os.path.join(output_folder, f"interactive_orbit_{sim_id}.html"))
    plotter.close()
    
    # =========================================
    # 2. Total Energy Stability
    # =========================================
    fig, ax = plt.subplots(figsize=(10, 4))
    energy_change = (energy[::plot_skip] - energy[0]) / np.abs(energy[0])
    ax.plot(time_days[::plot_skip], energy_change, color='green')
    ax.set_title("Total Hamiltonian Stability")
    ax.set_xlabel("Time (Days)")
    ax.set_ylabel("Relative Energy Error")
    ax.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_folder, f"total_energy_{sim_id}.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # =========================================
    # 3. Ship Specific Energy
    # =========================================
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(time_days[::plot_skip], ship_energy[::plot_skip], color='purple')
    ax.set_title("Ship Hamiltonian")
    ax.set_xlabel("Time (Days)")
    ax.set_ylabel("Energy (Joules)")
    ax.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_folder, f"ship_energy_{sim_id}.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # =========================================
    # 4. Animated MP4 Video
    # =========================================
    # Dynamically target ~400 total frames for a smooth ~13-second video
    skip = max(1, len(time_days) // 400)
    plotter = pv.Plotter(window_size=[800, 800], off_screen=True)
    plotter.set_background('white')
    plotter.add_mesh(bounds_mesh, style='wireframe', color='lightgray', opacity=0.3)
    plotter.add_axes()
    plotter.camera_position = 'iso'
    plotter.camera.zoom(1.3)
    
    plotter.open_movie(os.path.join(output_folder, f"animation_{sim_id}.mp4"), framerate=30)
    
    frames = len(time_days) // skip
    for frame in range(frames):
        if frame % max(1, frames // 10) == 0:
            if sim_id == 67: 
                print(f"SIX SEVEN, SIX SEVEN")
            
            print(f"  -> Sim {sim_id}: Rendering MP4 video... {frame/frames*100:.0f}%", flush=True)

        idx = min(frame * skip, len(time_days) - 1)
        
        plotter.add_text(f"Simulation {sim_id} Animation\nTime: {time_days[idx]:.1f} days", name="time_text", font_size=12, color='black')
        
        for i, name in enumerate(body_names):
            # Apply the exact same `skip` to the line trail. 
            # This completely decouples rendering time from the simulation resolution!
            pts = history[0:idx+1:skip, i, :]
            
            # Guarantee the trail perfectly connects to the current head position
            if len(pts) > 0 and not np.array_equal(pts[-1], history[idx, i, :]):
                pts = np.vstack([pts, history[idx, i, :]])
                
            if len(pts) > 1:
                line = pv.PolyData(pts)
                line.lines = np.hstack([[len(pts)], np.arange(len(pts))])
                width = 1 if name == "Ship" else 2
                plotter.add_mesh(line, name=f"line_{i}", color=colors[i], line_width=width)
            # Use a low-poly sphere for the animation (massively speeds up geometry generation)
            plotter.add_mesh(pv.Sphere(radius=max_val*0.015, center=history[idx, i, :], theta_resolution=16, phi_resolution=16), name=f"head_{i}", color=colors[i])
            
        plotter.write_frame()
        
    plotter.close()

if __name__ == "__main__":
    # 1. Compile, setup folders, and execute C engine
    total_simulations_run, batch_folder = compile_and_run_c()
    
    # 2. Generate plots for every simulation run
    count = 0
    with ProcessPoolExecutor(MAX_WORKERS) as executor:
        futures = {executor.submit(generate_plots, sim, batch_folder): sim for sim in range(1, total_simulations_run + 1)}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"\n[ERROR in Sim {futures[future]}] Plot generation failed: {e}")
            count += 1
            print(f"[{count/total_simulations_run*100:3.0f}%] Completed full rendering pipeline for Sim {futures[future]}!", flush=True)
        
    # Clean up the temp file
    if os.path.exists("batch_path.txt"):
        os.remove("batch_path.txt")
        
    print("\n[SUCCESS] Entire pipeline completed.")