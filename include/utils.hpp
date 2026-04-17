#pragma once

#include "SFML/System.hpp"
#include "SFML/Window.hpp"
#include "SFML/Graphics.hpp"
#include "SFML/Audio.hpp"
#include "SFML/Network.hpp"
#include "string_utils.hpp"
#include "wrap_utils.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>
#include <filesystem>

#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
#endif

namespace py = pybind11;

template <typename T>
void add_copy_support(py::class_<T>& cls) {
    cls.def("__copy__", [](const T &self) {
        return T(self);
    })
    .def("__deepcopy__", [](const T &self, py::dict) {
        return T(self);
    }, py::arg("memo"));
}


template<typename T>
void hash_combine(std::size_t& seed, const T& val) {
    std::hash<T> hasher;
    seed ^= hasher(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}

sf::WindowHandle handleToSFMLHandle(uintptr_t qtWinId);

#ifdef __APPLE__
sf::WindowHandle handleToSFMLHandle_mac(uintptr_t qtWinId);
#endif
