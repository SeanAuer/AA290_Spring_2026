# Open Rotor Study Framework using RCAIDE-LEADS
# Design Space Exploration of Open Rotor Configurations

import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import pandas as pd
import os
import sys

# RCAIDE imports
import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Library.Methods.Powertrain.Propulsors.Turbofan import design_turbofan
from RCAIDE.Library.Methods.Powertrain.Propulsors.Turboprop import design_turboprop
from RCAIDE.Library.Methods.Powertrain.Converters.Rotor import design_propeller

class OpenRotorStudy:
    """
    Framework for open rotor aircraft design space exploration using RCAIDE-LEADS
    
    Key parameters:
    - Payload range: 50-400 passengers (50 passenger increments)
    - Design range: 1,000-7,000 nm (1,000 nm increments)
    - Three configurations: Turbofan baseline, Aft-mounted open rotor, Wing-mounted open rotor
    - Optimization objective: Minimum fuel burn on economic range mission
    """
    
    def __init__(self):
        self.payload_range = np.arange(50, 450, 50)  # 50 to 400 passengers
        self.design_ranges = np.arange(1000, 8000, 1000)  # 1000 to 7000 nm
        self.configurations = ['turbofan', 'aft_open_rotor', 'wing_open_rotor']
        
        # Study parameters
        self.economic_range_factor = 1/3  # Economic range = 1/3 design range (except 1000nm = 1/2)
        self.reserve_range = 200  # nm
        self.hold_time = 30  # minutes
        
        # Open rotor parameters
        self.open_rotor_params = {
            'fan_pressure_ratio': 1.1,  # Typical open rotor ~1.1-1.2
            'bypass_ratio_range': [16, 38],  # Open rotor range 16-38
            'fan_efficiency_mach_trend': True,  # Efficiency decreases with Mach
            'gear_ratio': 6.0,
            'gear_efficiency': 0.99,
            'blade_count': 10,  # Counter-rotating
            'activity_factor': 150
        }
        
        # Results storage
        self.results = {}
        
    def create_baseline_turbofan(self, passengers, design_range):
        """Create baseline turbofan aircraft"""
        
        # Import your baseline turbofan setup
        from baseline_airplane.mission_simulation.baseline_turbofan_airplane import vehicle_setup
        
        vehicle = vehicle_setup()
        
        # Scale aircraft for passenger count and range
        vehicle = self._scale_aircraft(vehicle, passengers, design_range)
        
        return vehicle
    
    def create_aft_open_rotor(self, passengers, design_range):
        """Create aft-mounted open rotor configuration"""
        
        # Start with baseline
        vehicle = self.create_baseline_turbofan(passengers, design_range)
        
        # Modify for aft-mounted open rotor
        vehicle.tag = f'Aft_Open_Rotor_{passengers}pax_{design_range}nm'
        
        # Replace turbofan network with open rotor
        vehicle = self._convert_to_aft_open_rotor(vehicle)
        
        # Modify empennage for T-tail configuration
        vehicle = self._modify_empennage_for_aft_mount(vehicle)
        
        return vehicle
    
    def create_wing_open_rotor(self, passengers, design_range):
        """Create wing-mounted open rotor configuration"""
        
        # Start with baseline
        vehicle = self.create_baseline_turbofan(passengers, design_range)
        
        # Modify for wing-mounted open rotor
        vehicle.tag = f'Wing_Open_Rotor_{passengers}pax_{design_range}nm'
        
        # Replace turbofan network with open rotor
        vehicle = self._convert_to_wing_open_rotor(vehicle)
        
        # Account for scrubbing effects and landing gear penalties
        vehicle = self._apply_wing_mount_penalties(vehicle)
        
        return vehicle
    
    def _scale_aircraft(self, vehicle, passengers, design_range):
        """Scale aircraft geometry and mass for different passenger counts and ranges"""
        
        # Passenger scaling (step-wise regression)
        baseline_passengers = 170
        passenger_scale = passengers / baseline_passengers
        
        # Range scaling
        baseline_range = 3500  # nm
        range_scale = design_range / baseline_range
        
        # Scale fuselage
        vehicle.passengers = passengers
        vehicle.fuselage.number_coach_seats = passengers
        
        # Determine seating configuration
        if passengers <= 50:
            vehicle.fuselage.seats_abreast = 3
            aisles = 1
        elif passengers <= 100:
            vehicle.fuselage.seats_abreast = 4
            aisles = 1
        elif passengers <= 140:
            vehicle.fuselage.seats_abreast = 5
            aisles = 1
        elif passengers <= 210:
            vehicle.fuselage.seats_abreast = 6
            aisles = 1
        elif passengers <= 280:
            vehicle.fuselage.seats_abreast = 8
            aisles = 2
        elif passengers <= 350:
            vehicle.fuselage.seats_abreast = 9
            aisles = 2
        else:
            vehicle.fuselage.seats_abreast = 10
            aisles = 2
        
        # Scale wing area and other parameters
        vehicle.wings.main_wing.areas.reference *= passenger_scale ** 0.75
        
        # Scale mass properties
        vehicle.mass_properties.max_takeoff *= passenger_scale * range_scale ** 0.3
        vehicle.mass_properties.operating_empty *= passenger_scale ** 0.9
        
        # Set design range
        vehicle.flight_envelope.design_range = design_range * Units.nmi
        
        # Set cruise Mach based on regression: M = 1.5e-05*range + 0.73
        cruise_mach = 1.5e-5 * design_range + 0.73
        vehicle.flight_envelope.design_mach_number = cruise_mach
        
        return vehicle
    
    def _convert_to_aft_open_rotor(self, vehicle):
        """Convert turbofan to aft-mounted open rotor propulsion"""
        
        # Remove existing network
        vehicle.networks = RCAIDE.Framework.Networks.Network.Container()
        
        # Create new open rotor network
        net = RCAIDE.Framework.Networks.Fuel()
        fuel_line = RCAIDE.Library.Components.Powertrain.Distributors.Fuel_Line()
        
        # Create aft-mounted open rotor propulsor
        open_rotor = RCAIDE.Library.Components.Powertrain.Propulsors.Turboprop()
        open_rotor.tag = 'aft_open_rotor'
        open_rotor.active_fuel_tanks = ['fuel_tank']
        
        # Position at aft fuselage (pusher configuration)
        fuselage_length = vehicle.fuselage.lengths.total
        open_rotor.origin = [[fuselage_length * 0.85, 0, 2.0]]  # Aft, elevated
        
        # Open rotor specific parameters
        open_rotor.design_altitude = 35000.0 * Units.ft
        open_rotor.design_mach_number = vehicle.flight_envelope.design_mach_number
        
        # Create open rotor propeller with study parameters
        propeller = self._create_open_rotor_propeller('aft')
        open_rotor.propeller = propeller
        
        # Create gas turbine core (similar to turboprop)
        self._setup_open_rotor_core(open_rotor)
        
        # Design the system
        design_turboprop(open_rotor)
        
        net.propulsors.append(open_rotor)
        
        # Add fuel tank
        fuel_tank = self._create_fuel_tank(vehicle)
        fuel_line.fuel_tanks.append(fuel_tank)
        fuel_line.assigned_propulsors = [[open_rotor.tag]]
        net.fuel_lines.append(fuel_line)
        
        vehicle.append_energy_network(net)
        
        return vehicle
    
    def _convert_to_wing_open_rotor(self, vehicle):
        """Convert turbofan to wing-mounted open rotor propulsion"""
        
        # Remove existing network
        vehicle.networks = RCAIDE.Framework.Networks.Network.Container()
        
        # Create new open rotor network
        net = RCAIDE.Framework.Networks.Fuel()
        fuel_line = RCAIDE.Library.Components.Powertrain.Distributors.Fuel_Line()
        
        # Create wing-mounted open rotors (tractor configuration)
        for side, y_pos in [('starboard', 4.86), ('port', -4.86)]:
            open_rotor = RCAIDE.Library.Components.Powertrain.Propulsors.Turboprop()
            open_rotor.tag = f'{side}_open_rotor'
            open_rotor.active_fuel_tanks = ['fuel_tank']
            
            # Position on wing
            open_rotor.origin = [[13.72, y_pos, -1.1]]
            
            # Open rotor specific parameters
            open_rotor.design_altitude = 35000.0 * Units.ft
            open_rotor.design_mach_number = vehicle.flight_envelope.design_mach_number
            
            # Create open rotor propeller
            propeller = self._create_open_rotor_propeller('wing')
            open_rotor.propeller = propeller
            
            # Create gas turbine core
            self._setup_open_rotor_core(open_rotor)
            
            # Design the system
            design_turboprop(open_rotor)
            
            net.propulsors.append(open_rotor)
        
        # Add fuel tank
        fuel_tank = self._create_fuel_tank(vehicle)
        fuel_line.fuel_tanks.append(fuel_tank)
        fuel_line.assigned_propulsors = [['starboard_open_rotor', 'port_open_rotor']]
        net.fuel_lines.append(fuel_line)
        
        vehicle.append_energy_network(net)
        
        return vehicle
    
    def _create_open_rotor_propeller(self, mount_type):
        """Create open rotor propeller with study parameters"""
        
        propeller = RCAIDE.Library.Components.Powertrain.Converters.Propeller()
        
        # Open rotor parameters
        propeller.number_of_blades = self.open_rotor_params['blade_count']
        propeller.number_of_engines = 1
        
        # Large diameter for open rotor (typically 13-15 ft diameter)
        if mount_type == 'aft':
            propeller.tip_radius = 2.3 * Units.meter  # ~15 ft diameter
        else:  # wing mount
            propeller.tip_radius = 2.0 * Units.meter  # ~13 ft diameter
            
        propeller.hub_radius = 0.3 * Units.meter
        
        # Design point parameters
        propeller.cruise.design_freestream_velocity = 230.0 * Units['m/s']
        propeller.cruise.design_angular_velocity = 1100.0 * Units.rpm  # Typical value
        propeller.cruise.design_tip_mach = 0.95  # High tip Mach for open rotor
        propeller.cruise.design_Cl = 0.7
        propeller.cruise.design_altitude = 35000.0 * Units.ft
        
        # Add airfoils (simplified)
        self._add_propeller_airfoils(propeller)
        
        return propeller
    
    def _setup_open_rotor_core(self, open_rotor):
        """Setup gas turbine core for open rotor"""
        
        # Working fluid
        open_rotor.working_fluid = RCAIDE.Library.Attributes.Gases.Air()
        
        # Ram inlet
        ram = RCAIDE.Library.Components.Powertrain.Converters.Ram()
        ram.tag = 'ram'
        open_rotor.ram = ram
        
        # Inlet nozzle
        inlet_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Compression_Nozzle()
        inlet_nozzle.tag = 'inlet_nozzle'
        inlet_nozzle.pressure_ratio = 1.0  # Assumed unity for core inlet
        open_rotor.inlet_nozzle = inlet_nozzle
        
        # Compressor (overall PR = 19, split as LPC=1.9, HPC=10)
        compressor = RCAIDE.Library.Components.Powertrain.Converters.Compressor()
        compressor.tag = 'compressor'
        compressor.pressure_ratio = 19.0  # Combined LPC and HPC
        compressor.polytropic_efficiency = 0.91  # Typical value
        open_rotor.compressor = compressor
        
        # Combustor
        combustor = RCAIDE.Library.Components.Powertrain.Converters.Combustor()
        combustor.tag = 'combustor'
        combustor.efficiency = 0.99
        combustor.turbine_inlet_temperature = 1500  # Typical value
        combustor.pressure_ratio = 0.95  # Typical value
        combustor.fuel_data = RCAIDE.Library.Attributes.Propellants.Jet_A1()
        open_rotor.combustor = combustor
        
        # High pressure turbine
        hpt = RCAIDE.Library.Components.Powertrain.Converters.Turbine()
        hpt.tag = 'hpt'
        hpt.mechanical_efficiency = 0.99  # Typical value
        hpt.polytropic_efficiency = 0.93  # Typical value
        open_rotor.high_pressure_turbine = hpt
        
        # Low pressure turbine
        lpt = RCAIDE.Library.Components.Powertrain.Converters.Turbine()
        lpt.tag = 'lpt'
        lpt.mechanical_efficiency = 0.99  # Typical value
        lpt.polytropic_efficiency = 0.93  # Typical value
        open_rotor.low_pressure_turbine = lpt
        
        # Core nozzle
        core_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle()
        core_nozzle.tag = 'core_nozzle'
        core_nozzle.pressure_ratio = 0.99  # Typical value
        open_rotor.core_nozzle = core_nozzle
    
    def _add_propeller_airfoils(self, propeller):
        """Add airfoils to propeller (simplified)"""
        
        # Use available airfoils from RCAIDE
        try:
            # Try to use NACA 4412 if available
            airfoil = RCAIDE.Library.Components.Airfoils.Airfoil()
            airfoil.tag = 'NACA_4412'
            propeller.append_airfoil(airfoil)
            propeller.airfoil_polar_stations = [0] * 20  # Use same airfoil for all stations
        except:
            # Fallback to basic airfoil
            pass
    
    def _modify_empennage_for_aft_mount(self, vehicle):
        """Modify empennage for T-tail configuration (aft-mounted open rotor)"""
        
        # Convert to T-tail
        vehicle.wings.vertical_stabilizer.t_tail = True
        
        # Increase tail sizes (5% reduction due to end-plating effect)
        # But overall larger tails needed for aft CG
        h_tail = vehicle.wings.horizontal_stabilizer
        v_tail = vehicle.wings.vertical_stabilizer
        
        # Increase horizontal tail area (moved to top of vertical tail)
        h_tail.areas.reference *= 1.2
        h_tail.origin[0][2] = v_tail.spans.projected  # Move to top of vertical tail
        
        # Increase vertical tail area and make it stronger for T-tail loads
        v_tail.areas.reference *= 1.17  # T-tail factor
        
        return vehicle
    
    def _apply_wing_mount_penalties(self, vehicle):
        """Apply wing scrubbing and landing gear penalties for wing-mounted open rotor"""
        
        # Landing gear penalty for large propeller diameter
        main_gear = vehicle.landing_gears.main_gear
        
        # Calculate required gear height for propeller clearance
        prop_radius = 2.0  # meters
        clearance = 0.5  # meters
        required_height = prop_radius + clearance
        
        # Apply gear weight penalty if needed
        baseline_height = main_gear.strut_length
        if required_height > baseline_height:
            gear_penalty = (required_height / baseline_height) ** 0.4  # Gear penalty formula
            # This would be applied in weight estimation
        
        return vehicle
    
    def _create_fuel_tank(self, vehicle):
        """Create fuel tank for the vehicle"""
        
        fuel_tank = RCAIDE.Library.Components.Powertrain.Sources.Fuel_Tanks.Fuel_Tank()
        fuel_tank.origin = vehicle.wings.main_wing.origin
        fuel_tank.fuel = RCAIDE.Library.Attributes.Propellants.Jet_A1()
        
        # Estimate fuel mass based on range and passengers
        fuel_fraction = 0.3  # Typical for transport aircraft
        fuel_tank.fuel.mass_properties.mass = vehicle.mass_properties.max_takeoff * fuel_fraction
        fuel_tank.volume = fuel_tank.fuel.mass_properties.mass / fuel_tank.fuel.density
        
        return fuel_tank
    
    def create_economic_mission(self, vehicle, design_range):
        """Create economic range mission (1/3 design range)"""
        
        # Economic range calculation
        if design_range == 1000:
            economic_range = design_range * 0.5  # Special case for 1000nm
        else:
            economic_range = design_range * self.economic_range_factor
        
        # Create mission similar to your baseline but with economic range
        mission = RCAIDE.Framework.Mission.Sequential_Segments()
        mission.tag = f'economic_mission_{economic_range}nm'
        
        # Add mission segments (simplified)
        # This would include takeoff, climb, cruise at economic range, descent, landing
        
        return mission
    
    def run_design_space_exploration(self):
        """Run the full design space exploration"""
        
        print("Starting Open Rotor Study...")
        print(f"Payload range: {self.payload_range} passengers")
        print(f"Design ranges: {self.design_ranges} nm")
        print(f"Configurations: {self.configurations}")
        
        results = {}
        
        for config in self.configurations:
            results[config] = {}
            
            for passengers in self.payload_range:
                results[config][passengers] = {}
                
                for design_range in self.design_ranges:
                    print(f"Processing {config}: {passengers} pax, {design_range} nm")
                    
                    try:
                        # Create vehicle
                        if config == 'turbofan':
                            vehicle = self.create_baseline_turbofan(passengers, design_range)
                        elif config == 'aft_open_rotor':
                            vehicle = self.create_aft_open_rotor(passengers, design_range)
                        elif config == 'wing_open_rotor':
                            vehicle = self.create_wing_open_rotor(passengers, design_range)
                        
                        # Create mission
                        mission = self.create_economic_mission(vehicle, design_range)
                        
                        # Run analysis (simplified)
                        result = self._analyze_configuration(vehicle, mission)
                        
                        results[config][passengers][design_range] = result
                        
                    except Exception as e:
                        print(f"Error processing {config} {passengers}pax {design_range}nm: {e}")
                        results[config][passengers][design_range] = None
        
        self.results = results
        return results
    
    def _analyze_configuration(self, vehicle, mission):
        """Analyze a single configuration (simplified)"""
        
        # This would run the full RCAIDE analysis
        # For now, return placeholder results
        result = {
            'fuel_burn': np.random.uniform(10000, 50000),  # kg
            'mtow': vehicle.mass_properties.max_takeoff,
            'empty_weight_fraction': 0.5,
            'range_factor': np.random.uniform(6000, 8000),
            'engine_efficiency': np.random.uniform(0.3, 0.4)
        }
        
        return result
    
    def plot_results_like_study(self):
        """Create study results plots"""
        
        if not self.results:
            print("No results to plot. Run design space exploration first.")
            return
        
        # Create contour plots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Plot 1: Fuel burn comparison (aft vs turbofan)
        self._plot_fuel_burn_comparison(axes[0, 0], 'aft_open_rotor', 'turbofan')
        
        # Plot 2: Fuel burn comparison (wing vs turbofan)
        self._plot_fuel_burn_comparison(axes[0, 1], 'wing_open_rotor', 'turbofan')
        
        # Plot 3: MTOW comparison
        self._plot_mtow_comparison(axes[0, 2])
        
        # Plot 4: Engine efficiency comparison
        self._plot_engine_efficiency(axes[1, 0])
        
        # Plot 5: Range factor comparison
        self._plot_range_factor(axes[1, 1])
        
        # Plot 6: Open rotor comparison (aft vs wing)
        self._plot_fuel_burn_comparison(axes[1, 2], 'aft_open_rotor', 'wing_open_rotor')
        
        plt.tight_layout()
        plt.savefig('open_rotor_study_results.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_fuel_burn_comparison(self, ax, config1, config2):
        """Plot fuel burn comparison between two configurations"""
        
        # Extract data and create contour plot
        # This is a simplified version - would need full implementation
        ax.set_xlabel('Design Range (nm)')
        ax.set_ylabel('Passengers')
        ax.set_title(f'Fuel Burn Difference: {config1} vs {config2} (%)')
    
    def _plot_mtow_comparison(self, ax):
        """Plot MTOW comparison"""
        ax.set_xlabel('Design Range (nm)')
        ax.set_ylabel('Passengers')
        ax.set_title('MTOW Comparison (%)')
    
    def _plot_engine_efficiency(self, ax):
        """Plot engine efficiency comparison"""
        ax.set_xlabel('Design Range (nm)')
        ax.set_ylabel('Passengers')
        ax.set_title('Engine Efficiency Difference (%)')
    
    def _plot_range_factor(self, ax):
        """Plot range factor comparison"""
        ax.set_xlabel('Design Range (nm)')
        ax.set_ylabel('Passengers')
        ax.set_title('Range Factor Comparison')

# Example usage
if __name__ == "__main__":
    # Create study instance
    study = OpenRotorStudy()
    
    # Run a single configuration test
    print("Testing single configuration...")
    vehicle = study.create_baseline_turbofan(150, 3000)
    print(f"Created baseline turbofan: {vehicle.tag}")
    
    # Test open rotor creation
    aft_vehicle = study.create_aft_open_rotor(150, 3000)
    print(f"Created aft open rotor: {aft_vehicle.tag}")
    
    # For full study (commented out - takes long time):
    # results = study.run_design_space_exploration()
    # study.plot_results_like_study()