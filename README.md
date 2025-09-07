PyRD - simplified Python GUI based on Ready frame.cpp/frame.hpp

This small project provides a simplified PyQt5 GUI that mirrors the structure of
`frame.cpp`/`frame.hpp` from the Ready project. It intentionally omits VTK,
OpenCL and the RD engine; instead it focuses on menus, toolbars, dock panes,
and a placeholder render canvas with paint tools.

How to run

1. Create a virtualenv and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python src/main.py
```

Files
- `src/ready_gui.py`: main PyQt GUI implementation
- `src/main.py`: small launcher

Notes
- This is a simplified, local reimplementation for rapid prototyping.
- If you want VTK support, install PyVista/VTK and integrate the render canvas.

License: MIT (for these Python wrappers)
