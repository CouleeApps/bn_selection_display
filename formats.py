import codecs
import struct
import selection_display


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
        result |= (byte & 0x7f) << shift
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


def add_default_formats():
    selection_display.SelectionDisplayWidget.add_format("Int LE Hex", lambda conts: f"0x{int(conts[::-1].hex(), 16):x}")
    selection_display.SelectionDisplayWidget.add_format("Int LE Dec", lambda conts: f"{int(conts[::-1].hex(), 16)}")
    selection_display.SelectionDisplayWidget.add_format("Int BE Hex", lambda conts: f"0x{int(conts.hex(), 16):x}")
    selection_display.SelectionDisplayWidget.add_format("Int BE Dec", lambda conts: f"{int(conts.hex(), 16)}")
    selection_display.SelectionDisplayWidget.add_format("Float LE",   lambda conts: transform_float(conts, "<"))
    selection_display.SelectionDisplayWidget.add_format("Float BE",   lambda conts: transform_float(conts, ">"))
    selection_display.SelectionDisplayWidget.add_format("Binary LE",  lambda conts: transform_bin(conts[::-1]))
    selection_display.SelectionDisplayWidget.add_format("Binary BE",  transform_bin)
    selection_display.SelectionDisplayWidget.add_format("ULEB128",    transform_uleb128)
    selection_display.SelectionDisplayWidget.add_format("SLEB128",    transform_sleb128)
    selection_display.SelectionDisplayWidget.add_format("Bytes",      lambda conts: repr(conts)[2:-1])
    selection_display.SelectionDisplayWidget.add_format("UTF-8",      lambda conts: codecs.decode(conts, 'utf-8'))
    selection_display.SelectionDisplayWidget.add_format("UTF-16 LE",  lambda conts: codecs.decode(conts, 'utf-16-le'))
    selection_display.SelectionDisplayWidget.add_format("UTF-16 BE",  lambda conts: codecs.decode(conts, 'utf-16-be'))
    selection_display.SelectionDisplayWidget.add_format("UTF-32 LE",  lambda conts: codecs.decode(conts, 'utf-32-le'))
    selection_display.SelectionDisplayWidget.add_format("UTF-32 BE",  lambda conts: codecs.decode(conts, 'utf-32-be'))
