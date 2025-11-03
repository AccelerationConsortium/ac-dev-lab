# Blockly OT-2 Integration Demo

This directory contains a demonstration of how [Blockly](https://developers.google.com/blockly) can be integrated with custom functions from the AC Training Lab, specifically the OT-2 liquid handler functions from `OT2mqtt.py`.

## Overview

Blockly is a visual programming library that allows users to create workflows by dragging and dropping blocks. This demo shows how to:

1. Create custom Blockly blocks that represent OT-2 functions
2. Generate Python code from visual blocks that can call functions from `OT2mqtt.py`
3. Provide a one-to-one correspondence between visual programming and Python code

## What's Included

### `blockly_ot2_demo.html`

An interactive HTML page that demonstrates:

- **Custom OT-2 Blocks**: Blocks for key functions from `OT2mqtt.py`:
  - `mix_color`: Mix RGB colors using the OT-2 pipette
  - `move_sensor_back`: Return sensor to charging position
  - `ot2_home`: Home the OT-2 robot

- **Standard Blockly Blocks**: Logic, loops, math, text, and variables for building complex workflows

- **Real-time Code Generation**: As you modify the blocks, the corresponding Python code is generated instantly

## How to Use

### Option 1: Direct Browser Access

1. Simply open `blockly_ot2_demo.html` in a web browser:
   ```bash
   # From the scripts directory
   firefox blockly_ot2_demo.html
   # or
   google-chrome blockly_ot2_demo.html
   # or
   open blockly_ot2_demo.html  # macOS
   ```

2. The page loads Blockly from a CDN, so no installation is required

### Option 2: Using Python HTTP Server

If you need to serve the file over HTTP:

```bash
# From the repository root
cd scripts
python -m http.server 8000
```

Then navigate to `http://localhost:8000/blockly_ot2_demo.html` in your browser.

## Example Workflow

The demo includes a pre-loaded example that demonstrates:

1. Homing the OT-2 robot
2. Repeating 3 times:
   - Mixing colors (100µL red, 50µL yellow, 75µL blue) in well A1
   - Moving the sensor back to charging position

This generates Python code like:

```python
# Generated from Blockly visual programming
# This code uses functions from OT2mqtt.py

from OT2mqtt import mix_color, move_sensor_back, protocol

# Main workflow
protocol.home()
for count in range(3):
  payload = {
      "command": {
          "R": 100,
          "Y": 50,
          "B": 75,
          "well": "A1"
      },
      "session_id": "session_001",
      "experiment_id": "exp_001"
  }
  mix_color(payload)
  payload = {
      "command": {
          "sensor_status": "complete"
      },
      "session_id": "session_001",
      "experiment_id": "exp_001"
  }
  move_sensor_back(payload)
```

## Extending with More Functions

To add more custom functions from `OT2mqtt.py` or other modules:

1. **Define the Block**: Add a new block definition in the JavaScript:
   ```javascript
   Blockly.Blocks['your_block_name'] = {
     init: function() {
       this.appendDummyInput()
           .appendField("Your Block Label");
       this.appendValueInput("PARAM1")
           .setCheck("Number")
           .appendField("Parameter 1");
       // Add more inputs as needed
       this.setPreviousStatement(true, null);
       this.setNextStatement(true, null);
       this.setColour(230);
       this.setTooltip("Description");
     }
   };
   ```

2. **Define Code Generation**: Add Python code generator:
   ```javascript
   Blockly.Python['your_block_name'] = function(block) {
     var value_param1 = Blockly.Python.valueToCode(block, 'PARAM1', Blockly.Python.ORDER_ATOMIC);
     var code = `your_function(${value_param1})\n`;
     return code;
   };
   ```

3. **Add to Toolbox**: Include the block in the toolbox XML

## Key Features Demonstrated

1. **Visual to Code**: One-to-one correspondence between blocks and Python code
2. **Custom Functions**: Integration with existing Python functions
3. **Composability**: Combine custom blocks with standard control flow blocks
4. **Real-time Feedback**: See generated code update as you modify blocks
5. **No Installation**: Runs directly in the browser using CDN-hosted Blockly

## Comparison with Other Tools

Like n8n, NODE-RED, and IvoryOS, Blockly provides a visual drag-and-drop interface. However, Blockly's key advantage is the direct Python code generation, making it ideal for:

- Educational purposes (learn programming visually, then see the code)
- Rapid prototyping of lab workflows
- Making automation accessible to non-programmers
- Generating reproducible Python scripts from visual designs

## Next Steps

To use this in a production environment:

1. Create a backend service that receives the generated Python code
2. Validate and sanitize the code before execution
3. Execute in a controlled environment with appropriate error handling
4. Add authentication and authorization
5. Integrate with existing MQTT broker for OT-2 communication

## References

- [Blockly Official Documentation](https://developers.google.com/blockly)
- [Blockly Getting Started Guide](https://blocklycodelabs.dev/codelabs/getting-started/index.html)
- [OT-2 Python API](https://docs.opentrons.com/v2/)
