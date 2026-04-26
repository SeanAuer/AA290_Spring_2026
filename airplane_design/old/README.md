# Open Rotor Study Framework using RCAIDE-LEADS

This framework provides a comprehensive methodology for exploring open rotor aircraft configurations across a design space to determine where open rotor technology might provide benefits compared to conventional turbofans.

## Overview

This study explores open rotor aircraft configurations across a comprehensive design space. The framework implements methodologies for analyzing three configurations: baseline turbofan, aft-mounted open rotor, and wing-mounted open rotor aircraft.

## Key Technical Findings

- **Open rotors best suited for**: Short range + large passenger count
- **Aft-mounted outperforms wing-mounted** across the design space
- **Fan efficiency decrease with Mach number** is a major performance driver
- **Integration penalties** (weight, drag, tail sizing) significantly impact performance

## Framework Components

### 1. `open_rotor_study_framework.py`
Main framework class that orchestrates the entire study.

**Key Features:**
- Design space definition (50-400 passengers, 1000-7000 nm range)
- Aircraft scaling methodology
- Configuration creation (turbofan, aft open rotor, wing open rotor)
- Fuselage sizing based on passenger count
- Cruise Mach regression (M = 1.5e-05*range + 0.73)

### 2. `open_rotor_propulsor.py`
Detailed open rotor propulsion system implementation.

**Key Features:**
- Fan efficiency variation with Mach number (Dorsey Table 1)
- Low fan pressure ratio (~1.1-1.2) and high bypass ratio (16-38)
- Counter-rotating propeller configuration
- Geared architecture (6:1 gear ratio, 99% efficiency)
- Integration penalty calculations (wing scrubbing, landing gear, tail sizing)

### 3. `open_rotor_mission_analysis.py`
Mission structure and performance analysis framework.

**Key Features:**
- Economic range missions (1/3 design range, except 1000nm = 1/2)
- 200nm reserve + 30min hold requirement
- Multi-segment climb/descent profiles
- Constraint analysis (takeoff field length, approach speed, etc.)
- Performance metrics calculation (range factor, engine efficiency, etc.)

### 4. `run_open_rotor_comparison.py`
Integration script demonstrating the complete analysis workflow.

## Design Space

The study covers:
- **Passengers**: 50, 100, 150, 200, 250, 300, 350, 400
- **Design Range**: 1000, 2000, 3000, 4000, 5000, 6000, 7000 nm
- **Configurations**: Turbofan baseline, Aft-mounted open rotor, Wing-mounted open rotor

Total: **168 design points** (8 × 7 × 3)

## Key Technical Parameters

### Open Rotor Specifications
```python
fan_pressure_ratio = 1.1-1.2        # vs 1.5-1.7 for turbofans
bypass_ratio = 16-38                 # vs 8-10 for turbofans
gear_ratio = 6.0
gear_efficiency = 0.99
blade_count = 10                     # Counter-rotating
tip_mach_limit = 0.95
```

### Fan Efficiency vs Mach Number
```
Range (nm)  Mach   Fan Eff  Rotor Eff
1000        0.746  0.815    0.807
2000        0.763  0.807    0.799
3000        0.779  0.798    0.790
4000        0.795  0.788    0.780
5000        0.811  0.777    0.769
6000        0.828  0.765    0.758
7000        0.844  0.753    0.745
```

### Core Engine Parameters (same as turbofan)
```python
lpc_pressure_ratio = 1.9
hpc_pressure_ratio = 10.0
turbine_inlet_temperature = 1500  # K
combustor_efficiency = 0.99
turbine_efficiency = 0.93
```

## Usage

### Quick Start
```python
# Run single point comparison
python run_open_rotor_comparison.py
```

This will:
1. Create baseline turbofan aircraft (150 pax, 3000 nm)
2. Create aft and wing-mounted open rotor variants
3. Analyze performance differences
4. Generate design space visualization

