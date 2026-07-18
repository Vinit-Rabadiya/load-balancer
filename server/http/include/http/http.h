#ifndef __HTTP_H
#define __HTTP_H

#include <stddef.h>

#include "route.h"

// HTTP request buffer size
#define __HTTP_BUFFER_SIZE (1024 * 4)

// Maximum number of routes allowed (16 by default)
#define __HTTP_MAX_ROUTES (16)

/**
 * HTTP Server struct
 */
typedef struct Server
{
    int sfd;                         // Socket file descriptor
    Route routes[__HTTP_MAX_ROUTES]; // Array of all route handlers
    size_t no_routes;                // Number of routes attached to the server
} Server;

// Create a new HTTP server
Server *CreateServer(int port);

// Add a route to a server
int AddRoute(Server *server, Route route);

// Close a server (handled on SIGINT)
int CloseServer(Server *server);

// Start the server
int StartServer(Server *server);

#endif // __HTTTP_H