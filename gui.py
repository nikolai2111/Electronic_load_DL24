import sys
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets

from PyQt5.QtCore import (
    Qt, )

from PyQt5.QtWidgets import (
    QWidget,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar

from matplotlib.figure import Figure
from datetime import time as tm

from instruments.instrument import Instrument


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Battery tester")
        self.resize(1024, 600)

        main_layout = QHBoxLayout()
        main_layout.addLayout(self.plot_layout())
        main_layout.addLayout(self.controls_layout())

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        self.show()

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def plot_layout(self):
        self.canvas = MplCanvas(self, width=8, height=4, dpi=100)
        self.ax = self.canvas.axes
        self.twinax = self.ax.twinx()

        toolbar = NavigationToolbar(self.canvas, self)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        return layout

    def controls_layout(self):
        layout = QVBoxLayout()

        self.en_checkbox = QCheckBox("Enabled")
        layout.addWidget(self.en_checkbox)

        self.set_v = QLineEdit()
        self.set_v.setMaxLength(5)
        self.set_v.returnPressed.connect(self.voltage_set)
        layout.addLayout(self.__label_for(self.set_v, "Voltage"))

        self.set_curr = QLineEdit()
        self.set_curr.setMaxLength(5)
        self.set_curr.returnPressed.connect(self.current_set)
        layout.addLayout(self.__label_for(self.set_curr, "Current"))

        return layout

    def __label_for(self, control, text):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(text))
        layout.addWidget(control)

        return layout

    def update_plot(self):
        print("update_plot")
        data = self.backend.datastore.data
        if len(data) > 0:
            lastrow = data.tail(1)

            set_voltage = lastrow['set_voltage'].to_list()[0]
            if not self.set_v.hasFocus():
                self.set_v.setText('{:4.2f}'.format(set_voltage))

            set_current = lastrow['set_current'].to_list()[0]
            if not self.set_curr.hasFocus():
                self.set_curr.setText('{:4.2f}'.format(set_current))

            time = lastrow['time'].to_list()[0]

            is_on = lastrow['is_on'].to_list()[0]
            if is_on:
                self.en_checkbox.setCheckState(Qt.Checked)
            else:
                self.en_checkbox.setCheckState(Qt.Unchecked)

            if time != tm(0):
                self.ax.cla()
                self.twinax.cla()
                data.plot(ax=self.ax, x='time', y=['voltage'])
                self.ax.legend(loc='center left')
                self.ax.set_ylabel('Voltage, V')
                self.ax.set_ylim(bottom=set_voltage)
                data.plot(ax=self.twinax, x='time', y=['current'], style='r')
                self.twinax.legend(loc='center right')
                self.twinax.set_ylabel('Current, A')
                self.twinax.set_ylim(0, 10)
                self.canvas.draw()

    def set_backend(self, backend):
        self.backend = backend

    def closeEvent(self, event):
        self.backend.at_exit()
        event.accept()

    def voltage_set(self):
        value = float(self.set_v.text())
        self.set_v.clearFocus()
        self.backend.send_command({Instrument.COMMAND_SET_VOLTAGE: value})

    def current_set(self):
        value = float(self.set_curr.text())
        self.set_curr.clearFocus()
        self.backend.send_command({Instrument.COMMAND_SET_CURRENT: value})


class GUI:
    def __init__(self, backend):
        app = QtWidgets.QApplication(sys.argv)
        self.window = MainWindow()
        self.window.set_backend(backend)
        app.exec_()