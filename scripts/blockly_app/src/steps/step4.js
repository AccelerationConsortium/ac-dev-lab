/**
 * Blockly OT-2 Integration Application
 * 
 * This application demonstrates real Blockly installation with custom blocks
 * for OT-2 liquid handler functions from OT2mqtt.py
 */

import * as Blockly from 'blockly';
import {pythonGenerator} from 'blockly/python';

// Define custom block: OT-2 Home
Blockly.Blocks['ot2_home'] = {
  init: function() {
    this.appendDummyInput()
        .appendField('🏠 OT-2: Home Robot');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(230);
    this.setTooltip('Home the OT-2 robot to its initial position');
    this.setHelpUrl('');
  }
};

pythonGenerator.forBlock['ot2_home'] = function(block, generator) {
  const code = 'protocol.home()\n';
  return code;
};

// Define custom block: OT-2 Mix Color
Blockly.Blocks['ot2_mix_color'] = {
  init: function() {
    this.appendDummyInput()
        .appendField('🎨 OT-2: Mix Color');
    this.appendValueInput('R')
        .setCheck('Number')
        .appendField('Red (µL)');
    this.appendValueInput('Y')
        .setCheck('Number')
        .appendField('Yellow (µL)');
    this.appendValueInput('B')
        .setCheck('Number')
        .appendField('Blue (µL)');
    this.appendValueInput('WELL')
        .setCheck('String')
        .appendField('Well');
    this.appendValueInput('SESSION_ID')
        .setCheck('String')
        .appendField('Session ID');
    this.appendValueInput('EXPERIMENT_ID')
        .setCheck('String')
        .appendField('Experiment ID');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(230);
    this.setTooltip('Mix RGB colors in a well using the OT-2 pipette');
    this.setHelpUrl('');
  }
};

pythonGenerator.forBlock['ot2_mix_color'] = function(block, generator) {
  const value_r = generator.valueToCode(block, 'R', pythonGenerator.ORDER_ATOMIC) || '0';
  const value_y = generator.valueToCode(block, 'Y', pythonGenerator.ORDER_ATOMIC) || '0';
  const value_b = generator.valueToCode(block, 'B', pythonGenerator.ORDER_ATOMIC) || '0';
  const value_well = generator.valueToCode(block, 'WELL', pythonGenerator.ORDER_ATOMIC) || '"A1"';
  const value_session_id = generator.valueToCode(block, 'SESSION_ID', pythonGenerator.ORDER_ATOMIC) || '"session_001"';
  const value_experiment_id = generator.valueToCode(block, 'EXPERIMENT_ID', pythonGenerator.ORDER_ATOMIC) || '"exp_001"';
  
  const code = `payload = {
    "command": {
        "R": ${value_r},
        "Y": ${value_y},
        "B": ${value_b},
        "well": ${value_well}
    },
    "session_id": ${value_session_id},
    "experiment_id": ${value_experiment_id}
}
mix_color(payload)
`;
  return code;
};

// Define custom block: OT-2 Move Sensor Back
Blockly.Blocks['ot2_move_sensor_back'] = {
  init: function() {
    this.appendDummyInput()
        .appendField('↩️ OT-2: Move Sensor Back');
    this.appendValueInput('SENSOR_STATUS')
        .setCheck('String')
        .appendField('Sensor Status');
    this.appendValueInput('SESSION_ID')
        .setCheck('String')
        .appendField('Session ID');
    this.appendValueInput('EXPERIMENT_ID')
        .setCheck('String')
        .appendField('Experiment ID');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(230);
    this.setTooltip('Move the sensor back to charging position');
    this.setHelpUrl('');
  }
};

pythonGenerator.forBlock['ot2_move_sensor_back'] = function(block, generator) {
  const value_sensor_status = generator.valueToCode(block, 'SENSOR_STATUS', pythonGenerator.ORDER_ATOMIC) || '"complete"';
  const value_session_id = generator.valueToCode(block, 'SESSION_ID', pythonGenerator.ORDER_ATOMIC) || '"session_001"';
  const value_experiment_id = generator.valueToCode(block, 'EXPERIMENT_ID', pythonGenerator.ORDER_ATOMIC) || '"exp_001"';
  
  const code = `payload = {
    "command": {
        "sensor_status": ${value_sensor_status}
    },
    "session_id": ${value_session_id},
    "experiment_id": ${value_experiment_id}
}
move_sensor_back(payload)
`;
  return code;
};

