#include "B_bind_Vector.hpp"

void B_bind_Vector(py::module &m_sf) {
    bind_Vector2T<int>(m_sf, "Vector2i");
    bind_Vector2T<unsigned int>(m_sf, "Vector2u");
    bind_Vector2T<bool>(m_sf, "Vector2b");

    bind_Vector2T_Explicit_Template<float>(m_sf, "Vector2f");

    bind_Vector3T<int>(m_sf, "Vector3i");
    bind_Vector3T<bool>(m_sf, "Vector3b");

    bind_Vector3T_Explicit_Template<float>(m_sf, "Vector3f");

    bind_Vector4T<int>(m_sf, "Vector4i");
    bind_Vector4T<float>(m_sf, "Vector4f");
    bind_Vector4T<bool>(m_sf, "Vector4b");
}
