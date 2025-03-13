# enhanced_visualization.py
# Enhanced visualization tools for data center layouts

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

def visualize_datacenter_enhanced(datacenter, title="Enhanced Data Center Layout", 
                                show_metrics=True, highlight_zones=False, 
                                cooling_analysis=False, show_grid=True):
    """
    Enhanced visualization for data center layouts with additional information.
    
    Args:
        datacenter: Instance of DataCenterGrid
        title: Title for the plot
        show_metrics: Whether to show metrics on the plot
        highlight_zones: Whether to highlight different zones (high/low density)
        cooling_analysis: Whether to show cooling analysis heatmap
        show_grid: Whether to show the grid lines
            
    Returns:
        Figure and axis objects
    """
    # Create figure with appropriate size
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Set plot limits in meters with added margin
    x_margin, y_margin = 1, 1
    ax.set_xlim(-x_margin, datacenter.width_m + x_margin)
    ax.set_ylim(-y_margin, datacenter.length_m + y_margin)
    
    # Draw room outline
    room_outline = patches.Rectangle((0, 0), datacenter.width_m, datacenter.length_m, 
                                    linewidth=2, edgecolor='black', 
                                    facecolor='none')
    ax.add_patch(room_outline)
    
    # Draw grid lines if requested
    if show_grid:
        for i in range(0, datacenter.grid_width + 1):
            ax.axvline(i * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.2)
        for j in range(0, datacenter.grid_length + 1):
            ax.axhline(j * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.2)
    
    # Draw cooling analysis heatmap if requested
    if cooling_analysis:
        # Create a heatmap showing cooling efficiency
        cooling_grid = np.zeros((datacenter.grid_length, datacenter.grid_width))
        
        # Calculate cooling efficiency based on distance from walls and density of racks
        for y in range(datacenter.grid_length):
            for x in range(datacenter.grid_width):
                # Distance from nearest wall as a factor (closer to wall = better cooling)
                dist_from_wall = min(x, y, datacenter.grid_width-x, datacenter.grid_length-y)
                wall_factor = max(0, 1 - dist_from_wall/10)
                
                # Count nearby racks (more racks = worse cooling)
                rack_count = 0
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        ny, nx = y+dy, x+dx
                        if (0 <= ny < datacenter.grid_length and 
                            0 <= nx < datacenter.grid_width and
                            datacenter.grid[ny, nx] == datacenter.RACK):
                            rack_count += 1
                
                density_factor = max(0, 1 - rack_count/20)
                
                # Combined cooling efficiency (higher = better)
                cooling_grid[y, x] = (wall_factor + density_factor) / 2
        
        # Create a custom colormap for cooling efficiency
        colors = [(0.8, 0, 0), (1, 1, 0), (0, 0.8, 0)]  # Red -> Yellow -> Green
        cmap = LinearSegmentedColormap.from_list('cooling_cmap', colors, N=100)
        
        # Display the heatmap with transparency
        cooling_img = ax.imshow(cooling_grid, origin='lower', extent=[0, datacenter.width_m, 0, datacenter.length_m],
                               cmap=cmap, alpha=0.3, interpolation='bilinear')
        
        # Add colorbar
        cbar = plt.colorbar(cooling_img, ax=ax)
        cbar.set_label('Cooling Efficiency')
    
    # Draw pillars
    for pillar in datacenter.pillars:
        p = patches.Rectangle(
            (pillar['x'], pillar['y']),
            pillar['width'], pillar['height'],
            linewidth=1, edgecolor='red', facecolor='darkgray'
        )
        ax.add_patch(p)
    
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
    
    # Highlight zones if requested
    if highlight_zones:
        # Calculate rack density
        density_grid = np.zeros((datacenter.grid_length, datacenter.grid_width))
        
        for y in range(datacenter.grid_length):
            for x in range(datacenter.grid_width):
                # Count racks within a radius
                rack_count = 0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        ny, nx = y+dy, x+dx
                        if (0 <= ny < datacenter.grid_length and 
                            0 <= nx < datacenter.grid_width and
                            datacenter.grid[ny, nx] == datacenter.RACK):
                            rack_count += 1
                
                density_grid[y, x] = rack_count
        
        # Find high density areas (top 25% of density values)
        if density_grid.max() > 0:  # Only if there are racks
            threshold = np.percentile(density_grid[density_grid > 0], 75)
            
            # Highlight high density areas
            high_density_coords = np.where(density_grid >= threshold)
            for y, x in zip(high_density_coords[0], high_density_coords[1]):
                rect_x = x * datacenter.grid_size_m
                rect_y = y * datacenter.grid_size_m
                
                r = patches.Rectangle(
                    (rect_x, rect_y),
                    datacenter.grid_size_m, datacenter.grid_size_m,
                    linewidth=0, facecolor='red', alpha=0.1
                )
                ax.add_patch(r)
    
    # Draw racks with different colors based on row/cluster
    if datacenter.racks:
        # Group racks by row
        rack_rows = {}
        for rack in datacenter.racks:
            row_key = rack['grid_y']  # Use Y coordinate as row key
            if row_key not in rack_rows:
                rack_rows[row_key] = []
            rack_rows[row_key].append(rack)
        
        # Generate colors for each row
        colors = plt.cm.tab20(np.linspace(0, 1, len(rack_rows)))
        
        # Draw racks colored by row
        for i, (row_key, racks) in enumerate(rack_rows.items()):
            color = colors[i % len(colors)]
            
            for rack in racks:
                r = patches.Rectangle(
                    (rack['x'], rack['y']),
                    rack['width'], rack['height'],
                    linewidth=1, edgecolor='black', facecolor=color, alpha=0.8
                )
                ax.add_patch(r)
                
                # Add rack ID
                rack_id = rack.get('id', f'R{datacenter.racks.index(rack)+1}')
                ax.text(
                    rack['x'] + rack['width']/2,
                    rack['y'] + rack['height']/2,
                    rack_id, ha='center', va='center', 
                    color='white', fontsize=8, fontweight='bold'
                )
    
    # Add metrics if requested
    if show_metrics:
        # Calculate metrics
        total_racks = len(datacenter.racks)
        total_area = datacenter.width_m * datacenter.length_m
        rack_area = sum(rack['width'] * rack['height'] for rack in datacenter.racks)
        density = rack_area / total_area
        
        # Find aisles by detecting empty rows between rack rows
        rack_y_coords = sorted(set(rack['grid_y'] for rack in datacenter.racks))
        aisles = 0
        for i in range(len(rack_y_coords) - 1):
            if rack_y_coords[i+1] - rack_y_coords[i] > 1:
                aisles += 1
        
        # Create metrics text
        metrics_text = (
            f"Racks: {total_racks}\n"
            f"Density: {density:.1%}\n"
            f"Aisles: {aisles}\n"
            f"Area: {total_area:.1f} m²"
        )
        
        # Add metrics to plot
        plt.figtext(0.02, 0.02, metrics_text, fontsize=10,
                   bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
    
    # Set title, labels and grid
    ax.set_title(title, pad=20, fontsize=14)
    ax.set_xlabel("Width (meters)", labelpad=10)
    ax.set_ylabel("Length (meters)", labelpad=10)
    
    # Add legend for zones if needed
    if highlight_zones:
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', alpha=0.1, label='High Density Zone')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    return fig, ax

def compare_layouts_visually(datacenter_layouts, titles=None, figsize=(15, 10)):
    """
    Create a comparative visualization of multiple layouts side by side.
    
    Args:
        datacenter_layouts: List of DataCenterGrid instances with different layouts
        titles: Optional list of titles for each layout
        figsize: Figure size
    
    Returns:
        Figure and axes
    """
    n_layouts = len(datacenter_layouts)
    if n_layouts <= 0:
        return None, None
    
    # Calculate grid size (try to make it square-ish)
    n_cols = min(3, n_layouts)
    n_rows = (n_layouts + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    
    # Flatten axes for easier indexing
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    # Hide unused subplots
    for i in range(n_layouts, len(axes)):
        axes[i].axis('off')
    
    # Plot each layout
    for i, datacenter in enumerate(datacenter_layouts):
        ax = axes[i]
        
        # Set plot limits
        ax.set_xlim(-1, datacenter.width_m + 1)
        ax.set_ylim(-1, datacenter.length_m + 1)
        
        # Draw room outline
        room_outline = patches.Rectangle((0, 0), datacenter.width_m, datacenter.length_m, 
                                        linewidth=2, edgecolor='black', 
                                        facecolor='none')
        ax.add_patch(room_outline)
        
        # Draw grid lines (simplified)
        for j in range(0, datacenter.grid_width + 1, 5):  # Show fewer grid lines
            ax.axvline(j * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.2)
        for j in range(0, datacenter.grid_length + 1, 5):
            ax.axhline(j * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.2)
        
        # Draw pillars
        for pillar in datacenter.pillars:
            p = patches.Rectangle(
                (pillar['x'], pillar['y']),
                pillar['width'], pillar['height'],
                linewidth=1, edgecolor='red', facecolor='darkgray'
            )
            ax.add_patch(p)
        
        # Draw support rooms
        if hasattr(datacenter, 'support_rooms') and datacenter.support_rooms:
            for room in datacenter.support_rooms:
                r = patches.Rectangle(
                    (room['x'], room['y']),
                    room['width'], room['height'],
                    linewidth=1, edgecolor='black', facecolor='lightgreen', alpha=0.7
                )
                ax.add_patch(r)
        
        # Draw racks
        for rack in datacenter.racks:
            r = patches.Rectangle(
                (rack['x'], rack['y']),
                rack['width'], rack['height'],
                linewidth=1, edgecolor='black', facecolor='royalblue', alpha=0.8
            )
            ax.add_patch(r)
        
        # Add title
        if titles and i < len(titles):
            title = titles[i]
        else:
            title = f"Layout {i+1}"
        
        ax.set_title(title)
        
        # Add rack count
        ax.text(0.02, 0.02, f"Racks: {len(datacenter.racks)}", transform=ax.transAxes,
               fontsize=9, verticalalignment='bottom',
               bbox=dict(facecolor='white', alpha=0.7))
        
        # Set axis labels for outer plots only
        if i >= len(axes) - n_cols:  # Bottom row
            ax.set_xlabel("Width (m)")
        if i % n_cols == 0:  # Leftmost column
            ax.set_ylabel("Length (m)")
    
    plt.tight_layout()
    return fig, axes

def create_usage_heatmap(datacenter):
    """
    Create a heatmap visualization showing the usage of space in the data center.
    
    Args:
        datacenter: DataCenterGrid instance
    
    Returns:
        Figure and axis
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create a custom colormap for different elements
    cmap = plt.cm.colors.ListedColormap(['#f0f0f0', '#a0a0a0', '#4682b4', '#90ee90'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
    
    # Create the heatmap
    im = ax.imshow(datacenter.grid, cmap=cmap, norm=norm, origin='lower',
                  extent=[0, datacenter.width_m, 0, datacenter.length_m])
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_ticks([0, 1, 2, 3])
    
    # Set colorbar labels based on what's actually in the datacenter
    labels = ['Empty']
    if hasattr(datacenter, 'PILLAR'):
        labels.append('Pillar')
    else:
        labels.append('Obstacle')
    
    if hasattr(datacenter, 'RACK'):
        labels.append('Rack')
    else:
        labels.append('Equipment')
    
    if hasattr(datacenter, 'SUPPORT_ROOM'):
        labels.append('Support Room')
    elif hasattr(datacenter, 'WALL'):
        labels.append('Wall/Room')
    else:
        labels.append('Other')
    
    cbar.set_ticklabels(labels)
    
    # Add title and labels
    ax.set_title('Data Center Space Usage Heatmap')
    ax.set_xlabel('Width (meters)')
    ax.set_ylabel('Length (meters)')
    
    # Add metrics
    total_cells = datacenter.grid_width * datacenter.grid_length
    empty_cells = np.sum(datacenter.grid == 0)
    rack_cells = np.sum(datacenter.grid == 2)  # Assumes RACK=2
    usage_pct = 100 - (empty_cells / total_cells * 100)
    
    metrics_text = (
        f"Total cells: {total_cells}\n"
        f"Used: {total_cells - empty_cells} ({usage_pct:.1f}%)\n"
        f"Racks: {rack_cells} cells\n"
        f"Empty: {empty_cells} cells"
    )
    
    # Add metrics to the plot
    plt.figtext(0.02, 0.02, metrics_text, fontsize=10,
               bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
    
    plt.tight_layout()
    return fig, ax

def create_3d_visualization(datacenter, show_racks=True, show_pillars=True, show_rooms=True):
    """
    Create a 3D visualization of the data center.
    
    Args:
        datacenter: DataCenterGrid instance
        show_racks: Whether to show racks
        show_pillars: Whether to show pillars
        show_rooms: Whether to show support rooms
    
    Returns:
        Figure and axis
    """
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Set plot limits
    ax.set_xlim(0, datacenter.width_m)
    ax.set_ylim(0, datacenter.length_m)
    ax.set_zlim(0, 2.5)  # Standard rack height is about 2.2m
    
    # Draw floor
    floor_x = [0, datacenter.width_m, datacenter.width_m, 0, 0]
    floor_y = [0, 0, datacenter.length_m, datacenter.length_m, 0]
    floor_z = [0, 0, 0, 0, 0]
    ax.plot(floor_x, floor_y, floor_z, 'k-', alpha=0.3)
    
    # Draw pillars as 3D boxes
    if show_pillars and hasattr(datacenter, 'pillars'):
        for pillar in datacenter.pillars:
            # Bottom corners
            x1, y1 = pillar['x'], pillar['y']
            x2, y2 = x1 + pillar['width'], y1
            x3, y3 = x2, y1 + pillar['height']
            x4, y4 = x1, y3
            
            # Top corners (assuming 2.5m height)
            z_top = 2.5
            
            # Draw the pillar
            # Bottom
            ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], [0, 0, 0, 0, 0], 'k-')
            # Top
            ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], [z_top, z_top, z_top, z_top, z_top], 'k-')
            # Edges
            ax.plot([x1, x1], [y1, y1], [0, z_top], 'k-')
            ax.plot([x2, x2], [y2, y2], [0, z_top], 'k-')
            ax.plot([x3, x3], [y3, y3], [0, z_top], 'k-')
            ax.plot([x4, x4], [y4, y4], [0, z_top], 'k-')
            
            # Fill the faces
            # Use alpha to make it semi-transparent
            alpha = 0.3
            ax.fill([x1, x2, x3, x4], [y1, y2, y3, y4], [0], color='darkgray', alpha=alpha)
            ax.fill([x1, x2, x3, x4], [y1, y2, y3, y4], [z_top], color='darkgray', alpha=alpha)
            ax.fill([x1, x2, x2, x1], [y1, y2, y2, y1], [0, 0, z_top, z_top], color='darkgray', alpha=alpha)
            ax.fill([x2, x3, x3, x2], [y2, y3, y3, y2], [0, 0, z_top, z_top], color='darkgray', alpha=alpha)
            ax.fill([x3, x4, x4, x3], [y3, y4, y4, y3], [0, 0, z_top, z_top], color='darkgray', alpha=alpha)
            ax.fill([x4, x1, x1, x4], [y4, y1, y1, y4], [0, 0, z_top, z_top], color='darkgray', alpha=alpha)
    
    # Draw racks as 3D boxes
    if show_racks and hasattr(datacenter, 'racks'):
        rack_height = 2.0  # Standard rack height in meters
        
        for rack in datacenter.racks:
            # Bottom corners
            x1, y1 = rack['x'], rack['y']
            x2, y2 = x1 + rack['width'], y1
            x3, y3 = x2, y1 + rack['height']
            x4, y4 = x1, y3
            
            # Draw the rack similar to pillars
            # Bottom
            ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], [0, 0, 0, 0, 0], 'k-')
            # Top
            ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], [rack_height, rack_height, rack_height, rack_height, rack_height], 'k-')
            # Edges
            ax.plot([x1, x1], [y1, y1], [0, rack_height], 'k-')
            ax.plot([x2, x2], [y2, y2], [0, rack_height], 'k-')
            ax.plot([x3, x3], [y3, y3], [0, rack_height], 'k-')
            ax.plot([x4, x4], [y4, y4], [0, rack_height], 'k-')
            
            # Fill the faces with blue color
            alpha = 0.5
            ax.fill([x1, x2, x3, x4], [y1, y2, y3, y4], [0], color='royalblue', alpha=alpha)
            ax.fill([x1, x2, x3, x4], [y1, y2, y3, y4], [rack_height], color='royalblue', alpha=alpha)
            ax.fill([x1, x2, x2, x1], [y1, y2, y2, y1], [0, 0, rack_height, rack_height], color='royalblue', alpha=alpha)
            ax.fill([x2, x3, x3, x2], [y2, y3, y3, y2], [0, 0, rack_height, rack_height], color='royalblue', alpha=alpha)
            ax.fill([x3, x4, x4, x3], [y3, y4, y4, y3], [0, 0, rack_height, rack_height], color='royalblue', alpha=alpha)
            ax.fill([x4, x1, x1, x4], [y4, y1, y1, y4], [0, 0, rack_height, rack_height], color='royalblue', alpha=alpha)
    
    # Draw support rooms
    if show_rooms and hasattr(datacenter, 'support_rooms'):
        room_height = 2.5  # Support room height in meters
        
        for room in datacenter.support_rooms:
            # Bottom corners
            x1, y1 = room['x'], room['y']
            x2, y2 = x1 + room['width'], y1
            x3, y3 = x2, y1 + room['height']
            x4, y4 = x1, y3
            
            # Draw similar to pillars and racks
            # Bottom
            ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], [0, 0, 0, 0, 0], 'k-')
            # Top
            ax.plot([x1, x2, x3, x4, x1], [y1, y2, y3, y4, y1], [room_height, room_height, room_height, room_height, room_height], 'k-')
            # Edges
            ax.plot([x1, x1], [y1, y1], [0, room_height], 'k-')
            ax.plot([x2, x2], [y2, y2], [0, room_height], 'k-')
            ax.plot([x3, x3], [y3, y3], [0, room_height], 'k-')
            ax.plot([x4, x4], [y4, y4], [0, room_height], 'k-')
            
            # Fill the faces with green color
            alpha = 0.3
            ax.fill([x1, x2, x3, x4], [y1, y2, y3, y4], [0], color='lightgreen', alpha=alpha)
            ax.fill([x1, x2, x3, x4], [y1, y2, y3, y4], [room_height], color='lightgreen', alpha=alpha)
            ax.fill([x1, x2, x2, x1], [y1, y2, y2, y1], [0, 0, room_height, room_height], color='lightgreen', alpha=alpha)
            ax.fill([x2, x3, x3, x2], [y2, y3, y3, y2], [0, 0, room_height, room_height], color='lightgreen', alpha=alpha)
            ax.fill([x3, x4, x4, x3], [y3, y4, y4, y3], [0, 0, room_height, room_height], color='lightgreen', alpha=alpha)
            ax.fill([x4, x1, x1, x4], [y4, y1, y1, y4], [0, 0, room_height, room_height], color='lightgreen', alpha=alpha)
            
            # Add room label if name is available
            if 'name' in room:
                ax.text(x1 + room['width']/2, y1 + room['height']/2, room_height/2,
                       room['name'], ha='center', va='center')
    
    # Set labels
    ax.set_xlabel('Width (m)')
    ax.set_ylabel('Length (m)')
    ax.set_zlabel('Height (m)')
    ax.set_title('3D Data Center Visualization')
    
    return fig, ax