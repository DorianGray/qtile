# Copyright (c) 2017 Dario Giovannetti
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

import pytest

from test.layouts import layout_configs
from test.layouts.layout_utils import (
    assert_dimensions_fit,
    assert_focus_path_unordered,
    assert_focused,
)

each_layout_config = pytest.mark.parametrize(
    "manager",
    layout_configs.all_layouts_config.values(),
    indirect=True,
)
all_layouts_config = pytest.mark.parametrize(
    "manager", [layout_configs.AllLayouts],
    indirect=True,
)
each_layout_config_events = pytest.mark.parametrize(
    "manager",
    layout_configs.all_layouts_config_events.values(),
    indirect=True,
)
each_delegate_layout_config = pytest.mark.parametrize(
    "manager",
    layout_configs.all_delegate_layouts_config.values(),
    indirect=True,
)


@each_layout_config
def test_window_types(manager):
    manager.test_window("one")

    # A dialog should take focus and be floating
    manager.test_dialog("dialog")
    manager.c.window.info()['floating'] is True
    assert_focused(manager, "dialog")

    # A notification shouldn't steal focus and should be floating
    manager.test_notification("notification")
    assert manager.c.group.info()['focus'] != 'notification'
    manager.c.group.info_by_name('notification')['floating'] is True


@each_layout_config
def test_focus_cycle(manager):
    manager.test_window("one")
    manager.test_window("two")
    manager.test_dialog("float1")
    manager.test_dialog("float2")
    manager.test_window("three")

    # Test preconditions (the order of items in 'clients' is managed by each layout)
    assert set(manager.c.layout.info()['clients']) == {'one', 'two', 'three'}
    assert_focused(manager, "three")

    # Assert that the layout cycles the focus on all windows
    assert_focus_path_unordered(manager, 'float1', 'float2', 'one', 'two', 'three')


@each_layout_config
def test_focus_back(manager):
    # No exception must be raised without windows
    manager.c.group.focus_back()

    # Nothing must happen with only one window
    manager.test_window("one")
    manager.c.group.focus_back()
    assert_focused(manager, "one")

    # 2 windows
    two = manager.test_window("two")
    assert_focused(manager, "two")
    manager.c.group.focus_back()
    assert_focused(manager, "one")
    manager.c.group.focus_back()
    assert_focused(manager, "two")

    # Float a window
    three = manager.test_window("three")
    manager.c.group.focus_back()
    assert_focused(manager, "two")
    manager.c.window.toggle_floating()
    manager.c.group.focus_back()
    assert_focused(manager, "three")

    # If the previous window is killed, the further previous one must be focused
    manager.test_window("four")
    manager.kill_window(two)
    manager.kill_window(three)
    assert_focused(manager, "four")
    manager.c.group.focus_back()
    assert_focused(manager, "one")


# TODO: Test more events
@each_layout_config_events
def test_focus_change_event(manager):
    # Test that the correct number of focus_change events are fired e.g. when
    # opening, closing or switching windows.
    # If for example a layout explicitly fired a focus_change event even though
    # group._Group.focus() or group._Group.remove() already fire one, the other
    # installed layouts would wrongly react to it and cause misbehaviour.
    # In short, this test prevents layouts from influencing each other in
    # unexpected ways.

    # TODO: Why does it start with 2?
    assert manager.c.get_test_data()['focus_change'] == 2

    # Spawning a window must fire only 1 focus_change event
    one = manager.test_window("one")
    assert manager.c.get_test_data()['focus_change'] == 3
    two = manager.test_window("two")
    assert manager.c.get_test_data()['focus_change'] == 4
    three = manager.test_window("three")
    assert manager.c.get_test_data()['focus_change'] == 5

    # Switching window must fire only 1 focus_change event
    assert_focused(manager, "three")
    manager.c.group.focus_by_name("one")
    assert manager.c.get_test_data()['focus_change'] == 6
    assert_focused(manager, "one")

    # Focusing the current window must fire another focus_change event
    manager.c.group.focus_by_name("one")
    assert manager.c.get_test_data()['focus_change'] == 7

    # Toggling a window floating should not fire focus_change events
    manager.c.window.toggle_floating()
    assert manager.c.get_test_data()['focus_change'] == 7
    manager.c.window.toggle_floating()
    assert manager.c.get_test_data()['focus_change'] == 7

    # Removing the focused window must fire only 1 focus_change event
    assert_focused(manager, "one")
    assert manager.c.group.info()['focus_history'] == ["two", "three", "one"]
    manager.kill_window(one)
    assert manager.c.get_test_data()['focus_change'] == 8

    # The position where 'one' was after it was floated and unfloated
    # above depends on the layout, so we can't predict here what window gets
    # selected after killing it; for this reason, focus 'three' explicitly to
    # continue testing
    manager.c.group.focus_by_name("three")
    assert manager.c.group.info()['focus_history'] == ["two", "three"]
    assert manager.c.get_test_data()['focus_change'] == 9

    # Removing a non-focused window must not fire focus_change events
    manager.kill_window(two)
    assert manager.c.get_test_data()['focus_change'] == 9
    assert_focused(manager, "three")

    # Removing the last window must still generate 1 focus_change event
    manager.kill_window(three)
    assert manager.c.layout.info()['clients'] == []
    assert manager.c.get_test_data()['focus_change'] == 10


