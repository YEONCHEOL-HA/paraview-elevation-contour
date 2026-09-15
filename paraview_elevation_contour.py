#!/usr/bin/env pvpython
# -*- coding: utf-8 -*-
"""
paraview_elevation_contour.py   (v3)
=============================================================================
"Guide to 3D modelling" 매뉴얼의 마지막 섹션
    "Quick Guide to Visualising the Model as Elevation (height maps)
     and Contour images using Paraview"  (Step 1 ~ Step 12)
를 GUI 조작 없이 자동으로 수행하는 스크립트.

    pvpython paraview_elevation_contour.py --input model.obj
    (기본 단위는 mm — 모델 좌표가 미터라면 --model-unit m 을 붙인다)

결과는 항상 '입력 모델이 있는 폴더/paraview_image/' 에 저장된다(자동 생성).
출력 경로를 지정하는 옵션은 없다.

-----------------------------------------------------------------------------
매뉴얼 스텝 <-> 코드 대응표
-----------------------------------------------------------------------------
  Step 1  모델 열기                     -> OpenDataFile()      (load_model)
  Step 2  Pipeline 에서 모델 선택        -> SetActiveSource()   (load_model)
  Step 3  Filters > Elevation           -> Elevation()         (make_elevation)
  Step 4  Z 축 선택 후 Apply             -> LowPoint/HighPoint  (make_elevation)
  Step 5  'show line' 해제               -> 3D 위젯일 뿐, 렌더 결과에 무관 (주석)
  Step 6  low/high point 를 mm 로 반올림  -> _truncate_to_mm()   (make_elevation)
  Step 7  Scalar Range 0~1 -> 0~높이     -> ScalarRange         (make_elevation)
  Step 8  Coloring preset 적용           -> ApplyPreset()       (apply_preset)
  Step 9  Filters > Contour             -> Contour()           (make_contour)
  Step 10 Contour 색을 검정으로          -> Solid color [0,0,0] (color_contour)
  Step 11 Value Range 에 steps 추가      -> Isosurfaces=linspace (make_contour)
  Step 12 elevation / contour 이미지 저장 -> SaveScreenshot()    (save_pair)
          + Save state                  -> SaveState()         (main)

=============================================================================
[v3 변경점]
=============================================================================
(A) 단위: mm 가 기본이다.
      --model-unit : 모델 좌표 1 단위의 실제 크기.  기본 mm.
                     (CloudCompare / Metashape 에서 mm 로 스케일한 모델 기준)
                     모델이 미터 단위면 --model-unit m 으로 바꾼다.
      --unit       : 컬러바에 표시할 단위.  기본 mm (auto 로 두면 크기에 따라
                     mm/cm/m 를 자동 선택).
    높이 범위 D(mm) = (high - low) * (모델단위 -> mm 환산계수)
    이전 버전은 모델 좌표를 항상 '미터'로 가정해서, 실제로는 32 mm 인 모델이
    32 m 로 표시되는 문제가 있었다.

(B) 컬러바 눈금 숫자: 기본 방식을 '주석(Annotation)' 으로 바꿨다.
    이전 버전은 UseCustomLabels + LabelFormat 을 썼는데, ParaView 의 일부
    버전에서 커스텀 라벨이 포맷 문자열("%-#6.2f")을 그대로 출력하는 버그가
    있다(맨 위/아래 범위 라벨은 RangeLabelFormat 을 쓰므로 정상 출력됨 —
    화면에 0.00 과 32.12 만 제대로 보였던 이유).
    => 주석 방식은 '값'과 '표시할 글자'를 직접 문자열로 주기 때문에
       포맷 문자열이 개입할 여지가 아예 없다.  --label-mode 로 전환 가능:
         annotation (기본) : LUT Annotations 로 값+글자를 직접 지정
         auto              : ParaView 자동 눈금/자동 포맷
         format            : 자동 눈금 + printf 포맷("%-#6.1f" 스타일)
         custom            : 예전 UseCustomLabels 방식(버그 있는 버전 주의)

(C) 글자 크기: 출력 해상도에 비례해 계산 + SaveScreenshot 에
    FontScaling='Do not scale fonts' 를 줘서 GUI 창 크기와 무관하게 고정.

(D) --presets 로 여러 컬러 프리셋의 이미지를 한 번에 생성.

(E) 출력 경로 설정 제거: 결과는 입력 모델 폴더 안의 paraview_image/ 에 저장된다.
=============================================================================
근거(References):
  - paraview.simple.Elevation  (LowPoint/HighPoint/ScalarRange) :
      https://www.paraview.org/paraview-docs/v5.13.0/python/paraview.simple.Elevation.html
  - paraview.simple.Contour    (ContourBy/Isosurfaces) :
      https://www.paraview.org/paraview-docs/v5.13.3/python/paraview.simple.Contour.html
  - Color maps / Annotations / Color legend :
      https://docs.paraview.org/en/v5.13.0/ReferenceManual/colorMapping.html
  - Saving results (SaveScreenshot FontScaling / SaveState) :
      https://docs.paraview.org/en/v5.10.0/UsersGuide/savingResults.html
=============================================================================
"""

from __future__ import print_function

import argparse
import math
import os
import re
import sys

try:
    from paraview.simple import (
        OpenDataFile, SetActiveSource, Elevation, Contour, Show, Hide,
        ColorBy, GetColorTransferFunction, GetScalarBar, GetActiveViewOrCreate,
        ResetCamera, Render, SaveScreenshot, SaveState,
    )
