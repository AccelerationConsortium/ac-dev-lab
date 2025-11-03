# OT-2 Inventory Management and Restock System

This system provides automated inventory tracking and restock maintenance for the OT-2 color mixing demo. It tracks paint stock levels, accounts for evaporation over time, and provides Prefect flows for manual restocking operations.

## Features

- **Stock Level Tracking**: Monitors red, yellow, and blue paint volumes in real-time
- **Evaporation Accounting**: Automatically subtracts evaporated volume based on elapsed time
- **Pre-Mixing Validation**: Checks stock availability before each color mixing operation
- **Automatic Stock Subtraction**: Updates inventory after each experiment
- **Manual Restock Capability**: Prefect flow for triggering restock operations
- **Inventory Status Monitoring**: Check current levels and get low-stock alerts
- **Audit Trail**: Logs all restock operations in MongoDB

## Architecture

### MongoDB Collections

1. **inventory**: Stores current stock levels for each color
   - Fields: `color_key`, `color`, `position`, `volume_ul`, `last_updated`, `evaporation_rate_ul_per_hour`

2. **restock_log**: Audit trail of all restock operations
   - Fields: `timestamp`, `operator`, `restock_data`, `operation_type`

### Prefect Flows

1. **restock-maintenance**: Manual restock operation
   - Queue: `maintenance`
   - Priority: 4
   
2. **initialize-inventory**: Initialize or reset the inventory system
   - Queue: `maintenance`
   - Priority: 4

3. **check-inventory-status**: Check current inventory and get alerts
   - Queue: `monitoring`
   - Priority: 5

4. **mix-color-with-inventory**: Color mixing with integrated inventory tracking
   - Queue: `high-priority`
   - Priority: 1

## Setup

### 1. Install Dependencies

```bash
pip install prefect pymongo pandas
```

### 2. Set Environment Variables

```bash
export MONGODB_PASSWORD="your_mongodb_password"
export blinded_connection_string="your_connection_string_with_<db_password>_placeholder"
```

### 3. Set up Work Pool and Queues

```bash
cd src/ac_training_lab/ot-2/_scripts/prefect_deploy/
python setup_work_pool.py
```

This creates:
- Work pool: `ot2-device-pool`
- Queues: `high-priority`, `standard`, `low-priority`, `maintenance`, `monitoring`

### 4. Deploy Flows

Deploy restock maintenance flows:
```bash
python deploy_restock.py
```

Deploy device flows with inventory tracking:
```bash
python device_with_inventory.py
```

### 5. Start Workers

On the OT-2 device or control computer:

```bash
# Start worker for all queues
prefect worker start --pool ot2-device-pool

# Or start workers for specific queues
prefect worker start --pool ot2-device-pool --queue high-priority
prefect worker start --pool ot2-device-pool --queue maintenance
prefect worker start --pool ot2-device-pool --queue monitoring
```

## Usage

### Initialize Inventory System

First-time setup or complete reset:

```bash
# Using Python
python orchestrator_restock.py initialize 15 15 15

# Using Prefect CLI
prefect deployment run initialize-inventory/initialize-inventory \
  --param red_volume=15000 \
  --param yellow_volume=15000 \
  --param blue_volume=15000
```

### Check Inventory Status

```bash
# Using Python
python orchestrator_restock.py check 5.0

# Using Prefect CLI
prefect deployment run check-inventory-status/check-inventory-status \
  --param low_threshold_ml=5.0
```

### Restock Operation

```bash
# Using Python (volumes in ml)
python orchestrator_restock.py restock 10 5 8 lab_tech_1

# Using Prefect CLI (volumes in ul)
prefect deployment run restock-maintenance/restock-maintenance \
  --param red_volume=10000 \
  --param yellow_volume=5000 \
  --param blue_volume=8000 \
  --param operator=lab_tech_1
```

### Run Color Mixing with Inventory Tracking

