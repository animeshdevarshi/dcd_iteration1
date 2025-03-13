# advanced_layout_strategies.py
# Advanced rack layout strategies for data centers

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

class AdvancedRackLayoutStrategies:
    """
    Class that implements advanced rack layout strategies for data centers.
    Can be used with the RackLayoutOptimizer to experiment with additional layouts.
    """
    
    def __init__(self, datacenter_grid):
        """
        Initialize with a datacenter grid
        
        Args:
            datacenter_grid: A DataCenterGrid instance
        """
        self.grid = datacenter_grid
        
        # Get rack dimensions from the grid
        # Default rack dimensions if not available
        self.RACK_WIDTH_CELLS = 2
        self.RACK_HEIGHT_CELLS = 1
        
        # Try to get rack dimensions from the grid's rack manager (if available)
        rack_mgr_attrs = dir(self.grid)
        if 'rack_width_cells' in rack_mgr_attrs:
            self.RACK_WIDTH_CELLS = self.grid.rack_width_cells
        if 'rack_height_cells' in rack_mgr_attrs:
            self.RACK_HEIGHT_CELLS = self.grid.rack_height_cells
    
    def generate_spine_leaf_layout(self, num_racks, params):
        """
        Generate a spine-leaf network-inspired layout.
        This layout optimizes for network traffic patterns in modern data centers.
        
        Args:
            num_racks: Number of racks to place
            params: Dictionary of parameters
            
        Returns:
            List of rack positions (grid_x, grid_y)
        """
        # Extract params with defaults
        top_margin = params.get("top_margin", 3)
        bottom_margin = params.get("bottom_margin", 3)
        left_margin = params.get("left_margin", 3)
        right_margin = params.get("right_margin", 3)
        row_spacing = params.get("row_spacing", 2)
        spine_width = params.get("spine_width", 4)  # Width of spine aisles
        
        # Available space after accounting for margins
        available_width = self.grid.grid_width - left_margin - right_margin
        available_height = self.grid.grid_length - top_margin - bottom_margin
        
        # Calculate spine and leaf dimensions
        num_spines = max(1, available_width // 20)  # One spine aisle per ~20 grid cells
        spine_positions = []
        
        for i in range(num_spines):
            pos_x = left_margin + i * (available_width / num_spines)
            spine_positions.append(int(pos_x))
        
        # Calculate leaf rows between spines
        leaf_sections = []
        for i in range(len(spine_positions)):
            start_x = spine_positions[i] + spine_width if i > 0 else left_margin
            end_x = spine_positions[i+1] if i < len(spine_positions)-1 else left_margin + available_width
            
            if end_x - start_x >= self.RACK_WIDTH_CELLS:
                leaf_sections.append((start_x, end_x))
        
        # Calculate rack positions
        rack_positions = []
        racks_needed = num_racks
        
        # Place racks in leaf sections
        for start_x, end_x in leaf_sections:
            section_width = end_x - start_x
            racks_per_row = section_width // self.RACK_WIDTH_CELLS
            
            if racks_per_row <= 0:
                continue
            
            # Calculate how many rows we need in this section
            rows_needed = min((racks_needed + racks_per_row - 1) // racks_per_row,
                             available_height // (self.RACK_HEIGHT_CELLS + row_spacing))
            
            for row in range(rows_needed):
                row_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + row_spacing)
                racks_in_row = min(racks_per_row, racks_needed)
                
                for rack in range(racks_in_row):
                    grid_x = start_x + rack * self.RACK_WIDTH_CELLS
                    grid_y = row_y
                    rack_positions.append((grid_x, grid_y))
                    racks_needed -= 1
                    
                    if racks_needed <= 0:
                        break
                
                if racks_needed <= 0:
                    break
        
        return rack_positions
    
    def generate_cluster_layout(self, num_racks, params):
        """
        Generate a cluster-based layout optimized for workload isolation.
        This layout creates distinct clusters with their own cooling and power domains.
        
        Args:
            num_racks: Number of racks to place
            params: Dictionary of parameters
            
        Returns:
            List of rack positions (grid_x, grid_y)
        """
        # Extract params with defaults
        top_margin = params.get("top_margin", 3)
        bottom_margin = params.get("bottom_margin", 3)
        left_margin = params.get("left_margin", 3)
        right_margin = params.get("right_margin", 3)
        cluster_spacing = params.get("cluster_spacing", 4)  # Spacing between clusters
        cluster_size = params.get("cluster_size", 8)  # Racks per cluster
        
        # Available space after accounting for margins
        available_width = self.grid.grid_width - left_margin - right_margin
        available_height = self.grid.grid_length - top_margin - bottom_margin
        
        # Calculate cluster dimensions
        cluster_width = int(math.sqrt(cluster_size)) * self.RACK_WIDTH_CELLS + cluster_spacing
        cluster_height = ((cluster_size + int(math.sqrt(cluster_size)) - 1) // int(math.sqrt(cluster_size))) * self.RACK_HEIGHT_CELLS + cluster_spacing
        
        # Calculate how many clusters fit
        clusters_per_row = available_width // cluster_width
        clusters_per_col = available_height // cluster_height
        
        total_clusters = clusters_per_row * clusters_per_col
        total_racks_in_clusters = total_clusters * cluster_size
        
        if total_racks_in_clusters < num_racks:
            print(f"Warning: Can only fit {total_racks_in_clusters} racks in {total_clusters} clusters")
        
        # Place racks in clusters
        rack_positions = []
        racks_needed = min(num_racks, total_racks_in_clusters)
        
        for cluster_row in range(clusters_per_col):
            for cluster_col in range(clusters_per_row):
                # Calculate cluster position
                cluster_x = left_margin + cluster_col * cluster_width
                cluster_y = bottom_margin + cluster_row * cluster_height
                
                # Calculate number of racks in this cluster
                racks_in_cluster = min(cluster_size, racks_needed)
                
                if racks_in_cluster <= 0:
                    break
                
                # Place racks in a grid pattern within the cluster
                cluster_grid_width = int(math.sqrt(cluster_size))
                cluster_grid_height = (cluster_size + cluster_grid_width - 1) // cluster_grid_width
                
                for i in range(min(cluster_grid_height, (racks_in_cluster + cluster_grid_width - 1) // cluster_grid_width)):
                    for j in range(min(cluster_grid_width, racks_in_cluster - i * cluster_grid_width)):
                        grid_x = cluster_x + j * self.RACK_WIDTH_CELLS
                        grid_y = cluster_y + i * self.RACK_HEIGHT_CELLS
                        
                        rack_positions.append((grid_x, grid_y))
                        racks_needed -= 1
                        
                        if racks_needed <= 0:
                            break
                    
                    if racks_needed <= 0:
                        break
                
                if racks_needed <= 0:
                    break
            
            if racks_needed <= 0:
                break
        
        return rack_positions
    
    def generate_circular_layout(self, num_racks, params):
        """
        Generate a circular/radial layout.
        This layout can be beneficial for certain cooling strategies and visual appeal.
        
        Args:
            num_racks: Number of racks to place
            params: Dictionary of parameters
            
        Returns:
            List of rack positions (grid_x, grid_y)
        """
        # Extract params with defaults
        center_x = params.get("center_x", self.grid.grid_width // 2)
        center_y = params.get("center_y", self.grid.grid_length // 2)
        min_radius = params.get("min_radius", 5)  # Minimum radius in grid cells
        spacing = params.get("spacing", 1)  # Spacing between rings
        
        # Calculate available space
        max_radius_x = min(center_x, self.grid.grid_width - center_x) - 1
        max_radius_y = min(center_y, self.grid.grid_length - center_y) - 1
        max_radius = min(max_radius_x, max_radius_y)
        
        if min_radius >= max_radius:
            print(f"Warning: Minimum radius ({min_radius}) is too large for the room")
            min_radius = max(1, max_radius - 5)
        
        # Generate rack positions in concentric rings
        rack_positions = []
        current_radius = min_radius
        racks_placed = 0
        
        while current_radius <= max_radius and racks_placed < num_racks:
            # Calculate circumference of this ring
            circumference = 2 * math.pi * current_radius
            
            # Calculate how many racks fit in this ring
            # Each rack occupies an arc length proportional to its width
            arc_length = self.RACK_WIDTH_CELLS
            racks_in_ring = min(int(circumference / arc_length), num_racks - racks_placed)
            
            if racks_in_ring <= 0:
                break
            
            # Place racks evenly around the ring
            for i in range(racks_in_ring):
                angle = 2 * math.pi * i / racks_in_ring
                
                # Calculate grid position
                grid_x = int(center_x + current_radius * math.cos(angle))
                grid_y = int(center_y + current_radius * math.sin(angle))
                
                # Adjust for rack dimensions
                grid_x -= self.RACK_WIDTH_CELLS // 2
                grid_y -= self.RACK_HEIGHT_CELLS // 2
                
                # Check if within grid bounds
                if (grid_x >= 0 and grid_x + self.RACK_WIDTH_CELLS <= self.grid.grid_width and
                    grid_y >= 0 and grid_y + self.RACK_HEIGHT_CELLS <= self.grid.grid_length):
                    rack_positions.append((grid_x, grid_y))
                    racks_placed += 1
            
            # Move to the next ring
            current_radius += self.RACK_WIDTH_CELLS + spacing
        
        return rack_positions[:num_racks]
    
    def generate_cooling_optimized_layout(self, num_racks, params):
        """
        Generate a layout optimized for cooling efficiency.
        This layout creates a pattern that maximizes airflow and cooling efficiency.
        
        Args:
            num_racks: Number of racks to place
            params: Dictionary of parameters
            
        Returns:
            List of rack positions (grid_x, grid_y)
        """
        # Extract params with defaults
        top_margin = params.get("top_margin", 3)
        bottom_margin = params.get("bottom_margin", 3)
        left_margin = params.get("left_margin", 3)
        right_margin = params.get("right_margin", 3)
        row_spacing = params.get("row_spacing", 2)
        cold_aisle_width = params.get("cold_aisle_width", 3)
        hot_aisle_width = params.get("hot_aisle_width", 4)
        
        # Available space after accounting for margins
        available_width = self.grid.grid_width - left_margin - right_margin
        available_height = self.grid.grid_length - top_margin - bottom_margin
        
        # Cooling layout uses alternating hot and cold aisles
        # We'll start and end with cold aisles
        
        # Calculate how many aisles we can fit
        aisle_pair_width = 2 * self.RACK_WIDTH_CELLS + cold_aisle_width + hot_aisle_width
        num_aisle_pairs = available_width // aisle_pair_width
        
        if num_aisle_pairs == 0:
            print("Warning: Room too narrow for cooling-optimized layout")
            # Fall back to a single hot/cold aisle pair
            cold_aisle_width = max(2, (available_width - 2 * self.RACK_WIDTH_CELLS) // 2)
            hot_aisle_width = cold_aisle_width
            num_aisle_pairs = 1
        
        # Calculate how many racks fit in each row
        racks_per_row = num_aisle_pairs * 2  # Two rack rows per aisle pair
        
        # Calculate how many rows we need
        rows_needed = (num_racks + racks_per_row - 1) // racks_per_row
        
        # Check if we have enough vertical space
        total_height_needed = rows_needed * (self.RACK_HEIGHT_CELLS + row_spacing) - row_spacing
        
        if total_height_needed > available_height:
            print(f"Warning: Not enough vertical space for {num_racks} racks. Will place as many as possible.")
            rows_needed = available_height // (self.RACK_HEIGHT_CELLS + row_spacing)
        
        # Generate rack positions
        rack_positions = []
        racks_needed = num_racks
        
        for row in range(rows_needed):
            row_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + row_spacing)
            
            # Place racks in this row
            for aisle_pair in range(num_aisle_pairs):
                # Calculate the start of this aisle pair
                aisle_start_x = left_margin + aisle_pair * aisle_pair_width
                
                # Place racks on the left side of the cold aisle
                grid_x = aisle_start_x
                rack_positions.append((grid_x, row_y))
                racks_needed -= 1
                
                if racks_needed <= 0:
                    break
                
                # Place racks on the right side of the cold aisle (facing the hot aisle)
                grid_x = aisle_start_x + self.RACK_WIDTH_CELLS + cold_aisle_width
                rack_positions.append((grid_x, row_y))
                racks_needed -= 1
                
                if racks_needed <= 0:
                    break
            
            if racks_needed <= 0:
                break
        
        return rack_positions[:num_racks]
    
    def generate_high_density_zones_layout(self, num_racks, params):
        """
        Generate a layout with high and low density zones.
        This is useful when you have racks with different power/cooling requirements.
        
        Args:
            num_racks: Number of racks to place
            params: Dictionary of parameters
            
        Returns:
            List of rack positions (grid_x, grid_y)
        """
        # Extract params with defaults
        top_margin = params.get("top_margin", 3)
        bottom_margin = params.get("bottom_margin", 3)
        left_margin = params.get("left_margin", 3)
        right_margin = params.get("right_margin", 3)
        high_density_pct = params.get("high_density_pct", 30)  # Percentage of racks that are high density
        high_density_spacing = params.get("high_density_spacing", 2)  # Extra spacing for high density racks
        
        # Calculate high and low density counts
        high_density_count = int(num_racks * high_density_pct / 100)
        low_density_count = num_racks - high_density_count
        
        # Available space after accounting for margins
        available_width = self.grid.grid_width - left_margin - right_margin
        available_height = self.grid.grid_length - top_margin - bottom_margin
        
        # We'll place high density racks on the left side (better cooling)
        # and low density racks on the right side
        
        # Divide the available space
        high_density_width = int(available_width * (high_density_count / num_racks) * 1.5)  # Extra space for high density
        low_density_width = available_width - high_density_width
        
        # Calculate rack positions
        rack_positions = []
        
        # Place high density racks with extra spacing
        hd_racks_per_row = high_density_width // (self.RACK_WIDTH_CELLS + high_density_spacing)
        if hd_racks_per_row <= 0:
            hd_racks_per_row = 1
        
        hd_rows_needed = (high_density_count + hd_racks_per_row - 1) // hd_racks_per_row
        
        for row in range(hd_rows_needed):
            row_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + high_density_spacing)
            
            for col in range(min(hd_racks_per_row, high_density_count - row * hd_racks_per_row)):
                grid_x = left_margin + col * (self.RACK_WIDTH_CELLS + high_density_spacing)
                rack_positions.append((grid_x, row_y))
        
        # Place low density racks normally
        ld_racks_per_row = low_density_width // self.RACK_WIDTH_CELLS
        if ld_racks_per_row <= 0:
            ld_racks_per_row = 1
        
        ld_rows_needed = (low_density_count + ld_racks_per_row - 1) // ld_racks_per_row
        
        for row in range(ld_rows_needed):
            row_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + 1)  # Standard spacing
            
            for col in range(min(ld_racks_per_row, low_density_count - row * ld_racks_per_row)):
                grid_x = left_margin + high_density_width + col * self.RACK_WIDTH_CELLS
                rack_positions.append((grid_x, row_y))
        
        return rack_positions[:num_racks]

# Example usage
if __name__ == "__main__":
    from datacenter_grid import DataCenterGrid
    
    # Create a data center grid
    datacenter = DataCenterGrid(45.0, 23.0)
    
    # Create advanced layout strategies
    strategies = AdvancedRackLayoutStrategies(datacenter)
    
    # Generate a layout
    rack_positions = strategies.generate_spine_leaf_layout(80, {})
    print(f"Generated {len(rack_positions)} rack positions")