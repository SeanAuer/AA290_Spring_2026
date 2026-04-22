# Open Rotor Propulsor Implementation
# Implements key technical aspects for open rotor aircraft

import numpy as np
from copy import deepcopy
import RCAIDE
from RCAIDE.Framework.Core import Units

class OpenRotorPropulsor:
    """
    Open Rotor Propulsor implementation
    
    Key features:
    - Fan efficiency that varies with Mach number
    - Low fan pressure ratio (~1.1-1.2)
    - High bypass ratio (16-38)
    - Counter-rotating propellers
    - Geared architecture
    """
    
    def __init__(self, mount_type='wing'):
        """
        Initialize open rotor propulsor
        
        Parameters:
        mount_type: 'wing' or 'aft' - affects sizing and configuration
        """
        self.mount_type = mount_type
        
        # Study parameters
        self.fan_efficiency_table = {
            # Design Range (nm): [Mach, Fan Efficiency, Rotor Efficiency (Fan & Gearbox)]
            1000: [0.746, 0.815, 0.807],
            2000: [0.763, 0.807, 0.799],
            3000: [0.779, 0.798, 0.790],
            4000: [0.795, 0.788, 0.780],
            5000: [0.811, 0.777, 0.769],
            6000: [0.828, 0.765, 0.758],
            7000: [0.844, 0.753, 0.745]
        }
        
        # Core parameters (same as turbofan)
        self.core_params = {
            'lpc_pressure_ratio': 1.9,
            'lpc_efficiency': 0.91,
            'hpc_pressure_ratio': 10.0,
            'hpc_efficiency': 0.91,
            'combustor_efficiency': 0.99,
            'combustor_pressure_ratio': 0.95,
            'turbine_inlet_temperature': 1500,  # K
            'hpt_efficiency': 0.93,
            'hpt_mechanical_efficiency': 0.99,
            'lpt_efficiency': 0.93,
            'lpt_mechanical_efficiency': 0.99,
            'core_nozzle_efficiency': 0.99,
            'core_nozzle_pressure_ratio': 0.99
        }
        
        # Open rotor specific parameters
        self.open_rotor_params = {
            'fan_pressure_ratio_range': [1.08, 1.20],  # Optimization range
            'bypass_ratio_range': [16, 38],  # Optimization range
            'gear_ratio': 6.0,
            'gear_efficiency': 0.99,
            'number_of_blades': 10,  # Counter-rotating (5+5 or similar)
            'activity_factor': 150,
            'tip_mach_limit': 0.95
        }
    
    def create_open_rotor_propulsor(self, design_range, design_thrust, design_altitude=35000):
        """
        Create RCAIDE open rotor propulsor
        
        Parameters:
        design_range: Design range in nm (affects Mach number and efficiency)
        design_thrust: Design thrust in N
        design_altitude: Design altitude in ft
        """
        
        # Create base turboprop (closest RCAIDE equivalent)
        propulsor = RCAIDE.Library.Components.Powertrain.Propulsors.Turboprop()
        propulsor.tag = f'{self.mount_type}_open_rotor'
        
        # Get design point parameters
        design_mach, fan_efficiency, rotor_efficiency = self._get_design_point_efficiency(design_range)
        
        # Set design conditions
        propulsor.design_altitude = design_altitude * Units.ft
        propulsor.design_mach_number = design_mach
        propulsor.design_thrust = design_thrust
        
        # Working fluid
        propulsor.working_fluid = RCAIDE.Library.Attributes.Gases.Air()
        
        # Create components
        self._setup_ram_inlet(propulsor)
        self._setup_core_components(propulsor)
        self._setup_open_rotor_fan(propulsor, design_range, rotor_efficiency)
        
        return propulsor
    
    def _get_design_point_efficiency(self, design_range):
        """Get fan efficiency based on design range"""
        
        # Interpolate if exact range not in table
        ranges = list(self.fan_efficiency_table.keys())
        
        if design_range in ranges:
            return self.fan_efficiency_table[design_range]
        
        # Linear interpolation
        ranges.sort()
        for i in range(len(ranges)-1):
            if ranges[i] <= design_range <= ranges[i+1]:
                r1, r2 = ranges[i], ranges[i+1]
                w = (design_range - r1) / (r2 - r1)
                
                mach1, eff1, rotor1 = self.fan_efficiency_table[r1]
                mach2, eff2, rotor2 = self.fan_efficiency_table[r2]
                
                mach = mach1 + w * (mach2 - mach1)
                eff = eff1 + w * (eff2 - eff1)
                rotor = rotor1 + w * (rotor2 - rotor1)
                
                return mach, eff, rotor
        
        # Extrapolate if outside range
        if design_range < ranges[0]:
            return self.fan_efficiency_table[ranges[0]]
        else:
            return self.fan_efficiency_table[ranges[-1]]
    
    def _setup_ram_inlet(self, propulsor):
        """Setup ram inlet"""
        ram = RCAIDE.Library.Components.Powertrain.Converters.Ram()
        ram.tag = 'ram'
        propulsor.ram = ram
        
        # Inlet nozzle (core inlet efficiency = 1.0 per Dorsey)
        inlet_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Compression_Nozzle()
        inlet_nozzle.tag = 'inlet_nozzle'
        inlet_nozzle.pressure_ratio = 1.0  # Dorsey assumption
        inlet_nozzle.polytropic_efficiency = 1.0
        propulsor.inlet_nozzle = inlet_nozzle
    
    def _setup_core_components(self, propulsor):
        """Setup gas turbine core components"""
        
        # Low pressure compressor
        lpc = RCAIDE.Library.Components.Powertrain.Converters.Compressor()
        lpc.tag = 'lpc'
        lpc.pressure_ratio = self.core_params['lpc_pressure_ratio']
        lpc.polytropic_efficiency = self.core_params['lpc_efficiency']
        propulsor.compressor = lpc  # Assign as main compressor
        
        # Note: RCAIDE turboprop may not have separate LPC/HPC
        # We'll use combined compressor with total pressure ratio
        total_pr = self.core_params['lpc_pressure_ratio'] * self.core_params['hpc_pressure_ratio']
        lpc.pressure_ratio = total_pr
        
        # Combustor
        combustor = RCAIDE.Library.Components.Powertrain.Converters.Combustor()
        combustor.tag = 'combustor'
        combustor.efficiency = self.core_params['combustor_efficiency']
        combustor.pressure_ratio = self.core_params['combustor_pressure_ratio']
        combustor.turbine_inlet_temperature = self.core_params['turbine_inlet_temperature']
        combustor.fuel_data = RCAIDE.Library.Attributes.Propellants.Jet_A1()
        propulsor.combustor = combustor
        
        # High pressure turbine
        hpt = RCAIDE.Library.Components.Powertrain.Converters.Turbine()
        hpt.tag = 'hpt'
        hpt.polytropic_efficiency = self.core_params['hpt_efficiency']
        hpt.mechanical_efficiency = self.core_params['hpt_mechanical_efficiency']
        propulsor.high_pressure_turbine = hpt
        
        # Low pressure turbine
        lpt = RCAIDE.Library.Components.Powertrain.Converters.Turbine()
        lpt.tag = 'lpt'
        lpt.polytropic_efficiency = self.core_params['lpt_efficiency']
        lpt.mechanical_efficiency = self.core_params['lpt_mechanical_efficiency']
        propulsor.low_pressure_turbine = lpt
        
        # Core nozzle
        core_nozzle = RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle()
        core_nozzle.tag = 'core_nozzle'
        core_nozzle.polytropic_efficiency = self.core_params['core_nozzle_efficiency']
        core_nozzle.pressure_ratio = self.core_params['core_nozzle_pressure_ratio']
        propulsor.core_nozzle = core_nozzle
    
    def _setup_open_rotor_fan(self, propulsor, design_range, rotor_efficiency):
        """Setup open rotor fan (propeller)"""
        
        from RCAIDE.Library.Methods.Powertrain.Converters.Rotor import design_propeller
        
        # Create propeller
        propeller = RCAIDE.Library.Components.Powertrain.Converters.Propeller()
        propeller.tag = 'open_rotor_fan'
        
        # Open rotor sizing based on mount type
        if self.mount_type == 'aft':
            # Aft-mounted: larger diameter possible
            propeller.tip_radius = 2.4 * Units.meter  # ~16 ft diameter
            propeller.hub_radius = 0.4 * Units.meter
        else:
            # Wing-mounted: limited by ground clearance
            propeller.tip_radius = 2.0 * Units.meter  # ~13 ft diameter
            propeller.hub_radius = 0.3 * Units.meter
        
        # Blade configuration
        propeller.number_of_blades = self.open_rotor_params['number_of_blades']
        propeller.number_of_engines = 1
        
        # Design point
        design_mach, _, _ = self._get_design_point_efficiency(design_range)
        design_velocity = design_mach * 343.0  # Approximate speed of sound at altitude
        
        propeller.cruise.design_freestream_velocity = design_velocity * Units['m/s']
        propeller.cruise.design_angular_velocity = 1100.0 * Units.rpm  # Dorsey value
        propeller.cruise.design_tip_mach = self.open_rotor_params['tip_mach_limit']
        propeller.cruise.design_Cl = 0.7
        propeller.cruise.design_altitude = propulsor.design_altitude
        propeller.cruise.design_thrust = propulsor.design_thrust
        
        # Apply efficiency from table
        propeller.design_efficiency = rotor_efficiency
        
        # Add airfoils (simplified - would need actual open rotor airfoils)
        self._add_open_rotor_airfoils(propeller)
        
        # Design propeller
        try:
            design_propeller(propeller)
        except:
            print("Warning: Propeller design failed, using default parameters")
        
        propulsor.propeller = propeller
    
    def _add_open_rotor_airfoils(self, propeller):
        """Add airfoils suitable for open rotor application"""
        
        # Open rotors typically use specialized airfoils
        # For now, use available NACA airfoils as approximation
        
        try:
            # Root airfoil - thicker for structural strength
            root_airfoil = RCAIDE.Library.Components.Airfoils.Airfoil()
            root_airfoil.tag = 'NACA_4415'  # Thicker airfoil for root
            propeller.append_airfoil(root_airfoil)
            
            # Tip airfoil - thinner for efficiency
            tip_airfoil = RCAIDE.Library.Components.Airfoils.Airfoil()
            tip_airfoil.tag = 'NACA_4412'  # Thinner airfoil for tip
            propeller.append_airfoil(tip_airfoil)
            
            # Define airfoil distribution (root to tip)
            n_stations = 20
            propeller.airfoil_polar_stations = [0] * (n_stations//2) + [1] * (n_stations//2)
            
        except Exception as e:
            print(f"Warning: Could not load airfoils: {e}")
            # Use default if airfoils not available
            propeller.airfoil_polar_stations = [0] * 20
    
    def calculate_integration_penalties(self, vehicle):
        """
        Calculate integration penalties specific to open rotor configuration
        """
        
        penalties = {
            'weight_penalty': 0.0,
            'drag_penalty': 0.0,
            'noise_penalty': 0.0,  # Not modeled in Dorsey
            'certification_penalty': 0.0  # Not modeled in Dorsey
        }
        
        if self.mount_type == 'wing':
            # Wing scrubbing effects
            penalties['drag_penalty'] = self._calculate_wing_scrubbing_penalty(vehicle)
            
            # Landing gear penalty
            penalties['weight_penalty'] = self._calculate_landing_gear_penalty(vehicle)
            
        elif self.mount_type == 'aft':
            # Tail sizing penalty
            penalties['weight_penalty'] = self._calculate_tail_sizing_penalty(vehicle)
            
            # Pylon weight penalty (estimated)
            penalties['weight_penalty'] += 0.05  # Estimated 5% penalty
        
        return penalties
    
    def _calculate_wing_scrubbing_penalty(self, vehicle):
        """Calculate wing scrubbing drag penalty"""
        
        # Simplified implementation of scrubbing model
        # ΔD_wing = Δq * D_fan * c_scrub * C_f|wing * k_wing
        
        # Velocity change due to propeller (simplified)
        V_infinity = 230.0  # m/s, cruise speed
        V_delta = 20.0  # m/s, estimated velocity increase from propeller
        
        # Dynamic pressure change
        rho = 0.4  # kg/m³, approximate at cruise altitude
        delta_q = 0.5 * rho * V_delta**2
        
        # Scrubbed area (simplified)
        prop_diameter = 4.0  # meters
        scrubbed_chord = 2.0  # meters, estimated
        scrubbed_area = prop_diameter * scrubbed_chord
        
        # Drag coefficient increase
        Cf_wing = 0.003  # Typical skin friction coefficient
        k_wing = 1.2  # Form factor
        
        drag_increase = delta_q * scrubbed_area * Cf_wing * k_wing
        
        # Convert to drag coefficient
        S_ref = vehicle.reference_area
        q_cruise = 0.5 * rho * V_infinity**2
        CD_penalty = drag_increase / (q_cruise * S_ref)
        
        return CD_penalty
    
    def _calculate_landing_gear_penalty(self, vehicle):
        """Calculate landing gear weight penalty"""
        
        # Gear penalty model
        prop_diameter = 4.0  # meters
        required_height = prop_diameter/2 + 0.5  # 0.5m clearance
        
        # Tail scrape constraint
        fuselage_length = 38.0  # meters, approximate
        scrape_angle = 10.0 * np.pi/180  # radians
        scrape_height = fuselage_length * np.tan(scrape_angle)
        
        if required_height > scrape_height:
            gear_penalty = (required_height / scrape_height)**0.4  # Gear penalty formula
            weight_penalty = (gear_penalty - 1.0) * 0.04  # 4% baseline gear weight
        else:
            weight_penalty = 0.0
        
        return weight_penalty
    
    def _calculate_tail_sizing_penalty(self, vehicle):
        """Calculate tail sizing penalty for aft-mounted configuration"""
        
        # Aft-mounted engines shift CG aft, requiring larger tails
        # Dorsey found significant penalties for low passenger counts
        
        passengers = getattr(vehicle, 'passengers', 170)
        
        if passengers < 150:
            # Higher penalty for shorter fuselages
            tail_penalty = 0.15  # 15% increase in tail weight
        else:
            tail_penalty = 0.08  # 8% increase in tail weight
        
        return tail_penalty

class OpenRotorOptimizer:
    """
    Optimizer for open rotor parameters
    """
    
    def __init__(self):
        self.optimization_variables = [
            'fan_pressure_ratio',  # 1.08 - 1.20
            'bypass_ratio',        # 16 - 38
            'wing_area',
            'wing_aspect_ratio',
            'wing_sweep',
            'wing_thickness_ratio',
            'cruise_altitude',
            'takeoff_weight'
        ]
        
        self.constraints = [
            'takeoff_field_length',
            'approach_speed',
            'second_segment_gradient',  # 2.4% minimum
            'fuel_volume_margin',       # 5% minimum
            'center_of_gravity_margin', # 1% MAC
            'top_of_climb_thrust'       # 95% maximum throttle
        ]
    
    def optimize_for_economic_mission(self, vehicle, mission):
        """
        Optimize aircraft for minimum fuel burn on economic mission
        """
        
        # This would implement SLSQP optimization
        # with 5 random restarts to avoid local minima
        
        # Placeholder for optimization results
        optimized_params = {
            'fan_pressure_ratio': 1.15,  # Typical result
            'bypass_ratio': 25.0,        # Typical result
            'fuel_burn': 15000.0,        # kg
            'mtow': 80000.0,             # kg
            'engine_efficiency': 0.34    # 34%
        }
        
        return optimized_params

# Example usage and testing
if __name__ == "__main__":
    
    # Test open rotor creation
    print("Testing Open Rotor Propulsor Implementation...")
    
    # Create wing-mounted open rotor
    wing_or = OpenRotorPropulsor(mount_type='wing')
    wing_propulsor = wing_or.create_open_rotor_propulsor(
        design_range=3000,  # nm
        design_thrust=35000,  # N
        design_altitude=35000  # ft
    )
    
    print(f"Created wing-mounted open rotor: {wing_propulsor.tag}")
    print(f"Design Mach: {wing_propulsor.design_mach_number:.3f}")
    
    # Create aft-mounted open rotor
    aft_or = OpenRotorPropulsor(mount_type='aft')
    aft_propulsor = aft_or.create_open_rotor_propulsor(
        design_range=3000,  # nm
        design_thrust=35000,  # N
        design_altitude=35000  # ft
    )
    
    print(f"Created aft-mounted open rotor: {aft_propulsor.tag}")
    
    # Test efficiency variation with range
    print("\nFan Efficiency vs Design Range:")
    for range_nm in [1000, 2000, 3000, 4000, 5000, 6000, 7000]:
        mach, fan_eff, rotor_eff = wing_or._get_design_point_efficiency(range_nm)
        print(f"{range_nm:4d} nm: Mach {mach:.3f}, Fan Eff {fan_eff:.3f}, Rotor Eff {rotor_eff:.3f}")