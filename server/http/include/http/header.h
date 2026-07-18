/**
 * Header file the defines constants for HTTP header sections
 */

#ifndef __HEADER_H
#define __HEADER_H

#define PATH_LEN (256)         // Buffer length for request path
#define HTTP_VER_LEN (16)      // Buffer length for HTTP version
#define CONTENT_TYPE_LEN (256) // Length of the content type header

#define SUPPORTED_STATUS_CODES (7)  // Number of supported status codes
#define SUPPORTED_CONTENT_TYPES (2) // Number of supported content types

// Status code type
typedef enum StatusCode
{
    Status_OK,
    Status_Created,
    Status_Accepted,
    Status_NoContent,
    Status_BadRequest,
    Status_NotFound,
    Status_InternalServerError,
    Status_NotImplemented
} StatusCode;

// Array of all status codes
static const char *STATUS_CODES[] = {
    "200 OK",
    "201 Created",
    "202 Accepted",
    "204 No Content",
    "400 Bad Request",
    "404 Not Found",
    "500 Internal Server Error",
    "501 Not Implemented"};

// Content types
typedef enum ContentType
{
    ContentType_ApplicationJSON,
    ContentType_TextPlain,
    ContentType_TextHTML,
    ContentType_NoContent, // Represents no content present in the body
    ContentType_Unkown
} ContentType;

// Array of all content types
static const char *CONTENT_TYPES[] = {
    "application/json",
    "text/plain",
    "text/html"};

#endif // __HEADER_H