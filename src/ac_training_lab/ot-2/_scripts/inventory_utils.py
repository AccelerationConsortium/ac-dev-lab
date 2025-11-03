"""
Inventory management utilities for OT-2 color mixing demo.

This module provides functions to track and manage paint stock levels,
including evaporation over time and stock subtraction with each experiment.
"""

import os
from datetime import datetime, timedelta

from prefect import task
from pymongo import MongoClient

MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
blinded_connection_string = os.getenv("blinded_connection_string")

# Handle case where environment variables are not set (e.g., during testing)
if MONGODB_PASSWORD and blinded_connection_string:
    connection_string = blinded_connection_string.replace("<db_password>", MONGODB_PASSWORD)
else:
    connection_string = None

# Color positions in the reservoir (from OT2mqtt.py)
COLOR_POSITIONS = {
    "R": "B1",  # Red
    "Y": "B2",  # Yellow
    "B": "B3",  # Blue
}

# Default evaporation rate: microliters per hour
DEFAULT_EVAPORATION_RATE = 5.0  # ul/hour per color reservoir


def get_inventory_collection():
    """Get MongoDB collection for inventory tracking."""
    if connection_string is None:
        raise ValueError(
            "MongoDB connection not configured. Please set MONGODB_PASSWORD and "
            "blinded_connection_string environment variables."
        )
    client = MongoClient(connection_string)
    db = client["LCM-OT-2-SLD"]
    return client, db["inventory"]


@task
def initialize_inventory(
    red_volume=15000, yellow_volume=15000, blue_volume=15000, evaporation_rate=DEFAULT_EVAPORATION_RATE
):
    """
    Initialize or reset the inventory collection with starting volumes.
    
    Parameters:
    - red_volume: Initial volume of red paint in microliters (default: 15000 ul = 15 ml)
    - yellow_volume: Initial volume of yellow paint in microliters
    - blue_volume: Initial volume of blue paint in microliters
    - evaporation_rate: Evaporation rate in ul/hour (default: 5 ul/hour)
    
    Returns:
    - Dictionary with initialized inventory state
    """
    client, collection = get_inventory_collection()
    
    try:
        timestamp = datetime.utcnow()
        
        inventory_data = {
            "R": {
                "color": "red",
                "position": COLOR_POSITIONS["R"],
                "volume_ul": red_volume,
                "last_updated": timestamp,
                "evaporation_rate_ul_per_hour": evaporation_rate,
            },
            "Y": {
                "color": "yellow",
                "position": COLOR_POSITIONS["Y"],
                "volume_ul": yellow_volume,
                "last_updated": timestamp,
                "evaporation_rate_ul_per_hour": evaporation_rate,
            },
            "B": {
                "color": "blue",
                "position": COLOR_POSITIONS["B"],
                "volume_ul": blue_volume,
                "last_updated": timestamp,
                "evaporation_rate_ul_per_hour": evaporation_rate,
            },
        }
        
        for color_key, data in inventory_data.items():
            query = {"color_key": color_key}
            update_data = {"$set": {**data, "color_key": color_key}}
            collection.update_one(query, update_data, upsert=True)
        
        return inventory_data
    
    finally:
        client.close()


@task
def get_current_inventory():
    """
    Get current inventory levels, accounting for evaporation since last update.
    
    Returns:
    - Dictionary with current inventory state after evaporation adjustment
    """
    client, collection = get_inventory_collection()
    
    try:
        current_time = datetime.utcnow()
        inventory = {}
        
        for color_key in ["R", "Y", "B"]:
            record = collection.find_one({"color_key": color_key})
            
            if record is None:
                # Initialize if not found
                client.close()
                initialize_inventory()
                client, collection = get_inventory_collection()
                record = collection.find_one({"color_key": color_key})
            
            # Calculate evaporation
            last_updated = record["last_updated"]
            hours_elapsed = (current_time - last_updated).total_seconds() / 3600
            evaporation_amount = hours_elapsed * record["evaporation_rate_ul_per_hour"]
            
            current_volume = max(0, record["volume_ul"] - evaporation_amount)
            
            inventory[color_key] = {
                "color": record["color"],
                "position": record["position"],
                "volume_ul": current_volume,
                "evaporation_loss_ul": evaporation_amount,
                "last_updated": record["last_updated"],
            }
        
        return inventory
    
    finally:
        client.close()


