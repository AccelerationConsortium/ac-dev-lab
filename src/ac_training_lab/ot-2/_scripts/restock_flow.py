"""
Restock maintenance flow for OT-2 color mixing demo.

This module provides Prefect flows for managing inventory restocking operations,
including manual restock triggers and automated inventory monitoring.
"""

import os
from datetime import datetime

from prefect import flow, task
from pymongo import MongoClient

from inventory_utils import (
    get_current_inventory,
    initialize_inventory,
    restock_inventory,
)

MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
blinded_connection_string = os.getenv("blinded_connection_string")

# Handle case where environment variables are not set (e.g., during testing)
if MONGODB_PASSWORD and blinded_connection_string:
    connection_string = blinded_connection_string.replace("<db_password>", MONGODB_PASSWORD)
else:
    connection_string = None


@task
def log_restock_operation(restock_data, operator="system"):
    """
    Log a restock operation to MongoDB for audit trail.
    
    Parameters:
    - restock_data: Dictionary with restock operation details
    - operator: Name/ID of person performing restock (default: "system")
    
    Returns:
    - Inserted document ID
    """
    if connection_string is None:
        raise ValueError(
            "MongoDB connection not configured. Please set MONGODB_PASSWORD and "
            "blinded_connection_string environment variables."
        )
    
    client = MongoClient(connection_string)
    db = client["LCM-OT-2-SLD"]
    collection = db["restock_log"]
    
    log_entry = {
        "timestamp": datetime.utcnow(),
        "operator": operator,
        "restock_data": restock_data,
        "operation_type": "manual_restock",
    }
    
    result = collection.insert_one(log_entry)
    client.close()
    
    return str(result.inserted_id)


@flow(name="restock-maintenance")
def restock_maintenance_flow(
    red_volume: int = 0,
    yellow_volume: int = 0,
    blue_volume: int = 0,
    operator: str = "system",
):
    """
    Prefect flow for restocking paint inventory.
    
    This flow can be triggered manually to restock one or more colors.
    
    Parameters:
    - red_volume: Volume of red paint to add in microliters (0 = no restock)
    - yellow_volume: Volume of yellow paint to add in microliters (0 = no restock)
    - blue_volume: Volume of blue paint to add in microliters (0 = no restock)
    - operator: Name/ID of person performing the restock operation
    
    Returns:
    - Dictionary with restock results and updated inventory levels
    
    Example:
        # Restock 10ml (10000 ul) of red and 15ml (15000 ul) of yellow
        restock_maintenance_flow(red_volume=10000, yellow_volume=15000, operator="lab_tech_1")
    """
    print(f"Starting restock maintenance operation by {operator}")
    print(f"Volumes to add - Red: {red_volume} ul, Yellow: {yellow_volume} ul, Blue: {blue_volume} ul")
    
    # Get inventory before restock
    inventory_before = get_current_inventory()
    print(f"Inventory before restock: {inventory_before}")
    
    # Perform restock
    restock_result = restock_inventory(
        red_volume=red_volume,
        yellow_volume=yellow_volume,
        blue_volume=blue_volume,
    )
    print(f"Restock operation completed: {restock_result}")
    
    # Log the operation
    log_id = log_restock_operation(restock_result, operator=operator)
    print(f"Restock operation logged with ID: {log_id}")
    
    # Get updated inventory
    inventory_after = get_current_inventory()
    print(f"Inventory after restock: {inventory_after}")
    
    result = {
        "status": "success",
        "operator": operator,
        "timestamp": datetime.utcnow().isoformat(),
        "volumes_added": {
            "red_ul": red_volume,
            "yellow_ul": yellow_volume,
            "blue_ul": blue_volume,
        },
        "inventory_before": inventory_before,
        "inventory_after": inventory_after,
        "log_id": log_id,
    }
    
    return result


