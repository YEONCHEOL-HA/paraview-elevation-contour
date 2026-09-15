# ParaView Elevation & Contour Automation

[English](README.en.md) | **한국어**

3D 모델링 매뉴얼(*Guide to 3D modelling*)의 마지막 섹션
**"Visualising the Model as Elevation (height maps) and Contour images using Paraview"** (Step 1~12)
를 GUI 조작 없이 자동으로 수행하는 파이썬 스크립트입니다.

입력 3D 모델(mesh)을 받아 **높이지도(elevation, height map)** 이미지와 **등고선(contour)** 이미지를
자동으로 생성/저장합니다. 컬러 프리셋을 여러 개 지정하면 프리셋마다 이미지를 한 번에 만듭니다.

## 요구 사항

- [ParaView](https://www.paraview.org/) 설치 (스크립트는 ParaView 내장 파이썬 `paraview.simple` 사용)
- 일반 `python` 이 아니라 ParaView 의 **`pvpython`**(또는 `pvbatch`), 혹은 ParaView GUI 의 **Python Shell** 로 실행

## 실행 방법

### 방법 A. 명령줄 (pvpython)

```bash
pvpython paraview_elevation_contour.py --input model.obj
```

결과는 **모델이 들어있는 폴더 안의 `paraview_image/`** 에 저장됩니다(자동 생성).
출력 경로를 지정하는 옵션은 없습니다.

옵션 예시:

```bash
pvpython paraview_elevation_contour.py \
    --input model.obj \
    --model-unit mm \
    --unit mm \
    --interval 1.0 \
    --presets "Rainbow Uniform,Turbo,Viridis (matplotlib),Cool to Warm" \
    --resolution 3840x2160
```

`pvpython` 위치 예시:
- Linux: `/opt/paraview/bin/pvpython`
- macOS: `/Applications/ParaView-5.x.app/Contents/bin/pvpython`
- Windows: `"C:\Program Files\ParaView 5.x\bin\pvpython.exe"`

### 방법 B. ParaView GUI (Run Script 버튼)

1. `run_in_paraview.py` 를 열어 맨 위 **설정** 의 경로 2줄(`MAIN_SCRIPT`, `INPUT_MODEL`)만 본인 것으로 수정
   — 출력 경로는 설정 항목이 없습니다
2. ParaView 실행 → **View → Python Shell** (구버전은 Tools → Python Shell)
3. Python Shell 의 **Run Script** 버튼 → `run_in_paraview.py` 선택
4. 작업이 끝나면 결과 폴더와 이미지가 자동으로 열립니다.

## 단위 (중요)

이 스크립트는 **mm 를 기본 단위**로 씁니다. CloudCompare / Metashape 에서 mm 로 스케일한 모델을
그대로 넣으면 됩니다.

| 옵션 | 의미 | 기본값 |
|------|------|--------|
| `--model-unit` | **모델 좌표 1 단위의 실제 크기** (`mm`/`cm`/`m`) | `mm` |
| `--unit` | **컬러바에 표시할 단위** (`mm`/`cm`/`m`/`auto`) | `mm` |

```
높이 범위 D(mm) = (high − low) × (모델단위 → mm 환산계수)
컬러바 표시값   = D(mm) / (표시단위 → mm 환산계수)
```

`--model-unit` 이 틀리면 높이가 1000배 어긋납니다. 예를 들어 OBJ 좌표의 z 범위가 `32.12` 이고
실제 높이차가 32 mm 라면 좌표 1 = 1 mm 이므로 `--model-unit mm` 입니다.
(모델이 미터 단위이면 `--model-unit m`. 스크립트가 값이 이상하면 경고를 출력합니다.)

`--unit auto` 로 두면 D < 10 mm 는 mm, < 1000 mm 는 cm, 그 이상은 m 로 자동 선택합니다.

## 컬러바(색 막대)

- 눈금 숫자는 **주석(Annotation) 방식**이 기본입니다(`--label-mode annotation`).
  값과 표시할 글자를 문자열로 직접 지정하므로, 일부 ParaView 버전에서 커스텀 라벨이
  포맷 문자열(`%-#6.2f`)을 그대로 출력하는 문제를 피할 수 있습니다.
  필요하면 `auto` / `format` / `custom` 으로 바꿀 수 있습니다.
- 눈금 값은 1 / 2 / 2.5 / 5 × 10ⁿ 의 '보기 좋은 간격'으로 고르고, 0 과 최댓값은 항상 포함합니다.
  글자끼리 겹칠 만큼 가까운 중간 눈금은 자동으로 뺍니다.
  예) 0 ~ 32 mm, `--n-labels 5` → `0, 10, 20, 30, 32`
- 글자 크기는 **출력 해상도에 비례**해 계산합니다(4K 기준 제목 52 px / 숫자 43 px, `--font-scale` 로 조절).
  저장 시 `FontScaling='Do not scale fonts'` 를 주기 때문에 ParaView 창 크기와 무관하게 동일하게 나옵니다.

## 주요 옵션

