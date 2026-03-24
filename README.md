# Humanoid Retarget (Godot Compatible)

**Humanoid Retarget** is a specialized Blender tool designed to simplify the process of remapping, aligning, and retargeting animations between different humanoid armatures. It is particularly optimized for **Godot Engine**'s humanoid bone naming conventions but flexible enough for any humanoid rig.

## 🚀 Key Features

* **Smart Auto-Detection**: Uses advanced geometric analysis and vertex group data to automatically map your source and target bones.
* **One-Click Pose Alignment**: Instantly aligns a target armature's pose to match a source armature's orientation, solving the "T-Pose vs. A-Pose" discrepancy.
* **Safe Rest Pose Application**: Applies the current pose as the new Rest Pose while automatically adjusting associated meshes so they don't distort or "explode."
* **Edit-Mode Bone Roll Copy**: Synchronizes local bone axes between armatures while preserving the world-space position of child objects (e.g., weapons, accessories).
* **Advanced Symmetry Logic**: Intelligently identifies Left/Right pairs and maps them based on naming differences, avoiding common "LowerLeg" to "RowerReg" replacement bugs.
* **JSON Import/Export**: Save and load your bone mapping configurations to reuse across different projects.

---

## 🛠 Installation

1.  Download the `blender_humanoid_retarget.py` file.
2.  Open Blender, go to **Edit > Preferences > Add-ons**.
3.  Click **Install...** and select the `.py` file.
4.  Enable the add-on: **Animation: Humanoid Retarget (Godot Compatible)**.
5.  Find the panel in the **3D View Sidebar (N-panel)** under the **Humanoid** tab.

---

## 📖 How to Use

### 1. Bone Mapping
1.  Select your **Source Armature** (the one with the animation) and **Target Armature** (the one you want to fix).
2.  **Auto-Detect**: Click `Detect Source/Target by Hips`. The plugin will analyze the bone hierarchy starting from the Hips to fill the mapping list.
3.  **Manual Tweak**: If any bone is missed, use the search box in the list to manually assign it.

### 2. Aligning the Pose
If your target model is in a different pose (e.g., Source is T-Pose, Target is A-Pose):
1.  Click **Align Target Pose (Godot)**. 
2.  The plugin will calculate the rotational difference between the bone chains and snap the target bones into precise alignment with the source.

### 3. Setting a New Rest Pose
To make the current alignment permanent:
1.  Select the **Target Armature**.
2.  Click **Apply Rest Pose (Keep Mesh)**.
3.  *Note:* The plugin applies the mesh modifiers, updates the armature's rest pose, and re-adds the modifiers automatically to ensure zero visual distortion.

### 4. Correcting Bone Rolls
To ensure your local X/Y/Z axes match the source (crucial for clean rotation math):
1.  Click **Copy Bone Roll & Keep Children**.
2.  This aligns the Edit-Mode bones while ensuring any objects parented to the armature stay in their exact world-space positions.

---

## 📄 License
Authored by **D3ZAX**. Licensed under the MIT License. Feel free to use it in your game development workflow!