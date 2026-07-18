add_library(http)

target_sources(http
    PRIVATE
        src/http.c
        src/request.c
        src/response.c
)

target_include_directories(http
    PUBLIC
        include
)