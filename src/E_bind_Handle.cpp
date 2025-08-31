#include "E_bind_Handle.hpp"

void E_bind_Handle(py::module &m_sf) {
    #if defined(SFML_SYSTEM_WINDOWS)
        py::class_<HWND__>(m_sf, "WindowHandle");
    #elif defined(SFML_SYSTEM_MACOS)
        py::class_<void*>(m_sf, "WindowHandle");
    #elif defined(SFML_SYSTEM_LINUX)
        py::class_<unsigned long>(m_sf, "WindowHandle");
    #else
        py::class_<void*>(m_sf, "WindowHandle");
    #endif
}
