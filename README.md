# ParaView Elevation & Contour Automation

3D 모델링 매뉴얼(*Guide to 3D modelling*)의 마지막 섹션
**"Visualising the Model as Elevation (height maps) and Contour images using Paraview"** (Step 1~12)
를 GUI 조작 없이 자동으로 수행하는 파이썬 스크립트입니다.

입력 3D 모델(mesh)을 받아 **높이지도(elevation, height map)** 이미지와 **등고선(contour)** 이미지를
자동으로 생성/저장합니다.

## 요구 사항

- [ParaView](https://www.paraview.org/) 설치 (스크립트는 ParaView 내장 파이썬 `paraview.simple` 사용)
- 일반 `python` 이 아니라 ParaView 의 **`pvpython`**(또는 `pvbatch`), 혹은 ParaView GUI 의 **Python Shell** 로 실행

## 실행 방법

### 방법 A. 명령줄 (pvpython)

```bash
pvpython paraview_elevation_contour.py --input model.ply --out ./results
```

옵션 예시:

```bash
pvpython paraview_elevation_contour.py \
    --input model.ply \
    --out ./results \
    --low 0.012 --high 0.058 \
    --interval 0.1 \
    --preset "Cool to Warm"
```

`pvpython` 위치 예시:
- Linux: `/opt/paraview/bin/pvpython`
- macOS: `/Applications/ParaView-5.x.app/Contents/bin/pvpython`
- Windows: `"C:\Program Files\ParaView 5.x\bin\pvpython.exe"`

### 방법 B. ParaView GUI (Run Script 버튼)

1. `run_in_paraview.py` 를 열어 맨 위 **설정** 부분의 경로 3줄(`MAIN_SCRIPT`, `INPUT_MODEL`, `OUTPUT_DIR`)을 본인 것으로 수정
2. ParaView 실행 → **View → Python Shell** (구버전은 Tools → Python Shell)
3. Python Shell 의 **Run Script** 버튼 → `run_in_paraview.py` 선택

## 주요 옵션

| 옵션 | 의미 | 기본값 |
|------|------|--------|
| `--input, -i` | 입력 3D 모델 (.ply/.obj/.vtk/.vtp/.stl 등) | (필수) |
| `--out, -o` | 결과 저장 폴더 | `./paraview_output` |
| `--axis` | Elevation 기준 축 | `z` |
| `--low` / `--high` | low/high point 값(미터). 미지정 시 경계상자에서 자동 검출 후 mm로 버림 | 자동 |
| `--interval` | 등고선 간격(mm) | `1.0` |
| `--max-contours` | 등고선 최대 개수 안전 한계 | `2000` |
| `--preset` | 컬러 프리셋 이름 | `Rainbow Uniform` |
| `--resolution` | 저장 이미지 해상도 WxH | `1920x1440` |
| `--no-contour` | 등고선 생략(높이지도만) | off |
| `--no-state` | `.pvsm` 상태 파일 저장 생략 | off |

## 출력물

- `<모델명>_elevation.png` — 높이지도 이미지 (Step 12)
- `<모델명>_contour.png` — 등고선 이미지 (Step 12)
- `<모델명>_state.pvsm` — ParaView 상태 파일 (Step 12, Save state)

## 매뉴얼 스텝 ↔ 코드 대응

| 매뉴얼 | 동작 | 코드 |
|--------|------|------|
| Step 1–2 | 모델 열기 + 선택 | `OpenDataFile` / `SetActiveSource` |
| Step 3 | Filters > Elevation | `Elevation()` |
| Step 4 | Z축 선택 + Apply | `LowPoint` / `HighPoint` |
| Step 5 | 'show line' 해제 | 3D 위젯일 뿐, 저장 결과에 무관 → 배치에서 무시 |
| Step 6 | low/high 를 mm로 반올림 | `floor(round(v*1000,6))/1000` |
| Step 7 | Scalar Range 0~1 → 0~거리(mm) | `ScalarRange = [0, D]` |
| Step 8 | 컬러 프리셋 적용 | `ApplyPreset` |
| Step 9 | Filters > Contour | `Contour()` |
| Step 10 | 등고선 검정색 | `AmbientColor/DiffuseColor=[0,0,0]` |
| Step 11 | steps(등고선) 추가 | `Isosurfaces = [0, δ, 2δ, ..., D]` |
| Step 12 | 이미지/상태 저장 | `SaveScreenshot` / `SaveState` |

## 핵심 수식

**높이 스칼라 (Elevation, `vtkElevationFilter`):**
점 P, LowPoint L, HighPoint H 에 대해

```
s = clamp( ((P−L)·(H−L)) / |H−L|² , 0, 1 )    (s ∈ [0,1])
출력 = ScalarRange0 + s·(ScalarRange1 − ScalarRange0) = s·D   (단위 mm)
```

**등고선 개수 (Step 11):**
높이 범위 D(mm), 간격 δ(mm) 일 때

```
등고선 개수 N = D/δ + 1
등고선 값     v_i = i·δ   (i = 0,1,...,D/δ)
```

예) D=46mm, δ=1mm → N=47 (값 0,1,...,46) / δ=0.1mm → N=461

> 참고: 매뉴얼 Step 11 의 두 번째 예시 "30mm → (30+1)=30" 은 매뉴얼의 오타이며,
> 수학적으로 올바른 값은 **31** 입니다 (0,1,...,30 = 31개). 이 스크립트는 31을 사용합니다.

## 주의: 입력은 '메시(mesh)' 여야 합니다

Elevation/Contour 필터는 입력의 형태(topology)를 바꾸지 않습니다.
면(face)이 없는 **점군(point cloud)** 을 넣으면 결과도 점으로 나오고 등고선이 제대로 만들어지지 않습니다.
매뉴얼이 가정하는 입력은 Metashape **Build Mesh** 로 만든 메시입니다.

## 참고(References)

- Elevation 필터: <https://www.paraview.org/paraview-docs/v5.13.0/python/paraview.simple.Elevation.html>
- Contour 필터: <https://www.paraview.org/paraview-docs/v5.13.3/python/paraview.simple.Contour.html>
- 색상 매핑(ColorBy/ApplyPreset/RescaleTransferFunction): <https://docs.paraview.org/en/v5.13.0/ReferenceManual/colorMapping.html>
- 결과 저장(SaveScreenshot/SaveState): <https://docs.paraview.org/en/v5.10.0/UsersGuide/savingResults.html>
