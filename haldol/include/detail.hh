
#ifndef HALDOL_INCLUDE_DETAIL_HPP_
#define HALDOL_INCLUDE_DETAIL_HPP_

#include <tuple>
#include <array>
#include <memory>
#include <string>
#include <vector>
#include <sstream>
#include <utility>
#include <exception>
#include <functional>
#include <type_traits>
#include <initializer_list>

#include <Python.h>
#include "haldol.hh"

#define NO_IMPORT_ARRAY
#include <numpy/arrayobject.h>

namespace py {
    
    using py::byte;
    using bytevec_t = std::vector<byte>;
    using charvec_t = std::vector<char>;
    using stringvec_t = std::vector<std::string>;
    
    PyObject* None();
    PyObject* True();
    PyObject* False();
    
    PyObject* boolean(bool truth = false);
    PyObject* string(std::string const&);
    PyObject* string(std::wstring const&);
    PyObject* string(bytevec_t const&);
    PyObject* string(charvec_t const&);
    PyObject* string(char const*);
    PyObject* string(char const*, std::size_t);
    PyObject* string(char);
    PyObject* format(char const*, ...);
    PyObject* object(PyObject* arg);
    #if PY_MAJOR_VERSION < 3
    PyObject* object(PyFileObject* arg);
    PyObject* object(PyStringObject* arg);
    #endif
    PyObject* object(PyTypeObject* arg);
    PyObject* object(PyArrayObject* arg);
    PyObject* object(PyArray_Descr* arg);
    
    template <typename ...Args> inline
    PyObject* tuple(Args&& ...args) {
        static_assert(
            sizeof...(Args) > 0,
            "Can't pack a zero-length arglist as a PyTuple");
        
        return PyTuple_Pack(
            sizeof...(Args),
            std::forward<Args>(args)...);
    }
    
    PyObject* convert(PyObject*);
    #if PY_MAJOR_VERSION < 3
    PyObject* convert(PyFileObject*);
    PyObject* convert(PyStringObject*);
    #endif
    PyObject* convert(PyTypeObject*);
    PyObject* convert(PyArrayObject*);
    PyObject* convert(PyArray_Descr*);
    PyObject* convert(std::nullptr_t);
    PyObject* convert(void);
    PyObject* convert(void*);
    PyObject* convert(bool);
    PyObject* convert(std::size_t);
    PyObject* convert(Py_ssize_t);
    PyObject* convert(int8_t);
    PyObject* convert(int16_t);
    PyObject* convert(int32_t);
    PyObject* convert(int64_t);
    PyObject* convert(uint8_t);
    PyObject* convert(uint16_t);
    PyObject* convert(uint32_t);
    PyObject* convert(uint64_t);
    PyObject* convert(float);
    PyObject* convert(double);
    PyObject* convert(long double);
    PyObject* convert(char*);
    PyObject* convert(char const*);
    PyObject* convert(std::string const&);
    PyObject* convert(char*, std::size_t);
    PyObject* convert(char const*, std::size_t);
    PyObject* convert(std::string const&, std::size_t);
    PyObject* convert(std::wstring const&);
    PyObject* convert(std::wstring const&, std::size_t);
    PyObject* convert(char const*, va_list);
    PyObject* convert(std::string const&, va_list);
    PyObject* convert(Py_buffer*);
    PyObject* convert(std::exception const&);
    
    /* >>>>>>>>>>>>>>>>>>> FORWARD DECLARATIONS <<<<<<<<<<<<<<<<<<<< */
    
    template <typename First, typename Second>
    PyObject* convert(std::pair<First, Second> pair);
    
    template <typename ...Args>
    PyObject* convert(std::tuple<Args...> argtuple);
    
    template <typename ...Args>
    PyObject* convert(std::tuple<Args&&...> argtuple);
    
    template <typename Vector,
              typename Value = typename Vector::value_type>
    PyObject* convert(Vector const& vector);
    
    template <typename Mapping,
              typename Value = typename Mapping::mapped_type,
              typename std::enable_if_t<
                       std::is_constructible<std::string,
                                             typename Mapping::key_type>::value,
              int> = 0>
    PyObject* convert(Mapping const& mapping);
    
    /* >>>>>>>>>>>>>>>>>>> EXPLICIT CASTS <<<<<<<<<<<<<<<<<<<< */
    
