// game.js
// Constants with corrected dimensions
const TILE_SIZE = 64;
const GRID_WIDTH = 5; // X-coordinate (columns)
const GRID_HEIGHT = 12; // Y-coordinate (rows)
const GAME_WIDTH = GRID_WIDTH * TILE_SIZE;
const GAME_HEIGHT = GRID_HEIGHT * TILE_SIZE;

// Game object classes
class GameObject {
  constructor(id, position, sprite) {
    this.id = id;
    this.position = position; // [x, y] where x is column and y is row
    this.sprite = sprite;
  }
}

class Castle extends GameObject {
  constructor(id, ally, position, sprite) {
    super(id, position, sprite);
    this.ally = ally;
  }
}

class Wall extends GameObject {
  constructor(id, position, sprite) {
    super(id, position, sprite);
  }
}

class Unit extends GameObject {
  constructor(id, ally, name, isRanged, fighterType, position, sprite) {
    super(id, position, sprite);
    this.ally = ally;
    this.name = name;
    this.isRanged = isRanged;
    this.fighterType = fighterType;
    this.isMoving = false;
    this.targetPosition = null;
    this.shadow = null;
    this.glowEffect = null;
    this.isHovered = false;
    this.isSelected = false;
  }
}

// Main game class
class MedievalGame {
  constructor() {
    this.config = {
      type: Phaser.AUTO,
      width: GAME_WIDTH,
      height: GAME_HEIGHT,
      parent: "game",
      scene: {
        preload: this.preload.bind(this),
        create: this.create.bind(this),
        update: this.update.bind(this),
      },
    };

    this.game = new Phaser.Game(this.config);
    this.gameObjects = {};
    this.scene = null;
  }

  preload() {
    this.scene = this.game.scene.scenes[0];

    // Load assets
    this.scene.load.image("ground", "img/grass.png");
    this.scene.load.image("castle-ally", "img/castle.png");
    this.scene.load.image("castle-enemy", "img/castle.png");
    this.scene.load.image("wall", "img/wall.png");
    this.scene.load.image("knight", "img/knight.png");
    this.scene.load.image("archer", "img/archer.png");
    this.scene.load.image("shadow", "img/shadow.png");
  }

  create() {
    // Create ground
    const ground = this.scene.add.tileSprite(
      GAME_WIDTH / 2,
      GAME_HEIGHT / 2,
      GAME_WIDTH,
      GAME_HEIGHT,
      "ground"
    );

    // Create grid for debugging
    const gridGraphics = this.scene.add.graphics();
    gridGraphics.lineStyle(1, 0xffffff, 0.2);

    // Draw horizontal lines
    for (let y = 0; y <= GRID_HEIGHT; y++) {
      gridGraphics.moveTo(0, y * TILE_SIZE);
      gridGraphics.lineTo(GAME_WIDTH, y * TILE_SIZE);
    }

    // Draw vertical lines
    for (let x = 0; x <= GRID_WIDTH; x++) {
      gridGraphics.moveTo(x * TILE_SIZE, 0);
      gridGraphics.lineTo(x * TILE_SIZE, GAME_HEIGHT);
    }

    gridGraphics.strokePath();

    // Initialize game objects
    this.createInitialObjects();

    // Setup HUD
    this.setupHUD();
  }

  update() {
    // Update unit animations and movements
    Object.values(this.gameObjects).forEach((obj) => {
      if (obj instanceof Unit) {
        // Update glow effects
        this.updateUnitGlow(obj);
      }
    });
  }

  createInitialObjects() {
    // Edit this to create more/different objects
    // Create castles - positions are now [x, y] = [column, row]
    this.createCastle("Castle1", true, [2, 0]);
    this.createCastle("Castle2", false, [2, 10]);

    // Create knights
    this.createUnit("Knight1", true, "Roland", false, "knight", [0, 1]);
    this.createUnit("Knight2", true, "Hugo", false, "knight", [1, 1]);
    this.createUnit("Knight3", true, "Edric", false, "knight", [3, 1]);

    // Create archer
    this.createUnit("Archer1", true, "Owen", true, "archer", [4, 1]);

    // Create walls
    this.createWall("Wall1", [1, 5]);
    this.createWall("Wall2", [3, 6]);
  }

