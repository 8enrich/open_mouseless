from cx_Freeze import setup, Executable

setup(
    name="open_mouseless",
    version="0.1",
    options={
        'build_exe': {
            'includes': ['pyautogui', 'PyQt5'],
        }
    },
    executables = [Executable("main.py", target_name="open_mouseless")]
)
