#pragma once

#include "SFML/Graphics/Drawable.hpp"
#include "SFML/Graphics/RenderTarget.hpp"
#include "SFML/Graphics/RenderStates.hpp"
#include "A_utils.hpp"
namespace py = pybind11;

struct PyDrawable : sf::Drawable {
    void draw(sf::RenderTarget &target, sf::RenderStates states) const override;
};

void F_bind_Drawable(py::module &m_sf);
