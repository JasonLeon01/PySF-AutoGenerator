#pragma once

#include "SFML/System.hpp"
#include "SFML/Window.hpp"
#include "SFML/Graphics.hpp"
#include "SFML/Audio.hpp"
#include "SFML/Network.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/buffer_info.h>
#include <filesystem>
#include <vector>

#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
#endif

namespace py = pybind11;

sf::String toSFString(const std::string& str);

std::string toUTF8String(const sf::String& str);

template <typename Class>
void def_string_property(py::class_<Class> &cls,
                         const char *name,
                         sf::String Class::*field) {
    cls.def_property(
        name,
        [field](const Class &self) { return toUTF8String(self.*field); },
        [field](Class &self, const std::string &value) { self.*field = toSFString(value); }
    );
}

sf::SoundSource::EffectProcessor wrap_effect_processor(py::function func);

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
