#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "easylzma/decompress.h"

#define LZMA_SUCCESS 0
#define LZMA_ERROR_INPUT 1
#define LZMA_ERROR_OUTPUT 2
#define LZMA_ERROR_MEMORY 3
#define LZMA_ERROR_CORRUPT 4

typedef struct {
    const unsigned char *data;
    size_t size;
    size_t position;
} read_buffer_context;

typedef struct {
    unsigned char **data;
    size_t *size;
} write_buffer_context;

static int buffer_read_callback(void *ctx, void *buf, size_t *size) {
    read_buffer_context *context = (read_buffer_context *)ctx;
    size_t remaining = context->size - context->position;
    size_t to_read = remaining < *size ? remaining : *size;
    
    if (to_read > 0) {
        memcpy(buf, context->data + context->position, to_read);
        context->position += to_read;
    }
    
    *size = to_read;
    return 0;
}

static size_t buffer_write_callback(void *ctx, const void *buf, size_t size) {
    write_buffer_context *context = (write_buffer_context *)ctx;
    
    *context->data = realloc(*context->data, *context->size + size);
    if (!*context->data) return 0;
    
    memcpy(*context->data + *context->size, buf, size);
    *context->size += size;
    
    return size;
}

char* decompress_file(const char *input_path, size_t *out_size) {
    FILE *in = fopen(input_path, "rb");
    if (!in) {
        perror("Failed to open input file");
        return NULL;
    }

    fseek(in, 0, SEEK_END);
    size_t input_size = ftell(in);
    fseek(in, 0, SEEK_SET);
    if (input_size == 0) {
        fprintf(stderr, "Input file is empty\n");
        fclose(in);
        return NULL;
    }

    unsigned char *input_buffer = (unsigned char *)malloc(input_size);
    if (!input_buffer) {
        fclose(in);
        fprintf(stderr, "Memory allocation failed\n");
        return NULL;
    }

    if (fread(input_buffer, 1, input_size, in) != input_size) {
        perror("Failed to read input file");
        fclose(in);
        free(input_buffer);
        return NULL;
    }

    fclose(in);

    unsigned char *output_buffer = NULL;
    size_t output_size = 0;
    
    elzma_decompress_handle handle;
    handle = elzma_decompress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate decompression handle\n");
        free(input_buffer);
        return NULL;
    }

    read_buffer_context input_ctx = {
        .data = input_buffer,
        .size = input_size,
        .position = 0
    };
    
    write_buffer_context output_ctx = {
        .data = &output_buffer,
        .size = &output_size
    };
    
    int ret = elzma_decompress_run(handle, 
                                 buffer_read_callback, &input_ctx,
                                 buffer_write_callback, &output_ctx,
                                 ELZMA_lzma);
    elzma_decompress_free(&handle);
    
    free(input_buffer);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Decompression failed with error code: %d\n", ret);
        return NULL;
    }

    if (output_size > (100 * 1024 * 1024)) {
        fprintf(stderr, "Decompressed size is too large: %zu bytes\n", output_size);
        free(output_buffer);
        return NULL;
    }

    *out_size = output_size;
    return (char*)output_buffer;
}

int decompress_buffer(const unsigned char *input_buffer, size_t input_size,
                     unsigned char **output_buffer, size_t *output_size) {
    elzma_decompress_handle handle = elzma_decompress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate decompression handle\n");
        return LZMA_ERROR_MEMORY;
    }
    
    read_buffer_context input_ctx = {
        .data = input_buffer,
        .size = input_size,
        .position = 0
    };
    
    *output_buffer = NULL;
    *output_size = 0;
    
    write_buffer_context output_ctx = {
        .data = output_buffer,
        .size = output_size
    };
    
    int ret = elzma_decompress_run(handle, 
                                 buffer_read_callback, &input_ctx,
                                 buffer_write_callback, &output_ctx,
                                 ELZMA_lzma);
    
    elzma_decompress_free(&handle);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Decompression failed with error code %d\n", ret);
        free(*output_buffer);
        *output_buffer = NULL;
        *output_size = 0;
        return LZMA_ERROR_CORRUPT;
    }
    
    return LZMA_SUCCESS;
}