@flow(name="initialize-inventory")
def initialize_inventory_flow(
    red_volume: int = 15000,
    yellow_volume: int = 15000,
    blue_volume: int = 15000,
    evaporation_rate: float = 5.0,
):
    """
    Initialize or reset the inventory system.
    
    Use this flow to set up the inventory system for the first time
    or to completely reset it with new starting volumes.
    
    Parameters:
    - red_volume: Initial red paint volume in microliters (default: 15000 ul = 15 ml)
    - yellow_volume: Initial yellow paint volume in microliters (default: 15000 ul = 15 ml)
    - blue_volume: Initial blue paint volume in microliters (default: 15000 ul = 15 ml)
    - evaporation_rate: Evaporation rate in ul/hour (default: 5.0)
    
    Returns:
    - Dictionary with initialized inventory state
    """
    print("Initializing inventory system...")
    print(f"Starting volumes - Red: {red_volume} ul, Yellow: {yellow_volume} ul, Blue: {blue_volume} ul")
    print(f"Evaporation rate: {evaporation_rate} ul/hour")
    
    result = initialize_inventory(
        red_volume=red_volume,
        yellow_volume=yellow_volume,
        blue_volume=blue_volume,
        evaporation_rate=evaporation_rate,
    )
    
    print(f"Inventory initialized: {result}")
    
    return result


@flow(name="check-inventory-status")
def check_inventory_status_flow(low_threshold_ml: float = 2.0):
    """
    Check current inventory status and identify colors needing restock.
    
    This flow can be run periodically to monitor inventory levels
    and alert when colors are running low.
    
    Parameters:
    - low_threshold_ml: Threshold in milliliters below which a warning is issued (default: 2.0 ml)
    
    Returns:
    - Dictionary with inventory status and restock recommendations
    """
    print("Checking inventory status...")
    
    inventory = get_current_inventory()
    low_threshold_ul = low_threshold_ml * 1000  # Convert to microliters
    
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "inventory": inventory,
        "warnings": [],
        "recommendations": [],
    }
    
    for color_key, data in inventory.items():
        volume_ml = data["volume_ul"] / 1000
        color_name = data["color"]
        
        print(f"{color_name.capitalize()}: {volume_ml:.2f} ml ({data['volume_ul']:.0f} ul)")
        
        if data["volume_ul"] <= 0:
            warning = f"{color_name.capitalize()} is OUT OF STOCK (0 ml) - RESTOCK IMMEDIATELY"
            status["warnings"].append(warning)
            status["recommendations"].append(f"Restock {color_name} with at least 15 ml (15000 ul)")
            print(f"⚠️  {warning}")
        elif data["volume_ul"] < low_threshold_ul:
            warning = f"{color_name.capitalize()} is LOW ({volume_ml:.2f} ml) - restock recommended"
            status["warnings"].append(warning)
            status["recommendations"].append(f"Restock {color_name} soon (current: {volume_ml:.2f} ml)")
            print(f"⚠️  {warning}")
        else:
            print(f"✓ {color_name.capitalize()} level is adequate ({volume_ml:.2f} ml)")
    
    if not status["warnings"]:
        status["overall_status"] = "All colors adequately stocked"
        print("\n✓ All colors are adequately stocked")
    else:
        status["overall_status"] = "Action required"
        print(f"\n⚠️  {len(status['warnings'])} color(s) need attention")
    
    return status


if __name__ == "__main__":
    # Example: Initialize inventory
    print("=" * 60)
    print("Example 1: Initialize Inventory")
    print("=" * 60)
    initialize_inventory_flow(red_volume=15000, yellow_volume=15000, blue_volume=15000)
    
    # Example: Check inventory status
    print("\n" + "=" * 60)
    print("Example 2: Check Inventory Status")
    print("=" * 60)
    check_inventory_status_flow(low_threshold_ml=5.0)
    
    # Example: Restock operation
    print("\n" + "=" * 60)
    print("Example 3: Restock Operation")
    print("=" * 60)
    restock_maintenance_flow(
        red_volume=5000,
        yellow_volume=3000,
        blue_volume=0,
        operator="lab_technician_demo"
    )
    
    # Example: Check inventory status after restock
    print("\n" + "=" * 60)
    print("Example 4: Check Status After Restock")
    print("=" * 60)
    check_inventory_status_flow(low_threshold_ml=5.0)