| 옵션 | 의미 | 기본값 |
|------|------|--------|
| `--input, -i` | 입력 3D 모델 (.ply/.obj/.vtk/.vtp/.stl 등) | (필수) |
| `--axis` | Elevation 기준 축 | `z` |
| `--model-unit` | 모델 좌표 1 단위의 실제 크기 (`mm`/`cm`/`m`) | `mm` |
| `--unit` | 컬러바 표시 단위 (`mm`/`cm`/`m`/`auto`) | `mm` |
| `--low` / `--high` | low/high point (모델 좌표). 미지정 시 경계상자에서 자동 검출 후 1 mm 미만 버림 | 자동 |
| `--interval` | 등고선 간격(mm) | `1.0` |
| `--line-width` | 등고선 굵기 (4K 는 2~3 권장) | `1.0` |
| `--max-contours` | 등고선 최대 개수 안전 한계 | `2000` |
| `--presets` | 콤마로 구분한 컬러 프리셋 목록 (프리셋마다 이미지 생성) | `Rainbow Uniform,Turbo,Viridis (matplotlib),Cool to Warm` |
| `--preset` | 프리셋 1개만 쓸 때 (구버전 호환) | — |
| `--list-presets` | 설치본에서 쓸 수 있는 프리셋 이름 출력 후 종료 | off |
| `--resolution` | 저장 이미지 해상도 WxH (16:9 권장) | `3840x2160` |
| `--label-mode` | 눈금 숫자 방식 (`annotation`/`auto`/`format`/`custom`) | `annotation` |
| `--n-labels` | 눈금 숫자 목표 개수 | `5` |
| `--font-scale` | 컬러바 글자/막대 크기 배율 | `1.0` |
| `--colorbar-frac` | 컬러바가 차지할 오른쪽 폭 비율 | `0.20` |
| `--margin` | 이미지 가장자리 여백 비율 | `0.04` |
| `--perspective` | 원근 투영 사용 (기본은 정사영) | off |
| `--no-contour-colorbar` | 등고선 이미지에는 컬러바를 넣지 않음 | off |
| `--no-contour` | 등고선 생략(높이지도만) | off |
| `--no-state` | `.pvsm` 상태 파일 저장 생략 | off |
| `--no-open` | 끝나고 결과 폴더/이미지를 자동으로 열지 않음 | off |
| `--open-images` | 자동으로 띄울 elevation 이미지 개수 | `4` |

## 출력물

입력 모델 폴더 안에 `paraview_image/` 가 자동으로 생기고, 그 안에 저장됩니다.

```
<모델폴더>/
├─ model.obj
└─ paraview_image/
   ├─ model_rainbow_uniform_elevation.png
   ├─ model_rainbow_uniform_contour.png
   ├─ model_turbo_elevation.png
   ├─ model_turbo_contour.png
   ├─ ...
   └─ model_state.pvsm
```

- 두 이미지는 카메라가 동일하므로 그대로 겹쳐 볼 수 있습니다.
- 배경은 흰색, 모든 글자는 검정, 모델은 컬러바를 침범하지 않는 한도에서 최대 크기로 배치됩니다.

## 매뉴얼 스텝 ↔ 코드 대응

| 매뉴얼 | 동작 | 코드 |
|--------|------|------|
| Step 1–2 | 모델 열기 + 선택 | `OpenDataFile` / `SetActiveSource` |
| Step 3 | Filters > Elevation | `Elevation()` |
| Step 4 | Z축 선택 + Apply | `LowPoint` / `HighPoint` |
| Step 5 | 'show line' 해제 | 3D 위젯일 뿐, 저장 결과에 무관 → 배치에서 무시 |
| Step 6 | low/high 에서 1 mm 미만 버림 | `floor(v / q) · q`, `q` = 모델 좌표로 표현한 1 mm |
| Step 7 | Scalar Range 0~1 → 0~D | `ScalarRange = [0, D/factor]` |
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
출력 = ScalarRange0 + s·(ScalarRange1 − ScalarRange0) = s·D/factor
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

**카메라 (컬러바와 겹치지 않는 최대 확대):**
화면을 `[ 여백 | 모델 frac_w | 간격 | 컬러바 ]` 로 나누고, 경계상자의 화면상 반너비 `hw`,
반높이 `hh` 에 대해

```
CameraParallelScale S = max( hh / frac_h , hw / (frac_w · aspect) )
모델 영역 중심으로 이동 Δ = (0.5 − xc) · 2·S·aspect
```

## 주의: 입력은 '메시(mesh)' 여야 합니다

Elevation/Contour 필터는 입력의 형태(topology)를 바꾸지 않습니다.
면(face)이 없는 **점군(point cloud)** 을 넣으면 결과도 점으로 나오고 등고선이 제대로 만들어지지 않습니다.
매뉴얼이 가정하는 입력은 Metashape **Build Mesh** 로 만든 메시입니다.

## 문제 해결

| 증상 | 원인 / 해결 |
|------|------------|
| 컬러바 단위가 m 로 나온다 | `--model-unit` 이 실제와 다름. mm 모델이면 `--model-unit mm` (기본값) |
| 눈금에 `%-#6.2f` 같은 글자가 찍힌다 | 일부 ParaView 버전의 커스텀 라벨 버그. `--label-mode annotation`(기본) 또는 `auto` 사용 |
| 컬러바 글자가 너무 작다/크다 | `--font-scale` 조절. 숫자가 잘리면 `--colorbar-frac` 을 0.24~0.28 로 |
| 등고선이 너무 많다는 오류 | `--interval` 을 키우거나 `--model-unit` 이 맞는지 확인 (단위가 틀리면 D 가 1000배) |
| 프리셋이 적용되지 않는다 | `--list-presets` 로 설치본의 정확한 이름 확인 |

## 참고(References)

- Elevation 필터: <https://www.paraview.org/paraview-docs/v5.13.0/python/paraview.simple.Elevation.html>
- Contour 필터: <https://www.paraview.org/paraview-docs/v5.13.3/python/paraview.simple.Contour.html>
- 색상 매핑(ColorBy/ApplyPreset/Annotations): <https://docs.paraview.org/en/v5.13.0/ReferenceManual/colorMapping.html>
- 결과 저장(SaveScreenshot/SaveState): <https://docs.paraview.org/en/v5.10.0/UsersGuide/savingResults.html>
