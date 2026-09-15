# ParaView Elevation & Contour Automation

**English** | [한국어](README.md)

A Python script that automates the last section of the 3D modelling guide
(*Guide to 3D modelling*) —
**"Visualising the Model as Elevation (height maps) and Contour images using Paraview"** (Steps 1–12) —
without any manual GUI operation.

Given an input 3D model (mesh), it automatically generates and saves an
**elevation (height map)** image and a **contour** image. Pass several color
presets and it renders one image set per preset in a single run.

## Requirements

- [ParaView](https://www.paraview.org/) installed (the script uses ParaView's built-in `paraview.simple`)
- Run it with ParaView's **`pvpython`** (or `pvbatch`), or from the ParaView GUI **Python Shell** — not a plain `python`

## Usage

### Option A. Command line (pvpython)

```bash
pvpython paraview_elevation_contour.py --input model.obj
```

Results go to **`paraview_image/` inside the model's own folder** (created
automatically). There is no option to set the output path.

With options:

```bash
pvpython paraview_elevation_contour.py \
    --input model.obj \
    --model-unit mm \
    --unit mm \
    --interval 1.0 \
    --presets "Rainbow Uniform,Turbo,Viridis (matplotlib),Cool to Warm" \
    --resolution 3840x2160
```

Typical `pvpython` locations:
- Linux: `/opt/paraview/bin/pvpython`
- macOS: `/Applications/ParaView-5.x.app/Contents/bin/pvpython`
- Windows: `"C:\Program Files\ParaView 5.x\bin\pvpython.exe"`

### Option B. ParaView GUI (Run Script button)

1. Open `run_in_paraview.py` and edit just two paths in the **config** section
   (`MAIN_SCRIPT`, `INPUT_MODEL`). There is no output-path setting.
2. Launch ParaView → **View → Python Shell** (older versions: Tools → Python Shell).
3. Click **Run Script** in the Python Shell → select `run_in_paraview.py`.
4. When it finishes, the output folder and images open automatically.

## Units (important)

The script works in **millimetres by default**. A model scaled to mm in
CloudCompare / Metashape can be used as-is.

| Option | Meaning | Default |
|------|------|--------|
| `--model-unit` | **What one model coordinate unit actually is** (`mm`/`cm`/`m`) | `mm` |
| `--unit` | **Unit shown on the color bar** (`mm`/`cm`/`m`/`auto`) | `mm` |

```
height range D(mm) = (high − low) × (model unit → mm factor)
color bar value    = D(mm) / (display unit → mm factor)
```

A wrong `--model-unit` is off by a factor of 1000. For example, if the OBJ's z
range is `32.12` and the true relief is 32 mm, then one coordinate unit is 1 mm,
so `--model-unit mm`. (Use `--model-unit m` for models in metres; the script
warns when the numbers look implausible.)

With `--unit auto`, D < 10 mm shows as mm, < 1000 mm as cm, and larger as m.

## Color bar

- Tick numbers use **annotations** by default (`--label-mode annotation`): the value
  *and* its printed text are given as strings, which avoids the bug in some ParaView
  versions where custom labels render the format string (`%-#6.2f`) literally.
  Other modes: `auto`, `format`, `custom`.
- Tick values are chosen on a 1 / 2 / 2.5 / 5 × 10ⁿ "nice step"; 0 and the maximum are
  always included, and interior ticks that would collide with them are dropped.
  e.g. 0–32 mm with `--n-labels 5` → `0, 10, 20, 30, 32`.
- Font sizes scale with the **output resolution** (52 px title / 43 px labels at 4K,
  adjustable via `--font-scale`). Screenshots are saved with
  `FontScaling='Do not scale fonts'`, so results do not depend on the ParaView window size.

## Options

