"""
Data Logger

Records simulation outputs for analysis and export.
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd


class DataLogger:
    """
    Logs and exports simulation data.

    Supports CSV and JSON export formats.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize data logger.

        Args:
            output_dir: Directory for output files (default: "output")
        """
        self.output_dir = output_dir
        self.data = []

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def log(self, timestamp: float, data: Dict[str, Any]):
        """
        Log data at current timestamp.

        Args:
            timestamp: Simulation time in minutes
            data: Dictionary of values to log
        """
        entry = {
            'time': timestamp,
            **data
        }
        self.data.append(entry)

    def export_csv(self, filename: str):
        """
        Export logged data to CSV file.

        Args:
            filename: Name of CSV file (e.g., "results.csv")
        """
        if not self.data:
            print("Warning: No data to export")
            return

        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)

            # Create full path
            filepath = os.path.join(self.output_dir, filename)

            # Export to CSV
            df.to_csv(filepath, index=False)

            print(f"  Exported to: {filepath} ({len(df)} rows)")

        except Exception as e:
            print(f"Error exporting CSV: {e}")

    def export_json(self, filename: str):
        """
        Export logged data to JSON file.

        Args:
            filename: Name of JSON file (e.g., "results.json")
        """
        if not self.data:
            print("Warning: No data to export")
            return

        try:
            # Create full path
            filepath = os.path.join(self.output_dir, filename)

            # Export to JSON with pretty printing
            with open(filepath, 'w') as f:
                json.dump(self.data, f, indent=2)

            print(f"  Exported to: {filepath}")

        except Exception as e:
            print(f"Error exporting JSON: {e}")

    def clear(self):
        """
        Clear all logged data.

        Resets the data list to empty.
        """
        self.data = []

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of logged data.

        Returns:
            Dict containing:
                - total_points: Number of data points
                - time_range: (start_time, end_time) tuple
                - columns: List of available data columns
        """
        if not self.data:
            return {
                'total_points': 0,
                'time_range': (0, 0),
                'columns': []
            }

        # Get time range
        times = [entry['time'] for entry in self.data]
        time_range = (min(times), max(times))

        # Get all unique columns
        columns = set()
        for entry in self.data:
            columns.update(entry.keys())

        return {
            'total_points': len(self.data),
            'time_range': time_range,
            'columns': sorted(list(columns))
        }
