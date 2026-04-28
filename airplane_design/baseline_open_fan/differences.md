# Configuration Differences: Baseline Turbofan vs Open Fan Aircraft

## Parameter Comparison Table

| Parameter | Baseline Turbofan | Open Fan | Change Description |
|-----------|------------------|----------|-------------------|
| **Function Signature** | `vehicle_setup()` | `vehicle_setup(fan_pressure_ratio=1.10, bypass_ratio=25)` | Added parametric inputs |
| **Import Statement** | `design_turbofan` | `design_turboprop` | Changed design function |
| **Propulsor Class** | `Turbofan()` | `Turboprop()` | Changed propulsion architecture |
| **Bypass Ratio** | 5.4 (fixed) | 25 (parametric) | Increased for open rotor concept |
| **Fan Component** | Separate Fan() component | Integrated propeller efficiency | Removed ducted fan |
| **Fan Pressure Ratio** | 1.7 (fixed) | 1.10 (parametric) | Reduced for open rotor |
| **Propeller Efficiency** | N/A | Mach-dependent (0.745-0.807) | Added Dorsey Table 1 data |
| **Gearbox Efficiency** | N/A | 0.99 | Added for open rotor |
| **LPC Pressure Ratio** | 1.9 | fan_pressure_ratio (1.10) | Simplified to single stage |
| **HPC Pressure Ratio** | 10.0 | Removed | Eliminated high pressure compressor |
| **Compressor Architecture** | LPC + HPC | Single compressor | Simplified core |
| **Fan Nozzle** | Present | Removed | No bypass duct |
| **Nacelle Diameter** | 2.05 m | 1.5 m | Smaller core-only nacelle |
| **Nacelle Type** | `Body_of_Revolution_Nacelle` | `Stack_Nacelle` | Simplified nacelle |
| **Nacelle Wetted Area** | 1.1×π×D×L | 1.0 | Reduced area |
| **Design Function** | `design_turbofan()` | `design_turboprop()` | Changed design method |

## Key Technical Changes

### Propulsion System Architecture
- **Turbofan → Open Rotor**: Changed from ducted turbofan to unducted open rotor using RCAIDE's Turboprop class
- **Simplified Core**: Removed high pressure compressor, using single low-pressure stage
- **Efficiency Model**: Implemented Mach-dependent propeller efficiency based on Dorsey AIAA paper data

### Performance Parameters
- **Efficiency Range**: 0.745 (M=0.844) to 0.807 (M=0.746) including 0.99 gearbox efficiency
- **Pressure Ratios**: Reduced from turbofan levels (1.7 fan, 1.9 LPC, 10.0 HPC) to single 1.10 compressor
- **Bypass Concept**: Increased from 5.4 to 25 (conceptual for open rotor)

### Physical Configuration
- **Nacelle Size**: Reduced diameter from 2.05m to 1.5m for core-only configuration
- **Component Removal**: Eliminated fan nozzle, high pressure compressor, and separate fan component
- **Parametric Design**: Added function parameters for design space exploration

### Maintained Elements
- **Core Components**: Same combustor (TIT=1500K), HPT, and LPT as baseline
- **Aircraft Geometry**: Identical wing, fuselage, and empennage configuration
- **Mission Profile**: Same flight segments and operational requirements
- **Fuel System**: Identical fuel tank and distribution system

## Usage
```python
# Baseline turbofan (fixed parameters)
vehicle = vehicle_setup()

# Open fan with default parameters
vehicle = vehicle_setup()

# Open fan with custom parameters
vehicle = vehicle_setup(fan_pressure_ratio=1.15, bypass_ratio=30)
```