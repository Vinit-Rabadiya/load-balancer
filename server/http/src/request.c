#include "http/request.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>

static Method GetMethod(char *method)
{
    for (int i = 0; i < SUPPORTED_METHODS; i++)
    {
        if (strcmp(method, METHODS[i]) == 0)
        {
            return i;
        }
    }

    return UNKNOWN;
}

Request ParseRequest(char *message)
{
    // Make a copy of the message string to prevent overwriting it with strtok
    size_t msg_len = strlen(message) + 1;
    char *msg_copy = (char *)calloc(msg_len, sizeof(char));
    memcpy(msg_copy, message, msg_len);

    char *saveptr;
    char *token = strtok_r(msg_copy, "\n", &saveptr);

    // Parse the request start line first
    char method_str[METHOD_LEN], path[PATH_LEN], version[HTTP_VER_LEN];
    sscanf(token, "%s %s %s", method_str, path, version);
    Method method = GetMethod(method_str);

    // Pointer to start of HTTP body
    char *body = NULL;

    while (token != NULL)
    {
        // If the next line starts with a \r, we've reached the end of the HTTP header
        if (*saveptr == '\r')
        {
            strtok_r(NULL, "\n", &saveptr);        // Parse the next line to advance the saveptr
            ptrdiff_t length = saveptr - msg_copy; // Some pointer arithmetic to get where the body starts
            body = msg_copy + length;
            break;
        }
        token = strtok_r(NULL, "\n", &saveptr);
    }

    Request request;

    request.method = method;
    memcpy(request.path, path, PATH_LEN);
    memcpy(request.http_version, version, HTTP_VER_LEN);

    request.content_length = strlen(body);
    request.body = (char *)calloc(request.content_length + 1, sizeof(char));
    memcpy(request.body, body, request.content_length + 1);

    free(msg_copy);

    return request;
}

void DeleteRequest(Request request)
{
    free(request.body);
}