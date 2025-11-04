# Building a Blockly Workflow: Step-by-Step Guide

This guide demonstrates how to build an OT-2 automation workflow using Blockly's visual programming interface, from an empty workspace to a complete workflow with generated Python code.

## Step-by-Step Process

### Step 1: Start with Empty Workspace

![Empty Workspace - Coming Soon](https://via.placeholder.com/800x600/f0f0f0/666666?text=Step+1:+Empty+Workspace)

- Open the Blockly application
- The workspace is empty and ready for blocks
- Toolbox on the left shows available block categories:
  - OT-2 Commands
  - Logic
  - Loops
  - Math
  - Text
  - Variables

**Generated Code:**
```python
# No blocks yet...
```

---

### Step 2: Add "OT-2: Home Robot" Block

![Adding Home Block - Coming Soon](https://via.placeholder.com/800x600/f0f0f0/666666?text=Step+2:+Home+Robot+Block)

1. Click on **"OT-2 Commands"** category in toolbox
2. Drag the **"🏠 OT-2: Home Robot"** block to workspace
3. Place it at the top of your workflow

**Generated Code:**
```python
from OT2mqtt import protocol

protocol.home()
```

---

### Step 3: Add "Repeat 3 Times" Loop

![Adding Loop Block - Coming Soon](https://via.placeholder.com/800x600/f0f0f0/666666?text=Step+3:+Repeat+Loop)

1. Click on **"Loops"** category in toolbox
2. Drag the **"repeat _ times"** block to workspace
3. Change the number to `3`
4. Place it below the Home Robot block

**Generated Code:**
```python
from OT2mqtt import protocol

protocol.home()

for count in range(3):
  pass  # Loop body empty for now
```

---

### Step 4: Add "OT-2: Mix Color" Block Inside Loop

![Adding Mix Color Block - Coming Soon](https://via.placeholder.com/800x600/f0f0f0/666666?text=Step+4:+Mix+Color+Block)

1. From **"OT-2 Commands"**, drag **"🎨 OT-2: Mix Color"** block
2. Drop it inside the loop's "do" section
3. Fill in the parameters:
   - **Red (µL):** 100
   - **Yellow (µL):** 50
   - **Blue (µL):** 75
   - **Well:** A1
   - **Session ID:** session_001
   - **Experiment ID:** exp_001

**Generated Code:**
```python
from OT2mqtt import mix_color, protocol

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
```

---

### Step 5: Add "OT-2: Move Sensor Back" Block

![Adding Sensor Block - Coming Soon](https://via.placeholder.com/800x600/f0f0f0/666666?text=Step+5:+Move+Sensor+Back)

1. From **"OT-2 Commands"**, drag **"↩️ OT-2: Move Sensor Back"** block
2. Attach it below the Mix Color block (still inside the loop)
3. Fill in the parameters:
   - **Sensor Status:** complete
   - **Session ID:** session_001
   - **Experiment ID:** exp_001

**Generated Code:**
```python
from OT2mqtt import mix_color, move_sensor_back, protocol

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

---

### Step 6: Complete Workflow

![Complete Workflow](https://github.com/user-attachments/assets/e03bf195-edc8-4926-9980-170590c5fc24)

The workflow is now complete! The visual blocks on the left automatically generate the Python code on the right.

**Final Generated Code:**
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
            "well": 'A1'
        },
        "session_id": 'session_001',
        "experiment_id": 'exp_001'
    }
    mix_color(payload)
    
    payload = {
        "command": {
            "sensor_status": 'complete'
        },
        "session_id": 'session_001',
        "experiment_id": 'exp_001'
    }
    move_sensor_back(payload)
```

---

## Workflow Summary

This workflow demonstrates:

1. **Starting Simple**: Begin with a Home command
2. **Adding Control Flow**: Use loops to repeat actions
3. **Custom Functions**: Integrate OT-2 specific operations
4. **Parameter Configuration**: Set values for each operation
5. **Sequential Operations**: Chain multiple actions together
6. **Automatic Code Generation**: Python code is generated in real-time

## Key Features

✨ **Drag and Drop**: Build workflows visually without writing code  
🔄 **Real-time Updates**: Code updates as you modify blocks  
🎯 **One-to-One Mapping**: Each block directly corresponds to Python code  
🎓 **Educational**: Learn Python by seeing how blocks translate to code  
🔧 **Customizable**: Easy to modify parameters and extend with new blocks  

## Try It Yourself

```bash
cd scripts/blockly_app
npm install
npm start
```

Then open http://localhost:8080 and start building your own workflow!

---

**Note:** Screenshots for steps 1-5 show placeholders. Real screenshots will be captured from the actual Blockly application showing the progressive building of the workflow.
