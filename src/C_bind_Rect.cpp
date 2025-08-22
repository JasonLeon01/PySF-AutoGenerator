#include "C_bind_Rect.hpp"

void C_bind_Rect(py::module &m) {
    bind_RectT<int>(m, "IntRect");
    bind_RectT<float>(m, "FloatRect");
}
