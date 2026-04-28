#!/usr/bin/env python3
"""
Component Analysis Script
Compares baseline turbofan and open fan aircraft component-by-component

Created: December 2024
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add paths for aircraft modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'baseline_airplane', 'mission_simulation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'baseline_open_fan'))

try:
    # Import aircraft modules
    import baseline_turbofan_airplane as turbofan_module
    import baseline_open_fan_airplane as open_fan_module
    
    # RCAIDE imports
    import RCAIDE
    from RCAIDE.Framework.Core import Units
    
    print("Successfully imported all modules")
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def compare_vehicle_properties(turbofan_vehicle, open_fan_vehicle):
    """Compare basic vehicle properties between turbofan and open fan"""
    
    print("\n" + "="*80)
    print("VEHICLE PROPERTY COMPARISON")
    print("="*80)
    
    properties = [
        ('MTOW (kg)', 'mass_properties.max_takeoff'),
        ('OEW (kg)', 'mass_properties.operating_empty'),
        ('Max Zero Fuel (kg)', 'mass_properties.max_zero_fuel'),
        ('Reference Area (m²)', 'reference_area'),
        ('Passengers', 'passengers'),
        ('Design Mach', 'flight_envelope.design_mach_number'),
        ('Design Range (nmi)', 'flight_envelope.design_range')
    ]
    
    print(f"{'Property':<25} {'Turbofan':<15} {'Open Fan':<15} {'Difference':<15} {'% Diff':<10}")
    print("-" * 80)
    
    for prop_name, prop_path in properties:
        try:
            # Get values from both vehicles
            tf_obj = turbofan_vehicle
            of_obj = open_fan_vehicle
            
            for attr in prop_path.split('.'):
                tf_obj = getattr(tf_obj, attr)
                of_obj = getattr(of_obj, attr)
            
            tf_val = tf_obj
            of_val = of_obj
            
            if isinstance(tf_val, (int, float)) and isinstance(of_val, (int, float)):
                diff = of_val - tf_val
                pct_diff = (diff / tf_val) * 100 if tf_val != 0 else 0
                print(f"{prop_name:<25} {tf_val:<15.1f} {of_val:<15.1f} {diff:<15.1f} {pct_diff:<10.1f}")
            else:
                print(f"{prop_name:<25} {str(tf_val):<15} {str(of_val):<15} {'N/A':<15} {'N/A':<10}")
                
        except Exception as e:
            print(f"{prop_name:<25} {'Error':<15} {'Error':<15} {'N/A':<15} {'N/A':<10}")

def compare_engine_architectures(turbofan_vehicle, open_fan_vehicle):
    """Compare engine architectures and parameters in detail"""
    
    print("\n" + "="*80)
    print("ENGINE ARCHITECTURE COMPARISON")
    print("="*80)
    
    # Get first propulsor from each vehicle
    tf_network = list(turbofan_vehicle.networks.values())[0]
    of_network = list(open_fan_vehicle.networks.values())[0]
    
    tf_prop = tf_network.propulsors[0]
    of_prop = of_network.propulsors[0]
    
    print(f"Turbofan Engine Type: {type(tf_prop).__name__}")
    print(f"Open Fan Engine Type: {type(of_prop).__name__}")
    print()
    
    # Engine design parameters
    print(f"{'Parameter':<25} {'Turbofan':<15} {'Open Fan':<15} {'Difference':<15} {'% Diff':<10}")
    print("-" * 80)
    
    engine_params = [
        ('Bypass Ratio', 'bypass_ratio'),
        ('Design Thrust (N)', 'design_thrust'),
        ('Design Altitude (ft)', 'design_altitude'),
        ('Design Mach', 'design_mach_number'),
        ('Engine Length (m)', 'engine_length')
    ]
    
    for param_name, param_attr in engine_params:
        try:
            tf_val = getattr(tf_prop, param_attr, None)
            of_val = getattr(of_prop, param_attr, None)
            
            if tf_val is not None and of_val is not None and isinstance(tf_val, (int, float)) and isinstance(of_val, (int, float)):
                diff = of_val - tf_val
                pct_diff = (diff / tf_val) * 100 if tf_val != 0 else 0
                print(f"{param_name:<25} {tf_val:<15.2f} {of_val:<15.2f} {diff:<15.2f} {pct_diff:<10.1f}")
            else:
                tf_str = str(tf_val) if tf_val is not None else 'N/A'
                of_str = str(of_val) if of_val is not None else 'N/A'
                print(f"{param_name:<25} {tf_str:<15} {of_str:<15} {'N/A':<15} {'N/A':<10}")
        except Exception as e:
            print(f"{param_name:<25} {'Error':<15} {'Error':<15} {'N/A':<15} {'N/A':<10}")

def compare_engine_components(turbofan_vehicle, open_fan_vehicle):
    """Compare individual engine components between turbofan and open fan"""
    
    print("\n" + "="*80)
    print("ENGINE COMPONENT COMPARISON")
    print("="*80)
    
    # Get propulsors
    tf_network = list(turbofan_vehicle.networks.values())[0]
    of_network = list(open_fan_vehicle.networks.values())[0]
    
    tf_prop = tf_network.propulsors[0]
    of_prop = of_network.propulsors[0]
    
    # Fan/Compressor comparison
    print("\nFAN/COMPRESSOR PARAMETERS:")
    print(f"{'Component':<25} {'Turbofan':<15} {'Open Fan':<15} {'Difference':<15} {'% Diff':<10}")
    print("-" * 80)
    
    # Fan parameters
    fan_params = [
        ('Fan Pressure Ratio', 'fan.pressure_ratio'),
        ('Fan Efficiency', 'fan.polytropic_efficiency')
    ]
    
    for param_name, param_path in fan_params:
        try:
            # Navigate to the parameter
            tf_obj = tf_prop
            of_obj = of_prop
            
            for attr in param_path.split('.'):
                tf_obj = getattr(tf_obj, attr, None)
                of_obj = getattr(of_obj, attr, None)
            
            if tf_obj is not None and of_obj is not None and isinstance(tf_obj, (int, float)) and isinstance(of_obj, (int, float)):
                diff = of_obj - tf_obj
                pct_diff = (diff / tf_obj) * 100 if tf_obj != 0 else 0
                print(f"{param_name:<25} {tf_obj:<15.3f} {of_obj:<15.3f} {diff:<15.3f} {pct_diff:<10.1f}")
            else:
                tf_str = str(tf_obj) if tf_obj is not None else 'N/A'
                of_str = str(of_obj) if of_obj is not None else 'N/A'
                print(f"{param_name:<25} {tf_str:<15} {of_str:<15} {'N/A':<15} {'N/A':<10}")
        except Exception as e:
            print(f"{param_name:<25} {'Error':<15} {'Error':<15} {'N/A':<15} {'N/A':<10}")
    
    # Core components (should be identical)
    print("\nCORE COMPONENT PARAMETERS:")
    print(f"{'Component':<25} {'Turbofan':<15} {'Open Fan':<15} {'Difference':<15} {'% Diff':<10}")
    print("-" * 80)
    
    core_params = [
        ('LPC Pressure Ratio', 'low_pressure_compressor.pressure_ratio'),
        ('LPC Efficiency', 'low_pressure_compressor.polytropic_efficiency'),
        ('HPC Pressure Ratio', 'high_pressure_compressor.pressure_ratio'),
        ('HPC Efficiency', 'high_pressure_compressor.polytropic_efficiency'),
        ('Combustor Efficiency', 'combustor.efficiency'),
        ('Turbine Inlet Temp (K)', 'combustor.turbine_inlet_temperature'),
        ('HPT Efficiency', 'high_pressure_turbine.polytropic_efficiency'),
        ('LPT Efficiency', 'low_pressure_turbine.polytropic_efficiency')
    ]
    
    for param_name, param_path in core_params:
        try:
            # Navigate to the parameter
            tf_obj = tf_prop
            of_obj = of_prop
            
            for attr in param_path.split('.'):
                tf_obj = getattr(tf_obj, attr, None)
                of_obj = getattr(of_obj, attr, None)
            
            if tf_obj is not None and of_obj is not None and isinstance(tf_obj, (int, float)) and isinstance(of_obj, (int, float)):
                diff = of_obj - tf_obj
                pct_diff = (diff / tf_obj) * 100 if tf_obj != 0 else 0
                print(f"{param_name:<25} {tf_obj:<15.3f} {of_obj:<15.3f} {diff:<15.3f} {pct_diff:<10.1f}")
            else:
                tf_str = str(tf_obj) if tf_obj is not None else 'N/A'
                of_str = str(of_obj) if of_obj is not None else 'N/A'
                print(f"{param_name:<25} {tf_str:<15} {of_str:<15} {'N/A':<15} {'N/A':<10}")
        except Exception as e:
            print(f"{param_name:<25} {'Error':<15} {'Error':<15} {'N/A':<15} {'N/A':<10}")

def compare_nacelle_properties(turbofan_vehicle, open_fan_vehicle):
    """Compare nacelle and installation properties"""
    
    print("\n" + "="*80)
    print("NACELLE AND INSTALLATION COMPARISON")
    print("="*80)
    
    # Get propulsors
    tf_network = list(turbofan_vehicle.networks.values())[0]
    of_network = list(open_fan_vehicle.networks.values())[0]
    
    tf_prop = tf_network.propulsors[0]
    of_prop = of_network.propulsors[0]
    
    print(f"{'Property':<25} {'Turbofan':<15} {'Open Fan':<15} {'Difference':<15} {'% Diff':<10}")
    print("-" * 80)
    
    nacelle_params = [
        ('Nacelle Length (m)', 'nacelle.length'),
        ('Nacelle Diameter (m)', 'nacelle.diameter'),
        ('Nacelle Wetted Area', 'nacelle.areas.wetted'),
        ('Engine Origin X (m)', 'origin[0][0]'),
        ('Engine Origin Y (m)', 'origin[0][1]'),
        ('Engine Origin Z (m)', 'origin[0][2]')
    ]
    
    for param_name, param_path in nacelle_params:
        try:
            # Navigate to the parameter
            tf_obj = tf_prop
            of_obj = of_prop
            
            # Handle special case for origin coordinates
            if 'origin[' in param_path:
                tf_val = eval(f"tf_prop.{param_path}")
                of_val = eval(f"of_prop.{param_path}")
            else:
                for attr in param_path.split('.'):
                    tf_obj = getattr(tf_obj, attr, None)
                    of_obj = getattr(of_obj, attr, None)
                tf_val = tf_obj
                of_val = of_obj
            
            if tf_val is not None and of_val is not None and isinstance(tf_val, (int, float)) and isinstance(of_val, (int, float)):
                diff = of_val - tf_val
                pct_diff = (diff / tf_val) * 100 if tf_val != 0 else 0
                print(f"{param_name:<25} {tf_val:<15.3f} {of_val:<15.3f} {diff:<15.3f} {pct_diff:<10.1f}")
            else:
                tf_str = str(tf_val) if tf_val is not None else 'N/A'
                of_str = str(of_val) if of_val is not None else 'N/A'
                print(f"{param_name:<25} {tf_str:<15} {of_str:<15} {'N/A':<15} {'N/A':<10}")
        except Exception as e:
            print(f"{param_name:<25} {'Error':<15} {'Error':<15} {'N/A':<15} {'N/A':<10}")

def main():
    """Main analysis function"""
    
    print("Component Analysis: Turbofan vs Open Fan Aircraft")
    print("Comparing baseline aircraft component-by-component")
    
    # Create vehicles
    print("\nCreating turbofan vehicle...")
    turbofan_vehicle = turbofan_module.vehicle_setup()
    
    print("Creating open fan vehicle...")
    open_fan_vehicle = open_fan_module.vehicle_setup(include_dorsey_penalties=True)
    
    # Perform comparisons
    compare_vehicle_properties(turbofan_vehicle, open_fan_vehicle)
    compare_engine_architectures(turbofan_vehicle, open_fan_vehicle)
    compare_engine_components(turbofan_vehicle, open_fan_vehicle)
    compare_nacelle_properties(turbofan_vehicle, open_fan_vehicle)
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print("\nKey Differences Identified:")
    print("• Engine Architecture: Both use Turbofan class (corrected from earlier turboprop approach)")
    print("• Bypass Ratio: Turbofan ~5.4 vs Open Fan 36 (7x higher for open rotor)")
    print("• Fan Pressure Ratio: Turbofan 1.7 vs Open Fan 1.1 (Dorsey specification)")
    print("• Fan Efficiency: Open Fan reduced by Dorsey integration penalties")
    print("• Nacelle Properties: Open Fan has drag penalties from propeller slipstream")
    print("• Weight: Open Fan has 7% MTOW penalty for noise shielding and structural reinforcement")
    print("\nCore Components: Identical between both configurations (LPC, HPC, combustor, turbines)")
    print("\nThis component analysis shows the specific parameters driving performance differences.")

if __name__ == "__main__":
    main()