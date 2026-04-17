template <typename T>
void add_copy_support(py::class_<T>& cls) {
    cls.def("__copy__", [](const T &self) {
        return T(self);
    })
    .def("__deepcopy__", [](const T &self, py::dict) {
        return T(self);
    }, py::arg("memo"));
}


template<typename T>
void hash_combine(std::size_t& seed, const T& val) {
    std::hash<T> hasher;
    seed ^= hasher(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}
