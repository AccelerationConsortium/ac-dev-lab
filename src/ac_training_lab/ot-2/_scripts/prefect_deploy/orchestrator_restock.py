"""
orchestrator_restock.py - Orchestrate restock maintenance operations

This script provides examples of how to submit restock maintenance jobs
to the Prefect work pool. Use this to manually trigger restock operations,
check inventory status, or initialize the inventory system.
"""

from prefect.deployments import run_deployment


def submit_restock_job(red_ml=0, yellow_ml=0, blue_ml=0, operator="system"):
    """
    Submit a restock maintenance job.
    
    Parameters:
    - red_ml: Volume of red paint to add in milliliters
    - yellow_ml: Volume of yellow paint to add in milliliters
    - blue_ml: Volume of blue paint to add in milliliters
    - operator: Name/ID of person performing the restock
    
    Example:
        # Restock 10ml of red and 15ml of yellow
        submit_restock_job(red_ml=10, yellow_ml=15, operator="lab_tech_1")
    """
    # Convert milliliters to microliters
    red_ul = int(red_ml * 1000)
    yellow_ul = int(yellow_ml * 1000)
    blue_ul = int(blue_ml * 1000)
    
    print(f"Submitting restock job by {operator}...")
    print(f"Volumes: Red={red_ml}ml, Yellow={yellow_ml}ml, Blue={blue_ml}ml")
    
    run_deployment(
        name="restock-maintenance/restock-maintenance",
        parameters={
            "red_volume": red_ul,
            "yellow_volume": yellow_ul,
            "blue_volume": blue_ul,
            "operator": operator,
        },
    )
    print("Restock job submitted to maintenance queue")


def submit_check_inventory_job(low_threshold_ml=2.0):
    """
    Submit an inventory status check job.
    
    Parameters:
    - low_threshold_ml: Threshold in milliliters below which a warning is issued
    
    Example:
        # Check inventory status with 5ml low threshold
        submit_check_inventory_job(low_threshold_ml=5.0)
    """
    print(f"Submitting inventory status check (low threshold: {low_threshold_ml}ml)...")
    
    run_deployment(
        name="check-inventory-status/check-inventory-status",
        parameters={"low_threshold_ml": low_threshold_ml},
    )
    print("Inventory check job submitted to monitoring queue")


def submit_initialize_inventory_job(red_ml=15, yellow_ml=15, blue_ml=15, evaporation_rate=5.0):
    """
    Submit an inventory initialization job.
    
    WARNING: This will reset the inventory to the specified starting volumes.
    Only use this for initial setup or when completely restocking all colors.
    
    Parameters:
    - red_ml: Initial red paint volume in milliliters
    - yellow_ml: Initial yellow paint volume in milliliters
    - blue_ml: Initial blue paint volume in milliliters
    - evaporation_rate: Evaporation rate in ul/hour
    
    Example:
        # Initialize with 15ml of each color
        submit_initialize_inventory_job(red_ml=15, yellow_ml=15, blue_ml=15)
    """
    # Convert milliliters to microliters
    red_ul = int(red_ml * 1000)
    yellow_ul = int(yellow_ml * 1000)
    blue_ul = int(blue_ml * 1000)
    
    print("⚠️  WARNING: This will reset the inventory system!")
    print(f"Initial volumes: Red={red_ml}ml, Yellow={yellow_ml}ml, Blue={blue_ml}ml")
    print(f"Evaporation rate: {evaporation_rate} ul/hour")
    
    run_deployment(
        name="initialize-inventory/initialize-inventory",
        parameters={
            "red_volume": red_ul,
            "yellow_volume": yellow_ul,
            "blue_volume": blue_ul,
            "evaporation_rate": evaporation_rate,
        },
    )
    print("Initialization job submitted to maintenance queue")


def run_maintenance_workflow():
    """
    Run a complete maintenance workflow:
    1. Check current inventory status
    2. Restock colors as needed
    3. Verify inventory after restock
    """
    print("=" * 60)
    print("Starting maintenance workflow...")
    print("=" * 60)
    
    # Step 1: Check current status
    print("\nStep 1: Checking current inventory status...")
    submit_check_inventory_job(low_threshold_ml=5.0)
    
    # Step 2: Restock colors (example - adjust volumes as needed)
    print("\nStep 2: Restocking colors...")
    submit_restock_job(
        red_ml=10,
        yellow_ml=10,
        blue_ml=10,
        operator="maintenance_workflow",
    )
    
    # Step 3: Verify inventory after restock
    print("\nStep 3: Verifying inventory after restock...")
    submit_check_inventory_job(low_threshold_ml=5.0)
    
    print("\n" + "=" * 60)
    print("Maintenance workflow submitted successfully!")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            # Check inventory status
            threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
            submit_check_inventory_job(low_threshold_ml=threshold)
        
        elif command == "restock":
            # Restock operation
            # Usage: python orchestrator_restock.py restock <red_ml> <yellow_ml> <blue_ml> <operator>
            red = float(sys.argv[2]) if len(sys.argv) > 2 else 0
            yellow = float(sys.argv[3]) if len(sys.argv) > 3 else 0
            blue = float(sys.argv[4]) if len(sys.argv) > 4 else 0
            operator = sys.argv[5] if len(sys.argv) > 5 else "system"
            submit_restock_job(red_ml=red, yellow_ml=yellow, blue_ml=blue, operator=operator)
        
        elif command == "initialize":
            # Initialize inventory
            # Usage: python orchestrator_restock.py initialize <red_ml> <yellow_ml> <blue_ml>
            red = float(sys.argv[2]) if len(sys.argv) > 2 else 15
            yellow = float(sys.argv[3]) if len(sys.argv) > 3 else 15
            blue = float(sys.argv[4]) if len(sys.argv) > 4 else 15
            submit_initialize_inventory_job(red_ml=red, yellow_ml=yellow, blue_ml=blue)
        
        elif command == "maintenance":
            # Run full maintenance workflow
            run_maintenance_workflow()
        
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python orchestrator_restock.py check [threshold_ml]")
            print("  python orchestrator_restock.py restock <red_ml> <yellow_ml> <blue_ml> [operator]")
            print("  python orchestrator_restock.py initialize [red_ml] [yellow_ml] [blue_ml]")
            print("  python orchestrator_restock.py maintenance")
    
    else:
        # Default: run examples
        print("=" * 60)
        print("Example 1: Check Inventory Status")
        print("=" * 60)
        submit_check_inventory_job(low_threshold_ml=5.0)
        
        print("\n" + "=" * 60)
        print("Example 2: Restock Operation")
        print("=" * 60)
        submit_restock_job(
            red_ml=10,
            yellow_ml=5,
            blue_ml=8,
            operator="lab_technician_demo"
        )
        
        print("\n" + "=" * 60)
        print("Example 3: Full Maintenance Workflow")
        print("=" * 60)
        print("To run full maintenance workflow, use:")
        print("  python orchestrator_restock.py maintenance")
