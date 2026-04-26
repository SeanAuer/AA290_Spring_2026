# turbofan_results.py
# Sweeps passengers and design range for the baseline 737-800 turbofan
# and generates contour plots of key performance metrics.
#
# Usage:
#   python turbofan_results.py          # run sweep (resumes from pickle if interrupted)
#   python turbofan_results.py --plot   # just re-plot from saved data

import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import pickle
import time

# Add parent directories to path so we can import the baseline vehicle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mission_simulation'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import RCAIDE
from RCAIDE.Framework.Core import Units
from RCAIDE.Library.Plots import *

from baseline_turbofan_airplane import vehicle_setup, configs_setup, analyses_setup

DATA_DIR  = os.path.join(os.path.dirname(__file__), 'output_data')
DATA_FILE = os.path.join(DATA_DIR, 'turbofan_sweep.pkl')

# ---------------------------------------------------------------
#   Mission Setup (parameterized by cruise distance)
# ---------------------------------------------------------------
def mission_setup(analyses, cruise_distance_nmi):
    """Build mission with a variable cruise distance (economic range)."""

    mission = RCAIDE.Framework.Mission.Sequential_Segments()
    mission.tag = 'the_mission'

    Segments = RCAIDE.Framework.Mission.Segments
    base_segment = Segments.Segment()

    # ---- Takeoff ----
    segment = Segments.Ground.Takeoff(base_segment)
    segment.tag = "Takeoff"
    segment.analyses.extend(analyses.takeoff)
    segment.velocity_start       = 10.0 * Units.knots
    segment.velocity_end         = 125.0 * Units['m/s']
    segment.friction_coefficient = 0.04
    segment.altitude             = 0.0
    mission.append_segment(segment)

    # ---- Climb 1 ----
    segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "climb_1"
    segment.analyses.extend(analyses.takeoff)
    segment.altitude_start = 0.0   * Units.km
    segment.altitude_end   = 3.0   * Units.km
    segment.air_speed      = 125.0 * Units['m/s']
    segment.climb_rate     = 6.0   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Climb 2 ----
    segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "climb_2"
    segment.analyses.extend(analyses.cruise)
    segment.altitude_end = 8.0   * Units.km
    segment.air_speed    = 190.0 * Units['m/s']
    segment.climb_rate   = 6.0   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Climb 3 ----
    segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "climb_3"
    segment.analyses.extend(analyses.cruise)
    segment.altitude_end = 10.5   * Units.km
    segment.air_speed    = 226.0  * Units['m/s']
    segment.climb_rate   = 3.0    * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Cruise (variable distance) ----
    segment = Segments.Cruise.Constant_Speed_Constant_Altitude(base_segment)
    segment.tag = "cruise"
    segment.analyses.extend(analyses.cruise)
    segment.altitude  = 10.668 * Units.km
    segment.air_speed = 230.412 * Units['m/s']
    segment.distance  = cruise_distance_nmi * Units.nmi
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Descent 1 ----
    segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "descent_1"
    segment.analyses.extend(analyses.cruise)
    segment.altitude_start = 10.5 * Units.km
    segment.altitude_end   = 8.0  * Units.km
    segment.air_speed      = 220.0 * Units['m/s']
    segment.descent_rate   = 4.5   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Descent 2 ----
    segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "descent_2"
    segment.analyses.extend(analyses.cruise)
    segment.altitude_end = 6.0   * Units.km
    segment.air_speed    = 195.0 * Units['m/s']
    segment.descent_rate = 5.0   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Descent 3 ----
    segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "descent_3"
    segment.analyses.extend(analyses.cruise)
    segment.altitude_end = 4.0   * Units.km
    segment.air_speed    = 170.0 * Units['m/s']
    segment.descent_rate = 5.0   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Descent 4 ----
    segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "descent_4"
    segment.analyses.extend(analyses.cruise)
    segment.altitude_end = 2.0   * Units.km
    segment.air_speed    = 150.0 * Units['m/s']
    segment.descent_rate = 5.0   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Descent 5 ----
    segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "descent_5"
    segment.analyses.extend(analyses.landing)
    segment.altitude_end = 0.0   * Units.km
    segment.air_speed    = 145.0 * Units['m/s']
    segment.descent_rate = 3.0   * Units['m/s']
    segment.flight_dynamics.force_x = True
    segment.flight_dynamics.force_z = True
    segment.assigned_control_variables.throttle.active              = True
    segment.assigned_control_variables.throttle.assigned_propulsors = [['starboard_propulsor', 'port_propulsor']]
    segment.assigned_control_variables.body_angle.active            = True
    mission.append_segment(segment)

    # ---- Landing ----
    segment = Segments.Ground.Landing(base_segment)
    segment.tag = "Landing"
    segment.analyses.extend(analyses.reverse_thrust)
    segment.velocity_start = 145.0 * Units['m/s']
    segment.velocity_end   = 10 * Units.knots
    segment.friction_coefficient = 0.4
    segment.altitude = 0.0
    segment.assigned_control_variables.elapsed_time.active                = True
    segment.assigned_control_variables.elapsed_time.initial_guess_values  = [[30.]]
    mission.append_segment(segment)

    return mission

