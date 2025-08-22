#include "B_bind_Vector.hpp"

void B_bind_Vector(py::module &m) {
    bind_Vector2T<int>(m, "Vector2i");
    bind_Vector2T<unsigned int>(m, "Vector2u");
    bind_Vector2T<bool>(m, "Vector2b");

    bind_Vector2T_Explicit_Template<float>(m, "Vector2f");

    bind_Vector3T<int>(m, "Vector3i");
    bind_Vector3T<bool>(m, "Vector3b");

    bind_Vector3T_Explicit_Template<float>(m, "Vector3f");

    bind_Vector4T<int>(m, "Vector4i");
    bind_Vector4T<float>(m, "Vector4f");
    bind_Vector4T<bool>(m, "Vector4b");
}
