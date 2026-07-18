#ifndef __RESPONSE_H
#define __RESPONSE_H

#include <stddef.h>

#include "header.h"

typedef struct Response
{
    char http_version[HTTP_VER_LEN]; // HTTP version of the response
    StatusCode status;                // Response status
    ContentType content_type;        // Content-Type header
    char *body;                      // Response body
    size_t content_length;           // Length of the body
} Response;

/**
 * Create a response object.
 *
 * The HTTP version should match the request version.
 *
 * The content type can be set to either `ApplicationJSON` or `TextHTML` and the `body` must be a valid non-null pointer
 * to a non-empty string. If content type is set to `NoContent`, the body is ignored and not added.
 */
Response CreateReponse(char *http_version, StatusCode status, ContentType content_type, char *body);

// Send the response to the client file descriptor
int SendResponse(int cfd, Response response);

// Change the response body.
int SetResponseBody(Response *resp, char *body);

// Free the memory allocated for the response
void DeleteResponse(Response response);


// Default response error messages

// 404 Not found error response
static const char *NOT_FOUND_RESPONSE = 
        "HTTP/1.1 404 Not Found\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 37\r\n"
        "\r\n"
        "The specified path could not be found";

// Internal server error reponse
static const char *INTERNAL_SERVER_ERROR_RESPONSE = 
        "HTTP/1.1 500 Internal Server Error\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 21\r\n"
        "\r\n"
        "Internal server error";

// Method not implemented error reponse
static const char *NOT_IMPLEMENTED_RESPONSE = 
        "HTTP/1.1 501 Not Implemented\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 39\r\n"
        "\r\n"
        "The requested method is not implemented";

#endif // __RESPONSE_H