except ImportError:
    sys.stderr.write(
        "\n[오류] 'paraview.simple' 모듈을 불러올 수 없습니다.\n"
        "       이 스크립트는 반드시 ParaView 의 파이썬 인터프리터로 실행해야 합니다.\n\n"
        "       예) pvpython paraview_elevation_contour.py --input model.ply\n"
        "           pvbatch  paraview_elevation_contour.py --input model.ply\n\n"
        "       (pvpython/pvbatch 는 ParaView 설치 폴더의 bin/ 안에 있습니다.)\n"
    )
    sys.exit(1)

try:
    from paraview.simple import LoadPalette
except ImportError:  # pragma: no cover - 구버전 ParaView
    LoadPalette = None


BLACK = [0.0, 0.0, 0.0]
WHITE = [1.0, 1.0, 1.0]

DEFAULT_COLORBAR_FRAC = 0.20
DEFAULT_MARGIN = 0.04
DEFAULT_N_LABELS = 5

# 폰트/막대 크기 = 이미지 세로 픽셀 x 비율 x --font-scale
TITLE_FONT_FRAC = 0.024   # 2160px -> 52px
LABEL_FONT_FRAC = 0.020   # 2160px -> 43px
BAR_THICK_FRAC = 0.016    # 2160px -> 35px

DEFAULT_PRESETS = "Rainbow Uniform,Turbo,Viridis (matplotlib),Cool to Warm"

# 결과 이미지를 저장할 폴더 이름.  입력 모델이 있는 폴더 안에 이 이름으로 만든다.
OUTPUT_FOLDER_NAME = "paraview_image"

# 단위 -> mm 환산.  1 (그 단위) = N mm
UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0}


# =============================================================================
# 유틸리티
# =============================================================================
def _axis_index(axis):
    return {"x": 0, "y": 1, "z": 2}[axis.lower()]


def log(msg):
    print("[paraview-auto] " + msg)
    try:
        sys.stdout.flush()
    except Exception:
        pass


def _try_set(obj, name, value):
    """버전마다 없는 속성이 있으므로 조용히 넘어가는 setattr 헬퍼. 성공 시 True."""
    try:
        setattr(obj, name, value)
        return True
    except Exception:
        return False


def _add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def _scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _normalize(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0.0:
        return [0.0, 0.0, 0.0]
    return [v[0] / n, v[1] / n, v[2] / n]


def _slug(text):
    """'Viridis (matplotlib)' -> 'viridis_matplotlib'"""
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(text)).strip("_").lower()
    return s or "preset"


def _truncate_to_mm(value_model, model_to_mm):
    """
    Step 6: "delete submillimeter numbers".
    모델 좌표값에서 '1 mm 미만'을 버린다(버림/floor — 매뉴얼 예시가 버림).

      1 mm = q (모델 단위)  ->  q = 1 / model_to_mm
      결과 = floor(value / q) * q

    예) 모델이 m 단위(model_to_mm=1000): q=0.001
        0.012838485 m -> 0.012 m (= 12 mm)          [매뉴얼 예시와 동일]
        모델이 mm 단위(model_to_mm=1): q=1
        31.82 -> 31 (= 31 mm)

    주의: 부동소수점 오차 보정을 위해 round(...,6) 후 floor.
    """
    q = 1.0 / float(model_to_mm)
    return math.floor(round(value_model / q, 6)) * q


# =============================================================================
# 단위
# =============================================================================
def resolve_unit(distance_mm, unit="mm"):
    """
    컬러바 표시 단위 결정.
        D <   10 mm          -> mm
        10 <= D < 1000 mm    -> cm
        D >= 1000 mm         -> m
    반환: (단위이름, factor);  표시값 = mm값 / factor
    """
    u = (unit or "mm").lower()
    if u == "auto":
        if distance_mm < 10.0:
            u = "mm"
        elif distance_mm < 1000.0:
            u = "cm"
        else:
            u = "m"
    if u not in UNIT_TO_MM:
        raise ValueError("알 수 없는 단위: %s (mm/cm/m/auto 중 하나)" % unit)
    return u, UNIT_TO_MM[u]


# =============================================================================
# 눈금 숫자
# =============================================================================
def _nice_step(rough):
    """rough 이상이면서 가장 가까운 '보기 좋은 간격'(1, 2, 2.5, 5 x 10^n)."""
    if rough <= 0:
        return 1.0
    exp = math.floor(math.log10(rough))
    base = 10.0 ** exp
    f = rough / base
    for m in (1.0, 2.0, 2.5, 5.0, 10.0):
        if f <= m * (1.0 + 1e-9):
            return m * base
    return 10.0 * base


def _decimals_for(value, max_d=3):
    """value 를 오차 없이 적는 데 필요한 소수 자릿수(최대 max_d)."""
    v = abs(float(value))
    for d in range(0, max_d + 1):
        scaled = v * (10.0 ** d)
        if abs(scaled - round(scaled)) < 1e-6:
            return d
    return max_d


def _fmt_value(value, max_d=3):
    """숫자를 '필요한 자릿수만' 써서 문자열로. 10 -> '10', 32.12 -> '32.12'"""
    d = _decimals_for(value, max_d)
    s = ("%%.%df" % d) % float(value)
    if s == "-0":
        s = "0"
    return s


