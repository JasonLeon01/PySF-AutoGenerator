#include "SFML/Graphics/Transform.hpp"
#include "SFML/Graphics/Glsl.hpp"

template <int N>
void bind_MatrixT(py::module &m_sf, const std::string& name) {
    auto v_sfMatrix = py::class_<sf::priv::Matrix<N, N>>(m_sf, name.c_str(), "\\brief 4x4 float matrix (\\p mat4 in GLSL)\n\nThe matrix can be constructed from an array with 4x4\n\nelements, aligned in column-major order. For example,\n\na translation by (x, y) looks as follows:\n\n\\code\nfloat array[9] =\n{\n    1, 0, 0,\n    0, 1, 0,\n    x, y, 1\n};\n\nsf::Glsl::Mat4 matrix(array);\n\\endcode\n\nMat4 can also be implicitly converted from `sf::Transform`:\n\n\\code\nsf::Transform transform;\nsf::Glsl::Mat4 matrix = transform;\n\\endcode");
    v_sfMatrix.def(py::init<>([](const std::vector<float>& pointer) { return new sf::priv::Matrix<N, N>(pointer.data()); }), py::arg("pointer"));
    v_sfMatrix.def(py::init<>([](const sf::Transform& transform) { return new sf::priv::Matrix<N, N>(transform); }), py::arg("transform"));
    v_sfMatrix.def_readwrite("array", &sf::priv::Matrix<N, N>::array);
    v_sfMatrix.def_static("copyMatrix", [](sf::Transform& source, sf::priv::Matrix<N, N>& dest) { return sf::priv::copyMatrix(source, dest); }, py::arg("source"), py::arg("dest"));
    v_sfMatrix.def("__hash__", [](sf::priv::Matrix<N, N>& self) { std::size_t seed = 0; for (int i = 0; i < N * N; ++i) hash_combine(seed, self.array[i]); return seed; });
    v_sfMatrix.def("__repr__", [](sf::priv::Matrix<N, N>& self) {
        std::stringstream ss;
        ss << "Matrix" << N << "(";
        for (int i = 0; i < N * N; ++i) {
            ss << self.array[i];
            if (i < N * N - 1) ss << ", ";
        }
        ss << ")";
        return ss.str();
    });
    add_copy_support(v_sfMatrix);
}