  createCastle(id, ally, position) {
    const sprite = this.scene.add.sprite(
      this.gridToPixelX(position[0]),
      this.gridToPixelY(position[1]),
      ally ? "castle-ally" : "castle-enemy"
    );
    sprite.setScale(0.12);
    sprite.setDepth(GRID_HEIGHT - position[1]); // Set depth

    this.gameObjects[id] = new Castle(id, ally, position, sprite);
  }

  createWall(id, position) {
    const sprite = this.scene.add.sprite(
      this.gridToPixelX(position[0]),
      this.gridToPixelY(position[1]),
      "wall"
    );
    sprite.setScale(0.12);
    sprite.setDepth(GRID_HEIGHT - position[1]); // Set depth

    this.gameObjects[id] = new Wall(id, position, sprite);
  }

  createUnit(id, ally, name, isRanged, fighterType, position) {
    const sprite = this.scene.add.sprite(
      this.gridToPixelX(position[0]),
      this.gridToPixelY(position[1]),
      fighterType === "knight" ? "knight" : "archer"
    );

    sprite.setScale(fighterType === "knight" ? 0.08 : 0.066);

    // Create shadow
    const shadow = this.scene.add.image(
      this.gridToPixelX(position[0]),
      this.gridToPixelY(position[1]) + 25,
      "shadow"
    );
    shadow.setScale(0.1);
    shadow.setAlpha(0.4);

    // Create glow effect
    const glowEffect = this.scene.add.graphics();
    this.updateGlowGraphics(glowEffect, position, false, false);
    // Set initial depth based on y position (smaller y = higher depth)
    const depth = GRID_HEIGHT - position[1]; // Invert y for depth
    sprite.setDepth(depth);
    shadow.setDepth(depth - 0.1); // Shadow slightly below unit
    glowEffect.setDepth(depth - 0.2); // Glow below shadow

    const unit = new Unit(
      id,
      ally,
      name,
      isRanged,
      fighterType,
      position,
      sprite
    );
    unit.shadow = shadow;
    unit.glowEffect = glowEffect;

    this.gameObjects[id] = unit;
  }

  updateGlowGraphics(graphics, position, isHovered, isSelected) {
    const x = this.gridToPixelX(position[0]);
    const y = this.gridToPixelY(position[1]);
    const radius = 35;

    // Clear previous graphics
    graphics.clear();

    if (isHovered || isSelected) {
      // Set color based on state (cyan for hover, green for selected)
      const color = isSelected ? 0x00ff00 : 0x00ffff;
      const alpha = 0.5;

      // Draw glow circle
      graphics.fillStyle(color, alpha);
      graphics.fillCircle(x, y, radius);

      // Draw stroke
      graphics.lineStyle(2, color, 0.8);
      graphics.strokeCircle(x, y, radius);
    }
  }

  updateUnitGlow(unit) {
    if (unit.glowEffect) {
      this.updateGlowGraphics(
        unit.glowEffect,
        unit.position,
        unit.isHovered,
        unit.isSelected
      );
    }
  }

  // Convert grid coordinates to pixel coordinates
  gridToPixelX(gridX) {
    return gridX * TILE_SIZE + TILE_SIZE / 2;
  }

  gridToPixelY(gridY) {
    // Invert Y to make (0,0) the bottom-left corner
    return (GRID_HEIGHT - gridY - 1) * TILE_SIZE + TILE_SIZE / 2;
  }

