#include "SFML/Graphics/Rect.hpp"

template <typename T>
void bind_RectT(py::module &m_sf, const std::string& name) {
    auto v_sfRect = py::class_<sf::Rect<T>>(m_sf, name.c_str(), "\\brief Utility class for manipulating 2D axis aligned rectangles");
    v_sfRect.def(py::init<>(), "\\brief Default constructor\n\nCreates an empty rectangle (it is equivalent to calling\n\n`Rect({0, 0}, {0, 0})`).");
    v_sfRect.def(py::init<>([](sf::Vector2<T> position, sf::Vector2<T> size) { return new sf::Rect<T>(position, size); }), "\\brief Construct the rectangle from position and size\n\nBe careful, the last parameter is the size,\n\nnot the bottom-right corner!\n\n\\param position Position of the top-left corner of the rectangle\n\n\\param size     Size of the rectangle", py::arg("position"), py::arg("size"));
    v_sfRect.def("contains", [](sf::Rect<T>& self, sf::Vector2<T> point) { return self.contains(point); }, "\\brief Check if a point is inside the rectangle's area\n\nThis check is non-inclusive. If the point lies on the\n\nedge of the rectangle, this function will return `false`.\n\n\\param point Point to test\n\n\\return `true` if the point is inside, `false` otherwise\n\n\\see `findIntersection`", py::arg("point"));
    v_sfRect.def("findIntersection", [](sf::Rect<T>& self, sf::Rect<T> rectangle) { return self.findIntersection(rectangle); }, "\\brief Check the intersection between two rectangles\n\n\\param rectangle Rectangle to test\n\n\\return Intersection rectangle if intersecting, `std::nullopt` otherwise\n\n\\see `contains`", py::arg("rectangle"));
    v_sfRect.def("getCenter", [](sf::Rect<T>& self) { return self.getCenter(); }, "\\brief Get the position of the center of the rectangle\n\n\\return Center of rectangle");
    v_sfRect.def_readwrite("position", &sf::Rect<T>::position);
    v_sfRect.def_readwrite("size", &sf::Rect<T>::size);
    v_sfRect.def("__eq__", [](sf::Rect<T>& self, sf::Rect<T> right) { return self == right; }, py::arg("right"));  // from global binary operator
    v_sfRect.def("__ne__", [](sf::Rect<T>& self, sf::Rect<T> right) { return self != right; }, py::arg("right"));  // from global binary operator
    v_sfRect.def("__hash__", [](sf::Rect<T>& self) { std::size_t seed = 0; hash_combine(seed, self.position.x); hash_combine(seed, self.position.y); hash_combine(seed, self.size.x); hash_combine(seed, self.size.y); return seed; });
    v_sfRect.def("__repr__", [name](sf::Rect<T>& self) {
        std::stringstream ss;
        ss << name << "(" << self.position.x << ", " << self.position.y << ", " << self.size.x << ", " << self.size.y << ")";
        return ss.str();
    });
    add_copy_support(v_sfRect);
}
