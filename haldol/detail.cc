
#include <cstdarg>
#include <vector>
#include <algorithm>

#include "detail.hh"
#include "gil.hh"
#include "structcode.hh"

#define NO_IMPORT_ARRAY
#include <numpy/ndarrayobject.h>

namespace py {
    
    PyObject* None()  { return Py_BuildValue("O", Py_None); }
    PyObject* True()  { return Py_BuildValue("O", Py_True); }
    PyObject* False() { return Py_BuildValue("O", Py_False); }
    
    PyObject* boolean(bool truth) {
         return Py_BuildValue("O", truth ? Py_True : Py_False);
    }
    
    #if PY_MAJOR_VERSION < 3
    PyObject* string(std::string const& s) {
        return PyString_FromStringAndSize(s.c_str(), s.size());
    }
    PyObject* string(std::wstring const& w) {
        return PyUnicode_FromWideChar(w.data(), w.size());
    }
    PyObject* string(bytevec_t const& bv) {
        return PyString_FromStringAndSize((char const*)&bv[0], bv.size());
    }
    PyObject* string(charvec_t const& cv) {
        return PyString_FromStringAndSize((char const*)&cv[0], cv.size());
    }
    PyObject* string(char const* s) {
        return PyString_FromString(s);
    }
    PyObject* string(char const* s, std::size_t length) {
        return PyString_FromStringAndSize(s, length);
    }
    PyObject* string(char s) {
        return PyString_FromFormat("%c", s);
    }
    PyObject* format(char const* format, ...) {
        va_list arguments;
        va_start(arguments, format);
        PyObject* out = PyString_FromFormatV(format, arguments);
        va_end(arguments);
        return out;
    }
    // PyObject* format(std::string const& format, ...) {
    //     va_list arguments;
    //     va_start(arguments, format);
    //     PyObject* out = PyString_FromFormatV(format.c_str(), arguments);
    //     va_end(arguments);
    //     return out;
    // }
    #elif PY_MAJOR_VERSION >= 3
    PyObject* string(std::string const& s) {
        return PyBytes_FromStringAndSize(s.c_str(), s.size());
    }
    PyObject* string(std::wstring const& w) {
        return PyUnicode_FromWideChar(w.data(), w.size());
    }
    PyObject* string(bytevec_t const& bv) {
        return PyBytes_FromStringAndSize((char const*)&bv[0], bv.size());
    }
    PyObject* string(charvec_t const& cv) {
        return PyBytes_FromStringAndSize((char const*)&cv[0], cv.size());
    }
    PyObject* string(char const* s) {
        return PyBytes_FromString(s);
    }
    PyObject* string(char const* s, std::size_t length) {
        return PyBytes_FromStringAndSize(s, length);
    }
    PyObject* string(char s) {
        return PyBytes_FromFormat("%c", s);
    }
    PyObject* format(char const* format, ...) {
        va_list arguments;
        va_start(arguments, format);
        PyObject* out = PyString_FromFormatV(format, arguments);
        va_end(arguments);
        return out;
    }
    // PyObject* format(std::string const& format, ...) {
    //     va_list arguments;
    //     va_start(arguments, format);
    //     PyObject* out = PyString_FromFormatV(format.c_str(), arguments);
    //     va_end(arguments);
    //     return out;
    // }
    #endif
    
    PyObject* object(PyObject* arg) {
        return Py_BuildValue("O", arg ? arg : Py_None);
    }
    PyObject* object(PyFileObject* arg) {
        return py::object((PyObject*)arg);
    }
    PyObject* object(PyStringObject* arg) {
        return py::object((PyObject*)arg);
    }
    PyObject* object(PyTypeObject* arg) {
        return py::object((PyObject*)arg);
    }
    PyObject* object(PyArrayObject* arg) {
        return py::object((PyObject*)arg);
    }
    PyObject* object(PyArray_Descr* arg) {
        return py::object((PyObject*)arg);
    }
    