def build_labels(span, n_target=DEFAULT_N_LABELS, bar_px=0.0, label_px=0.0,
                 max_d=3):
    """
    0 ~ span 에 찍을 눈금값 목록을 만든다.  반환: [(값, 표시문자열), ...]

    - 간격은 1/2/2.5/5 x 10^n 중에서 고른다 (span/n_target 이상인 최소값).
    - 0 과 span(최댓값)은 항상 포함한다.
    - 양 끝 글자와 겹칠 만큼 가까운 중간 눈금은 뺀다.
        필요한 최소 간격(픽셀) ~= 1.9 x 글자높이
        -> 값으로 환산하면  min_sep = span * 1.9*label_px/bar_px
    """
    if span <= 0:
        return [(0.0, "0")]
    n_target = max(2, int(n_target))
    step = _nice_step(span / float(n_target))

    interior = []
    i = 1
    while i * step < span * (1.0 - 1e-9):
        interior.append(i * step)
        i += 1

    min_sep = 0.0
    if bar_px > 0 and label_px > 0:
        min_sep = span * (1.9 * float(label_px) / float(bar_px))

    interior = [t for t in interior if t > min_sep and (span - t) > min_sep]

    values = [0.0] + interior + [float(span)]
    return [(v, _fmt_value(v, max_d)) for v in values]


def paraview_label_format(decimals):
    """
    ParaView 가 확실히 인식하는 printf 형식(기본값이 '%-#6.3g' / '%-#6.1f').
    '%.1f' 처럼 폭/플래그가 없는 형식은 일부 버전에서 그대로 출력된다.
    """
    return "%%-#6.%df" % int(max(0, min(6, decimals)))


# =============================================================================
# Step 1 ~ 2 : 모델 열기 + 활성화
# =============================================================================
def load_model(path):
    if not os.path.isfile(path):
        raise IOError("입력 파일을 찾을 수 없습니다: %s" % path)

    log("Step 1-2: 모델 로드 -> %s" % path)
    reader = OpenDataFile(path)
    if reader is None:
        raise RuntimeError(
            "ParaView 가 이 파일 형식을 열 수 있는 리더를 찾지 못했습니다: %s" % path)
    SetActiveSource(reader)
    # 파일을 연 직후엔 데이터가 아직 안 읽혀 GetBounds() 가 빈 경계상자를 준다.
    reader.UpdatePipeline()
    return reader


# =============================================================================
# Step 3 ~ 7 : Elevation 필터
# =============================================================================
def make_elevation(reader, axis="z", low=None, high=None,
                   model_unit="mm", unit="mm"):
    """
    Step 3/4/6/7.
    반환: (elevation 필터, D(mm), 표시단위이름, 표시단위 factor)

    단위 처리
      model_to_mm = UNIT_TO_MM[model_unit]     # 모델 좌표 1 단위 = 몇 mm 인가
      D(mm)       = (high - low) * model_to_mm
      표시값      = D(mm) / factor             # factor = UNIT_TO_MM[표시단위]

    vtkElevationFilter 수학:
      s = clamp( ((P-L)·(H-L)) / |H-L|^2, 0, 1 )
      출력 = ScalarRange[0] + s*(ScalarRange[1]-ScalarRange[0]) = s * D/factor
    """
    ai = _axis_index(axis)
    mu = (model_unit or "mm").lower()
    if mu not in UNIT_TO_MM:
        raise ValueError("--model-unit 은 mm/cm/m 중 하나여야 합니다: %s" % model_unit)
    model_to_mm = UNIT_TO_MM[mu]

    reader.UpdatePipeline()
    bounds = reader.GetDataInformation().GetBounds()
    axis_min = bounds[2 * ai]
    axis_max = bounds[2 * ai + 1]

    if axis_min > axis_max:
        raise RuntimeError(
            "모델의 경계상자를 읽지 못했습니다(빈 데이터): bounds=%s" % (bounds,))

    raw_span_mm = (axis_max - axis_min) * model_to_mm
    log("모델 좌표 단위: %s  (좌표 1 = %g mm)   |  %s축 원본 범위 %.4f ~ %.4f "
        "(= %.4g mm)"
        % (mu, model_to_mm, axis.upper(), axis_min, axis_max, raw_span_mm))

    # 단위를 잘못 잡으면 높이가 1000배 어긋난다. 양쪽 방향 모두 경고한다.
    if mu == "mm" and raw_span_mm < 1.0:
        log("  ! 주의: mm 단위로 보면 높이 차가 %.4g mm 밖에 안 됩니다."
            % raw_span_mm)
        log("    모델 좌표가 '미터' 단위일 수 있습니다."
            "  -> --model-unit m (런처: MODEL_UNIT = \"m\")")
    elif mu == "m" and raw_span_mm > 5000.0:
        log("  ! 주의: 미터 단위로 보면 높이 차가 %.1f m 입니다." % (raw_span_mm / 1000.0))
        log("    표본/노두 스캔이라면 모델 좌표가 mm 단위일 가능성이 큽니다."
            "  -> --model-unit mm (런처: MODEL_UNIT = \"mm\")")

    # Step 6: 값을 주지 않으면 경계상자에서 자동으로 잡고 1 mm 미만은 버린다.
    if low is None:
        low = _truncate_to_mm(axis_min, model_to_mm)
    if high is None:
        high = _truncate_to_mm(axis_max, model_to_mm)

    if high <= low:
        raise ValueError(
            "high point(%.4f) 가 low point(%.4f) 보다 커야 합니다. "
            "--low / --high 로 직접 지정해 보세요." % (high, low))

    distance_mm = (high - low) * model_to_mm
    # mm 단위로는 정수로 떨어지게 정리(매뉴얼 Step 6 의 취지)
    distance_mm = round(distance_mm, 3)

    unit_name, factor = resolve_unit(distance_mm, unit)
    span_disp = distance_mm / factor

    log("Step 4/6: %s축 low=%.4f, high=%.4f (모델좌표) -> 높이 범위 D=%.4g mm "
        "(= %.4g %s)" % (axis.upper(), low, high, distance_mm,
                         span_disp, unit_name))

    elev = Elevation(Input=reader)

    low_pt = [0.0, 0.0, 0.0]
    high_pt = [0.0, 0.0, 0.0]
    low_pt[ai] = low
    high_pt[ai] = high
    elev.LowPoint = low_pt
    elev.HighPoint = high_pt

    # Step 7: 스칼라 값 자체가 '표시 단위의 높이'가 되도록
    elev.ScalarRange = [0.0, float(span_disp)]
    elev.UpdatePipeline()
    log("Step 3/7: Elevation 필터 적용, ScalarRange = [0, %.6g] %s"
        % (span_disp, unit_name))

    return elev, distance_mm, unit_name, factor


