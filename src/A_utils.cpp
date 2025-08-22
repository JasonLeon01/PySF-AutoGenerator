#include "A_utils.hpp"

sf::SoundSource::EffectProcessor wrap_effect_processor(py::function func) {
    return [func](const float* inputFrames, unsigned int& inputFrameCount,
                  float* outputFrames, unsigned int& outputFrameCount,
                  unsigned int frameChannelCount) {
        py::gil_scoped_acquire gil;
        func(py::capsule(inputFrames), inputFrameCount,
             py::capsule(outputFrames), outputFrameCount,
             frameChannelCount);
    };
}
