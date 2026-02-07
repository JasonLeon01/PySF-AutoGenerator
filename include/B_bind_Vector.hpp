#pragma once

#include "SFML/System/Vector2.hpp"
#include "SFML/System/Vector3.hpp"
#include "SFML/Graphics/Glsl.hpp"
#include "A_utils.hpp"

namespace py = pybind11;

template <typename T>
void bind_VectorTCommon(py::class_<T>& v_sfVector) {
    v_sfVector.def(py::init<>());
    v_sfVector.def("lengthSquared", [](T& self) { return self.lengthSquared(); });
    v_sfVector.def("dot", [](T& self, T rhs) { return self.dot(rhs); }, py::arg("rhs"));
    v_sfVector.def("cross", [](T& self, T rhs) { return self.cross(rhs); }, py::arg("rhs"));
    v_sfVector.def("componentWiseMul", [](T& self, T rhs) { return self.componentWiseMul(rhs); }, py::arg("rhs"));
    v_sfVector.def("componentWiseDiv", [](T& self, T rhs) { return self.componentWiseDiv(rhs); }, py::arg("rhs"));
    v_sfVector.def("__neg__", [](T& self) { return -self; });
    v_sfVector.def("__iadd__", [](T& self, T right) { return self += right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__isub__", [](T& self, T right) { return self -= right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__add__", [](T& self, T right) { return self + right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__sub__", [](T& self, T right) { return self - right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__eq__", [](T& self, T right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__ne__", [](T& self, T right) { return self != right; }, py::arg("right"));  // from global binary operator
    add_copy_support(v_sfVector);
}

template <typename T>
void bind_Vector2T_Common(py::class_<sf::Vector2<T>>& v_sfVector2, const std::string& name) {
    bind_VectorTCommon(v_sfVector2);
    v_sfVector2.def(py::init<>([](T x, T y) { return new sf::Vector2<T>(x, y); }), py::arg("x"), py::arg("y"));
    v_sfVector2.def("perpendicular", [](sf::Vector2<T>& self) { return self.perpendicular(); });
    v_sfVector2.def_readwrite("x", &sf::Vector2<T>::x);
    v_sfVector2.def_readwrite("y", &sf::Vector2<T>::y);
    v_sfVector2.def("unpack", [](sf::Vector2<T>& self) { return py::make_tuple(self.x, self.y); });
    v_sfVector2.def("__mul__", [](sf::Vector2<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__imul__", [](sf::Vector2<T>& self, T right) { return self *= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__truediv__", [](sf::Vector2<T>& self, T right) { return self / right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__itruediv__", [](sf::Vector2<T>& self, T right) { return self /= right; }, py::arg("right"));  // from global binary operator
    v_sfVector2.def("__hash__", [](sf::Vector2<T>& self) { std::size_t seed = 0; hash_combine(seed, self.x); hash_combine(seed, self.y); return seed; });
    v_sfVector2.def("__repr__", [name](sf::Vector2<T>& self) {
        std::stringstream ss;
        ss << name << "(" << self.x << ", " << self.y << ")";
        return ss.str();
    });
}

template <typename T>
void bind_Vector2T(py::module &m_sf, const std::string& name) {
    auto v_sfVector2 = py::class_<sf::Vector2<T>>(m_sf, name.c_str());
    bind_Vector2T_Common(v_sfVector2, name);
}

template <typename T>
void bind_Vector2T_Explicit_Template(py::module &m_sf, const std::string& name) {
    auto v_sfVector2 = py::class_<sf::Vector2<T>>(m_sf, name.c_str());
    bind_Vector2T_Common(v_sfVector2, name);
    v_sfVector2.def(py::init<>([](T r, sf::Angle phi) { return sf::Vector2<T>(r, phi); }), py::arg("r"), py::arg("phi"));
    v_sfVector2.def("length", [](sf::Vector2<T>& self) { return self.length(); });
    v_sfVector2.def("normalized", [](sf::Vector2<T>& self) { return self.normalized(); });
    v_sfVector2.def("angleTo", [](sf::Vector2<T>& self, sf::Vector2<T> rhs) { return self.angleTo(rhs); }, py::arg("rhs"));
    v_sfVector2.def("angle", [](sf::Vector2<T>& self) { return self.angle(); });
    v_sfVector2.def("rotatedBy", [](sf::Vector2<T>& self, sf::Angle phi) { return self.rotatedBy(phi); }, py::arg("phi"));
    v_sfVector2.def("projectedOnto", [](sf::Vector2<T>& self, sf::Vector2<T> axis) { return self.projectedOnto(axis); }, py::arg("axis"));
}

template <typename T>
void bind_Vector3T_Common(py::class_<sf::Vector3<T>>& v_sfVector3, const std::string& name) {
    bind_VectorTCommon(v_sfVector3);
    v_sfVector3.def(py::init<>([](T x, T y, T z) { return new sf::Vector3<T>(x, y, z); }), py::arg("x"), py::arg("y"), py::arg("z"));
    v_sfVector3.def_readwrite("x", &sf::Vector3<T>::x);
    v_sfVector3.def_readwrite("y", &sf::Vector3<T>::y);
    v_sfVector3.def_readwrite("z", &sf::Vector3<T>::z);
    v_sfVector3.def("unpack", [](sf::Vector3<T>& self) { return py::make_tuple(self.x, self.y, self.z); });
    v_sfVector3.def("__mul__", [](sf::Vector3<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__imul__", [](sf::Vector3<T>& self, T right) { return self *= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__truediv__", [](sf::Vector3<T>& self, T right) { return self / right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__itruediv__", [](sf::Vector3<T>& self, T right) { return self /= right; }, py::arg("right"));  // from global binary operator
    v_sfVector3.def("__hash__", [](sf::Vector3<T>& self) { std::size_t seed = 0; hash_combine(seed, self.x); hash_combine(seed, self.y); hash_combine(seed, self.z); return seed; });
    v_sfVector3.def("__repr__", [name](sf::Vector3<T>& self) {
        std::stringstream ss;
        ss << name << "(" << self.x << ", " << self.y << ", " << self.z << ")";
        return ss.str();
    });
}

template <typename T>
void bind_Vector3T(py::module &m_sf, const std::string& name) {
    auto v_sfVector3 = py::class_<sf::Vector3<T>>(m_sf, name.c_str());
    bind_Vector3T_Common(v_sfVector3, name);
}

template <typename T>
void bind_Vector3T_Explicit_Template(py::module &m_sf, const std::string& name) {
    auto v_sfVector3 = py::class_<sf::Vector3<T>>(m_sf, name.c_str());
    bind_Vector3T_Common(v_sfVector3, name);
    v_sfVector3.def("length", [](sf::Vector3<T>& self) { return self.length(); });
    v_sfVector3.def("normalized", [](sf::Vector3<T>& self) { return self.normalized(); });
}

template <typename T>
void bind_Vector4T(py::module &m_sf, const std::string& name) {
    auto v_sfVector4 = py::class_<sf::priv::Vector4<T>>(m_sf, name.c_str());
    v_sfVector4.def(py::init<>());
    v_sfVector4.def(py::init<>([](T x, T y, T z, T w) { return new sf::priv::Vector4<T>(x, y, z, w); }), py::arg("x"), py::arg("y"), py::arg("z"), py::arg("w"));
    v_sfVector4.def_readwrite("x", &sf::priv::Vector4<T>::x);
    v_sfVector4.def_readwrite("y", &sf::priv::Vector4<T>::y);
    v_sfVector4.def_readwrite("z", &sf::priv::Vector4<T>::z);
    v_sfVector4.def_readwrite("w", &sf::priv::Vector4<T>::w);
    v_sfVector4.def("unpack", [](sf::priv::Vector4<T>& self) { return py::make_tuple(self.x, self.y, self.z, self.w); });
    v_sfVector4.def("__hash__", [](sf::priv::Vector4<T>& self) { std::size_t seed = 0; hash_combine(seed, self.x); hash_combine(seed, self.y); hash_combine(seed, self.z); hash_combine(seed, self.w); return seed; });
    v_sfVector4.def("__repr__", [name](sf::priv::Vector4<T>& self) {
        std::stringstream ss;
        ss << name << "(" << self.x << ", " << self.y << ", " << self.z << ", " << self.w << ")";
        return ss.str();
    });
    add_copy_support(v_sfVector4);
}

void B_bind_Vector(py::module &m_sf);
