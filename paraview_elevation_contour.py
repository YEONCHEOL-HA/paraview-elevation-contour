#!/usr/bin/env pvpython
# -*- coding: utf-8 -*-
"""
paraview_elevation_contour.py
=============================================================================
"Guide to 3D modelling" 매뉴얼의 마지막 섹션
    "Quick Guide to Visualising the Model as Elevation (height maps)
     and Contour images using Paraview"  (Step 1 ~ Step 12)
를 GUI 조작 없이 자동으로 수행하는 스크립트.

ParaView 의 파이썬 인터페이스 `paraview.simple` 을 사용한다.
따라서 실행은 일반 `python` 이 아니라 ParaView 에 포함된
`pvpython`(또는 `pvbatch`) 인터프리터로 해야 한다.

    pvpython paraview_elevation_contour.py --input model.ply --out ./results

-----------------------------------------------------------------------------
매뉴얼 스텝 ↔ 코드 대응표
-----------------------------------------------------------------------------
  Step 1  모델 열기                     -> OpenDataFile()      (load_model)
  Step 2  Pipeline 에서 모델 선택        -> SetActiveSource()   (load_model)
  Step 3  Filters > Elevation           -> Elevation()         (make_elevation)
  Step 4  Z 축 선택 후 Apply             -> LowPoint/HighPoint  (make_elevation)
  Step 5  'show line' 해제               -> 3D 위젯일 뿐, 렌더 결과에 무관 (주석)
  Step 6  low/high point 를 mm 로 반올림  -> _truncate_to_mm()   (make_elevation)
  Step 7  Scalar Range 0~1 -> 0~거리(mm)  -> ScalarRange         (make_elevation)
  Step 8  Coloring preset 적용           -> ApplyPreset()       (color_elevation)
  Step 9  Filters > Contour             -> Contour()           (make_contour)
  Step 10 Contour 색을 검정으로          -> Solid color [0,0,0] (color_contour)
  Step 11 Value Range 에 steps 추가      -> Isosurfaces=linspace (make_contour)
  Step 12 elevation / contour 이미지 저장 -> SaveScreenshot()    (save_images)
          + Save state                  -> SaveState()         (main)
=============================================================================
근거(References):
  - paraview.simple.Elevation  (LowPoint/HighPoint/ScalarRange) :
      https://www.paraview.org/paraview-docs/v5.13.0/python/paraview.simple.Elevation.html
  - paraview.simple.Contour    (ContourBy/Isosurfaces) :
      https://www.paraview.org/paraview-docs/v5.13.3/python/paraview.simple.Contour.html
  - Color maps (ColorBy / GetColorTransferFunction / ApplyPreset /
    RescaleTransferFunction) :
      https://docs.paraview.org/en/v5.13.0/ReferenceManual/colorMapping.html
  - Saving results (SaveScreenshot / SaveState) :
      https://docs.paraview.org/en/v5.10.0/UsersGuide/savingResults.html
=============================================================================
"""

from __future__ import print_function

import argparse
import math
import os
import sys

