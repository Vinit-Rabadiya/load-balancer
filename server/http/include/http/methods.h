#ifndef __METHODS_H
#define __METHODS_H

#define METHOD_LEN (16) // Buffer length for HTTP method string

#define SUPPORTED_METHODS (9) // Number of supported methods

// HTTP methods enum
typedef enum Method
{
    GET,
    POST,
    PUT,
    DELETE,
    HEAD,
    CONNECT,
    OPTIONS,
    TRACE,
    PATCH,
    UNKNOWN
} Method;

static const char *METHODS[] = {
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "HEAD",
    "CONNECT",
    "OPTIONS",
    "TRACE",
    "PATCH"};

#endif // __METHODS_H