# rack_manager.py
# Class for managing rack placement in the data center

class RackManager:
    """
    Class to manage rack placement in the data center.
    """
    def __init__(self, datacenter_grid):
        """
        Initialize the rack manager with a reference to the data center grid.
        
        Args:
            datacenter_grid: Instance of DataCenterGrid
        """
        self.grid = datacenter_grid
        
        # Standard rack dimensions (in grid cells)
        self.RACK_WIDTH_CELLS = 2  # 1200mm / 600mm = 2 cells
        self.RACK_HEIGHT_CELLS = 1  # 600mm / 600mm = 1 cell
    

    def calculate_rack_positions(self, num_racks, top_margin=1, bottom_margin=1, 
                                left_margin=1, right_margin=1, row_spacing=1):
        """
        Calculate the positions for racks in a standard row layout.
        
        Args:
            num_racks: Number of racks to place
            top_margin: Margin from the top edge (in grid cells)
            bottom_margin: Margin from the bottom edge (in grid cells)
            left_margin: Margin from the left edge (in grid cells)
            right_margin: Margin from the right edge (in grid cells)
            row_spacing: Spacing between rows of racks (in grid cells)
        
        Returns:
            List of rack positions in grid coordinates (grid_x, grid_y)
        """
        # Calculate available space
        available_width = self.grid.grid_width - left_margin - right_margin
        available_height = self.grid.grid_length - top_margin - bottom_margin
        
        # Calculate how many racks can fit in a row
        # Each rack is RACK_WIDTH_CELLS wide
        max_racks_per_row = available_width // self.RACK_WIDTH_CELLS
        
        if max_racks_per_row == 0:
            print("Error: Room too narrow to fit racks with specified margins")
            return []
        
        # Calculate how many rows we need
        rows_needed = (num_racks + max_racks_per_row - 1) // max_racks_per_row
        
        # Check if we have enough vertical space for the rows
        total_height_needed = rows_needed * (self.RACK_HEIGHT_CELLS + row_spacing) - row_spacing
        
        if total_height_needed > available_height:
            print(f"Warning: Not enough vertical space for {num_racks} racks. Will place as many as possible.")
            # Recalculate how many rows we can fit
            max_rows = available_height // (self.RACK_HEIGHT_CELLS + row_spacing)
            max_racks = max_rows * max_racks_per_row
            print(f"Can only fit {max_racks} racks.")
            num_racks = max_racks
            rows_needed = max_rows
        
        # Calculate positions for all racks
        rack_positions = []
        
        # Arrange racks in rows (from bottom to top)
        for row in range(rows_needed):
            # Calculate the y-coordinate for this row
            # Start from the bottom of the room and move up
            grid_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + row_spacing)
            
            # Calculate how many racks go in this row
            racks_in_this_row = min(max_racks_per_row, num_racks - row * max_racks_per_row)
            
            if racks_in_this_row <= 0:
                break
            
            # Distribute racks evenly in this row
            for rack_idx in range(racks_in_this_row):
                grid_x = left_margin + rack_idx * self.RACK_WIDTH_CELLS
                rack_positions.append((grid_x, grid_y))
        
        return rack_positions
    
    # def calculate_rack_positions_with_aisle(self, num_racks, top_margin=1, bottom_margin=1,
    #                                      left_margin=1, right_margin=1, row_spacing=1, aisle_width=2):
    #     """
    #     Calculate rack positions with a central aisle design (hot/cold aisle configuration).
        
    #     Args:
    #         num_racks: Number of racks to place
    #         top_margin: Margin from the top edge (in grid cells)
    #         bottom_margin: Margin from the bottom edge (in grid cells)
    #         left_margin: Margin from the left edge (in grid cells)
    #         right_margin: Margin from the right edge (in grid cells)
    #         row_spacing: Spacing between rows of racks (in grid cells)
    #         aisle_width: Width of the central aisle (in grid cells)
        
    #     Returns:
    #         List of rack positions in grid coordinates (grid_x, grid_y)
    #     """
    #     # Calculate available space
    #     available_width = self.grid.grid_width - left_margin - right_margin
    #     available_height = self.grid.grid_length - top_margin - bottom_margin
        
    #     # Calculate how many racks can fit in a row on one side of the aisle
    #     max_racks_per_half_row = (available_width - aisle_width) // (2 * self.RACK_WIDTH_CELLS)
        
    #     if max_racks_per_half_row == 0:
    #         print("Error: Room too narrow to fit racks with central aisle")
    #         return []
        
    #     max_racks_per_row = max_racks_per_half_row * 2
        
    #     # Calculate how many rows we need
    #     rows_needed = (num_racks + max_racks_per_row - 1) // max_racks_per_row
        
    #     # Check if we have enough vertical space for the rows
    #     total_height_needed = rows_needed * (self.RACK_HEIGHT_CELLS + row_spacing) - row_spacing
        
    #     if total_height_needed > available_height:
    #         print(f"Warning: Not enough vertical space for {num_racks} racks. Will place as many as possible.")
    #         # Recalculate how many rows we can fit
    #         max_rows = available_height // (self.RACK_HEIGHT_CELLS + row_spacing)
    #         max_racks = max_rows * max_racks_per_row
    #         print(f"Can only fit {max_racks} racks.")
    #         num_racks = max_racks
    #         rows_needed = max_rows
        
    #     # Calculate positions for all racks
    #     rack_positions = []
        
    #     # Calculate the center of the aisle
    #     center_x = left_margin + available_width // 2
        
    #     # Arrange racks in rows
    #     for row in range(rows_needed):
    #         # Calculate the y-coordinate for this row
    #         grid_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + row_spacing)
            
    #         # Calculate how many racks go in this row
    #         racks_in_this_row = min(max_racks_per_row, num_racks - row * max_racks_per_row)
            
    #         if racks_in_this_row <= 0:
    #             break
            
    #         # Distribute racks to the left and right of the aisle
    #         racks_left = min(max_racks_per_half_row, racks_in_this_row)
    #         racks_right = min(max_racks_per_half_row, racks_in_this_row - racks_left)
            
    #         # Place racks on the left side
    #         for rack_idx in range(racks_left):
    #             grid_x = center_x - aisle_width//2 - (rack_idx + 1) * self.RACK_WIDTH_CELLS
    #             rack_positions.append((grid_x, grid_y))
            
    #         # Place racks on the right side
    #         for rack_idx in range(racks_right):
    #             grid_x = center_x + aisle_width//2 + rack_idx * self.RACK_WIDTH_CELLS
    #             rack_positions.append((grid_x, grid_y))
        
    #     return rack_positions
    # Update to rack_manager.py to include aisle_width parameter

    def calculate_rack_positions_with_aisle(self, num_racks, top_margin=1, bottom_margin=1,
                                        left_margin=1, right_margin=1, row_spacing=1, aisle_width=2):
        """
        Calculate rack positions with a central aisle design (hot/cold aisle configuration).
        
        Args:
            num_racks: Number of racks to place
            top_margin: Margin from the top edge (in grid cells)
            bottom_margin: Margin from the bottom edge (in grid cells)
            left_margin: Margin from the left edge (in grid cells)
            right_margin: Margin from the right edge (in grid cells)
            row_spacing: Spacing between rows of racks (in grid cells)
            aisle_width: Width of the central aisle (in grid cells)
        
        Returns:
            List of rack positions in grid coordinates (grid_x, grid_y)
        """
        # Calculate available space
        available_width = self.grid.grid_width - left_margin - right_margin
        available_height = self.grid.grid_length - top_margin - bottom_margin
        
        # Calculate how many racks can fit in a row on one side of the aisle
        max_racks_per_half_row = (available_width - aisle_width) // (2 * self.RACK_WIDTH_CELLS)
        
        if max_racks_per_half_row == 0:
            print("Error: Room too narrow to fit racks with central aisle")
            return []
        
        max_racks_per_row = max_racks_per_half_row * 2
        
        # Calculate how many rows we need
        rows_needed = (num_racks + max_racks_per_row - 1) // max_racks_per_row
        
        # Check if we have enough vertical space for the rows
        total_height_needed = rows_needed * (self.RACK_HEIGHT_CELLS + row_spacing) - row_spacing
        
        if total_height_needed > available_height:
            print(f"Warning: Not enough vertical space for {num_racks} racks. Will place as many as possible.")
            # Recalculate how many rows we can fit
            max_rows = available_height // (self.RACK_HEIGHT_CELLS + row_spacing)
            max_racks = max_rows * max_racks_per_row
            print(f"Can only fit {max_racks} racks.")
            num_racks = max_racks
            rows_needed = max_rows
        
        # Calculate positions for all racks
        rack_positions = []
        
        # Calculate the center of the aisle
        center_x = left_margin + available_width // 2
        
        # Arrange racks in rows
        for row in range(rows_needed):
            # Calculate the y-coordinate for this row
            grid_y = bottom_margin + row * (self.RACK_HEIGHT_CELLS + row_spacing)
            
            # Calculate how many racks go in this row
            racks_in_this_row = min(max_racks_per_row, num_racks - row * max_racks_per_row)
            
            if racks_in_this_row <= 0:
                break
            
            # Distribute racks to the left and right of the aisle
            racks_left = min(max_racks_per_half_row, racks_in_this_row)
            racks_right = min(max_racks_per_half_row, racks_in_this_row - racks_left)
            
            # Place racks on the left side
            for rack_idx in range(racks_left):
                grid_x = center_x - aisle_width//2 - (rack_idx + 1) * self.RACK_WIDTH_CELLS
                rack_positions.append((grid_x, grid_y))
            
            # Place racks on the right side
            for rack_idx in range(racks_right):
                grid_x = center_x + aisle_width//2 + rack_idx * self.RACK_WIDTH_CELLS
                rack_positions.append((grid_x, grid_y))
        
        return rack_positions

    def place_racks(self, rack_positions):
        """
        Place racks on the grid at the specified positions.
        
        Args:
            rack_positions: List of (grid_x, grid_y) tuples for rack positions
            
        Returns:
            List of placed rack details
        """
        placed_racks = []
        
        for i, (grid_x, grid_y) in enumerate(rack_positions):
            # Try to place the rack
            rack = self.grid.place_element(
                grid_x, grid_y, 
                self.RACK_WIDTH_CELLS, self.RACK_HEIGHT_CELLS,
                self.grid.RACK
            )
            
            if rack:
                # Add rack ID for reference
                rack['id'] = f'R{i+1}'
                self.grid.racks.append(rack)
                placed_racks.append(rack)
            else:
                print(f"Warning: Could not place rack at position ({grid_x}, {grid_y})")
        
        print(f"Successfully placed {len(placed_racks)} racks")
        return placed_racks
    
    def get_rack_coordinates(self):
        """
        Get the coordinates of all racks.
        
        Returns:
            List of dictionaries with rack details
        """
        return self.grid.racks