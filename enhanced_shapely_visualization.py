# enhanced_shapely_visualization.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap

def visualize_datacenter_with_shapely(datacenter, title="Data Center Layout with Shapely", 
                                     show_metrics=True, highlight_zones=False, 
                                     cooling_analysis=True, show_grid=True):
    """
    Enhanced visualization for data center layouts using Shapely for geometric analysis.
    
    Args:
        datacenter: Instance of DataCenterGrid
        title: Title for the plot
        show_metrics: Whether to show metrics on the plot
        highlight_zones: Whether to highlight different zones (high/low density)
        cooling_analysis: Whether to show cooling analysis heatmap
        show_grid: Whether to show the grid lines
            
    Returns:
        Figure and axis objects, along with dictionary of Shapely geometries
    """
    # Create figure with appropriate size
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Set plot limits in meters with added margin
    x_margin, y_margin = 1, 1
    ax.set_xlim(-x_margin, datacenter.width_m + x_margin)
    ax.set_ylim(-y_margin, datacenter.length_m + y_margin)
    
    # Convert components to Shapely geometries
    geometries = {
        'room': box(0, 0, datacenter.width_m, datacenter.length_m),
        'pillars': [],
        'racks': [],
        'support_rooms': []
    }
    
    # Draw room outline
    room_outline = patches.Rectangle((0, 0), datacenter.width_m, datacenter.length_m, 
                                    linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(room_outline)
    
    # Draw grid lines if requested
    if show_grid:
        for i in range(0, datacenter.grid_width + 1):
            ax.axvline(i * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.2)
        for j in range(0, datacenter.grid_length + 1):
            ax.axhline(j * datacenter.grid_size_m, color='gray', linestyle='-', alpha=0.2)
    
    # Draw pillars and create Shapely geometries
    for pillar in datacenter.pillars:
        p = patches.Rectangle(
            (pillar['x'], pillar['y']),
            pillar['width'], pillar['height'],
            linewidth=1, edgecolor='red', facecolor='darkgray'
        )
        ax.add_patch(p)
        
        # Create Shapely geometry for this pillar
        pillar_poly = box(pillar['x'], pillar['y'], 
                         pillar['x'] + pillar['width'], 
                         pillar['y'] + pillar['height'])
        geometries['pillars'].append(pillar_poly)
    
    # Draw support rooms and create Shapely geometries
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
            
            # Create Shapely geometry for this room
            room_poly = box(room['x'], room['y'], 
                           room['x'] + room['width'], 
                           room['y'] + room['height'])
            geometries['support_rooms'].append(room_poly)
            
            # Add room label if name is available
            if 'name' in room:
                ax.text(
                    room['x'] + room['width']/2,
                    room['y'] + room['height']/2,
                    room['name'], ha='center', va='center', fontsize=10
                )
    
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
                
                # Create Shapely geometry for this rack
                rack_poly = box(rack['x'], rack['y'], 
                               rack['x'] + rack['width'], 
                               rack['y'] + rack['height'])
                geometries['racks'].append(rack_poly)
                
                # Add rack ID
                rack_id = rack.get('id', f'R{datacenter.racks.index(rack)+1}')
                ax.text(
                    rack['x'] + rack['width']/2,
                    rack['y'] + rack['height']/2,
                    rack_id, ha='center', va='center', 
                    color='white', fontsize=8, fontweight='bold'
                )
    
    # Use Shapely for cooling analysis
    if cooling_analysis:
        # Create a grid for the cooling heatmap
        resolution = 0.3  # meters per cell (higher resolution)
        cooling_grid_width = int(datacenter.width_m / resolution)
        cooling_grid_height = int(datacenter.length_m / resolution)
        cooling_grid = np.zeros((cooling_grid_height, cooling_grid_width))
        
        # Calculate a "clearance" map showing distance to nearest object
        if geometries['racks'] or geometries['pillars'] or geometries['support_rooms']:
            # Create a unified obstacle geometry
            obstacles = geometries['racks'] + geometries['pillars'] + geometries['support_rooms']
            if obstacles:
                all_obstacles = unary_union(obstacles)
                
                # Calculate cooling efficiency for each point in the grid
                for y in range(cooling_grid_height):
                    for x in range(cooling_grid_width):
                        # Convert grid coordinates to real-world coordinates
                        real_x = x * resolution
                        real_y = y * resolution
                        point = Point(real_x, real_y)
                        
                        # Calculate distance to nearest obstacle
                        if all_obstacles.contains(point):
                            # Point is inside an obstacle
                            distance = 0
                        else:
                            # Calculate distance to nearest obstacle
                            distance = all_obstacles.boundary.distance(point)
                        
                        # Apply cooling efficiency formula
                        # Areas closer to walls/corners are more efficient for cooling
                        wall_distance = min(
                            real_x, real_y, 
                            datacenter.width_m - real_x, 
                            datacenter.length_m - real_y
                        )
                        
                        # Cooling is better near walls but not too close to obstacles
                        cooling_grid[y, x] = 0.7 * (1 - min(wall_distance, 5) / 5) + 0.3 * min(distance, 3) / 3
        
        # Create a custom colormap for cooling efficiency
        colors = [(0.8, 0, 0), (1, 1, 0), (0, 0.8, 0)]  # Red -> Yellow -> Green
        cmap = LinearSegmentedColormap.from_list('cooling_cmap', colors, N=100)
        
        # Display the heatmap with transparency
        cooling_img = ax.imshow(cooling_grid, origin='lower', 
                               extent=[0, datacenter.width_m, 0, datacenter.length_m],
                               cmap=cmap, alpha=0.3, interpolation='bilinear')
        
        # Add colorbar
        cbar = plt.colorbar(cooling_img, ax=ax)
        cbar.set_label('Cooling Efficiency')
    
    # Use Shapely to calculate hot spots (areas with high rack density)
    if highlight_zones:
        # Create buffer zones around each rack to identify high density areas
        rack_buffers = []
        for rack_poly in geometries['racks']:
            # Create a 1-meter buffer around each rack
            buffer = rack_poly.buffer(1.0)
            rack_buffers.append(buffer)
        
        if rack_buffers:
            # Combine all buffers
            all_buffers = unary_union(rack_buffers)
            
            # Find areas where buffers overlap (high density)
            # This is an approximation - we could do more sophisticated analysis
            # For each rack, count how many other rack buffers it intersects
            high_density_areas = []
            for i, rack_poly in enumerate(geometries['racks']):
                intersect_count = 0
                for j, other_buffer in enumerate(rack_buffers):
                    if i != j and rack_poly.intersects(other_buffer):
                        intersect_count += 1
                
                if intersect_count >= 3:  # Arbitrary threshold for "high density"
                    high_density_areas.append(rack_poly.buffer(0.5))
            
            if high_density_areas:
                # Combine high density areas
                combined_high_density = unary_union(high_density_areas)
                
                # Add to the plot as a highlighted zone
                from descartes import PolygonPatch
                high_density_patch = PolygonPatch(
                    combined_high_density,
                    fc='red', ec='none', alpha=0.2,
                    label='High Density Zone'
                )
                ax.add_patch(high_density_patch)
    
    # Add metrics if requested
    if show_metrics:
        # Calculate metrics using Shapely
        total_area = geometries['room'].area
        
        # Calculate rack area and utilization
        rack_area = sum(p.area for p in geometries['racks'])
        pillar_area = sum(p.area for p in geometries['pillars'])
        support_room_area = sum(p.area for p in geometries['support_rooms'])
        
        # Calculate usable area (total minus pillars and support rooms)
        usable_area = total_area - pillar_area - support_room_area
        
        # Calculate space utilization
        density = rack_area / usable_area if usable_area > 0 else 0
        
        # Calculate walkways (negative space)
        obstacle_union = unary_union(geometries['racks'] + geometries['pillars'] + geometries['support_rooms'])
        walkway_area = geometries['room'].area - obstacle_union.area
        
        # Calculate rack zone metrics
        rack_hulls = []
        if geometries['racks']:
            from shapely.ops import cascaded_union
            rack_hull = unary_union(geometries['racks']).convex_hull
            rack_zone_area = rack_hull.area
            rack_zone_util = rack_area / rack_zone_area if rack_zone_area > 0 else 0
        else:
            rack_zone_area = 0
            rack_zone_util = 0
        
        # Create metrics text
        metrics_text = (
            f"Racks: {len(geometries['racks'])}\n"
            f"Rack Area: {rack_area:.1f} m²\n"
            f"Usable Area: {usable_area:.1f} m²\n"
            f"Space Utilization: {density:.1%}\n"
            f"Walkway Area: {walkway_area:.1f} m²\n"
            f"Rack Zone Utilization: {rack_zone_util:.1%}"
        )
        
        # Add metrics to plot
        plt.figtext(0.02, 0.02, metrics_text, fontsize=10,
                   bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
    
    # Optional: Calculate and display Shapely-based airflow paths
    # This would show optimal airflow channels between rack rows
    
    # Set title, labels and grid
    ax.set_title(title, pad=20, fontsize=14)
    ax.set_xlabel("Width (meters)", labelpad=10)
    ax.set_ylabel("Length (meters)", labelpad=10)
    
    # Add legend for zones if needed
    if highlight_zones:
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', alpha=0.2, label='High Density Zone')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    return fig, ax, geometries

def calculate_optimal_rack_clearance(datacenter, geometries, min_clearance=0.9):
    """
    Calculate and visualize optimal rack clearances using Shapely.
    This helps ensure adequate cooling and maintenance access.
    
    Args:
        datacenter: DataCenterGrid instance
        geometries: Dictionary of Shapely geometries
        min_clearance: Minimum required clearance in meters
    
    Returns:
        Figure and axis with clearance visualization
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Set plot limits
    ax.set_xlim(0, datacenter.width_m)
    ax.set_ylim(0, datacenter.length_m)
    
    # Draw room outline
    room_outline = patches.Rectangle((0, 0), datacenter.width_m, datacenter.length_m, 
                                     linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(room_outline)
    
    # Draw all objects from the datacenter
    # Draw pillars
    for pillar in datacenter.pillars:
        p = patches.Rectangle(
            (pillar['x'], pillar['y']),
            pillar['width'], pillar['height'],
            linewidth=1, edgecolor='black', facecolor='darkgray'
        )
        ax.add_patch(p)
    
    # Draw racks with clearance buffers
    for i, rack in enumerate(datacenter.racks):
        # Draw the rack
        r = patches.Rectangle(
            (rack['x'], rack['y']),
            rack['width'], rack['height'],
            linewidth=1, edgecolor='black', facecolor='royalblue', alpha=0.8
        )
        ax.add_patch(r)
        
        # Get the corresponding Shapely geometry
        if i < len(geometries['racks']):
            rack_poly = geometries['racks'][i]
            
            # Create buffer for minimum clearance
            buffer = rack_poly.buffer(min_clearance)
            
            # Draw the clearance buffer
            from descartes import PolygonPatch
            buffer_patch = PolygonPatch(
                buffer, fc='none', ec='green', alpha=0.5, linestyle='--'
            )
            ax.add_patch(buffer_patch)
            
            # Check if this buffer overlaps with other racks or obstacles
            other_racks = [geo for j, geo in enumerate(geometries['racks']) if j != i]
            obstacles = geometries['pillars'] + geometries['support_rooms'] + other_racks
            
            for obstacle in obstacles:
                if buffer.intersects(obstacle):
                    # There's a clearance issue - highlight the intersection
                    intersection = buffer.intersection(obstacle)
                    if not intersection.is_empty:
                        intersection_patch = PolygonPatch(
                            intersection, fc='red', ec='none', alpha=0.4
                        )
                        ax.add_patch(intersection_patch)
    
    # Calculate and highlight airflow channels
    if geometries['racks']:
        # Create a unified obstacle geometry (everything that blocks airflow)
        obstacles = unary_union(geometries['racks'] + geometries['pillars'] + geometries['support_rooms'])
        
        # The negative space is the potential airflow channels
        airflow_channels = geometries['room'].difference(obstacles)
        
        # Draw the airflow channels
        from descartes import PolygonPatch
        channel_patch = PolygonPatch(
            airflow_channels, fc='lightskyblue', ec='none', alpha=0.2,
            label='Airflow Channels'
        )
        ax.add_patch(channel_patch)
        
        # Find narrow channels that might restrict airflow
        # This is an approximation using buffer operations
        narrow_areas = []
        for width in [0.6, 0.9, 1.2]:  # Different width thresholds
            eroded = airflow_channels.buffer(-width/2)
            dilated = eroded.buffer(width/2)
            narrow = airflow_channels.difference(dilated)
            if not narrow.is_empty:
                narrow_areas.append((narrow, width))
        
        # Draw narrow areas with different colors based on width
        colors = ['gold', 'orange', 'red']
        for i, (narrow, width) in enumerate(narrow_areas):
            if not narrow.is_empty:
                narrow_patch = PolygonPatch(
                    narrow, fc=colors[i % len(colors)], ec='none', alpha=0.5,
                    label=f'<{width}m passage'
                )
                ax.add_patch(narrow_patch)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='royalblue', alpha=0.8, label='Rack'),
        Patch(facecolor='none', edgecolor='green', alpha=0.5, linestyle='--', label=f'Min {min_clearance}m Clearance'),
        Patch(facecolor='red', alpha=0.4, label='Clearance Issue'),
        Patch(facecolor='lightskyblue', alpha=0.2, label='Airflow Channel'),
        Patch(facecolor='gold', alpha=0.5, label='<0.6m passage'),
        Patch(facecolor='orange', alpha=0.5, label='<0.9m passage'),
        Patch(facecolor='red', alpha=0.5, label='<1.2m passage')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Add title and labels
    ax.set_title("Rack Clearance and Airflow Analysis", fontsize=14)
    ax.set_xlabel("Width (meters)")
    ax.set_ylabel("Length (meters)")
    
    plt.tight_layout()
    return fig, ax

def calculate_cable_paths(datacenter, geometries, source_racks, destination_racks):
    """
    Calculate and visualize optimal cable paths between racks using Shapely.
    
    Args:
        datacenter: DataCenterGrid instance
        geometries: Dictionary of Shapely geometries
        source_racks: List of source rack indices
        destination_racks: List of destination rack indices
        
    Returns:
        Figure and axis with cable path visualization
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Set plot limits
    ax.set_xlim(0, datacenter.width_m)
    ax.set_ylim(0, datacenter.length_m)
    
    # Draw room outline
    room_outline = patches.Rectangle((0, 0), datacenter.width_m, datacenter.length_m, 
                                     linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(room_outline)
    
    # Draw all racks, pillars, and support rooms
    # Draw pillars
    for pillar in datacenter.pillars:
        p = patches.Rectangle(
            (pillar['x'], pillar['y']),
            pillar['width'], pillar['height'],
            linewidth=1, edgecolor='black', facecolor='darkgray'
        )
        ax.add_patch(p)
    
    # Draw all racks
    for i, rack in enumerate(datacenter.racks):
        # Color differently based on whether it's a source, destination, or other
        if i in source_racks:
            color = 'green'
        elif i in destination_racks:
            color = 'red'
        else:
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
    
    # Draw support rooms
    if hasattr(datacenter, 'support_rooms') and datacenter.support_rooms:
        for room in datacenter.support_rooms:
            r = patches.Rectangle(
                (room['x'], room['y']),
                room['width'], room['height'],
                linewidth=1, edgecolor='black', facecolor='lightgreen', alpha=0.7
            )
            ax.add_patch(r)
    
    # Create a unified obstacle geometry for pathfinding
    obstacles = unary_union(geometries['racks'] + geometries['pillars'] + geometries['support_rooms'])
    
    # Buffer obstacles slightly to ensure paths don't run too close
    buffered_obstacles = obstacles.buffer(0.3)
    
    # The available space for cable paths
    available_space = geometries['room'].difference(buffered_obstacles)
    
    # Draw the available space as a semi-transparent layer
    from descartes import PolygonPatch
    available_patch = PolygonPatch(
        available_space, fc='lightskyblue', ec='none', alpha=0.1
    )
    ax.add_patch(available_patch)
    
    # Calculate paths between source and destination racks
    # This is where we would use a pathfinding algorithm with Shapely
    # For this example, we'll use a simplified approach with centroids and straight lines
    
    # For each source-destination pair, find a path
    for src_idx in source_racks:
        for dst_idx in destination_racks:
            if src_idx < len(geometries['racks']) and dst_idx < len(geometries['racks']):
                src_rack = geometries['racks'][src_idx]
                dst_rack = geometries['racks'][dst_idx]
                
                # Get centroids
                src_centroid = src_rack.centroid
                dst_centroid = dst_rack.centroid
                
                # Create a line between them
                direct_line = LineString([
                    (src_centroid.x, src_centroid.y),
                    (dst_centroid.x, dst_centroid.y)
                ])
                
                # Check if the direct line intersects any obstacles
                if direct_line.intersects(buffered_obstacles):
                    # In a real implementation, we would use a pathfinding algorithm here
                    # For now, we'll just draw the direct line in red to indicate an issue
                    ax.plot([src_centroid.x, dst_centroid.x], 
                           [src_centroid.y, dst_centroid.y], 
                           'r-', linewidth=2, alpha=0.7, linestyle='--')
                else:
                    # Direct path is clear
                    ax.plot([src_centroid.x, dst_centroid.x], 
                           [src_centroid.y, dst_centroid.y], 
                           'g-', linewidth=2, alpha=0.7)
    
    # Add legend
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor='green', alpha=0.8, label='Source Rack'),
        Patch(facecolor='red', alpha=0.8, label='Destination Rack'),
        Patch(facecolor='royalblue', alpha=0.8, label='Other Rack'),
        Patch(facecolor='lightskyblue', alpha=0.1, label='Available Path Space'),
        Line2D([0], [0], color='g', linewidth=2, linestyle='-', label='Clear Path'),
        Line2D([0], [0], color='r', linewidth=2, linestyle='--', label='Obstructed Path')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Add title and labels
    ax.set_title("Cable Path Analysis", fontsize=14)
    ax.set_xlabel("Width (meters)")
    ax.set_ylabel("Length (meters)")
    
    plt.tight_layout()
    return fig, ax