  setupHUD() {
    // Function select change handler
    const functionSelect = document.getElementById("function-select");
    functionSelect.addEventListener("change", () => {
      const directionParams = document.getElementById("direction-params");
      const targetParams = document.getElementById("target-params");

      if (functionSelect.value === "moveDirection") {
        directionParams.style.display = "flex";
        targetParams.style.display = "none";
      } else {
        directionParams.style.display = "none";
        targetParams.style.display = "flex";
      }
    });

    // Populate unit checkboxes
    const unitCheckboxes = document.getElementById("unit-checkboxes");
    Object.values(this.gameObjects).forEach((obj) => {
      if (obj instanceof Unit) {
        const label = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = obj.id;

        const labelText = document.createTextNode(
          ` ${obj.name} (${obj.fighterType})`
        );

        label.appendChild(checkbox);
        label.appendChild(labelText);
        unitCheckboxes.appendChild(label);

        // Add hover event
        label.addEventListener("mouseenter", () => {
          obj.isHovered = true;
        });

        label.addEventListener("mouseleave", () => {
          obj.isHovered = false;
        });

        // Add selection event
        checkbox.addEventListener("change", (e) => {
          obj.isSelected = e.target.checked;
        });
      }
    });

    // Populate target dropdown
    const targetSelect = document.getElementById("target-select");
    Object.values(this.gameObjects).forEach((obj) => {
      if (!(obj instanceof Unit)) {
        const option = document.createElement("option");
        option.value = obj.id;
        option.textContent = obj.id;
        targetSelect.appendChild(option);
      }
    });

    // Go button click handler
    const goButton = document.getElementById("go-button");
    goButton.addEventListener("click", () => {
      const functionType = functionSelect.value;

      // Get selected units
      const selectedUnits = [];
      const checkboxes = unitCheckboxes.querySelectorAll(
        'input[type="checkbox"]:checked'
      );
      checkboxes.forEach((checkbox) => {
        selectedUnits.push(checkbox.value);
      });

      if (selectedUnits.length === 0) {
        alert("Please select at least one unit");
        return;
      }

      if (functionType === "moveDirection") {
        const xDelta = parseInt(document.getElementById("x-delta").value);
        const yDelta = parseInt(document.getElementById("y-delta").value);
        this.moveDirection(selectedUnits, xDelta, yDelta);
      } else {
        const targetId = targetSelect.value;
        this.moveTarget(selectedUnits, targetId);
      }

      // Log game world
      this.logGameWorld();
    });
  }

  moveDirection(unitIds, xDelta, yDelta) {
    unitIds.forEach((unitId) => {
      const unit = this.gameObjects[unitId];
      if (unit && unit instanceof Unit) {
        const currentPos = unit.position;
        const targetPos = [
          Math.max(0, Math.min(GRID_WIDTH - 1, currentPos[0] + xDelta)),
          Math.max(0, Math.min(GRID_HEIGHT - 1, currentPos[1] + yDelta)),
        ];

        this.moveUnitToPosition(unit, targetPos);
      }
    });
  }

  moveTarget(unitIds, targetId) {
    const target = this.gameObjects[targetId];
    if (!target) return;

    unitIds.forEach((unitId) => {
      const unit = this.gameObjects[unitId];
      if (unit && unit instanceof Unit) {
        this.moveUnitToPosition(unit, target.position);
      }
    });
  }

  moveUnitToPosition(unit, targetPos) {
    // Don't move if already moving
    if (unit.isMoving) {
      return;
    }

    // Create a direct linear path
    const startPos = [...unit.position];
    let endPos = [...targetPos];

    // Check if target is occupied
    const isTargetOccupied = Object.values(this.gameObjects).some((obj) => {
      // Skip the current unit when checking
      if (obj.id === unit.id) return false;

      // Check if any object is at the target position
      return obj.position[0] === endPos[0] && obj.position[1] === endPos[1];
    });

    // If target is occupied, adjust the end position to be near the target
    if (isTargetOccupied) {
      // Calculate direction vector
      const dx = endPos[0] - startPos[0];
      const dy = endPos[1] - startPos[1];

      // Calculate distance to target
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance > 0.5) {
        // Normalize direction
        const nx = dx / distance;
        const ny = dy / distance;

        // Move 0.5 tiles less in that direction
        endPos = [
          startPos[0] + nx * (distance - 0.5),
          startPos[1] + ny * (distance - 0.5),
        ];
      } else {
        // If we're already very close, don't move
        return;
      }
    }

    // Don't move if already at target or adjusted position
    if (
      Math.abs(unit.position[0] - endPos[0]) < 0.1 &&
      Math.abs(unit.position[1] - endPos[1]) < 0.1
    ) {
      return;
    }

    unit.isMoving = true;
    unit.targetPosition = endPos;

    // Set the final position for the tween animation
    const targetX = this.gridToPixelX(endPos[0]);
    const targetY = this.gridToPixelY(endPos[1]);

    // Determine flip direction based on horizontal movement
    if (endPos[0] > unit.position[0]) {
      unit.sprite.setFlipX(false); // Moving right
    } else if (endPos[0] < unit.position[0]) {
      unit.sprite.setFlipX(true); // Moving left
    }

    // Calculate duration based on distance (faster for shorter distances)
    const dx = endPos[0] - startPos[0];
    const dy = endPos[1] - startPos[1];
    const distance = Math.sqrt(dx * dx + dy * dy);
    const duration = Math.max(500, distance * 300); // Minimum 500ms, scales with distance

    // Start bouncing animation
    this.scene.tweens.add({
      targets: unit.sprite,
      y: "-=10",
      duration: 300,
      yoyo: true,
      repeat: -1,
    });

