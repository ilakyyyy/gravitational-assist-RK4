import old_python.defs as defs
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

def CreateGif(history, bodies, t_vector, output_folder, sim_id, skip, fps, title_text):
    
    # 1. Setup the 2D Figure
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Calculate fixed bounds so the camera doesn't jitter
    # We use the relative positions (planet - sun)
    all_x = (history[:, :, 0]).flatten()
    all_y = (history[:, :, 1]).flatten()
    
    # Find max distance to center the view
    max_range = (np.max(all_x) - np.min(all_x)) / 2.0
    mid_x = (np.max(all_x) + np.min(all_x)) * 0.5
    mid_y = (np.max(all_y) + np.min(all_y)) * 0.5
    
    # Set limits with a 10% buffer
    buffer = max_range * 0.1
    ax.set_xlim(mid_x - max_range - buffer, mid_x + max_range + buffer)
    ax.set_ylim(mid_y - max_range - buffer, mid_y + max_range + buffer)
    ax.set_aspect('equal') # Crucial for circular orbits
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_title(title_text, fontsize=10)
    
    # 2. Initialize Lines and Heads
    lines = [] # The trails
    heads = [] # The planet dots
    colors = ['gold', 'blue', 'orange', 'red']
    labels = []
    
    for i, body in enumerate(bodies):
        color = colors[i % len(colors)]
        style = '--' if body.name == "Ship" else '-'
        
        # Trail (line)
        line, = ax.plot([], [], color=color, linestyle=style, alpha=0.6, linewidth=1)
        # Head (dot)
        head, = ax.plot([], [], marker='o', color=color, markersize=8)
        
        lines.append(line)
        heads.append(head)
        labels.append(body.name)
    
    ax.legend(lines, labels, loc="upper right", fontsize=9)
    
    # Add a time label in the corner
    time_text = ax.text(0.05, 0.95, '', transform=ax.transAxes)

    # 3. The Update Function
    num_frames = len(t_vector) // skip

    def update(frame_idx):
        real_idx = frame_idx * skip
        if real_idx >= len(t_vector): real_idx = len(t_vector) - 1
        
        current_time = t_vector[real_idx]
        time_text.set_text(f"Hour: {current_time:.1f}")
        
        for i, body in enumerate(bodies):
            # Get relative coordinates up to this time
            x_data = history[:real_idx, i, 0]
            y_data = history[:real_idx, i, 1]
            
            # Update Trail (Show full history up to now)
            lines[i].set_data(x_data, y_data)
            
            # Update Head (Current position only)
            if len(x_data) > 0:
                heads[i].set_data([x_data[-1]], [y_data[-1]])
                
        return lines + heads + [time_text]

    # 4. Save Animation
    ani = FuncAnimation(fig, update, frames=num_frames, interval=30, blit=True)
    gif_filename = os.path.join(output_folder, f"anim_sim_{sim_id+1}.gif")
    
    # Use PillowWriter (standard in matplotlib)
    ani.save(gif_filename, writer=PillowWriter(fps=fps))
    plt.close(fig)

def GeneratePlots(output_folder, sim_id, history, energy_history, ship_energy_history, bodies, 
                  initial_v_ph, initial_ship_v, min_distance, final_ship_v, 
                  gif, skip, fps, factor):

    # =========================================
    # Plot 1: 2D Orbit Trajectories
    # =========================================
    fig, ax = plt.subplots(figsize=(10, 8)) 

    colors = ['gold', 'blue', 'orange', 'red'] 
    for i, body in enumerate(bodies):
        x = history[:, i, 0]
        y = history[:, i, 1]
        
        color = colors[i % len(colors)]
        style = '--' if body.name == "Ship" else '-'
        width = 1.0 if body.name == "Ship" else 2.0
        alpha = 0.8
        
        # 2D Plot: Only X and Y
        ax.plot(x, y, color=color, linestyle=style, linewidth=width, label=body.name, alpha=alpha)
        # Markers
        ax.plot(x[-1], y[-1], marker='o', color=color, markersize=5) 
        ax.plot(x[0], y[0], marker='.', color=color, markersize=2) 

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    
    ax.set_title(f"2D trajectories \nInitial venus phase: {round(initial_v_ph, 3)} - Initial ship velocity: {round(initial_ship_v, 3)}\n Final ship velocity: {round(final_ship_v, 3)} m/s - Minimum Distance: {round(min_distance, 0)} m \nFactor: {factor}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal') 

    plot_filename = os.path.join(output_folder, f"orbit_plot_sim_{sim_id}.png")
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # =========================================
    # Plot 2: Total Hamiltonian
    # =========================================
    fig_en, ax_en = plt.subplots(figsize=(10, 4))
    # Plot percentage change in energy relative to start
    energy_change = (energy_history - energy_history[0]) / np.abs(energy_history[0])
    ax_en.plot(energy_change)
    ax_en.set_title("Total Hamiltonian Stability")
    ax_en.set_xlabel("Time Steps")
    ax_en.set_ylabel("Relative Hamiltonian Change")
    ax_en.grid(True)

    energy_filename = os.path.join(output_folder, f"energy_stability_plot_{sim_id+1}.png")
    plt.savefig(energy_filename, dpi=300, bbox_inches='tight')
    plt.close(fig_en)

    # =========================================
    # Plot 3: Ship Specific Hamiltonian
    # =========================================
    fig_ship, ax_ship = plt.subplots(figsize=(10, 4))
    
    ax_ship.plot(ship_energy_history, color='purple')
    
    ax_ship.set_title(f"Ship Hamiltonian")
    ax_ship.set_xlabel("Time Steps")
    ax_ship.set_ylabel("Energy (Joules)")
    ax_ship.grid(True, alpha=0.3)
    
    ship_energy_filename = os.path.join(output_folder, f"ship_energy_plot_{sim_id+1}.png")
    plt.savefig(ship_energy_filename, dpi=300, bbox_inches='tight')
    plt.close(fig_ship)

    # =========================================
    # Plot 4: GIF
    # =========================================
    if gif == True:
        # We need a t_vector for the GIF. Since we passed everything else, 
        # we can just generate a dummy index vector if strictly needed, 
        # but your CreateGif likely relies on the array length.
        # Ideally, pass t_vector to this function too if CreateGif needs time labels.
        # Assuming history length is enough for now:
        t_vector_dummy = np.arange(len(history)) 
        
        text = f"Initial venus phase: {round(initial_v_ph, 3)} - Initial velocity: {round(initial_ship_v, 3)} - Final velocity: {round(final_ship_v, 3)}\nFactor: {factor}"
        CreateGif(history, bodies, t_vector_dummy, output_folder, sim_id, skip, fps, text)