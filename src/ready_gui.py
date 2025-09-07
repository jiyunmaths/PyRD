from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QToolBar, QLabel, QTextEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QDockWidget, QListWidget,
    QFileDialog, QColorDialog, QSpinBox, QStatusBar, QTreeWidget, QTreeWidgetItem,
    QStyle
)
from info_panel import InfoPanel
import os
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk


class RenderCanvas(QWidget):
    """Placeholder central canvas. In the original C++ app VTK is used.
    Here we provide a simple QWidget that can be painted to and that
    responds to mouse events for paint/pick actions.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(pal)
        self._last_pos = None
        self._paint_value = 0.5
        self._brush_size = 2
        self._mode = 'pointer'  # pointer, pencil, brush, picker

    def set_mode(self, mode):
        self._mode = mode

    def set_brush_size(self, size_index):
        sizes = [2, 4, 8, 16, 32]
        self._brush_size = sizes[size_index]

    def set_paint_value(self, v: float):
        self._paint_value = v

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._last_pos = ev.pos()
            if self._mode == 'pencil':
                self.update()  # placeholder for drawing
            elif self._mode == 'brush':
                self.update()
            elif self._mode == 'picker':
                # toggle a fake picked value based on position
                self._paint_value = (ev.x() % 255) / 255.0
                self.parent().on_color_picked(self._paint_value)

    def mouseMoveEvent(self, ev):
        if self._last_pos and (self._mode in ('pencil', 'brush')):
            self.update()

    def mouseReleaseEvent(self, ev):
        self._last_pos = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Reaction Diffusion Simulator')
        self.resize(1200, 700)

        # state
        self.is_running = False
        self.current_paint_value = 0.5
        self.current_brush_size_index = 1

        # central render canvas
        self.vtk_canvas = VTKCanvas(self)
        self.setCentralWidget(self.vtk_canvas)

        # status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel('Stopped. Timesteps: 0')
        self.status.addWidget(self.status_label)
        self.timesteps = 0

        # timer to simulate OnIdle driven run loop
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # 10 fps update
        self.timer.timeout.connect(self._on_idle)

        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_docks()

    def _create_actions(self):
        self.act_new = QAction('New Pattern...', self)
        self.act_open = QAction('Open Pattern...', self)
        self.act_save = QAction('Save Pattern...', self)
        self.act_about = QAction('About', self)

        self.act_run = QAction('Run', self)
        self.act_run.setCheckable(True)
        self.act_run.triggered.connect(self.toggle_run)

        self.act_step = QAction('Step', self)
        self.act_step.triggered.connect(self.step_once)

        # paint tools
        self.act_pointer = QAction('Pointer', self)
        self.act_pointer.setCheckable(True)
        self.act_pointer.triggered.connect(lambda: self._set_tool('pointer'))
        self.act_pencil = QAction('Pencil', self)
        self.act_pencil.setCheckable(True)
        self.act_pencil.triggered.connect(lambda: self._set_tool('pencil'))
        self.act_brush = QAction('Brush', self)
        self.act_brush.setCheckable(True)
        self.act_brush.triggered.connect(lambda: self._set_tool('brush'))
        self.act_picker = QAction('Picker', self)
        self.act_picker.setCheckable(True)
        self.act_picker.triggered.connect(lambda: self._set_tool('picker'))

        self.paint_actions = [self.act_pointer, self.act_pencil, self.act_brush, self.act_picker]

        # brush sizes
        self.brush_size_actions = [QAction(s, self) for s in ['XS', 'S', 'M', 'L', 'XL']]
        for i, a in enumerate(self.brush_size_actions):
            a.setCheckable(True)
            a.triggered.connect(lambda checked, idx=i: self._set_brush_size(idx))

        # color
        self.act_color = QAction('Color...', self)
        self.act_color.triggered.connect(self._choose_color)

    def _create_menus(self):
        mb = self.menuBar()
        filem = mb.addMenu('&File')
        filem.addAction(self.act_new)
        filem.addAction(self.act_open)
        filem.addAction(self.act_save)
        filem.addSeparator()
        filem.addAction(self.act_about)

        viewm = mb.addMenu('&View')
        self.act_fullscreen = QAction('Full Screen', self)
        self.act_fullscreen.setCheckable(True)
        self.act_fullscreen.triggered.connect(self._toggle_fullscreen)
        viewm.addAction(self.act_fullscreen)

    def _create_toolbars(self):
        # file toolbar
        tb_file = QToolBar('File')
        tb_file.addAction(self.act_new)
        tb_file.addAction(self.act_open)
        tb_file.addAction(self.act_save)
        self.addToolBar(tb_file)

        # action toolbar
        tb_action = QToolBar('Action')
        tb_action.addAction(self.act_step)
        tb_action.addAction(self.act_run)
        tb_action.addAction(QAction('Slower', self))
        tb_action.addAction(QAction('Faster', self))
        self.timesteps_label = QLabel('Timesteps per render: 16')
        tb_action.addWidget(self.timesteps_label)
        self.addToolBar(tb_action)

        # paint toolbar
        tb_paint = QToolBar('Paint')
        for a in self.paint_actions:
            tb_paint.addAction(a)
        tb_paint.addSeparator()
        for a in self.brush_size_actions:
            tb_paint.addAction(a)
        tb_paint.addSeparator()
        tb_paint.addAction(self.act_color)
        self.color_swatch = QLabel()
        self._update_color_swatch()
        tb_paint.addWidget(self.color_swatch)
        self.addToolBar(tb_paint)

        # select default tool
        self.act_pointer.setChecked(True)

    def _create_docks(self):
        # Patterns pane (populate from filesystem `patterns` folder)
        self.patterns = QTreeWidget()
        self.patterns.setHeaderHidden(True)
        self.patterns.itemDoubleClicked.connect(self.on_pattern_activated)
        dock_patterns = QDockWidget('Patterns Pane', self)
        dock_patterns.setWidget(self.patterns)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_patterns)

        # build tree from patterns directory relative to repo
        self.build_patterns_tree()

        # Info pane (use InfoPanel for richer file previews)
        self.info = InfoPanel()
        self.info.set_info('Info pane (system status)')
        dock_info = QDockWidget('Info Pane', self)
        dock_info.setWidget(self.info)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_info)

        # Help pane
        self.help = QTextEdit()
        self.help.setReadOnly(True)
        self.help.setPlainText('Help pane')
        dock_help = QDockWidget('Help Pane', self)
        dock_help.setWidget(self.help)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_help)

    def build_patterns_tree(self):
        """Scan the repository `patterns/` directory and populate the tree."""
        # patterns directory is ../patterns relative to this file
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'patterns'))
        self.patterns.clear()
        if not os.path.isdir(root_dir):
            return

        # prepare folder icon (use project's icons/open-folder.png if present)
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'icons', 'open-folder.png'))
        if os.path.exists(icon_path):
            folder_icon = QIcon(icon_path)
        else:
            # fallback to standard directory icon
            folder_icon = self.style().standardIcon(QStyle.SP_DirIcon)

        # set icon size for tree items
        self.patterns.setIconSize(QSize(24, 24))

        def add_dir(parent_item, full_path):
            try:
                entries = sorted(os.listdir(full_path), key=lambda s: s.lower())
            except Exception:
                return
            for name in entries:
                path = os.path.join(full_path, name)
                if os.path.isdir(path):
                    node = QTreeWidgetItem(parent_item, [name])
                    node.setData(0, Qt.UserRole, None)
                    node.setIcon(0, folder_icon)
                    add_dir(node, path)
                else:
                    leaf = QTreeWidgetItem(parent_item, [name])
                    # store absolute path for activation
                    leaf.setData(0, Qt.UserRole, path)

        # top-level: show each top-level folder as a root node
        top_entries = sorted(os.listdir(root_dir), key=lambda s: s.lower())
        for entry in top_entries:
            full = os.path.join(root_dir, entry)
            if os.path.isdir(full):
                root_item = QTreeWidgetItem(self.patterns, [entry])
                root_item.setData(0, Qt.UserRole, None)
                root_item.setIcon(0, folder_icon)
                add_dir(root_item, full)
            else:
                leaf = QTreeWidgetItem(self.patterns, [entry])
                leaf.setData(0, Qt.UserRole, os.path.join(root_dir, entry))

        self.patterns.expandToDepth(0)

    def on_pattern_activated(self, item, column):
        """Called when user double-clicks a tree item; if it's a file open/show it."""
        path = item.data(0, Qt.UserRole)
        if path:
            # show selected pattern in status and delegate display to InfoPanel
            self.status_label.setText(f'Selected: {os.path.basename(path)}')
            try:
                self.info.show_file(path)
            except Exception:
                # fallback message
                try:
                    size = os.path.getsize(path)
                except Exception:
                    size = 'unknown'
                self.info.set_info(f'Cannot display file contents (error).\nPath: {path}\nSize: {size}')
        else:
            # toggle expand/collapse for directories
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)

    def _toggle_fullscreen(self):
        if self.act_fullscreen.isChecked():
            self.showFullScreen()
        else:
            self.showNormal()

    def toggle_run(self, checked):
        self.is_running = checked
        if self.is_running:
            self.timer.start()
            self.status_label.setText('Running. Timesteps: %d' % self.timesteps)
            self.act_run.setText('Stop')
        else:
            self.timer.stop()
            self.status_label.setText('Stopped. Timesteps: %d' % self.timesteps)
            self.act_run.setText('Run')

    def step_once(self):
        # perform a single timestep
        self.timesteps += 1
        self.status_label.setText(('Running.' if self.is_running else 'Stopped.') + f' Timesteps: {self.timesteps}')
        # simulate updating render
        if hasattr(self, 'vtk_canvas'):
            try:
                self.vtk_canvas.vtkWidget.GetRenderWindow().Render()
            except Exception:
                pass

    def _on_idle(self):
        # called periodically when running
        # simulate variable number of steps per timer tick
        self.timesteps += 1
        self.status_label.setText('Running. Timesteps: %d' % self.timesteps)
        # update VTK render
        if hasattr(self, 'vtk_canvas'):
            try:
                self.vtk_canvas.vtkWidget.GetRenderWindow().Render()
            except Exception:
                pass

    def _set_tool(self, name):
        for a in self.paint_actions:
            a.setChecked(False)
        mapping = {'pointer': self.act_pointer, 'pencil': self.act_pencil, 'brush': self.act_brush, 'picker': self.act_picker}
        mapping[name].setChecked(True)
        if hasattr(self, 'vtk_canvas'):
            try:
                self.vtk_canvas.set_mode(name)
            except Exception:
                pass

    def _set_brush_size(self, idx):
        for a in self.brush_size_actions:
            a.setChecked(False)
        self.brush_size_actions[idx].setChecked(True)
        self.current_brush_size_index = idx
        if hasattr(self, 'vtk_canvas'):
            try:
                self.vtk_canvas.set_brush_size(idx)
            except Exception:
                pass

    def _choose_color(self):
        # present a QColorDialog and set a float value between 0..1
        c = QColorDialog.getColor()
        if c.isValid():
            # use lightness as float for paint value
            v = c.lightness() / 255.0
            self.current_paint_value = v
            self._update_color_swatch()

    def on_color_picked(self, float_value: float):
        # from canvas when picker used
        self.current_paint_value = float_value
        self._update_color_swatch()

    def _update_color_swatch(self):
        # generate a small pixmap showing the current value
        size = 22
        v = int(self.current_paint_value * 255)
        pix = QPixmap(size, size)
        pix.fill(QColor(v, 0, 0))
        self.color_swatch.setPixmap(pix)


class VTKCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.vtkWidget)

        # Create renderer and basic scene
        self.ren = vtk.vtkRenderer()
        rw = self.vtkWidget.GetRenderWindow()
        rw.AddRenderer(self.ren)
        self.ren.SetBackground(0.15, 0.15, 0.2)

        # quick test actor (sphere)
        src = vtk.vtkSphereSource()
        src.SetRadius(0.5)
        src.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(src.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)

        # initialize interactor (do not call Start() — let Qt loop drive it)
        self.vtkWidget.Initialize()
        self.vtkWidget.Enable()
        self.ren.ResetCamera()
        rw.Render()

        # keep interactor handy for event binding
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        # add a pick observer
        self.interactor.AddObserver("LeftButtonPressEvent", self._on_left_click_vtk)

    def _on_left_click_vtk(self, caller, event):
        # get mouse position and pick in the renderer
        x, y = self.interactor.GetEventPosition()
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(1e-6)
        picked = picker.Pick(x, y, 0, self.ren)
        if picked:
            pos = picker.GetPickPosition()
            print("VTK picked:", pos)
        # forward normally so interactor style can process it too
        return

    # optional stubs so MainWindow can call these methods without error
    def set_mode(self, mode):
        # mode could be 'pointer','pencil','brush','picker'
        self._mode = mode

    def set_brush_size(self, idx):
        sizes = [2, 4, 8, 16, 32]
        self._brush_size = sizes[idx] if 0 <= idx < len(sizes) else sizes[1]