    PyObject* convert(PyObject* operand)            { return operand; }
    PyObject* convert(PyFileObject* operand)        { return (PyObject*)operand; }
    PyObject* convert(PyStringObject* operand)      { return (PyObject*)operand; }
    PyObject* convert(PyTypeObject* operand)        { return (PyObject*)operand; }
    PyObject* convert(PyArrayObject* operand)       { return (PyObject*)operand; }
    PyObject* convert(PyArray_Descr* operand)       { return (PyObject*)operand; }
    PyObject* convert(std::nullptr_t operand)       { return Py_BuildValue("O", Py_None); }
    PyObject* convert(void)                         { return Py_BuildValue("O", Py_None); }
    PyObject* convert(void* operand)                { return (PyObject*)operand; }
    PyObject* convert(bool operand)                 { return Py_BuildValue("O", operand ? Py_True : Py_False); }
    PyObject* convert(std::size_t operand)          { return PyInt_FromSize_t(operand); }
    PyObject* convert(Py_ssize_t operand)           { return PyInt_FromSsize_t(operand); }
    PyObject* convert(int8_t operand)               { return PyInt_FromSsize_t(static_cast<Py_ssize_t>(operand)); }
    PyObject* convert(int16_t operand)              { return PyInt_FromSsize_t(static_cast<Py_ssize_t>(operand)); }
    PyObject* convert(int32_t operand)              { return PyInt_FromSsize_t(static_cast<Py_ssize_t>(operand)); }
    PyObject* convert(int64_t operand)              { return PyLong_FromLong(operand); }
    // PyObject* convert(int128_t operand)             { return PyLong_FromLongLong(operand); }
    PyObject* convert(uint8_t operand)              { return PyInt_FromSize_t(static_cast<std::size_t>(operand)); }
    PyObject* convert(uint16_t operand)             { return PyInt_FromSize_t(static_cast<std::size_t>(operand)); }
    PyObject* convert(uint32_t operand)             { return PyInt_FromSize_t(static_cast<std::size_t>(operand)); }
    PyObject* convert(uint64_t operand)             { return PyLong_FromUnsignedLong(operand); }
    // PyObject* convert(uint128_t operand)            { return PyLong_FromUnsignedLongLong(operand); }
    PyObject* convert(float operand)                { return PyFloat_FromDouble(static_cast<double>(operand)); }
    PyObject* convert(double operand)               { return PyFloat_FromDouble(operand); }
    PyObject* convert(long double operand)          { return PyFloat_FromDouble(static_cast<double>(operand)); }
    
    #if PY_MAJOR_VERSION < 3
    PyObject* convert(char* operand)                { return PyString_FromString(operand); }
    PyObject* convert(char const* operand)          { return PyString_FromString(operand); }
    PyObject* convert(std::string const& operand)   { return PyString_FromStringAndSize(operand.c_str(), operand.size()); }
    PyObject* convert(char* operand,
                      std::size_t length)           { return PyString_FromStringAndSize(operand, length); }
    PyObject* convert(char const* operand,
                      std::size_t length)           { return PyString_FromStringAndSize(operand, length); }
    PyObject* convert(std::string const& operand,
                      std::size_t length)           { return PyString_FromStringAndSize(operand.c_str(), length); }
    PyObject* convert(char const* operand,
                      va_list arguments)            { return PyString_FromFormatV(operand, arguments); }
    PyObject* convert(std::string const& operand,
                      va_list arguments)            { return PyString_FromFormatV(operand.c_str(), arguments); }
    #elif PY_MAJOR_VERSION >= 3
    PyObject* convert(char* operand)                { return PyBytes_FromString(operand); }
    PyObject* convert(char const* operand)          { return PyBytes_FromString(operand); }
    PyObject* convert(std::string const& operand)   { return PyBytes_FromStringAndSize(operand.c_str(), operand.size()); }
    PyObject* convert(char* operand,
                      std::size_t length)           { return PyBytes_FromStringAndSize(operand, length); }
    PyObject* convert(char const* operand,
                      std::size_t length)           { return PyBytes_FromStringAndSize(operand, length); }
    PyObject* convert(std::string const& operand,
                      std::size_t length)           { return PyBytes_FromStringAndSize(operand.c_str(), length); }
    PyObject* convert(char const* operand,
                      va_list arguments)            { return PyBytes_FromFormatV(operand, arguments); }
    PyObject* convert(std::string const& operand,
                      va_list arguments)            { return PyBytes_FromFormatV(operand.c_str(), arguments); }
    #endif
    
    PyObject* convert(std::wstring const& operand)  { return PyUnicode_FromWideChar(operand.data(), operand.size()); }
    PyObject* convert(std::wstring const& operand,
                      std::size_t length)           { return PyUnicode_FromWideChar(operand.data(), length); }
    PyObject* convert(Py_buffer* operand)           { return PyMemoryView_FromBuffer(operand); }
    PyObject* convert(std::exception const& exc)    { return PyErr_NewExceptionWithDoc(const_cast<char*>("NativeException"),
                                                                                       const_cast<char*>(exc.what()),
                                                                                       nullptr, nullptr); }
    
