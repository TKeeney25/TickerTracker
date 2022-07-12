import weakref

from kivy.graphics import Rectangle, Color
from kivy.uix.behaviors import DragBehavior
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout


class MyLabel(Label):
    pass


class MyH1Label(MyLabel):
    pass


class MyH2Label(MyLabel):
    pass


class MyButton(Button):
    pass


class FilterButton(MyButton):
    pass


class PanFilterButton(MyButton):
    def __init__(self, button_id, parent_view, **kwargs):
        super().__init__(**kwargs)
        self.id = button_id
        self.parent_view = parent_view


class MyNavBar(Widget):
    pass


class Spacer(Widget):
    pass


class MyLogLabel(Label):
    def __init__(self, **kwargs):
        super(MyLogLabel, self).__init__(**kwargs)


class DragScatter(Scatter):
    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                if self.scale < 10:
                    self.scale = self.scale * 1.1
            elif touch.button == 'scrollup':
                if self.scale > 1:
                    self.scale = self.scale * 0.8
        else:
            super(DragScatter, self).on_touch_down(touch)


class DragLabel(DragBehavior, Label):
    pass

class LogicNode(BoxLayout):
    def __init__(self, id_value, filter_type):
        super().__init__(orientation='horizontal', size_hint_x=None, size_hint_y=None, height=40, width=200)
        self.id = id_value
        new_button = PanFilterButton(text='-', size_hint=(.5, 1), button_id=id_value + '-', parent_view=self)
        print(new_button)
        self.add_widget(new_button)
        self.ids[id_value + '-'] = weakref.ref(new_button)
        self.add_widget(Label(text=filter_type))
        new_button = PanFilterButton(text='+', size_hint=(.5, 1), button_id=id_value + '+', parent_view=self)
        self.add_widget(new_button)
        self.ids[id_value + '+'] = weakref.ref(new_button)


class LogicFilter(BoxLayout):
    def __init__(self, id_value, filter_type):
        super().__init__(orientation='vertical', size_hint_x=None, width=200)
        layout = LogicNode(id_value, filter_type)
        for layout_id in layout.ids:
            self.ids[layout_id] = getattr(layout.ids, layout_id)
        self.add_widget(layout)
