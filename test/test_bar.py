# Copyright (c) 2011 Florian Mounier
# Copyright (c) 2012-2013 Craig Barnes
# Copyright (c) 2012 roger
# Copyright (c) 2012, 2014-2015 Tycho Andersen
# Copyright (c) 2014 Sean Vig
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import tempfile

import pytest

import libqtile.bar
import libqtile.config
import libqtile.confreader
import libqtile.layout
import libqtile.widget
from test.conftest import with_config


class GBConfig(libqtile.confreader.Config):
    auto_fullscreen = True
    keys = []
    mouse = []
    groups = [
        libqtile.config.Group("a"),
        libqtile.config.Group("bb"),
        libqtile.config.Group("ccc"),
        libqtile.config.Group("dddd"),
        libqtile.config.Group("Pppy")
    ]
    layouts = [libqtile.layout.stack.Stack(num_stacks=1)]
    floating_layout = libqtile.resources.default_config.floating_layout
    screens = [
        libqtile.config.Screen(
            top=libqtile.bar.Bar(
                [
                    libqtile.widget.CPUGraph(
                        width=libqtile.bar.STRETCH,
                        type="linefill",
                        border_width=20,
                        margin_x=1,
                        margin_y=1
                    ),
                    libqtile.widget.MemoryGraph(type="line"),
                    libqtile.widget.SwapGraph(type="box"),
                    libqtile.widget.TextBox(name="text",
                                            background="333333"),
                ],
                50,
            ),
            bottom=libqtile.bar.Bar(
                [
                    libqtile.widget.GroupBox(),
                    libqtile.widget.AGroupBox(),
                    libqtile.widget.Prompt(),
                    libqtile.widget.WindowName(),
                    libqtile.widget.Sep(),
                    libqtile.widget.Clock(),
                ],
                50
            ),
            # TODO: Add vertical bars and test widgets that support them
        )
    ]


def test_completion():
    c = libqtile.widget.prompt.CommandCompleter(None, True)
    c.reset()
    c.lookup = [
        ("a", "x/a"),
        ("aa", "x/aa"),
    ]
    assert c.complete("a") == "a"
    assert c.actual() == "x/a"
    assert c.complete("a") == "aa"
    assert c.complete("a") == "a"

    c = libqtile.widget.prompt.CommandCompleter(None)
    r = c.complete("l")
    assert c.actual().endswith(r)

    c.reset()
    assert c.complete("/bi") == "/bin/"
    c.reset()
    assert c.complete("/bin") != "/bin/"
    c.reset()

    home_dir = os.path.expanduser("~")
    with tempfile.TemporaryDirectory(prefix="qtile_test_",
                                     dir=home_dir) as absolute_tmp_path:
        tmp_dirname = absolute_tmp_path[len(home_dir + os.sep):]
        user_input = os.path.join("~", tmp_dirname)
        assert c.complete(user_input) == user_input

        c.reset()
        test_bin_dir = os.path.join(absolute_tmp_path, "qtile-test-bin")
        os.mkdir(test_bin_dir)
        assert c.complete(user_input) == os.path.join(user_input, "qtile-test-bin") + os.sep

    c.reset()
    s = "thisisatotallynonexistantpathforsure"
    assert c.complete(s) == s
    assert c.actual() == s
    c.reset()


@with_config(GBConfig)
def test_draw(manager):
    manager.test_window("one")
    b = manager.c.bar["bottom"].info()
    assert b["widgets"][0]["name"] == "groupbox"


@with_config(GBConfig)
def test_prompt(manager):
    assert manager.c.widget["prompt"].info()["width"] == 0
    manager.c.spawncmd(":")
    manager.c.widget["prompt"].fake_keypress("a")
    manager.c.widget["prompt"].fake_keypress("Tab")

    manager.c.spawncmd(":")
    manager.c.widget["prompt"].fake_keypress("slash")
    manager.c.widget["prompt"].fake_keypress("Tab")


@with_config(GBConfig)
def test_event(manager):
    manager.c.group["bb"].toscreen()


