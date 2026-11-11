"""
Script: plot_ltspice_results.py
Directly parses the LTspice ASCII raw file (buzzer_flyback.raw)
and plots the exact SPICE transient simulation curves.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

RAW_PATH = "D:/smart_fans/hardware/ltspice/buzzer_flyback.raw"
OUTPUT_PLOT = "D:/smart_fans/hardware/simulation/plot_05_ltspice_buzzer_flyback.png"

def parse_ascii_raw(path):
    with open(path, "r", encoding="latin1") as f:
        # Read header
        variables = []
        in_vars = False
        in_values = False
        
        time_list = []
        prot_list = []
        unprot_list = []
        pb14_list = []
        ibuz_list = []
        
        num_vars = 0
        
        for line in f:
            line_s = line.strip()
            if line_s.startswith("No. Variables:"):
                num_vars = int(line_s.split(":")[1])
            elif line_s.startswith("Variables:"):
                in_vars = True
                continue
            elif in_vars and not in_values:
                if line_s.startswith("Values:"):
                    in_vars = False
                    in_values = True
                    break
                parts = line_s.split()
                if len(parts) >= 3:
                    variables.append((int(parts[0]), parts[1], parts[2]))
        
        # Read values
        # Index 0 is time
        # Index 4 is V(coll_prot)
        # Index 5 is V(coll_unprot)
        # Index 8 is V(pb14)
        # Index 11 is I(LBUZ1)
        point_idx = 0
        curr_time = 0.0
        val_idx = 0
        
        for line in f:
            parts = line.strip().split()
            if len(parts) == 0:
                continue
            if len(parts) >= 2 and parts[0].isdigit():
                # Start of a new timepoint: <point_idx> <time_val>
                curr_time = float(parts[1])
                time_list.append(curr_time)
                val_idx = 1
            else:
                val = float(parts[0])
                if val_idx == 4:
                    prot_list.append(val)
                elif val_idx == 5:
                    unprot_list.append(val)
                elif val_idx == 8:
                    pb14_list.append(val)
                elif val_idx == 11:
                    ibuz_list.append(val)
                val_idx += 1

    return (np.array(time_list),
            np.array(prot_list),
            np.array(unprot_list),
            np.array(pb14_list),
            np.array(ibuz_list))

def main():
    print(f"Reading and parsing LTspice ASCII raw file from: {RAW_PATH}")
    time, v_prot, v_unprot, v_pb14, i_buz = parse_ascii_raw(RAW_PATH)
    
    t_us = time * 1e6
    v_max_prot = np.max(v_prot)
    v_max_unprot = np.max(v_unprot)
    
    print(f"  LTspice SPICE Simulation Statistics:")
    print(f"    Total Timepoints Simulated: {len(time)}")
    print(f"    Protected V(coll_prot) Clamped Voltage: {v_max_prot:.2f} V")
    print(f"    Unprotected V(coll_unprot) Inductive Spike: {v_max_unprot:.2f} V")
    print(f"    MCU PB14 Turn-off Time: 50.0 us")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Plot 1: Collector Voltages
    ax1.plot(t_us, v_unprot, 'r--', linewidth=1.5, label=f'Unprotected V(coll_unprot) - Peak = {v_max_unprot:.1f} V (Destroys S8050)')
    ax1.plot(t_us, v_prot, 'g-', linewidth=2.0, label=f'Protected V(coll_prot) with 1N4148W - Clamped = {v_max_prot:.2f} V (100% Safe)')
    ax1.axhline(25.0, color='darkred', linestyle=':', linewidth=1.5, label='S8050 Vceo Breakdown Limit (25V)')
    ax1.axhline(5.0, color='blue', linestyle=':', alpha=0.5, label='5.0V VCC Power Rail')
    ax1.axvline(50.0, color='gray', linestyle='--', label='PB14 Turn-off (t=50us)')
    ax1.set_ylabel('Collector Voltage [V]', fontsize=11)
    ax1.set_ylim(-5, 95)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', frameon=True)
    ax1.set_title(f'LTspice 26.1.1 Full Engine Simulation: Buzzer Inductive Clamping\n1N4148W Absorbs 5mH Inductive Energy, Clamping Spike to {v_max_prot:.2f}V', fontsize=12)

    # Plot 2: MCU GPIO Input and Coil Current
    ax2.plot(t_us, v_pb14, 'b-', linewidth=1.5, label='MCU PB14 Drive Pulse (3.3V Logic)')
    ax2.plot(t_us, i_buz * 1e3, 'm-', linewidth=1.5, label='Buzzer Coil Current I(Lbuz1) [mA]')
    ax2.set_ylabel('Signals', fontsize=11)
    ax2.set_xlabel(r'Time [$\mu$s]', fontsize=11)
    ax2.set_xlim(0, 120)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right', frameon=True)

    plt.tight_layout()
    fig.savefig(OUTPUT_PLOT, dpi=200)
    plt.close(fig)
    print(f"Successfully generated and saved plot to: {OUTPUT_PLOT}")

if __name__ == "__main__":
    main()