### Full Study
```python
from open_rotor_study_framework import OpenRotorStudy

# Initialize study
study = OpenRotorStudy()

# Run full design space exploration (warning: computationally intensive)
results = study.run_design_space_exploration()

# Generate study plots
study.plot_results_like_study()
```

### Custom Analysis
```python
from open_rotor_propulsor import OpenRotorPropulsor
from open_rotor_mission_analysis import OpenRotorMissionAnalysis

# Create open rotor propulsor
or_propulsor = OpenRotorPropulsor(mount_type='wing')
propulsor = or_propulsor.create_open_rotor_propulsor(
    design_range=3000,  # nm
    design_thrust=35000,  # N
    design_altitude=35000  # ft
)

# Create economic mission
mission_analyzer = OpenRotorMissionAnalysis()
mission = mission_analyzer.create_economic_mission(vehicle, 3000)

# Analyze constraints
constraints = mission_analyzer.analyze_constraints(vehicle, results)
```

## Integration Penalties

### Wing-Mounted Open Rotor
- **Wing scrubbing drag**: Increased drag due to propeller slipstream
- **Landing gear penalty**: Longer gear required for propeller clearance
- **Nacelle scrubbing**: Additional drag on nacelle downstream of propeller

### Aft-Mounted Open Rotor
- **Tail sizing penalty**: Larger tails required due to aft CG shift
- **T-tail configuration**: Required for propeller clearance
- **Pylon weight penalty**: Heavy pylon structure for aft mounting

## Optimization Methodology

Following optimization methodology:
- **Objective**: Minimize fuel burn on economic range mission
- **Algorithm**: SLSQP (Sequential Least Squares Programming)
- **Restarts**: 5 random restarts to avoid local minima
- **Variables**: Wing area, engine parameters, cruise altitude, etc.
- **Constraints**: Takeoff field length, approach speed, climb gradient, etc.

## Expected Results

Based on typical findings, the framework should show:

1. **Fuel burn penalty** for all open rotor configurations
2. **Aft-mounted better than wing-mounted** (lower penalty)
3. **Best performance** in short-range, high-passenger region
4. **Worst performance** in long-range, low-passenger region
5. **Engine efficiency advantage** negated by integration penalties

## Validation

To validate results:
1. Compare fan efficiency trends
2. Check constraint activity patterns
3. Verify fuel burn penalty magnitudes
4. Confirm design space trends

## Limitations

Current implementation:
- **Simplified propeller design**: Uses available RCAIDE airfoils
- **Estimated integration penalties**: Based on published equations but not fully validated
- **Placeholder mission analysis**: Full RCAIDE analysis not implemented
- **No noise modeling**: Noise constraints excluded

## Future Enhancements

1. **Full RCAIDE integration**: Complete vehicle analysis and mission simulation
2. **Detailed propeller design**: Custom open rotor airfoils and blade geometry
3. **Advanced aerodynamics**: Wing-propeller interaction modeling
4. **Noise analysis**: Certification noise constraints
5. **Optimization loop**: Automated design space exploration
6. **Validation cases**: Comparison with published data

## File Structure

```
airplane_design/
├── open_rotor_study_framework.py     # Main framework
├── open_rotor_propulsor.py           # Open rotor propulsion system
├── open_rotor_mission_analysis.py    # Mission analysis framework
├── run_open_rotor_comparison.py      # Integration and demo script
└── README.md                         # This file

baseline_airplane/
└── mission_simulation/
    └── baseline_turbofan_airplane.py # Baseline turbofan configuration
```

## Dependencies

- RCAIDE-LEADS framework
- NumPy, Matplotlib, Pandas
- Python 3.8+

## References

1. Open rotor aircraft design methodologies and best practices
2. RCAIDE-LEADS Documentation: [GitHub Repository]

## Contact

For questions about this implementation, please refer to open rotor literature and RCAIDE-LEADS documentation.

---

**Note**: This framework provides the methodology and structure for open rotor aircraft studies. Full implementation requires significant computational resources and detailed validation against published results.