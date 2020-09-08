import json
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import NamedTuple, List

CODE_TEMPLATE = \
"""
#ifndef __faust2hpp_{class_name}_H__
#define __faust2hpp_{class_name}_H__

#include <cmath>

#include "{class_name}Faust.h"

#define USCALE(x, l, u) (x + 1.0f) / 2.0f * (u - l) + l
#define ULSCALE(x, l, u) std::exp((x + 1.0f) / 2.0f * (std::log(u) - std::log(l)) + std::log(l))

class {class_name}
{{
public:
  {class_name}() = default;
  ~{class_name}() = default;

  void reset()
  {{
    faustDsp.instanceClear();
    zeroParameters();
  }}

  void prepare(int sampleRate)
  {{
    faustDsp.init(sampleRate);
    zeroParameters();
  }}

  void process(int count, FAUSTFLOAT** buffer)
  {{
    faustDsp.compute(count, buffer, buffer);
  }}

  {setters}

private:
  {class_name}Faust faustDsp;

  {pointers}

  void zeroParameters()
  {{
    {to_zero}
  }}
}};

#undef USCALE
#undef ULSCALE

#endif
""".strip()

SOURCE_PATH = Path(__file__).parent / "Source"


def copy_sources(out_path: Path):
    """Copy the source headers to the output directory"""
    out_path = Path(out_path)
    shutil.copy(SOURCE_PATH / "Meta.h", out_path / "Meta.h")
    shutil.copy(SOURCE_PATH / "UI.h", out_path / "UI.h")
    shutil.copy(SOURCE_PATH / "FaustImpl.h", out_path / "FaustImpl.h")


def compile_faust(out_path: Path, dsp_path: Path, class_name: str):
    """Compile the FAUST code into the C++ header"""
    faust_impl_path = str(SOURCE_PATH / "FaustImpl.h")
    command = (
        f"faust {str(dsp_path)} "
        f"-lang cpp -i -scal -inpl -ftz 2 -json "
        "-scn FaustImpl "
        f"-cn {class_name}Faust "
        f"-a {faust_impl_path} "
        f"-o {class_name}Faust.h "
        f"-O {str(out_path)}"
    )
    subprocess.check_call(command.split(" "))


class ParameterInfo(NamedTuple):
    """Strings used to generate code for a parameter"""
    name: str
    setter: str
    pointer: str
    to_zero: str


def build_parameters(compile_path: Path, dsp_path: Path, transforms_path: Path = None) -> List[ParameterInfo]:
    """Build the parameter infor for code generation"""
    compile_json = (compile_path / f"{dsp_path.name}.json")
    with compile_json.open("r") as fio:
        meta = json.load(fio)
    compile_json.unlink()

    if transforms_path is not None:
        with transforms_path.open("r") as fio:
            transforms = json.load(fio)
    else:
        transforms = {}

    parameter_names = [i["label"] for i in meta["ui"][0]["items"]]

    parameters = list()

    for name in parameter_names:
        transform = transforms.pop(name, "x")
        setter = f"void set_{name}(FAUSTFLOAT x) {{ *par_{name} = {transform}; }}"
        pointer = f"FAUSTFLOAT* par_{name} = faustDsp.getParameter(\"{name}\");"
        to_zero = f"set_{name}(0.0f);"
        parameters.append(ParameterInfo(
            name=name,
            setter=setter,
            pointer=pointer,
            to_zero=to_zero,
        ))

    unused_transforms = list(transforms.keys())
    if unused_transforms:
        warnings.warn("unused parameter transforms: {}".format(", ".join(unused_transforms)))

    return parameters


def generte_code(parameter_info: List[ParameterInfo], out_path: Path, class_name: str):
    """Generate the standalone class header"""
    setters = [p.setter for p in parameter_info]
    to_zero = [p.to_zero for p in parameter_info]
    pointers = [p.pointer for p in parameter_info]

    code_path = out_path / (class_name + ".h")

    with code_path.open("w") as fout:
        fout.write(CODE_TEMPLATE.format(
            class_name=class_name,
            setters="\n  ".join(setters),
            to_zero="\n    ".join(to_zero),
            pointers="\n  ".join(pointers),
        ))
