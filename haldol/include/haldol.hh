
#ifndef HALDOL_INCLUDE_HALDOL_HH_
#define HALDOL_INCLUDE_HALDOL_HH_

#include <cstdint>
#include <vector>

#ifndef __has_feature                       /// Optional
#define __has_feature(x)                0   /// Compatibility with non-clang compilers
#endif

namespace py {
    
    /// `byte` is a way better token than `uint8_t` from, like,
    /// a human mnemonic perspective.
    
    using byte = uint8_t;
    using bytevec_t = std::vector<byte>;
    
/// `unpack` is a sleazy trick for -- YOU GUESSED IT -- 
/// expanding variadic template parameter packs. USAGE:
///
///     unpack {
///         (out += std::to_string(array[I]))...
///     };

#define unpack                     __attribute__((unused)) int unpacker[]
    
}

#endif /// HALDOL_INCLUDE_HALDOL_HH_