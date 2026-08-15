#include <pybind11/pybind11.h>
#include <string>

std::string hello() {
    return "Hello from C++!";
}

PYBIND11_MODULE(_core, m) {
    m.doc() = "AlphaForge C++ core";
    m.def("hello", &hello);
}