| Option | Meaning | Default |
|------|------|--------|
| `--input, -i` | Input 3D model (.ply/.obj/.vtk/.vtp/.stl, etc.) | (required) |
| `--axis` | Elevation reference axis | `z` |
| `--model-unit` | What one model coordinate unit is (`mm`/`cm`/`m`) | `mm` |
| `--unit` | Color bar display unit (`mm`/`cm`/`m`/`auto`) | `mm` |
| `--low` / `--high` | Low/high point (model coordinates). If omitted, auto-detected from the bounding box and truncated below 1 mm | auto |
| `--interval` | Contour spacing (mm) | `1.0` |
| `--line-width` | Contour line width (2–3 recommended at 4K) | `1.0` |
| `--max-contours` | Safety cap on the number of contours | `2000` |
| `--presets` | Comma-separated color presets (one image set per preset) | `Rainbow Uniform,Turbo,Viridis (matplotlib),Cool to Warm` |
| `--preset` | Single preset (backward compatible) | — |
| `--list-presets` | Print the presets available in this ParaView build and exit | off |
| `--resolution` | Output image resolution WxH (16:9 recommended) | `3840x2160` |
| `--label-mode` | Tick label method (`annotation`/`auto`/`format`/`custom`) | `annotation` |
| `--n-labels` | Target number of tick labels | `5` |
| `--font-scale` | Color bar font / thickness multiplier | `1.0` |
| `--colorbar-frac` | Fraction of image width reserved for the color bar | `0.20` |
| `--margin` | Image margin fraction | `0.04` |
| `--perspective` | Perspective projection (default is parallel) | off |
| `--no-contour-colorbar` | Omit the color bar from contour images | off |
| `--no-contour` | Skip contours (elevation only) | off |
| `--no-state` | Skip saving the `.pvsm` state file | off |
| `--no-open` | Do not open the output folder / images when finished | off |
| `--open-images` | Number of elevation images to open automatically | `4` |

## Outputs

A `paraview_image/` folder is created automatically next to the input model:

```
<model folder>/
├─ model.obj
└─ paraview_image/
   ├─ model_rainbow_uniform_elevation.png
   ├─ model_rainbow_uniform_contour.png
   ├─ model_turbo_elevation.png
   ├─ model_turbo_contour.png
   ├─ ...
   └─ model_state.pvsm
```

- Both images share the same camera, so they can be overlaid directly.
- White background, black text, and the model is scaled as large as possible
  without intruding into the color bar strip.

## Manual steps ↔ code

| Manual | Action | Code |
|--------|------|------|
| Step 1–2 | Open + select model | `OpenDataFile` / `SetActiveSource` |
| Step 3 | Filters > Elevation | `Elevation()` |
| Step 4 | Select Z axis + Apply | `LowPoint` / `HighPoint` |
| Step 5 | Un-select 'show line' | Just a 3D widget; irrelevant to saved output → ignored in batch |
| Step 6 | Truncate low/high below 1 mm | `floor(v / q) · q`, `q` = 1 mm in model coordinates |
| Step 7 | Scalar Range 0–1 → 0–D | `ScalarRange = [0, D/factor]` |
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
output = ScalarRange0 + s·(ScalarRange1 − ScalarRange0) = s·D/factor
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

**Camera (largest zoom that never overlaps the color bar):**
The frame is split into `[ margin | model frac_w | gap | color bar ]`; with the
bounding box's on-screen half-width `hw` and half-height `hh`,

```
CameraParallelScale S = max( hh / frac_h , hw / (frac_w · aspect) )
shift to the model region centre Δ = (0.5 − xc) · 2·S·aspect
```

## Note: the input must be a *mesh*

The Elevation/Contour filters do not change the input topology. If you feed a
**point cloud** (no faces), the output stays points and contours will not be
produced correctly. The manual assumes a mesh built with Metashape **Build Mesh**.

## Troubleshooting

| Symptom | Cause / fix |
|------|------------|
| Color bar reads in metres | `--model-unit` does not match the model. For mm models use `--model-unit mm` (the default) |
| Ticks show `%-#6.2f` instead of numbers | Custom-label bug in some ParaView builds. Use `--label-mode annotation` (default) or `auto` |
| Color bar text too small / too large | Adjust `--font-scale`; if numbers are clipped, raise `--colorbar-frac` to 0.24–0.28 |
| "Too many contours" error | Increase `--interval`, or check `--model-unit` (a wrong unit inflates D by 1000×) |
| A preset is not applied | Run `--list-presets` to see the exact names in your ParaView build |

## References

- Elevation filter: <https://www.paraview.org/paraview-docs/v5.13.0/python/paraview.simple.Elevation.html>
- Contour filter: <https://www.paraview.org/paraview-docs/v5.13.3/python/paraview.simple.Contour.html>
- Color mapping (ColorBy/ApplyPreset/Annotations): <https://docs.paraview.org/en/v5.13.0/ReferenceManual/colorMapping.html>
- Saving results (SaveScreenshot/SaveState): <https://docs.paraview.org/en/v5.10.0/UsersGuide/savingResults.html>