# ---------------------------------------------------------------
#   Extract performance metrics from mission results
# ---------------------------------------------------------------
def extract_metrics(results, pax, economic_range_nmi):
    """Pull MTOW, OEW fraction, fuel burn per seat-mile, and initial cruise L/D."""

    # Find the cruise segment
    cruise_tag = 'cruise'
    cruise_seg = None
    for seg in results.segments:
        if seg.tag == cruise_tag:
            cruise_seg = seg
            break

    if cruise_seg is None:
        return None

    # Weight at start and end of full mission
    w_start = results.segments[0].conditions.weights.total_mass[0, 0]
    w_end   = results.segments[-1].conditions.weights.total_mass[-1, 0]
    fuel_burned = w_start - w_end  # kg

    # MTOW (kg -> lbm for consistency with Dorsey)
    mtow_kg  = w_start
    mtow_lbm = mtow_kg * 2.20462

    # OEW approximation: MTOW - fuel - payload
    pax_weight_kg = pax * 100.0  # ~220 lbm per pax including luggage
    oew_kg  = mtow_kg - fuel_burned - pax_weight_kg
    ew_frac = oew_kg / mtow_kg

    # Fuel burn per seat-mile (lbm / (pax * nm))
    fuel_burned_lbm = fuel_burned * 2.20462
    fb_per_seat_mile = fuel_burned_lbm / (pax * economic_range_nmi) if (pax * economic_range_nmi) > 0 else np.nan

    # Initial cruise L/D (first control point of cruise segment)
    CL = cruise_seg.conditions.aerodynamics.coefficients.lift.total[0, 0]
    CD = cruise_seg.conditions.aerodynamics.coefficients.drag.total[0, 0]
    LD = CL / CD if CD > 0 else np.nan

    return {
        'mtow_lbm'         : mtow_lbm,
        'ew_fraction'      : ew_frac,
        'fb_per_seat_mile' : fb_per_seat_mile,
        'cruise_LD'        : LD,
    }

# ---------------------------------------------------------------
#   Data persistence (single pickle file)
# ---------------------------------------------------------------
def save_data(pax_vals, range_vals, data_grids, completed):
    """Save everything to one pickle. ~instant. Uses atomic write to prevent corruption."""
    payload = {
        'pax_vals'   : pax_vals,
        'range_vals' : range_vals,
        'data_grids' : data_grids,
        'completed'  : completed,   # set of (pax, range) tuples already done
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_file = DATA_FILE + '.tmp'
    with open(tmp_file, 'wb') as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp_file, DATA_FILE)  # atomic on NTFS

def load_data():
    """Load from pickle. Returns None if file doesn't exist."""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, 'rb') as f:
        return pickle.load(f)

