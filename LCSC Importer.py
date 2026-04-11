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
    def __init__(self, parent=None):
        super().__init__(parent, title="LCSC Part Importer")

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

        self.symbol_checkbox = wx.CheckBox(panel, label="Symbol")
        self.footprint_checkbox = wx.CheckBox(panel, label="Footprint")
        self.model_checkbox = wx.CheckBox(panel, label="3D Model")

        for checkbox in [
            self.symbol_checkbox,
            self.footprint_checkbox,
            self.model_checkbox,
        ]:
            checkbox.SetValue(True)
            panel_sizer.Add(checkbox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(panel_sizer)

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 0)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if button_sizer:
            dialog_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(dialog_sizer)
        self.SetSize((420, 260))
        self.SetMinSize((420, 260))
        self.CentreOnParent()
        self.part_number_ctrl.SetFocus()

    def get_values(self):
        return {
            "part_number": self.part_number_ctrl.GetValue().strip(),
            "symbol": self.symbol_checkbox.GetValue(),
            "footprint": self.footprint_checkbox.GetValue(),
            "3d": self.model_checkbox.GetValue(),
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

    def _get_project_library_output(self):
        board = pcbnew.GetBoard()
        board_file = board.GetFileName() if board else ""

        if not board_file:
            raise RuntimeError(
                "Save the current board first so the importer can use the project directory."
            )

        project_dir = os.path.dirname(os.path.abspath(board_file))
        project_name = os.path.splitext(os.path.basename(board_file))[0]
        return project_dir, os.path.join(project_dir, f"{project_name}.kicad_sym")

    def _build_success_message(self, project_dir, cad_data, selected):
        lines = ["Part imported successfully.", ""]

        if selected["symbol"]:
            symbol_name = EasyedaSymbolImporter(cad_data).get_symbol().info.name
            lines.append(f"Symbol: {symbol_name}")

        if selected["footprint"]:
            footprint_name = EasyedaFootprintImporter(cad_data).get_footprint().info.name
            lines.append(f"Footprint: {footprint_name}.kicad_mod")

        if selected["3d"]:
            model = Easyeda3dModelImporter(cad_data, False).output
            if model:
                lines.append(f"3D model: {model.name}.step")
            else:
                lines.append("3D model: none available")

        lines.extend(["", "Saved to:", project_dir])
        return "\n".join(lines)

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

    def _get_conflicts(self, project_dir, output_path, cad_data, selected):
        conflicts = []

        if selected["symbol"]:
            symbol_name = EasyedaSymbolImporter(cad_data).get_symbol().info.name
            if os.path.isfile(output_path) and id_already_in_symbol_lib(
                lib_path=output_path,
                component_name=symbol_name,
                kicad_version=KicadVersion.v6,
            ):
                conflicts.append(f"Symbol: {symbol_name}")

        if selected["footprint"]:
            footprint_name = EasyedaFootprintImporter(cad_data).get_footprint().info.name
            footprint_path = os.path.join(
                project_dir,
                f"{os.path.splitext(os.path.basename(output_path))[0]}.pretty",
                f"{footprint_name}.kicad_mod",
            )
            if os.path.isfile(footprint_path):
                conflicts.append(f"Footprint: {footprint_name}.kicad_mod")

        if selected["3d"]:
            model = Easyeda3dModelImporter(cad_data, False).output
            if model:
                model_path = os.path.join(project_dir, "3dshapes", f"{model.name}.step")
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

    def Run(self):
        logging.info("Run method started")
        dialog = ImportOptionsDialog(None)
        
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

                project_dir, output_path = self._get_project_library_output()
                had_conflicts, should_continue = self._confirm_overwrite(
                    self._get_conflicts(project_dir, output_path, cad_data, values)
                )
                if not should_continue:
                    logging.info("Import canceled by user due to existing files")
                    return

                arguments = [f"--lcsc_id={part_number}", f"--output={output_path}"]
                if values["symbol"]:
                    arguments.append("--symbol")
                if values["footprint"]:
                    arguments.append("--footprint")
                if values["3d"]:
                    arguments.append("--3d")
                if values["footprint"] or values["3d"]:
                    arguments.append("--project-relative")
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
                    self._build_success_message(project_dir, cad_data, values),
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