# -----------------------------------------------------------------------------
# paraview.simple 은 pvpython/pvbatch 환경에서만 import 된다.
# 일반 python 으로 실행하면 여기서 친절한 안내와 함께 종료한다.
# -----------------------------------------------------------------------------
try:
    from paraview.simple import (
        OpenDataFile, SetActiveSource, Elevation, Contour, Show, Hide,
        ColorBy, GetColorTransferFunction, GetActiveViewOrCreate,
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


# =============================================================================
# 유틸리티
# =============================================================================
def _truncate_to_mm(value_m):
    """
    Step 6: "delete submillimeter numbers".
    미터 단위 값에서 mm(소수점 3자리) 미만을 버린다.

    수학적으로:  floor(value_m * 1000) / 1000
    예) 0.012838485 m -> floor(12.838...) / 1000 = 12/1000 = 0.012 m (= 12 mm)

    floor 를 쓰는 이유: 매뉴얼 예시(0.012838485 -> 0.012)가 반내림(버림)이기 때문.

    주의: 부동소수점 오차 보정.
      0.058 * 1000 = 57.99999999999999 이므로 그냥 floor 하면 57(=0.057)이 되어버린다.
      -> 먼저 round(...,6) 으로 오차를 없앤 뒤 floor 한다.
    """
    return math.floor(round(value_m * 1000.0, 6)) / 1000.0


def _axis_index(axis):
    """'x'/'y'/'z' 문자를 0/1/2 인덱스로 변환."""
    return {"x": 0, "y": 1, "z": 2}[axis.lower()]


def log(msg):
    print("[paraview-auto] " + msg, flush=True)


# =============================================================================
# Step 1 ~ 2 : 모델 열기 + 활성화
# =============================================================================
def load_model(path):
    """
    Step 1: 모델 열기 (Filters/Reader 자동 선택).
            매뉴얼에는 'Open the model in CloudCompare' 라고 적혀 있으나
            이 섹션 제목이 'using Paraview' 이므로 ParaView 로 여는 것이 맞다.
    Step 2: Pipeline Browser 에서 모델을 선택(활성 소스로 지정).

    .ply, .obj, .vtk, .vtp, .stl 등 확장자에 맞는 리더가 자동 선택된다.
    """
    if not os.path.isfile(path):
        raise IOError("입력 파일을 찾을 수 없습니다: %s" % path)

    log("Step 1-2: 모델 로드 -> %s" % path)
    reader = OpenDataFile(path)
    if reader is None:
        raise RuntimeError(
            "ParaView 가 이 파일 형식을 열 수 있는 리더를 찾지 못했습니다: %s" % path
        )
    SetActiveSource(reader)

    # 중요: 파일을 연 직후에는 데이터가 아직 읽히지 않아 GetBounds() 가
    #       VTK 의 '빈 경계상자' 기본값 [1,-1, 1,-1, 1,-1] 을 돌려준다.
    #       파이프라인을 갱신해야 실제 좌표 범위를 얻을 수 있다.
    reader.UpdatePipeline()
    return reader


# =============================================================================
# Step 3 ~ 7 : Elevation 필터
# =============================================================================
def make_elevation(reader, axis="z", low_m=None, high_m=None):
    """
    Step 3: Filters > Alphabetical > Elevation.
    Step 4: 'Z axis' 선택 -> LowPoint/HighPoint 를 해당 축 방향으로 설정.
    Step 6: low/high point 값을 mm 단위(소수 3자리)로 반올림(버림).
    Step 7: Scalar Range 를 0~1 에서 0~(거리 mm) 로 변경.
            -> 컬러바가 '0 mm ~ D mm' 로 읽히도록 만든다.

    반환: (elevation 필터, 스칼라 최대값 = 거리(mm))

    -------------------------------------------------------------------------
    Elevation 필터의 수학 (vtkElevationFilter):
      각 점 P 에 대해, LowPoint L 과 HighPoint H 를 잇는 벡터에 투영한 정규값
          s = clamp( ( (P - L) · (H - L) ) / |H - L|^2 ,  0, 1 )   (s ∈ [0,1])
      출력 스칼라 = ScalarRange[0] + s * (ScalarRange[1] - ScalarRange[0])
      여기서 ScalarRange = [0, D] 이므로  출력 = s * D  (단위: mm).
    -------------------------------------------------------------------------
    """
    ai = _axis_index(axis)

    # 모델의 경계상자(bounding box)로 축 방향 최소/최대 좌표를 얻는다.
    # GetBounds() -> [xmin,xmax, ymin,ymax, zmin,zmax]  (단위: 모델 좌표 = 미터 가정)
    reader.UpdatePipeline()  # 안전을 위해 한 번 더 갱신
    bounds = reader.GetDataInformation().GetBounds()
    axis_min = bounds[2 * ai]
    axis_max = bounds[2 * ai + 1]

    # 경계상자가 비어있으면(VTK 기본값 min>max) 데이터가 안 읽힌 것.
    if axis_min > axis_max:
        raise RuntimeError(
            "모델의 경계상자를 읽지 못했습니다(빈 데이터). 파일이 비었거나 "
            "ParaView 가 이 파일을 제대로 읽지 못했을 수 있습니다: bounds=%s" % (bounds,)
        )

    # Step 6: 사용자가 값을 주지 않으면 경계상자에서 자동으로 잡고 mm 로 버림.
    if low_m is None:
        low_m = _truncate_to_mm(axis_min)
    if high_m is None:
        high_m = _truncate_to_mm(axis_max)

    if high_m <= low_m:
        raise ValueError(
            "high point(%.4f m) 가 low point(%.4f m) 보다 커야 합니다. "
            "--low / --high 로 직접 지정해 보세요." % (high_m, low_m)
        )

    # Step 7 준비: 거리 D(mm) = (high - low) * 1000
    distance_mm = round((high_m - low_m) * 1000.0)
    log("Step 4/6: %s축 low=%.3f m, high=%.3f m -> 거리 D=%.0f mm"
        % (axis.upper(), low_m, high_m, distance_mm))

    # Step 3: Elevation 필터 생성
    elev = Elevation(Input=reader)

    # Step 4: 축 방향으로 LowPoint / HighPoint 지정 (나머지 두 축은 0)
    low_pt = [0.0, 0.0, 0.0]
    high_pt = [0.0, 0.0, 0.0]
    low_pt[ai] = low_m
    high_pt[ai] = high_m
    elev.LowPoint = low_pt
    elev.HighPoint = high_pt

    # Step 7: Scalar Range 를 [0, D(mm)] 로.  -> 스칼라가 곧 '높이(mm)'
    elev.ScalarRange = [0.0, float(distance_mm)]

    elev.UpdatePipeline()
    log("Step 3/7: Elevation 필터 적용, ScalarRange = [0, %.0f] mm" % distance_mm)

    # Step 5: 'show line' 은 LowPoint~HighPoint 를 잇는 3D 상호작용 위젯 표시 여부일 뿐,
    #         파일로 저장되는 렌더 결과에는 영향이 없으므로 배치 모드에서는 무시한다.

    return elev, distance_mm


def color_elevation(elev, view, preset="Rainbow Uniform"):
    """
    Step 8: Coloring > Edit > Choose preset -> Apply.
            elevation 표면을 'Elevation' 스칼라로 색칠하고 컬러 프리셋을 적용한다.
    """
    disp = Show(elev, view)
    disp.Representation = "Surface"

    # ColorBy(display, ('POINTS', 'Elevation'))
    ColorBy(disp, ("POINTS", "Elevation"))

    lut = GetColorTransferFunction("Elevation")
    try:
        lut.ApplyPreset(preset, True)  # True = 프리셋의 전체 색을 그대로 적용
        log("Step 8: 컬러 프리셋 '%s' 적용" % preset)
    except Exception as exc:  # 프리셋 이름이 설치본에 없을 수 있음
        log("Step 8: 프리셋 '%s' 적용 실패(%s). 기본 색상 유지." % (preset, exc))

    # 컬러바(스칼라바)를 화면에 표시
    try:
        disp.SetScalarBarVisibility(view, True)
    except Exception:
        pass

    return disp


# =============================================================================
# Step 9 ~ 11 : Contour 필터
# =============================================================================
def make_contour(elev, distance_mm, interval_mm=1.0, max_contours=2000):
    """
    Step 9:  Filters > Alphabetical > Contour  (기본 1개 등고선).
    Step 11: Value Range 에 'steps' 를 추가해 일정 간격의 등고선을 생성.

    -------------------------------------------------------------------------
    등고선 개수의 수학 (매뉴얼 Step 11 그대로):
      높이 범위 D(mm), 등고선 간격 δ(mm) 일 때
          steps(등고선 개수) N = D/δ + 1
          등고선 값           v_i = i * δ   (i = 0, 1, ..., D/δ)
      예) D=46 mm, δ=1   mm -> N = 46/1   + 1 = 47   (값 0,1,2,...,46)
          D=46 mm, δ=0.1 mm -> N = 46/0.1 + 1 = 461  (값 0,0.1,...,46)
      즉 v = linspace(0, D, N) 과 동일하다.
    -------------------------------------------------------------------------
    """
    if interval_mm <= 0:
        raise ValueError("등고선 간격(interval_mm)은 0보다 커야 합니다.")

    # N = D/δ + 1 (정수), 값 = 0, δ, 2δ, ..., D
    n_intervals = int(round(distance_mm / interval_mm))
    n_steps = n_intervals + 1

    # 안전장치: 등고선이 지나치게 많으면(넓은 지형 등) ParaView 가 메모리 부족으로
    #           튕길 수 있다. 크래시 대신 여기서 멈추고 해결법을 알려준다.
    if n_steps > max_contours:
        suggested = math.ceil(distance_mm / (max_contours - 1) * 10) / 10.0
        raise ValueError(
            "등고선이 %d 개나 생성됩니다 (높이범위 D=%.0f mm, 간격 %.3g mm).\n"
            "       이렇게 많으면 ParaView 가 메모리 부족으로 튕길 수 있어 중단했습니다.\n"
            "       => 등고선 간격(--interval, 또는 run_in_paraview.py 의 INTERVAL_MM)을\n"
            "          약 %.1f mm 이상으로 키우거나, --max-contours 값을 올리세요.\n"
            "       (참고: 이 모델의 높이범위는 %.3f m 입니다.)"
            % (n_steps, distance_mm, interval_mm, suggested, distance_mm / 1000.0)
        )

    values = [round(i * interval_mm, 6) for i in range(n_steps)]

    # Step 9: Contour 필터 생성, 'Elevation' 스칼라 기준으로 등고선 추출
    contour = Contour(Input=elev)
    contour.ContourBy = ["POINTS", "Elevation"]

    # Step 11: 등고선 값 목록 지정 (steps)
    contour.Isosurfaces = values
    contour.UpdatePipeline()

    log("Step 9/11: Contour 필터 적용 - 간격 %.3g mm, 등고선 %d개 (0 ~ %.0f mm)"
        % (interval_mm, n_steps, distance_mm))
    return contour


def color_contour(contour, view):
    """
    Step 10: Contour 색을 검정색으로.
             등고선은 값에 상관없이 단색(검정) 선으로 그린다.
    """
    disp = Show(contour, view)
    disp.Representation = "Surface"      # 선(폴리라인)도 Surface 로 그려짐
    ColorBy(disp, None)                  # 스칼라 색칠 해제 -> 단색 사용
    disp.AmbientColor = [0.0, 0.0, 0.0]
    disp.DiffuseColor = [0.0, 0.0, 0.0]
    try:
        disp.LineWidth = 1.0
    except Exception:
        pass
    log("Step 10: Contour 를 검정색 단색으로 설정")
    return disp


# =============================================================================
# 카메라 (높이지도이므로 위에서 내려다보는 top-down 뷰)
# =============================================================================
def set_topdown_view(reader, view, axis="z"):
    """height map/등고선은 보통 위(축 방향)에서 정사영으로 본다."""
    b = reader.GetDataInformation().GetBounds()
    cx = 0.5 * (b[0] + b[1])
    cy = 0.5 * (b[2] + b[3])
    cz = 0.5 * (b[4] + b[5])
    diag = math.sqrt((b[1]-b[0])**2 + (b[3]-b[2])**2 + (b[5]-b[4])**2) or 1.0

    view.CameraFocalPoint = [cx, cy, cz]
    ai = _axis_index(axis)
    pos = [cx, cy, cz]
    pos[ai] = ([b[0], b[2], b[4]][ai]) + diag  # 축 방향으로 위에서
    view.CameraPosition = pos
    # ViewUp: z축 뷰면 +y 가 위, 아니면 +z 가 위
    view.CameraViewUp = [0.0, 1.0, 0.0] if axis.lower() == "z" else [0.0, 0.0, 1.0]
    ResetCamera(view)
    Render(view)


# =============================================================================
# Step 12 : 이미지 저장
# =============================================================================
def save_images(elev_disp, contour_disp, view, out_dir, resolution, basename):
    """
    Step 12: elevation 만 보이게 하고 저장 -> contour 만 보이게 하고 저장.
    """
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    elev_png = os.path.join(out_dir, basename + "_elevation.png")
    cont_png = os.path.join(out_dir, basename + "_contour.png")

    # (a) elevation 만 표시
    elev_disp.Visibility = 1
    if contour_disp is not None:
        contour_disp.Visibility = 0
    Render(view)
    SaveScreenshot(elev_png, view, ImageResolution=resolution)
    log("Step 12: elevation 이미지 저장 -> %s" % elev_png)

    # (b) contour 만 표시
    if contour_disp is not None:
        elev_disp.Visibility = 0
        contour_disp.Visibility = 1
        Render(view)
        SaveScreenshot(cont_png, view, ImageResolution=resolution)
        log("Step 12: contour 이미지 저장 -> %s" % cont_png)
    else:
        cont_png = None

    # 다시 둘 다 켜 둔다(상태 저장 대비)
    elev_disp.Visibility = 1
    if contour_disp is not None:
        contour_disp.Visibility = 1
    Render(view)

    return elev_png, cont_png


# =============================================================================
# main
# =============================================================================
def parse_args(argv):
    p = argparse.ArgumentParser(
        description="매뉴얼의 ParaView(Elevation+Contour) 시각화 섹션 자동화 스크립트. "
                    "pvpython 으로 실행하세요.")
    p.add_argument("--input", "-i", required=True,
                   help="입력 3D 모델 파일 (.ply/.obj/.vtk/.vtp/.stl 등)")
    p.add_argument("--out", "-o", default="./paraview_output",
                   help="결과 저장 폴더 (기본: ./paraview_output)")
    p.add_argument("--axis", default="z", choices=["x", "y", "z"],
                   help="Elevation 기준 축 (기본: z)")
    p.add_argument("--low", type=float, default=None,
                   help="low point 값(미터). 미지정 시 경계상자에서 자동 검출 후 mm로 버림.")
    p.add_argument("--high", type=float, default=None,
                   help="high point 값(미터). 미지정 시 경계상자에서 자동 검출 후 mm로 버림. "
                        "(색 정보를 제한하려면 이 값을 직접 낮춰 지정)")
    p.add_argument("--interval", type=float, default=1.0,
                   help="등고선 간격(mm). 예: 1.0 또는 0.1 (기본: 1.0)")
    p.add_argument("--max-contours", type=int, default=2000,
                   help="등고선 최대 개수 안전 한계 (기본: 2000). 넘으면 크래시 대신 안내 후 중단.")
    p.add_argument("--preset", default="Rainbow Uniform",
                   help="컬러 프리셋 이름 (기본: 'Rainbow Uniform')")
    p.add_argument("--resolution", default="1920x1440",
                   help="저장 이미지 해상도 WxH (기본: 1920x1440)")
    p.add_argument("--no-contour", action="store_true",
                   help="등고선 단계를 건너뛰고 elevation 이미지만 저장")
    p.add_argument("--no-state", action="store_true",
                   help=".pvsm 상태 파일 저장을 건너뜀")
    return p.parse_args(argv)


def main(argv):
    args = parse_args(argv)

    # 해상도 파싱
    try:
        w, h = (int(x) for x in args.resolution.lower().split("x"))
        resolution = [w, h]
    except Exception:
        raise ValueError("--resolution 형식은 WxH 여야 합니다. 예: 1920x1440")

    basename = os.path.splitext(os.path.basename(args.input))[0]
    view = GetActiveViewOrCreate("RenderView")
    view.Background = [1.0, 1.0, 1.0]  # 흰 배경
    try:
        view.OrientationAxesVisibility = 0
    except Exception:
        pass

    # ---- 파이프라인 실행 ----
    reader = load_model(args.input)                                   # Step 1-2
    elev, distance_mm = make_elevation(                               # Step 3-7
        reader, axis=args.axis, low_m=args.low, high_m=args.high)

    # 원본 리더는 화면에서 숨긴다(elevation 결과만 보이도록)
    Hide(reader, view)

    elev_disp = color_elevation(elev, view, preset=args.preset)       # Step 8

    contour = None
    contour_disp = None
    if not args.no_contour:
        contour = make_contour(elev, distance_mm, interval_mm=args.interval,
                               max_contours=args.max_contours)        # 9-11
        contour_disp = color_contour(contour, view)                   # Step 10

    set_topdown_view(reader, view, axis=args.axis)

    elev_png, cont_png = save_images(                                 # Step 12
        elev_disp, contour_disp, view, args.out, resolution, basename)

    # Step 12(마지막): Save state (.pvsm)
    if not args.no_state:
        state_path = os.path.join(args.out, basename + "_state.pvsm")
        SaveState(state_path)
        log("Step 12: 상태 파일 저장 -> %s" % state_path)

    log("완료. 결과 폴더: %s" % os.path.abspath(args.out))
    print()
    print("  - 높이지도(elevation): %s" % elev_png)
    if cont_png:
        print("  - 등고선(contour)   : %s" % cont_png)


if __name__ == "__main__":
    main(sys.argv[1:])
