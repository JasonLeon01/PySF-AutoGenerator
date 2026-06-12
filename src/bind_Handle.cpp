#include "bind_Handle.hpp"

void bind_Handle(py::module &m_sf) {
    py::class_<WindowHandle>(m_sf, "WindowHandle")
        .def(py::init<std::uintptr_t>(), py::arg("nativeHandle"))
        .def("getNativeHandle", &WindowHandle::toInteger)
        .def("__int__", &WindowHandle::toInteger)
        .def("__index__", &WindowHandle::toInteger)
        .def("__repr__", [](const WindowHandle& self) {
            return "WindowHandle(" + std::to_string(self.toInteger()) + ")";
        });
}
