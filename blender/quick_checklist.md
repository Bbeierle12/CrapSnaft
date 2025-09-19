# Phase 1 Quick Reference - Molly Voxelization

## ⚡ Fast Track Steps

### 1. Manifold Pass (In Progress ✅)
```
3D-Print Toolbox → Check All → Make Manifold
```

### 2. Position Model
```
• Belly at Z=0
• Length = 594mm target
• Save backup before voxelization!
```

### 3. Voxel Remesh
```
Modifier → Remesh → Voxel
• Voxel Size: 4.0mm (EXACT)
• Remove Disconnected: ON
• Apply when ready
```

### 4. Export
```
File → Export → STL
• Binary format
• Path: blender/exports/molly_voxel.stl
• Units: Millimeters
```

### 5. Validate
```
• Re-import to test
• Check dimensions (~594mm length)
• Run 3D-Print check again
```

## 🔧 Blender Hotkeys
- `N` - Properties panel
- `Tab` - Edit mode
- `G + Z` - Move on Z-axis only
- `O` - Proportional editing
- `S` - Scale
- `Alt+A` - Deselect all

## 📋 Critical Settings
- **Voxel Size**: 4.0mm (matches config)
- **Units**: Millimeters
- **Origin**: Belly at Z=0
- **Format**: Binary STL

## ⚠️ Common Mistakes
- ❌ Wrong voxel size (must be 4.0mm)
- ❌ Forgetting to apply modifiers
- ❌ Wrong export units
- ❌ Not checking manifold after remesh
- ❌ Skipping backup before voxelization

## ✅ Success Criteria
- [ ] 3D-Print Toolbox all green
- [ ] Length ≈ 594mm 
- [ ] File size several MB
- [ ] Clean re-import test