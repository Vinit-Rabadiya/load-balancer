/**
 * Handles parsing HTTP requests
 */

#ifndef __HTTP_REQUESTS_H
#define __HTTP_REQUESTS_H

#include "methods.h"
#include "header.h"

#include <stddef.h>

// Struct representing a HTTP request
typedef struct Request
{
    Method method;                   // The request method
    char path[PATH_LEN];             // Requested path
    char http_version[HTTP_VER_LEN]; // HTTP version
    char *body;                      // Request body
    size_t content_length;           // Size in bytes of the body (excluding the \0 character)
} Request;

// Parse a request message
Request ParseRequest(char *message);

// Free allocated memory for a request
void DeleteRequest(Request request);

#endif // __HTTP_REQUESTS_H