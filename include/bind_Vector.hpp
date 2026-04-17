#pragma once

#include "utils.hpp"
#include <string>
#include <vector>

namespace py = pybind11;

std::string getVectorDesc(int dimension);

std::string getVectorConstructDesc(int dimension);

std::string getVectorConstructDescWithParams(int dimension);

template <typename T>
void bind_VectorTCommon(py::class_<T>& v_sfVector, int dimension);

template <typename T>
void bind_Vector2T_Common(py::class_<sf::Vector2<T>>& v_sfVector2, const std::string& name);

template <typename T>
void bind_Vector3T_Common(py::class_<sf::Vector3<T>>& v_sfVector3, const std::string& name);

template <typename T>
void bind_Vector2T(py::module &m_sf, const std::string& name);

template <typename T>
void bind_Vector3T(py::module &m_sf, const std::string& name);

template <typename T>
void bind_Vector4T(py::module &m_sf, const std::string& name);

void bind_Vector(py::module &m_sf);

#include "bind_Vector.inl"