    template <typename Cast,
              typename Original,
              typename std::enable_if_t<std::is_arithmetic<Cast>::value &&
                                        std::is_arithmetic<Original>::value,
              int> = 0> inline
    PyObject* convert(Original orig) {
        return py::convert(static_cast<Cast>(orig));
    }
    
    template <typename Cast,
              typename Original,
              typename std::enable_if_t<!std::is_arithmetic<Cast>::value &&
                                        !std::is_arithmetic<Original>::value,
              int> = 0> inline
    PyObject* convert(Original orig) {
        return py::convert(reinterpret_cast<Cast>(orig));
    }
    
    template <typename ...Args>
    using convertible = std::is_same<std::add_pointer_t<PyObject>,
                                     std::common_type_t<
                                         decltype(
                                      py::convert(std::declval<Args>()))...>>;
    
    template <typename ...Args>
    bool convertible_v = py::convertible<Args...>::value;
    
    /* >>>>>>>>>>>>>>>>>>> PRINTF-ISH FORMAT STYLE <<<<<<<<<<<<<<<<<<<< */
    
    namespace impl {
        
        __attribute__((format(printf, 1, 2)))
        void argcheck(const char* format, ...);
        va_list&& argcompand(std::nullptr_t, ...);
        
        #define static_argcheck(disambiguate, ...) \
            if (false) { py::impl::argcheck(__VA_ARGS__); }
        
    }
    
    template <typename ...Args>
    __attribute__((nonnull(1)))
    PyObject* convert(char const* formatstring, bool disambiguate, Args&&... args) {
        /// trigger compile-time type checks for printf-style variadics
        /// -- this is a no-op at runtime:
        static_argcheck(disambiguate,
                        formatstring,
                        std::forward<Args>(args)...);
        
        /// dispatch using argument pack companded as a va_list:
        return py::convert(formatstring,
               py::impl::argcompand(nullptr, std::forward<Args>(args)...));
    }
    
    /* >>>>>>>>>>>>>>>>>>> TUPLIZE <<<<<<<<<<<<<<<<<<<< */
    
    PyObject* tuplize();
    
    template <typename ListType,
              typename std::enable_if_t<
                        py::convertible<ListType>::value,
              int> = 0>
    PyObject* tuplize(std::initializer_list<ListType> list) {
        Py_ssize_t idx = 0,
                   max = list.size();
        PyObject* tuple = PyTuple_New(max);
        for (ListType const& item : list) {
            PyTuple_SET_ITEM(tuple, idx, py::convert(item));
            idx++;
        }
        return tuple;
    }
    
    template <typename Args,
              typename std::enable_if_t<
                        py::convertible<Args>::value,
              int> = 0>
    PyObject* tuplize(Args arg) {
        return PyTuple_Pack(1,
            py::convert(std::forward<Args>(arg)));
    }
    
    template <typename ...Args>
    PyObject* tuplize(Args&& ...args) {
        static_assert(
            sizeof...(Args) > 1,
            "Can't tuplize a zero-length arglist");
        
        return PyTuple_Pack(
            sizeof...(Args),
            py::convert(std::forward<Args>(args))...);
    }
    
    /* >>>>>>>>>>>>>>>>>>> LISTIFY <<<<<<<<<<<<<<<<<<<< */
    
    PyObject* listify();
    
    template <typename ListType,
              typename std::enable_if_t<
                        py::convertible<ListType>::value,
              int> = 0>
    PyObject* listify(std::initializer_list<ListType> list) {
        Py_ssize_t idx = 0,
                   max = list.size();
        PyObject* pylist = PyList_New(max);
        for (ListType const& item : list) {
            PyList_SET_ITEM(pylist, idx, py::convert(item));
            idx++;
        }
        return pylist;
    }
    
    template <typename Args,
              typename std::enable_if_t<
                        py::convertible<Args>::value,
              int> = 0>
    PyObject* listify(Args arg) {
        PyObject* pylist = PyList_New(1);
        PyList_SET_ITEM(pylist, 0,
            py::convert(std::forward<Args>(arg)));
        return pylist;
    }
    