```bash
prefect deployment run mix-color-with-inventory/mix-color-with-inventory \
  --param R=120 \
  --param Y=50 \
  --param B=80 \
  --param G=0 \
  --param mix_well=B2
```

## Monitoring

### View Inventory Status Programmatically

```python
from inventory_utils import get_current_inventory

inventory = get_current_inventory()
for color_key, data in inventory.items():
    print(f"{data['color']}: {data['volume_ul']/1000:.2f} ml")
```

### Set Up Scheduled Inventory Checks

You can schedule regular inventory checks using Prefect schedules:

```python
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

# Check inventory every day at 8 AM
deployment = Deployment.build_from_flow(
    flow=check_inventory_status_flow,
    name="daily-inventory-check",
    schedule=CronSchedule(cron="0 8 * * *"),
)
deployment.apply()
```

## Configuration

### Evaporation Rate

The default evaporation rate is 5 ul/hour per color reservoir. Adjust this during initialization:

```python
initialize_inventory(
    red_volume=15000,
    yellow_volume=15000,
    blue_volume=15000,
    evaporation_rate=3.0  # Custom rate in ul/hour
)
```

### Low Stock Threshold

The default threshold for stock availability checks is 100 ul. Adjust when checking stock:

```python
check_stock_availability(
    red_volume=100,
    yellow_volume=50,
    blue_volume=80,
    threshold=200  # Custom threshold in ul
)
```

## Error Handling

### Insufficient Stock Error

If an experiment is attempted with insufficient stock, the flow will raise a `ValueError`:

```
ValueError: Insufficient stock for: yellow (available: 45.0 ul, required: 150.0 ul). 
Please restock before proceeding.
```

To resolve:
1. Check current inventory: `python orchestrator_restock.py check`
2. Restock needed colors: `python orchestrator_restock.py restock 0 10 0 operator_name`
3. Retry the experiment

## Maintenance Workflow

Complete maintenance workflow example:

```bash
# 1. Check current status
python orchestrator_restock.py check 5.0

# 2. Restock colors as needed
python orchestrator_restock.py restock 10 10 10 maintenance_team

# 3. Verify restock
python orchestrator_restock.py check 2.0

# Or run all steps together
python orchestrator_restock.py maintenance
```

## Files

- `inventory_utils.py`: Core inventory management functions
- `restock_flow.py`: Prefect flows for restock operations
- `device_with_inventory.py`: Device flows with inventory integration
- `deploy_restock.py`: Deployment script for restock flows
- `orchestrator_restock.py`: Job submission script for restock operations
- `setup_work_pool.py`: Work pool and queue setup (updated with new queues)

## Troubleshooting

### Inventory Not Initialized

Error: `Inventory not initialized for color X`

Solution: Run initialization flow first

### MongoDB Connection Error

Check environment variables:
```bash
echo $MONGODB_PASSWORD
echo $blinded_connection_string
```

### Negative Stock Levels

If stock levels become negative due to evaporation or errors, reinitialize:
```bash
python orchestrator_restock.py initialize 15 15 15
```

## Best Practices

1. **Regular Monitoring**: Schedule daily inventory checks to catch low stock early
2. **Restock Threshold**: Keep stock above 5 ml (5000 ul) for reliable operation
3. **Audit Trail**: Always provide operator name when restocking for accountability
4. **Evaporation Calibration**: Monitor actual evaporation rates and adjust if needed
5. **Pre-Class Checks**: Check inventory before lab sessions to avoid interruptions

## Integration with Existing Systems

The inventory system integrates seamlessly with existing OT-2 workflows:

- **Backward Compatible**: Original `mix_color` flow still available
- **Drop-in Replacement**: Use `mix_color_with_inventory` instead
- **Minimal Changes**: Only requires environment variables and MongoDB setup
- **Optional Usage**: Can be deployed alongside existing flows

## Future Enhancements

Potential improvements:
- Automated restock scheduling based on usage patterns
- Integration with external ordering systems
- SMS/email alerts for low stock
- Machine learning for evaporation rate prediction
- Multi-location inventory management
