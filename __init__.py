import struct
from typing import Optional

from PySide2.QtGui import QFontMetricsF, Qt
from binaryninja import BinaryDataNotification, BinaryView
from binaryninjaui import DockContextHandler, UIContextNotification, UIContext, ViewFrame, View, ViewLocation, \
    getMonospaceFont
from PySide2.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QTableWidgetItem, QAbstractItemView
from . import widget


class SelectionDisplayWidget(QWidget, DockContextHandler, BinaryDataNotification, UIContextNotification):
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

        def transform_float(conts, endian=">"):
            if len(conts) == 2:
                return str(struct.unpack(f"{endian}e", conts)[0])
            if len(conts) == 4:
                return str(struct.unpack(f"{endian}f", conts)[0])
            if len(conts) == 8:
                return str(struct.unpack(f"{endian}d", conts)[0])
            if len(conts) == 10:
                return "TODO: tfloats"
            raise NotImplementedError("Invalid size float")

        def transform_bin(conts):
            return " ".join(f"{c:08b}" for c in conts)

        def transform_uleb128(conts):
            shift = 0
            result = 0
            i = 0
            while True:
                byte = conts[i]
                if shift == 63 and byte != 0 and byte != 1:
                    # Longer than 64 bits
                    raise ValueError("Invalid data")

                bits = byte & 0x7f
                result |= bits << shift
                shift += 7
                i += 1

                if byte & 0x80 == 0:
                    break

            return f"{result}"

        def transform_sleb128(conts):
            shift = 0
            result = 0
            i = 0
            while True:
                byte = conts[i]
                result |= (byte & 0x7f) << shift
                shift += 7
                i += 1

                if byte & 0x80 == 0:
                    break

            if (byte & 0x40) == 0x40:
                result |= ~0 << shift

            return f"{result}"

        transforms = [
            ("Int LE Hex", lambda conts: f"0x{int(conts[::-1].hex(), 16):x}"),
            ("Int LE Dec", lambda conts: f"{int(conts[::-1].hex(), 16)}"),
            ("Int BE Hex", lambda conts: f"0x{int(conts.hex(), 16):x}"),
            ("Int BE Dec", lambda conts: f"{int(conts.hex(), 16)}"),
            ("Float LE",   lambda conts: transform_float(conts, "<")),
            ("Float BE",   lambda conts: transform_float(conts, ">")),
            ("Binary LE",  lambda conts: transform_bin(conts[::-1])),
            ("Binary BE",  transform_bin),
            ("Bytes",      lambda conts: repr(conts)[2:-1]),
            ("UTF-8",      lambda conts: conts.decode(conts, 'utf-8')),
            ("UTF-16 LE",  lambda conts: conts.decode(conts, 'utf-16-le')),
            ("UTF-16 BE",  lambda conts: conts.decode(conts, 'utf-16-be')),
            ("UTF-32 BE",  lambda conts: conts.decode(conts, 'utf-32-be')),
            ("UTF-32 BE",  lambda conts: conts.decode(conts, 'utf-32-be')),
            ("ULEB128",    transform_uleb128),
            ("SLEB128",    transform_sleb128),
        ]

        self.table.setRowCount(len(transforms))

        for i, (name, fn) in enumerate(transforms):
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


widget.register_dockwidget(SelectionDisplayWidget, "Selection Display", default_visibility=False)
