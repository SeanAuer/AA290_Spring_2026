# Open Rotor Aircraft Design Framework Overview

This document explains the structure and functionality of the `airplane_design/` directory, which contains a comprehensive framework for open rotor aircraft design space exploration using RCAIDE-LEADS.

## Directory Structure

```
airplane_design/
├── mission_simulation/
│   ├── simple_open_rotor.py          # Simplified open rotor aircraft
│   ├── open_rotor_airplane.py        # Full open rotor aircraft with detailed modeling
│   └── B737*.txt                     # Airfoil coordinate files
├── open_rotor_propulsor.py           # Open rotor propulsion system implementation
├── open_rotor_study_framework.py     # Main design space exploration framework
├── open_rotor_mission_analysis.py    # Mission analysis and performance evaluation
├── run_open_rotor_comparison.py      # Integration script and demonstration
└── README.md                         # Framework documentation
```

## Component Overview

### 1. Simple Open Rotor (`mission_simulation/simple_open_rotor.py`)

**Purpose**: Minimal working version of an open rotor aircraft for initial testing and development.

**Key Features**:
- Based on Boeing 737-800 geometry
- Simplified propulsion system without detailed open rotor modeling
- Basic RCAIDE vehicle setup with wings, fuselage, and energy network
- Placeholder for open rotor propulsion development

**Usage**: Starting point for understanding RCAIDE vehicle structure and testing basic functionality.

```python
# Creates a simplified open rotor aircraft
vehicle = vehicle_setup()    # Boeing 737-800 based geometry
configs = configs_setup(vehicle)  # Flight configurations
analyses = analyses_setup(configs)  # Analysis setup
```

### 2. Full Open Rotor Aircraft (`mission_simulation/open_rotor_airplane.py`)

**Purpose**: Complete open rotor aircraft implementation with detailed propulsion modeling.

**Key Features**:
- **Detailed Geometry**: Full Boeing 737-800 geometry with multiple wing segments, detailed fuselage segments, horizontal/vertical stabilizers
- **Landing Gear**: Main and nose gear with proper sizing
- **Open Rotor Propulsion**: Twin open rotor propulsors using RCAIDE turboprop framework
- **Large Diameter Propellers**: 5-meter diameter (2.5m radius) open rotors with 8 blades
- **Complete Mission Capability**: Full mission segments from takeoff to landing
- **Control Surfaces**: Flaps, slats, ailerons, elevators with deflection schedules

**Technical Specifications**:
- Propeller diameter: ~16 ft (5m)
- Blade count: 8 per rotor
- RPM: 1100-2000 depending on flight phase
- Gas turbine core with realistic pressure ratios and efficiencies

**Usage**: Foundation for detailed open rotor performance analysis and mission simulation.

### 3. Open Rotor Propulsor (`open_rotor_propulsor.py`)

**Purpose**: Specialized implementation of open rotor propulsion characteristics and integration effects.

**Core Functionality**:

#### Fan Efficiency Modeling
- **Mach Number Dependency**: Fan efficiency decreases with increasing cruise Mach number
- **Design Range Table**: Efficiency values for 1000-7000 nm design ranges
- **Key Finding**: Efficiency degradation with Mach is the primary performance driver

```python
# Fan efficiency varies with design range (and thus cruise Mach)
fan_efficiency_table = {
    1000: [0.746, 0.815, 0.807],  # [Mach, Fan Eff, Rotor Eff]
    3000: [0.779, 0.798, 0.790],
    7000: [0.844, 0.753, 0.745]   # Higher Mach = Lower efficiency
}
```

#### Open Rotor Parameters
- **Low Fan Pressure Ratio**: 1.08-1.20 (vs 1.5-1.7 for turbofans)
- **High Bypass Ratio**: 16-38 (vs 5-12 for turbofans)
- **Counter-Rotating Architecture**: 10 blades total (5+5 configuration)
- **Geared System**: 6:1 gear ratio with 99% efficiency

#### Integration Penalties
- **Wing-Mounted**: Scrubbing drag, landing gear height penalties
- **Aft-Mounted**: Tail sizing penalties, T-tail configuration required

**Usage**: Provides realistic open rotor performance characteristics for design studies.

### 4. Study Framework (`open_rotor_study_framework.py`)

**Purpose**: Main framework for comprehensive design space exploration.

**Design Space Coverage**:
- **Passengers**: 50-400 in 50-passenger increments (8 points)
- **Design Range**: 1000-7000 nm in 1000 nm increments (7 points)
- **Configurations**: 3 types (Turbofan baseline, Aft open rotor, Wing open rotor)
- **Total**: 168 design points (8 × 7 × 3)

**Key Capabilities**:

#### Aircraft Scaling
- **Passenger Scaling**: Step-wise regression for fuselage sizing
- **Seating Configuration**: Automatic determination of seats abreast and aisles
- **Mass Scaling**: Wing area and mass properties scale with passenger count and range
- **Cruise Mach**: Regression-based Mach number selection (M = 1.5e-05×range + 0.73)

#### Configuration Creation
```python
# Three main aircraft configurations
turbofan = study.create_baseline_turbofan(passengers, design_range)
aft_or = study.create_aft_open_rotor(passengers, design_range)
wing_or = study.create_wing_open_rotor(passengers, design_range)
```

#### Open Rotor Modifications
- **Aft-Mounted**: T-tail configuration, pusher propellers, tail sizing penalties
- **Wing-Mounted**: Tractor propellers, scrubbing effects, landing gear penalties

**Usage**: Orchestrates the complete design space exploration study.

### 5. Mission Analysis (`open_rotor_mission_analysis.py`)

**Purpose**: Mission structure and performance evaluation framework.

**Mission Types**:

