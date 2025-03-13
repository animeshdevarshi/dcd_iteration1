# datacenter_grid.py
# Base class for data center grid representation

import numpy as np
import math

class DataCenterGrid:
    """
    A class that manages a grid-based data center layout.
    """
    # Element type constants
    EMPTY = 0
    PILLAR = 1
    RACK = 2
    WALL = 3
    
    def __init__(self, width_m, length_m, grid_size_m=0.6):
        """
        Initialize the data center grid.
        
        Args:
            width_m (float): Width of the data center in meters
            length_m (float): Length of the data center in meters
            grid_size_m (float): Size of each grid cell in meters (default: 0.6m or 600mm)
        """
        self.width_m = width_m
        self.length_m = length_m
        self.grid_size_m = grid_size_m
        
        # Calculate grid dimensions
        self.grid_width = int(np.ceil(width_m / grid_size_m))
        self.grid_length = int(np.ceil(length_m / grid_size_m))
        
        # Initialize grid (0 = empty)
        self.grid = np.zeros((self.grid_length, self.grid_width), dtype=int)
        
        # Lists to store elements
        self.pillars = []
        self.racks = []
        self.walls = []
        self.support_rooms = []  # Added for compatibility
        
        print(f"Created data center grid: {width_m}m × {length_m}m")
        print(f"Using standard {grid_size_m*1000:.0f}mm × {grid_size_m*1000:.0f}mm grid: {self.grid_width} × {self.grid_length} cells")
    
    def get_grid_coordinates(self, x_m, y_m):
        """
        Convert real-world coordinates to grid coordinates.
        
        Args:
            x_m (float): X coordinate in meters
            y_m (float): Y coordinate in meters
            
        Returns:
            tuple: (grid_x, grid_y) coordinates
        """
        grid_x = int(x_m / self.grid_size_m)
        grid_y = int(y_m / self.grid_size_m)
        
        # Ensure coordinates are within grid bounds
        grid_x = max(0, min(grid_x, self.grid_width - 1))
        grid_y = max(0, min(grid_y, self.grid_length - 1))
        
        return grid_x, grid_y
    
    def get_real_coordinates(self, grid_x, grid_y):
        """
        Convert grid coordinates to real-world coordinates (bottom-left corner).
        
        Args:
            grid_x (int): X coordinate in grid
            grid_y (int): Y coordinate in grid
            
        Returns:
            tuple: (x_m, y_m) coordinates in meters
        """
        x_m = grid_x * self.grid_size_m
        y_m = grid_y * self.grid_size_m
        
        return x_m, y_m
    
    def snap_to_grid(self, value_m):
        """
        Snap a real-world measurement to the grid.
        
        Args:
            value_m (float): Value in meters
            
        Returns:
            float: Value snapped to grid
        """
        return round(value_m / self.grid_size_m) * self.grid_size_m
    
    def is_within_grid(self, grid_x, grid_y, width_cells, height_cells):
        """
        Check if the specified grid cells are within the grid boundaries.
        
        Args:
            grid_x (int): Starting X coordinate in grid
            grid_y (int): Starting Y coordinate in grid
            width_cells (int): Width in grid cells
            height_cells (int): Height in grid cells
            
        Returns:
            bool: True if within grid, False otherwise
        """
        if (grid_x < 0 or grid_y < 0 or 
            grid_x + width_cells > self.grid_width or 
            grid_y + height_cells > self.grid_length):
            return False
        return True
    
    def is_area_empty(self, grid_x, grid_y, width_cells, height_cells):
        """
        Check if the specified grid area is empty.
        
        Args:
            grid_x (int): Starting X coordinate in grid
            grid_y (int): Starting Y coordinate in grid
            width_cells (int): Width in grid cells
            height_cells (int): Height in grid cells
            
        Returns:
            bool: True if area is empty, False otherwise
        """
        if not self.is_within_grid(grid_x, grid_y, width_cells, height_cells):
            return False
        
        for y in range(grid_y, grid_y + height_cells):
            for x in range(grid_x, grid_x + width_cells):
                if self.grid[y, x] != self.EMPTY:
                    return False
        return True
    
    def place_element(self, grid_x, grid_y, width_cells, height_cells, element_type):
        """
        Place an element on the grid if possible.
        
        Args:
            grid_x (int): Starting X coordinate in grid
            grid_y (int): Starting Y coordinate in grid
            width_cells (int): Width in grid cells
            height_cells (int): Height in grid cells
            element_type (int): Type of element to place
            
        Returns:
            dict: Element data if placed successfully, None otherwise
        """
        if not self.is_area_empty(grid_x, grid_y, width_cells, height_cells):
            return None
        
        # Mark the grid cells as occupied
        for y in range(grid_y, grid_y + height_cells):
            for x in range(grid_x, grid_x + width_cells):
                self.grid[y, x] = element_type
        
        # Get real-world coordinates
        x_m, y_m = self.get_real_coordinates(grid_x, grid_y)
        width_m = width_cells * self.grid_size_m
        height_m = height_cells * self.grid_size_m
        
        # Create element data
        element = {
            'grid_x': grid_x,
            'grid_y': grid_y,
            'width_cells': width_cells,
            'height_cells': height_cells,
            'x': x_m,
            'y': y_m,
            'width': width_m,
            'height': height_m,
            'type': element_type
        }
        
        return element
    
    def get_element_coordinates(self):
        """
        Get coordinates of all elements on the grid.
        
        Returns:
            dict: Dictionary with pillars, racks, and walls
        """
        return {
            'pillars': self.pillars,
            'racks': self.racks,
            'walls': self.walls,
            'support_rooms': self.support_rooms if hasattr(self, 'support_rooms') else []
        }
    
    def print_grid(self):
        """
        Print the current state of the grid.
        """
        symbols = {
            self.EMPTY: '.',
            self.PILLAR: 'P',
            self.RACK: 'R',
            self.WALL: 'W'
        }
        
        print("\nData Center Grid Layout:")
        for y in range(self.grid_length - 1, -1, -1):  # Print from top to bottom
            row = ""
            for x in range(self.grid_width):
                row += symbols[self.grid[y, x]] + " "
            print(row)