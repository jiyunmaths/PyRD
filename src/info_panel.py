from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt

import os
import time
from xml_file_parser import XMLFileParser


class InfoPanel(QWidget):
    """A simple Info panel that displays metadata and a text preview
    for a selected file. Use `show_file(path)` to populate the pane.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)

        # selected information to display
        self.rule_name_label = "Rule name"
        self.rule_type_label = "Rule type"
        self.description_label = "Description"
        self.num_chemicals_label = "Number of chemicals"
        self.formula_label = "Formula"
        self.kernel_label = "Kernel"
        self.dimensions_label = "Dimensions"
        self.block_size_label = "Block size"
        self.use_local_memory_label = "Use local memory"
        self.number_of_cells_label = "Number of cells"
        self.wrap_label = "Toroidal wrap-around"
        self.data_type_label = "Data type"
        self.neighborhood_type_label = "Neighborhood"
        self.neighborhood_range_label = "Neighborhood range"
        self.neighborhood_weight_label = "Neighborhood weight"
        self.accuracy_label = "Accuracy"
        self.accuracy_labels = ["low", "medium", "high" ]



    def set_info(self, text: str):
        self.editor.setPlainText(text)

    def clear(self):
        self.editor.clear()

    def show_file(self, path: str):
        """Display information and a safe text preview for `path`.
        For .vti/.vtu files, show a summary of the XML structure using XMLFileParser.
        """
        if not path:
            self.set_info('No file selected')
            return

        if not os.path.exists(path):
            self.set_info(f'File not found: {path}')
            return

        try:
            st = os.stat(path)
            size = st.st_size
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime))
            ext = os.path.splitext(path)[1].lower()

            header = [f'File: {path}', f'Size: {format_size(size)}', f'Modified: {mtime}', f'Type: {ext or "(none)"}', '']

            if ext in ('.vti', '.vtu', '.xml'):
                try:
                    parser = XMLFileParser(path)
                    parser.parse()
                    xml_summary = parser.get_summary()
                    body = f'XML Structure Summary:\n\n{xml_summary}'
                except Exception as e:
                    body = f'Failed to parse XML: {e}'
                self.set_info('\n'.join(header + [body]))
                return

            # fallback to original text/binary preview for other files
            is_text = True
            with open(path, 'rb') as fh:
                chunk = fh.read(2048)
                if b'\x00' in chunk:
                    is_text = False

            if not is_text:
                body = 'Binary or non-text file; contents omitted.'
                self.set_info('\n'.join(header + [body]))
                return

            max_chars = 50000
            with open(path, 'r', errors='replace') as fh:
                txt = fh.read(max_chars + 1)

            truncated = False
            if len(txt) > max_chars:
                truncated = True
                txt = txt[:max_chars]

            if truncated:
                header.append(f'(truncated to {max_chars} chars)')
            header.append('')
            body = txt
            self.set_info('\n'.join(header) + body)

        except Exception as e:
            self.set_info(f'Failed to read file: {path}\nError: {e}')


def format_size(n: int) -> str:
    """Human readable size."""
    try:
        n = float(n)
    except Exception:
        return str(n)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024.0:
            if unit == 'B':
                return f'{int(n)} {unit}'
            return f'{n:.1f} {unit}'
        n /= 1024.0
    return f'{n:.1f} TB'


if __name__ == '__main__':
    # quick standalone demo: launch a window and optionally show a file
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = InfoPanel()
    if len(sys.argv) > 1:
        w.show_file(sys.argv[1])
    else:
        w.set_info('InfoPanel demo. Pass a file path as the first argument to preview it.')
    w.resize(700, 500)
    w.show()
    sys.exit(app.exec_())
