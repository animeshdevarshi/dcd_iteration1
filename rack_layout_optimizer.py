# rack_layout_optimizer.py
# Layout optimization for data center racks

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from datacenter_grid import DataCenterGrid
from rack_manager import RackManager
from pillar_manager import PillarManager

class RackLayoutOptimizer:
    """
    Class to generate and compare different rack layout strategies
    for a data center.
    """
    
    def __init__(self, datacenter_grid):
        """
        Initialize with a datacenter grid
        
        Args:
            datacenter_grid: A DataCenterGrid instance
        """
        self.grid = datacenter_grid
        self.rack_manager = RackManager(datacenter_grid)
        
        # Layout options
        self.LAYOUT_STANDARD = "standard"
        self.LAYOUT_HOT_COLD = "hot_cold_aisle"
        self.LAYOUT_DIAGONAL = "diagonal"
        self.LAYOUT_PERIMETER = "perimeter"
        self.LAYOUT_PODS = "pods"
        
        # Metrics for comparison
        self.layout_metrics = {}
        
    def generate_layout(self, layout_type, num_racks, **kwargs):
        """
        Generate a specific layout type
        
        Args:
            layout_type: Type of layout to generate
            num_racks: Number of racks to place
            **kwargs: Additional parameters specific to the layout type
        
        Returns:
            List of rack positions in grid coordinates
        """
        # Reset the grid - clear all racks
        self._clear_racks()
        
        # Default parameters
        params = {
            "top_margin": 3,
            "bottom_margin": 3,
            "left_margin": 3,
            "right_margin": 3,
            "row_spacing": 2,
            "aisle_width": 4,
            "pod_size": 16,  # For pod layout
            "diagonal_angle": 30  # For diagonal layout
        }
        
        # Update with user-provided parameters
        params.update(kwargs)
        
        # Generate the specified layout type
        if layout_type == self.LAYOUT_STANDARD:
            rack_positions = self._generate_standard_layout(num_racks, params)
        elif layout_type == self.LAYOUT_HOT_COLD:
            rack_positions = self._generate_hot_cold_layout(num_racks, params)
        elif layout_type == self.LAYOUT_DIAGONAL:
            rack_positions = self._generate_diagonal_layout(num_racks, params)
        elif layout_type == self.LAYOUT_PERIMETER:
            rack_positions = self._generate_perimeter_layout(num_racks, params)
        elif layout_type == self.LAYOUT_PODS:
            rack_positions = self._generate_pod_layout(num_racks, params)
        else:
            raise ValueError(f"Unknown layout type: {layout_type}")
        
        # Calculate metrics for this layout
        racks_placed = self.rack_manager.place_racks(rack_positions)
        self._calculate_metrics(layout_type, racks_placed, params)
        
        return rack_positions
    
    def _clear_racks(self):
        """Clear all racks from the grid"""
        # Remove rack elements from the grid
        for rack in self.grid.racks:
            for y in range(rack['grid_y'], rack['grid_y'] + rack.get('width_cells', rack.get('grid_width', 2))):
                for x in range(rack['grid_x'], rack['grid_x'] + rack.get('height_cells', rack.get('grid_height', 1))):
                    try:
                        # Only clear if it's a rack
                        if self.grid.grid[y, x] == self.grid.RACK:
                            self.grid.grid[y, x] = self.grid.EMPTY
                    except IndexError:
                        pass
        
        # Clear the rack list
        self.grid.racks = []
    
    def _generate_standard_layout(self, num_racks, params):
        """Generate a standard row-based layout"""
        return self.rack_manager.calculate_rack_positions(
            num_racks,
            top_margin=params["top_margin"],
            bottom_margin=params["bottom_margin"],
            left_margin=params["left_margin"],
            right_margin=params["right_margin"],
            row_spacing=params["row_spacing"]
        )
    
    def _generate_hot_cold_layout(self, num_racks, params):
        """Generate a hot/cold aisle layout"""
        return self.rack_manager.calculate_rack_positions_with_aisle(
            num_racks,
            top_margin=params["top_margin"],
            bottom_margin=params["bottom_margin"],
            left_margin=params["left_margin"],
            right_margin=params["right_margin"],
            row_spacing=params["row_spacing"],
            aisle_width=params["aisle_width"]
        )
    
    def _generate_diagonal_layout(self, num_racks, params):
        """
        Generate a diagonal layout where racks are arranged at an angle
        This can be useful for certain airflow patterns
        """
        # Available space after accounting for margins
        available_width = self.grid.grid_width - params["left_margin"] - params["right_margin"]
        available_height = self.grid.grid_length - params["top_margin"] - params["bottom_margin"]
        
        # Rack dimensions
        rack_width = self.rack_manager.RACK_WIDTH_CELLS
        rack_height = self.rack_manager.RACK_HEIGHT_CELLS
        
        # Convert angle to radians
        angle_rad = math.radians(params["diagonal_angle"])
        
        # Calculate how many racks fit in a diagonal row
        # This is a bit complex due to the angle
        diagonal_length = available_width * math.cos(angle_rad) + available_height * math.sin(angle_rad)
        racks_per_diagonal = int(diagonal_length / (rack_width * math.cos(angle_rad) + rack_height * math.sin(angle_rad)))
        
        # How many diagonal rows can we fit
        row_width = rack_width * math.sin(angle_rad) + rack_height * math.cos(angle_rad)
        diagonal_rows = int(available_width / (row_width + params["row_spacing"]))
        
        # Positioning
        rack_positions = []
        for row in range(min(diagonal_rows, (num_racks + racks_per_diagonal - 1) // racks_per_diagonal)):
            row_racks = min(racks_per_diagonal, num_racks - row * racks_per_diagonal)
            
            for i in range(row_racks):
                # Calculate position based on diagonal placement
                offset_x = i * rack_width * math.cos(angle_rad)
                offset_y = i * rack_width * math.sin(angle_rad)
                
                grid_x = params["left_margin"] + int(row * (row_width + params["row_spacing"]) + offset_x)
                grid_y = params["bottom_margin"] + int(offset_y)
                
                # Check if within bounds
                if (grid_x >= 0 and grid_x + rack_width <= self.grid.grid_width and
                    grid_y >= 0 and grid_y + rack_height <= self.grid.grid_length):
                    rack_positions.append((grid_x, grid_y))
        
        return rack_positions
    
    def _generate_perimeter_layout(self, num_racks, params):
        """
        Generate a perimeter layout where racks are placed along the edges
        This minimizes cable runs and can improve cooling in certain data centers
        """
        # Available space after accounting for margins
        available_width = self.grid.grid_width - params["left_margin"] - params["right_margin"]
        available_height = self.grid.grid_length - params["top_margin"] - params["bottom_margin"]
        
        # Rack dimensions
        rack_width = self.rack_manager.RACK_WIDTH_CELLS
        rack_height = self.rack_manager.RACK_HEIGHT_CELLS
        
        # Calculate how many racks fit on each side
        left_right_racks = available_height // rack_height
        top_bottom_racks = (available_width - 2 * rack_width) // rack_width  # Subtract corners
        
        total_perimeter_racks = 2 * left_right_racks + 2 * top_bottom_racks + 4  # +4 for corners
        
        # If we need more racks than fit on perimeter, add inner rings
        rack_positions = []
        current_margin = 0
        racks_needed = num_racks
        
        while racks_needed > 0 and current_margin * 2 < min(available_width, available_height):
            # Calculate dimensions of this ring
            ring_width = available_width - 2 * current_margin
            ring_height = available_height - 2 * current_margin
            
            # Calculate racks in this ring
            left_right = min(2 * (ring_height // rack_height), racks_needed)
            racks_needed -= left_right
            
            # If we still need racks, add top and bottom
            if racks_needed > 0:
                top_bottom = min(2 * ((ring_width - 2 * rack_width) // rack_width), racks_needed)
                racks_needed -= top_bottom
            else:
                top_bottom = 0
            
            # Calculate positions for this ring
            # Left side
            for i in range(min(ring_height // rack_height, left_right)):
                grid_x = params["left_margin"] + current_margin
                grid_y = params["bottom_margin"] + current_margin + i * rack_height
                rack_positions.append((grid_x, grid_y))
            
            # Right side
            for i in range(min(ring_height // rack_height, max(0, left_right - ring_height // rack_height))):
                grid_x = params["left_margin"] + current_margin + ring_width - rack_width
                grid_y = params["bottom_margin"] + current_margin + i * rack_height
                rack_positions.append((grid_x, grid_y))
            
            # Bottom side (excluding corners)
            for i in range(min((ring_width - 2 * rack_width) // rack_width, top_bottom)):
                grid_x = params["left_margin"] + current_margin + rack_width + i * rack_width
                grid_y = params["bottom_margin"] + current_margin
                rack_positions.append((grid_x, grid_y))
            
            # Top side (excluding corners)
            for i in range(min((ring_width - 2 * rack_width) // rack_width, max(0, top_bottom - (ring_width - 2 * rack_width) // rack_width))):
                grid_x = params["left_margin"] + current_margin + rack_width + i * rack_width
                grid_y = params["bottom_margin"] + current_margin + ring_height - rack_height
                rack_positions.append((grid_x, grid_y))
            
            # Move to the next inner ring
            current_margin += rack_width + params["row_spacing"]
        
        return rack_positions[:num_racks]
    
    def _generate_pod_layout(self, num_racks, params):
        """
        Generate a pod-based layout where racks are arranged in clusters (pods)
        This is common in modern data centers for more efficient cooling and maintenance
        """
        # Available space after accounting for margins
        available_width = self.grid.grid_width - params["left_margin"] - params["right_margin"]
        available_height = self.grid.grid_length - params["top_margin"] - params["bottom_margin"]
        
        # Rack dimensions
        rack_width = self.rack_manager.RACK_WIDTH_CELLS
        rack_height = self.rack_manager.RACK_HEIGHT_CELLS
        
        # Pod configuration (4x4 racks by default)
        pod_rows = int(math.sqrt(params["pod_size"]))
        pod_cols = params["pod_size"] // pod_rows
        
        # Pod dimensions including internal spacing
        pod_width = pod_cols * rack_width + (pod_cols - 1)
        pod_height = pod_rows * rack_height + (pod_rows - 1)
        
        # Calculate how many pods fit in each dimension
        pods_per_row = available_width // (pod_width + params["aisle_width"])
        pods_per_col = available_height // (pod_height + params["aisle_width"])
        
        # Total pods that will fit
        total_pods = pods_per_row * pods_per_col
        
        # Total racks we can fit in all pods
        total_racks_in_pods = total_pods * params["pod_size"]
        racks_to_place = min(num_racks, total_racks_in_pods)
        
        # Generate positions for all racks
        rack_positions = []
        racks_placed = 0
        
        for pod_row in range(pods_per_col):
            for pod_col in range(pods_per_row):
                # Skip this pod if we've placed enough racks
                if racks_placed >= racks_to_place:
                    break
                
                # Calculate pod position
                pod_x = params["left_margin"] + pod_col * (pod_width + params["aisle_width"])
                pod_y = params["bottom_margin"] + pod_row * (pod_height + params["aisle_width"])
                
                # Place racks within this pod
                for row in range(pod_rows):
                    for col in range(pod_cols):
                        # Skip if we've placed enough racks
                        if racks_placed >= racks_to_place:
                            break
                        
                        # Calculate rack position within pod
                        grid_x = pod_x + col * (rack_width + 1)
                        grid_y = pod_y + row * (rack_height + 1)
                        
                        rack_positions.append((grid_x, grid_y))
                        racks_placed += 1
        
        return rack_positions
    
    def _calculate_metrics(self, layout_type, racks, params):
        """Calculate and store metrics for a layout"""
        # Count racks actually placed
        racks_placed = len(racks)
        
        # Calculate space utilization
        total_space = self.grid.grid_width * self.grid.grid_length  # Total grid cells
        rack_space = sum(rack.get('width_cells', rack.get('grid_width', 2)) * 
                         rack.get('height_cells', rack.get('grid_height', 1)) 
                         for rack in racks)
        space_utilization = rack_space / total_space if total_space > 0 else 0
        
        # Calculate aisle accessibility score
        # TODO: Implement more sophisticated accessibility scoring
        
        # Store metrics
        self.layout_metrics[layout_type] = {
            "racks_placed": racks_placed,
            "space_utilization": space_utilization,
            "parameters": params
        }
    
    def compare_layouts(self, num_racks, plot=True):
        """
        Generate and compare different layout types
        
        Args:
            num_racks: Number of racks to place
            plot: Whether to plot the layouts
            
        Returns:
            Dictionary of metrics for each layout
        """
        layout_types = [
            self.LAYOUT_STANDARD,
            self.LAYOUT_HOT_COLD,
            self.LAYOUT_DIAGONAL,
            self.LAYOUT_PERIMETER,
            self.LAYOUT_PODS
        ]
        
        results = {}
        
        for layout_type in layout_types:
            try:
                print(f"Generating {layout_type} layout...")
                self.generate_layout(layout_type, num_racks)
                results[layout_type] = self.layout_metrics.get(layout_type, {})
                
                if plot:
                    from visualization import visualize_datacenter
                    fig, ax = visualize_datacenter(self.grid, title=f"{layout_type.replace('_', ' ').title()} Layout")
                    plt.close(fig)  # Close the figure to avoid display
            except Exception as e:
                print(f"Error generating {layout_type} layout: {e}")
        
        # Print comparison
        print("\nLayout Comparison:")
        print("=" * 50)
        for layout_type, metrics in results.items():
            print(f"{layout_type.replace('_', ' ').title()}:")
            print(f"  Racks placed: {metrics.get('racks_placed', 0)}/{num_racks}")
            print(f"  Space utilization: {metrics.get('space_utilization', 0):.2%}")
            print("-" * 50)
        
        return results
    
    def get_best_layout(self, num_racks, metric="space_utilization"):
        """
        Determine the best layout based on a specific metric
        
        Args:
            num_racks: Number of racks to place
            metric: Metric to use for comparison
            
        Returns:
            Tuple of (best_layout_type, metrics)
        """
        # First, generate all layouts if not already done
        if len(self.layout_metrics) < 5:  # 5 layout types
            self.compare_layouts(num_racks, plot=False)
        
        # Find the best layout
        best_layout = None
        best_value = -1
        
        for layout_type, metrics in self.layout_metrics.items():
            if metric in metrics:
                if metric == "space_utilization":
                    # Higher is better
                    if metrics[metric] > best_value:
                        best_value = metrics[metric]
                        best_layout = layout_type
                else:
                    # Assume higher is better for other metrics too
                    if metrics[metric] > best_value:
                        best_value = metrics[metric]
                        best_layout = layout_type
        
        return best_layout, self.layout_metrics.get(best_layout, {})

# Example usage
if __name__ == "__main__":
    # Create a data center grid
    datacenter = DataCenterGrid(45.0, 23.0)
    
    # Create optimizer
    optimizer = RackLayoutOptimizer(datacenter)
    
    # Compare different layouts for 80 racks
    optimizer.compare_layouts(80)