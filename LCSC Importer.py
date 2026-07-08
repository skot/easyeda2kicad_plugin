import pcbnew
import wx
import os
import sys
import logging

plugin_dir = os.path.dirname(__file__)
vendor_path = os.path.join(plugin_dir, "vendor")
easyeda_path = os.path.join(plugin_dir, "easyeda2kicad")

for path in [vendor_path, easyeda_path]:
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

# Configure logging
log_file = os.path.join(plugin_dir, "lcsc_importer.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("LCSC Part Importer Plugin initialized")


class ImportOptionsDialog(wx.Dialog):
    def __init__(self, parent=None, defaults=None):
        super().__init__(parent, title="LCSC Part Importer")
        defaults = defaults or {}

        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        panel_sizer.Add(
            wx.StaticText(panel, label="Enter LCSC Part Number:"),
            0,
            wx.ALL,
            10,
        )

        self.part_number_ctrl = wx.TextCtrl(panel)
        panel_sizer.Add(
            self.part_number_ctrl,
            0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            10,
        )

        self.symbol_checkbox, self.symbol_path_ctrl = self._add_path_row(
            panel,
            panel_sizer,
            "Symbol",
            defaults.get("symbol_path", ""),
            self._browse_symbol_library,
        )
        self.footprint_checkbox, self.footprint_path_ctrl = self._add_path_row(
            panel,
            panel_sizer,
            "Footprint",
            defaults.get("footprint_path", ""),
            self._browse_directory,
        )
        self.model_checkbox, self.model_path_ctrl = self._add_path_row(
            panel,
            panel_sizer,
            "3D Model",
            defaults.get("model_path", ""),
            self._browse_directory,
        )

        panel.SetSizer(panel_sizer)

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 0)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if button_sizer:
            dialog_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(dialog_sizer)
        self.SetSize((760, 360))
        self.SetMinSize((640, 340))
        self.CentreOnParent()
        self.part_number_ctrl.SetFocus()

    def _add_path_row(self, panel, panel_sizer, label, default_path, browse_handler):
        checkbox = wx.CheckBox(panel, label=label)
        checkbox.SetValue(True)

        path_ctrl = wx.TextCtrl(panel, value=default_path)
        browse_button = wx.Button(panel, label="Browse...")
        browse_button.Bind(wx.EVT_BUTTON, lambda event: browse_handler(path_ctrl))

        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        row_sizer.Add(checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row_sizer.Add(path_ctrl, 1, wx.RIGHT | wx.EXPAND, 8)
        row_sizer.Add(browse_button, 0)
        panel_sizer.Add(row_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        checkbox.Bind(
            wx.EVT_CHECKBOX,
            lambda event: self._set_path_row_enabled(
                checkbox,
                path_ctrl,
                browse_button,
            ),
        )
        self._set_path_row_enabled(checkbox, path_ctrl, browse_button)
        return checkbox, path_ctrl

    def _set_path_row_enabled(self, checkbox, path_ctrl, browse_button):
        enabled = checkbox.GetValue()
        path_ctrl.Enable(enabled)
        browse_button.Enable(enabled)

    def _browse_symbol_library(self, path_ctrl):
        current_path = path_ctrl.GetValue().strip()
        current_dir = os.path.dirname(current_path) if current_path else ""
        current_file = os.path.basename(current_path) if current_path else ""
        with wx.FileDialog(
            self,
            "Choose symbol library",
            defaultDir=current_dir,
            defaultFile=current_file,
            wildcard="KiCad symbol libraries (*.kicad_sym)|*.kicad_sym",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path_ctrl.SetValue(file_dialog.GetPath())

    def _browse_directory(self, path_ctrl):
        current_path = path_ctrl.GetValue().strip()
        with wx.DirDialog(
            self,
            "Choose folder",
            defaultPath=current_path,
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                path_ctrl.SetValue(dir_dialog.GetPath())

    def get_values(self):
        return {
            "part_number": self.part_number_ctrl.GetValue().strip(),
            "symbol": self.symbol_checkbox.GetValue(),
            "footprint": self.footprint_checkbox.GetValue(),
            "3d": self.model_checkbox.GetValue(),
            "symbol_path": self.symbol_path_ctrl.GetValue().strip(),
            "footprint_path": self.footprint_path_ctrl.GetValue().strip(),
            "model_path": self.model_path_ctrl.GetValue().strip(),
        }

# Check for bundled dependencies and alert user if anything is missing
def check_dependencies():
    missing_dependencies = []
    try:
        import pydantic
    except ImportError:
        missing_dependencies.append("pydantic")

    try:
        import requests
    except ImportError:
        missing_dependencies.append("requests")

    if missing_dependencies:
        missing_deps_str = ", ".join(missing_dependencies)
        message = (
            f"The plugin bundle is missing required Python packages: {missing_deps_str}.\n"
            "Reinstall the plugin and make sure the bundled `vendor` folder is present."
        )
        logging.warning(message)
        wx.MessageBox(message, "Missing Dependencies", style=wx.ICON_WARNING)
        raise ImportError(f"Missing dependencies: {missing_deps_str}")

# Run the dependency check
try:
    check_dependencies()
except ImportError as e:
    logging.error(f"Dependency check failed: {e}")
    raise e  # Stop execution if dependencies are missing

try:
    from easyeda2kicad.__main__ import main  # import the main function from easyeda2kicad
    from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
    from easyeda2kicad.easyeda.easyeda_importer import (
        Easyeda3dModelImporter,
        EasyedaFootprintImporter,
        EasyedaSymbolImporter,
    )
    from easyeda2kicad.helpers import id_already_in_symbol_lib
    from easyeda2kicad.kicad.parameters_kicad_symbol import KicadVersion
    logging.info("Imported easyeda2kicad successfully")
except Exception as e:
    logging.error(f"Failed to import easyeda2kicad: {e}")
    wx.MessageBox(f"Error loading easyeda2kicad:\n{e}", "Import Error", style=wx.ICON_ERROR)
    raise e  # Stop execution if import fails

class EasyEDAImporterPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "LCSC Part Importer"
        self.category = "Utility"
        self.description = "Import a part from LCSC to KiCad using easyeda2kicad"
        self.show_toolbar_button = True  # optional, defaults to False
        self.icon_file_name = os.path.join(easyeda_path, "lcsc_logo.png")
        logging.info("Plugin defaults set")

    def _get_default_outputs(self):
        board = pcbnew.GetBoard()
        board_file = board.GetFileName() if board else ""

        if not board_file:
            raise RuntimeError(
                "Save the current board first so the importer can use the project directory."
            )

        project_dir = os.path.dirname(os.path.abspath(board_file))
        project_name = os.path.splitext(os.path.basename(board_file))[0]
        return {
            "project_dir": project_dir,
            "symbol_path": os.path.join(project_dir, f"{project_name}.kicad_sym"),
            "footprint_path": os.path.join(project_dir, f"{project_name}.pretty"),
            "model_path": os.path.join(project_dir, "3d"),
        }

    def _build_success_message(self, cad_data, selected):
        lines = ["Part imported successfully.", ""]

        if selected["symbol"]:
            symbol_name = EasyedaSymbolImporter(cad_data).get_symbol().info.name
            lines.append(f"Symbol: {symbol_name}")
            lines.append(f"  {selected['symbol_path']}")

        if selected["footprint"]:
            footprint_name = EasyedaFootprintImporter(cad_data).get_footprint().info.name
            lines.append(f"Footprint: {footprint_name}.kicad_mod")
            lines.append(f"  {selected['footprint_path']}")

        if selected["3d"]:
            model = Easyeda3dModelImporter(cad_data, False).output
            if model:
                lines.append(f"3D model: {model.name}.step")
                lines.append(f"  {selected['model_path']}")
            else:
                lines.append("3D model: none available")

        return "\n".join(lines)

    def _validate_output_paths(self, selected):
        if selected["symbol"]:
            symbol_path = selected["symbol_path"]
            if not symbol_path:
                raise RuntimeError("Choose a symbol library path.")
            if not symbol_path.endswith(".kicad_sym"):
                raise RuntimeError("The symbol library must be a .kicad_sym file.")
            symbol_dir = os.path.dirname(os.path.abspath(symbol_path))
            if not os.path.isdir(symbol_dir):
                raise RuntimeError(f"The symbol library folder does not exist:\n{symbol_dir}")

        if selected["symbol"] or selected["footprint"]:
            footprint_path = selected["footprint_path"]
            if not footprint_path:
                raise RuntimeError("Choose a footprint library folder.")
            if not footprint_path.endswith(".pretty"):
                raise RuntimeError("The footprint library folder must end with .pretty.")

        if selected["footprint"] or selected["3d"]:
            model_path = selected["model_path"]
            if not model_path:
                raise RuntimeError("Choose a 3D model folder.")

    def _validate_requested_items(self, part_number, cad_data, selected):
        if selected["symbol"]:
            try:
                EasyedaSymbolImporter(cad_data).get_symbol()
            except Exception as exc:
                raise RuntimeError(
                    f"LCSC part {part_number} does not have a symbol available."
                ) from exc

        if selected["footprint"]:
            try:
                EasyedaFootprintImporter(cad_data).get_footprint()
            except Exception as exc:
                raise RuntimeError(
                    f"LCSC part {part_number} does not have a footprint available."
                ) from exc

        if selected["3d"]:
            model = Easyeda3dModelImporter(cad_data, False).output
            if not model:
                raise RuntimeError(
                    f"LCSC part {part_number} does not have a 3D model available."
                )

    def _get_conflicts(self, cad_data, selected):
        conflicts = []

        if selected["symbol"]:
            symbol_name = EasyedaSymbolImporter(cad_data).get_symbol().info.name
            output_path = selected["symbol_path"]
            if os.path.isfile(output_path) and id_already_in_symbol_lib(
                lib_path=output_path,
                component_name=symbol_name,
                kicad_version=KicadVersion.v6,
            ):
                conflicts.append(f"Symbol: {symbol_name}")

        if selected["footprint"]:
            footprint_name = EasyedaFootprintImporter(cad_data).get_footprint().info.name
            footprint_path = os.path.join(
                selected["footprint_path"],
                f"{footprint_name}.kicad_mod",
            )
            if os.path.isfile(footprint_path):
                conflicts.append(f"Footprint: {footprint_name}.kicad_mod")

        if selected["3d"]:
            model = Easyeda3dModelImporter(cad_data, False).output
            if model:
                model_path = os.path.join(selected["model_path"], f"{model.name}.step")
                if os.path.isfile(model_path):
                    conflicts.append(f"3D model: {model.name}.step")

        return conflicts

    def _confirm_overwrite(self, conflicts):
        if not conflicts:
            return False, True

        message = "The following files or symbols already exist:\n\n"
        message += "\n".join(conflicts)
        message += "\n\nDo you want to overwrite them?"

        overwrite = wx.MessageBox(
            message,
            "Confirm Overwrite",
            style=wx.YES_NO | wx.ICON_WARNING,
        )
        return True, overwrite == wx.YES

    def _model_path_for_footprint(self, project_dir, model_path):
        model_path = os.path.abspath(model_path)
        try:
            relative_path = os.path.relpath(model_path, project_dir)
        except ValueError:
            return model_path.replace("\\", "/")

        if relative_path == ".":
            return "${KIPRJMOD}"
        if not relative_path.startswith(".."):
            return "${KIPRJMOD}/" + relative_path.replace("\\", "/")
        return model_path.replace("\\", "/")

    def Run(self):
        logging.info("Run method started")
        try:
            default_outputs = self._get_default_outputs()
        except Exception as e:
            wx.MessageBox(str(e), "Project Required", style=wx.ICON_WARNING)
            logging.error(f"Could not determine default output paths: {e}")
            return

        dialog = ImportOptionsDialog(None, default_outputs)
        
        if dialog.ShowModal() == wx.ID_OK:
            values = dialog.get_values()
            part_number = values["part_number"]
            logging.info(f"User entered part number: {part_number}")

            if not part_number:
                wx.MessageBox(
                    "Enter an LCSC part number before importing.",
                    "Missing Part Number",
                    style=wx.ICON_WARNING,
                )
                dialog.Destroy()
                logging.info("Dialog closed")
                return

            if not any([values["symbol"], values["footprint"], values["3d"]]):
                wx.MessageBox(
                    "Select at least one of Symbol, Footprint, or 3D Model.",
                    "Nothing Selected",
                    style=wx.ICON_WARNING,
                )
                dialog.Destroy()
                logging.info("Dialog closed")
                return

            try:
                self._validate_output_paths(values)
            except Exception as e:
                wx.MessageBox(str(e), "Invalid Output Path", style=wx.ICON_WARNING)
                dialog.Destroy()
                logging.info("Dialog closed")
                return
            
            # Run easyeda2kicad's main function with the part number
            try:
                api = EasyedaApi()
                cad_data = api.get_cad_data_of_component(part_number)
                if not cad_data:
                    detail = api.last_error_message or "No importable EasyEDA data was found."
                    raise RuntimeError(
                        f"LCSC part {part_number} could not be imported.\n"
                        f"Reason: {detail}\n\n"
                        "This usually means the part does not have EasyEDA symbol, "
                        "footprint, or 3D model data available."
                    )

                self._validate_requested_items(part_number, cad_data, values)

                had_conflicts, should_continue = self._confirm_overwrite(
                    self._get_conflicts(cad_data, values)
                )
                if not should_continue:
                    logging.info("Import canceled by user due to existing files")
                    return

                model_path_prefix = self._model_path_for_footprint(
                    default_outputs["project_dir"],
                    values["model_path"],
                )
                footprint_lib_name = os.path.basename(values["footprint_path"])
                if footprint_lib_name.endswith(".pretty"):
                    footprint_lib_name = footprint_lib_name[:-7]
                arguments = [
                    f"--lcsc_id={part_number}",
                    f"--output={values['symbol_path']}",
                    f"--footprint-output={values['footprint_path']}",
                    f"--model-output={values['model_path']}",
                    f"--model-path={model_path_prefix}",
                    f"--footprint-lib-name={footprint_lib_name}",
                ]
                if values["symbol"]:
                    arguments.append("--symbol")
                if values["footprint"]:
                    arguments.append("--footprint")
                if values["3d"]:
                    arguments.append("--3d")
                if had_conflicts:
                    arguments.append("--overwrite")

                result = main(
                    arguments
                )
                if result != 0:
                    raise RuntimeError(
                        "easyeda2kicad reported an error. Check the log for details."
                    )
                logging.info(f"Part imported successfully: {result}")
                wx.MessageBox(
                    self._build_success_message(cad_data, values),
                    "Success",
                )
            except Exception as e:
                error_message = f"Error importing part:\n{e}"
                logging.error(error_message)
                wx.MessageBox(error_message, "Execution Error", style=wx.ICON_ERROR)
        else:
            logging.info("Dialog was canceled by the user")
        
        dialog.Destroy()
        logging.info("Dialog closed")

# Register the plugin with KiCad
EasyEDAImporterPlugin().register()
logging.info("LCSC Part Importer Plugin registered")