def available_presets():
    """설치본에 들어있는 컬러 프리셋 이름 목록(가능하면)."""
    try:
        from paraview import servermanager as sm
        presets = sm.vtkSMTransferFunctionPresets.GetInstance()
        return [presets.GetPresetName(i)
                for i in range(presets.GetNumberOfPresets())]
    except Exception:
        return []


def show_elevation(elev, view):
    """Elevation 표면을 'Elevation' 스칼라로 색칠해 화면에 올린다."""
    disp = Show(elev, view)
    disp.Representation = "Surface"
    ColorBy(disp, ("POINTS", "Elevation"))
    lut = GetColorTransferFunction("Elevation")
    try:
        disp.SetScalarBarVisibility(view, True)
    except Exception:
        pass
    return disp, lut


def apply_preset(lut, preset, known=None):
    """Step 8: 컬러 프리셋 적용. 성공하면 True."""
    if known and preset not in known:
        log("  ! 프리셋 '%s' 가 이 ParaView 설치본에 없습니다. 건너뜁니다." % preset)
        return False
    try:
        lut.ApplyPreset(preset, True)   # True = 프리셋의 전체 색을 그대로 적용
        log("Step 8: 컬러 프리셋 '%s' 적용" % preset)
        return True
    except Exception as exc:
        log("  ! 프리셋 '%s' 적용 실패(%s)." % (preset, exc))
        return False


# =============================================================================
# 배경 / 글자색 / 컬러바 모양
# =============================================================================
def setup_white_view(view, resolution):
    """배경 흰색 + 글자 검정. (저장 시점에도 한 번 더 강제 — _save_png 참고)"""
    if LoadPalette is not None:
        try:
            LoadPalette(paletteName="WhiteBackground")
        except Exception:
            pass

    _try_set(view, "UseColorPaletteForBackground", 0)
    _try_set(view, "BackgroundColorMode", "Single Color")
    _try_set(view, "UseGradientBackground", 0)
    _try_set(view, "Background", list(WHITE))
    _try_set(view, "Background2", list(WHITE))

    _try_set(view, "OrientationAxesVisibility", 0)
    _try_set(view, "OrientationAxesLabelColor", list(BLACK))
    _try_set(view, "CenterAxesVisibility", 0)

    try:
        grid = view.AxesGrid
        for prop in ("XTitleColor", "YTitleColor", "ZTitleColor",
                     "XLabelColor", "YLabelColor", "ZLabelColor",
                     "GridColor"):
            _try_set(grid, prop, list(BLACK))
    except Exception:
        pass

    _try_set(view, "ViewSize", [int(resolution[0]), int(resolution[1])])


def _clear_annotations(lut):
    _try_set(lut, "Annotations", [])


