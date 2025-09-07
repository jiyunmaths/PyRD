import sys
import wx
from ready_gui_wx import MyFrame


def main():
    app = wx.App(False)
    frame = MyFrame(None, title="Ready (wx) - simplified")
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