@with_config(GBConfig)
def test_textbox(manager):
    assert "text" in manager.c.list_widgets()
    s = "some text"
    manager.c.widget["text"].update(s)
    assert manager.c.widget["text"].get() == s
    s = "Aye, much longer string than the initial one"
    manager.c.widget["text"].update(s)
    assert manager.c.widget["text"].get() == s
    manager.c.group["Pppy"].toscreen()
    manager.c.widget["text"].set_font(fontsize=12)


@with_config(GBConfig)
def test_textbox_errors(manager):
    manager.c.widget["text"].update(None)
    manager.c.widget["text"].update("".join(chr(i) for i in range(255)))
    manager.c.widget["text"].update("V\xE2r\xE2na\xE7\xEE")
    manager.c.widget["text"].update("\ua000")


@with_config(GBConfig)
def test_groupbox_button_press(manager):
    manager.c.group["ccc"].toscreen()
    assert manager.c.groups()["a"]["screen"] is None
    manager.c.bar["bottom"].fake_button_press(0, "bottom", 10, 10, 1)
    assert manager.c.groups()["a"]["screen"] == 0


class GeomConfig(libqtile.confreader.Config):
    auto_fullscreen = False
    keys = []
    mouse = []
    groups = [
        libqtile.config.Group("a"),
        libqtile.config.Group("b"),
        libqtile.config.Group("c"),
        libqtile.config.Group("d")
    ]
    layouts = [libqtile.layout.stack.Stack(num_stacks=1)]
    floating_layout = libqtile.resources.default_config.floating_layout
    screens = [
        libqtile.config.Screen(
            top=libqtile.bar.Bar([], 10),
            bottom=libqtile.bar.Bar([], 10),
            left=libqtile.bar.Bar([], 10),
            right=libqtile.bar.Bar([], 10),
        )
    ]


class DBarH(libqtile.bar.Bar):
    def __init__(self, widgets, size):
        libqtile.bar.Bar.__init__(self, widgets, size)
        self.horizontal = True


class DBarV(libqtile.bar.Bar):
    def __init__(self, widgets, size):
        libqtile.bar.Bar.__init__(self, widgets, size)
        self.horizontal = False


class DWidget:
    def __init__(self, length, length_type):
        self.length, self.length_type = length, length_type


@with_config(GeomConfig)
def test_geometry(manager):
    manager.test_xeyes()
    g = manager.c.screens()[0]["gaps"]
    assert g["top"] == (0, 0, 800, 10)
    assert g["bottom"] == (0, 590, 800, 10)
    assert g["left"] == (0, 10, 10, 580)
    assert g["right"] == (790, 10, 10, 580)
    assert len(manager.c.windows()) == 1
    geom = manager.c.windows()[0]
    assert geom["x"] == 10
    assert geom["y"] == 10
    assert geom["width"] == 778
    assert geom["height"] == 578
    internal = manager.c.internal_windows()
    assert len(internal) == 4
    wid = manager.c.bar["bottom"].info()["window"]
    assert manager.c.window[wid].inspect()


@with_config(GeomConfig)
def test_resize(manager):
    def wd(dwidget_list):
        return [i.length for i in dwidget_list]

    def offx(dwidget_list):
        return [i.offsetx for i in dwidget_list]

    def offy(dwidget_list):
        return [i.offsety for i in dwidget_list]

    for DBar, off in ((DBarH, offx), (DBarV, offy)):  # noqa: N806
        b = DBar([], 100)

        dwidget_list = [
            DWidget(10, libqtile.bar.CALCULATED),
            DWidget(None, libqtile.bar.STRETCH),
            DWidget(None, libqtile.bar.STRETCH),
            DWidget(10, libqtile.bar.CALCULATED),
        ]
        b._resize(100, dwidget_list)
        assert wd(dwidget_list) == [10, 40, 40, 10]
        assert off(dwidget_list) == [0, 10, 50, 90]

        b._resize(101, dwidget_list)
        assert wd(dwidget_list) == [10, 40, 41, 10]
        assert off(dwidget_list) == [0, 10, 50, 91]

        dwidget_list = [
            DWidget(10, libqtile.bar.CALCULATED)
        ]
        b._resize(100, dwidget_list)
        assert wd(dwidget_list) == [10]
        assert off(dwidget_list) == [0]

        dwidget_list = [
            DWidget(10, libqtile.bar.CALCULATED),
            DWidget(None, libqtile.bar.STRETCH)
        ]
        b._resize(100, dwidget_list)
        assert wd(dwidget_list) == [10, 90]
        assert off(dwidget_list) == [0, 10]

        dwidget_list = [
            DWidget(None, libqtile.bar.STRETCH),
            DWidget(10, libqtile.bar.CALCULATED),
        ]
        b._resize(100, dwidget_list)
        assert wd(dwidget_list) == [90, 10]
        assert off(dwidget_list) == [0, 90]

        dwidget_list = [
            DWidget(10, libqtile.bar.CALCULATED),
            DWidget(None, libqtile.bar.STRETCH),
            DWidget(10, libqtile.bar.CALCULATED),
        ]
        b._resize(100, dwidget_list)
        assert wd(dwidget_list) == [10, 80, 10]
        assert off(dwidget_list) == [0, 10, 90]