def style_scalar_bar(lut, view, unit_name, span_disp, resolution,
                     colorbar_frac=DEFAULT_COLORBAR_FRAC, margin=DEFAULT_MARGIN,
                     n_labels=DEFAULT_N_LABELS, font_scale=1.0,
                     label_mode="annotation", label_format=None, title=None):
    """
    컬러바: 오른쪽 세로 막대 / 큰 검정 글씨 / 눈금 숫자 소수 개.

    label_mode
      "annotation" (기본) : LUT 의 Annotations 로 '값 + 표시할 글자'를 직접 지정.
                            글자를 문자열로 직접 주므로 포맷 문자열이 그대로
                            찍히는 ParaView 버그의 영향을 받지 않는다.
      "auto"              : ParaView 자동 눈금 + 자동 포맷.
      "format"            : 자동 눈금 + printf 포맷("%-#6.1f" 스타일).
      "custom"            : UseCustomLabels (버전에 따라 포맷 문자열이 그대로
                            출력되는 버그가 있음 — 권장하지 않음).
    """
    sb = GetScalarBar(lut, view)
    height = float(resolution[1])

    title_fs = max(14, int(round(height * TITLE_FONT_FRAC * font_scale)))
    label_fs = max(12, int(round(height * LABEL_FONT_FRAC * font_scale)))
    thickness = max(8, int(round(height * BAR_THICK_FRAC * font_scale)))

    _try_set(sb, "Title", title if title is not None
             else "Elevation (%s)" % unit_name)
    _try_set(sb, "ComponentTitle", "")

    _try_set(sb, "TitleColor", list(BLACK))
    _try_set(sb, "LabelColor", list(BLACK))
    _try_set(sb, "TitleFontSize", title_fs)
    _try_set(sb, "LabelFontSize", label_fs)
    _try_set(sb, "TitleBold", 1)
    _try_set(sb, "LabelBold", 0)
    _try_set(sb, "TitleOpacity", 1.0)
    _try_set(sb, "LabelOpacity", 1.0)
    _try_set(sb, "TitleFontFamily", "Arial")
    _try_set(sb, "LabelFontFamily", "Arial")

    _try_set(sb, "Orientation", "Vertical")
    for loc in ("Any Location", "AnyLocation"):
        if _try_set(sb, "WindowLocation", loc):
            break

    bar_x = 1.0 - colorbar_frac + 0.015
    bar_y = margin + 0.06
    bar_len = max(0.2, 1.0 - 2.0 * bar_y)
    _try_set(sb, "Position", [bar_x, bar_y])
    _try_set(sb, "ScalarBarLength", bar_len)
    _try_set(sb, "ScalarBarThickness", thickness)

    # ---- 눈금 숫자 ----------------------------------------------------------
    bar_px = bar_len * height
    labels = build_labels(span_disp, n_labels, bar_px=bar_px, label_px=label_fs)
    decimals = max([_decimals_for(v) for v, _ in labels] or [0])
    mode = (label_mode or "annotation").lower()

    _clear_annotations(lut)

    if mode == "annotation":
        # Annotations = [값1(문자열), 글자1, 값2, 글자2, ...]
        flat = []
        for v, txt in labels:
            flat += ["%.10g" % v, txt]
        ok = _try_set(lut, "Annotations", flat)
        if ok:
            _try_set(sb, "DrawAnnotations", 1)
            _try_set(sb, "AddRangeAnnotations", 0)
            _try_set(sb, "AutomaticAnnotations", 0)
            _try_set(sb, "DrawTickLabels", 0)   # 자동 숫자는 끈다(중복 방지)
            _try_set(sb, "DrawTickMarks", 0)
            _try_set(sb, "AddRangeLabels", 0)
            _try_set(sb, "AnnotationTextScaling", 0)
            shown = ", ".join(t for _, t in labels)
        else:
            log("  ! Annotations 설정 실패 -> 자동 눈금으로 전환")
            mode = "auto"

    if mode in ("auto", "format", "custom"):
        _try_set(sb, "DrawAnnotations", 0)
        _try_set(sb, "DrawTickLabels", 1)
        _try_set(sb, "DrawTickMarks", 1)
        _try_set(sb, "AddRangeLabels", 1)

        if mode == "auto":
            _try_set(sb, "AutomaticLabelFormat", 1)
            _try_set(sb, "UseCustomLabels", 0)
            shown = "(ParaView 자동)"
        else:
            fmt = label_format or paraview_label_format(decimals)
            ok = _try_set(sb, "AutomaticLabelFormat", 0)
            okf = _try_set(sb, "LabelFormat", fmt)
            _try_set(sb, "RangeLabelFormat", fmt)
            if not (ok and okf):
                _try_set(sb, "AutomaticLabelFormat", 1)
            if mode == "custom":
                inner = [float(v) for v, _ in labels[1:-1]]
                if inner and _try_set(sb, "UseCustomLabels", 1):
                    _try_set(sb, "CustomLabels", inner)
                shown = ", ".join(t for _, t in labels) + "  (custom, %s)" % fmt
            else:
                _try_set(sb, "UseCustomLabels", 0)
                shown = "(자동 눈금, 포맷 %s)" % fmt

    log("컬러바: 'Elevation (%s)', 0 ~ %s %s | 눈금 [%s] | 모드 %s | "
        "제목/숫자 %dpx/%dpx | 오른쪽 %d%%"
        % (unit_name, _fmt_value(span_disp), unit_name, shown, mode,
           title_fs, label_fs, round(colorbar_frac * 100)))
    return sb


# =============================================================================
# Step 9 ~ 11 : Contour 필터
# =============================================================================
def make_contour(elev, distance_mm, interval_mm=1.0, max_contours=2000,
                 factor=1.0, unit_name="mm"):
    """
    Step 9/11.
      steps N = D/δ + 1,  값 v_i = i·δ  (i = 0 ... D/δ)  == linspace(0, D, N)
    등고선 간격은 mm 로 받아 표시 단위로 환산해 넣는다(스칼라와 단위를 맞춰야 함).
    """
    if interval_mm <= 0:
        raise ValueError("등고선 간격(interval_mm)은 0보다 커야 합니다.")

    n_intervals = int(round(distance_mm / interval_mm))
    n_steps = n_intervals + 1

    if n_steps > max_contours:
        suggested = math.ceil(distance_mm / (max_contours - 1) * 10) / 10.0
        raise ValueError(
            "등고선이 %d 개나 생성됩니다 (높이범위 D=%.4g mm, 간격 %.3g mm).\n"
            "       ParaView 가 메모리 부족으로 튕길 수 있어 중단했습니다.\n"
            "       => 간격(--interval / INTERVAL_MM)을 약 %.1f mm 이상으로 키우거나,\n"
            "          --max-contours 값을 올리세요.\n"
            "       (모델 좌표 단위 설정 --model-unit 이 맞는지도 확인하세요. "
            "단위를 잘못 잡으면 D 가 1000배로 계산됩니다.)"
            % (n_steps, distance_mm, interval_mm, suggested))

    values = [round(i * interval_mm / factor, 9) for i in range(n_steps)]

    contour = Contour(Input=elev)
    contour.ContourBy = ["POINTS", "Elevation"]
    contour.Isosurfaces = values
    contour.UpdatePipeline()

    log("Step 9/11: Contour - 간격 %.3g mm (= %.4g %s), 등고선 %d개 (0 ~ %.4g %s)"
        % (interval_mm, interval_mm / factor, unit_name, n_steps,
           distance_mm / factor, unit_name))
    return contour


def color_contour(contour, view, line_width=1.0):
    """Step 10: 등고선을 검정 단색으로."""
    disp = Show(contour, view)
    disp.Representation = "Surface"
    ColorBy(disp, None)
    disp.AmbientColor = list(BLACK)
    disp.DiffuseColor = list(BLACK)
    _try_set(disp, "LineWidth", float(line_width))
    log("Step 10: Contour 검정 단색, 선 두께 %.1f" % line_width)
    return disp