// Create toolbox
const toolbox = {
  "kind": "categoryToolbox",
  "contents": [
    {
      "kind": "category",
      "name": "OT-2 Commands",
      "colour": "#5C81A6",
      "contents": [
        {
          "kind": "block",
          "type": "ot2_home"
        },
        {
          "kind": "block",
          "type": "ot2_mix_color",
          "inputs": {
            "R": {
              "shadow": {
                "type": "math_number",
                "fields": {
                  "NUM": 100
                }
              }
            },
            "Y": {
              "shadow": {
                "type": "math_number",
                "fields": {
                  "NUM": 50
                }
              }
            },
            "B": {
              "shadow": {
                "type": "math_number",
                "fields": {
                  "NUM": 75
                }
              }
            },
            "WELL": {
              "shadow": {
                "type": "text",
                "fields": {
                  "TEXT": "A1"
                }
              }
            },
            "SESSION_ID": {
              "shadow": {
                "type": "text",
                "fields": {
                  "TEXT": "session_001"
                }
              }
            },
            "EXPERIMENT_ID": {
              "shadow": {
                "type": "text",
                "fields": {
                  "TEXT": "exp_001"
                }
              }
            }
          }
        },
        {
          "kind": "block",
          "type": "ot2_move_sensor_back",
          "inputs": {
            "SENSOR_STATUS": {
              "shadow": {
                "type": "text",
                "fields": {
                  "TEXT": "complete"
                }
              }
            },
            "SESSION_ID": {
              "shadow": {
                "type": "text",
                "fields": {
                  "TEXT": "session_001"
                }
              }
            },
            "EXPERIMENT_ID": {
              "shadow": {
                "type": "text",
                "fields": {
                  "TEXT": "exp_001"
                }
              }
            }
          }
        }
      ]
    },
    {
      "kind": "category",
      "name": "Logic",
      "colour": "#5C68A6",
      "contents": [
        {
          "kind": "block",
          "type": "controls_if"
        },
        {
          "kind": "block",
          "type": "logic_compare"
        }
      ]
    },
    {
      "kind": "category",
      "name": "Loops",
      "colour": "#5CA65C",
      "contents": [
        {
          "kind": "block",
          "type": "controls_repeat_ext",
          "inputs": {
            "TIMES": {
              "shadow": {
                "type": "math_number",
                "fields": {
                  "NUM": 3
                }
              }
            }
          }
        },
        {
          "kind": "block",
          "type": "controls_whileUntil"
        }
      ]
    },
    {
      "kind": "category",
      "name": "Math",
      "colour": "#5C68A6",
      "contents": [
        {
          "kind": "block",
          "type": "math_number"
        },
        {
          "kind": "block",
          "type": "math_arithmetic"
        }
      ]
    },
    {
      "kind": "category",
      "name": "Text",
      "colour": "#5CA68A",
      "contents": [
        {
          "kind": "block",
          "type": "text"
        },
        {
          "kind": "block",
          "type": "text_print"
        }
      ]
    },
    {
      "kind": "category",
      "name": "Variables",
      "colour": "#A65C81",
      "custom": "VARIABLE"
    }
  ]
};

// Initialize Blockly workspace
const workspace = Blockly.inject('blocklyDiv', {
  toolbox: toolbox,
  grid: {
    spacing: 20,
    length: 3,
    colour: '#ccc',
    snap: true
  },
  zoom: {
    controls: true,
    wheel: true,
    startScale: 1.0,
    maxScale: 3,
    minScale: 0.3,
    scaleSpeed: 1.2
  },
  trashcan: true
});

// Load initial workspace

// Load initial workspace - Step 4: Home + Repeat + Mix Color
const startBlocks = {
  "blocks": {
    "languageVersion": 0,
    "blocks": [
      {
        "type": "ot2_home",
        "id": "start_home",
        "x": 50,
        "y": 50
      },
      {
        "type": "controls_repeat_ext",
        "id": "repeat_loop",
        "x": 50,
        "y": 120,
        "inputs": {
          "TIMES": {
            "shadow": {
              "type": "math_number",
              "id": "repeat_times",
              "fields": {
                "NUM": 3
              }
            }
          },
          "DO": {
            "block": {
              "type": "ot2_mix_color",
              "id": "mix_block",
              "inputs": {
                "R": {
                  "shadow": {
                    "type": "math_number",
                    "fields": {
                      "NUM": 100
                    }
                  }
                },
                "Y": {
                  "shadow": {
                    "type": "math_number",
                    "fields": {
                      "NUM": 50
                    }
                  }
                },
                "B": {
                  "shadow": {
                    "type": "math_number",
                    "fields": {
                      "NUM": 75
                    }
                  }
                },
                "WELL": {
                  "shadow": {
                    "type": "text",
                    "fields": {
                      "TEXT": "A1"
                    }
                  }
                },
                "SESSION_ID": {
                  "shadow": {
                    "type": "text",
                    "fields": {
                      "TEXT": "session_001"
                    }
                  }
                },
                "EXPERIMENT_ID": {
                  "shadow": {
                    "type": "text",
                    "fields": {
                      "TEXT": "exp_001"
                    }
                  }
                }
              }
            }
          }
        }
      }
    ]
  }
};

Blockly.serialization.workspaces.load(startBlocks, workspace);

// Generate code function
function generateCode() {
  const code = pythonGenerator.workspaceToCode(workspace);
  const fullCode = `# Generated from Blockly visual programming
# This code uses functions from OT2mqtt.py

from OT2mqtt import mix_color, move_sensor_back, protocol

# Main workflow
${code}`;
  
  document.getElementById('codeOutput').textContent = fullCode;
}

// Update code on workspace change
workspace.addChangeListener(generateCode);

// Generate initial code
generateCode();

// Expose generate function to button
window.generateCode = generateCode;
