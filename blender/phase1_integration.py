# Phase 1 Integration Script
# Links Blender workflow to BrickGPT configuration

import os
import yaml
from pathlib import Path

def check_blender_export():
    """Check if molly_voxel.stl exists and get its properties"""
    export_path = Path("blender/exports/molly_voxel.stl")
    
    if not export_path.exists():
        print("❌ molly_voxel.stl not found")
        print("   Complete Blender export first")
        return False
    
    size_mb = export_path.stat().st_size / (1024 * 1024)
    print(f"✅ Found molly_voxel.stl ({size_mb:.1f} MB)")
    
    if size_mb < 1:
        print("⚠️  File seems small - check export settings")
    
    return True

def validate_config_files():
    """Check that config files are properly set up"""
    configs = ["configs/targets.yaml", "configs/molly.yaml"]
    
    for config_path in configs:
        if not Path(config_path).exists():
            print(f"❌ Missing {config_path}")
            return False
        print(f"✅ Found {config_path}")
    
    # Check molly.yaml points to correct STL
    with open("configs/molly.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    stl_path = config.get('model', {}).get('path', '')
    if stl_path == "blender/exports/molly_voxel.stl":
        print("✅ Configuration points to correct STL path")
    else:
        print(f"⚠️  Config STL path: {stl_path}")
    
    return True

def create_phase1_completion_marker():
    """Create a marker file indicating Phase 1 is complete"""
    marker_content = f"""# Phase 1 Completion Marker
# Generated automatically

phase: 1
status: complete
timestamp: {datetime.now().isoformat()}
outputs:
  stl_file: blender/exports/molly_voxel.stl
  voxel_size_mm: 4.0
  target_length_mm: 594.36

validation:
  manifold_check: "Run 3D-Print Toolbox verification"
  dimension_check: "Verify ~594mm length"
  export_format: "Binary STL in millimeters"

next_phase: "Phase 2 - Compiler v0.2 upgrades"
"""
    
    with open("blender/PHASE1_COMPLETE.md", 'w') as f:
        f.write(marker_content)
    
    print("✅ Phase 1 completion marker created")

def main():
    """Main validation and integration check"""
    print("Phase 1 Integration Check")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not Path("configs").exists():
        print("❌ Not in BrickGPT root directory")
        print("   Run from: c:\\Users\\Bbeie\\legobuilder\\BrickGPT\\")
        return
    
    # Validate Blender export
    if not check_blender_export():
        return
    
    # Validate configuration
    if not validate_config_files():
        return
    
    # Create completion marker
    create_phase1_completion_marker()
    
    print("\n" + "=" * 30)
    print("PHASE 1 STATUS: READY FOR PHASE 2")
    print("=" * 30)
    print("\nNext steps:")
    print("1. Implement v0.2 compiler upgrades (Phase 2)")
    print("2. Run smoke tests (Phase 3)")
    print("3. Generate first build plan (Phase 4)")

if __name__ == "__main__":
    import datetime
    main()