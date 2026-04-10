# EasyEDA / LCSC Part Importer for KiCad

A KiCad PCB Editor plugin for importing parts from the LCSC library into your project, based on the [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py) tool.

The plugin now ships with its Python dependencies bundled, so users do not need to run `pip install` manually.

### Key Features
- **Seamless Import**: Quickly import LCSC parts by entering their part number.
- **Direct Access**: Integrated into the toolbar in the KiCad PCB Editor.
  
![Toolbar Screenshot](https://github.com/user-attachments/assets/d925aedc-483a-429f-ae3e-cf4fea454317)

### How It Works
1. **Enter LCSC Part Number**: Type in the LCSC part number to import its symbol, footprint, and 3D model directly into KiCad.

![Import Menu Screenshot](https://github.com/user-attachments/assets/8438877e-8ba5-46f7-bc8d-0552915c4243)

2. **Auto-Save**: Imported parts are stored in the current KiCad project directory as `<projectname>.kicad_sym`, `<projectname>.pretty`, and `3dshapes/`.
   On KiCad 10, the plugin stores STEP 3D models only.

---

## Installation

1. **Download or clone this repo**
   A release zip is the easiest option if one is available.

2. **Copy these 3 items into KiCad's plugins folder**
   - `LCSC Importer.py`
   - `easyeda2kicad/`
   - `vendor/`

3. **Use the correct KiCad plugins folder**
   - Windows: `%APPDATA%/kicad/<version>/scripting/plugins`
   - macOS: `~/Library/Preferences/kicad/<version>/scripting/plugins`
   - Linux: `~/.local/share/kicad/<version>/scripting/plugins`

4. **Restart KiCad and open the PCB Editor**
   The button appears in the PCB Editor toolbar. It does not appear in the Schematic Editor.

No separate `pip install` step is required.

## Usage

1. **Save your project and board first**
   The plugin uses the current board file to find the project folder.

2. **Run the plugin from the PCB Editor toolbar**
   Enter an LCSC part number such as `C2040`.

3. **The plugin writes files into your project**
   - Symbol library: `<projectname>.kicad_sym`
   - Footprint library: `<projectname>.pretty/`
   - 3D models: `3dshapes/` with `.step` files

4. **Add the symbol and footprint libraries to the project**
   - Symbol library: `${KIPRJMOD}/<projectname>.kicad_sym`
   - Footprint library: `${KIPRJMOD}/<projectname>.pretty`

3D model paths are referenced automatically from `${KIPRJMOD}/3dshapes` using STEP models.

## Packaging

If you publish releases for other users, run `python3 package_release.py`. It creates `dist/easyeda2kicad_plugin.zip` with the flat layout users can extract directly into KiCad's plugins directory.

---

This plugin is aimed at KiCad 10 style project-local libraries and STEP-based 3D models.
