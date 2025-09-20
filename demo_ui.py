#!/usr/bin/env python3
"""
BrickGPT Builder UI Demo
========================

This script demonstrates the various UI components available in BrickGPT:
1. Project Molly compiler interface (mollyc)
2. BrickGPT text-to-LEGO inference
3. Mesh-to-brick converter
4. Configuration management

Since BrickGPT is primarily a command-line tool with Python APIs,
this demo shows how to interact with the various interfaces.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def show_molly_interface():
    """Demonstrate the Project Molly compiler interface."""
    print("="*60)
    print("PROJECT MOLLY COMPILER INTERFACE")
    print("="*60)
    print()
    print("The Project Molly compiler (mollyc) provides these commands:")
    print()
    print("1. PLAN - Generate a build plan from 3D models")
    print("   Usage: mollyc plan --config configs/molly.yaml")
    print("   Features:")
    print("   • Voxelization of STL files")
    print("   • Optimization for LEGO brick placement")
    print("   • Structural integrity validation")
    print("   • Technic beam integration for strength")
    print()
    
    print("2. VALIDATE - Check build plans for issues")
    print("   Usage: mollyc validate --config configs/molly.yaml")
    print("   Checks:")
    print("   • Complete model coverage")
    print("   • No brick collisions")
    print("   • Structural connectivity")
    print("   • Cantilever limits")
    print("   • Maximum span validation")
    print()
    
    print("3. BOM - Generate Bill of Materials")
    print("   Usage: mollyc bom --config configs/molly.yaml")
    print("   Outputs:")
    print("   • LDraw (.ldr) files for visualization")
    print("   • Multi-part documents (.mpd) with submodels")
    print("   • BrickLink XML for purchasing")
    print("   • Build instructions")
    print()

def show_brickgpt_interface():
    """Demonstrate the BrickGPT text-to-LEGO interface."""
    print("="*60)
    print("BRICKGPT TEXT-TO-LEGO INTERFACE")
    print("="*60)
    print()
    print("BrickGPT generates LEGO models from text descriptions.")
    print()
    print("Usage: python -c \"import sys; sys.path.insert(0, 'src'); from brickgpt.infer import main; main()\"")
    print()
    print("Interactive Features:")
    print("• Enter text prompts like 'Table with four legs'")
    print("• Specify output filenames for results")
    print("• Set generation seeds for reproducibility")
    print("• Automatic rendering to PNG images")
    print()
    print("Output Formats:")
    print("• .txt - Human-readable brick list")
    print("• .ldr - LDraw format for 3D visualization")
    print("• .png - Rendered image of the model")
    print()
    print("Example prompts:")
    print("• 'Simple house with a door and two windows'")
    print("• 'Racing car with spoiler and large wheels'")
    print("• 'Castle with towers and defensive walls'")
    print("• 'Bridge spanning across a river'")
    print()

def show_mesh2brick_interface():
    """Demonstrate the mesh-to-brick converter."""
    print("="*60)
    print("MESH-TO-BRICK CONVERTER")
    print("="*60)
    print()
    print("Convert 3D mesh files (.obj, .glb, etc.) to LEGO brick structures.")
    print()
    print("Usage: python -m mesh2brick.mesh2brick [INPUT_MESH] [OUTPUT_FILE]")
    print()
    print("Options:")
    print("• --world_dim: Size of the brick structure (default: 20)")
    print("• --max_failures: Max re-merge attempts (default: 10)")
    print("• --x_rotation: Rotation around X-axis (default: 90°)")
    print()
    print("Output formats:")
    print("• .json - Detailed brick data with positions")
    print("• .txt - Human-readable brick list")
    print("• .ldr - LDraw format for visualization")
    print()

def show_ui_facade():
    """Demonstrate the UI facade for programmatic access."""
    print("="*60)
    print("PROGRAMMATIC UI INTERFACE")
    print("="*60)
    print()
    print("For developers, BrickGPT provides a Python API:")
    print()
    
    print("from brickgpt.ui import MollyUI")
    print()
    print("# Initialize the UI facade")
    print("ui = MollyUI(config_path='configs/molly.yaml',")
    print("            targets_path='configs/targets.yaml')")
    print()
    print("# Generate a build plan")
    print("plan = ui.plan(dimensions=[30, 20, 15])")
    print()
    print("# Validate the plan")
    print("report = ui.validate()")
    print()
    print("# Export results")
    print("outputs = ui.export()")
    print()

def show_configuration():
    """Show configuration options."""
    print("="*60)
    print("CONFIGURATION SYSTEM")
    print("="*60)
    print()
    print("BrickGPT uses YAML configuration files:")
    print()
    print("1. molly.yaml - Main configuration")
    print("   • Model input settings")
    print("   • Voxelization parameters")
    print("   • Optimization weights")
    print("   • Output formats")
    print()
    print("2. targets.yaml - Build constraints")
    print("   • Dimensional constraints")
    print("   • Brick palette restrictions")
    print("   • Color schemes")
    print("   • Structural requirements")
    print()
    
    # Show actual config location
    config_path = Path("configs/molly.yaml")
    if config_path.exists():
        print(f"✓ Configuration found: {config_path.absolute()}")
    else:
        print(f"⚠ Configuration not found: {config_path.absolute()}")
    print()

def main():
    """Main demo function."""
    print("BrickGPT Builder UI Preview")
    print("=" * 80)
    print()
    print("BrickGPT is a comprehensive LEGO building system with multiple interfaces:")
    print()
    
    try:
        show_molly_interface()
        show_brickgpt_interface()
        show_mesh2brick_interface()
        show_ui_facade()
        show_configuration()
        
        print("="*60)
        print("GETTING STARTED")
        print("="*60)
        print()
        print("To use BrickGPT:")
        print()
        print("1. Install dependencies (requires Python 3.11+):")
        print("   pip install torch transformers pyyaml numpy")
        print()
        print("2. For 3D rendering (optional):")
        print("   Install Blender and bpy module")
        print()
        print("3. For optimization (optional):")
        print("   Install Gurobi (free academic license available)")
        print()
        print("4. Try the interfaces:")
        print("   • Text-to-LEGO: Use the infer command")
        print("   • Mesh conversion: Use mesh2brick")
        print("   • Advanced builds: Use mollyc compiler")
        print()
        print("Check the README.md for detailed installation instructions.")
        print()
        
    except Exception as e:
        print(f"Demo error: {e}")
        print("This is normal if dependencies are not fully installed.")
        print("The interfaces shown above are available when BrickGPT is properly set up.")

if __name__ == "__main__":
    main()