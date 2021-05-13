# faust2hpp

Convert [FAUST](https://faust.grame.fr/) code to a header-only standalone C++ library.
A collection of header files is generated as the output.
A class is provided from which a DSP object can be built with methods in the style of [JUCE](https://juce.com) DSP objects.

## Installation

From the project root:

```bash
pip install .
```

## Usage

The `faust2hpp` script will be made available in your path by the PIP installation.

```bash
faust2hpp --help
```

## Background

FAUST allows converting DSP code to a variety of formats, including standalone plugins.
However there doesn't seem to be a good option for integrating the resulting C++ code into a separate codebase.

FAUST does generate C++ code, but it relies on two classes which must be implemented: the `Meta` and the `UI` classes.
Moreover, the public interface provided by the resulting code consists of only: initialization, resetting and the compute loop.
There lacks the ability to modify the parameters of the DSP algorithm.

It could be possible to monkey patch some solution involving editing of the generated C++ code.
However this isn't a very robust option because a) the code is a private API, so to speak, and can easily change with different FAUST compilation parameters and b) editing C++ code without a full parse is dangerous.

The generated code can provide a public API to the parameters: the parameters exposed by the UI get linked to their UI name.

The idea behind this package then is to create an implementation of the `UI` class which simply allows access to those public names.
Then, the resulting FAUST class has public access to its parameters.
Moreover, that object is wrapped in a new class which follows the JUCE conventions for DSP objects, and provides getters and setters directly to the variable memory.

## TODO

* Don't silently fail in the `setParameter` method when the name isn't in the map
* Don't copy the `FaustImpl.h` header in the FAUST generated code.
* Create a single hader mode
* Add documentation to the script