# =============================================================================
# 카메라
# =============================================================================
def frame_model(view, bounds, axis, resolution,
                colorbar_frac=DEFAULT_COLORBAR_FRAC, margin=DEFAULT_MARGIN,
                parallel=True, gap=0.02):
    """
    축 방향 top-down 카메라 + '컬러바 영역을 뺀 나머지'에 모델을 꽉 채우기.

      화면 분할: [ margin | 모델 frac_w | gap | 컬러바 colorbar_frac ]
      S = CameraParallelScale = max( hh/frac_h , hw/(frac_w·aspect) )
      가로 이동  Δ = (0.5 − xc)·2·S·aspect
      원근이면   d = S / tan(θ/2)
    """
    ai = _axis_index(axis)
    w, h = float(resolution[0]), float(resolution[1])
    aspect = w / h

    center = [0.5 * (bounds[0] + bounds[1]),
              0.5 * (bounds[2] + bounds[3]),
              0.5 * (bounds[4] + bounds[5])]
    half = [0.5 * (bounds[1] - bounds[0]),
            0.5 * (bounds[3] - bounds[2]),
            0.5 * (bounds[5] - bounds[4])]
    diag = math.sqrt(4.0 * (half[0] ** 2 + half[1] ** 2 + half[2] ** 2)) or 1.0

    axis_dir = [0.0, 0.0, 0.0]
    axis_dir[ai] = 1.0
    view_up = [0.0, 1.0, 0.0] if ai == 2 else [0.0, 0.0, 1.0]
    forward = _scale(axis_dir, -1.0)
    right = _normalize(_cross(forward, view_up))
    up = _normalize(view_up)

    hw = abs(right[0]) * half[0] + abs(right[1]) * half[1] + abs(right[2]) * half[2]
    hh = abs(up[0]) * half[0] + abs(up[1]) * half[1] + abs(up[2]) * half[2]
    hw = hw or 1e-6
    hh = hh or 1e-6

    colorbar_frac = max(0.0, min(0.5, colorbar_frac))
    margin = max(0.0, min(0.3, margin))
    right_reserved = (colorbar_frac + gap) if colorbar_frac > 0 else margin
    frac_w = max(0.1, 1.0 - margin - right_reserved)
    frac_h = max(0.1, 1.0 - 2.0 * margin)

    scale = max(hh / frac_h, hw / (frac_w * aspect))

    xc = margin + 0.5 * frac_w
    shift = (0.5 - xc) * 2.0 * scale * aspect
    focal = _add(center, _scale(right, shift))

    if parallel:
        _try_set(view, "CameraParallelProjection", 1)
        dist = diag * 2.0 + 1.0
        _try_set(view, "CameraParallelScale", scale)
    else:
        _try_set(view, "CameraParallelProjection", 0)
        try:
            angle = float(view.CameraViewAngle)
        except Exception:
            angle = 30.0
        dist = scale / math.tan(math.radians(angle * 0.5))

    view.CameraFocalPoint = focal
    view.CameraPosition = _add(focal, _scale(axis_dir, dist))
    view.CameraViewUp = up
    _try_set(view, "CenterOfRotation", list(center))

    Render(view)
    log("카메라: %s축 top-down, %s 투영, 모델이 가로의 %d%% 를 채움 (오른쪽 %d%% 컬러바)"
        % (axis.upper(), "정사영" if parallel else "원근",
           round(frac_w * 100), round(colorbar_frac * 100)))


# =============================================================================
# Step 12 : 이미지 저장
# =============================================================================
def _save_png(path, view, resolution):
    """
    SaveScreenshot 래퍼.
      * OverrideColorPalette='WhiteBackground' -> 저장본도 흰 배경/검정 글자
      * FontScaling='Do not scale fonts'
          -> GUI 창 크기에 비례해 글자가 멋대로 커지거나 작아지는 것을 막는다.
             (기본값 'Scale fonts proportionally' 는 창 높이 대비 배율로
              글자를 스케일하므로 재현이 안 된다)
    버전에 따라 인자가 없을 수 있어 단계적으로 폴백한다.
    """
    res = [int(resolution[0]), int(resolution[1])]
    attempts = (
        dict(ImageResolution=res, TransparentBackground=0,
             OverrideColorPalette="WhiteBackground",
             FontScaling="Do not scale fonts"),
        dict(ImageResolution=res, TransparentBackground=0,
             FontScaling="Do not scale fonts"),
        dict(ImageResolution=res, TransparentBackground=0,
             OverrideColorPalette="WhiteBackground"),
        dict(ImageResolution=res, TransparentBackground=0),
        dict(ImageResolution=res),
    )
    last = None
    for kwargs in attempts:
        try:
            SaveScreenshot(path, view, **kwargs)
            return
        except Exception as exc:
            last = exc
    raise RuntimeError("이미지 저장 실패: %s (%s)" % (path, last))


def save_pair(elev_disp, contour_disp, view, resolution,
              elev_png, cont_png, scalar_bar=None, contour_colorbar=True):
    """elevation 만 보이게 저장 -> contour 만 보이게 저장 (카메라 동일)."""
    elev_disp.Visibility = 1
    if contour_disp is not None:
        contour_disp.Visibility = 0
    Render(view)
    _save_png(elev_png, view, resolution)
    log("  -> elevation 저장: %s (%dx%d)"
        % (os.path.basename(elev_png), resolution[0], resolution[1]))

    if contour_disp is not None and cont_png:
        elev_disp.Visibility = 0
        contour_disp.Visibility = 1
        # elevation 을 숨기면 컬러바도 사라지므로 필요하면 다시 켠다.
        if contour_colorbar and scalar_bar is not None:
            _try_set(scalar_bar, "Visibility", 1)
        Render(view)
        _save_png(cont_png, view, resolution)
        log("  -> contour 저장  : %s (%dx%d)"
            % (os.path.basename(cont_png), resolution[0], resolution[1]))
    else:
        cont_png = None

    elev_disp.Visibility = 1
    if contour_disp is not None:
        contour_disp.Visibility = 1
    Render(view)
    return elev_png, cont_png


