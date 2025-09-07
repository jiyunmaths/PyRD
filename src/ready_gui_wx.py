import wx
import wx.aui
import wx.adv
from vtkmodules.vtkRenderingCore import vtkRenderWindow, vtkRenderer
from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import vtkmodules.all as vtk


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetSize((1000, 700))
        self.is_running = False
        self.timesteps = 0

        # AUI manager
        self._mgr = wx.aui.AuiManager(self)

        # create menu
        self._create_menu()
        # toolbars
        self._create_toolbars()
        # panes
        self._create_panes()
        # central VTK render window
        self._create_vtk_window()

        # status bar
        self.CreateStatusBar()
        self.SetStatusText('Stopped. Timesteps: 0')

        # timer to emulate OnIdle loop
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        self._mgr.Update()

    def _create_menu(self):
        mb = wx.MenuBar()
        filem = wx.Menu()
        filem.Append(wx.ID_NEW, 'New Pattern...')
        filem.Append(wx.ID_OPEN, 'Open Pattern...')
        filem.Append(wx.ID_SAVE, 'Save Pattern...')
        filem.AppendSeparator()
        filem.Append(wx.ID_EXIT, 'Quit')
        mb.Append(filem, '&File')

        viewm = wx.Menu()
        self.mi_fullscreen = viewm.AppendCheckItem(wx.ID_ANY, 'Full Screen')
        mb.Append(viewm, '&View')

        helpm = wx.Menu()
        helpm.Append(wx.ID_ABOUT, 'About')
        mb.Append(helpm, '&Help')

        self.SetMenuBar(mb)
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_toggle_fullscreen, id=self.mi_fullscreen.GetId())

    def _create_toolbars(self):
        tb_file = wx.aui.AuiToolBar(self, -1)
        tb_file.AddTool(wx.ID_NEW, 'New', wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR))
        tb_file.AddTool(wx.ID_OPEN, 'Open', wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
        tb_file.AddTool(wx.ID_SAVE, 'Save', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
        tb_file.Realize()
        self._mgr.AddPane(tb_file, wx.aui.AuiPaneInfo().Name('FileToolbar').ToolbarPane().Top())

        tb_action = wx.aui.AuiToolBar(self, -1)
        self.tbtn_step = tb_action.AddTool(wx.ID_ANY, 'Step', wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR))
        self.tbtn_run = tb_action.AddTool(wx.ID_ANY, 'Run', wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR), kind=wx.ITEM_CHECK)
        tb_action.Realize()
        self._mgr.AddPane(tb_action, wx.aui.AuiPaneInfo().Name('ActionToolbar').ToolbarPane().Top().Position(1))

        # Bind toolbar events
        self.Bind(wx.EVT_TOOL, self.on_step, id=self.tbtn_step.GetId())
        self.Bind(wx.EVT_TOOL, self.on_run_toggle, id=self.tbtn_run.GetId())

    def _create_panes(self):
        # Patterns pane (left)
        self.patterns = wx.ListBox(self, wx.ID_ANY)
        for i in range(8):
            self.patterns.Append(f'Pattern {i+1}')
        self._mgr.AddPane(self.patterns, wx.aui.AuiPaneInfo().Left().Name('PatternsPane').Caption('Patterns Pane').BestSize((220, 400)))

        # Info pane (right)
        self.info = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.info.SetValue('Info pane (system status)')
        self._mgr.AddPane(self.info, wx.aui.AuiPaneInfo().Right().Name('InfoPane').Caption('Info Pane').BestSize((400, 300)))

        # Help pane (right)
        self.help = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.help.SetValue('Help pane')
        self._mgr.AddPane(self.help, wx.aui.AuiPaneInfo().Right().Name('HelpPane').Caption('Help Pane').BestSize((400, 300)).Position(1))

    def _create_vtk_window(self):
        # create VTK render window interactor
        self.vtk_widget = wxVTKRenderWindowInteractor(self, -1)
        ren = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(ren)
        ren.SetBackground(0.2, 0.2, 0.3)

        # add a simple actor (cube) so we see something
        cube = vtk.vtkCubeSource()
        cube.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cube.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        ren.AddActor(actor)

        self._mgr.AddPane(self.vtk_widget, wx.aui.AuiPaneInfo().CenterPane().Name('CanvasPane').Caption('Render Pane'))

        # ensure interactor starts
        self.vtk_widget.Enable()
        self.vtk_widget.GetRenderWindow().Render()

    # Event handlers
    def on_quit(self, event):
        self.Close()

    def on_about(self, event):
        wx.MessageBox('Ready (wx) simplified GUI\nVTK version: ' + vtk.vtkVersion.GetVTKSourceVersion(), 'About')

    def on_toggle_fullscreen(self, event):
        if self.mi_fullscreen.IsChecked():
            self.ShowFullScreen(True)
        else:
            self.ShowFullScreen(False)

    def on_step(self, event):
        self.timesteps += 1
        self.SetStatusText(f'Stopped. Timesteps: {self.timesteps}')
        self.vtk_widget.GetRenderWindow().Render()

    def on_run_toggle(self, event):
        is_checked = self._mgr.GetPane('ActionToolbar').window.GetToolBar().GetToolState(self.tbtn_run.GetId()) if False else self.tbtn_run.IsToggled() if hasattr(self.tbtn_run, 'IsToggled') else False
        # simpler: toggle by checking tool's toggled state
        state = self._mgr.GetPane('ActionToolbar').window.GetToolBar().GetToolState(self.tbtn_run.GetId()) if False else self.tbtn_run.IsToggled() if hasattr(self.tbtn_run, 'IsToggled') else False
        # fallback: use tool's toggle via GetToolState not always available, so use local is_running flip
        self.is_running = not self.is_running
        if self.is_running:
            self.timer.Start(100)
            self.SetStatusText(f'Running. Timesteps: {self.timesteps}')
        else:
            self.timer.Stop()
            self.SetStatusText(f'Stopped. Timesteps: {self.timesteps}')

    def on_timer(self, event):
        # simulate running step and render
        self.timesteps += 1
        self.SetStatusText(f'Running. Timesteps: {self.timesteps}')
        self.vtk_widget.GetRenderWindow().Render()

    def __del__(self):
        try:
            self._mgr.UnInit()
        except Exception:
            pass
