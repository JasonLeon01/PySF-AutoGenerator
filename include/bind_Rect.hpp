#pragma once

#include "utils.hpp"
#include <string>

namespace py = pybind11;

template <typename T>
void bind_RectT(py::module &m_sf, const std::string& name);

void bind_Rect(py::module &m_sf);

#include "bind_Rect.inl"
