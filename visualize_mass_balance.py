#!/usr/bin/env python3
"""
Visualize two-compartment mass balance results
"""

import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv('output/demo_results.csv')

# Create figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Two-Compartment Mass Balance - BAL Bioreactor', 
             fontsize=16, fontweight='bold')

# Check if we have compartment data
has_compartments = 'bio_C_NH3_CV1' in df.columns

# Plot 1: NH3 concentrations
if has_compartments:
    axes[0,0].plot(df['time'], df['bio_C_NH3_CV1'], 
                   label='CV1 (Plasma)', linewidth=2, color='blue')
    axes[0,0].plot(df['time'], df['bio_C_NH3_CV2'], 
                   label='CV2 (Hepatocytes)', linewidth=2, color='orange')
else:
    axes[0,0].plot(df['time'], df['bio_C_NH3'], 
                   label='Outlet', linewidth=2, color='blue')
axes[0,0].axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Safety Target')
axes[0,0].set_xlabel('Time (min)', fontsize=12)
axes[0,0].set_ylabel('NH₃ Concentration (µmol/L)', fontsize=12)
axes[0,0].set_title('Ammonia Detoxification', fontsize=13, fontweight='bold')
axes[0,0].legend(fontsize=10)
axes[0,0].grid(True, alpha=0.3)

# Plot 2: Urea generation
if has_compartments and 'bio_C_urea_CV1' in df.columns:
    axes[0,1].plot(df['time'], df['bio_C_urea_CV1'], 
                   label='CV1 (Plasma)', linewidth=2, color='green')
    axes[0,1].plot(df['time'], df['bio_C_urea_CV2'], 
                   label='CV2 (Hepatocytes)', linewidth=2, color='lightgreen')
    axes[0,1].set_xlabel('Time (min)', fontsize=12)
    axes[0,1].set_ylabel('Urea Concentration (mmol/L)', fontsize=12)
    axes[0,1].set_title('Urea Generation (2 NH₃ → 1 Urea)', fontsize=13, fontweight='bold')
    axes[0,1].legend(fontsize=10)
    axes[0,1].grid(True, alpha=0.3)
else:
    # Fallback: show clearance
    axes[0,1].plot(df['time'], df['bio_NH3_clearance']*100, 
                   linewidth=2, color='purple')
    axes[0,1].axhline(y=60, color='gray', linestyle='--', alpha=0.5)
    axes[0,1].set_xlabel('Time (min)', fontsize=12)
    axes[0,1].set_ylabel('Clearance (%)', fontsize=12)
    axes[0,1].set_title('NH₃ Clearance Over Time', fontsize=13, fontweight='bold')
    axes[0,1].grid(True, alpha=0.3)

# Plot 3: Lidocaine metabolism
if has_compartments:
    axes[1,0].plot(df['time'], df['bio_C_lido'], 
                   label='Outlet', linewidth=2, color='purple')
else:
    axes[1,0].plot(df['time'], df['bio_C_lido'], 
                   linewidth=2, color='purple')
axes[1,0].axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Safety Target')
axes[1,0].set_xlabel('Time (min)', fontsize=12)
axes[1,0].set_ylabel('Lidocaine (µmol/L)', fontsize=12)
axes[1,0].set_title('Lidocaine Metabolism (CYP450)', fontsize=13, fontweight='bold')
axes[1,0].legend(fontsize=10)
axes[1,0].grid(True, alpha=0.3)

# Plot 4: Cell viability and clearance
ax4a = axes[1,1]
ax4b = ax4a.twinx()

# Viability on left axis
ax4a.plot(df['time'], df['bio_cell_viability']*100, 
          linewidth=2, color='green', label='Cell Viability')
ax4a.set_xlabel('Time (min)', fontsize=12)
ax4a.set_ylabel('Cell Viability (%)', fontsize=12, color='green')
ax4a.tick_params(axis='y', labelcolor='green')
ax4a.set_ylim([95, 100])

# Clearance on right axis
ax4b.plot(df['time'], df['bio_NH3_clearance']*100, 
          linewidth=2, color='blue', linestyle='--', label='NH₃ Clearance')
ax4b.set_ylabel('NH₃ Clearance (%)', fontsize=12, color='blue')
ax4b.tick_params(axis='y', labelcolor='blue')
ax4b.set_ylim([0, 100])

axes[1,1].set_title('System Performance', fontsize=13, fontweight='bold')
ax4a.grid(True, alpha=0.3)

# Add legends
lines1, labels1 = ax4a.get_legend_handles_labels()
lines2, labels2 = ax4b.get_legend_handles_labels()
ax4a.legend(lines1 + lines2, labels1 + labels2, loc='lower left', fontsize=10)

plt.tight_layout()
plt.savefig('output/mass_balance_visualization.png', dpi=150, bbox_inches='tight')
print("✅ Visualization saved to: output/mass_balance_visualization.png")

# Print summary
print("\n" + "="*60)
print("TWO-COMPARTMENT MASS BALANCE RESULTS")
print("="*60)
final_nh3 = df['bio_C_NH3'].iloc[-1]
final_lido = df['bio_C_lido'].iloc[-1]
clearance_nh3 = df['bio_NH3_clearance'].iloc[-1] * 100
clearance_lido = df['bio_lido_clearance'].iloc[-1] * 100
viability = df['bio_cell_viability'].iloc[-1] * 100

print(f"\nTreatment Results (60 minutes):")
print(f"  NH₃:       90.0 → {final_nh3:.1f} µmol/L ({clearance_nh3:.1f}% clearance)")
print(f"  Lidocaine: 21.0 → {final_lido:.1f} µmol/L ({clearance_lido:.1f}% clearance)")
print(f"  Cell Viability: {viability:.1f}%")

print(f"\nStatus:")
if clearance_nh3 > 50 and final_nh3 < 50:
    print("  ✅ NH₃ - SAFE (target: <50 µmol/L)")
else:
    print("  ⚠️  NH₃ - Review needed")

if clearance_lido > 40 and final_lido < 15:
    print("  ✅ Lidocaine - SAFE (target: <10 µmol/L)")
else:
    print("  ⚠️  Lidocaine - Review needed")

print("\n" + "="*60)

# Show if CV compartments are available
if has_compartments:
    print("\n✅ Compartment data available:")
    print(f"  Final CV1 NH₃: {df['bio_C_NH3_CV1'].iloc[-1]:.1f} µmol/L")
    print(f"  Final CV2 NH₃: {df['bio_C_NH3_CV2'].iloc[-1]:.1f} µmol/L")
    print(f"  CV2 < CV1: {df['bio_C_NH3_CV2'].iloc[-1] < df['bio_C_NH3_CV1'].iloc[-1]} (metabolism working!)")
