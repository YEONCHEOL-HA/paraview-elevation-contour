# -*- coding: utf-8 -*-
"""
run_in_paraview.py  --  ParaView GUI 전용 실행 런처
=============================================================================
ParaView 프로그램(GUI) 안에서 "클릭"만으로 자동화를 돌리기 위한 파일입니다.

[사용법]
  1) ParaView 실행
  2) 상단 메뉴 View > Python Shell  (구버전은 Tools > Python Shell)
  3) Python Shell 창의 'Run Script' 버튼 클릭 -> 이 파일(run_in_paraview.py) 선택
  4) 끝. 결과 폴더에 _elevation.png / _contour.png / _state.pvsm 가 생깁니다.

* 실행 전에 아래 '설정' 부분의 경로 3~4줄만 본인 것으로 고치면 됩니다.
* Windows 경로는 역슬래시(\\) 때문에 문자열 앞에 r 을 붙여 r"C:\...\model.ply"
  형태로 쓰세요. (또는 슬래시 / 를 사용)
=============================================================================
"""

import os
import sys
import runpy

# ============================ 설정 (여기만 고치세요) ==========================

# (1) 같은 폴더에 있는 메인 스크립트(paraview_elevation_contour.py)의 전체 경로
MAIN_SCRIPT = r"C:\Users\내이름\Desktop\paraview_elevation_contour.py"

# (2) 처리할 3D 모델 파일 (.ply / .obj / .vtk / .stl 등)
INPUT_MODEL = r"C:\Users\내이름\Desktop\model.ply"

# (3) 결과를 저장할 폴더
OUTPUT_DIR  = r"C:\Users\내이름\Desktop\paraview_results"

# (4) 선택 옵션 -----------------------------------------------------------
AXIS        = "z"                 # 높이 기준 축: "x" / "y" / "z"
INTERVAL_MM = 1.0                 # 등고선 간격(mm). 예: 1.0 또는 0.1
PRESET      = "Rainbow Uniform"   # 컬러 프리셋 이름
RESOLUTION  = "1920x1440"         # 저장 이미지 해상도 WxH
LOW_M       = None                # low point(미터). None 이면 자동 검출
HIGH_M      = None                # high point(미터). None 이면 자동 검출
MAX_CONTOURS = 2000               # 등고선 최대 개수 안전 한계
MAKE_CONTOUR = True               # 등고선 이미지도 만들지 여부
SAVE_STATE   = True               # .pvsm 상태 파일 저장 여부

# ============================================================================
# (아래는 건드릴 필요 없음)
# ============================================================================

def _build_argv():
    argv = ["paraview_elevation_contour.py",
            "--input", INPUT_MODEL,
            "--out", OUTPUT_DIR,
            "--axis", AXIS,
            "--interval", str(INTERVAL_MM),
            "--max-contours", str(MAX_CONTOURS),
            "--preset", PRESET,
            "--resolution", RESOLUTION]
    if LOW_M is not None:
        argv += ["--low", str(LOW_M)]
    if HIGH_M is not None:
        argv += ["--high", str(HIGH_M)]
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

    # 메인 스크립트가 argparse 로 sys.argv 를 읽으므로, 여기서 인자를 주입한다.
    sys.argv = _build_argv()
    print("[run_in_paraview] 실행 인자:", " ".join(sys.argv[1:]))

    # run_name='__main__' 로 실행하면 메인 스크립트의 if __name__=='__main__' 블록이
    # 그대로 동작한다. (한글 주석 때문에 UTF-8 로 읽히도록 runpy 사용)
    runpy.run_path(MAIN_SCRIPT, run_name="__main__")


main()