@each_layout_config
def test_remove(manager):
    one = manager.test_window("one")
    two = manager.test_window("two")
    three = manager.test_window("three")
    assert_focused(manager, "three")
    assert manager.c.group.info()['focus_history'] == ["one", "two", "three"]

    # Removing a focused window must focus another (which one depends on the layout)
    manager.kill_window(three)
    assert manager.c.window.info()['name'] in manager.c.layout.info()['clients']

    # To continue testing, explicitly set focus on 'two'
    manager.c.group.focus_by_name("two")
    manager.test_window("four")
    assert_focused(manager, "four")
    assert manager.c.group.info()['focus_history'] == ["one", "two", "four"]

    # Removing a non-focused window must not change the current focus
    manager.kill_window(two)
    assert_focused(manager, "four")
    assert manager.c.group.info()['focus_history'] == ["one", "four"]

    # Add more windows and shuffle the focus order
    five = manager.test_window("five")
    manager.test_window("six")
    manager.c.group.focus_by_name("one")
    seven = manager.test_window("seven")
    manager.c.group.focus_by_name("six")
    assert_focused(manager, "six")
    assert manager.c.group.info()['focus_history'] == ["four", "five", "one",
                                                       "seven", "six"]

    manager.kill_window(five)
    manager.kill_window(one)
    assert_focused(manager, "six")
    assert manager.c.group.info()['focus_history'] == ["four", "seven", "six"]

    manager.c.group.focus_by_name("seven")
    manager.kill_window(seven)
    assert manager.c.window.info()['name'] in manager.c.layout.info()['clients']


@each_layout_config
def test_remove_floating(manager):
    one = manager.test_window("one")
    manager.test_window("two")
    float1 = manager.test_dialog("float1")
    assert_focused(manager, "float1")
    assert set(manager.c.layout.info()['clients']) == {"one", "two"}
    assert manager.c.group.info()['focus_history'] == ["one", "two", "float1"]

    # Removing a focused floating window must focus the one that was focused before
    manager.kill_window(float1)
    assert_focused(manager, "two")
    assert manager.c.group.info()['focus_history'] == ["one", "two"]

    float2 = manager.test_dialog("float2")
    assert_focused(manager, "float2")
    assert manager.c.group.info()['focus_history'] == ["one", "two", "float2"]

    # Removing a non-focused floating window must not change the current focus
    manager.c.group.focus_by_name("two")
    manager.kill_window(float2)
    assert_focused(manager, "two")
    assert manager.c.group.info()['focus_history'] == ["one", "two"]

    # Add more windows and shuffle the focus order
    manager.test_window("three")
    float3 = manager.test_dialog("float3")
    manager.c.group.focus_by_name("one")
    float4 = manager.test_dialog("float4")
    float5 = manager.test_dialog("float5")
    manager.c.group.focus_by_name("three")
    manager.c.group.focus_by_name("float3")
    assert manager.c.group.info()['focus_history'] == ["two", "one", "float4",
                                                       "float5", "three", "float3"]

    manager.kill_window(one)
    assert_focused(manager, "float3")
    assert manager.c.group.info()['focus_history'] == ["two", "float4",
                                                       "float5", "three", "float3"]

    manager.kill_window(float5)
    assert_focused(manager, "float3")
    assert manager.c.group.info()['focus_history'] == ["two", "float4", "three", "float3"]

    # The focus must be given to the previous window even if it's floating
    manager.c.group.focus_by_name("float4")
    assert manager.c.group.info()['focus_history'] == ["two", "three", "float3", "float4"]
    manager.kill_window(float4)
    assert_focused(manager, "float3")
    assert manager.c.group.info()['focus_history'] == ["two", "three", "float3"]

    four = manager.test_window("four")
    float6 = manager.test_dialog("float6")
    five = manager.test_window("five")
    manager.c.group.focus_by_name("float3")
    assert manager.c.group.info()['focus_history'] == ["two", "three", "four",
                                                       "float6", "five", "float3"]

    # Killing several unfocused windows before the current one, and then
    # killing the current window, must focus the remaining most recently
    # focused window
    manager.kill_window(five)
    manager.kill_window(four)
    manager.kill_window(float6)
    assert manager.c.group.info()['focus_history'] == ["two", "three", "float3"]
    manager.kill_window(float3)
    assert_focused(manager, "three")
    assert manager.c.group.info()['focus_history'] == ["two", "three"]