    template <typename Tuple, std::size_t ...I>
    PyObject* listify(Tuple&& t, std::index_sequence<I...>) {
        PyObject* pylist = PyList_New(
            std::tuple_size<Tuple>::value);
        unpack {
            PyList_SET_ITEM(pylist, I,
                py::convert(std::get<I>(std::forward<Tuple>(t))))...
        };
        return pylist;
    }
    
    template <typename ...Args>
    PyObject* listify(Args&& ...args) {
        using Indices = std::index_sequence_for<Args...>;
        static_assert(
            sizeof...(Args) > 1,
            "Can't listify a zero-length arglist");
        
        return py::listify(
            std::forward_as_tuple(args...),
            Indices());
    }
    
    namespace impl {
        
        template <typename Tuple>
        std::size_t tuple_size_v = std::tuple_size<Tuple>::value;
        
        template <typename F, typename Tuple, std::size_t ...I> inline
        auto apply_impl(F&& f, Tuple&& t, std::index_sequence<I...>) {
            return std::forward<F>(f)(std::get<I>(std::forward<Tuple>(t))...);
        }
        
        template <typename F, typename Tuple> inline
        auto apply(F&& f, Tuple&& t) {
            using Indices = std::make_index_sequence<tuple_size_v<std::decay_t<Tuple>>>;
            return apply_impl(std::forward<F>(f), std::forward<Tuple>(t), Indices());
        }
        
    }
    
    /* >>>>>>>>>>>>>>>>>>> PAIR AND TUPLE CONVERTERS <<<<<<<<<<<<<<<<<<<< */
    
    template <typename First, typename Second>
    PyObject* convert(std::pair<First, Second> pair) {
        using Pair = std::pair<First, Second>;
        using Indices = std::make_index_sequence<2>;
        return py::impl::apply_impl(py::tuplize<First, Second>,
                                    std::forward<Pair>(pair),
                                    Indices());
    }
    
    template <typename ...Args>
    PyObject* convert(std::tuple<Args...> argtuple) {
        using Tuple = std::tuple<Args...>;
        using Indices = std::index_sequence_for<Args...>;
        if (py::impl::tuple_size_v<Tuple> == 0) {
            return py::tuplize();
        }
        return py::impl::apply_impl(py::tuplize<Args...>,
                                    std::forward<Tuple>(argtuple),
                                    Indices());
    }
    
    template <typename ...Args>
    PyObject* convert(std::tuple<Args&&...> argtuple) {
        using Tuple = std::tuple<Args&&...>;
        using Indices = std::index_sequence_for<Args...>;
        if (py::impl::tuple_size_v<Tuple> == 0) {
            return py::tuplize();
        }
        return py::impl::apply_impl(py::tuplize<Args...>,
                                    std::forward<Tuple>(argtuple),
                                    Indices());
    }
    
    /* >>>>>>>>>>>>>>>>>>> GENERIC DECONTAINERIZERS <<<<<<<<<<<<<<<<<<<< */
    
    template <typename Vector, typename Value>
    PyObject* convert(Vector const& vector) {
        Py_ssize_t idx = 0,
                   max = vector.size();
        PyObject* tuple = PyTuple_New(max);
        for (Value const& item : vector) {
            PyTuple_SET_ITEM(tuple, idx, py::convert(item));
            idx++;
        }
        return tuple;
    }
    
    template <typename Mapping, typename Value,
              typename std::enable_if_t<
                       std::is_constructible<std::string,
                                             typename Mapping::key_type>::value,
              int>>
    PyObject* convert(Mapping const& mapping) {
        PyObject* dict = PyDict_New();
        for (auto const& item : mapping) {
            std::string key(item.first);
            PyObject* pytem = py::convert(item.second);
            PyDict_SetItemString(dict, key.c_str(), pytem);
            Py_DECREF(pytem);
        }
        return dict;
    }
    
    /// enum class base-type-izer function,
    /// courtesy http://stackoverflow.com/a/14589519/298171
    template <typename EnumType>
    constexpr auto integralize(EnumType e) -> typename std::underlying_type<EnumType>::type {
       return static_cast<typename std::underlying_type<EnumType>::type>(e);
    }
    
    template <typename EnumType>
    PyObject* integral(EnumType e) {
        return py::convert(py::integralize<EnumType>(e));
    }
    
