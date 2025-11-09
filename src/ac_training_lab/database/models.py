"""
Data models for MongoDB storage of BO experiments

This module defines the data schemas for storing Bayesian Optimization
experiment data in MongoDB.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class Experiment:
    """
    Represents a Bayesian Optimization experiment campaign
    
    Stored in the 'experiments' collection
    """
    experiment_id: str
    name: str
    description: str
    objective_name: str
    parameter_space: Dict[str, Any]  # Ax parameter space definition
    n_iterations: int
    random_seed: Optional[int]
    status: str  # 'running', 'completed', 'failed', 'paused'
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    flow_run_id: Optional[str] = None
    slack_channel: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experiment':
        """Create Experiment from MongoDB document"""
        # Convert ISO format strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class Trial:
    """
    Represents a single trial (parameter suggestion + evaluation) in a BO experiment
    
    Stored in the 'trials' collection
    """
    trial_id: str
    experiment_id: str
    trial_index: int
    iteration: int
    parameters: Dict[str, float]  # Parameter values suggested by Ax
    objective_value: Optional[float] = None
    objective_name: str = "objective"
    evaluation_method: str = "human"  # 'human', 'automated', 'api'
    status: str = "pending"  # 'pending', 'evaluated', 'failed'
    human_notes: Optional[str] = None
    evaluation_time_seconds: Optional[float] = None
    suggested_at: datetime = None
    evaluated_at: Optional[datetime] = None
    slack_message_sent: bool = False
    
    def __post_init__(self):
        if self.suggested_at is None:
            self.suggested_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['suggested_at'] = self.suggested_at.isoformat()
        if self.evaluated_at:
            data['evaluated_at'] = self.evaluated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trial':
        """Create Trial from MongoDB document"""
        # Convert ISO format strings back to datetime objects
        data['suggested_at'] = datetime.fromisoformat(data['suggested_at'])
        if data.get('evaluated_at'):
            data['evaluated_at'] = datetime.fromisoformat(data['evaluated_at'])
        return cls(**data)


@dataclass
class ExperimentResult:
    """
    Represents the final results of a completed BO experiment
    
    Stored in the 'results' collection
    """
    experiment_id: str
    best_parameters: Dict[str, float]
    best_objective_value: float
    total_trials: int
    successful_trials: int
    failed_trials: int
    total_duration_seconds: float
    avg_evaluation_time_seconds: Optional[float]
    convergence_metrics: Optional[Dict[str, Any]] = None
    all_trials_summary: Optional[List[Dict[str, Any]]] = None
    ax_state_json: Optional[str] = None  # Serialized Ax client state for reproduction
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentResult':
        """Create ExperimentResult from MongoDB document"""
        # Convert ISO format strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


def generate_experiment_id(name: str, timestamp: datetime = None) -> str:
    """Generate a unique experiment ID"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Create a clean name for the ID
    clean_name = name.lower().replace(' ', '_').replace('-', '_')
    clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
    
    # Add timestamp for uniqueness
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    return f"{clean_name}_{timestamp_str}"


def generate_trial_id(experiment_id: str, trial_index: int) -> str:
    """Generate a unique trial ID"""
    return f"{experiment_id}_trial_{trial_index}"