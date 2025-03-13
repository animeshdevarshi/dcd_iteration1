# visualization.py
# Basic visualization functions for data center layout

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.figure import figaspect

def visualize_datacenter(datacenter, title="Data Center Layout"):
    """
    Visualize the current state of the data center grid.
    
    Args:
        datacenter: Instance of DataCenterGrid
        title: Title for the plot
            
    Returns:
        Figure and axis objects
    """
    # Create figure with appropriate size and margins
    # Use figaspect to ensure the aspect ratio is preserved
    w, h = figaspect(datacenter.length_m / datacenter.width_m)
    fig = plt.figure(figsize=(15, 15 * datacenter.length_m / datacenter.width_m))
    
    # Create the main axis
    ax = fig.add_subplot(111)
    
    # Set plot limits in meters with added margin
    x_margin = 1
    y_margin = 1
    x_min, x_max = -x_margin, datacenter.width_m + x_margin
    y_min, y_max = -y_margin, datacenter.length_m + y_margin
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    # Draw room outline
    room_outline = patches.Rectangle((0, 0), datacenter.width_m, datacenter.length_m, 
                                     linewidth=2, edgecolor='black', 
                                     facecolor='none')
    ax.add_patch(room_outline)
    
    # Draw grid lines
    for i in range(0, datacenter.grid_width + 1):
        ax.axvline(i * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.3)
    for j in range(0, datacenter.grid_length + 1):
        ax.axhline(j * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.3)
    
    # Add grid indicators with improved spacing
    # Only label every 5 cells (3m) to prevent crowding
    for i in range(0, datacenter.grid_width + 1, 5):
        x_pos = i * datacenter.grid_size_m
        ax.text(x_pos, -0.7, f"{x_pos:.1f}m", 
               ha='center', va='top', fontsize=8)
    
    for j in range(0, datacenter.grid_length + 1, 5):
        y_pos = j * datacenter.grid_size_m
        ax.text(-0.7, y_pos, f"{y_pos:.1f}m", 
               ha='right', va='center', fontsize=8)
    
    # Draw pillars
    for pillar in datacenter.pillars:
        p = patches.Rectangle(
            (pillar['x'], pillar['y']),
            pillar['width'], pillar['height'],
            linewidth=1, edgecolor='red', facecolor='darkgray'
        )
        ax.add_patch(p)
        
        # Add pillar measurements
        text = f"{pillar.get('width_cells', '')}×{pillar.get('height_cells', '')}"
        ax.text(
            pillar['x'] + pillar['width']/2,
            pillar['y'] + pillar['height']/2,
            text, ha='center', va='center', fontsize=6
        )
    
    # Draw support rooms (if any)
    if hasattr(datacenter, 'support_rooms') and datacenter.support_rooms:
        colors = ['lightgreen', 'lightblue', 'lightyellow', 'mistyrose', 'lavender']
        for i, room in enumerate(datacenter.support_rooms):
            color = colors[i % len(colors)]
            r = patches.Rectangle(
                (room['x'], room['y']),
                room['width'], room['height'],
                linewidth=1, edgecolor='black', facecolor=color, alpha=0.7
            )
            ax.add_patch(r)
            
            # Add room label if name is available
            if 'name' in room:
                ax.text(
                    room['x'] + room['width']/2,
                    room['y'] + room['height']/2,
                    room['name'], ha='center', va='center', fontsize=10
                )
    
    # Draw racks (if any)
    for i, rack in enumerate(datacenter.racks):
        color = 'royalblue'
        r = patches.Rectangle(
            (rack['x'], rack['y']),
            rack['width'], rack['height'],
            linewidth=1, edgecolor='black', facecolor=color, alpha=0.8
        )
        ax.add_patch(r)
        
        # Add rack ID
        rack_id = rack.get('id', f'R{i+1}')
        ax.text(
            rack['x'] + rack['width']/2,
            rack['y'] + rack['height']/2,
            rack_id, ha='center', va='center', 
            color='white', fontsize=8, fontweight='bold'
        )
    
    # Set axis labels with proper spacing
    ax.set_xlabel("Width (meters)", labelpad=20)
    ax.set_ylabel("Length (meters)", labelpad=20)
    
    # Add title with improved layout
    title_text = title + "\n"
    title_text += f"Room: {datacenter.width_m:.1f}m × {datacenter.length_m:.1f}m | "
    title_text += f"Grid: {datacenter.grid_size_m*1000:.0f}mm × {datacenter.grid_size_m*1000:.0f}mm ({datacenter.grid_width} × {datacenter.grid_length} cells)"
    
    # Position the title with more space
    ax.set_title(title_text, pad=20)
    
    # Ensure tight layout but with enough margin for the labels
    plt.tight_layout(pad=2.0)
    
    return fig, ax

def plot_grid_heatmap(datacenter):
    """
    Create a heatmap visualization of the data center grid.
    Useful for quickly checking element placement.
    
    Args:
        datacenter: Instance of DataCenterGrid
        
    Returns:
        Figure and axis objects
    """
    plt.figure(figsize=(10, 6))
    
    # Create a custom colormap for the different element types
    cmap = plt.cm.colors.ListedColormap(['white', 'red', 'blue', 'green'])
    
    # Set the boundaries for the colormap
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
    
    # Create the heatmap
    plt.imshow(datacenter.grid, cmap=cmap, norm=norm, origin='lower')
    
    # Add a colorbar with labels
    cbar = plt.colorbar(ticks=[0, 1, 2, 3])
    cbar.set_ticklabels(['Empty', 'Pillar', 'Rack', 'Support Room/Wall'])
    
    # Add grid lines
    plt.grid(which='major', color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Add labels
    plt.title('Data Center Grid Heatmap')
    plt.xlabel('Grid X')
    plt.ylabel('Grid Y')
    
    # Add rack ID labels
    for rack in datacenter.racks:
        rack_id = rack.get('id', 'R')
        grid_x = rack.get('grid_x', 0)
        grid_y = rack.get('grid_y', 0)
        grid_width = rack.get('width_cells', 2)
        grid_height = rack.get('height_cells', 1)
        
        plt.text(
            grid_x + grid_width/2 - 0.5, 
            grid_y + grid_height/2 - 0.5,
            rack_id, ha='center', va='center', 
            color='white', fontsize=8, fontweight='bold'
        )
    
    plt.tight_layout()
    return plt.gcf(), plt.gca()