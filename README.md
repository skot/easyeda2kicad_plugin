# EasyEda / LCSC Part Importer for KiCad!

A KiCad plugin that allows you to easily import parts (symbols, footprints, and 3D models) from the LCSC library directly into KiCad, based on the [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py) command line tool.

### Key Features
- **Seamless Import**: Quickly import LCSC parts by entering their part number.
- **Direct Access**: Integrated into the toolbar for easy access within the PCB editor.
  
![Toolbar Screenshot](https://github.com/user-attachments/assets/d925aedc-483a-429f-ae3e-cf4fea454317)

### How It Works
1. **Enter LCSC Part Number**: Type in the LCSC part number to import its symbol, footprint, and 3D model directly into KiCad.

![Import Menu Screenshot](https://github.com/user-attachments/assets/8438877e-8ba5-46f7-bc8d-0552915c4243)

2. **Auto-Save**: Imported parts are stored in the current KiCad project directory as `easyeda2kicad.kicad_sym`, `easyeda2kicad.pretty`, and `easyeda2kicad.3dshapes`.

---

## Installation

1. **Clone the Repository**  
   Clone this repository to your downloads folder.

2. **Move Files to KiCad Plugin Folder**  
   Move all contents to your KiCad plugins directory:  
   Windows: `KiCad/(version)/scripting/plugins`\
   Macos: `/Users/[USER]/Documents/KiCad/[x.x]/scripting/plugins`

3. **Install dependencies (Macos)**  
   Install Pydantic dependency on Macos execute: 
   `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/pip3.9 install pydantic`

5. **Organize the Files**  
   Ensure `LCSC Importer.py` is not inside any subfolder.

6. **Install dependencies**  
   When you first launch KiCad, you may be missing one or more dependencies to run the plugin. Install these using pip.
   On Windows you may have to install them through the _KiCad Command Promt_ found in programs/KiCadX/.

7. **Run the plugin**  
   Once all dependencies are installed, save your KiCad project and board, then run the plugin by clicking the LCSC icon in the top menu bar in the PCB editor.
   The plugin will generate the required project-local libraries inside the current project folder.

8. **Add libraries in KiCad**  
   Lastly, tell KiCad where to find the parts you import for this project:
    - Go to Preferences > Manage Symbol Libraries, and add the project library `easyeda2kicad` from `${KIPRJMOD}/easyeda2kicad.kicad_sym`
    - Go to Preferences > Manage Footprint Libraries, and add the project library `easyeda2kicad` from `${KIPRJMOD}/easyeda2kicad.pretty`

---

Enjoy simplified part importing from LCSC directly into your KiCad designs!
