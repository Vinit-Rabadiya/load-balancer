#ifndef __ROUTE_H
#define __ROUTE_H

#include "methods.h"
#include "request.h"
#include "response.h"

/**
 * Function type for handling routes
 */
typedef void (*route_handler)(Request *, Response *);

// HTTP Route
typedef struct Route
{
    char *path;            // Route path (only handles a single path, no nested paths)
    Method method;           // Route type (eg. GET, POST, DELETE, PUT)
    route_handler handler; // Route callback function
} Route;

#endif // __ROUTE_H