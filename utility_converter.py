# utility_converter.py
# Utility functions for unit conversion

"""
Unit converter utility functions for the Data Center Designer.
This module provides conversion functions that can be used by other modules.
"""

# Conversion constants
MM_TO_M = 0.001  # Millimeters to meters
FT_TO_M = 0.3048  # Feet to meters

def mm_to_meters(mm):
    """Convert millimeters to meters"""
    return mm * MM_TO_M

def ft_to_meters(ft):
    """Convert feet to meters"""
    return ft * FT_TO_M