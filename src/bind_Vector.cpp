#include "bind_Vector.hpp"
#include <sstream>
#include <cctype>

std::string getVectorDesc(int dimension) {
    return (std::ostringstream() << "\\brief Class template for manipulating\n" << dimension << "-dimensional vectors").str();
}

std::string getVectorConstructDesc(int dimension) {
    std::string constructDesc = "(";
    for (int i = 0; i < dimension; ++i) {
        constructDesc += "0";
        if (i != dimension - 1) {
            constructDesc += ", ";
        }
    }
    constructDesc += ")";
    return (std::ostringstream() << "\\brief Default constructor\n" << "Creates a `Vector" << dimension << constructDesc << "`.").str();
}

std::string getVectorConstructDescWithParams(int dimension) {
    std::vector<std::string> params = { "x", "y", "z", "w" };
    auto constructDesc = std::ostringstream() << "\\brief Construct the vector from " << (dimension == 2 ? "cartesian" : "its") << " coordinates\n\n";
    for (int i = 0; i < dimension; ++i) {
        constructDesc << "- \\param " << params[i] << " " << char(std::toupper(params[i][0])) << " coordinate" << "\n";
    }
    return constructDesc.str();
}

void bind_Vector(py::module &m_sf) {
    bind_Vector2T<int>(m_sf, "Vector2i");
    bind_Vector2T<float>(m_sf, "Vector2f");
    bind_Vector2T<unsigned int>(m_sf, "Vector2u");
    bind_Vector2T<bool>(m_sf, "Vector2b");

    bind_Vector3T<int>(m_sf, "Vector3i");
    bind_Vector3T<float>(m_sf, "Vector3f");
    bind_Vector3T<unsigned int>(m_sf, "Vector3u");
    bind_Vector3T<bool>(m_sf, "Vector3b");

    bind_Vector4T<int>(m_sf, "Vector4i");
    bind_Vector4T<float>(m_sf, "Vector4f");
    bind_Vector4T<bool>(m_sf, "Vector4b");
}
