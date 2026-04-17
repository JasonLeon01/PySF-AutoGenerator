#include <utility>

namespace py = pybind11;

namespace detail {
    template <typename Signature>
    std::function<Signature> wrap_impl(py::function func) {
        static_assert(always_false<Signature>::value, "wrap_impl not implemented for this signature");
        return nullptr;
    }

    template <>
    std::function<void(const float*, unsigned int&, float*, unsigned int&, unsigned int)>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)](const float* inputFrames, unsigned int& inputFrameCount,
                    float* outputFrames, unsigned int& outputFrameCount,
                    unsigned int frameChannelCount)
        {
            py::gil_scoped_acquire gil;
            auto input = py::memoryview::from_buffer(
                const_cast<float*>(inputFrames),
                sizeof(float),
                py::format_descriptor<float>::format().c_str(),
                {inputFrameCount, frameChannelCount},
                {sizeof(float) * frameChannelCount, sizeof(float)}
            );
            auto output = py::memoryview::from_buffer(
                outputFrames,
                sizeof(float),
                py::format_descriptor<float>::format().c_str(),
                {outputFrameCount, frameChannelCount},
                {sizeof(float) * frameChannelCount, sizeof(float)}
            );
            func(input, inputFrameCount, output, outputFrameCount, frameChannelCount);
        };
    }

    template <>
    std::function<void(sf::PlaybackDevice::Notification)>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)](sf::PlaybackDevice::Notification notification)
        {
            py::gil_scoped_acquire gil;
            func(notification);
        };
    }

    template <>
    std::function<void(const sf::Text::ShapedGlyph&, std::uint32_t&, sf::Color&, sf::Color&, float&)>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)](const sf::Text::ShapedGlyph& shapedGlyph, std::uint32_t& style, sf::Color& fillColor, sf::Color& outlineColor, float& outlineThickness)
        {
            py::gil_scoped_acquire gil;
            func(shapedGlyph, style, fillColor, outlineColor, outlineThickness);
        };
    }

    template <>
    std::function<bool(const void*, std::size_t)>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)](const void* data, std::size_t size)
        {
            py::gil_scoped_acquire gil;
            auto inData = py::memoryview::from_buffer(
                const_cast<void*>(data),
                1,
                "B",
                { static_cast<py::ssize_t>(size) },
                { 1 }
            );
            return func(inData, size).cast<bool>();
        };
    }

    template <>
    std::function<bool(void*, std::size_t&)>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)](void* data, std::size_t& size)
        {
            py::gil_scoped_acquire gil;
            auto inData = py::memoryview::from_buffer(
                const_cast<void*>(data),
                1,
                "B",
                { static_cast<py::ssize_t>(size) },
                { 1 }
            );
            return func(inData, size).cast<bool>();
        };
    }

    template <>
    std::function<void(sf::SocketSelector::ReadinessType)>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)](sf::SocketSelector::ReadinessType readiness)
        {
            py::gil_scoped_acquire gil;
            func(readiness);
        };
    }

    template <>
    std::function<bool()>
    wrap_impl(py::function func)
    {
        return [func = std::move(func)]()
        {
            py::gil_scoped_acquire gil;
            return func().cast<bool>();
        };
    }
}

template <typename Signature>
auto wrap_pyfunction(py::function func) {
    return detail::wrap_impl<Signature>(std::move(func));
}