    /// The py::ref mini-class is a little bitty tiny wrapper around
    /// a PyObject*, intended for casual-friday, C++-y, RAII-diculous scope-based
    /// use in treatment of acute reference-count-induced frontal lobe irritation.
    /// If you dislike having to stick calls to Py_DECREF() all over everything,
    /// and want to generally lexically underscore that a given Python object pointer
    /// -- a PyObject*, as we often say -- is a mere temporary, never to see a lifetime
    /// beyond the scope of its acquisition... well then, you should use py::ref to
    /// simplify your Python/C++ programming experience. Like instead of:
    ///
    ///     PyObject* pyThing = PyObject_SomeAPICall();
    ///     /// your pyThing stuff is herein done
    ///     Py_DECREF(pyThing);
    ///
    /// ... you can basically just do:
    /// 
    ///     py::ref pyThing = PyObject_SomeAPICall();
    ///     /// do the same* pyThing stuff ...
    ///     /// ... but as a chuckling Jobs said c. 1999, THERE IS NO STEP THREE
    ///
    /// ... (*) the fine print: some calls may balk at being passed a py::ref instead of
    /// a vanilla PyObject*, notably macros e.g. PyString_AS_STRING(); you can deal
    /// with those by manually sticking in a get() method call e.g. PyString_AS_STRING(ref.get())
    /// which will inline a return of the wrapped PyObject*. 
    ///
    /// There are convenience template constructors for the creation of a py::ref from
    /// any type that py::convert() can hanlde, e.g.:
    ///
    ///     py::ref ref0 = 3;                               /// ref0 is a PyInt/PyLong
    ///     py::ref ref1 = 3.14159f;                        /// ref1 is a PyFloat
    ///     py::ref ref2 = "Yo Dogg";                       /// ref2 is a PyString
    ///     std::vector<byte> bv = image.plane<byte>(0);
    ///     Py_buffer* view = PyObject_GetBuffer(image);    /// (NB. not really this API call's signature)
    ///     py::buffer::source pyview(*view);               /// ... py::ref can't release a Py_buffer*!
    ///     py::ref ref3 = bv;                              /// ref3 is a PyTuple with bytes from an image's zero-plane
    ///     py::ref ref4 = view;                            /// ref4 is a PyMemoryView on the image buffer-back
    ///     py::ref ref5 = py::string(bv);                  /// ref5 is a PyString-ified copy of ref3's planar byte data
    ///     py::ref ref6 = py::listify(true, 2, "yo dogg"); /// ref6 is a 3-item PyList containing what you think it does
    /// 
    /// ... the above code bits, when evaluated in a scoped context, will clean
    /// themselves up without the need for any additional Python API calls... Hence
    /// the bit up there with py::buffer::source -- many users are often confused by how
    /// PyObject* refcounting is totally separate from the Py_buffer API; relatedly,
    /// a py::ref created from a Py_buffer* doesn't know anything about where
    /// that Py_buffer* came from -- it does not care about what happens to
    /// its referent after the py::convert() call and as such the py::ref will
    /// release its internal temporary PyMemoryView object at scope exit and
    /// leave the dangling Py_buffer* unreleased. So TL;DR use py::buffer::source to
    /// do separate Py_buffer* scope-sitting alongside py::ref right? You get this.
    
    class ref {
        
        public:
            
            /// A pedantic way to say PyObject*
            using pyptr_t = std::add_pointer_t<PyObject>;
            
            /// py::ref::can_convert<T>::value == true for any (T t) iff
            /// the expression:
            ///
            ///     PyObject* py_t = py::convert(t);
            ///
            /// will successfully compile. (but remember at runtime
            /// who but GvR can know though, I'm just saying doggie)
            template <typename ...Args>
            using can_convert = std::is_same<pyptr_t, std::common_type_t<decltype(
                                                       py::convert(std::declval<Args>()))...>>;
            
            /// default constructor, yields a nullptr referent
            ref() noexcept;
            
            /// explicit boolean constructor, for disabling destructor logic
            explicit ref(bool) noexcept;
            
            /// py::refs are moveable via construction/assignment
            /// ... but *not* copyable as you may note
            ref(ref&& other) noexcept;
            ref& operator=(ref&& other) noexcept;
            
