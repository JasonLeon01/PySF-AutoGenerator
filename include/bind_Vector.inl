#include "SFML/System/Angle.hpp"
#include "SFML/System/Vector2.hpp"
#include "SFML/System/Vector3.hpp"
#include "SFML/Graphics/Glsl.hpp"
#include <type_traits>

template <typename T>
void bind_VectorTCommon(py::class_<T>& v_sfVector, int dimension) {
    v_sfVector.def(py::init<>(), getVectorConstructDesc(dimension).c_str());
    v_sfVector.def("lengthSquared", [](T& self) { return self.lengthSquared(); }, "\\brief Square of vector's length.\n\nSuitable for comparisons, more efficient than `length()`.");
    v_sfVector.def("dot", [](T& self, T rhs) { return self.dot(rhs); }, "\\brief Dot product of two <2/3>D vectors.", py::arg("rhs"));
    v_sfVector.def("cross", [](T& self, T rhs) { return self.cross(rhs); }, "\\brief Z component of the cross product of two 2D vectors.\n\nTreats the operands as 3D vectors, computes their cross product\nand returns the result's Z component (X and Y components are always zero).", py::arg("rhs"));
    v_sfVector.def("componentWiseMul", [](T& self, T rhs) { return self.componentWiseMul(rhs); }, "\\brief Component-wise multiplication of `*this` and `rhs`.\n\nComputes `(lhs.x*rhs.x, lhs.y*rhs.y)`.\n\nScaling is the most common use case for component-wise multiplication/division.\nThis operation is also known as the Hadamard or Schur product.", py::arg("rhs"));
    v_sfVector.def("componentWiseDiv", [](T& self, T rhs) { return self.componentWiseDiv(rhs); }, "\\brief Component-wise division of `*this` and `rhs`.\n\nComputes `(lhs.x/rhs.x, lhs.y/rhs.y)`.\n\nScaling is the most common use case for component-wise multiplication/division.\n\\pre Neither component of `rhs` is zero.", py::arg("rhs"));
    v_sfVector.def("__iadd__", [](T& self, T right) { return self += right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__isub__", [](T& self, T right) { return self -= right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__add__", [](T& self, T right) { return self + right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__sub__", [](T& self, T right) { return self - right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__eq__", [](T& self, T right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfVector.def("__ne__", [](T& self, T right) { return self != right; }, py::arg("right"));  // from global binary operator
    if constexpr (std::is_same_v<T, sf::Vector2f> || std::is_same_v<T, sf::Vector3f>) {
        v_sfVector.def("length", [](T& self) { return self.length(); }, "\\brief Length of the vector <i><b>(floating-point)</b></i>.\n\nIf you are not interested in the actual length, but only in comparisons, consider using `lengthSquared()`.");
        v_sfVector.def("normalized", [](T& self) { return self.normalized(); }, "\\brief Vector with same direction but length 1 <i><b>(floating-point)</b></i>.\n\n\\pre `*this` is no zero vector.");
    }
    add_copy_support(v_sfVector);
}

template <typename T>
void bind_Vector2T_Common(py::class_<sf::Vector2<T>>& v_sfVector2, const std::string& name) {
    bind_VectorTCommon(v_sfVector2, 2);
    v_sfVector2.def(py::init<>([](T x, T y) { return new sf::Vector2<T>(x, y); }), getVectorConstructDescWithParams(2).c_str(), py::arg("x"), py::arg("y"));
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
    v_sfVector2.def("perpendicular", [](sf::Vector2<T>& self) { return self.perpendicular(); }, "\\brief Returns a perpendicular vector.\n\nReturns `*this` rotated by +90 degrees; (x,y) becomes (-y,x).\nFor example, the vector (1,0) is transformed to (0,1).\n\nIn SFML's default coordinate system with +X right and +Y down,\nthis amounts to a clockwise rotation.");
    if constexpr (std::is_floating_point_v<T>) {
        v_sfVector2.def(py::init<>([](T r, sf::Angle phi) { return new sf::Vector2<T>(r, phi); }), "\\brief Construct the vector from polar coordinates <i><b>(floating-point)</b></i>\n\n- \\param r   Length of vector (can be negative)\n- \\param phi Angle from X axis\n\nNote that this constructor is lossy: calling `length()` and `angle()`\nmay return values different to those provided in this constructor.\n\nIn particular, these transforms can be applied:\n* `Vector2(r, phi) == Vector2(-r, phi + 180_deg)`\n* `Vector2(r, phi) == Vector2(r, phi + n * 360_deg)`", py::arg("r"), py::arg("phi"));
        v_sfVector2.def("angleTo", [](sf::Vector2<T>& self, sf::Vector2<T>& rhs) { return self.angleTo(rhs); }, "\\brief Signed angle from `*this` to `rhs` <i><b>(floating-point)</b></i>.\n\n\\return The smallest angle which rotates `*this` in positive\nor negative direction, until it has the same direction as `rhs`.\nThe result has a sign and lies in the range [-180, 180) degrees.\n\\pre Neither `*this` nor `rhs` is a zero vector.", py::arg("rhs"));
        v_sfVector2.def("angle", [](sf::Vector2<T>& self) { return self.angle(); }, "\\brief Signed angle from +X or (1,0) vector <i><b>(floating-point)</b></i>.\n\nFor example, the vector (1,0) corresponds to 0 degrees, (0,1) corresponds to 90 degrees.\n\n\\return Angle in the range [-180, 180) degrees.\n\\pre This vector is no zero vector.");
        v_sfVector2.def("rotatedBy", [](sf::Vector2<T>& self, sf::Angle& phi) { return self.rotatedBy(phi); }, "\\brief Rotate by angle \\c phi <i><b>(floating-point)</b></i>.\n\nReturns a vector with same length but different direction.\n\nIn SFML's default coordinate system with +X right and +Y down,\nthis amounts to a clockwise rotation by `phi`.", py::arg("phi"));
        v_sfVector2.def("projectedOnto", [](sf::Vector2<T>& self, sf::Vector2<T>& axis) { return self.projectedOnto(axis); }, "\\brief Projection of this vector onto `axis` <i><b>(floating-point)</b></i>.\n\n- \\param axis Vector being projected onto. Need not be normalized.\n\\pre `axis` must not have length zero.", py::arg("axis"));
    }
}

template <typename T>
void bind_Vector3T_Common(py::class_<sf::Vector3<T>>& v_sfVector3, const std::string& name) {
    bind_VectorTCommon(v_sfVector3, 3);
    v_sfVector3.def(py::init<>([](T x, T y, T z) { return new sf::Vector3<T>(x, y, z); }), getVectorConstructDescWithParams(3).c_str(), py::arg("x"), py::arg("y"), py::arg("z"));
    v_sfVector3.def_readwrite("x", &sf::Vector3<T>::x);
    v_sfVector3.def_readwrite("y", &sf::Vector3<T>::y);
    v_sfVector3.def_readwrite("z", &sf::Vector3<T>::z);
    v_sfVector3.def("unpack", [](sf::Vector3<T>& self) { return py::make_tuple(self.x, self.y, self.z); });
    v_sfVector3.def("__mul__", [](sf::Vector2<T>& self, T right) { return self * right; }, py::arg("right"));  // from global binary operator
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
void bind_Vector2T(py::module &m_sf, const std::string& name) {
    auto v_sfVector2 = py::class_<sf::Vector2<T>>(m_sf, name.c_str(), getVectorDesc(2).c_str());
    bind_Vector2T_Common(v_sfVector2, name);
}

template <typename T>
void bind_Vector3T(py::module &m_sf, const std::string& name) {
    auto v_sfVector3 = py::class_<sf::Vector3<T>>(m_sf, name.c_str(), getVectorDesc(3).c_str());
    bind_Vector3T_Common(v_sfVector3, name);
}

template <typename T>
void bind_Vector4T(py::module &m_sf, const std::string& name) {
    auto v_sfVector4 = py::class_<sf::priv::Vector4<T>>(m_sf, name.c_str(), "\\brief Utility template class for manipulating\n\n4-dimensional vectors");
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
