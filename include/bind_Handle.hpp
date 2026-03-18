#pragma once

#include "SFML/Window/WindowHandle.hpp"
#include "utils.hpp"
namespace py = pybind11;


void bind_Handle(py::module &m_sf);
