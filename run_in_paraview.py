# -*- coding: utf-8 -*-
"""
run_in_paraview.py  --  ParaView GUI 전용 실행 런처  (v3)
=============================================================================
[사용법]
  1) ParaView 실행
  2) 상단 메뉴 View > Python Shell  (구버전은 Tools > Python Shell)
  3) Python Shell 창의 'Run Script' 버튼 클릭 -> 이 파일(run_in_paraview.py) 선택

결과는 모델이 들어있는 폴더 안 "paraview_image" 폴더에 저장되고(자동 생성),
작업이 끝나면 그 폴더와 이미지가 자동으로 열립니다.
출력 경로는 지정할 필요가 없습니다 — 고칠 경로는 MAIN_SCRIPT, INPUT_MODEL 2줄뿐입니다.

★ 가장 중요한 설정 두 가지
   - MODEL_UNIT : 모델 좌표 1 단위가 실제로 mm 인지 m 인지.
                  (이게 틀리면 컬러바가 32 mm 를 32 m 로 표시합니다)
   - UNIT       : 컬러바에 쓸 단위(mm/cm/m).
=============================================================================
"""

import os
import sys
import runpy

# ============================ 설정 (여기만 고치세요) ==========================

# (1) 메인 스크립트(paraview_elevation_contour.py)의 전체 경로
MAIN_SCRIPT = r"C:\Users\user\Downloads\paraview_elevation_contour.py"

# (2) 처리할 3D 모델 파일 (.ply / .obj / .vtk / .stl 등)
INPUT_MODEL = r"D:\3D\진주 악어발자국\crocodile.obj"

# (3) 결과 저장 위치 — 고칠 것이 없습니다.
#     모델이 들어있는 폴더 안에 paraview_image 폴더가 자동으로 만들어지고
#     모든 이미지가 그 안에 저장됩니다.
#       D:\3D\경산(제3층) 공룡발자국\Gyungsan_....obj
#         -> D:\3D\경산(제3층) 공룡발자국\paraview_image\
OPEN_RESULT = True   # 끝나면 결과 폴더를 열고 이미지를 기본 뷰어로 보여줍니다.
OPEN_IMAGES = 4      # 자동으로 띄울 elevation 이미지 개수 (0 이면 폴더만 열기)

# (4) ★ 단위 ★ ---------------------------------------------------------------
MODEL_UNIT = "mm"   # 모델 좌표 1 단위의 실제 크기: "mm" / "cm" / "m"
                    #   CloudCompare 에서 mm 로 스케일했다면 그대로 "mm".
                    #   (확인: ParaView Information 탭의 Bounds 숫자가
                    #    실제로 몇 mm 인지 보면 됩니다)
UNIT       = "mm"   # 컬러바에 표시할 단위: "mm" / "cm" / "m" / "auto"
                    #   "auto" 로 두면 크기에 따라 mm/cm/m 를 자동으로 고릅니다.

# (5) 컬러 프리셋 -----------------------------------------------------------
#     콤마로 여러 개 -> 프리셋마다 <모델명>_<프리셋>_elevation.png 생성
PRESETS = "Rainbow Uniform,Turbo,Viridis (matplotlib),Cool to Warm"
#   다른 후보: "Jet", "Inferno (matplotlib)", "Plasma (matplotlib)",
#              "Black-Body Radiation", "Cool to Warm (Extended)",
#              "Blue Orange (divergent)", "Rainbow Desaturated"
LIST_PRESETS = False   # True 로 두면 설치본의 프리셋 이름만 출력하고 끝납니다.

# (6) 컬러바(색 막대) 모양 ----------------------------------------------------
LABEL_MODE    = "annotation"
#   "annotation" (기본/권장) : 눈금 값과 '글자'를 직접 지정.
#                              포맷 문자열("%-#6.2f")이 그대로 찍히는
#                              ParaView 버그의 영향을 받지 않습니다.
#   "auto"                   : ParaView 자동 눈금/자동 포맷.
#   "format"                 : 자동 눈금 + printf 포맷.
#   "custom"                 : 예전 방식(버그 있는 버전 있음. 비권장).
N_LABELS      = 5      # 눈금 숫자 개수 목표. 0 과 최댓값은 항상 포함.
                       #   예) 0 ~ 32 mm -> 0, 10, 20, 30, 32
