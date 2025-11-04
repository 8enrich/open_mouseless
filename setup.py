from cx_Freeze import setup, Executable

setup(
    name="open_mouseless",
    version="0.3",
    options={
        'build_exe': {
            'includes': ['pyautogui', 'PyQt5'],
            'build_exe': 'bin',
            'include_files': ['settings.json', 'assets/'],
            'packages': ['Xlib', 'Xlib.ext', 'Xlib.ext.xfixes', 'pyautogui']
        },
    },
    executables = [Executable("main.py", target_name="open_mouseless")]
)
