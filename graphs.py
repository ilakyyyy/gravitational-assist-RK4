import os
import sys
import subprocess
import re
import numpy as np
import matplotlib
matplotlib.use('Agg') # Ensures thread-safe, headless rendering
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

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
        vel_match = re.search(r'Final Ship Velocity:\s*([0-9]+)', content)
        
        min_dist = min_dist_match.group(1) if min_dist_match else "Unknown"
        vel = vel_match.group(1) if vel_match else "Unknown"
        
    # Rename the folder to include the minimum distance and velocity
    min_dist_val = float(min_dist) / 1000.0 if min_dist != "Unknown" else "Unknown"
    new_folder_name = f"sim_{sim_id}_V{vel}_D{min_dist_val}"
    output_folder = os.path.join(batch_folder, new_folder_name)
    os.rename(old_output_folder, output_folder)
    
    bin_path = os.path.join(output_folder, f"simulation_data_{sim_id}.bin")
        
    # Load the flat binary array and reshape into 11 columns
    data = np.fromfile(bin_path, dtype=np.float64).reshape(-1, 11)
    
    time_days = data[:, 0]
    energy = data[:, 1]
    ship_energy = data[:, 2]
    # Reshape the remaining 8 columns into shape (steps, 4 bodies, 2 dimensions [x, y])
    history = data[:, 3:].reshape(-1, 4, 2)
    
    # Target max 10,000 points for static plots to render instantly
    plot_skip = max(1, len(time_days) // 10000)
    
    body_names = ["Ship", "Sun", "Venus", "Earth"]
    colors = ['purple', 'gold', 'orange', 'blue']
    
    # =========================================
    # 1. 2D Trajectories Plot
    # =========================================
    fig, ax = plt.subplots(figsize=(10, 10))
    for i, name in enumerate(body_names):
        x, y = history[::plot_skip, i, 0], history[::plot_skip, i, 1]
        style = '--' if name == "Ship" else '-'
        width = 1.0 if name == "Ship" else 2.0
        
        ax.plot(x, y, color=colors[i], linestyle=style, linewidth=width, label=name, alpha=0.8)
        ax.plot(history[-1, i, 0], history[-1, i, 1], marker='o', color=colors[i], markersize=6) # Exact end position
        ax.plot(history[0, i, 0], history[0, i, 1], marker='.', color=colors[i], markersize=3)   # Exact start position
        
    ax.set_aspect('equal')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title(f"Simulation {sim_id} - Orbital Trajectories")
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    plt.savefig(os.path.join(output_folder, f"orbit_plot_{sim_id}.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    
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
    # 4. Animated GIF
    # =========================================
    # Dynamically target ~200 frames to prevent massive slowdowns on high-precision runs
    skip = max(1, len(time_days) // 200)
    fig, ax = plt.subplots(figsize=(8, 8))
    max_val = np.max(np.abs(history[:, :, :])) * 1.1 # Dynamically scale bounds to fit all bodies
    ax.set_xlim(-max_val, max_val)
    ax.set_ylim(-max_val, max_val)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f"Simulation {sim_id} Animation")
    
    lines, heads = [], []
    for i, name in enumerate(body_names):
        style = '--' if name == "Ship" else '-'
        line, = ax.plot([], [], color=colors[i], linestyle=style, alpha=0.6, linewidth=1, label=name)
        head, = ax.plot([], [], marker='o', color=colors[i], markersize=6)
        lines.append(line); heads.append(head)
        
    ax.legend(loc="upper right")
    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)
    
    def update(frame):
        idx = min(frame * skip, len(time_days) - 1)
        time_text.set_text(f"Time: {time_days[idx]:.1f} days")
        for i in range(4):
            lines[i].set_data(history[:idx, i, 0], history[:idx, i, 1])
            if idx > 0:
                heads[i].set_data([history[idx, i, 0]], [history[idx, i, 1]])
        return lines + heads + [time_text]
        
    frames = len(time_days) // skip
    ani = FuncAnimation(fig, update, frames=frames, interval=30, blit=True)
    ani.save(os.path.join(output_folder, f"animation_{sim_id}.gif"), writer=PillowWriter(fps=30))
    plt.close(fig)

if __name__ == "__main__":
    # 1. Compile, setup folders, and execute C engine
    total_simulations_run, batch_folder = compile_and_run_c()
    
    # 2. Generate plots for every simulation run
    count = 0
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(generate_plots, sim, batch_folder) for sim in range(1, total_simulations_run + 1)]
        for _ in as_completed(futures):
            count += 1
            print(f"\r[{count/total_simulations_run*100:3.0f}%] Generating plots...", end="", flush=True)
        
    # Clean up the temp file
    if os.path.exists("batch_path.txt"):
        os.remove("batch_path.txt")
        
    print("\n[SUCCESS] Entire pipeline completed.")