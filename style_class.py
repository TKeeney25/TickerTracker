from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class MyLabel(Label):
    pass


class MyH1Label(MyLabel):
    pass


class MyH2Label(MyLabel):
    pass


class MyButton(Button):
    pass


class MyNavBar(Widget):
    pass


class MyLogLabel(Label):
    def __init__(self, **kwargs):
        super(MyLogLabel, self).__init__(**kwargs)