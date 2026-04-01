FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 go build -o device-service .

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/device-service .
EXPOSE 8083
CMD ["./device-service"]
