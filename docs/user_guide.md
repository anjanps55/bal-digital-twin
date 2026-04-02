# BAL Digital Twin - User Guide

## Getting Started

### Installation

1. Ensure Python 3.9+ is installed
2. Create and activate virtual environment
3. Install dependencies: `pip install -r requirements.txt`

### Running the Simulator

**Command Line:**
```bash
python main.py
```

**With GUI:**
Uncomment the GUI section in `main.py`

## Module Overview

### Module 1: Plasma Separator
- Separates plasma from cellular components
- 6 discrete states from priming to failure
- Monitors TMP, separation efficiency

### Module 2: Pump Control
- Controls plasma flow rate
- 12 states including safety alarms
- Monitors pressure, temperature, flow

### Module 3: Bioreactor
- Contains membrane, hepatocytes, sensors
- Performs metabolic detoxification
- Converts ammonia to urea

### Module 4: Sampler
- Monitors cell viability
- Collects samples for analysis

### Module 5: Mixer
- Recombines plasma with blood cells
- Restores proper hematocrit

### Module 6: Return Monitor
- Final safety check
- Verifies toxin levels before return

## Configuration

Edit `config/constants.py` to adjust:
- Flow rates
- Concentration thresholds
- State transition conditions
- Safety limits

## Output

Simulation results are logged to:
- JSON format: Complete time series data
- CSV format: Tabular data for analysis

## Troubleshooting

Contact the development team for assistance.
