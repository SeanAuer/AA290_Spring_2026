# Mission Analysis Framework for Open Rotor Study
# Implements mission structure and analysis methodology

import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import RCAIDE
from RCAIDE.Framework.Core import Units

class OpenRotorMissionAnalysis:
    """
    Mission analysis framework for open rotor studies
    
    Key features:
    - Economic range missions (1/3 design range, except 1000nm = 1/2)
    - 200nm reserve + 30min hold
    - Mid-cruise step optimization
    - Constraint analysis (takeoff field length, approach speed, etc.)
    - Performance metrics calculation
    """
    
    def __init__(self):
        self.reserve_range = 200  # nm
        self.hold_time = 30  # minutes
        
        # Constraint regressions
        self.constraint_regressions = {
            'cruise_mach': lambda range_nm: 1.5e-5 * range_nm + 0.73,
            'approach_speed': lambda mtow_lbs: 2.8e-5 * mtow_lbs + 130,  # KCAS
            'takeoff_field_length': {
                'large': lambda mtow_lbs: 0.012 * mtow_lbs + 5600,  # ft
                'small': lambda mtow_lbs: 0.042 * mtow_lbs + 3800   # ft
            }
        }
        
        # Performance metrics
        self.performance_metrics = [
            'max_takeoff_weight',
            'empty_weight_fraction',
            'fuel_fraction',
            'range_factor',  # V * L/D * (1/SFC)
            'engine_efficiency'
        ]
    
    def create_economic_mission(self, vehicle, design_range_nm):
        """
        Create economic range mission
        
        Parameters:
        vehicle: RCAIDE vehicle
        design_range_nm: Design range in nautical miles
        
        Returns:
        mission: RCAIDE mission for economic range
        """
        
        # Calculate economic range
        if design_range_nm == 1000:
            economic_range_nm = 500  # Half of design range for 1000nm case
        else:
            economic_range_nm = design_range_nm / 3  # One third for all others
        
        # Create mission
        mission = RCAIDE.Framework.Mission.Sequential_Segments()
        mission.tag = f'economic_mission_{economic_range_nm:.0f}nm'
        
        # Get design parameters
        cruise_mach = self.constraint_regressions['cruise_mach'](design_range_nm)
        cruise_altitude = self._get_optimal_cruise_altitude(vehicle, economic_range_nm)
        
        # Mission segments
        Segments = RCAIDE.Framework.Mission.Segments
        base_segment = Segments.Segment()
        
        # 1. Takeoff
        segment = self._create_takeoff_segment(base_segment, vehicle)
        mission.append_segment(segment)
        
        # 2. Climb segments (multiple segments)
        climb_segments = self._create_climb_segments(base_segment, vehicle, cruise_altitude)
        for segment in climb_segments:
            mission.append_segment(segment)
        
        # 3. Cruise segment
        segment = self._create_cruise_segment(base_segment, vehicle, 
                                            economic_range_nm, cruise_altitude, cruise_mach)
        mission.append_segment(segment)
        
        # 4. Descent segments
        descent_segments = self._create_descent_segments(base_segment, vehicle, cruise_altitude)
        for segment in descent_segments:
            mission.append_segment(segment)
        
        # 5. Reserve mission (200nm + 30min hold)
        reserve_segments = self._create_reserve_mission(base_segment, vehicle, cruise_altitude)
        for segment in reserve_segments:
            mission.append_segment(segment)
        
        # 6. Landing
        segment = self._create_landing_segment(base_segment, vehicle)
        mission.append_segment(segment)
        
        return mission
    
    def create_design_range_mission(self, vehicle, design_range_nm):
        """Create design range mission for constraint checking"""
        
        mission = RCAIDE.Framework.Mission.Sequential_Segments()
        mission.tag = f'design_mission_{design_range_nm:.0f}nm'
        
        # Similar structure but with full design range
        cruise_mach = self.constraint_regressions['cruise_mach'](design_range_nm)
        cruise_altitude = self._get_optimal_cruise_altitude(vehicle, design_range_nm)
        
        Segments = RCAIDE.Framework.Mission.Segments
        base_segment = Segments.Segment()
        
        # Takeoff
        segment = self._create_takeoff_segment(base_segment, vehicle)
        mission.append_segment(segment)
        
        # Climb
        climb_segments = self._create_climb_segments(base_segment, vehicle, cruise_altitude)
        for segment in climb_segments:
            mission.append_segment(segment)
        
        # Cruise (full design range)
        segment = self._create_cruise_segment(base_segment, vehicle, 
                                            design_range_nm, cruise_altitude, cruise_mach)
        mission.append_segment(segment)
        
        # Descent
        descent_segments = self._create_descent_segments(base_segment, vehicle, cruise_altitude)
        for segment in descent_segments:
            mission.append_segment(segment)
        
        # Reserve
        reserve_segments = self._create_reserve_mission(base_segment, vehicle, cruise_altitude)
        for segment in reserve_segments:
            mission.append_segment(segment)
        
        # Landing
        segment = self._create_landing_segment(base_segment, vehicle)
        mission.append_segment(segment)
        
        return mission
    
    def _create_takeoff_segment(self, base_segment, vehicle):
        """Create takeoff segment"""
        
        Segments = RCAIDE.Framework.Mission.Segments
        segment = Segments.Ground.Takeoff(base_segment)
        segment.tag = "takeoff"
        
        # Takeoff parameters
        segment.velocity_start = 10.0 * Units.knots
        segment.velocity_end = self._get_v2_speed(vehicle)
        segment.friction_coefficient = 0.04
        segment.altitude = 0.0
        
        return segment
    
    def _create_climb_segments(self, base_segment, vehicle, cruise_altitude_ft):
        """Create multiple climb segments"""
        
        Segments = RCAIDE.Framework.Mission.Segments
        segments = []
        
        # Climb 1: 0 - 3km
        segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
        segment.tag = "climb_1"
        segment.altitude_start = 0.0 * Units.km
        segment.altitude_end = 3.0 * Units.km
        segment.air_speed = 125.0 * Units['m/s']
        segment.climb_rate = 6.0 * Units['m/s']
        self._add_flight_controls(segment)
        segments.append(segment)
        
        # Climb 2: 3 - 8km
        segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
        segment.tag = "climb_2"
        segment.altitude_start = 3.0 * Units.km
        segment.altitude_end = 8.0 * Units.km
        segment.air_speed = 190.0 * Units['m/s']
        segment.climb_rate = 6.0 * Units['m/s']
        self._add_flight_controls(segment)
        segments.append(segment)
        
        # Climb 3: 8km - cruise altitude
        segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
        segment.tag = "climb_3"
        segment.altitude_start = 8.0 * Units.km
        segment.altitude_end = cruise_altitude_ft * Units.ft
        segment.air_speed = 226.0 * Units['m/s']
        segment.climb_rate = 3.0 * Units['m/s']
        self._add_flight_controls(segment)
        segments.append(segment)
        
        return segments
    
    def _create_cruise_segment(self, base_segment, vehicle, range_nm, altitude_ft, mach):
        """Create cruise segment"""
        
        Segments = RCAIDE.Framework.Mission.Segments
        segment = Segments.Cruise.Constant_Speed_Constant_Altitude(base_segment)
        segment.tag = "cruise"
        
        segment.altitude = altitude_ft * Units.ft
        segment.mach_number = mach
        segment.distance = range_nm * Units.nmi
        
        self._add_flight_controls(segment)
        
        return segment
    
    def _create_descent_segments(self, base_segment, vehicle, cruise_altitude_ft):
        """Create multiple descent segments"""
        
        Segments = RCAIDE.Framework.Mission.Segments
        segments = []
        
        # Descent 1: cruise - 8km
        segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
        segment.tag = "descent_1"
        segment.altitude_start = cruise_altitude_ft * Units.ft
        segment.altitude_end = 8.0 * Units.km
        segment.air_speed = 220.0 * Units['m/s']
        segment.descent_rate = 4.5 * Units['m/s']
        self._add_flight_controls(segment)
        segments.append(segment)
        
        # Descent 2: 8 - 4km
        segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
        segment.tag = "descent_2"
        segment.altitude_start = 8.0 * Units.km
        segment.altitude_end = 4.0 * Units.km
        segment.air_speed = 195.0 * Units['m/s']
        segment.descent_rate = 5.0 * Units['m/s']
        self._add_flight_controls(segment)
        segments.append(segment)
        
        # Descent 3: 4km - 0
        segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
        segment.tag = "descent_3"
        segment.altitude_start = 4.0 * Units.km
        segment.altitude_end = 0.0 * Units.km
        segment.air_speed = 145.0 * Units['m/s']
        segment.descent_rate = 3.0 * Units['m/s']
        self._add_flight_controls(segment)
        segments.append(segment)
        
        return segments
    
    def _create_reserve_mission(self, base_segment, vehicle, cruise_altitude_ft):
        """Create reserve mission (200nm + 30min hold)"""
        
        Segments = RCAIDE.Framework.Mission.Segments
        segments = []
        
        # Reserve cruise (200nm)
        segment = Segments.Cruise.Constant_Speed_Constant_Altitude(base_segment)
        segment.tag = "reserve_cruise"
        segment.altitude = cruise_altitude_ft * Units.ft
        segment.distance = self.reserve_range * Units.nmi
        segment.air_speed = 230.0 * Units['m/s']  # Typical cruise speed
        self._add_flight_controls(segment)
        segments.append(segment)
        
        # Hold (30 minutes)
        segment = Segments.Cruise.Constant_Speed_Constant_Altitude(base_segment)
        segment.tag = "hold"
        segment.altitude = 5000 * Units.ft  # Typical hold altitude
        segment.time = self.hold_time * Units.minutes
        segment.air_speed = 150.0 * Units['m/s']  # Hold speed
        self._add_flight_controls(segment)
        segments.append(segment)
        
        return segments
    
    def _create_landing_segment(self, base_segment, vehicle):
        """Create landing segment"""
        
        Segments = RCAIDE.Framework.Mission.Segments
        segment = Segments.Ground.Landing(base_segment)
        segment.tag = "landing"
        
        segment.velocity_start = 145.0 * Units['m/s']
        segment.velocity_end = 10.0 * Units.knots
        segment.friction_coefficient = 0.4
        segment.altitude = 0.0
        
        return segment
    
    def _add_flight_controls(self, segment):
        """Add flight controls to segment"""
        
        # Flight dynamics
        segment.flight_dynamics.force_x = True
        segment.flight_dynamics.force_z = True
        
        # Control variables
        segment.assigned_control_variables.throttle.active = True
        segment.assigned_control_variables.body_angle.active = True
        
        # Assign propulsors (generic - would need to be specific to vehicle)
        try:
            # Try to get propulsor names from vehicle
            segment.assigned_control_variables.throttle.assigned_propulsors = [['propulsor_1', 'propulsor_2']]
        except:
            pass
    
    def _get_optimal_cruise_altitude(self, vehicle, range_nm):
        """Get optimal cruise altitude based on range and vehicle"""
        
        # Simplified altitude selection
        if range_nm < 2000:
            return 35000  # ft
        elif range_nm < 4000:
            return 37000  # ft
        else:
            return 39000  # ft
    
    def _get_v2_speed(self, vehicle):
        """Get V2 speed for takeoff"""
        
        # Simplified V2 calculation
        # Would normally be based on stall speed and V2/Vs ratio
        return 125.0 * Units['m/s']
    
    def analyze_constraints(self, vehicle, results):
        """
        Analyze constraints
        
        Returns dictionary of constraint margins and active constraints
        """
        
        constraints = {}
        
        # 1. Takeoff field length constraint
        mtow_lbs = vehicle.mass_properties.max_takeoff / Units.lb
        
        if mtow_lbs < 300000:  # Small aircraft
            required_tofl = self.constraint_regressions['takeoff_field_length']['small'](mtow_lbs)
        else:  # Large aircraft
            required_tofl = self.constraint_regressions['takeoff_field_length']['large'](mtow_lbs)
        
        # Get actual TOFL from results (would need to be calculated)
        actual_tofl = 8000  # ft, placeholder
        
        constraints['takeoff_field_length'] = {
            'required': required_tofl,
            'actual': actual_tofl,
            'margin': (actual_tofl - required_tofl) / required_tofl,
            'active': abs(actual_tofl - required_tofl) < 100  # ft tolerance
        }
        
        # 2. Approach speed constraint
        required_approach_speed = self.constraint_regressions['approach_speed'](mtow_lbs)
        actual_approach_speed = 135  # KCAS, placeholder
        
        constraints['approach_speed'] = {
            'required': required_approach_speed,
            'actual': actual_approach_speed,
            'margin': (required_approach_speed - actual_approach_speed) / required_approach_speed,
            'active': abs(actual_approach_speed - required_approach_speed) < 2  # KCAS tolerance
        }
        
        # 3. Second segment gradient (2.4% minimum)
        constraints['second_segment_gradient'] = {
            'required': 0.024,
            'actual': 0.025,  # placeholder
            'margin': (0.025 - 0.024) / 0.024,
            'active': False
        }
        
        # 4. Top of climb thrust (95% maximum throttle)
        constraints['top_of_climb_thrust'] = {
            'required': 0.95,
            'actual': 0.95,  # placeholder
            'margin': 0.0,
            'active': True  # Often found active
        }
        
        # 5. Fuel volume margin (5% minimum)
        constraints['fuel_volume_margin'] = {
            'required': 0.05,
            'actual': 0.10,  # placeholder
            'margin': (0.10 - 0.05) / 0.05,
            'active': False
        }
        
        # 6. Center of gravity margin (1% MAC)
        constraints['cg_margin'] = {
            'required': 0.01,
            'actual': 0.01,  # placeholder
            'margin': 0.0,
            'active': True
        }
        
        return constraints
    
    def calculate_performance_metrics(self, vehicle, results):
        """
        Calculate performance metrics
        
        Returns dictionary of performance metrics
        """
        
        metrics = {}
        
        # Maximum Takeoff Weight
        metrics['max_takeoff_weight'] = vehicle.mass_properties.max_takeoff
        
        # Empty Weight Fraction
        metrics['empty_weight_fraction'] = (vehicle.mass_properties.operating_empty / 
                                          vehicle.mass_properties.max_takeoff)
        
        # Fuel Fraction (from results)
        fuel_mass = 15000  # kg, placeholder - would get from results
        metrics['fuel_fraction'] = fuel_mass / vehicle.mass_properties.max_takeoff
        
        # Range Factor: V * L/D * (1/SFC)
        # This is the Breguet range equation without the weight term
        cruise_speed = 230.0  # m/s
        lift_to_drag = 17.0   # typical value
        sfc = 0.55           # lbm/lbf-hr, typical
        
        # Convert SFC to SI units (kg/N-s)
        sfc_si = sfc * 0.453592 / (4.44822 * 3600)  # conversion factor
        
        metrics['range_factor'] = cruise_speed * lift_to_drag / sfc_si
        
        # Engine Efficiency (total energy content of fuel to thrust)
        # Simplified calculation
        metrics['engine_efficiency'] = 0.34  # 34%, typical for open rotor
        
        # Additional metrics
        metrics['lift_to_drag_ratio'] = lift_to_drag
        metrics['specific_fuel_consumption'] = sfc
        metrics['cruise_mach'] = 0.78  # typical
        
        return metrics
    
    def compare_configurations(self, baseline_results, open_rotor_results):
        """
        Compare open rotor results to baseline
        
        Returns percentage differences for key metrics
        """
        
        comparison = {}
        
        # Fuel burn comparison (primary metric)
        baseline_fuel = baseline_results.get('fuel_burn', 20000)
        or_fuel = open_rotor_results.get('fuel_burn', 22000)
        comparison['fuel_burn_difference_pct'] = ((or_fuel - baseline_fuel) / baseline_fuel) * 100
        
        # MTOW comparison
        baseline_mtow = baseline_results.get('max_takeoff_weight', 80000)
        or_mtow = open_rotor_results.get('max_takeoff_weight', 85000)
        comparison['mtow_difference_pct'] = ((or_mtow - baseline_mtow) / baseline_mtow) * 100
        
        # Engine efficiency comparison
        baseline_eff = baseline_results.get('engine_efficiency', 0.33)
        or_eff = open_rotor_results.get('engine_efficiency', 0.34)
        comparison['engine_efficiency_difference_pct'] = ((or_eff - baseline_eff) / baseline_eff) * 100
        
        # Range factor comparison
        baseline_rf = baseline_results.get('range_factor', 7000)
        or_rf = open_rotor_results.get('range_factor', 7200)
        comparison['range_factor_difference_pct'] = ((or_rf - baseline_rf) / baseline_rf) * 100
        
        return comparison
    
    def create_study_plots(self, results_database):
        """
        Create contour plots for study results
        
        Parameters:
        results_database: Dictionary with structure [config][passengers][range] = results
        """
        
        # Extract data for plotting
        passengers = sorted(results_database['turbofan'].keys())
        ranges = sorted(results_database['turbofan'][passengers[0]].keys())
        
        # Create meshgrid
        P, R = np.meshgrid(passengers, ranges)
        
        # Create figure with subplots like Dorsey
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Open Rotor Design Space Exploration', fontsize=16)
        
        # Plot 1: Fuel burn difference (Aft vs Turbofan)
        Z1 = self._extract_metric_grid(results_database, 'fuel_burn_difference', 
                                      'aft_open_rotor', 'turbofan', P, R)
        cs1 = axes[0,0].contourf(R, P, Z1, levels=20, cmap='RdYlBu_r')
        axes[0,0].set_title('Fuel Burn Difference: Aft Open Rotor vs Turbofan (%)')
        axes[0,0].set_xlabel('Design Range (nm)')
        axes[0,0].set_ylabel('Passengers')
        plt.colorbar(cs1, ax=axes[0,0])
        
        # Plot 2: Fuel burn difference (Wing vs Turbofan)
        Z2 = self._extract_metric_grid(results_database, 'fuel_burn_difference', 
                                      'wing_open_rotor', 'turbofan', P, R)
        cs2 = axes[0,1].contourf(R, P, Z2, levels=20, cmap='RdYlBu_r')
        axes[0,1].set_title('Fuel Burn Difference: Wing Open Rotor vs Turbofan (%)')
        axes[0,1].set_xlabel('Design Range (nm)')
        axes[0,1].set_ylabel('Passengers')
        plt.colorbar(cs2, ax=axes[0,1])
        
        # Plot 3: MTOW difference
        Z3 = self._extract_metric_grid(results_database, 'mtow_difference', 
                                      'aft_open_rotor', 'turbofan', P, R)
        cs3 = axes[0,2].contourf(R, P, Z3, levels=20, cmap='RdYlBu_r')
        axes[0,2].set_title('MTOW Difference: Aft Open Rotor vs Turbofan (%)')
        axes[0,2].set_xlabel('Design Range (nm)')
        axes[0,2].set_ylabel('Passengers')
        plt.colorbar(cs3, ax=axes[0,2])
        
        # Plot 4: Engine efficiency difference
        Z4 = self._extract_metric_grid(results_database, 'engine_efficiency_difference', 
                                      'aft_open_rotor', 'turbofan', P, R)
        cs4 = axes[1,0].contourf(R, P, Z4, levels=20, cmap='RdBu')
        axes[1,0].set_title('Engine Efficiency Difference: Aft Open Rotor vs Turbofan (%)')
        axes[1,0].set_xlabel('Design Range (nm)')
        axes[1,0].set_ylabel('Passengers')
        plt.colorbar(cs4, ax=axes[1,0])
        
        # Plot 5: Range factor difference
        Z5 = self._extract_metric_grid(results_database, 'range_factor_difference', 
                                      'wing_open_rotor', 'turbofan', P, R)
        cs5 = axes[1,1].contourf(R, P, Z5, levels=20, cmap='RdBu')
        axes[1,1].set_title('Range Factor Difference: Wing Open Rotor vs Turbofan (%)')
        axes[1,1].set_xlabel('Design Range (nm)')
        axes[1,1].set_ylabel('Passengers')
        plt.colorbar(cs5, ax=axes[1,1])
        
        # Plot 6: Open rotor comparison (Aft vs Wing)
        Z6 = self._extract_metric_grid(results_database, 'fuel_burn_difference', 
                                      'aft_open_rotor', 'wing_open_rotor', P, R)
        cs6 = axes[1,2].contourf(R, P, Z6, levels=20, cmap='RdBu')
        axes[1,2].set_title('Fuel Burn Difference: Aft vs Wing Open Rotor (%)')
        axes[1,2].set_xlabel('Design Range (nm)')
        axes[1,2].set_ylabel('Passengers')
        plt.colorbar(cs6, ax=axes[1,2])
        
        plt.tight_layout()
        plt.savefig('open_rotor_study_results.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _extract_metric_grid(self, results_db, metric, config1, config2, P, R):
        """Extract metric data for contour plotting"""
        
        Z = np.zeros_like(P)
        
        for i, passengers in enumerate(P[0,:]):
            for j, range_nm in enumerate(R[:,0]):
                try:
                    result1 = results_db[config1][passengers][range_nm]
                    result2 = results_db[config2][passengers][range_nm]
                    
                    if result1 and result2:
                        if 'difference' in metric:
                            # Calculate percentage difference
                            base_metric = metric.replace('_difference', '')
                            val1 = result1.get(base_metric, 0)
                            val2 = result2.get(base_metric, 0)
                            Z[j,i] = ((val1 - val2) / val2) * 100 if val2 != 0 else 0
                        else:
                            Z[j,i] = result1.get(metric, 0)
                    else:
                        Z[j,i] = np.nan
                        
                except (KeyError, TypeError):
                    Z[j,i] = np.nan
        
        return Z

# Example usage
if __name__ == "__main__":
    
    print("Testing Open Rotor Mission Analysis Framework...")
    
    # Create mission analyzer
    analyzer = OpenRotorMissionAnalysis()
    
    # Test economic range calculation
    for design_range in [1000, 2000, 3000, 4000, 5000, 6000, 7000]:
        if design_range == 1000:
            economic_range = design_range * 0.5
        else:
            economic_range = design_range / 3
        
        cruise_mach = analyzer.constraint_regressions['cruise_mach'](design_range)
        print(f"Design Range: {design_range:4d} nm, Economic Range: {economic_range:6.1f} nm, Cruise Mach: {cruise_mach:.3f}")
    
    # Test constraint analysis
    print("\nTesting constraint analysis...")
    
    # Create dummy vehicle and results
    class DummyVehicle:
        def __init__(self):
            self.mass_properties = type('obj', (object,), {
                'max_takeoff': 80000,  # kg
                'operating_empty': 45000  # kg
            })()
    
    dummy_vehicle = DummyVehicle()
    dummy_results = {}
    
    constraints = analyzer.analyze_constraints(dummy_vehicle, dummy_results)
    
    print("Active constraints:")
    for constraint, data in constraints.items():
        if data['active']:
            print(f"  {constraint}: {data['actual']:.3f} (required: {data['required']:.3f})")
    
    # Test performance metrics
    metrics = analyzer.calculate_performance_metrics(dummy_vehicle, dummy_results)
    print(f"\nPerformance metrics:")
    print(f"  Empty weight fraction: {metrics['empty_weight_fraction']:.3f}")
    print(f"  Range factor: {metrics['range_factor']:.0f}")
    print(f"  Engine efficiency: {metrics['engine_efficiency']:.3f}")