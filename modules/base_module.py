"""
Base module class for all BAL system modules.
Implements state machine pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseModule(ABC):
    """
    Abstract base class for all BAL modules.
    
    All modules must implement:
    - State machine with discrete states
    - update() method for time stepping
    - State transition logic
    - Input/output handling
    """
    
    def __init__(self, name: str):
        self.name = name
        self.state = None
        self.time_in_state = 0.0  # minutes
        self.simulation_time = 0.0  # total elapsed time
        
    @abstractmethod
    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        """
        Advance module simulation by dt minutes.
        
        Args:
            dt: Time step in minutes
            **inputs: Module-specific inputs from upstream modules
            
        Returns:
            Dict containing all outputs for downstream modules
        """
        pass
    
    @abstractmethod
    def _check_state_transition(self):
        """Check if state transition conditions are met."""
        pass
    
    def get_state_name(self) -> str:
        """Return human-readable state name."""
        return str(self.state)
    
    def reset(self):
        """Reset module to initial state."""
        self.time_in_state = 0.0
        self.simulation_time = 0.0
