# simple_3d_visualization.py
# Simplified 3D visualization for data center layouts

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def create_simple_3d_visualization(datacenter, elevation=30, azimuth=45, show_racks=True, show_pillars=True):
    """
    Create a simplified 3D visualization of the data center.
    
    Args:
        datacenter: DataCenterGrid instance
        elevation: Viewing angle elevation in degrees
        azimuth: Viewing angle azimuth in degrees
        show_racks: Whether to show racks
        show_pillars: Whether to show pillars
    
    Returns:
        Figure and axis
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Set plot limits
    ax.set_xlim(0, datacenter.width_m)
    ax.set_ylim(0, datacenter.length_m)
    ax.set_zlim(0, 3)  # Maximum height in meters
    
    # Set viewing angle
    ax.view_init(elev=elevation, azim=azimuth)
    
    # Draw floor as a semi-transparent surface
    floor_x = np.array([[0, datacenter.width_m], [0, datacenter.width_m]])
    floor_y = np.array([[0, 0], [datacenter.length_m, datacenter.length_m]])
    floor_z = np.zeros((2, 2))
    
    ax.plot_surface(floor_x, floor_y, floor_z, alpha=0.3, color='gray', edgecolor='k', linewidth=0.5)
    
    # Draw room outline
    ax.plot([0, datacenter.width_m, datacenter.width_m, 0, 0], 
            [0, 0, datacenter.length_m, datacenter.length_m, 0], 
            [0, 0, 0, 0, 0], 'k-', linewidth=2)
    
    # Draw pillars if requested
    if show_pillars and hasattr(datacenter, 'pillars'):
        for pillar in datacenter.pillars:
            # Get pillar coordinates
            x, y = pillar['x'], pillar['y']
            w, h = pillar['width'], pillar['height']
            z_height = 2.5  # Standard ceiling height in meters
            
            # Define the 8 corners of the pillar (bottom and top)
            corners_x = [x, x+w, x+w, x, x, x+w, x+w, x]
            corners_y = [y, y, y+h, y+h, y, y, y+h, y+h]
            corners_z = [0, 0, 0, 0, z_height, z_height, z_height, z_height]
            
            # Draw the bottom face
            ax.plot([corners_x[0], corners_x[1], corners_x[2], corners_x[3], corners_x[0]],
                    [corners_y[0], corners_y[1], corners_y[2], corners_y[3], corners_y[0]],
                    [corners_z[0], corners_z[1], corners_z[2], corners_z[3], corners_z[0]], 'k-')
            
            # Draw the top face
            ax.plot([corners_x[4], corners_x[5], corners_x[6], corners_x[7], corners_x[4]],
                    [corners_y[4], corners_y[5], corners_y[6], corners_y[7], corners_y[4]],
                    [corners_z[4], corners_z[5], corners_z[6], corners_z[7], corners_z[4]], 'k-')
            
            # Draw the vertical edges
            for i in range(4):
                ax.plot([corners_x[i], corners_x[i+4]],
                        [corners_y[i], corners_y[i+4]],
                        [corners_z[i], corners_z[i+4]], 'k-')
            
            # Fill the faces with color
            # Top
            ax.plot_surface(
                np.array([[corners_x[4], corners_x[5]], [corners_x[7], corners_x[6]]]),
                np.array([[corners_y[4], corners_y[5]], [corners_y[7], corners_y[6]]]),
                np.array([[corners_z[4], corners_z[5]], [corners_z[7], corners_z[6]]]),
                color='darkgray', alpha=0.7
            )
            
            # Sides
            # Front
            ax.plot_surface(
                np.array([[corners_x[0], corners_x[1]], [corners_x[4], corners_x[5]]]),
                np.array([[corners_y[0], corners_y[1]], [corners_y[4], corners_y[5]]]),
                np.array([[corners_z[0], corners_z[1]], [corners_z[4], corners_z[5]]]),
                color='darkgray', alpha=0.7
            )
            
            # Right
            ax.plot_surface(
                np.array([[corners_x[1], corners_x[2]], [corners_x[5], corners_x[6]]]),
                np.array([[corners_y[1], corners_y[2]], [corners_y[5], corners_y[6]]]),
                np.array([[corners_z[1], corners_z[2]], [corners_z[5], corners_z[6]]]),
                color='darkgray', alpha=0.7
            )
            
            # Back
            ax.plot_surface(
                np.array([[corners_x[2], corners_x[3]], [corners_x[6], corners_x[7]]]),
                np.array([[corners_y[2], corners_y[3]], [corners_y[6], corners_y[7]]]),
                np.array([[corners_z[2], corners_z[3]], [corners_z[6], corners_z[7]]]),
                color='darkgray', alpha=0.7
            )
            
            # Left
            ax.plot_surface(
                np.array([[corners_x[3], corners_x[0]], [corners_x[7], corners_x[4]]]),
                np.array([[corners_y[3], corners_y[0]], [corners_y[7], corners_y[4]]]),
                np.array([[corners_z[3], corners_z[0]], [corners_z[7], corners_z[4]]]),
                color='darkgray', alpha=0.7
            )
    
    # Draw racks if requested
    if show_racks and hasattr(datacenter, 'racks'):
        # Group racks by row for coloring
        rack_rows = {}
        for rack in datacenter.racks:
            row_key = rack['grid_y']
            if row_key not in rack_rows:
                rack_rows[row_key] = []
            rack_rows[row_key].append(rack)
        
        # Generate colors for each row
        import matplotlib.cm as cm
        colors = cm.tab20(np.linspace(0, 1, len(rack_rows)))
        
        # Draw racks colored by row
        for i, (row_key, racks) in enumerate(rack_rows.items()):
            color = colors[i % len(colors)]
            
            for rack in racks:
                # Get rack coordinates
                x, y = rack['x'], rack['y']
                w, h = rack['width'], rack['height']
                z_height = 2.0  # Standard rack height in meters
                
                # Define the 8 corners of the rack (bottom and top)
                corners_x = [x, x+w, x+w, x, x, x+w, x+w, x]
                corners_y = [y, y, y+h, y+h, y, y, y+h, y+h]
                corners_z = [0, 0, 0, 0, z_height, z_height, z_height, z_height]
                
                # Draw the bottom face
                ax.plot([corners_x[0], corners_x[1], corners_x[2], corners_x[3], corners_x[0]],
                        [corners_y[0], corners_y[1], corners_y[2], corners_y[3], corners_y[0]],
                        [corners_z[0], corners_z[1], corners_z[2], corners_z[3], corners_z[0]], 'k-')
                
                # Draw the top face
                ax.plot([corners_x[4], corners_x[5], corners_x[6], corners_x[7], corners_x[4]],
                        [corners_y[4], corners_y[5], corners_y[6], corners_y[7], corners_y[4]],
                        [corners_z[4], corners_z[5], corners_z[6], corners_z[7], corners_z[4]], 'k-')
                
                # Draw the vertical edges
                for j in range(4):
                    ax.plot([corners_x[j], corners_x[j+4]],
                            [corners_y[j], corners_y[j+4]],
                            [corners_z[j], corners_z[j+4]], 'k-')
                
                # Fill the faces with color
                # Top
                ax.plot_surface(
                    np.array([[corners_x[4], corners_x[5]], [corners_x[7], corners_x[6]]]),
                    np.array([[corners_y[4], corners_y[5]], [corners_y[7], corners_y[6]]]),
                    np.array([[corners_z[4], corners_z[5]], [corners_z[7], corners_z[6]]]),
                    color=color, alpha=0.7
                )
                
                # Sides
                # Front
                ax.plot_surface(
                    np.array([[corners_x[0], corners_x[1]], [corners_x[4], corners_x[5]]]),
                    np.array([[corners_y[0], corners_y[1]], [corners_y[4], corners_y[5]]]),
                    np.array([[corners_z[0], corners_z[1]], [corners_z[4], corners_z[5]]]),
                    color=color, alpha=0.7
                )
                
                # Right
                ax.plot_surface(
                    np.array([[corners_x[1], corners_x[2]], [corners_x[5], corners_x[6]]]),
                    np.array([[corners_y[1], corners_y[2]], [corners_y[5], corners_y[6]]]),
                    np.array([[corners_z[1], corners_z[2]], [corners_z[5], corners_z[6]]]),
                    color=color, alpha=0.7
                )
                
                # Back
                ax.plot_surface(
                    np.array([[corners_x[2], corners_x[3]], [corners_x[6], corners_x[7]]]),
                    np.array([[corners_y[2], corners_y[3]], [corners_y[6], corners_y[7]]]),
                    np.array([[corners_z[2], corners_z[3]], [corners_z[6], corners_z[7]]]),
                    color=color, alpha=0.7
                )
                
                # Left
                ax.plot_surface(
                    np.array([[corners_x[3], corners_x[0]], [corners_x[7], corners_x[4]]]),
                    np.array([[corners_y[3], corners_y[0]], [corners_y[7], corners_y[4]]]),
                    np.array([[corners_z[3], corners_z[0]], [corners_z[7], corners_z[4]]]),
                    color=color, alpha=0.7
                )
                
                # Add rack ID
                rack_id = rack.get('id', f"R{datacenter.racks.index(rack)+1}")
                ax.text(x + w/2, y + h/2, z_height + 0.2, rack_id, ha='center', va='bottom')
    
    # Set labels
    ax.set_xlabel('Width (m)')
    ax.set_ylabel('Length (m)')
    ax.set_zlabel('Height (m)')
    ax.set_title('3D Data Center Visualization')
    
    return fig, ax
