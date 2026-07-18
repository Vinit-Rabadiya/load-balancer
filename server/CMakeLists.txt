cmake_minimum_required(VERSION 3.19)

project(HttpServer C)

add_subdirectory(http)

add_executable(main)

target_sources(main
    PRIVATE
        src/main.c
)

target_link_libraries(main
    PRIVATE
        http
)