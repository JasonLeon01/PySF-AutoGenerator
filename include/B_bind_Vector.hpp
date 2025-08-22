#pragma once

#include "SFML/System/Vector2.hpp"
#include "SFML/System/Vector3.hpp"
#include "SFML/Graphics/Glsl.hpp"
#include "A_utils.hpp"
namespace py = pybind11;

template <typename T>
void bind_Vector2T(py::module &m, const std::string& name) {
    py::module m_sf = m.def_submodule("sf");
    auto v_sfVector2 = py::class_<sf::Vector2<T>>(m_sf, name.c_str());
    v_sfVector2.def(py::init<>());
    v_sfVector2.def(py::init<>([](T x, T y) { return sf::Vector2<T>(x, y); }), py::arg("x"), py::arg("y"));
    v_sfVector2.def("lengthSquared", [](sf::Vector2<T>& self) { return self.lengthSquared(); });
    v_sfVector2.def("perpendicular", [](sf::Vector2<T>& self) { return self.perpendicular(); });
    v_sfVector2.def("dot", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.dot(rhs); }, py::arg("rhs"));
    v_sfVector2.def("cross", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.cross(rhs); }, py::arg("rhs"));
    v_sfVector2.def("componentWiseMul", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.componentWiseMul(rhs); }, py::arg("rhs"));
    v_sfVector2.def("componentWiseDiv", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.componentWiseDiv(rhs); }, py::arg("rhs"));
    v_sfVector2.def_readwrite("x", &sf::Vector2<T>::x);
    v_sfVector2.def_readwrite("y", &sf::Vector2<T>::y);
    v_sfVector2.def("__neg__", [](sf::Vector2<T>& self) { return -self; });
    v_sfVector2.def("__iadd__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self += right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__isub__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self -= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__add__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self + right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__sub__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self - right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__mul__", [](sf::Vector2<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__imul__", [](sf::Vector2<T>& self, T right) { return self *= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__truediv__", [](sf::Vector2<T>& self, T right) { return self / right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__itruediv__", [](sf::Vector2<T>& self, T right) { return self /= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__eq__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__ne__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
}

template <typename T>
void bind_Vector2T_Explicit_Template(py::module &m, const std::string& name) {
    py::module m_sf = m.def_submodule("sf");
    auto v_sfVector2 = py::class_<sf::Vector2<T>>(m_sf, name.c_str());
    v_sfVector2.def(py::init<>());
    v_sfVector2.def(py::init<>([](T x, T y) { return sf::Vector2<T>(x, y); }), py::arg("x"), py::arg("y"));
    v_sfVector2.def(py::init<>([](T r, sf::Angle phi) { return sf::Vector2<T>(r, phi); }), py::arg("r"), py::arg("phi"));
    v_sfVector2.def("length", [](sf::Vector2<T>& self) { return self.length(); });
    v_sfVector2.def("normalized", [](sf::Vector2<T>& self) { return self.normalized(); });
    v_sfVector2.def("angleTo", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.angleTo(rhs); }, py::arg("rhs"));
    v_sfVector2.def("angle", [](sf::Vector2<T>& self) { return self.angle(); });
    v_sfVector2.def("rotatedBy", [](sf::Vector2<T>& self, sf::Angle phi) { return self.rotatedBy(phi); }, py::arg("phi"));
    v_sfVector2.def("projectedOnto", [](sf::Vector2<T>& self, sf::Vector2<T> axis) { return self.projectedOnto(axis); }, py::arg("axis"));
    v_sfVector2.def("lengthSquared", [](sf::Vector2<T>& self) { return self.lengthSquared(); });
    v_sfVector2.def("perpendicular", [](sf::Vector2<T>& self) { return self.perpendicular(); });
    v_sfVector2.def("dot", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.dot(rhs); }, py::arg("rhs"));
    v_sfVector2.def("cross", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.cross(rhs); }, py::arg("rhs"));
    v_sfVector2.def("componentWiseMul", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.componentWiseMul(rhs); }, py::arg("rhs"));
    v_sfVector2.def("componentWiseDiv", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.componentWiseDiv(rhs); }, py::arg("rhs"));
    v_sfVector2.def_readwrite("x", &sf::Vector2<T>::x);
    v_sfVector2.def_readwrite("y", &sf::Vector2<T>::y);
    v_sfVector2.def("__neg__", [](sf::Vector2<T>& self) { return -self; });
    v_sfVector2.def("__iadd__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self += right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__isub__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self -= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__add__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self + right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__sub__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self - right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__mul__", [](sf::Vector2<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__imul__", [](sf::Vector2<T>& self, T right) { return self *= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__truediv__", [](sf::Vector2<T>& self, T right) { return self / right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__itruediv__", [](sf::Vector2<T>& self, T right) { return self /= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__eq__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__ne__", [](sf::Vector2<T>& self, sf::Vector2<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
}

template <typename T>
void bind_Vector3T(py::module &m, const std::string& name) {
    py::module m_sf = m.def_submodule("sf");
    auto v_sfVector3 = py::class_<sf::Vector3<T>>(m_sf, name.c_str());
    v_sfVector3.def(py::init<>());
    v_sfVector3.def(py::init<>([](T x, T y, T z) { return sf::Vector3<T>(x, y, z); }), py::arg("x"), py::arg("y"), py::arg("z"));
    v_sfVector3.def("lengthSquared", [](sf::Vector3<T>& self) { return self.lengthSquared(); });
    v_sfVector3.def("dot", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.dot(rhs); }, py::arg("rhs"));
    v_sfVector3.def("cross", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.cross(rhs); }, py::arg("rhs"));
    v_sfVector3.def("componentWiseMul", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.componentWiseMul(rhs); }, py::arg("rhs"));
    v_sfVector3.def("componentWiseDiv", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.componentWiseDiv(rhs); }, py::arg("rhs"));
    v_sfVector3.def_readwrite("x", &sf::Vector3<T>::x);
    v_sfVector3.def_readwrite("y", &sf::Vector3<T>::y);
    v_sfVector3.def_readwrite("z", &sf::Vector3<T>::z);
    v_sfVector3.def("__neg__", [](sf::Vector3<T>& self) { return -self; });
    v_sfVector3.def("__iadd__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self += right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__isub__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self -= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__add__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self + right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__sub__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self - right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__mul__", [](sf::Vector3<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__imul__", [](sf::Vector3<T>& self, T right) { return self *= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__truediv__", [](sf::Vector3<T>& self, T right) { return self / right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__itruediv__", [](sf::Vector3<T>& self, T right) { return self /= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__eq__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__ne__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
}
template <typename T>
void bind_Vector3T_Explicit_Template(py::module &m, const std::string& name) {
    py::module m_sf = m.def_submodule("sf");
    auto v_sfVector3 = py::class_<sf::Vector3<T>>(m_sf, name.c_str());
    v_sfVector3.def(py::init<>());
    v_sfVector3.def(py::init<>([](T x, T y, T z) { return sf::Vector3<T>(x, y, z); }), py::arg("x"), py::arg("y"), py::arg("z"));
    v_sfVector3.def("length", [](sf::Vector3<T>& self) { return self.length(); });
    v_sfVector3.def("normalized", [](sf::Vector3<T>& self) { return self.normalized(); });
    v_sfVector3.def("lengthSquared", [](sf::Vector3<T>& self) { return self.lengthSquared(); });
    v_sfVector3.def("dot", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.dot(rhs); }, py::arg("rhs"));
    v_sfVector3.def("cross", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.cross(rhs); }, py::arg("rhs"));
    v_sfVector3.def("componentWiseMul", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.componentWiseMul(rhs); }, py::arg("rhs"));
    v_sfVector3.def("componentWiseDiv", [](sf::Vector3<T>& self, sf::Vector3<T> rhs) { return self.componentWiseDiv(rhs); }, py::arg("rhs"));
    v_sfVector3.def_readwrite("x", &sf::Vector3<T>::x);
    v_sfVector3.def_readwrite("y", &sf::Vector3<T>::y);
    v_sfVector3.def_readwrite("z", &sf::Vector3<T>::z);
    v_sfVector3.def("__neg__", [](sf::Vector3<T>& self) { return -self; });
    v_sfVector3.def("__iadd__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self += right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__isub__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self -= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__add__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self + right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__sub__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self - right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__mul__", [](sf::Vector3<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__imul__", [](sf::Vector3<T>& self, T right) { return self *= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__truediv__", [](sf::Vector3<T>& self, T right) { return self / right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__itruediv__", [](sf::Vector3<T>& self, T right) { return self /= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__eq__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__ne__", [](sf::Vector3<T>& self, sf::Vector3<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
}

template <typename T>
void bind_Vector4T(py::module &m, const std::string& name) {
    py::module m_sf = m.def_submodule("sf");
    auto v_sfVector4 = py::class_<sf::priv::Vector4<T>>(m_sf, name.c_str());
    v_sfVector4.def(py::init<>());
    v_sfVector4.def(py::init<>([](T x, T y, T z, T w) { return sf::priv::Vector4<T>(x, y, z, w); }), py::arg("x"), py::arg("y"), py::arg("z"), py::arg("w"));
    v_sfVector4.def_readwrite("x", &sf::priv::Vector4<T>::x);
    v_sfVector4.def_readwrite("y", &sf::priv::Vector4<T>::y);
    v_sfVector4.def_readwrite("z", &sf::priv::Vector4<T>::z);
    v_sfVector4.def_readwrite("w", &sf::priv::Vector4<T>::w);
}

void B_bind_Vector(py::module &m);
