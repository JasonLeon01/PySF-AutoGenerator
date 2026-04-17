template <typename Class>
void def_string_property(py::class_<Class> &cls,
                         const char *name,
                         sf::String Class::*field,
                         const std::string& docstring) {
    cls.def_property(
        name,
        [field](const Class &self) { return toUTF8String(self.*field); },
        [field](Class &self, const std::string &value) { self.*field = toSFString(value); },
        docstring.c_str()
    );
}

template <typename Class, typename Field>
void def_string_property_readonly(py::class_<Class> &cls,
                                 const char *name,
                                 Field field,
                                 const std::string& docstring) {
    cls.def_property_readonly(
        name,
        [field](const Class &self) { return toUTF8String(self.*field); },
        docstring.c_str()
    );
}

template <typename Class>
void def_vector_string_property(py::class_<Class> &cls,
                         const char *name,
                         std::vector<sf::String> Class::*field,
                         const std::string& docstring) {
    cls.def_property(
        name,
        [field](const Class &self) { return toVectorUTF8String(self.*field); },
        [field](Class &self, const std::vector<std::string>& value) { self.*field = toVectorSFString(value); },
        docstring.c_str()
    );
}

template <typename Class, typename Field>
void def_vector_string_property_readonly(py::class_<Class> &cls,
                                 const char *name,
                                 Field field,
                                 const std::string& docstring) {
    cls.def_property_readonly(
        name,
        [field](const Class &self) { return toVectorUTF8String(self.*field); },
        docstring.c_str()
    );
}

template <typename Class>
void def_vector_vector_string_property(py::class_<Class> &cls,
                         const char *name,
                         std::vector<std::vector<sf::String>> Class::*field,
                         const std::string& docstring) {
    cls.def_property(
        name,
        [field](const Class &self) { return toVectorVectorUTF8String(self.*field); },
        [field](Class &self, const std::vector<std::vector<std::string>>& value) { self.*field = toVectorVectorSFString(value); },
        docstring.c_str()
    );
}

template <typename Class, typename Field>
void def_vector_vector_string_property_readonly(py::class_<Class> &cls,
                                 const char *name,
                                 Field field,
                                 const std::string& docstring) {
    cls.def_property_readonly(
        name,
        [field](const Class &self) { return toVectorVectorUTF8String(self.*field); },
        docstring.c_str()
    );
}
