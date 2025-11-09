"""
Database operations for BO experiments

This module provides high-level database operations for storing and retrieving
Bayesian Optimization experiment data.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo.errors import DuplicateKeyError
from .mongodb_client import MongoDBClient, get_mongodb_client
from .models import Experiment, Trial, ExperimentResult


logger = logging.getLogger(__name__)


class ExperimentOperations:
    """High-level operations for BO experiment data"""
    
    def __init__(self, client: Optional[MongoDBClient] = None):
        """
        Initialize operations with MongoDB client
        
        Args:
            client: MongoDB client instance (uses global client if None)
        """
        self.client = client or get_mongodb_client()
    
    async def save_experiment(self, experiment: Experiment) -> bool:
        """
        Save experiment to database
        
        Args:
            experiment: Experiment object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("experiments")
            result = collection.insert_one(experiment.to_dict())
            
            logger.info(f"Saved experiment {experiment.experiment_id} to database")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Experiment {experiment.experiment_id} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Failed to save experiment {experiment.experiment_id}: {e}")
            return False
    
    def save_experiment_sync(self, experiment: Experiment) -> bool:
        """Synchronous version of save_experiment"""
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("experiments")
            result = collection.insert_one(experiment.to_dict())
            
            logger.info(f"Saved experiment {experiment.experiment_id} to database")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Experiment {experiment.experiment_id} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Failed to save experiment {experiment.experiment_id}: {e}")
            return False
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """
        Retrieve experiment by ID
        
        Args:
            experiment_id: Unique experiment identifier
            
        Returns:
            Experiment object if found, None otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("experiments")
            doc = collection.find_one({"experiment_id": experiment_id})
            
            if doc:
                # Remove MongoDB _id field before converting to Experiment
                doc.pop("_id", None)
                return Experiment.from_dict(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve experiment {experiment_id}: {e}")
            return None
    
    def update_experiment_status(self, experiment_id: str, status: str, completed_at: Optional[datetime] = None) -> bool:
        """
        Update experiment status
        
        Args:
            experiment_id: Unique experiment identifier
            status: New status ('running', 'completed', 'failed', 'paused')
            completed_at: Completion timestamp (for completed experiments)
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("experiments")
            
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if completed_at and status == "completed":
                update_data["completed_at"] = completed_at.isoformat()
            
            result = collection.update_one(
                {"experiment_id": experiment_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated experiment {experiment_id} status to {status}")
                return True
            else:
                logger.warning(f"No experiment found with ID {experiment_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update experiment {experiment_id} status: {e}")
            return False
    
    def save_trial(self, trial: Trial) -> bool:
        """
        Save trial to database
        
        Args:
            trial: Trial object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("trials")
            result = collection.insert_one(trial.to_dict())
            
            logger.info(f"Saved trial {trial.trial_id} to database")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Trial {trial.trial_id} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Failed to save trial {trial.trial_id}: {e}")
            return False
    
    def update_trial_evaluation(
        self,
        trial_id: str,
        objective_value: float,
        human_notes: Optional[str] = None,
        evaluation_time_seconds: Optional[float] = None
    ) -> bool:
        """
        Update trial with evaluation results
        
        Args:
            trial_id: Unique trial identifier
            objective_value: Evaluated objective value
            human_notes: Optional notes from human evaluator
            evaluation_time_seconds: Time taken for evaluation
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("trials")
            
            update_data = {
                "objective_value": objective_value,
                "status": "evaluated",
                "evaluated_at": datetime.utcnow().isoformat()
            }
            
            if human_notes:
                update_data["human_notes"] = human_notes
            if evaluation_time_seconds is not None:
                update_data["evaluation_time_seconds"] = evaluation_time_seconds
            
            result = collection.update_one(
                {"trial_id": trial_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated trial {trial_id} with objective value {objective_value}")
                return True
            else:
                logger.warning(f"No trial found with ID {trial_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update trial {trial_id}: {e}")
            return False
    
    def get_experiment_trials(self, experiment_id: str) -> List[Trial]:
        """
        Get all trials for an experiment
        
        Args:
            experiment_id: Unique experiment identifier
            
        Returns:
            List of Trial objects sorted by trial_index
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("trials")
            cursor = collection.find(
                {"experiment_id": experiment_id}
            ).sort("trial_index", 1)
            
            trials = []
            for doc in cursor:
                # Remove MongoDB _id field before converting to Trial
                doc.pop("_id", None)
                trials.append(Trial.from_dict(doc))
            
            return trials
            
        except Exception as e:
            logger.error(f"Failed to retrieve trials for experiment {experiment_id}: {e}")
            return []
    
    def save_experiment_result(self, result: ExperimentResult) -> bool:
        """
        Save experiment results to database
        
        Args:
            result: ExperimentResult object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("results")
            result_doc = collection.insert_one(result.to_dict())
            
            logger.info(f"Saved results for experiment {result.experiment_id} to database")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Results for experiment {result.experiment_id} already exist in database")
            return False
        except Exception as e:
            logger.error(f"Failed to save results for experiment {result.experiment_id}: {e}")
            return False
    
    def get_experiment_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        Retrieve experiment results by ID
        
        Args:
            experiment_id: Unique experiment identifier
            
        Returns:
            ExperimentResult object if found, None otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("results")
            doc = collection.find_one({"experiment_id": experiment_id})
            
            if doc:
                # Remove MongoDB _id field before converting to ExperimentResult
                doc.pop("_id", None)
                return ExperimentResult.from_dict(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve results for experiment {experiment_id}: {e}")
            return None
    
    def list_experiments(self, status: Optional[str] = None, limit: int = 50) -> List[Experiment]:
        """
        List experiments with optional status filter
        
        Args:
            status: Optional status filter ('running', 'completed', 'failed', 'paused')
            limit: Maximum number of experiments to return
            
        Returns:
            List of Experiment objects sorted by creation time (newest first)
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            collection = self.client.get_collection("experiments")
            
            query = {}
            if status:
                query["status"] = status
            
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            
            experiments = []
            for doc in cursor:
                # Remove MongoDB _id field before converting to Experiment
                doc.pop("_id", None)
                experiments.append(Experiment.from_dict(doc))
            
            return experiments
            
        except Exception as e:
            logger.error(f"Failed to list experiments: {e}")
            return []
    
    def cleanup_experiment(self, experiment_id: str) -> bool:
        """
        Delete experiment and all associated trials and results
        
        Args:
            experiment_id: Unique experiment identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if not self.client.is_connected:
                self.client.connect()
            
            # Delete from all collections
            experiments_collection = self.client.get_collection("experiments")
            trials_collection = self.client.get_collection("trials")
            results_collection = self.client.get_collection("results")
            
            exp_result = experiments_collection.delete_one({"experiment_id": experiment_id})
            trials_result = trials_collection.delete_many({"experiment_id": experiment_id})
            results_result = results_collection.delete_one({"experiment_id": experiment_id})
            
            logger.info(f"Cleanup experiment {experiment_id}: "
                       f"deleted {exp_result.deleted_count} experiments, "
                       f"{trials_result.deleted_count} trials, "
                       f"{results_result.deleted_count} results")
            
            return exp_result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup experiment {experiment_id}: {e}")
            return False