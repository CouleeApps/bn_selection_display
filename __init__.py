from typing import Optional

from PySide2.QtGui import QFontMetricsF, Qt
from PySide2.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QTableWidgetItem, QAbstractItemView
from binaryninja import BinaryDataNotification, BinaryView
from binaryninjaui import DockContextHandler, UIContextNotification, UIContext, ViewFrame, View, ViewLocation, \
    getMonospaceFont

import selection_display.formats
import selection_display.widget


class SelectionDisplayWidget(QWidget, DockContextHandler, BinaryDataNotification, UIContextNotification):
    FORMATS = []

    def __init__(self, parent: QWidget, name: str, data: BinaryView):
        if not type(data) == BinaryView:
            raise Exception('expected widget data to be a BinaryView')

        self.bv = data

        QWidget.__init__(self, parent)
        DockContextHandler.__init__(self, self, name)
        BinaryDataNotification.__init__(self)
        UIContextNotification.__init__(self)

        self.last_selection = (0, 0)
        self.init_ui()

        data.register_notification(self)
        UIContext.registerNotification(self)

    def __del__(self):
        self.bv.unregister_notification(self)
        UIContext.unregisterNotification(self)

    def init_ui(self):
        self.table = QTableWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        self.font = getMonospaceFont(self)
        self.table.setRowCount(0)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setLineWidth(0)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setFont(self.font)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(QFontMetricsF(self.font).height())
        self.setLayout(layout)

    def update_ui(self):
        conts = self.bv[self.last_selection[0]:self.last_selection[1]]

        self.table.setRowCount(len(SelectionDisplayWidget.FORMATS))
        for i, (name, fn) in enumerate(SelectionDisplayWidget.FORMATS):
            label_item = QTableWidgetItem(name)
            label_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(i, 0, label_item)
            try:
                value = fn(conts)
                assert type(value) == str
            except:
                value = "<error>"
            self.table.setItem(i, 1, QTableWidgetItem(value))

    def OnAddressChange(self, context: UIContext, frame: Optional[ViewFrame], view: View, location: ViewLocation):
        selection = view.getSelectionOffsets()

        if selection != self.last_selection:
            self.last_selection = selection
            self.update_ui()

    def data_written(self, view, offset, length):
        write_start = offset
        write_end = offset + length

        if write_start > self.last_selection[1] or write_end < self.last_selection[0]:
            return

        self.update_ui()

    @staticmethod
    def add_format(name, func):
        SelectionDisplayWidget.FORMATS.append((name, func))


formats.add_default_formats()
widget.register_dockwidget(SelectionDisplayWidget, "Selection Display", default_visibility=False)
