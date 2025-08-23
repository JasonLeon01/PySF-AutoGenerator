#pragma once

#include "SFML/Graphics/Rect.hpp"
#include "A_utils.hpp"
namespace py = pybind11;

template <typename T>
void bind_RectT(py::module &m_sf, const std::string& name) {
    auto v_sfRect = py::class_<sf::Rect<T>>(m_sf, name.c_str());
    v_sfRect.def(py::init<>());
    v_sfRect.def(py::init<>([](sf::Vector2<T> position, sf::Vector2<T> size) { return sf::Rect<T>(position, size); }), py::arg("position"), py::arg("size"));
    v_sfRect.def("contains", [](sf::Rect<T>& self, sf::Vector2<T> point) { return self.contains(point); }, py::arg("point"));
    v_sfRect.def("findIntersection", [](sf::Rect<T>& self, sf::Rect<T> rectangle) { return self.findIntersection(rectangle); }, py::arg("rectangle"));
    v_sfRect.def("getCenter", [](sf::Rect<T>& self) { return self.getCenter(); });
    v_sfRect.def_readwrite("position", &sf::Rect<T>::position);
    v_sfRect.def_readwrite("size", &sf::Rect<T>::size);
    v_sfRect.def("__eq__", [](sf::Rect<T>& self, sf::Rect<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfRect.def("__ne__", [](sf::Rect<T>& self, sf::Rect<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
}

void C_bind_Rect(py::module &m_sf);
