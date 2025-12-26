#pragma once

#include "SFML/Graphics/Rect.hpp"
#include "A_utils.hpp"
namespace py = pybind11;

template <typename T>
void bind_RectT(py::module &m_sf, const std::string& name) {
    auto v_sfRect = py::class_<sf::Rect<T>>(m_sf, name.c_str());
    v_sfRect.def(py::init<>());
    v_sfRect.def(py::init<>([](sf::Vector2<T> position, sf::Vector2<T> size) { return new sf::Rect<T>(position, size); }), py::arg("position"), py::arg("size"));
    v_sfRect.def("asCapsule", [](sf::Rect<T>& self) { return py::capsule(&self, typeid(sf::Rect<T>).name()); }, py::return_value_policy::reference_internal);
    v_sfRect.def("contains", [](sf::Rect<T>& self, sf::Vector2<T> point) { return self.contains(point); }, py::arg("point"));
    v_sfRect.def("findIntersection", [](sf::Rect<T>& self, sf::Rect<T> rectangle) { return self.findIntersection(rectangle); }, py::arg("rectangle"));
    v_sfRect.def("getCenter", [](sf::Rect<T>& self) { return self.getCenter(); });
    v_sfRect.def_readwrite("position", &sf::Rect<T>::position);
    v_sfRect.def_readwrite("size", &sf::Rect<T>::size);
    v_sfRect.def("__eq__", [](sf::Rect<T>& self, sf::Rect<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfRect.def("__ne__", [](sf::Rect<T>& self, sf::Rect<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
    v_sfRect.def("__hash__", [](sf::Rect<T>& self) { std::size_t seed = 0; hash_combine(seed, self.position.x); hash_combine(seed, self.position.y); hash_combine(seed, self.size.x); hash_combine(seed, self.size.y); return seed; });
    v_sfRect.def("__repr__", [](sf::Rect<T>& self) {
        std::stringstream ss;
        ss << "Rect(" << self.position.x << ", " << self.position.y << ", " << self.size.x << ", " << self.size.y << ")";
        return ss.str();
    });
    add_copy_support(v_sfRect);
}

void C_bind_Rect(py::module &m_sf);