#### Economic Range Mission
- **Range Calculation**: 1/3 design range (except 1000nm = 1/2)
- **Optimization Objective**: Minimum fuel burn on economic mission
- **Reserve Requirements**: 200nm + 30min hold

#### Design Range Mission
- **Full Range**: Complete design range capability
- **Constraint Checking**: Takeoff field length, approach speed, climb gradient

**Mission Segments**:
1. **Takeoff**: Ground roll with friction modeling
2. **Climb**: Multi-segment climb (0-3km, 3-8km, 8km-cruise)
3. **Cruise**: Constant speed/altitude at economic range
4. **Descent**: Multi-segment descent to landing
5. **Reserve**: 200nm cruise + 30min hold
6. **Landing**: Ground roll with reverse thrust

**Constraint Analysis**:
- **Takeoff Field Length**: Regression-based requirements
- **Approach Speed**: MTOW-dependent limits
- **Second Segment Gradient**: 2.4% minimum
- **Top of Climb Thrust**: 95% maximum throttle
- **Fuel Volume Margin**: 5% minimum
- **Center of Gravity**: 1% MAC margin

**Performance Metrics**:
- Maximum takeoff weight
- Empty weight fraction
- Fuel fraction
- Range factor (V × L/D × 1/SFC)
- Engine efficiency

**Usage**: Provides mission analysis capability and constraint checking for optimization.

### 6. Integration Script (`run_open_rotor_comparison.py`)

**Purpose**: Demonstration script showing how all components work together.

**Functionality**:

#### Single Point Analysis
- Creates all three aircraft configurations
- Demonstrates open rotor characteristics
- Shows fan efficiency variation with Mach number
- Simulates performance analysis results

#### Design Space Visualization
- Creates contour plots showing fuel burn penalties
- Identifies promising regions for open rotors
- Shows design space classification

#### Study Results Simulation
- Simulates realistic performance trends
- Shows fuel burn penalties (typically 8-25% worse than turbofan)
- Demonstrates regional effects (short range + high passengers = best for OR)

**Key Findings Demonstrated**:
- Open rotors best suited for SHORT RANGE + LARGE PASSENGER COUNT
- Aft-mounted outperforms wing-mounted across design space
- Fan efficiency decrease with Mach number is largest performance driver
- Open rotor configurations often show fuel burn penalty vs turbofan

**Usage**: Entry point for understanding the complete framework and running demonstrations.

## How the Components Work Together

### 1. Framework Integration Flow

```
run_open_rotor_comparison.py
    ↓
OpenRotorStudy.create_*_aircraft()
    ↓
OpenRotorPropulsor.create_open_rotor_propulsor()
    ↓
OpenRotorMissionAnalysis.create_economic_mission()
    ↓
RCAIDE Analysis & Optimization
    ↓
Results Processing & Visualization
```

### 2. Data Flow

1. **Input Parameters**: Passenger count, design range
2. **Aircraft Creation**: Scaled geometry, propulsion system
3. **Mission Definition**: Economic range mission with reserves
4. **Analysis**: RCAIDE simulation (or simulated results)
5. **Performance Metrics**: Fuel burn, MTOW, efficiency
6. **Comparison**: Percentage differences vs baseline

### 3. Key Technical Relationships

#### Open Rotor Performance Drivers
- **Cruise Mach → Fan Efficiency**: Higher Mach = Lower efficiency
- **Design Range → Cruise Mach**: Longer range = Higher Mach
- **Passenger Count → Mission Profile**: More passengers = More climb-dominated

#### Integration Effects
- **Wing-Mounted**: Scrubbing drag + landing gear penalties
- **Aft-Mounted**: T-tail benefits - tail sizing penalties
- **Both**: Lower fan pressure ratio + higher bypass ratio

#### Optimization Constraints
- **Active Constraints**: Often top-of-climb thrust and CG margin
- **Design Drivers**: Takeoff field length, approach speed
- **Mission Optimization**: Economic range fuel burn minimization

## Usage Examples

### Basic Single Configuration
```python
from open_rotor_study_framework import OpenRotorStudy

study = OpenRotorStudy()
vehicle = study.create_aft_open_rotor(passengers=200, design_range=3000)
```

### Full Design Space Exploration
```python
results = study.run_design_space_exploration()
study.plot_results_like_study()
```

### Mission Analysis
```python
from open_rotor_mission_analysis import OpenRotorMissionAnalysis

analyzer = OpenRotorMissionAnalysis()
mission = analyzer.create_economic_mission(vehicle, design_range=3000)
constraints = analyzer.analyze_constraints(vehicle, results)
```

### Propulsor Characteristics
```python
from open_rotor_propulsor import OpenRotorPropulsor

or_prop = OpenRotorPropulsor(mount_type='aft')
propulsor = or_prop.create_open_rotor_propulsor(
    design_range=3000, 
    design_thrust=35000
)
```

## Key Study Insights

### Design Space Regions
- **Most Promising**: 300+ passengers, ≤2000nm range
- **Least Promising**: ≤150 passengers, ≥5000nm range
- **Reason**: Short range → Low Mach → High fan efficiency

### Performance Trends
- **Fuel Burn**: Open rotors typically 8-25% penalty vs turbofan
- **MTOW**: Higher due to integration penalties
- **Engine Efficiency**: Higher core efficiency but system penalties
- **Configuration**: Aft-mounted consistently outperforms wing-mounted

### Technical Drivers
1. **Fan efficiency degradation with Mach number** (primary)
2. **Integration penalties** (secondary)
3. **Mission profile effects** (climb vs cruise dominated)
4. **Constraint activity** (top-of-climb thrust sizing)

This framework provides a complete methodology for open rotor aircraft design space exploration, from individual component modeling to full system optimization and comparison.