#pragma once

#include "SFML/System.hpp"
#include "SFML/Window.hpp"
#include "SFML/Graphics.hpp"
#include "SFML/Audio.hpp"
#include "SFML/Network.hpp"
#include <functional>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/buffer_info.h>

namespace py = pybind11;

namespace detail {
    template <typename T>
    struct always_false : std::false_type {};

    template <typename Signature>
    inline std::function<Signature> wrap_impl(py::function func);

    template <>
    inline std::function<void(const float*, unsigned int&, float*, unsigned int&, unsigned int)>
    wrap_impl(py::function func);

    template <>
    inline std::function<void(sf::PlaybackDevice::Notification)>
    wrap_impl(py::function func);

    template <>
    inline std::function<void(const sf::Text::ShapedGlyph&, std::uint32_t&, sf::Color&, sf::Color&, float&)>
    wrap_impl(py::function func);

    template <>
    inline std::function<bool(const void*, std::size_t)>
    wrap_impl(py::function func);

    template <>
    inline std::function<bool(void*, std::size_t&)>
    wrap_impl(py::function func);

    template <>
    inline std::function<void(sf::SocketSelector::ReadinessType)>
    wrap_impl(py::function func);

    template <>
    inline std::function<bool()>
    wrap_impl(py::function func);
}

template <typename Signature>
auto wrap_pyfunction(py::function func);

#include "wrap_utils.inl"
