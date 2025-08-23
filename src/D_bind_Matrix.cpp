#include "D_bind_Matrix.hpp"

void D_bind_Matrix(py::module &m_sf) {
    bind_MatrixT<3>(m_sf, "Mat3");
    bind_MatrixT<4>(m_sf, "Mat4");
}
