import json
import shutil
import subprocess
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import List, NamedTuple

CODE_TEMPLATE = """
#ifndef __faust2hpp_{class_name}_H__
#define __faust2hpp_{class_name}_H__

#include <cmath>

#define uscale(x, l, u) (x + 1.0f) / 2.0f * (u - l) + l;
#define ulscale(x, l, u) std::exp((x + 1.0f) / 2.0f * (std::log(u) - std::log(l)) + std::log(l));

#include "{class_name}Faust.h"

class {class_name}
{{
public:
  {class_name}()
  {{
    faustDsp.buildUserInterface(&faustDsp);
    {assign_pointers}
  }}

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

  {declare_pointers}

  void zeroParameters()
  {{
    {to_zero}
  }}
}};

#undef uscale
#undef ulscale

#endif
""".strip()

SOURCE_PATH = Path(__file__).parent / "Source"


@contextmanager
def remove_file_ctx(path: Path):
    yield
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def copy_sources(out_path: Path):
    """Copy the source headers to the output directory"""
    out_path = Path(out_path)
    shutil.copy(SOURCE_PATH / "Meta.h", out_path / "Meta.h")
    shutil.copy(SOURCE_PATH / "UI.h", out_path / "UI.h")
    shutil.copy(SOURCE_PATH / "FaustImpl.h", out_path / "FaustImpl.h")


def compile_faust(out_path: Path, dsp_path: Path, class_name: str) -> List[str]:
    """Compile the FAUST code into the C++ header"""
    faust_impl_path = str(SOURCE_PATH / "FaustImpl.h")
    output_json_path = out_path / f"{dsp_path.name}.json"

    with remove_file_ctx(output_json_path):
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

        with output_json_path.open("r") as fio:
            meta = json.load(fio)
        parameter_names = [i["label"] for i in meta["ui"][0]["items"]]

    return parameter_names


class ParameterInfo(NamedTuple):
    """Strings used to generate code for a parameter"""

    name: str
    setter: str
    declare_pointer: str
    assign_pointer: str
    to_zero: str


def build_parameters(
    parameter_names: List[str], info_path: Path
) -> List[ParameterInfo]:
    """Build the parameter infor for code generation"""
    if info_path is not None:
        with info_path.open("r") as fio:
            infos = json.load(fio)
    else:
        infos = {}

    extra_names = list(sorted(set(infos.keys()) - set(parameter_names)))
    if extra_names:
        warnings.warn("unused parameter names: {}".format(", ".join(extra_names)))

    parameters = list()

    for name in parameter_names:
        if info_path is not None and name not in infos:
            warnings.warn(f"no parameter info: {name}")

        transform = infos.get(name, {}).get("transform", "x")
        default = infos.get(name, {}).get("default", 0)

        setter = "\n  ".join(
            [
                f"inline void set_{name}(FAUSTFLOAT x)",
                "{",
                f"  x += {default:.6e}f;",
                f"  *par_{name} = {transform};",
                "}",
            ]
        )
        declare_pointer = f"FAUSTFLOAT* par_{name} = nullptr;"
        assign_pointer = f'par_{name} = faustDsp.getParameter("{name}");'
        to_zero = f"set_{name}(0.0f);"
        parameters.append(
            ParameterInfo(
                name=name,
                setter=setter,
                declare_pointer=declare_pointer,
                assign_pointer=assign_pointer,
                to_zero=to_zero,
            )
        )

    return parameters


def generte_code(parameter_info: List[ParameterInfo], out_path: Path, class_name: str):
    """Generate the standalone class header"""
    setters = [p.setter for p in parameter_info]
    to_zero = [p.to_zero for p in parameter_info]
    declare_pointers = [p.declare_pointer for p in parameter_info]
    assign_pointers = [p.assign_pointer for p in parameter_info]

    code_path = out_path / (class_name + ".h")

    with code_path.open("w") as fout:
        fout.write(
            CODE_TEMPLATE.format(
                class_name=class_name,
                setters="\n  ".join(setters),
                to_zero="\n    ".join(to_zero),
                declare_pointers="\n  ".join(declare_pointers),
                assign_pointers="\n    ".join(assign_pointers),
            )
        )
