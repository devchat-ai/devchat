import os

from .rpc import rpc_call
from .types import LocationWithText


@rpc_call
def run_code(code: str):
    pass


@rpc_call
def diff_apply(filepath, content):
    pass


@rpc_call
def get_symbol_defines_in_selected_code():
    pass


def find_symbol(command, abspath, line, col):
    code = (
        f"const position = new vscode.Position({line}, {col});"
        f"const absPath = vscode.Uri.file('{abspath}');"
        f"return await vscode.commands.executeCommand('{command}', absPath, position);"
    )
    result = run_code(code=code)
    return result


def find_definition(abspath: str, line: int, col: int):
    return find_symbol("vscode.executeDefinitionProvider", abspath, line, col)


def find_type_definition(abspath: str, line: int, col: int):
    return find_symbol("vscode.executeTypeDefinitionProvider", abspath, line, col)


def find_declaration(abspath: str, line: int, col: int):
    return find_symbol("vscode.executeDeclarationProvider", abspath, line, col)


def find_implementation(abspath: str, line: int, col: int):
    return find_symbol("vscode.executeImplementationProvider", abspath, line, col)


def find_reference(abspath: str, line: int, col: int):
    return find_symbol("vscode.executeReferenceProvider", abspath, line, col)


def document_symbols(abspath: str):
    code = (
        f"const fileUri = vscode.Uri.file('{abspath}');"
        "return await vscode.commands.executeCommand("
        "'vscode.executeDocumentSymbolProvider', fileUri);"
    )
    symbols = run_code(code=code)
    return symbols


def workspace_symbols(query: str):
    code = (
        "return await vscode.commands.executeCommand('vscode.executeWorkspaceSymbolProvider',"
        f" '{query}');"
    )
    return run_code(code=code)


def active_text_editor():
    code = "return vscode.window.activeTextEditor;"
    return run_code(code=code)


def open_folder(folder: str):
    folder = folder.replace("\\", "/")
    code = (
        f"const folderUri = vscode.Uri.file('{folder}');"
        "vscode.commands.executeCommand(`vscode.openFolder`, folderUri);"
    )
    run_code(code=code)


def visible_lines():
    active_document = active_text_editor()
    fail_result = {
        "filePath": "",
        "visibleText": "",
        "visibleRange": [-1, -1],
    }

    if not active_document:
        return fail_result
    if not os.path.exists(active_document["document"]["uri"]["fsPath"]):
        return fail_result

    file_path = active_document["document"]["uri"]["fsPath"]
    start_line = active_document["visibleRanges"][0][0]["line"]
    end_line = active_document["visibleRanges"][0][1]["line"]

    # read file lines from start_line to end_line
    with open(file_path, "r", encoding="utf-8") as file:
        _lines = file.readlines()
        _visible_lines = _lines[start_line : end_line + 1]

    # continue with the rest of the function
    return {
        "filePath": file_path,
        "visibleText": "".join(_visible_lines),
        "visibleRange": [start_line, end_line],
    }


def visible_range() -> LocationWithText:
    visible_range_text = visible_lines()
    return LocationWithText(
        text=visible_range_text["visibleText"],
        abspath=visible_range_text["filePath"],
        range={
            "start": {
                "line": visible_range_text["visibleRange"][0],
                "character": 0,
            },
            "end": {
                "line": visible_range_text["visibleRange"][1],
                "character": 0,
            },
        },
    )


def selected_lines():
    active_document = active_text_editor()
    fail_result = {
        "filePath": "",
        "selectedText": "",
        "selectedRange": [-1, -1, -1, -1],
    }

    if not active_document:
        return fail_result
    if not os.path.exists(active_document["document"]["uri"]["fsPath"]):
        return fail_result

    file_path = active_document["document"]["uri"]["fsPath"]
    start_line = active_document["selection"]["start"]["line"]
    start_col = active_document["selection"]["start"]["character"]
    end_line = active_document["selection"]["end"]["line"]
    end_col = active_document["selection"]["end"]["character"]

    # read file lines from start_line to end_line
    with open(file_path, "r", encoding="utf-8") as file:
        _lines = file.readlines()
        _selected_lines = _lines[start_line : end_line + 1]

    # continue with the rest of the function
    return {
        "filePath": file_path,
        "selectedText": "".join(_selected_lines),
        "selectedRange": [start_line, start_col, end_line, end_col],
    }


def selected_range() -> LocationWithText:
    selected_range_text = selected_lines()
    return LocationWithText(
        text=selected_range_text["selectedText"],
        abspath=selected_range_text["filePath"],
        range={
            "start": {
                "line": selected_range_text["selectedRange"][0],
                "character": selected_range_text["selectedRange"][1],
            },
            "end": {
                "line": selected_range_text["selectedRange"][2],
                "character": selected_range_text["selectedRange"][3],
            },
        },
    )
