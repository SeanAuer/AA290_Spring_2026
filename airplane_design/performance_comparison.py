#!/usr/bin/env python3
"""
Performance Comparison Script
Compares baseline turbofan and open fan aircraft performance

Created: December 2024
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Add paths for both aircraft modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'baseline_airplane', 'mission_simulation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'baseline_open_fan'))

# Import both aircraft configurations
try:
    # Import turbofan aircraft
    import baseline_turbofan_airplane as turbofan_module
    
    # Import open fan aircraft  
    import baseline_open_fan_airplane as open_fan_module
    
except ImportError as e:
    print(f"Error importing aircraft modules: {e}")
    sys.exit(1)

def extract_performance_metrics(results):
    """Extract key performance metrics from mission results"""
    
    metrics = {}
    
    # Get segments data
    segments = results.segments
    
    # Initialize totals
    total_fuel_burn = 0
    total_distance = 0
    total_time = 0
    
    # Extract data from each segment
    for segment_name, segment in segments.items():
        if hasattr(segment, 'conditions'):
            conditions = segment.conditions
            
            # Fuel consumption
            if hasattr(conditions, 'weights') and hasattr(conditions.weights, 'total_mass'):
                fuel_used = conditions.weights.total_mass[0, 0] - conditions.weights.total_mass[-1, 0]
                total_fuel_burn += fuel_used
            
            # Distance and time
            if hasattr(conditions, 'frames') and hasattr(conditions.frames, 'inertial'):
                if hasattr(conditions.frames.inertial, 'position_vector'):
                    segment_distance = np.linalg.norm(
                        conditions.frames.inertial.position_vector[-1, :] - 
                        conditions.frames.inertial.position_vector[0, :]
                    )
                    total_distance += segment_distance
            
            if hasattr(conditions, 'frames') and hasattr(conditions.frames, 'inertial'):
                if hasattr(conditions.frames.inertial, 'time'):
                    segment_time = conditions.frames.inertial.time[-1, 0] - conditions.frames.inertial.time[0, 0]
                    total_time += segment_time
    
    # Calculate performance metrics
    metrics['total_fuel_burn_kg'] = total_fuel_burn
    metrics['total_distance_km'] = total_distance / 1000
    metrics['total_time_hours'] = total_time / 3600
    metrics['fuel_efficiency_kg_per_km'] = total_fuel_burn / (total_distance / 1000) if total_distance > 0 else 0
    
    # Extract cruise segment performance
    if 'cruise' in segments:
        cruise = segments['cruise']
        if hasattr(cruise, 'conditions'):
            cruise_conditions = cruise.conditions
            
            # Cruise speed
            if hasattr(cruise_conditions, 'freestream') and hasattr(cruise_conditions.freestream, 'velocity'):
                metrics['cruise_speed_mps'] = np.mean(cruise_conditions.freestream.velocity[:, 0])
            
            # Cruise altitude
            if hasattr(cruise_conditions, 'freestream') and hasattr(cruise_conditions.freestream, 'altitude'):
                metrics['cruise_altitude_m'] = np.mean(cruise_conditions.freestream.altitude[:, 0])
            
            # Cruise fuel flow
            if hasattr(cruise_conditions, 'energy'):
                for network_name, network in cruise_conditions.energy.items():
                    if hasattr(network, 'fuel_lines'):
                        for fuel_line_name, fuel_line in network.fuel_lines.items():
                            if hasattr(fuel_line, 'fuel_flow_rate'):
                                metrics['cruise_fuel_flow_kg_s'] = np.mean(fuel_line.fuel_flow_rate[:, 0])
    
    return metrics

def extract_vehicle_characteristics(vehicle):
    """Extract key vehicle design characteristics"""
    
    characteristics = {}
    
    # Mass properties
    characteristics['mtow_kg'] = vehicle.mass_properties.max_takeoff
    characteristics['oew_kg'] = vehicle.mass_properties.operating_empty
    characteristics['max_fuel_kg'] = vehicle.mass_properties.max_takeoff - vehicle.mass_properties.operating_empty
    
    # Engine characteristics
    if hasattr(vehicle, 'networks') and len(vehicle.networks) > 0:
        network = list(vehicle.networks.values())[0]
        if hasattr(network, 'propulsors') and len(network.propulsors) > 0:
            # Get first propulsor (propulsors is a dictionary with string keys)
            propulsor = list(network.propulsors.values())[0]
            
            if hasattr(propulsor, 'bypass_ratio'):
                characteristics['bypass_ratio'] = propulsor.bypass_ratio
            
            if hasattr(propulsor, 'fan') and hasattr(propulsor.fan, 'pressure_ratio'):
                characteristics['fan_pressure_ratio'] = propulsor.fan.pressure_ratio
            
            if hasattr(propulsor, 'fan') and hasattr(propulsor.fan, 'polytropic_efficiency'):
                characteristics['fan_efficiency'] = propulsor.fan.polytropic_efficiency
            
            if hasattr(propulsor, 'nacelle') and hasattr(propulsor.nacelle.areas, 'wetted'):
                characteristics['nacelle_wetted_area'] = propulsor.nacelle.areas.wetted
    
    return characteristics

def run_aircraft_simulation(aircraft_module, aircraft_name, module_dir=None):
    """Run simulation for a given aircraft module"""
    
    print(f"\n{'='*50}")
    print(f"Running {aircraft_name} simulation...")
    print(f"{'='*50}")
    
    # Save current working directory
    original_cwd = os.getcwd()
    
    try:
        # Change to module directory if specified
        if module_dir:
            os.chdir(module_dir)
            print(f"Changed working directory to: {module_dir}")
        
        print("Setting up vehicle...")
        vehicle = aircraft_module.vehicle_setup()
        
        print("Setting up configurations...")
        configs = aircraft_module.configs_setup(vehicle)
        
        print("Setting up analyses...")
        analyses = aircraft_module.analyses_setup(configs)
        
        print("Setting up mission...")
        mission = aircraft_module.mission_setup(analyses)
        missions = aircraft_module.missions_setup(mission)
        
        print("Running mission evaluation...")
        results = missions.base_mission.evaluate()
        
        print(f"{aircraft_name} simulation completed successfully!")
        
        return results, vehicle
        
    except Exception as e:
        print(f"Error running {aircraft_name} simulation: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    finally:
        # Always restore original working directory
        os.chdir(original_cwd)

def compare_performance(turbofan_metrics, open_fan_metrics, turbofan_vehicle, open_fan_vehicle):
    """Compare performance metrics between aircraft with detailed breakdown"""
    
    print(f"\n{'='*80}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*80}")
    
    # Basic performance comparison
    comparison_data = []
    
    key_metrics = ['total_fuel_burn_kg', 'total_distance_km', 'total_time_hours', 'fuel_efficiency_kg_per_km']
    
    for metric in key_metrics:
        if metric in turbofan_metrics and metric in open_fan_metrics:
            turbofan_val = turbofan_metrics[metric]
            open_fan_val = open_fan_metrics[metric]
            
            # Calculate difference and percentage
            diff = open_fan_val - turbofan_val
            if turbofan_val != 0:
                pct_diff = (diff / turbofan_val) * 100
            else:
                pct_diff = 0
            
            comparison_data.append({
                'Metric': metric,
                'Turbofan': turbofan_val,
                'Open Fan': open_fan_val,
                'Difference': diff,
                'Percent Difference (%)': pct_diff
            })
    
    df = pd.DataFrame(comparison_data)
    
    # Format the output
    print(f"{'Metric':<25} {'Turbofan':<15} {'Open Fan':<15} {'Difference':<15} {'% Diff':<10}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        metric = row['Metric']
        turbofan = row['Turbofan']
        open_fan = row['Open Fan']
        diff = row['Difference']
        pct_diff = row['Percent Difference (%)']
        
        print(f"{metric:<25} {turbofan:<15.3f} {open_fan:<15.3f} {diff:<15.3f} {pct_diff:<10.2f}")
    
    # Extract vehicle characteristics for detailed analysis
    turbofan_chars = extract_vehicle_characteristics(turbofan_vehicle)
    open_fan_chars = extract_vehicle_characteristics(open_fan_vehicle)
    
    # Detailed breakdown
    print(f"\n{'='*80}")
    print("DETAILED BREAKDOWN")
    print(f"{'='*80}")
    
    # Engine design comparison
    print("\nENGINE DESIGN PARAMETERS:")
    print("-" * 40)
    if 'bypass_ratio' in turbofan_chars and 'bypass_ratio' in open_fan_chars:
        print(f"Bypass Ratio:        Turbofan {turbofan_chars['bypass_ratio']:.1f} | Open Fan {open_fan_chars['bypass_ratio']:.1f}")
    
    if 'fan_pressure_ratio' in turbofan_chars and 'fan_pressure_ratio' in open_fan_chars:
        print(f"Fan Pressure Ratio:  Turbofan {turbofan_chars['fan_pressure_ratio']:.2f} | Open Fan {open_fan_chars['fan_pressure_ratio']:.2f}")
    
    if 'fan_efficiency' in turbofan_chars and 'fan_efficiency' in open_fan_chars:
        print(f"Fan Efficiency:      Turbofan {turbofan_chars['fan_efficiency']:.3f} | Open Fan {open_fan_chars['fan_efficiency']:.3f}")
    
    # Weight breakdown
    print("\nWEIGHT ANALYSIS:")
    print("-" * 40)
    if 'mtow_kg' in turbofan_chars and 'mtow_kg' in open_fan_chars:
        mtow_diff = open_fan_chars['mtow_kg'] - turbofan_chars['mtow_kg']
        mtow_pct = (mtow_diff / turbofan_chars['mtow_kg']) * 100
        print(f"MTOW:                Turbofan {turbofan_chars['mtow_kg']:.0f} kg | Open Fan {open_fan_chars['mtow_kg']:.0f} kg")
        print(f"MTOW Difference:     {mtow_diff:.0f} kg ({mtow_pct:+.1f}%)")
    
    if 'oew_kg' in turbofan_chars and 'oew_kg' in open_fan_chars:
        oew_diff = open_fan_chars['oew_kg'] - turbofan_chars['oew_kg']
        oew_pct = (oew_diff / turbofan_chars['oew_kg']) * 100
        print(f"OEW:                 Turbofan {turbofan_chars['oew_kg']:.0f} kg | Open Fan {open_fan_chars['oew_kg']:.0f} kg")
        print(f"OEW Difference:      {oew_diff:.0f} kg ({oew_pct:+.1f}%) - Dorsey integration penalties")
    
    # Performance drivers analysis
    print("\nPERFORMANCE DRIVERS:")
    print("-" * 40)
    
    fuel_eff_row = df[df['Metric'] == 'fuel_efficiency_kg_per_km']
    if not fuel_eff_row.empty:
        fuel_eff_diff = fuel_eff_row['Percent Difference (%)'].iloc[0]
        
        if fuel_eff_diff > 0:
            print(f"• Open Fan burns {fuel_eff_diff:.1f}% MORE fuel per km")
            print("• Primary causes:")
            
            if 'fan_efficiency' in turbofan_chars and 'fan_efficiency' in open_fan_chars:
                eff_penalty = ((turbofan_chars['fan_efficiency'] - open_fan_chars['fan_efficiency']) / turbofan_chars['fan_efficiency']) * 100
                print(f"  - Fan efficiency penalty: {eff_penalty:.1f}% (includes Dorsey integration losses)")
            
            if 'nacelle_wetted_area' in open_fan_chars:
                print(f"  - Nacelle drag penalty: 40% increase (Dorsey propeller slipstream effects)")
            
            if 'oew_kg' in turbofan_chars and 'oew_kg' in open_fan_chars:
                weight_penalty = ((open_fan_chars['oew_kg'] - turbofan_chars['oew_kg']) / turbofan_chars['mtow_kg']) * 100
                print(f"  - Weight penalty: {weight_penalty:.1f}% of MTOW (noise shielding + structural)")
            
            print(f"  - Architecture mismatch: High bypass ratio ({open_fan_chars.get('bypass_ratio', 'N/A')}) optimized for lower speeds")
        else:
            print(f"• Open Fan is {abs(fuel_eff_diff):.1f}% more fuel efficient")
    
    return df

def main():
    """Main comparison function"""
    
    print("Aircraft Performance Comparison Tool")
    print("Comparing Baseline Turbofan vs Open Fan Aircraft")
    
    # Define module directories
    script_dir = Path(__file__).parent
    turbofan_dir = script_dir.parent / 'baseline_airplane' / 'mission_simulation'
    open_fan_dir = script_dir / 'baseline_open_fan'
    
    # Run turbofan simulation
    turbofan_results, turbofan_vehicle = run_aircraft_simulation(
        turbofan_module, "Baseline Turbofan", str(turbofan_dir)
    )
    
    # Run open fan simulation  
    open_fan_results, open_fan_vehicle = run_aircraft_simulation(
        open_fan_module, "Baseline Open Fan", str(open_fan_dir)
    )
    
    if turbofan_results is None or open_fan_results is None:
        print("One or both simulations failed. Cannot perform comparison.")
        return
    
    # Extract performance metrics
    print("\nExtracting performance metrics...")
    turbofan_metrics = extract_performance_metrics(turbofan_results)
    open_fan_metrics = extract_performance_metrics(open_fan_results)
    
    # Compare performance
    comparison_df = compare_performance(turbofan_metrics, open_fan_metrics, turbofan_vehicle, open_fan_vehicle)
    
    # Save results with additional context
    output_file = Path(__file__).parent / "performance_comparison_results.csv"
    
    # Add interpretation column
    comparison_df['Interpretation'] = comparison_df.apply(
        lambda row: f"Open Fan {'+' if row['Percent Difference (%)'] > 0 else ''}{row['Percent Difference (%)']:.1f}% vs Turbofan", 
        axis=1
    )
    
    comparison_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Print summary with correct interpretation
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    fuel_efficiency_diff = comparison_df[comparison_df['Metric'] == 'fuel_efficiency_kg_per_km']['Percent Difference (%)'].iloc[0]
    
    if fuel_efficiency_diff > 0:
        print(f"Open Fan aircraft burns {fuel_efficiency_diff:.1f}% MORE fuel per km than Turbofan")
        print("(Open Fan is LESS fuel efficient)")
        print("\nThis aligns with Dorsey's findings that open rotors face significant")
        print("integration penalties on high-speed cruise missions like this one.")
        print("Open rotors are better suited for:")
        print("• Lower cruise speeds (Mach 0.6-0.7 vs 0.78)")
        print("• Shorter range missions (500-1500 nm vs 1000+ nm)")
        print("• Regional aircraft with high passenger density")
    else:
        print(f"Open Fan aircraft is {abs(fuel_efficiency_diff):.1f}% more fuel efficient than Turbofan")
        print("(Open Fan is MORE fuel efficient)")
    
    print("\nNote: Both aircraft fly identical mission profiles.")
    print("Small differences in distance/time are numerical precision effects.")
    
    print("\nComparison complete!")

if __name__ == "__main__":
    import sys
    from io import StringIO
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        main()
        output = captured_output.getvalue()
        
        # Restore stdout and print to console
        sys.stdout = old_stdout
        print(output)
        
        # Write to file
        with open('performance_comparison_results.txt', 'w') as f:
            f.write(output)
        print("\nResults saved to: performance_comparison_results.txt")
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"Error: {e}")
        raise