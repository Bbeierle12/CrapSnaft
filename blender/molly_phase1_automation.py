"""
Blender automation script for Molly Phase 1 preparation
Run this script in Blender's Text Editor to automate voxelization

Usage:
1. Load your Molly model in Blender
2. Select the model object
3. Open Text Editor and run this script
4. Follow the prompts for each step
"""

import bpy
import bmesh
from mathutils import Vector

def check_3d_print_addon():
    """Check if 3D-Print Toolbox is enabled"""
    return 'object_print3d_utils' in bpy.context.preferences.addons.keys()

def position_model_at_origin():
    """Position model so belly is at Z=0"""
    obj = bpy.context.active_object
    if not obj:
        print("ERROR: No object selected")
        return False
    
    # Get the lowest Z coordinate
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_z = min(corner.z for corner in bbox)
    
    # Move object so lowest point is at Z=0
    obj.location.z -= min_z
    print(f"Model positioned: moved {-min_z:.3f}mm on Z-axis")
    return True

def setup_voxel_remesh():
    """Add and configure voxel remesh modifier"""
    obj = bpy.context.active_object
    if not obj:
        print("ERROR: No object selected")
        return False
    
    # Remove existing remesh modifiers
    for mod in obj.modifiers:
        if mod.type == 'REMESH':
            obj.modifiers.remove(mod)
    
    # Add new voxel remesh
    remesh = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.004  # 4.0mm in Blender units (meters)
    remesh.use_remove_disconnected = True
    remesh.adaptivity = 0.0
    
    print("Voxel remesh configured:")
    print(f"  - Voxel size: {remesh.voxel_size * 1000:.1f}mm")
    print(f"  - Remove disconnected: {remesh.use_remove_disconnected}")
    print("  - Ready to apply (do this manually when satisfied)")
    return True

def check_dimensions():
    """Check current object dimensions"""
    obj = bpy.context.active_object
    if not obj:
        print("ERROR: No object selected")
        return False
    
    # Get dimensions
    dims = obj.dimensions
    length_mm = max(dims) * 1000  # Convert to mm
    
    print(f"Current dimensions:")
    print(f"  - X: {dims.x * 1000:.1f}mm")
    print(f"  - Y: {dims.y * 1000:.1f}mm") 
    print(f"  - Z: {dims.z * 1000:.1f}mm")
    print(f"  - Length (max): {length_mm:.1f}mm")
    
    target = 594.36
    if abs(length_mm - target) < 10:
        print(f"✅ Length close to target ({target}mm)")
    else:
        print(f"⚠️  Length differs from target ({target}mm)")
    
    return True

def setup_export_settings():
    """Prepare export settings for STL"""
    # Set scene units to metric
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
    
    print("Scene configured for export:")
    print("  - Units: Metric/Millimeters")
    print("  - Ready for STL export")
    print("  - Export path: blender/exports/molly_voxel.stl")
    
def main():
    """Main automation sequence"""
    print("=" * 50)
    print("MOLLY PHASE 1 AUTOMATION")
    print("=" * 50)
    
    # Check prerequisites
    if not check_3d_print_addon():
        print("⚠️  3D-Print Toolbox not enabled")
        print("   Enable in Edit → Preferences → Add-ons")
    
    if not bpy.context.active_object:
        print("❌ No object selected")
        print("   Select your Molly model first")
        return
    
    print(f"Selected object: {bpy.context.active_object.name}")
    
    # Step 1: Position model
    print("\n1. Positioning model at Z=0...")
    if position_model_at_origin():
        print("✅ Model positioned")
    
    # Step 2: Check current dimensions
    print("\n2. Checking dimensions...")
    check_dimensions()
    
    # Step 3: Setup voxel remesh
    print("\n3. Setting up voxel remesh...")
    if setup_voxel_remesh():
        print("✅ Voxel remesh configured")
    
    # Step 4: Prepare export settings
    print("\n4. Configuring export settings...")
    setup_export_settings()
    print("✅ Export settings ready")
    
    print("\n" + "=" * 50)
    print("MANUAL STEPS REMAINING:")
    print("=" * 50)
    print("1. Run 3D-Print Toolbox → Check All → Make Manifold")
    print("2. Apply the Voxel Remesh modifier when satisfied")
    print("3. File → Export → STL:")
    print("   - Format: Binary")
    print("   - Path: blender/exports/molly_voxel.stl")
    print("4. Validate by re-importing the STL")
    print("=" * 50)

if __name__ == "__main__":
    main()