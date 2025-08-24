#include "A_utils.hpp"

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