# =============================================================================
# 결과 폴더 / 결과 열기
# =============================================================================
def output_dir_for(input_path, folder_name=OUTPUT_FOLDER_NAME):
    """
    결과 폴더는 항상 '입력 모델이 들어있는 폴더' 안의 paraview_image 다.
      <모델 폴더>/model.obj  ->  <모델 폴더>/paraview_image/
    출력 경로를 따로 지정하는 옵션은 없다(경로를 두 군데 고치다 틀리는 일을 막는다).
    """
    in_dir = os.path.dirname(os.path.abspath(input_path))
    return os.path.join(in_dir, folder_name)


def open_results(out_dir, image_paths, max_images=4):
    """
    작업이 끝나면 결과 폴더를 열고, elevation 이미지를 기본 뷰어로 띄운다.
    (Windows: os.startfile / macOS: open / Linux: xdg-open)
    ParaView Python Shell 안에서도 그대로 동작한다.
    실패해도 작업 결과에는 영향이 없으므로 조용히 넘어간다.
    """
    targets = [out_dir] + list(image_paths)[:max(0, int(max_images))]

    def _launch(path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)                      # noqa: S606 (Windows 전용)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", path])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])
            return True
        except Exception as exc:
            log("  ! 열기 실패(%s): %s" % (os.path.basename(path), exc))
            return False

    opened = 0
    for t in targets:
        if os.path.exists(t) and _launch(t):
            opened += 1
    if opened:
        log("결과 폴더와 이미지 %d개를 화면에 띄웠습니다." % max(0, opened - 1))


# =============================================================================
# main
# =============================================================================
def parse_resolution(text):
    try:
        w, h = (int(x) for x in str(text).lower().replace(" ", "").split("x"))
    except Exception:
        raise ValueError("--resolution 형식은 WxH 여야 합니다. 예: 3840x2160")
    if w <= 0 or h <= 0:
        raise ValueError("--resolution 의 가로/세로는 양수여야 합니다.")
    if abs((float(w) / float(h)) - (16.0 / 9.0)) > 0.01:
        log("경고: %dx%d 는 16:9 가 아닙니다 (16:9 예: 1920x1080, 3840x2160)." % (w, h))
    return [w, h]


def parse_presets(text):
    out = []
    for name in str(text).split(","):
        name = name.strip()
        if name and name not in out:
            out.append(name)
    if not out:
        raise ValueError("--presets 에 최소 1개의 프리셋 이름이 필요합니다.")
    return out


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="ParaView(Elevation+Contour) 시각화 자동화. pvpython 으로 실행하세요.")
    p.add_argument("--input", "-i", required=True,
                   help="입력 3D 모델 파일 (.ply/.obj/.vtk/.vtp/.stl 등)")
    p.add_argument("--axis", default="z", choices=["x", "y", "z"],
                   help="Elevation 기준 축 (기본: z)")
    p.add_argument("--model-unit", default="mm", choices=["mm", "cm", "m"],
                   help="모델 좌표 1 단위의 실제 크기 (기본: mm). "
                        "CloudCompare/Metashape 에서 mm 로 스케일했다면 그대로 mm. "
                        "모델이 미터 단위라면 --model-unit m 으로 바꾸세요. "
                        "이 값이 틀리면 높이가 1000배 어긋납니다.")
    p.add_argument("--low", type=float, default=None,
                   help="low point(모델 좌표). 미지정 시 경계상자에서 자동 검출.")
    p.add_argument("--high", type=float, default=None,
                   help="high point(모델 좌표). 미지정 시 자동 검출.")
    p.add_argument("--interval", type=float, default=1.0,
                   help="등고선 간격(mm). 예: 1.0 또는 0.1 (기본: 1.0)")
    p.add_argument("--max-contours", type=int, default=2000,
                   help="등고선 최대 개수 안전 한계 (기본: 2000)")
    p.add_argument("--line-width", type=float, default=1.0,
                   help="등고선 굵기 (기본: 1.0). 4K 에서는 2~3 권장.")
    p.add_argument("--presets", default=DEFAULT_PRESETS,
                   help="콤마로 구분한 컬러 프리셋 목록 (기본: '%s')" % DEFAULT_PRESETS)
    p.add_argument("--preset", default=None,
                   help="(구버전 호환) 프리셋 1개만. 지정하면 --presets 를 덮어씀.")
    p.add_argument("--list-presets", action="store_true",
                   help="사용 가능한 프리셋 이름을 출력하고 종료")
    p.add_argument("--resolution", default="3840x2160",
                   help="저장 이미지 해상도 WxH, 16:9 권장 (기본: 3840x2160)")
    p.add_argument("--unit", default="mm", choices=["mm", "cm", "m", "auto"],
                   help="컬러바에 표시할 높이 단위 (기본: mm). "
                        "auto = D<10mm면 mm, <1000mm면 cm, 그 이상은 m")
    p.add_argument("--n-labels", type=int, default=DEFAULT_N_LABELS,
                   help="컬러바 눈금 숫자 목표 개수 (기본: %d)" % DEFAULT_N_LABELS)
    p.add_argument("--font-scale", type=float, default=1.0,
                   help="컬러바 글자/막대 크기 배율 (기본: 1.0)")
    p.add_argument("--label-mode", default="annotation",
                   choices=["annotation", "auto", "format", "custom"],
                   help="눈금 숫자 방식 (기본: annotation — 글자를 직접 지정하므로 "
                        "포맷 문자열이 그대로 찍히는 문제가 없음)")
    p.add_argument("--label-format", default=None,
                   help="'format'/'custom' 모드에서 쓸 printf 포맷. 예: '%%-#6.1f'")
    p.add_argument("--colorbar-frac", type=float, default=DEFAULT_COLORBAR_FRAC,
                   help="컬러바가 차지할 오른쪽 폭 비율 (기본: %.2f)" % DEFAULT_COLORBAR_FRAC)
    p.add_argument("--margin", type=float, default=DEFAULT_MARGIN,
                   help="이미지 가장자리 여백 비율 (기본: %.2f)" % DEFAULT_MARGIN)
    p.add_argument("--perspective", action="store_true",
                   help="원근 투영 사용 (기본은 정사영)")
    p.add_argument("--no-contour-colorbar", action="store_true",
                   help="등고선 이미지에는 컬러바를 넣지 않음")
    p.add_argument("--no-contour", action="store_true",
                   help="등고선 단계를 건너뛰고 elevation 이미지만 저장")
    p.add_argument("--no-state", action="store_true",
                   help=".pvsm 상태 파일 저장을 건너뜀")
    p.add_argument("--no-open", action="store_true",
                   help="작업이 끝나도 결과 폴더/이미지를 자동으로 열지 않음")
    p.add_argument("--open-images", type=int, default=4,
                   help="끝나고 자동으로 띄울 elevation 이미지 개수 (기본: 4, 0이면 폴더만)")
    return p.parse_args(argv)