            /// py::refs are constructable/assignable direct from PyObject*
            ref(pyptr_t obj) noexcept;
            ref& operator=(pyptr_t obj) noexcept;
            
            /// conditionally-enabled templates to allow direct construction
            /// and/or assignment of py::refs from ANY type that can
            /// be successfully turned into a PyObject* via py::convert()
            template <typename RawType,
                      typename std::enable_if_t<
                              !std::is_same<RawType, pyptr_t>::value &&
                               py::ref::can_convert<RawType>::value,
                      int> = 0>
            ref(RawType&& raw)
                :referent(py::convert(std::forward<RawType>(raw)))
                {}
            
            template <typename RawType,
                      typename std::enable_if_t<
                              !std::is_same<RawType, pyptr_t>::value &&
                               py::ref::can_convert<RawType>::value,
                      int> = 0>
            ref& operator=(RawType&& raw) {
                Py_XDECREF(referent);
                referent = py::convert(std::forward<RawType>(raw));
                return *this;
            }
            
            /// virtual destructor, Py_XDECREFs the referent pointer
            virtual ~ref();
            
            /// explicitly set and Py_INCREF a new referent --
            /// -- and optionally a new boolean value for 'destroy' --
            /// ... self-returning, for chainability
            ref const& set(pyptr_t);
            ref const& set(pyptr_t, bool);
            
            /// implicit and explicit getters for the internal PyObject*
            operator pyptr_t() const noexcept;
            pyptr_t* operator&() const noexcept;
            pyptr_t operator->() const noexcept;
            pyptr_t get() const noexcept;
            
            /// refcount control methods, mapped to their macro namesakes
            ref const& inc() const;
            ref const& dec() const;
            ref const& xinc() const;
            ref const& xdec() const;
            ref&      clear();
            
            ref const& inc(std::size_t) const;
            ref const& dec(std::size_t) const;
            ref const& xinc(std::size_t) const;
            ref const& xdec(std::size_t) const;
            
            /// std::shared_ptr-esque calls, for explicit lifecycle termination
            pyptr_t release() noexcept;
            ref& reset();
            ref& reset(pyptr_t);
            
            /// member swap and friend swap
            void swap(ref& other) noexcept;
            friend void swap(ref& lhs, ref& rhs) noexcept;
            
            /// member hash method
            std::size_t hash() const;
            
            /// boolean-test methods and boolean-conversion operator
            bool empty() const noexcept;
            bool truth() const;
            bool none() const;
            explicit operator bool() const noexcept;
            
            /// wrappers for PyObject_RichCompareBool()
            bool operator==(ref const&) const;
            bool operator!=(ref const&) const;
            bool  operator<(ref const&) const;
            bool operator<=(ref const&) const;
            bool  operator>(ref const&) const;
            bool operator>=(ref const&) const;
            
            /// stringification
            std::string const repr() const;
            std::string const to_string() const;
            operator std::string() const;
            friend std::ostream& operator<<(std::ostream&, ref const&);
            
        private:
            
            ref(ref const&);                    /// NO COPYING
            ref& operator=(ref const&);         /// EYES ON YOUR OWN POINTER
        
        protected:
            
            mutable pyptr_t referent = nullptr; /// the object in question
            bool destroy = true;
    };
    
    class callable : public ref {
        
        public:
            
            template <typename ...Args,
                      typename std::enable_if_t<
                                py::ref::can_convert<Args...>::value,
                      int> = 0>
            py::ref operator()(Args&& ...args) {
                if (!referent)                      { return py::None(); }
                if (!PyCallable_Check(referent))    { return py::None(); }
                return PyObject_CallFunctionObjArgs(referent,
                                        py::convert(std::forward<Args>(args))...,
                                                    nullptr);
            }
        
    };
    
    /// get a py::ref for a PyObject* after incrementing its refcount --
    /// useful for temporary and scope-based py::refs:
    py::ref&& asref(PyObject*);
    
    namespace detail {
        
        /// Use nop<MyThing> to make a non-deleting unique_ptr e.g.
        /// 
        ///     using nondeleting_ptr = std::unique_ptr<MyThing,
        ///                             py::detail::nop<MyThing>>;
        /// 
        template <typename B>
        struct nop {
            constexpr nop() noexcept = default;
            template <typename U> nop(nop<U> const&) noexcept {}
            void operator()(std::add_pointer_t<B> ptr) { /*NOP*/ }
        };
        
