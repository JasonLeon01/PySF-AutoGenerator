#include "F_bind_Drawable.hpp"

void PyDrawable::draw(sf::RenderTarget &target, sf::RenderStates states) const {
    PYBIND11_OVERRIDE_PURE(
        void,
        sf::Drawable,
        draw,
        target, states
    );
}


void F_bind_Drawable(py::module &m_sf) {
    py::class_<sf::Drawable, PyDrawable, std::unique_ptr<sf::Drawable, py::nodelete>>(m_sf, "Drawable");
}