def main(argv):
    args = parse_args(argv)

    known = available_presets()
    if args.list_presets:
        log("사용 가능한 컬러 프리셋 (%d개):" % len(known))
        for name in known:
            print("   - %s" % name)
        return

    presets = [args.preset] if args.preset else parse_presets(args.presets)
    if known:
        missing = [p for p in presets if p not in known]
        if missing:
            log("경고: 설치본에 없는 프리셋 -> %s" % ", ".join(missing))
            log("      '--list-presets' 로 사용 가능한 이름을 확인하세요.")

    resolution = parse_resolution(args.resolution)
    basename = os.path.splitext(os.path.basename(args.input))[0]

    # 결과 폴더 = 입력 모델이 있는 폴더 안의 paraview_image (없으면 자동 생성)
    out_dir = output_dir_for(args.input)
    if os.path.isfile(out_dir):
        raise IOError(
            "결과 폴더를 만들 수 없습니다. 같은 이름의 파일이 이미 있습니다:\n  %s"
            % out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
        log("결과 폴더 생성: %s" % out_dir)
    else:
        log("결과 폴더: %s" % out_dir)

    view = GetActiveViewOrCreate("RenderView")
    setup_white_view(view, resolution)

    reader = load_model(args.input)                                    # Step 1-2
    elev, distance_mm, unit_name, factor = make_elevation(             # Step 3-7
        reader, axis=args.axis, low=args.low, high=args.high,
        model_unit=args.model_unit, unit=args.unit)
    Hide(reader, view)

    elev_disp, lut = show_elevation(elev, view)
    span_disp = distance_mm / factor

    scalar_bar = style_scalar_bar(
        lut, view, unit_name, span_disp, resolution,
        colorbar_frac=args.colorbar_frac, margin=args.margin,
        n_labels=args.n_labels, font_scale=args.font_scale,
        label_mode=args.label_mode, label_format=args.label_format)

    contour = None
    contour_disp = None
    if not args.no_contour:
        contour = make_contour(elev, distance_mm, interval_mm=args.interval,
                               max_contours=args.max_contours,
                               factor=factor, unit_name=unit_name)      # 9-11
        contour_disp = color_contour(contour, view,
                                     line_width=args.line_width)        # Step 10

    frame_model(view, reader.GetDataInformation().GetBounds(), args.axis,
                resolution, colorbar_frac=args.colorbar_frac, margin=args.margin,
                parallel=not args.perspective)

    contour_colorbar = not args.no_contour_colorbar
    made = []
    contour_saved_once = False

    for preset in presets:                                              # Step 12
        log("--- 프리셋: %s ---" % preset)
        if not apply_preset(lut, preset, known):
            continue
        Render(view)

        slug = _slug(preset)
        elev_png = os.path.join(out_dir, "%s_%s_elevation.png" % (basename, slug))

        if contour_disp is None:
            cont_png = None
        elif contour_colorbar:
            cont_png = os.path.join(out_dir, "%s_%s_contour.png" % (basename, slug))
        elif not contour_saved_once:
            cont_png = os.path.join(out_dir, "%s_contour.png" % basename)
        else:
            cont_png = None

        e, c = save_pair(elev_disp, contour_disp, view, resolution,
                         elev_png, cont_png, scalar_bar=scalar_bar,
                         contour_colorbar=contour_colorbar)
        if c:
            contour_saved_once = True
        made.append((preset, e, c))

    if not made:
        raise RuntimeError("이미지를 하나도 만들지 못했습니다. 프리셋 이름을 확인하세요 "
                           "(--list-presets).")

    if not args.no_state:
        state_path = os.path.join(out_dir, basename + "_state.pvsm")
        SaveState(state_path)
        log("Step 12: 상태 파일 저장 -> %s" % state_path)

    log("완료. 결과 폴더: %s" % os.path.abspath(out_dir))
    print()
    for preset, e, c in made:
        print("  [%s]" % preset)
        print("    - elevation: %s" % e)
        if c:
            print("    - contour  : %s" % c)

    if not args.no_open:
        open_results(out_dir, [e for _, e, _ in made],
                     max_images=args.open_images)


if __name__ == "__main__":
    main(sys.argv[1:])