# ---------------------------------------------------------------
#   Plotting
# ---------------------------------------------------------------
def plot_contours(range_vals, pax_vals, data_grids):
    """Create 2x2 filled contour plots in the style of Dorsey Figure 10."""

    R, P = np.meshgrid(range_vals, pax_vals)

    titles = [
        'Maximum Takeoff Weight (lbm)',
        'Empty Weight Fraction (--)',
        'Economic Mission Fuel Burn\nPer Seat-Mile (lbm/(pax·nm))',
        'Economic Range Initial Cruise\nLift to Drag Ratio (--)',
    ]
    keys = ['mtow_lbm', 'ew_fraction', 'fb_per_seat_mile', 'cruise_LD']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Turbofan Configuration: Payload vs Range Performance', fontsize=14, fontweight='bold')

    for ax, key, title in zip(axes.flatten(), keys, titles):
        Z = data_grids[key]
        if np.all(np.isnan(Z)):
            ax.set_title(title)
            ax.set_xlabel('Design Range (nm)')
            ax.set_ylabel('Passengers')
            ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, ha='center')
            continue

        cf = ax.contourf(R, P, Z, levels=15, cmap='viridis')
        fig.colorbar(cf, ax=ax)
        ax.set_title(title)
        ax.set_xlabel('Design Range (nm)')
        ax.set_ylabel('Passengers')

    plt.tight_layout()
    save_path = os.path.join(os.path.dirname(__file__), 'turbofan_performance_contours.png')
    plt.savefig(save_path, dpi=200)
    print(f'Saved figure to {save_path}')
    plt.show()

# ---------------------------------------------------------------
#   Main sweep
# ---------------------------------------------------------------
def main():

    # --plot flag: just re-plot from saved data, no RCAIDE needed
    if '--plot' in sys.argv:
        saved = load_data()
        if saved is None:
            print(f'No data file found at {DATA_FILE}')
            return
        print(f'Loaded {len(saved["completed"])} completed cases from {DATA_FILE}')
        plot_contours(saved['range_vals'], saved['pax_vals'], saved['data_grids'])
        return

    # Sweep parameters
    pax_vals   = np.arange(50, 401, 50)      # 50 to 400
    range_vals = np.arange(1000, 7001, 1000)  # 1000 to 7000 nm
    keys = ['mtow_lbm', 'ew_fraction', 'fb_per_seat_mile', 'cruise_LD']

    # Try to resume from previous run
    saved = load_data()
    if saved is not None:
        data_grids = saved['data_grids']
        completed  = saved['completed']
        print(f'Resuming: {len(completed)}/{len(pax_vals)*len(range_vals)} cases already done')
    else:
        data_grids = {k: np.full((len(pax_vals), len(range_vals)), np.nan) for k in keys}
        completed  = set()

    # Build vehicle once
    vehicle = vehicle_setup()

    total = len(pax_vals) * len(range_vals)
    done  = len(completed)

    for i, pax in enumerate(pax_vals):
        for j, design_range in enumerate(range_vals):

            # Skip already-completed cases
            if (int(pax), int(design_range)) in completed:
                continue

            # Economic range per Dorsey
            if design_range == 1000:
                econ_range = design_range / 2.0
            else:
                econ_range = design_range / 3.0

            done += 1
            print(f'[{done}/{total}] {pax} pax, {design_range} nm design, {econ_range:.0f} nm econ')
            t0 = time.time()

            try:
                vehicle.passengers = pax
                pax_weight = pax * 100.0  # kg
                vehicle.mass_properties.max_zero_fuel = vehicle.mass_properties.operating_empty + pax_weight

                configs  = configs_setup(vehicle)
                analyses = analyses_setup(configs)

                mission = mission_setup(analyses, econ_range)
                mission.tag = 'economic_mission'
                missions = RCAIDE.Framework.Mission.Missions()
                missions.append(mission)
                results = missions.economic_mission.evaluate()

                metrics = extract_metrics(results, pax, econ_range)
                if metrics is not None:
                    for k in keys:
                        data_grids[k][i, j] = metrics[k]

                elapsed = time.time() - t0
                print(f'  -> OK ({elapsed:.1f}s): MTOW={metrics["mtow_lbm"]:.0f}, '
                      f'EWF={metrics["ew_fraction"]:.3f}, '
                      f'FB/sm={metrics["fb_per_seat_mile"]:.4f}, '
                      f'L/D={metrics["cruise_LD"]:.2f}')

            except Exception as e:
                elapsed = time.time() - t0
                print(f'  -> FAILED ({elapsed:.1f}s): {e}')

            # Mark done and save after every case
            completed.add((int(pax), int(design_range)))
            save_data(pax_vals, range_vals, data_grids, completed)

    print(f'\nSweep complete. Data saved to {DATA_FILE}')
    plot_contours(range_vals, pax_vals, data_grids)

if __name__ == '__main__':
    main()
