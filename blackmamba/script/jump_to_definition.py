#!python3

from blackmamba.picker import load_picker_view, PickerItem, PickerDataSource
import editor
import console
import blackmamba.ide as ide
import os
import ui
import jedi


def _open_and_scroll(path, line):
    if editor.get_path() == path:
        ide.scroll_to_line(line)
    else:
        def scroll():
            ide.scroll_to_line(line)
        editor.open_file(path, new_tab=True)
        ui.delay(scroll, 0.2)


class LocationPickerItem(PickerItem):
    def __init__(self, path, line, display_folder):
        super().__init__(
            '{}, line {}'.format(os.path.basename(path), line),
            display_folder
        )
        self.path = path
        self.line = line

    def matches_title(self, terms):
        if not terms:
            return True

        start = 0
        for t in terms:
            start = self.path.find(t, start)

            if start == -1:
                return False

            start += len(t)

        return True


class LocationDataSource(PickerDataSource):
    def __init__(self, definitions):
        super().__init__()

        home_folder = os.path.expanduser('~/Documents')

        items = [
            LocationPickerItem(
                definition.module_path,
                definition.line,
                ' • '.join(os.path.dirname(definition.module_path)[len(home_folder) + 1:].split(os.sep))
            )
            for definition in definitions
        ]

        self.items = items


def _select_location(definitions):
    def open_location(item, shift_enter):
        _open_and_scroll(item.path, item.line)

    v = load_picker_view()
    v.name = 'Multiple definitions found'
    v.datasource = LocationDataSource(definitions)

    v.shift_enter_enabled = False
    v.help_label.text = (
        '⇅ - select • Enter - open file and scroll to location'
        '\n'
        'Esc - close • Ctrl [ - close with Apple smart keyboard'
    )
    v.textfield.placeholder = 'Start typing to filter files...'
    v.did_select_item_action = open_location
    v.present('sheet')
    v.wait_modal()


def jump_to_definition():
    ide.save()

    text = editor.get_text()
    if not text:
        return

    line = ide.get_line_number()
    column = ide.get_column_index()

    script = jedi.api.Script(text, line, column, editor.get_path())
    definitions = script.goto_definitions()

    if not definitions:
        console.hud_alert('Definition not found', 'error')
        return

    if len(definitions) == 1:
        _open_and_scroll(definitions[0].module_path, definitions[0].line)
    else:
        _select_location(definitions)


if __name__ == '__main__':
    jump_to_definition()