@each_layout_config
def test_desktop_notifications(manager):
    # Unlike normal floating windows such as dialogs, notifications don't steal
    # focus when they spawn, so test them separately

    # A notification fired in an empty group must not take focus
    notif1 = manager.test_notification("notif1")
    assert manager.c.group.info()['focus'] is None
    manager.kill_window(notif1)

    # A window is spawned while a notification is displayed
    notif2 = manager.test_notification("notif2")
    one = manager.test_window("one")
    assert manager.c.group.info()['focus_history'] == ["one"]
    manager.kill_window(notif2)

    # Another notification is fired, but the focus must not change
    notif3 = manager.test_notification("notif3")
    assert_focused(manager, 'one')
    manager.kill_window(notif3)

    # Complicate the scenario with multiple windows and notifications

    dialog1 = manager.test_dialog("dialog1")
    manager.test_window("two")
    notif4 = manager.test_notification("notif4")
    notif5 = manager.test_notification("notif5")
    assert manager.c.group.info()['focus_history'] == ["one", "dialog1", "two"]

    dialog2 = manager.test_dialog("dialog2")
    manager.kill_window(notif5)
    manager.test_window("three")
    manager.kill_window(one)
    manager.c.group.focus_by_name("two")
    notif6 = manager.test_notification("notif6")
    notif7 = manager.test_notification("notif7")
    manager.kill_window(notif4)
    notif8 = manager.test_notification("notif8")
    assert manager.c.group.info()['focus_history'] == ["dialog1", "dialog2",
                                                       "three", "two"]

    manager.test_dialog("dialog3")
    manager.kill_window(dialog1)
    manager.kill_window(dialog2)
    manager.kill_window(notif6)
    manager.c.group.focus_by_name("three")
    manager.kill_window(notif7)
    manager.kill_window(notif8)
    assert manager.c.group.info()['focus_history'] == ["two", "dialog3", "three"]


@each_delegate_layout_config
def test_only_uses_delegated_screen_rect(manager):
    manager.test_window("one")
    manager.c.group.focus_by_name("one")
    assert_focused(manager, "one")
    assert_dimensions_fit(manager, 256, 0, 800-256, 600)


@all_layouts_config
def test_cycle_layouts(manager):
    manager.test_window("one")
    manager.test_window("two")
    manager.test_window("three")
    manager.test_window("four")
    manager.c.group.focus_by_name("three")
    assert_focused(manager, "three")

    # Cycling all the layouts must keep the current window focused
    initial_layout_name = manager.c.layout.info()['name']
    while True:
        manager.c.next_layout()
        if manager.c.layout.info()['name'] == initial_layout_name:
            break
        # Use manager.c.layout.info()['name'] in the assertion message, so we
        # know which layout is buggy
        assert manager.c.window.info()['name'] == "three", manager.c.layout.info()['name']

    # Now try backwards
    while True:
        manager.c.prev_layout()
        if manager.c.layout.info()['name'] == initial_layout_name:
            break
        # Use manager.c.layout.info()['name'] in the assertion message, so we
        # know which layout is buggy
        assert manager.c.window.info()['name'] == "three", manager.c.layout.info()['name']
