# """
# streamlit_app.py - Streamlit application for the Data Center Layout Designer with compact UI
# """

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os
import tempfile
from io import BytesIO
import base64
import importlib

# Import your existing modules
from datacenter_grid import DataCenterGrid
from pillar_manager import PillarManager
from rack_manager import RackManager
from rack_layout_optimizer import RackLayoutOptimizer
from advanced_layout_strategies import AdvancedRackLayoutStrategies
from enhanced_visualization import visualize_datacenter_enhanced
from simple_3d_visualization import create_simple_3d_visualization

# Set page config
st.set_page_config(
    page_title="Data Center Layout Designer",
    page_icon="🏢",
    layout="wide"
)

# Custom CSS to make the UI more compact
st.markdown("""
<style>
    /* Make inputs and text areas more compact */
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Reduce space around headers */
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.2rem !important;
        margin-bottom: 0.5rem !important;
        font-weight: 600 !important;
    }
    
    /* Make radio buttons more compact */
    div[data-testid="stRadio"] > div {
        gap: 0.5rem !important;
    }
    
    /* Make checkboxes more compact */
    div[data-testid="stCheckbox"] > div {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    /* Make number inputs more compact */
    div[data-testid="stNumberInput"] > div {
        padding: 0px !important;
    }
    
    /* Reduce space between label and input */
    div.stNumberInput label {
        padding-bottom: 1px !important;
    }
    
    /* More compact slider */
    div[data-testid="stSlider"] > div {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Reduce space around tab content */
    div[data-testid="stTabContent"] {
        padding-top: 0.5rem !important;
    }
    
    /* Make expander more compact */
    div.streamlit-expanderHeader {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
    }
    
    /* Reduce padding in columns */
    div[data-testid="column"] {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Custom wrapper function for hot/cold aisle layout
def custom_calculate_rack_positions_with_aisle(rack_manager, num_racks, params):
    """
    Custom wrapper to handle hot/cold aisle layout with appropriate parameters.
    Inspects the available parameters in the method and only passes those that are supported.
    """
    import inspect
    
    # Get the signature of the method to determine which parameters it accepts
    signature = inspect.signature(rack_manager.calculate_rack_positions_with_aisle)
    valid_params = signature.parameters.keys()
    
    # Filter out params that aren't in the method signature
    supported_params = {}
    for param in valid_params:
        if param == 'self' or param == 'num_racks':
            continue
        if param in params:
            supported_params[param] = params[param]
    
    # Call the original method with only supported parameters
    return rack_manager.calculate_rack_positions_with_aisle(num_racks, **supported_params)

# Try to import Shapely-based visualization, fall back to simple if not available
try:
    from enhanced_shapely_visualization import visualize_datacenter_with_shapely, calculate_optimal_rack_clearance
    SHAPELY_AVAILABLE = True
except ImportError:
    from simple_visualization import visualize_datacenter_simple, visualize_rack_clearance_simple, calculate_simple_metrics
    SHAPELY_AVAILABLE = False
    st.warning("Shapely package not found. Using simplified visualization without advanced geometric analysis.")

# Function to generate visualization based on selected view type
def generate_grid_visualization(datacenter, view_type, layout_type):
    """
    Generate a visualization and return it as a base64 encoded image.
    This avoids issues with temporary file handling.
    """
    try:
        if view_type == "Standard":
            fig, ax = visualize_datacenter_enhanced(
                datacenter, 
                title=f"Data Center Layout - {layout_type}",
                show_metrics=True,
                highlight_zones=False,
                cooling_analysis=False
            )
        elif view_type == "Highlight Rows":
            # Similar to standard but with more pronounced row coloring
            fig, ax = visualize_datacenter_enhanced(
                datacenter, 
                title=f"Data Center Layout (Rows) - {layout_type}",
                show_metrics=True,
                highlight_zones=False,
                cooling_analysis=False
            )
        elif view_type == "Highlight Zones":
            fig, ax = visualize_datacenter_enhanced(
                datacenter, 
                title=f"Data Center Layout (Zones) - {layout_type}",
                show_metrics=True,
                highlight_zones=True,
                cooling_analysis=False
            )
        elif view_type == "Walkway Flow":
            # Try to use Shapely for better walkway visualization
            if SHAPELY_AVAILABLE:
                fig, ax, geometries = visualize_datacenter_with_shapely(
                    datacenter,
                    title=f"Walkway Flow - {layout_type}",
                    highlight_zones=False,
                    cooling_analysis=False
                )
            else:
                # Fallback to enhanced visualization
                fig, ax = visualize_datacenter_enhanced(
                    datacenter, 
                    title=f"Walkway Flow - {layout_type}",
                    show_metrics=True,
                    highlight_zones=False,
                    cooling_analysis=False
                )
    except Exception as e:
        st.warning(f"Enhanced visualization failed: {str(e)}. Using simplified visualization.")
        if SHAPELY_AVAILABLE:
            try:
                fig, ax, _ = visualize_datacenter_with_shapely(
                    datacenter,
                    title=f"Data Center Layout - {layout_type}",
                    cooling_analysis=False
                )
            except Exception as e2:
                st.warning(f"Shapely visualization failed: {str(e2)}. Using basic visualization.")
                fig, ax = visualize_datacenter_simple(
                    datacenter,
                    title=f"Data Center Layout - {layout_type}",
                    cooling_analysis=False
                )
        else:
            fig, ax = visualize_datacenter_simple(
                datacenter,
                title=f"Data Center Layout - {layout_type}",
                cooling_analysis=False
            )
    
    # Use BytesIO to save figure in memory instead of a temporary file
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    # Convert to base64 encoded string to avoid file system issues
    img_str = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{img_str}"

# Initialize session state variables if they don't exist
if 'datacenter' not in st.session_state:
    st.session_state.datacenter = None
if 'current_layout' not in st.session_state:
    st.session_state.current_layout = None
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'grid_view_type' not in st.session_state:
    st.session_state.grid_view_type = "Standard"
if 'grid_viz_image' not in st.session_state:
    st.session_state.grid_viz_image = None



# Title with less spacing
st.markdown("<h1 style='margin-bottom:0.5rem'>Data Center Layout Designer</h1>", unsafe_allow_html=True)

# Create 3 columns layout for inputs for more compact appearance
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("<h4>Room Dimensions</h4>", unsafe_allow_html=True)
    room_width = st.number_input("Room Width (m)", min_value=5.0, max_value=100.0, value=45.0, step=0.5, format="%.2f")
    room_length = st.number_input("Room Length (m)", min_value=5.0, max_value=100.0, value=23.0, step=0.5, format="%.2f")
    grid_size = st.number_input("Grid Size (mm)", min_value=300, max_value=1200, value=600, step=100) / 1000.0  # Convert to meters

    st.markdown("<h4>Pillar Information</h4>", unsafe_allow_html=True)
    pillar_width = st.number_input("Pillar Width (mm)", min_value=100, max_value=1000, value=500, step=50)
    pillar_height = st.number_input("Pillar Height (mm)", min_value=100, max_value=1000, value=500, step=50)

with col2:
    st.markdown("<h4>Pillar Layout</h4>", unsafe_allow_html=True)
    pillar_spacing_method = st.radio(
        "Pillar Placement Method",
        ["Distance Between Pillars", "Number of Pillars"],
        horizontal=True
    )
    
    if pillar_spacing_method == "Distance Between Pillars":
        pillar_x_spacing = st.number_input("Horizontal Distance (ft)", min_value=5.0, max_value=50.0, value=17.0, step=0.5, format="%.2f")
        pillar_y_spacing = st.number_input("Vertical Distance (ft)", min_value=5.0, max_value=50.0, value=17.0, step=0.5, format="%.2f")
    else:
        num_pillars_x = st.number_input("Pillars (Horizontal)", min_value=2, max_value=20, value=8)
        num_pillars_y = st.number_input("Pillars (Vertical)", min_value=2, max_value=20, value=4)
        
        # Calculate and display spacing
        pillar_x_spacing = room_width / (num_pillars_x - 1) / 0.3048  # Convert to feet
        pillar_y_spacing = room_length / (num_pillars_y - 1) / 0.3048  # Convert to feet
        
        st.caption(f"Calculated spacing: {pillar_x_spacing:.1f}ft × {pillar_y_spacing:.1f}ft")

with col3:
    st.markdown("<h4>Rack Configuration</h4>", unsafe_allow_html=True)
    num_racks = st.number_input("Number of Racks", min_value=1, max_value=500, value=80, step=1)
    
    st.markdown("<h4>Layout Strategy</h4>", unsafe_allow_html=True)
    layout_type = st.selectbox(
        "Layout Type",
        [
            "Standard Row-Based",
            "Hot/Cold Aisle",
            "Spine-Leaf Network",
            "Cluster-Based",
            "Cooling Optimized",
            "High Density Zones",
            "Circular/Radial",
            "Automatic (Best Space Utilization)"
        ]
    )
    
    st.markdown("<h4>Visualization Options</h4>", unsafe_allow_html=True)
    show_cooling_analysis = st.checkbox("Show Cooling Analysis", value=True)
    show_clearance_analysis = st.checkbox("Show Rack Clearance Analysis", value=False)

# Advanced options in a compact expander
with st.expander("Advanced Options"):
    adv_col1, adv_col2, adv_col3, adv_col4 = st.columns(4)
    
    with adv_col1:
        top_margin = st.slider("Top Margin", 1, 10, 3, 1)
        left_margin = st.slider("Left Margin", 1, 10, 3, 1)
    
    with adv_col2:
        bottom_margin = st.slider("Bottom Margin", 1, 10, 3, 1)
        right_margin = st.slider("Right Margin", 1, 10, 3, 1)
    
    with adv_col3:
        row_spacing = st.slider("Row Spacing", 1, 5, 2, 1)
        aisle_width = st.slider("Aisle Width", 2, 8, 4, 1)
    
    with adv_col4:
        if layout_type == "Cluster-Based":
            cluster_size = st.slider("Cluster Size", 4, 16, 8, 1)
            cluster_spacing = st.slider("Cluster Spacing", 2, 8, 4, 1)
        elif layout_type == "High Density Zones":
            high_density_pct = st.slider("High Density %", 10, 50, 30, 5)
            high_density_spacing = st.slider("HD Spacing", 1, 5, 2, 1)
        elif layout_type == "Circular/Radial":
            min_radius = st.slider("Min Radius", 3, 15, 5, 1)

# Generate button
if st.button("Generate Data Center Layout", type="primary", use_container_width=True):
    # Display a spinner while processing
    with st.spinner("Generating layout..."):
        # Create the data center grid
        datacenter = DataCenterGrid(room_width, room_length, grid_size)
        
        # Place pillars
        pillar_mgr = PillarManager(datacenter)
        
        # Place pillars based on selected method
        if pillar_spacing_method == "Distance Between Pillars":
            # Use exact distances between pillars
            pillar_mgr.place_pillars_with_exact_spacing(pillar_width, pillar_height, pillar_x_spacing, pillar_y_spacing)
        else:
            # Use specified number of pillars
            pillar_mgr.place_pillars_by_count(pillar_width, pillar_height, num_pillars_x, num_pillars_y)
        
        # Set up rack manager
        rack_mgr = RackManager(datacenter)
        
        # Create layout parameters
        params = {
            "top_margin": top_margin,
            "bottom_margin": bottom_margin,
            "left_margin": left_margin,
            "right_margin": right_margin,
            "row_spacing": row_spacing,
            "aisle_width": aisle_width
        }
        
        # Add layout-specific parameters
        if layout_type == "Cluster-Based":
            params["cluster_size"] = cluster_size
            params["cluster_spacing"] = cluster_spacing
        
        if layout_type == "High Density Zones":
            params["high_density_pct"] = high_density_pct
            params["high_density_spacing"] = high_density_spacing
        
        if layout_type == "Circular/Radial":
            params["min_radius"] = min_radius
        
        # Generate rack positions based on selected layout
        advanced_strategies = AdvancedRackLayoutStrategies(datacenter)
        
        if layout_type == "Standard Row-Based":
            rack_positions = rack_mgr.calculate_rack_positions(
                num_racks,
                top_margin=params["top_margin"],
                bottom_margin=params["bottom_margin"],
                left_margin=params["left_margin"],
                right_margin=params["right_margin"],
                row_spacing=params["row_spacing"]
            )
        elif layout_type == "Hot/Cold Aisle":
            # Use custom wrapper to handle parameter compatibility
            rack_positions = custom_calculate_rack_positions_with_aisle(rack_mgr, num_racks, params)
        elif layout_type == "Spine-Leaf Network":
            rack_positions = advanced_strategies.generate_spine_leaf_layout(num_racks, params)
        elif layout_type == "Cluster-Based":
            rack_positions = advanced_strategies.generate_cluster_layout(num_racks, params)
        elif layout_type == "Cooling Optimized":
            rack_positions = advanced_strategies.generate_cooling_optimized_layout(num_racks, params)
        elif layout_type == "High Density Zones":
            rack_positions = advanced_strategies.generate_high_density_zones_layout(num_racks, params)
        elif layout_type == "Circular/Radial":
            rack_positions = advanced_strategies.generate_circular_layout(num_racks, params)
        elif layout_type == "Automatic (Best Space Utilization)":
            # Use the optimizer to find the best layout
            optimizer = RackLayoutOptimizer(datacenter)
            results = optimizer.compare_layouts(num_racks, plot=False)
            best_layout, _ = optimizer.get_best_layout(num_racks)
            
            # Already placed by the optimizer, no need to place again
            st.success(f"Best layout selected: {best_layout}")
            layout_type = best_layout
            
            # Continue with visualization
            rack_positions = []  # This will be empty as racks are already placed by optimizer
        
        # Place racks if positions were generated
        if rack_positions:
            placed_racks = rack_mgr.place_racks(rack_positions)
            st.success(f"Successfully placed {len(placed_racks)} racks out of {num_racks} requested")
        
        # Store data in session state
        st.session_state.datacenter = datacenter
        st.session_state.current_layout = layout_type
        st.session_state.grid_view_type = "Standard"  # Default to standard view
        st.session_state.generated = True
        st.session_state.show_cooling_analysis = show_cooling_analysis
        st.session_state.show_clearance_analysis = show_clearance_analysis
        
        # Generate initial grid visualization
        st.session_state.grid_viz_image = generate_grid_visualization(
            datacenter, 
            "Standard",  # Default view
            layout_type
        )
        
        # Force rerun to show the tabs
        st.rerun()

# Only show visualization if we've generated a layout
if st.session_state.generated and st.session_state.datacenter is not None:
    datacenter = st.session_state.datacenter
    layout_type = st.session_state.current_layout
    
    # Get room dimensions from the datacenter
    room_width = datacenter.width_m
    room_length = datacenter.length_m
    grid_size = datacenter.grid_size_m
    num_racks = len(datacenter.racks)
    
    # Create tabs for different visualization options
    viz_tabs = st.tabs(["Grid Layout", "Cooling Analysis", "Clearance Analysis", "3D View", "Metrics"])
    
    # Grid Layout tab
    with viz_tabs[0]:
        # Use a container to group the radio buttons and visualization
        with st.container():
            # Radio buttons for grid view type with horizontal layout
            selected_view = st.radio(
                "Grid View Type:", 
                ["Standard", "Highlight Rows", "Highlight Zones", "Walkway Flow"],
                horizontal=True,
                key="grid_view_selector"
            )
            
            # Check if view type has changed
            if selected_view != st.session_state.grid_view_type or st.session_state.grid_viz_image is None:
                # Update session state
                st.session_state.grid_view_type = selected_view
                
                # Generate new visualization based on selected view
                st.session_state.grid_viz_image = generate_grid_visualization(
                    datacenter, 
                    selected_view,
                    layout_type
                )
            
            # Display the visualization using the base64 encoded image
            if st.session_state.grid_viz_image:
                st.markdown(f'<img src="{st.session_state.grid_viz_image}" alt="Data Center Grid Layout" width="100%">',
                           unsafe_allow_html=True)
                st.caption(f"Data Center Grid Layout - {layout_type}")
            
            # Compact explanation of the grid layout
            metrics_col1, metrics_col2 = st.columns(2)
            with metrics_col1:
                st.markdown(f"""
                **Room**: {room_width}m × {room_length}m  
                **Grid Size**: {grid_size*1000:.0f}mm  
                **Total Racks**: {len(datacenter.racks)}/{num_racks}
                """)
            with metrics_col2:
                st.markdown(f"""
                **Layout**: {layout_type}  
                **Pillar Count**: {len(datacenter.pillars)}  
                **Spacing**: {pillar_x_spacing:.1f}ft × {pillar_y_spacing:.1f}ft
                """)
    
    # Cooling analysis visualization
    with viz_tabs[1]:
        if st.session_state.show_cooling_analysis:
            try:
                # Generate cooling analysis visualization
                fig2, ax2 = visualize_datacenter_enhanced(
                    datacenter, 
                    title=f"Cooling Analysis - {layout_type}",
                    show_metrics=False,
                    highlight_zones=False,
                    cooling_analysis=True  # Enable cooling analysis for this view
                )
            except Exception as e:
                st.warning(f"Enhanced cooling visualization failed: {str(e)}. Using simplified visualization.")
                if SHAPELY_AVAILABLE:
                    try:
                        fig2, ax2, _ = visualize_datacenter_with_shapely(
                            datacenter,
                            title=f"Cooling Analysis - {layout_type}",
                            cooling_analysis=True
                        )
                    except Exception as e2:
                        st.warning(f"Shapely cooling visualization failed: {str(e2)}. Using basic visualization.")
                        fig2, ax2 = visualize_datacenter_simple(
                            datacenter,
                            title=f"Cooling Analysis - {layout_type}",
                            cooling_analysis=True
                        )
                else:
                    fig2, ax2 = visualize_datacenter_simple(
                        datacenter,
                        title=f"Cooling Analysis - {layout_type}",
                        cooling_analysis=True
                    )
            
            # Convert cooling figure to base64 string
            cooling_buf = BytesIO()
            fig2.savefig(cooling_buf, format='png', dpi=300, bbox_inches='tight')
            cooling_buf.seek(0)
            plt.close(fig2)
            
            cooling_img_str = base64.b64encode(cooling_buf.read()).decode()
            cooling_img_data = f"data:image/png;base64,{cooling_img_str}"
            
            # Display the visualization
            st.markdown(f'<img src="{cooling_img_data}" alt="Cooling Analysis" width="100%">',
                       unsafe_allow_html=True)
            st.caption(f"Cooling Efficiency Analysis - {layout_type}")
            
            # More compact explanation
            st.markdown("""
            <div style="font-size:0.9em">
            <b>Cooling Efficiency Legend:</b><br>
            🟢 <b>Green</b>: Good cooling efficiency<br>
            🟡 <b>Yellow</b>: Moderate cooling efficiency<br>
            🔴 <b>Red</b>: Poor cooling efficiency (potential hotspots)
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Cooling analysis was not enabled. Please regenerate the layout with 'Show Cooling Analysis' checked to see this view.")
    
    # Clearance analysis visualization
    with viz_tabs[2]:
        if st.session_state.show_clearance_analysis and hasattr(datacenter, 'racks') and len(datacenter.racks) > 0:
            if SHAPELY_AVAILABLE:
                try:
                    # First create the shapely visualization to get geometries
                    fig3, ax3, geometries = visualize_datacenter_with_shapely(
                        datacenter,
                        title="Data Center Layout with Shapely",
                        cooling_analysis=False
                    )
                    
                    # Close the figure since we don't need to display it
                    plt.close(fig3)
                    
                    # Now create the clearance analysis
                    fig4, ax4 = calculate_optimal_rack_clearance(datacenter, geometries)
                    
                    # Convert clearance figure to base64 string
                    clearance_buf = BytesIO()
                    fig4.savefig(clearance_buf, format='png', dpi=300, bbox_inches='tight')
                    clearance_buf.seek(0)
                    plt.close(fig4)
                    
                    clearance_img_str = base64.b64encode(clearance_buf.read()).decode()
                    clearance_img_data = f"data:image/png;base64,{clearance_img_str}"
                    
                    # Display the visualization
                    st.markdown(f'<img src="{clearance_img_data}" alt="Rack Clearance Analysis" width="100%">',
                               unsafe_allow_html=True)
                    st.caption("Rack Clearance Analysis")
                except Exception as e:
                    st.error(f"Error generating clearance analysis: {str(e)}")
                    st.info("Using simplified clearance analysis instead.")
                    
                    # Fallback to simplified visualization
                    fig4, ax4 = visualize_rack_clearance_simple(datacenter)
                    
                    # Convert clearance figure to base64 string
                    clearance_simple_buf = BytesIO()
                    fig4.savefig(clearance_simple_buf, format='png', dpi=300, bbox_inches='tight')
                    clearance_simple_buf.seek(0)
                    plt.close(fig4)
                    
                    clearance_simple_img_str = base64.b64encode(clearance_simple_buf.read()).decode()
                    clearance_simple_img_data = f"data:image/png;base64,{clearance_simple_img_str}"
                    
                    # Display the visualization
                    st.markdown(f'<img src="{clearance_simple_img_data}" alt="Rack Clearance Analysis (Simplified)" width="100%">',
                               unsafe_allow_html=True)
                    st.caption("Rack Clearance Analysis (Simplified)")
            else:
                # Use simplified visualization if Shapely is not available
                fig4, ax4 = visualize_rack_clearance_simple(datacenter)
                
                # Convert clearance figure to base64 string
                clearance_simple_buf = BytesIO()
                fig4.savefig(clearance_simple_buf, format='png', dpi=300, bbox_inches='tight')
                clearance_simple_buf.seek(0)
                plt.close(fig4)
                
                clearance_simple_img_str = base64.b64encode(clearance_simple_buf.read()).decode()
                clearance_simple_img_data = f"data:image/png;base64,{clearance_simple_img_str}"
                
                # Display the visualization
                st.markdown(f'<img src="{clearance_simple_img_data}" alt="Rack Clearance Analysis (Simplified)" width="100%">',
                           unsafe_allow_html=True)
                st.caption("Rack Clearance Analysis (Simplified)")
            
            # Compact explanation
            st.markdown("""
            <div style="font-size:0.9em">
            <b>Clearance Legend:</b><br>
            🟢 <b>Green dotted lines</b>: Minimum required clearance (0.9-1.2m)<br>
            🔴 <b>Red areas</b>: Clearance conflicts (too close)<br>
            🔵 <b>Blue areas</b>: Available pathways for movement and airflow
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Clearance analysis was not enabled or no racks were placed. Please regenerate the layout with 'Show Rack Clearance Analysis' checked to see this view.")
    
    # 3D visualization
    with viz_tabs[3]:
        st.markdown("<h4>3D Data Center Visualization</h4>", unsafe_allow_html=True)
        
        # Add 3D view controls in horizontal layout
        view_col1, view_col2 = st.columns(2)
        
        with view_col1:
            elevation_angle = st.slider("Elevation Angle", 0, 90, 30, 5)
            
        with view_col2:
            azimuth_angle = st.slider("Azimuth Angle", 0, 360, 45, 15)
        
        try:
            # Generate 3D visualization
            fig5, ax5 = create_simple_3d_visualization(
                datacenter,
                elevation=elevation_angle,
                azimuth=azimuth_angle,
                show_racks=True,
                show_pillars=True
            )
            
            # Convert 3D figure to base64 string
            viz_3d_buf = BytesIO()
            fig5.savefig(viz_3d_buf, format='png', dpi=300, bbox_inches='tight')
            viz_3d_buf.seek(0)
            plt.close(fig5)
            
            viz_3d_img_str = base64.b64encode(viz_3d_buf.read()).decode()
            viz_3d_img_data = f"data:image/png;base64,{viz_3d_img_str}"
            
            # Display the visualization
            st.markdown(f'<img src="{viz_3d_img_data}" alt="3D Visualization" width="100%">',
                       unsafe_allow_html=True)
            st.caption(f"3D Visualization - {layout_type}")
            
        except Exception as e:
            st.error(f"Error generating 3D visualization: {str(e)}")
            st.info("3D visualization requires matplotlib with 3D support. Please make sure you have the necessary packages installed.")
    
    # Metrics visualization
    with viz_tabs[4]:
        # Calculate metrics
        total_racks = len(datacenter.racks)
        total_area = datacenter.width_m * datacenter.length_m
        rack_area = sum(rack['width'] * rack['height'] for rack in datacenter.racks)
        density = rack_area / total_area
        
        # Calculate advanced metrics if possible
        if SHAPELY_AVAILABLE:
            try:
                # Get geometries for advanced metrics
                _, _, geometries = visualize_datacenter_with_shapely(
                    datacenter,
                    title="Data Center Layout with Shapely",
                    cooling_analysis=False,
                    show_metrics=False,
                    show_grid=False
                )
                
                # Calculate usable area (total minus pillars)
                pillar_area = sum(p.area for p in geometries['pillars'])
                usable_area = total_area - pillar_area
                
                # Calculate walkways (negative space)
                if 'racks' in geometries and geometries['racks']:
                    from shapely.ops import unary_union
                    obstacle_union = unary_union(geometries['racks'] + geometries['pillars'] + geometries['support_rooms'])
                    walkway_area = geometries['room'].area - obstacle_union.area
                else:
                    walkway_area = usable_area - rack_area
            except Exception as e:
                # Fall back to simple metrics
                pillar_area = sum(pillar['width'] * pillar['height'] for pillar in datacenter.pillars)
                usable_area = total_area - pillar_area
                walkway_area = usable_area - rack_area
        else:
            # Calculate simple metrics
            pillar_area = sum(pillar['width'] * pillar['height'] for pillar in datacenter.pillars)
            usable_area = total_area - pillar_area
            walkway_area = usable_area - rack_area
        
        # Display metrics with explanations in a more compact layout
        st.markdown("<h4>Data Center Layout Metrics</h4>", unsafe_allow_html=True)
        
        # Create a more visual metrics display using columns
        metrics_cols = st.columns(6)
        
        # Use smaller metrics for a more compact display
        with metrics_cols[0]:
            st.metric("Racks", f"{total_racks}")
            
        with metrics_cols[1]:
            st.metric("Rack Area", f"{rack_area:.1f} m²")
            
        with metrics_cols[2]:
            st.metric("Space Usage", f"{density:.1%}")
            
        with metrics_cols[3]:
            st.metric("Total Area", f"{total_area:.1f} m²")
            
        with metrics_cols[4]:
            st.metric("Usable Area", f"{usable_area:.1f} m²")
            
        with metrics_cols[5]:
            st.metric("Walkways", f"{walkway_area:.1f} m²")
        
        # Count aisles
        rack_y_coords = sorted(set(rack['grid_y'] for rack in datacenter.racks))
        aisles = 0
        for i in range(len(rack_y_coords) - 1):
            if rack_y_coords[i+1] - rack_y_coords[i] > 1:
                aisles += 1
        
        # Display layout scores and comparison
        st.markdown("<h4>Layout Performance Scores</h4>", unsafe_allow_html=True)
        
        # Calculate scores based on layout type and metrics
        cooling_score = 7.5  # Default score
        maintenance_score = 8.0  # Default score
        density_score = min(10, density * 20)  # Convert density to 0-10 scale
        
        # Adjust scores based on layout type
        if layout_type == "Hot/Cold Aisle":
            cooling_score = 8.5
        elif layout_type == "Cooling Optimized":
            cooling_score = 9.0
        elif layout_type == "High Density Zones":
            cooling_score = 7.0
            density_score += 1.0
        elif layout_type == "Spine-Leaf Network":
            maintenance_score = 8.5
        elif layout_type == "Cluster-Based":
            maintenance_score = 8.2
            cooling_score = 7.8
        
        # Calculate maintenance score based on walkway ratio
        walkway_factor = walkway_area / usable_area
        if walkway_factor < 0.3:
            maintenance_score = max(5.0, maintenance_score - 2.0)  # Penalize for too little walkway
        elif walkway_factor > 0.6:
            maintenance_score = max(6.0, maintenance_score - 1.0)  # Slight penalty for excessive walkway
        
        # Display scores with a horizontal bar chart
        scores = {
            "Cooling Efficiency": cooling_score,
            "Maintenance Access": maintenance_score,
            "Space Utilization": density_score,
            "Overall Score": (cooling_score + maintenance_score + density_score) / 3
        }
        
        # Create the chart with a more compact size
        fig, ax = plt.subplots(figsize=(10, 3))
        y_pos = np.arange(len(scores))
        score_values = list(scores.values())
        score_labels = list(scores.keys())
        
        # Create horizontal bars
        bars = ax.barh(y_pos, score_values, align='center', height=0.6)
        
        # Color the bars based on score
        colors = ['#ff6666', '#ffcc66', '#66b266']
        for i, bar in enumerate(bars):
            bar.set_color(colors[min(2, int(score_values[i] / 3.5))])
        
        # Add scores as text on the bars
        for i, v in enumerate(score_values):
            ax.text(v + 0.1, i, f"{v:.1f}/10", va='center', fontsize=9)
        
        # Customize the chart for a more compact look
        ax.set_yticks(y_pos)
        ax.set_yticklabels(score_labels, fontsize=9)
        ax.set_xlim(0, 10.5)
        ax.set_xlabel('Score (out of 10)', fontsize=9)
        
        # Add grid lines
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Convert chart to base64 string
        chart_buf = BytesIO()
        plt.tight_layout()
        plt.savefig(chart_buf, format='png', dpi=300, bbox_inches='tight')
        chart_buf.seek(0)
        plt.close()
        
        chart_img_str = base64.b64encode(chart_buf.read()).decode()
        chart_img_data = f"data:image/png;base64,{chart_img_str}"
        
        # Display the chart
        st.markdown(f'<img src="{chart_img_data}" alt="Layout Performance Scores" width="100%">',
                   unsafe_allow_html=True)
        
        # Add recommendations in a more compact format
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.markdown("<h5>Recommendations</h5>", unsafe_allow_html=True)
            
            # Determine recommendations based on layout type and scores
            recommendations = []
            
            if layout_type == "Hot/Cold Aisle":
                recommendations.append("Consider adding containment systems for better cooling")
                recommendations.append("Ensure proper airflow direction in hot aisles")
                
            elif layout_type == "Cooling Optimized":
                recommendations.append("Monitor temperature gradients to confirm optimization")
                recommendations.append("Consider in-row cooling for high heat areas")
                
            elif layout_type == "Spine-Leaf Network":
                recommendations.append("Position network switches optimally within the layout")
                recommendations.append("Use structured cabling for organization")
                
            elif layout_type == "Cluster-Based":
                recommendations.append("Implement isolated power for each cluster")
                recommendations.append("Consider separate monitoring for each cluster")
                
            elif layout_type == "High Density Zones":
                recommendations.append("Add extra cooling in high-density areas")
                recommendations.append("Consider liquid cooling for high power racks")
                
            elif layout_type == "Circular/Radial":
                recommendations.append("Plan cable lengths for non-traditional layout")
                recommendations.append("Use central cooling distribution for uniformity")
                
            # Add general recommendations based on metrics
            if density > 0.5:
                recommendations.append("⚠️ High rack density may cause cooling issues")
                
            if walkway_factor < 0.3:
                recommendations.append("⚠️ Limited walkway space may impede maintenance")
                
            if cooling_score < 7.0:
                recommendations.append("⚠️ Consider improving cooling efficiency")
                
            # Display recommendations as a compact list
            if recommendations:
                for rec in recommendations[:4]:  # Limit to top 4 recommendations
                    st.markdown(f"• {rec}")
            else:
                st.markdown("Layout appears well-balanced")
        
        with rec_col2:
            st.markdown("<h5>Efficiency Metrics</h5>", unsafe_allow_html=True)
            st.markdown(f"""
            • **Aisle Count**: {aisles}
            • **Walkway Ratio**: {walkway_area/usable_area:.1%}
            • **Pillar Area**: {pillar_area:.1f} m²
            • **Rack Density**: {density:.1%} (recommended: 30-40%)
            """)
            
            # Download option
            st.download_button(
                label="Download Layout Data",
                data="Layout data would be exported here in a real implementation",
                file_name=f"datacenter_layout_{layout_type.replace('/', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
    # Add a footer with action buttons
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        if st.button("Generate New Layout", use_container_width=True):
            st.session_state.generated = False
            st.rerun()
            
    with footer_col2:
        if st.button("Generate PDF Report", use_container_width=True):
            st.info("PDF report generation would be implemented here")
            
    with footer_col3:
        if st.button("Compare Layouts", use_container_width=True):
            st.info("Layout comparison would be implemented here")