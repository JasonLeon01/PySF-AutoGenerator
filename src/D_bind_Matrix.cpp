#include "D_bind_Matrix.hpp"

void D_bind_Matrix(py::module &m) {
    bind_MatrixT<3>(m, "Mat3");
    bind_MatrixT<4>(m, "Mat4");
}
