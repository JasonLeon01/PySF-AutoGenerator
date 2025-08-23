#include "C_bind_Rect.hpp"

void C_bind_Rect(py::module &m_sf) {
    bind_RectT<int>(m_sf, "IntRect");
    bind_RectT<float>(m_sf, "FloatRect");
}