    namespace impl {
        
        va_list&& argcompand(std::nullptr_t nothing, ...) {
            va_list arguments;
            va_start(arguments, nothing);
            va_list&& out = std::move(arguments);
            va_end(arguments);
            return std::move(out);
        }
        
    }
    
    PyObject* tuplize()                             { return PyTuple_New(0); }
    PyObject* listify()                             { return PyList_New(0);  }
    
    /*
     * THE IMPLEMENTATIONS: py::ref
     */
    
    ref::ref() noexcept {}
    
    ref::ref(bool destruct) noexcept
        :destroy(destruct)
        {}
    
    ref::ref(ref&& other) noexcept
        :referent(std::move(other.referent))
        ,destroy(other.destroy)
        {
            other.referent = nullptr;
        }
    
    ref& ref::operator=(ref&& other) noexcept {
        if (referent != other.referent) {
            Py_XDECREF(referent);
            referent = std::move(other.referent);
            destroy = other.destroy;
            other.referent = nullptr;
        }
        return *this;
    }
    
    ref::ref(ref::pyptr_t obj) noexcept
        :referent(obj)
        {}
    
    ref& ref::operator=(ref::pyptr_t obj) noexcept {
        if (referent != obj) {
            Py_XDECREF(referent);
            referent = obj;
        }
        return *this;
    }
    
    ref::~ref() {
        if (referent && destroy) {
            Py_DECREF(referent);
        }
    }
    
    ref const& ref::set(pyptr_t new_referent) {
        if (new_referent == referent) {
            return *this;
        }
        if (referent && destroy) {
            Py_DECREF(referent);
        }
        referent = new_referent;
        if (referent) {
            Py_INCREF(referent);
        }
        return *this;
    }
    
    ref const& ref::set(pyptr_t new_referent, bool new_destroy_value) {
        if (new_referent == referent) {
            return *this;
        }
        if (referent && destroy) {
            Py_DECREF(referent);
        }
        referent = new_referent;
        destroy = new_destroy_value;
        if (referent) {
            Py_INCREF(referent);
        }
        return *this;
    }
    
    ref::operator pyptr_t() const noexcept        { return referent; }
    ref::pyptr_t* ref::operator&() const noexcept { return &referent; }
    ref::pyptr_t ref::operator->() const noexcept { return referent; }
    ref::pyptr_t ref::get() const noexcept        { return referent; }
    
    ref const& ref::inc() const     { Py_INCREF(referent); return *this; }
    ref const& ref::dec() const     { Py_DECREF(referent); return *this; }
    ref const& ref::xinc() const    { Py_XINCREF(referent); return *this; }
    ref const& ref::xdec() const    { Py_XDECREF(referent); return *this; }
    ref&       ref::clear()         { Py_CLEAR(referent); return *this; }
    
    ref const& ref::inc(std::size_t c) const {
        switch (c) {
            case 0: return *this;
            case 1: return inc();
            default: {
                for (std::size_t idx = 0; idx < c; ++idx) { Py_INCREF(referent); }
                return *this;
            }
        }
    }
    
    ref const& ref::dec(std::size_t c) const {
        switch (c) {
            case 0: return *this;
            case 1: return dec();
            default: {
                for (std::size_t idx = 0; idx < c; ++idx) { Py_DECREF(referent); }
                return *this;
            }
        }
    }
    
    ref const& ref::xinc(std::size_t c) const {
        switch (c) {
            case 0: return *this;
            case 1: return xinc();
            default: {
                for (std::size_t idx = 0; idx < c; ++idx) { Py_XINCREF(referent); }
                return *this;
            }
        }
    }
    
    ref const& ref::xdec(std::size_t c) const {
        switch (c) {
            case 0: return *this;
            case 1: return xdec();
            default: {
                for (std::size_t idx = 0; idx < c; ++idx) { Py_XDECREF(referent); }
                return *this;
            }
        }
    }
    
    ref::pyptr_t ref::release() noexcept {
        ref::pyptr_t out = referent;
        referent = nullptr;
        return out;
    }
    
    ref& ref::reset() {
        return clear();
    }
    
    ref& ref::reset(ref::pyptr_t reset_to) {
        xdec();
        referent = reset_to;
        return *this;
    }
    
    void ref::swap(ref& other) noexcept {
        using std::swap;
        swap(referent, other.referent);
    }
    
    void swap(ref& lhs, ref& rhs) noexcept {
        using std::swap;
        swap(lhs.referent, rhs.referent);
    }
    
