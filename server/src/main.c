#include <stdio.h>
#include <stdlib.h>

#include "http/http.h"
#include "http/route.h"
#include "http/request.h"
#include "http/response.h"

// Server name: set by getting the OS environment variables
char *server_id = NULL;

// GET Endpoint for /
void get_root(Request *req, Response *resp)
{
    resp->status = Status_OK;
    resp->content_type = ContentType_ApplicationJSON;
    SetResponseBody(resp, "{\"status\":\"Server is running properly!\"}");
}

// GET Endpoint for /home
void get_home(Request *req, Response *resp)
{
    resp->status = Status_OK;
    resp->content_type = ContentType_ApplicationJSON;

    char resp_buff[256];
    snprintf(resp_buff, 256, "{\"message\":\"Hello from Server: %s\", \"status\": \"successful\"}", server_id);

    SetResponseBody(resp, resp_buff);
}

// GET Endpoint for /heartbeat
void get_heartbeat(Request *req, Response *resp)
{
    resp->status = Status_OK;
    resp->content_type = ContentType_NoContent;
}

int main()
{
    Server *server = CreateServer(5000);

    if (server == NULL)
    {
        printf("Could not create server!\n");
        return -1;
    }

    // Get the server ID environment variable
    server_id = getenv("SERVER_ID");
    if (server_id == NULL)
    {
        server_id = "unknown";
    }
    printf("%s\n", server_id);

    Route root = {.method = GET, .path = "/", .handler = get_root};
    Route home = {.method = GET, .path = "/home", .handler = get_home};
    Route heartbeat = {.method = GET, .path = "/heartbeat", .handler = get_heartbeat};

    AddRoute(server, root);
    AddRoute(server, home);
    AddRoute(server, heartbeat);

    StartServer(server);

    CloseServer(server);

    return 0;
}