@task
def check_stock_availability(red_volume=0, yellow_volume=0, blue_volume=0, threshold=100):
    """
    Check if sufficient stock is available for a mixing operation.
    
    Parameters:
    - red_volume: Required red paint volume in microliters
    - yellow_volume: Required yellow paint volume in microliters
    - blue_volume: Required blue paint volume in microliters
    - threshold: Minimum volume threshold in microliters (default: 100 ul)
    
    Returns:
    - Dictionary with availability status and current levels
    
    Raises:
    - ValueError if insufficient stock for any color
    """
    inventory = get_current_inventory()
    
    requirements = {
        "R": red_volume,
        "Y": yellow_volume,
        "B": blue_volume,
    }
    
    availability = {}
    insufficient_colors = []
    
    for color_key, required_volume in requirements.items():
        current_volume = inventory[color_key]["volume_ul"]
        is_available = current_volume >= (required_volume + threshold)
        
        availability[color_key] = {
            "color": inventory[color_key]["color"],
            "required_ul": required_volume,
            "available_ul": current_volume,
            "is_sufficient": is_available,
            "remaining_after_use_ul": current_volume - required_volume if is_available else 0,
        }
        
        if not is_available:
            insufficient_colors.append(
                f"{inventory[color_key]['color']} (available: {current_volume:.1f} ul, required: {required_volume + threshold:.1f} ul)"
            )
    
    if insufficient_colors:
        raise ValueError(
            f"Insufficient stock for: {', '.join(insufficient_colors)}. Please restock before proceeding."
        )
    
    return availability


@task
def subtract_stock(red_volume=0, yellow_volume=0, blue_volume=0):
    """
    Subtract stock volumes after a mixing operation and update evaporation.
    
    Parameters:
    - red_volume: Red paint volume used in microliters
    - yellow_volume: Yellow paint volume used in microliters
    - blue_volume: Blue paint volume used in microliters
    
    Returns:
    - Dictionary with updated inventory state
    
    Raises:
    - ValueError if inventory not initialized
    """
    client, collection = get_inventory_collection()
    
    try:
        current_time = datetime.utcnow()
        volumes = {"R": red_volume, "Y": yellow_volume, "B": blue_volume}
        updated_inventory = {}
        
        for color_key, used_volume in volumes.items():
            record = collection.find_one({"color_key": color_key})
            
            if record is None:
                raise ValueError(
                    f"Inventory not initialized for color {color_key}. "
                    "Run initialize_inventory() first."
                )
            
            # Calculate evaporation since last update
            last_updated = record["last_updated"]
            hours_elapsed = (current_time - last_updated).total_seconds() / 3600
            evaporation_amount = hours_elapsed * record["evaporation_rate_ul_per_hour"]
            
            # Calculate new volume (subtract used volume and evaporation)
            new_volume = max(0, record["volume_ul"] - used_volume - evaporation_amount)
            
            # Update database
            update_data = {
                "$set": {
                    "volume_ul": new_volume,
                    "last_updated": current_time,
                }
            }
            collection.update_one({"color_key": color_key}, update_data)
            
            updated_inventory[color_key] = {
                "color": record["color"],
                "volume_ul": new_volume,
                "used_ul": used_volume,
                "evaporation_ul": evaporation_amount,
            }
        
        return updated_inventory
    
    finally:
        client.close()


@task
def restock_inventory(red_volume=0, yellow_volume=0, blue_volume=0):
    """
    Add stock to inventory (restock operation).
    
    Parameters:
    - red_volume: Red paint volume to add in microliters
    - yellow_volume: Yellow paint volume to add in microliters
    - blue_volume: Blue paint volume to add in microliters
    
    Returns:
    - Dictionary with updated inventory state
    
    Raises:
    - ValueError if inventory not initialized
    """
    client, collection = get_inventory_collection()
    
    try:
        current_time = datetime.utcnow()
        volumes = {"R": red_volume, "Y": yellow_volume, "B": blue_volume}
        restocked_inventory = {}
        
        for color_key, add_volume in volumes.items():
            if add_volume == 0:
                continue
                
            record = collection.find_one({"color_key": color_key})
            
            if record is None:
                raise ValueError(
                    f"Inventory not initialized for color {color_key}. "
                    "Run initialize_inventory() first."
                )
            
            # Calculate evaporation since last update
            last_updated = record["last_updated"]
            hours_elapsed = (current_time - last_updated).total_seconds() / 3600
            evaporation_amount = hours_elapsed * record["evaporation_rate_ul_per_hour"]
            
            # Calculate new volume (add restock volume, subtract evaporation)
            current_volume = max(0, record["volume_ul"] - evaporation_amount)
            new_volume = current_volume + add_volume
            
            # Update database
            update_data = {
                "$set": {
                    "volume_ul": new_volume,
                    "last_updated": current_time,
                }
            }
            collection.update_one({"color_key": color_key}, update_data)
            
            restocked_inventory[color_key] = {
                "color": record["color"],
                "previous_volume_ul": current_volume,
                "added_ul": add_volume,
                "new_volume_ul": new_volume,
                "evaporation_ul": evaporation_amount,
            }
        
        return restocked_inventory
    
    finally:
        client.close()


if __name__ == "__main__":
    # Example usage
    print("Initializing inventory...")
    init_result = initialize_inventory()
    print(f"Initialized: {init_result}")
    
    print("\nGetting current inventory...")
    current = get_current_inventory()
    print(f"Current inventory: {current}")
    
    print("\nChecking stock availability for mixing...")
    try:
        availability = check_stock_availability(red_volume=100, yellow_volume=50, blue_volume=80)
        print(f"Stock check: {availability}")
    except ValueError as e:
        print(f"Stock check failed: {e}")