    std::size_t ref::hash() const {
        if (empty()) { return 0; }
        return std::size_t(PyObject_Hash(referent));
    }
    
    bool ref::empty() const noexcept {
        return referent == nullptr;
    }
    
    bool ref::truth() const {
        if (empty()) { return false; }
        return PyObject_IsTrue(referent) == 1;
    }
    
    bool ref::none() const {
        if (empty()) { return false; }
        return referent == Py_None;
    }
    
    ref::operator bool() const noexcept {
        return !empty();
    }
    
    bool ref::operator==(ref const& other) const {
        if (empty() && other.empty()) { return true; }
        if (empty() || other.empty()) { return false; }
        return PyObject_RichCompareBool(referent, other.referent, Py_EQ) == 1;
    }
    
    bool ref::operator!=(ref const& other) const {
        if (empty() && other.empty()) { return false; }
        if (empty() || other.empty()) { return true; }
        return PyObject_RichCompareBool(referent, other.referent, Py_NE) == 1;
    }
    
    bool  ref::operator<(ref const& other) const {
        if (empty() || other.empty()) { return false; }
        return PyObject_RichCompareBool(referent, other.referent, Py_LT) == 1;
    }
    
    bool ref::operator<=(ref const& other) const {
        if (empty() && other.empty()) { return true; }
        if (empty() || other.empty()) { return false; }
        return PyObject_RichCompareBool(referent, other.referent, Py_LE) == 1;
    }
    
    bool  ref::operator>(ref const& other) const {
        if (empty() || other.empty()) { return false; }
        return PyObject_RichCompareBool(referent, other.referent, Py_GT) == 1;
    }
    
    bool ref::operator>=(ref const& other) const {
        if (empty() && other.empty()) { return true; }
        if (empty() || other.empty()) { return false; }
        return PyObject_RichCompareBool(referent, other.referent, Py_GE) == 1;
    }
    
    std::string const ref::repr() const {
        if (empty()) { return "<nullptr>"; }
        if (PyString_Check(referent)) {
            return const_cast<char const*>(
                PyString_AS_STRING(referent));
        }
        py::ref representation = PyObject_Repr(referent);
        return representation.repr();
    }
    
    std::string const ref::to_string() const {
        if (empty()) { return "<nullptr>"; }
        if (PyString_Check(referent)) {
            return const_cast<char const*>(
                PyString_AS_STRING(referent));
        }
        py::ref stringified = PyObject_Str(referent);
        return stringified.to_string();
    }
    
    ref::operator std::string() const {
        return to_string();
    }
    
    std::ostream& operator<<(std::ostream& os, ref const& r) {
        return os << r.to_string();
    }
    
    py::ref&& asref(PyObject* referent) {
        py::ref out;
        out.set(referent);
        return std::move(out);
    }
    
    namespace detail {
        
        int setitem(PyObject* dict, PyObject* key, py::ref value) {
            return PyDict_SetItem(dict, key, value);
        }
        
        // int setitem(PyObject* dict, char const* key, py::ref value) {
        //     return PyDict_SetItemString(dict, key, value);
        // }
        
        // int setitem(PyObject* dict, std::string const& key, py::ref value) {
        //     return PyDict_SetItemString(dict, key.c_str(), value);
        // }
        
        int setitemstring(PyObject* dict, char const* key, py::ref value) {
            return PyDict_SetItemString(dict, key, value);
        }
        
        int setitemstring(PyObject* dict, std::string const& key, py::ref value) {
            return PyDict_SetItemString(dict, key.c_str(), value);
        }
        
        PyObject* structcode_to_dtype(char const* code) {
            using structcode::structcode_t;
            using structcode::parse_result_t;
            
            std::string endianness;
            stringvec_t parsetokens;
            structcode_t pairvec;
            Py_ssize_t imax = 0;
            
            {
                py::gil::release nogil;
                std::tie(endianness, parsetokens, pairvec) = structcode::parse(code);
                imax = static_cast<Py_ssize_t>(pairvec.size());
            }
            
            if (imax < 1) {
                PyErr_Format(PyExc_ValueError,
                    "Structcode %.200s parsed to zero-length", code);
                return nullptr;
            }
            
            /// Make python list of tuples
            PyObject* tuple = PyTuple_New(imax);
            for (Py_ssize_t idx = 0; idx < imax; idx++) {
                std::string endianized(endianness + pairvec[idx].second);
                PyTuple_SET_ITEM(tuple, idx, py::tuple(
                    py::string(pairvec[idx].first),
                    py::string(endianized)));
            }
            
            return tuple;
        }
    }
}