    // Create animation for continuous movement
    this.scene.tweens.add({
      targets: unit.sprite,
      x: targetX,
      y: targetY,
      duration: duration,
      ease: "Linear",
      onUpdate: (tween) => {
        // Update unit's logical position based on sprite position
        const progress = tween.progress;
        unit.position = [
          startPos[0] + (endPos[0] - startPos[0]) * progress,
          startPos[1] + (endPos[1] - startPos[1]) * progress,
        ];

        // Update depth based on current y position
        const depth = GRID_HEIGHT - unit.position[1];
        unit.sprite.setDepth(depth);
        unit.shadow.setDepth(depth - 0.1);
        unit.glowEffect.setDepth(depth - 0.2);

        // Update shadow position
        unit.shadow.x = unit.sprite.x;
        unit.shadow.y = unit.sprite.y + 20;

        // Update glow effect position
        if (unit.glowEffect) {
          this.updateGlowGraphics(
            unit.glowEffect,
            unit.position,
            unit.isHovered,
            unit.isSelected
          );
        }
      },
      onComplete: () => {
        // Set final position exactly
        unit.position = [...endPos];

        // Stop movement and animation
        unit.isMoving = false;
        this.scene.tweens.killTweensOf(unit.sprite);

        // Update shadow position one final time
        unit.shadow.x = unit.sprite.x;
        unit.shadow.y = unit.sprite.y + 20;
      },
    });
  }

  updateUnitMovement(unit) {
    if (unit.path.length === 0) {
      // Path complete
      unit.isMoving = false;

      // Stop bouncing animation
      this.scene.tweens.killTweensOf(unit.sprite);

      // Set position exactly
      unit.sprite.x = this.gridToPixelX(unit.position[0]);
      unit.sprite.y = this.gridToPixelY(unit.position[1]);
      unit.shadow.x = unit.sprite.x;
      unit.shadow.y = unit.sprite.y + 20;
      return;
    }

    // Get next position
    const nextPos = unit.path[0];

    // Check for blocking units (already moving units in the way)
    // this is disabled for now (units can overlap)
    // let blocked = false;
    // Object.values(this.gameObjects).forEach((obj) => {
    //   if (obj instanceof Unit && obj !== unit && obj.isMoving) {
    //     if (obj.position[0] === nextPos[0] && obj.position[1] === nextPos[1]) {
    //       blocked = true;
    //     }
    //   }
    // });

    // if (blocked) {
    //   // Wait for other unit to move
    //   return;
    // }

    // Move to next position
    const nextPosition = unit.path.shift();

    // Update direction
    if (nextPosition[0] > unit.position[0]) {
      unit.sprite.setFlipX(false); // Moving right
    } else if (nextPosition[0] < unit.position[0]) {
      unit.sprite.setFlipX(true); // Moving left
    }

    // Update position
    unit.position = nextPosition;

    // Calculate target pixel coordinates
    const targetX = this.gridToPixelX(nextPosition[0]);
    const targetY = this.gridToPixelY(nextPosition[1]);

    // Animate sprite with smoother movement
    this.scene.tweens.add({
      targets: unit.sprite,
      x: targetX,
      y: targetY,
      duration: 300, // Faster animation for smoother movement
      ease: "Power1", // A smoother easing function
      onComplete: () => {
        // Update shadow position with slight delay for bouncing effect
        this.scene.tweens.add({
          targets: unit.shadow,
          x: targetX,
          y: targetY + 20,
          duration: 150,
          ease: "Power1",
        });
      },
    });

    // Move glow effect immediately
    if (unit.glowEffect) {
      this.updateGlowGraphics(
        unit.glowEffect,
        unit.position,
        unit.isHovered,
        unit.isSelected
      );
    }
  }

  logGameWorld() {
    console.log("=== Game World State ===");
    Object.values(this.gameObjects).forEach((obj) => {
      if (obj instanceof Castle) {
        console.log(
          `=======\nObjectID: ${obj.id}\nally: ${obj.ally}\nposition: (${obj.position[0]}, ${obj.position[1]})`
        );
      } else if (obj instanceof Unit) {
        console.log(
          `=======\nObjectID: ${obj.id}\nally: ${obj.ally}\nname: ${obj.name}\nisRanged: ${obj.isRanged}\nfighterType: "${obj.fighterType}"\nposition: (${obj.position[0]}, ${obj.position[1]})`
        );
      } else if (obj instanceof Wall) {
        console.log(
          `=======\nObjectID: ${obj.id}\nposition: (${obj.position[0]}, ${obj.position[1]})`
        );
      }
    });
    console.log("=======");
  }
}

