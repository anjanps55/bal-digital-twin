"""
Graphical User Interface

User-friendly interface for running simulations and viewing results.
"""

import tkinter as tk
from tkinter import ttk


class BALGUI:
    """
    Main GUI window for BAL simulator.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BAL Digital Twin Simulator")
        self.root.geometry("1200x800")
        
        # TODO: Create GUI layout
        # - Input parameter controls
        # - Start/Stop/Pause buttons
        # - Module status display
        # - Real-time graphs
        
    def run(self):
        """Start GUI main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    gui = BALGUI()
    gui.run()
