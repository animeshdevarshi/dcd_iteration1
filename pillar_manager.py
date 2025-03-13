# Updated pillar_manager.py
# Class for managing pillars in the data center with enhanced spacing control

# Define conversion constants
MM_TO_M = 0.001
FT_TO_M = 0.3048

class PillarManager:
    """
    Class to manage pillar placement in the data center.
    """
    def __init__(self, datacenter_grid):
        """
        Initialize the pillar manager with a reference to the data center grid.
        
        Args:
            datacenter_grid: Instance of DataCenterGrid
        """
        self.grid = datacenter_grid
    
    def place_pillar(self, grid_x, grid_y, grid_width, grid_height):
        """
        Place a single pillar at the specified grid location.
        
        Args:
            grid_x: X-index in the grid
            grid_y: Y-index in the grid
            grid_width: Width in grid cells
            grid_height: Height in grid cells
            
        Returns:
            Dictionary with pillar details or None if placement failed
        """
        pillar = self.grid.place_element(grid_x, grid_y, grid_width, grid_height, self.grid.PILLAR)
        if pillar:
            self.grid.pillars.append(pillar)
        return pillar
    
    def place_pillar_at_meters(self, x_m, y_m, width_m, height_m):
        """
        Place a pillar at real-world coordinates, aligned to the grid.
        
        Args:
            x_m: X-coordinate in meters
            y_m: Y-coordinate in meters
            width_m: Width in meters
            height_m: Height in meters
            
        Returns:
            Dictionary with pillar details or None if placement failed
        """
        # Snap coordinates to grid
        x_m = self.grid.snap_to_grid(x_m)
        y_m = self.grid.snap_to_grid(y_m)
        
        # Convert to grid coordinates
        grid_x, grid_y = self.grid.get_grid_coordinates(x_m, y_m)
        grid_width = int(round(width_m / self.grid.grid_size_m))
        grid_height = int(round(height_m / self.grid.grid_size_m))
        
        return self.place_pillar(grid_x, grid_y, grid_width, grid_height)
    
    def mm_to_meters(self, mm):
        """Convert millimeters to meters"""
        return mm * MM_TO_M
        
    def ft_to_meters(self, ft):
        """Convert feet to meters"""
        return ft * FT_TO_M
    
    def place_pillars_with_exact_spacing(self, pillar_width_mm, pillar_height_mm, x_spacing_ft, y_spacing_ft):
        """
        Place pillars with the exact spacing provided by the user.
        Ensures pillars are at corners and edges, maintaining the specified spacing throughout.
        
        Args:
            pillar_width_mm: Width of each pillar in millimeters
            pillar_height_mm: Height of each pillar in millimeters
            x_spacing_ft: Exact spacing between pillar centers in x-direction (feet)
            y_spacing_ft: Exact spacing between pillar centers in y-direction (feet)
            
        Returns:
            List of all placed pillars
        """
        # Clear existing pillars
        self.grid.pillars = []
        
        # Convert dimensions to meters
        pillar_width_m = self.mm_to_meters(pillar_width_mm)
        pillar_height_m = self.mm_to_meters(pillar_height_mm)
        x_spacing_m = self.ft_to_meters(x_spacing_ft)
        y_spacing_m = self.ft_to_meters(y_spacing_ft)
        
        # Convert to grid cells
        pillar_grid_width = int(round(pillar_width_m / self.grid.grid_size_m))
        pillar_grid_height = int(round(pillar_height_m / self.grid.grid_size_m))
        x_spacing_cells = int(round(x_spacing_m / self.grid.grid_size_m))
        y_spacing_cells = int(round(y_spacing_m / self.grid.grid_size_m))
        
        print(f"Pillar dimensions: {pillar_width_mm}mm × {pillar_height_mm}mm")
        print(f"Spacing: {x_spacing_ft}ft × {y_spacing_ft}ft")
        print(f"In grid cells - Pillar: {pillar_grid_width}×{pillar_grid_height}, Spacing: {x_spacing_cells}×{y_spacing_cells}")
        
        # Calculate how many pillars will fit in each dimension
        room_width_cells = self.grid.grid_width
        room_length_cells = self.grid.grid_length
        
        # Calculate how many pillars will fit in each dimension
        # Start with at least 2 pillars for the edges
        x_pillars = max(2, (room_width_cells // x_spacing_cells) + 1)
        y_pillars = max(2, (room_length_cells // y_spacing_cells) + 1)
        
        print(f"Room can fit {x_pillars} pillars in x-direction")
        print(f"Room can fit {y_pillars} pillars in y-direction")
        
        # Calculate positions for all pillars
        pillar_positions = []
        
        # Place pillars in a grid pattern
        for y_idx in range(y_pillars):
            for x_idx in range(x_pillars):
                # Calculate position (special case for first and last in each dimension)
                if x_idx == 0:
                    # Left edge
                    grid_x = 0
                elif x_idx == x_pillars - 1:
                    # Right edge
                    grid_x = room_width_cells - pillar_grid_width
                else:
                    # Interior - evenly spaced
                    grid_x = x_idx * x_spacing_cells
                
                if y_idx == 0:
                    # Bottom edge
                    grid_y = 0
                elif y_idx == y_pillars - 1:
                    # Top edge
                    grid_y = room_length_cells - pillar_grid_height
                else:
                    # Interior - evenly spaced
                    grid_y = y_idx * y_spacing_cells
                
                pillar_positions.append((grid_x, grid_y))
        
        # Place the pillars
        placed_pillars = []
        for grid_x, grid_y in pillar_positions:
            pillar = self.place_pillar(grid_x, grid_y, pillar_grid_width, pillar_grid_height)
            if pillar:
                placed_pillars.append(pillar)
        
        print(f"Placed {len(placed_pillars)} pillars in total")
        return placed_pillars
    
    def place_pillars_by_count(self, pillar_width_mm, pillar_height_mm, num_pillars_x, num_pillars_y):
        """
        Place a specific number of pillars evenly distributed in the room.
        
        Args:
            pillar_width_mm: Width of each pillar in millimeters
            pillar_height_mm: Height of each pillar in millimeters
            num_pillars_x: Number of pillars to place horizontally
            num_pillars_y: Number of pillars to place vertically
            
        Returns:
            List of all placed pillars
        """
        # Clear existing pillars
        self.grid.pillars = []
        
        # Convert dimensions to meters
        pillar_width_m = self.mm_to_meters(pillar_width_mm)
        pillar_height_m = self.mm_to_meters(pillar_height_mm)
        
        # Convert to grid cells
        pillar_grid_width = int(round(pillar_width_m / self.grid.grid_size_m))
        pillar_grid_height = int(round(pillar_height_m / self.grid.grid_size_m))
        
        print(f"Pillar dimensions: {pillar_width_mm}mm × {pillar_height_mm}mm")
        print(f"Number of pillars: {num_pillars_x} × {num_pillars_y}")
        
        # Calculate spacing based on number of pillars
        room_width_cells = self.grid.grid_width
        room_length_cells = self.grid.grid_length
        
        # Calculate spacing (in cells)
        x_spacing_cells = room_width_cells // (num_pillars_x - 1) if num_pillars_x > 1 else room_width_cells
        y_spacing_cells = room_length_cells // (num_pillars_y - 1) if num_pillars_y > 1 else room_length_cells
        
        # Convert to real-world spacing
        x_spacing_m = x_spacing_cells * self.grid.grid_size_m
        y_spacing_m = y_spacing_cells * self.grid.grid_size_m
        
        # Convert to feet for display
        x_spacing_ft = x_spacing_m / FT_TO_M
        y_spacing_ft = y_spacing_m / FT_TO_M
        
        print(f"Calculated spacing: {x_spacing_ft:.2f}ft × {y_spacing_ft:.2f}ft")
        print(f"In grid cells - Spacing: {x_spacing_cells}×{y_spacing_cells}")
        
        # Calculate positions for all pillars
        pillar_positions = []
        
        # Place pillars in a grid pattern
        for y_idx in range(num_pillars_y):
            for x_idx in range(num_pillars_x):
                # Calculate position, ensuring first and last pillars are at edges
                if num_pillars_x > 1:
                    grid_x = x_idx * x_spacing_cells if x_idx < num_pillars_x - 1 else room_width_cells - pillar_grid_width
                else:
                    grid_x = (room_width_cells - pillar_grid_width) // 2  # Center if only one pillar
                
                if num_pillars_y > 1:
                    grid_y = y_idx * y_spacing_cells if y_idx < num_pillars_y - 1 else room_length_cells - pillar_grid_height
                else:
                    grid_y = (room_length_cells - pillar_grid_height) // 2  # Center if only one pillar
                
                # Ensure edge pillars are actually at edges
                if x_idx == 0:
                    grid_x = 0
                if y_idx == 0:
                    grid_y = 0
                
                pillar_positions.append((grid_x, grid_y))
        
        # Place the pillars
        placed_pillars = []
        for grid_x, grid_y in pillar_positions:
            pillar = self.place_pillar(grid_x, grid_y, pillar_grid_width, pillar_grid_height)
            if pillar:
                placed_pillars.append(pillar)
        
        print(f"Placed {len(placed_pillars)} pillars in total")
        return placed_pillars
    
    def get_pillar_coordinates(self):
        """
        Get the coordinates of all pillars.
        
        Returns:
            List of dictionaries with pillar details
        """
        return self.grid.pillars