FONT_SCALE    = 1.0    # 글자/막대 크기 배율. 더 키우려면 1.3, 1.5 ...
                       #   기본값이 4K 기준 제목 52px / 숫자 43px 입니다.
COLORBAR_FRAC = 0.20   # 컬러바가 차지할 오른쪽 폭 비율. 숫자가 잘리면 0.24~0.28.
LABEL_FORMAT  = None   # "format"/"custom" 모드에서만 사용. 예: r"%-#6.1f"

# (7) 그 외 옵션 --------------------------------------------------------------
AXIS        = "z"                 # 높이 기준 축: "x" / "y" / "z"
INTERVAL_MM = 1.0                 # 등고선 간격(mm). 32 mm 모델이면 33개 생성.
LINE_WIDTH  = 2.0                 # 등고선 굵기. 4K 는 2~3 이 잘 보입니다.
RESOLUTION  = "3840x2160"         # 저장 이미지 해상도 WxH (16:9)
LOW         = None                # low point(모델 좌표). None 이면 자동 검출
HIGH        = None                # high point(모델 좌표). None 이면 자동 검출
MAX_CONTOURS = 2000               # 등고선 최대 개수 안전 한계
MAKE_CONTOUR = True               # 등고선 이미지도 만들지 여부
SAVE_STATE   = True               # .pvsm 상태 파일 저장 여부
MARGIN       = 0.04               # 이미지 가장자리 여백 비율
PERSPECTIVE  = False              # True 면 원근 투영
CONTOUR_COLORBAR = True           # 등고선 이미지에도 컬러바를 넣을지

# ============================================================================
# (아래는 건드릴 필요 없음)
# ============================================================================

def _build_argv():
    if LIST_PRESETS:
        return ["paraview_elevation_contour.py",
                "--input", INPUT_MODEL, "--list-presets"]
    argv = ["paraview_elevation_contour.py",
            "--input", INPUT_MODEL,
            "--axis", AXIS,
            "--model-unit", MODEL_UNIT,
            "--unit", UNIT,
            "--interval", str(INTERVAL_MM),
            "--line-width", str(LINE_WIDTH),
            "--max-contours", str(MAX_CONTOURS),
            "--presets", PRESETS,
            "--resolution", RESOLUTION,
            "--label-mode", LABEL_MODE,
            "--n-labels", str(N_LABELS),
            "--font-scale", str(FONT_SCALE),
            "--colorbar-frac", str(COLORBAR_FRAC),
            "--margin", str(MARGIN)]
    if OPEN_RESULT:
        argv += ["--open-images", str(OPEN_IMAGES)]
    else:
        argv += ["--no-open"]
    if LABEL_FORMAT:
        argv += ["--label-format", LABEL_FORMAT]
    if LOW is not None:
        argv += ["--low", str(LOW)]
    if HIGH is not None:
        argv += ["--high", str(HIGH)]
    if PERSPECTIVE:
        argv += ["--perspective"]
    if not CONTOUR_COLORBAR:
        argv += ["--no-contour-colorbar"]
    if not MAKE_CONTOUR:
        argv += ["--no-contour"]
    if not SAVE_STATE:
        argv += ["--no-state"]
    return argv


def main():
    if not os.path.isfile(MAIN_SCRIPT):
        raise IOError(
            "MAIN_SCRIPT 경로가 잘못되었습니다. paraview_elevation_contour.py 의 "
            "정확한 위치로 고쳐주세요:\n  %s" % MAIN_SCRIPT)
    if not os.path.isfile(INPUT_MODEL):
        raise IOError("INPUT_MODEL(모델 파일)을 찾을 수 없습니다:\n  %s" % INPUT_MODEL)

    sys.argv = _build_argv()
    print("[run_in_paraview] 실행 인자:", " ".join(sys.argv[1:]))

    runpy.run_path(MAIN_SCRIPT, run_name="__main__")


main()
