#include "A_utils.hpp"

sf::String toSFString(const std::string& str) {
    return sf::String::fromUtf8(str.begin(), str.end());
}

std::string toUTF8String(const sf::String& str) {
    auto utf8Bytes = str.toUtf8();
    return std::string(utf8Bytes.begin(), utf8Bytes.end());
}

sf::SoundSource::EffectProcessor wrap_effect_processor(py::function func) {
    return [func](const float* inputFrames, unsigned int& inputFrameCount,
                  float* outputFrames, unsigned int& outputFrameCount,
                  unsigned int frameChannelCount) {
        py::gil_scoped_acquire gil;
        std::vector<float> input_vec(inputFrames, inputFrames + inputFrameCount * frameChannelCount);
        std::vector<float> output_vec(outputFrames, outputFrames + outputFrameCount * frameChannelCount);
        func(input_vec, inputFrameCount, output_vec, outputFrameCount, frameChannelCount);
        std::copy(output_vec.begin(), output_vec.end(), outputFrames);
    };
}

sf::WindowHandle handleToSFMLHandle(uintptr_t inQtHandle) {
#ifdef __APPLE__
    return handleToSFMLHandle_mac(inQtHandle);
#else
    return reinterpret_cast<sf::WindowHandle>(inQtHandle);
#endif
}
