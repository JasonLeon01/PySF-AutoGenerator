#pragma once

#include "utils.hpp"
#include <string>

namespace py = pybind11;

template <int N>
void bind_MatrixT(py::module &m_sf, const std::string& name);

void bind_Matrix(py::module &m_sf);

#include "bind_Matrix.inl"
