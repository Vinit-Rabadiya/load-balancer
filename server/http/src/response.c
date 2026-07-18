#include "http/response.h"

#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

#include <sys/socket.h>

#include "http/http.h"

Response CreateReponse(char *http_version, StatusCode status, ContentType content_type, char *body)
{
    Response resp;

    strncpy(resp.http_version, http_version, HTTP_VER_LEN);
    resp.status = status;
    resp.content_type = content_type;

    if (content_type != ContentType_NoContent)
    {
        size_t body_len = strlen(body);
        resp.body = (char *)calloc(body_len + 1, sizeof(char));
        if (resp.body == NULL)
        {
            perror("Couldn't allocate memory for response body");
        }
        strncpy(resp.body, body, body_len);
        resp.content_length = body_len;
    }
    else
    {
        resp.body = NULL;
        resp.content_length = 0;
    }

    return resp;
}

void DeleteResponse(Response resp)
{
    if (resp.content_type != ContentType_NoContent && resp.body != NULL)
    {
        free(resp.body);
    }
}

int SendResponse(int cfd, Response resp)
{
    // Construct the full message body
    char resp_buff[__HTTP_BUFFER_SIZE];

    char content_buff[__HTTP_BUFFER_SIZE / 4] = "";

    char *body_str = "";
    size_t content_length = 0;

    char *resp_format =
        "%s %s\r\n" // Response start line (HTTP/1.1 200 OK)
        "Server: C-HTTP-Server\r\n"
        "Content-Length: %d\r\n" // Content length must be present
        "%s"                     // Representation header and content
        "\r\n"
        "%s"; // Response body

    // Representation header string (only present if content type is not `NoContent`)
    char *content_format = "Content-Type: %s\r\n";
    if (resp.content_type != ContentType_NoContent && resp.content_type < SUPPORTED_CONTENT_TYPES)
    {
        snprintf(content_buff, __HTTP_BUFFER_SIZE / 4, content_format, CONTENT_TYPES[resp.content_type]);
        body_str = resp.body;
        content_length = resp.content_length;
        printf("Representation Header:\n%s\n", content_buff);
    }

    snprintf(resp_buff, __HTTP_BUFFER_SIZE, resp_format,
             resp.http_version, STATUS_CODES[resp.status],
             content_length, content_buff, body_str);

    printf("Response:\n%s\n", resp_buff);

    if (send(cfd, resp_buff, strlen(resp_buff), 0) == -1)
    {
        perror("Couldn't send response");
        return -1;
    }

    return 0;
}

int SetResponseBody(Response *resp, char *body)
{
    if (resp->body != NULL)
    {
        // Free the previously allocated response body
        free(resp->body);
    }

    size_t body_len = strlen(body);
    resp->body = (char *)calloc(body_len + 1, sizeof(char));
    if (resp->body == NULL)
    {
        perror("Couldn't allocate memory for response body");
        return -1;
    }
    strncpy(resp->body, body, body_len);
    resp->content_length = body_len;

    return 0;
}