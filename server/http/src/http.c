#include <sys/socket.h>
#include <netinet/ip.h>
#include <unistd.h>
#include <signal.h>

#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "http/http.h"
#include "http/request.h"
#include "http/response.h"

static volatile sig_atomic_t running = true;

static void handle_sigint(int sig)
{
    running = false;
}

Server *CreateServer(int port)
{
    Server *server = (Server *)malloc(sizeof(Server));
    if (server == NULL)
    {
        perror("Could not allocate memory for server");
        return NULL;
    }

    // Server socket fd
    int sfd = socket(AF_INET, SOCK_STREAM, 0);

    if (sfd == -1)
    {
        perror("Could not create socket");
        return NULL;
    }
    printf("Socket created (%d)\n", sfd);

    int opt = 1;
    if (setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1)
    {
        perror("Could not set socket option");
    }

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(port),
        .sin_addr = INADDR_ANY};

    if (bind(sfd, (struct sockaddr *)&addr, sizeof(addr)) == -1)
    {
        perror("Could not bind socket");
        close(sfd);
        return NULL;
    }
    printf("Socket bound to port %d\n", port);

    server->no_routes = 0;
    server->sfd = sfd;

    return server;
}

int AddRoute(Server *server, Route route)
{
    if (server->no_routes == __HTTP_MAX_ROUTES)
    {
        return -1;
    }

    server->routes[server->no_routes] = route;
    server->no_routes++;
    return 0;
}

int CloseServer(Server *server)
{
    printf("Closing server...\n");
    if (close(server->sfd) == -1)
    {
        perror("Could not close socket");
        return -1;
    }

    return 0;
}

int StartServer(Server *server)
{
    if (listen(server->sfd, 16) == -1)
    {
        perror("Could not put socket in listening state");
        return -1;
    }
    printf("Socket listening for connections...\n");

    // Override SIGINT
    struct sigaction sigact, oldact;
    memset(&sigact, 0, sizeof(sigact));
    sigact.sa_handler = handle_sigint;

    sigaction(SIGINT, &sigact, &oldact);

    while (running)
    {
        int cfd = accept(server->sfd, NULL, NULL);

        if (cfd == -1)
        {
            perror("Could not accept client request");
            continue;
        }

        char message[__HTTP_BUFFER_SIZE];
        ssize_t bytes_read = recv(cfd, message, __HTTP_BUFFER_SIZE, 0);
        if (bytes_read == -1)
        {
            perror("Could not read received data");
            close(cfd);
            continue;
        }

        Request req = ParseRequest(message);

        printf("DATA RECEIVED\n");
        printf("Method: %d\nPath: %s\n\nBody:\n%s\n", req.method, req.path, req.body);
        printf("=============\n\n");

        Response resp;

        if (req.method == UNKNOWN)
        {
            resp = CreateReponse(req.http_version, Status_NotImplemented, ContentType_TextPlain, "Requested method is not implemented");
        }
        else
        {
            int route_index = -1;
            for (int i = 0; i < server->no_routes; i++)
            {
                if ((strcmp(req.path, server->routes[i].path) == 0) &&
                    (req.method == server->routes[i].method))
                {
                    route_index = i;
                }
            }

            if (route_index == -1) {
                resp = CreateReponse(req.http_version, Status_NotFound, ContentType_NoContent, NULL);
            } else {
                resp = CreateReponse(req.http_version, Status_OK, ContentType_ApplicationJSON, "{\"status\": \"OK\"}");
                server->routes[route_index].handler(&req, &resp);
            }
        }

        SendResponse(cfd, resp);

        // Free the allocated memory for the request
        DeleteRequest(req);
        DeleteResponse(resp);

        // Clear the buffer
        memset(message, 0, __HTTP_BUFFER_SIZE);

        close(cfd);
    }

    // Set the default signal interrupt handler again
    sigaction(SIGINT, &oldact, NULL);

    return 0;
}