class ExampleWidget(libqtile.widget.base._Widget):
    orientations = libqtile.widget.base.ORIENTATION_HORIZONTAL

    def __init__(self):
        libqtile.widget.base._Widget.__init__(self, 10)

    def draw(self):
        pass


class IncompatibleWidgetConfig(libqtile.confreader.Config):
    keys = []
    mouse = []
    groups = [libqtile.config.Group("a")]
    layouts = [libqtile.layout.stack.Stack(num_stacks=1)]
    floating_layout = libqtile.resources.default_config.floating_layout
    screens = [
        libqtile.config.Screen(
            left=libqtile.bar.Bar(
                [
                    # This widget doesn't support vertical orientation
                    ExampleWidget(),
                ],
                10,
            ),
        )
    ]


def test_incompatible_widget(manager_nospawn):
    # Ensure that adding a widget that doesn't support the orientation of the
    # bar raises ConfigError
    m = manager_nospawn.create_manager(IncompatibleWidgetConfig)
    try:
        with pytest.raises(libqtile.confreader.ConfigError):
            m._configure()
    finally:
        m.core.finalize()


class BasicConfig(GeomConfig):
    screens = [
        libqtile.config.Screen(
            bottom=libqtile.bar.Bar(
                [
                    ExampleWidget(),
                    libqtile.widget.Spacer(libqtile.bar.STRETCH),
                    ExampleWidget(),
                    libqtile.widget.Spacer(libqtile.bar.STRETCH),
                    ExampleWidget(),
                    libqtile.widget.Spacer(libqtile.bar.STRETCH),
                    ExampleWidget(),
                ],
                10,
            )
        )
    ]


@with_config(BasicConfig)
def test_basic(manager):
    i = manager.c.bar["bottom"].info()
    assert i["widgets"][0]["offset"] == 0
    assert i["widgets"][1]["offset"] == 10
    assert i["widgets"][1]["width"] == 252
    assert i["widgets"][2]["offset"] == 262
    assert i["widgets"][3]["offset"] == 272
    assert i["widgets"][3]["width"] == 256
    assert i["widgets"][4]["offset"] == 528
    assert i["widgets"][5]["offset"] == 538
    assert i["widgets"][5]["width"] == 252
    assert i["widgets"][6]["offset"] == 790


class SingleSpacerConfig(GeomConfig):
    screens = [
        libqtile.config.Screen(
            bottom=libqtile.bar.Bar(
                [
                    libqtile.widget.Spacer(libqtile.bar.STRETCH),
                ],
                10,
            ),
        ),
    ]


@with_config(SingleSpacerConfig)
def test_singlespacer(manager):
    i = manager.c.bar["bottom"].info()
    assert i["widgets"][0]["offset"] == 0
    assert i["widgets"][0]["width"] == 800


class NoSpacerConfig(GeomConfig):
    screens = [
        libqtile.config.Screen(
            bottom=libqtile.bar.Bar(
                [
                    ExampleWidget(),
                    ExampleWidget(),
                ],
                10,
            ),
        ),
    ]


@with_config(NoSpacerConfig)
def test_nospacer(manager):
    i = manager.c.bar["bottom"].info()
    assert i["widgets"][0]["offset"] == 0
    assert i["widgets"][1]["offset"] == 10
