# Phase 1: Blender Geometry Preparation Guide

## Prerequisites
- Blender 3.0+ installed
- 3D-Print Toolbox addon enabled
- Original Molly model loaded in Blender

## Step-by-Step Instructions

### 1. Manifold Pass (CRITICAL)
**Goal**: Ensure the model is watertight and 3D-printable

1. **Select your Molly model** in Blender
2. **Enable 3D-Print Toolbox**:
   - Go to `Edit > Preferences > Add-ons`
   - Search for "3D-Print Toolbox"
   - Enable the checkbox
3. **Access the toolbox**:
   - Press `N` to open side panel
   - Click on "3D-Print" tab
4. **Run checks**:
   - Click "Check All" 
   - Review the report for issues:
     - Non-manifold edges
     - Bad contiguous edges
     - Intersecting faces
     - Degenerate faces
5. **Fix issues**:
   - Click "Make Manifold" to auto-fix
   - Manually fix any remaining issues
6. **Verify**: Re-run "Check All" until clean

### 2. Pose Adjustment (Optional)
**Goal**: Achieve target height of 13.8" (350.52mm) without changing length

**Current constraint**: Length locked at 23.4" (594.36mm)

If you want more height:
1. **Select the head/neck area**
2. **Rotate slightly upward**:
   - Use `R` (rotate) + `Y` (Y-axis) + angle
   - Small increments: 5-10 degrees max
3. **Check dimensions**:
   - Add a measuring tool or use dimensions panel
   - Ensure length stays at ~594mm
   - Target height: ~350mm

**Note**: Minor pose adjustments only. Major changes require returning to Phase 0.

### 3. Voxel Remesh (CRITICAL)
**Goal**: Convert to uniform voxel grid at exactly 4.0mm resolution

1. **Position the model**:
   - Move belly/underside to Z=0 level
   - Use `G` (grab) + `Z` + `0` to snap to Z=0
2. **Apply voxel remesh**:
   - Select the model
   - Go to `Modifier Properties` (wrench icon)
   - Add Modifier > Generate > Remesh
3. **Configure settings**:
   - **Mode**: Voxel
   - **Voxel Size**: 4.0 mm (EXACT - matches config)
   - **Adaptivity**: 0.0 (uniform grid)
   - **Remove Disconnected**: ON (critical for cleanup)
4. **Apply modifier**:
   - Click "Apply" (or Ctrl+A in modifier panel)

### 4. Quality Check
Before export, verify:
- [ ] Model is completely manifold (no holes)
- [ ] Voxel size is exactly 4.0mm
- [ ] Belly is at Z=0
- [ ] Overall length ≈ 594mm (23.4")
- [ ] No disconnected pieces

### 5. Export STL
**Goal**: Binary STL in millimeters for compiler

1. **Select the voxelized model**
2. **File > Export > STL (.stl)**
3. **Configure export**:
   - **Format**: Binary (faster, smaller)
   - **Scale**: 1.0 (keep in mm)
   - **Up Axis**: Z Up
   - **Forward**: Y Forward
4. **File path**: `blender/exports/molly_voxel.stl`
5. **Export**

### 6. Verification
**Critical acceptance criteria**:

1. **File size check**:
   - Should be several MB (voxelized models are large)
   - If <1MB, likely not voxelized properly

2. **Dimension verification**:
   - Reimport STL into new Blender scene
   - Measure length: should be ~594mm
   - Check that it's blocky/voxelized appearance

3. **Manifold verification**:
   - Run 3D-Print Toolbox "Check All" on imported STL
   - Should report "0 Non-Manifold Edges"

## Expected Results

### File Output
- `blender/exports/molly_voxel.stl` (binary format)
- Size: 5-20MB depending on detail level
- Dimensions: ~594mm length, voxelized appearance

### Visual Characteristics
- Blocky, Minecraft-like appearance
- Uniform 4mm voxel grid
- No smooth curves (will be restored by brick compiler)
- Belly flat against Z=0 plane

## Troubleshooting

### Issue: "Make Manifold" fails
**Solution**: 
- Try manual cleanup: `Alt+M` merge vertices
- Remove doubles: `M > By Distance`
- Recalculate normals: `Shift+N`

### Issue: Voxel size too large/small
**Problem**: Must be exactly 4.0mm to match compiler config
**Solution**: 
- Check Units: `Scene Properties > Units > Millimeters`
- Verify object scale is applied: `Ctrl+A > Scale`

### Issue: Model too complex after voxel
**Solution**:
- Increase voxel size slightly (4.2mm) for testing
- Update config files to match
- Consider decimation before voxel remesh

### Issue: Length changed during voxelization
**Solution**:
- Voxelization can slightly alter dimensions
- Acceptable range: 590-598mm (±1% tolerance)
- If outside range, adjust scale before re-export

## Next Steps

After successful Phase 1:
1. **Verify**: STL opens cleanly in any 3D viewer
2. **Measure**: Confirm dimensions using Blender or CAD software  
3. **Ready for Phase 2**: Compiler v0.2 upgrades
4. **Phase 3**: Configuration and smoke tests

## File Locations
```
BrickGPT/
├── blender/
│   └── exports/
│       └── molly_voxel.stl  ← Target output
├── configs/
│   ├── targets.yaml         ← Phase 0 constraints
│   └── molly.yaml          ← References this STL
```

The `molly.yaml` config is already set to look for this exact file path.