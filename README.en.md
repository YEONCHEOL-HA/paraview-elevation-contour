# ParaView Elevation & Contour Automation

**English** | [한국어](README.md)

A Python script that automates the last section of the 3D modelling guide
(*Guide to 3D modelling*) —
**"Visualising the Model as Elevation (height maps) and Contour images using Paraview"** (Steps 1–12) —
without any manual GUI operation.

Given an input 3D model (mesh), it automatically generates and saves an
**elevation (height map)** image and a **contour** image.

## Requirements

- [ParaView](https://www.paraview.org/) installed (the script uses ParaView's built-in `paraview.simple`)
- Run it with ParaView's **`pvpython`** (or `pvbatch`), or from the ParaView GUI **Python Shell** — not a plain `python`

## Usage

### Option A. Command line (pvpython)

```bash
pvpython paraview_elevation_contour.py --input model.ply --out ./results
```

With options:

```bash
pvpython paraview_elevation_contour.py \
    --input model.ply \
    --out ./results \
    --low 0.012 --high 0.058 \
    --interval 0.1 \
    --preset "Cool to Warm"
```

Typical `pvpython` locations:
- Linux: `/opt/paraview/bin/pvpython`
- macOS: `/Applications/ParaView-5.x.app/Contents/bin/pvpython`
- Windows: `"C:\Program Files\ParaView 5.x\bin\pvpython.exe"`

### Option B. ParaView GUI (Run Script button)

1. Open `run_in_paraview.py` and edit the three paths at the top of the **config** section (`MAIN_SCRIPT`, `INPUT_MODEL`, `OUTPUT_DIR`).
2. Launch ParaView → **View → Python Shell** (older versions: Tools → Python Shell).
3. Click the **Run Script** button in the Python Shell → select `run_in_paraview.py`.

## Options

| Option | Meaning | Default |
|------|------|--------|
| `--input, -i` | Input 3D model (.ply/.obj/.vtk/.vtp/.stl, etc.) | (required) |
| `--out, -o` | Output folder | `./paraview_output` |
| `--axis` | Elevation reference axis | `z` |
| `--low` / `--high` | Low/high point (metres). If omitted, auto-detected from the bounding box and truncated to mm | auto |
| `--interval` | Contour spacing (mm) | `1.0` |
| `--max-contours` | Safety cap on the number of contours | `2000` |
| `--preset` | Color preset name | `Rainbow Uniform` |
| `--resolution` | Output image resolution WxH | `1920x1440` |
| `--no-contour` | Skip contours (elevation only) | off |
| `--no-state` | Skip saving the `.pvsm` state file | off |

## Outputs

- `<model>_elevation.png` — elevation (height map) image (Step 12)
- `<model>_contour.png` — contour image (Step 12)
- `<model>_state.pvsm` — ParaView state file (Step 12, Save state)

## Manual steps ↔ code

| Manual | Action | Code |
|--------|------|------|
| Step 1–2 | Open + select model | `OpenDataFile` / `SetActiveSource` |
| Step 3 | Filters > Elevation | `Elevation()` |
| Step 4 | Select Z axis + Apply | `LowPoint` / `HighPoint` |
| Step 5 | Un-select 'show line' | Just a 3D widget; irrelevant to saved output → ignored in batch |
| Step 6 | Truncate low/high to mm | `floor(round(v*1000,6))/1000` |
| Step 7 | Scalar Range 0–1 → 0–distance(mm) | `ScalarRange = [0, D]` |
| Step 8 | Apply color preset | `ApplyPreset` |
| Step 9 | Filters > Contour | `Contour()` |
| Step 10 | Contour black | `AmbientColor/DiffuseColor=[0,0,0]` |
| Step 11 | Add steps (contours) | `Isosurfaces = [0, δ, 2δ, ..., D]` |
| Step 12 | Save images/state | `SaveScreenshot` / `SaveState` |

## Key math

**Elevation scalar (`vtkElevationFilter`):**
For a point P, LowPoint L, HighPoint H,

```
s = clamp( ((P−L)·(H−L)) / |H−L|² , 0, 1 )    (s ∈ [0,1])
output = ScalarRange0 + s·(ScalarRange1 − ScalarRange0) = s·D   (in mm)
```

**Number of contours (Step 11):**
For a height range D (mm) and spacing δ (mm),

```
N = D/δ + 1
v_i = i·δ   (i = 0, 1, ..., D/δ)
```

e.g. D=46mm, δ=1mm → N=47 (values 0,1,...,46); δ=0.1mm → N=461.

> Note: the manual's second example in Step 11, "30mm → (30+1)=30", is a typo in
> the manual. The mathematically correct value is **31** (0,1,...,30 = 31 values),
> and this script uses 31.

## Note: the input must be a *mesh*

The Elevation/Contour filters do not change the input topology. If you feed a
**point cloud** (no faces), the output stays points and contours will not be
produced correctly. The manual assumes a mesh built with Metashape **Build Mesh**.

## References

- Elevation filter: <https://www.paraview.org/paraview-docs/v5.13.0/python/paraview.simple.Elevation.html>
- Contour filter: <https://www.paraview.org/paraview-docs/v5.13.3/python/paraview.simple.Contour.html>
- Color mapping (ColorBy/ApplyPreset/RescaleTransferFunction): <https://docs.paraview.org/en/v5.13.0/ReferenceManual/colorMapping.html>
- Saving results (SaveScreenshot/SaveState): <https://docs.paraview.org/en/v5.10.0/UsersGuide/savingResults.html>
