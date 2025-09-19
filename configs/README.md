# Project Molly Configuration Documentation

This directory contains the configuration files for Project Molly, a comprehensive LEGO brick compiler for converting 3D models into buildable instructions.

## Configuration Files

### `targets.yaml` - Phase 0 Configuration
Defines the fundamental constraints and targets for the build:

#### Dimensions
- **locked_axis**: Which dimension to hold constant (`"length"`, `"width"`, `"height"`)
- **locked_value**: The fixed dimension value in inches
- **target_height**: Desired height (adjustable via model pose)

#### Palette Constraints
- **allowed_sizes**: Dictionary of brick dimensions (format: `"HxW": true/false`)
- **preferences**: General packing preferences and structural requirements

#### Colors
- **primary/accent**: Main color scheme
- **fallbacks**: Alternative colors when primary unavailable
- **details**: Special element colors (eyes, nose, collar)

### `molly.yaml` - Phase 3 Main Configuration
Complete configuration for the compiler pipeline:

#### Model Input
```yaml
model:
  path: "blender/exports/molly_voxel.stl"  # STL file path
  units: "auto"  # {mm,cm,m,auto} - auto-detect preferred
```

#### Voxelization
```yaml
voxelization:
  voxel_size_mm: 4.0      # Must match Blender voxel remesh
  layer_height_mm: 3.2    # LEGO plate height
  pitch_mm: 8.0           # LEGO stud spacing
```

#### Technic Core (Structural Reinforcement)
```yaml
technic_core:
  spines:
    count: 2              # Parallel longitudinal beams
    coverage: 0.67        # Fraction of length reinforced
  cross_ties:
    spacing_studs: 6      # Spacing between cross-connections
```

#### Optimization Weights
Controls the multi-objective optimization:
- **cost** (0.25): Minimize total piece cost
- **lots** (0.15): Minimize unique piece types
- **seam** (0.20): Minimize visible seams
- **strength** (0.15): Maximize structural integrity
- **short_penalty** (0.10): Penalize short bricks in spans
- **orientation** (0.10): Prefer consistent orientation
- **symmetry** (0.05): Maintain bilateral symmetry

## Usage Examples

### Basic Planning
```bash
mollyc plan --config configs/molly.yaml --lookahead 3
```

### Validation
```bash
mollyc validate --input out/molly.ldr --checks span,stagger,connectivity,cantilever
```

### Bill of Materials
```bash
mollyc bom --input out/molly.ldr --by-module --optimize-lots
```

## Expected Outputs

### Directory Structure
```
out/
├── molly.ldr              # Main LDraw file (MPD format)
├── molly.io               # Instruction file
├── molly_bricklink.xml    # BrickLink Wanted List
├── metrics.json           # Build statistics and scores
└── molly_layers/          # Per-layer LDraw files
    ├── layer_001.ldr
    ├── layer_002.ldr
    └── ...
```

### File Formats

#### LDraw (.ldr/.mpd)
- **MPD**: Multi-part document with submodels for head, torso, etc.
- **Integer LDU**: All coordinates in LDraw units
- **STEP/ROTSTEP**: Build sequence markers for instructions

#### Bill of Materials (.xml)
- **BrickLink format**: Compatible with BrickLink Wanted Lists
- **Price optimization**: Groups pieces into efficient lots
- **Module separation**: Separate BOMs for each model section

#### Metrics (.json)
```json
{
  "score_terms": {
    "cost": 142.50,
    "lots": 23,
    "seam_count": 8,
    "strength_score": 0.85
  },
  "build_stats": {
    "total_pieces": 847,
    "unique_pieces": 23,
    "estimated_build_time": "4.5 hours"
  }
}
```

## Customization Guide

### Adjusting Dimensions
To change the locked dimension:
1. Edit `targets.yaml` → `dimensions.locked_axis`
2. Update `locked_value` and corresponding mm conversion
3. Re-run Phase 1 (Blender voxelization) if major changes

### Modifying Brick Palette
To add/remove allowed brick sizes:
1. Edit `targets.yaml` → `palette.allowed_sizes`
2. Update `molly.yaml` → `packing.allowed_bricks` with weights
3. Consider structural implications for large changes

### Budget Optimization
To optimize for cost:
1. Increase `weights.cost` and `weights.lots` in `molly.yaml`
2. Enable `colors.enable_fallbacks` for more color options
3. Consider reducing allowed brick variety

### Structural Modifications
For different strength requirements:
1. Adjust `technic_core` settings (spine count, cross-tie spacing)
2. Modify `validation.limits` (cantilever, span limits)
3. Increase `weights.strength` for stronger builds

## Color Configuration

### LDraw Color Codes
Common colors and their LDraw codes:
- **Brown**: 6
- **Trans Brown**: 34
- **Trans Black**: 33
- **Black**: 0
- **Red**: 4

### Adding New Colors
1. Add to `colors.ldraw_mapping` in `molly.yaml`
2. Define fallback rules in `colors.fallback_rules`
3. Update `targets.yaml` color specifications

## Performance Tuning

### For Large Models
```yaml
performance:
  max_iterations: 2000      # Increase for better optimization
  parallel_workers: 8       # Use more CPU cores
  memory_limit_gb: 16      # Allow more memory usage
```

### For Quick Testing
```yaml
performance:
  max_iterations: 100       # Reduce for faster results
  convergence_threshold: 0.1  # Stop optimization earlier
```

## Troubleshooting

### Common Issues

1. **High piece count**: Increase weight on `lots` and `cost`
2. **Weak structure**: Enable more `technic_core` features, increase `weights.strength`
3. **Visible seams**: Increase `weights.seam`, adjust `packing.preferences`
4. **Build complexity**: Reduce allowed brick variety, increase `weights.orientation`

### Validation Failures
- **Cantilever**: Reduce `validation.limits.max_cantilever_studs`
- **Span**: Reduce `validation.limits.max_span_studs`
- **Connectivity**: Check `technic_core` configuration

### Memory Issues
- Reduce `performance.memory_limit_gb`
- Enable `performance.enable_caching` with appropriate `cache_dir`
- Consider processing in smaller chunks