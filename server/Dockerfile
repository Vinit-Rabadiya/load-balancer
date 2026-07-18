FROM alpine:3.14

RUN apk add --no-cache cmake build-base curl

# Build the source code
COPY . .
RUN cmake -B build
RUN cmake --build build

EXPOSE 5000
ENTRYPOINT ["./build/main"]