let medievalGame;
// Initialize the game when the page loads
window.onload = () => {
  medievalGame = new MedievalGame();
};

const apiEndpoint = "localhost:5000/api/";

// Convert gameObjects to a JSON-serializable format
const getGameObjectsForServer = (gameState) => {
  const gameObjectsData = Object.values(gameState.gameObjects).map((obj) => {
    const baseData = {
      id: obj.id,
      type: obj instanceof Unit ? "unit" : "structure", // Differentiate units vs structures
      position: obj.position,
    };

    if (obj instanceof Castle) {
      return {
        ...baseData,
        ally: obj.ally,
      };
    } else if (obj instanceof Wall) {
      return baseData; // Wall has no extra properties
    } else if (obj instanceof Unit) {
      return {
        ...baseData,
        ally: obj.ally,
        name: obj.name,
        isRanged: obj.isRanged,
        fighterType: obj.fighterType,
      };
    }
    return baseData; // Fallback for plain GameObject
  });
  return gameObjectsData;
};

document.addEventListener("DOMContentLoaded", () => {
  const commandInput = document.getElementById("command-input");
  const submitButton = document.getElementById("submit-command");
  const commandStatus = document.getElementById("command-status");

  // submit command used by submit button, and record button
  const submitCommand = async () => {
    const command = commandInput.value.trim();
    if (!command) return;

    commandStatus.textContent = "Loading...";
    submitButton.disabled = true;

    try {
      // Send the command with game objects
      const gameObjectsData = getGameObjectsForServer(medievalGame);
      const response = await fetch(apiEndpoint + "command", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          command: command,
          gameObjects: gameObjectsData,
        }),
      });

      if (!response.ok) {
        throw new Error("Server error");
      }
      const data = await response.json();
      console.log("command response", data);

      const result = data.result;
      result.forEach((commandData) => {
        console.log("processing agent command", commandData);
        if (commandData.name === "move_to_target") {
          const { unit_ids, target_id } = commandData.args;
          medievalGame.moveTarget(unit_ids, target_id);
        } else if (commandData.name === "move_in_direction") {
          const { unit_ids, x_delta, y_delta } = commandData.args;
          medievalGame.moveDirection(unit_ids, x_delta, y_delta);
        }
      });

      commandStatus.textContent = "Success!";
    } catch (error) {
      console.log("error:", error);
      commandStatus.textContent = "Error!";
    } finally {
      submitButton.disabled = false;
    }
  };

  // submit button is easy
  submitButton.addEventListener("click", submitCommand);

  // Voice recognition
  window.SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!window.SpeechRecognition) {
    alert("your browser does not support the Web Speech API");
  } else {
    // Initialize speech recognition
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    // Get record button elements
    const recordBtn = document.getElementById("record-btn");

    // Variables
    let finalTranscript = "";
    let isRecording = false;

    // Toggle recording function
    function toggleRecording() {
      if (!isRecording) {
        finalTranscript = ""; // Reset transcript
        recognition.start();
        recordBtn.textContent = "Stop Recording";
        commandStatus.textContent = "Recording... (Speak now)";
        submitButton.disabled = true;
        isRecording = true;
      } else {
        recognition.stop();
        recordBtn.textContent = "Record";
        commandStatus.textContent = "Stopped recording";
        submitButton.disabled = false;
        isRecording = false;

        if (commandInput.value !== "") {
          console.log("submitting from voice end", commandInput.value);
          submitCommand();
        }
      }
    }

    // Event handler for speech results
    recognition.onresult = (event) => {
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0].transcript;

        if (result.isFinal) {
          finalTranscript += text + " ";
        } else {
          interimTranscript += text;
        }
      }

      commandInput.value = finalTranscript + interimTranscript;
    };

    // Button click handler
    recordBtn.onclick = toggleRecording;

    // Error handling
    recognition.onerror = (event) => {
      commandStatus.textContent = `Error: ${event.error}`;
      recordBtn.textContent = "Record";
      submitButton.disabled = false;
      isRecording = false;
    };

    // When recognition ends
    recognition.onend = () => {
      if (isRecording) {
        // Restart if it ended unexpectedly while recording
        recognition.start();
      }
    };
  }
});