        template <typename T>
        bool null_or_void = std::is_void<T>::value ||
                            std::is_null_pointer<T>::value;
        
        /// pollyfills for C++17 std::clamp()
        /// q.v. http://ideone.com/IpcDt9, http://en.cppreference.com/w/cpp/algorithm/clamp
        template <class T, class Compare>
        constexpr T const& clamp(T const& v, T const& lo, T const& hi, Compare comp) {
            return comp(v, hi) ? std::max(v, lo, comp) : std::min(v, hi, comp);
        }
        template <class T>
        constexpr T const& clamp(T const& v, T const& lo, T const& hi) {
            return clamp(v, lo, hi, std::less<>());
        }
        
        /// polyfills for std::experimental::to_array()
        /// q.v. http://en.cppreference.com/w/cpp/experimental/to_array
        template <class T, std::size_t N, std::size_t ...I>
        constexpr std::array<std::remove_cv_t<T>, N> to_array_impl(T (&a)[N],
                                                                   std::index_sequence<I...>) {
            return {{ a[I]... }};
        }
        
        template <class T, std::size_t N>
        constexpr std::array<std::remove_cv_t<T>, N> to_array(T (&a)[N]) {
            return to_array_impl(a, std::make_index_sequence<N>{});
        }
        
        /// C++11 constexpr-friendly reimplementation of `offsetof()` --
        /// see also: https://gist.github.com/graphitemaster/494f21190bb2c63c5516
        /// 
        ///     std::size_t o = py::detail::offset(&ContainingType::classMember); /// or
        ///     std::size_t o = PYDEETS_OFFSET(ContainingType, classMember);
        /// 
        namespace {
            
            template <typename T1, typename T2>
            struct offset_impl {
                static T2 thing;
                static constexpr std::size_t off_by(T1 T2::*member) {
                    return std::size_t(&(offset_impl<T1, T2>::thing.*member)) -
                           std::size_t(&offset_impl<T1, T2>::thing);
                }
            };
            
            template <typename T1, typename T2>
            T2 offset_impl<T1, T2>::thing;
            
        }
        
        template <typename T1, typename T2> inline
        constexpr Py_ssize_t offset(T1 T2::*member) {
            return static_cast<Py_ssize_t>(
                offset_impl<T1, T2>::off_by(member));
        }
        
        #define PYDEETS_OFFSET(type, member) py::detail::offset(&type::member)
        
        /// XXX: remind me why in fuck did I write this shit originally
        template <typename T, typename pT>
        std::unique_ptr<T> dynamic_cast_unique(std::unique_ptr<pT>&& source) {
            /// Force a dynamic_cast upon a unique_ptr via interim swap
            /// ... danger, will robinson: DELETERS/ALLOCATORS NOT WELCOME
            /// ... from http://stackoverflow.com/a/14777419/298171
            if (!source) { return std::unique_ptr<T>(); }
            
            /// Throws a std::bad_cast() if this doesn't work out
            T* destination = &dynamic_cast<T&>(*source.get());
            
            source.release();
            std::unique_ptr<T> out(destination);
            return out;
        }
        
        /// Versions of PyDict_SetItem and PyDict_SetItemString that STEAL REFERENCES:
        int setitem(PyObject* dict, PyObject* key, py::ref value);
        // int setitem(PyObject* dict, char const* key, py::ref value);
        // int setitem(PyObject* dict, std::string const& key, py::ref value);
        int setitemstring(PyObject* dict, char const* key, py::ref value);
        int setitemstring(PyObject* dict, std::string const& key, py::ref value);
        
        /// A misnomer -- actually returns a dtype-compatible tuple full
        /// of label/format subtuples germane to the description
        /// of the parsed typecode you pass it
        PyObject* structcode_to_dtype(char const* code);
    }
    
}

namespace std {
    
    template <>
    struct hash<py::ref> {
        
        typedef py::ref argument_type;
        typedef std::size_t result_type;
        
        result_type operator()(argument_type const& ref) const {
            return static_cast<result_type>(ref.hash());
        }
        
    };
    
} /* namespace std */

#endif /// HALDOL_INCLUDE_DETAIL_HPP_