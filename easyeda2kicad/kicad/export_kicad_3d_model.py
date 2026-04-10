from easyeda2kicad.easyeda.parameters_easyeda import Ee3dModel


class Exporter3dModelKicad:
    def __init__(self, model_3d: Ee3dModel):
        self.input = model_3d
        self.output_step = model_3d.step if model_3d else None

    def export(self, output_dir: str) -> None:
        if self.output_step:
            with open(
                file=f"{output_dir}/{self.input.name}.step",
                mode="wb",
            ) as my_lib:
                my_lib.write(self.output_step)
