#ifndef PyImgC_STRUCTCODE_H
#define PyImgC_STRUCTCODE_H

#include <string>
#include <utility>
#include <vector>
#include <map>

namespace structcode {
    
    using stringmap_t = std::map<std::string, std::string>;
    using stringvec_t = std::vector<std::string>;
    
    struct structcodemaps {
        
        public:
            static stringmap_t init_byteorder();
            static stringmap_t init_native();
            static stringmap_t init_standard();
        
        public:
            static std::string const& byteorder_get(std::string const&);
            static std::string const& native_get(std::string const&);
            static std::string const& standard_get(std::string const&);
        
        private:
            static const stringmap_t byteorder;
            static const stringmap_t native;
            static const stringmap_t standard;
        
    };
    
    struct field_namer {
        
        public:
            field_namer();
            std::size_t next();
            void add(std::string const&);
            bool has(std::string const&) const;
            std::string operator()();
        
        private:
            std::size_t idx = 0;
            stringvec_t field_name_vector;
        
    };
    
    using shapevec_t = std::vector<int>;
    using structcode_t = std::vector<std::pair<std::string, std::string>>;
    
    using parse_result_t = std::tuple<std::string, stringvec_t, structcode_t>;
    
    shapevec_t parse_shape(std::string shapecode);
    parse_result_t parse(std::string structcode, bool toplevel=true);

} /// namespace structcode

#endif