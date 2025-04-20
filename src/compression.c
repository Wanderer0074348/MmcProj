#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "easylzma/compress.h"

// Define error codes since they're not provided by the library
#define LZMA_SUCCESS 0
#define LZMA_ERROR_INPUT 1
#define LZMA_ERROR_OUTPUT 2
#define LZMA_ERROR_MEMORY 3
#define LZMA_ERROR_CORRUPT 4

// Structure to hold buffer information for read callbacks
typedef struct {
    const unsigned char *data;
    size_t size;
    size_t position;
} read_buffer_context;

// Structure to hold buffer information for write callbacks
typedef struct {
    unsigned char **data;
    size_t *size;
} write_buffer_context;

// Callback for reading from a buffer
static int buffer_read_callback(void *ctx, void *buf, size_t *size) {
    read_buffer_context *context = (read_buffer_context *)ctx;
    size_t remaining = context->size - context->position;
    size_t to_read = remaining < *size ? remaining : *size;
    
    if (to_read > 0) {
        memcpy(buf, context->data + context->position, to_read);
        context->position += to_read;
    }
    
    *size = to_read;
    return 0; // Success
}

// Callback for writing to a dynamically allocated buffer
static size_t buffer_write_callback(void *ctx, const void *buf, size_t size) {
    write_buffer_context *context = (write_buffer_context *)ctx;
    
    // Reallocate the output buffer to accommodate new data
    *context->data = realloc(*context->data, *context->size + size);
    if (!*context->data) return 0; // Memory allocation failed
    
    // Copy the new data
    memcpy(*context->data + *context->size, buf, size);
    *context->size += size;
    
    return size; // Return the number of bytes written
}

int compress_file(const char *input_path, const char *output_path) {
    FILE *in = fopen(input_path, "rb");
    if (!in) {
        perror("Failed to open input file");
        return LZMA_ERROR_INPUT;
    }

    // Get input file size
    fseek(in, 0, SEEK_END);
    size_t input_size = ftell(in);
    fseek(in, 0, SEEK_SET);
    if (input_size == 0) {
        fprintf(stderr, "Input file is empty\n");
        fclose(in);
        return LZMA_ERROR_INPUT;
    }

    // Read input file into buffer
    unsigned char *input_buffer = (unsigned char *)malloc(input_size);
    if (!input_buffer) {
        fclose(in);
        fprintf(stderr, "Memory allocation failed\n");
        return LZMA_ERROR_MEMORY;
    }

    if (fread(input_buffer, 1, input_size, in) != input_size) {
        perror("Failed to read input file");
        fclose(in);
        free(input_buffer);
        return LZMA_ERROR_INPUT;
    }

    fclose(in);

    // Use EasyLZMA to compress the data
    unsigned char *compressed_data = NULL;
    size_t compressed_size = 0;

    // Create compression handle
    elzma_compress_handle handle;
    handle = elzma_compress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate compression handle\n");
        free(input_buffer);
        return LZMA_ERROR_MEMORY;
    }

    // Configure compression parameters with the correct number of arguments
    // Using default values for lc, lp, pb, and a compression level of 9
    int ret = elzma_compress_config(handle,
        ELZMA_LC_DEFAULT,      // lc (literal context bits)
        ELZMA_LP_DEFAULT,      // lp (literal position bits)
        ELZMA_PB_DEFAULT,      // pb (position bits)
        9,                     // level (highest compression level)
        ELZMA_DICT_SIZE_DEFAULT_MAX, // dictionarySize
        ELZMA_lzma,            // format
        input_size);           // uncompressedSize             // level (highest compression level)
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Failed to configure compression: %d\n", ret);
        elzma_compress_free(&handle);
        free(input_buffer);
        return LZMA_ERROR_CORRUPT;
    }

    // Set up input context
    read_buffer_context input_ctx = {
        .data = input_buffer,
        .size = input_size,
        .position = 0
    };
    
    // Set up output context
    write_buffer_context output_ctx = {
        .data = &compressed_data,
        .size = &compressed_size
    };
    
    // Perform compression with the correct number of arguments
    ret = elzma_compress_run(handle, 
                           buffer_read_callback, &input_ctx,
                           buffer_write_callback, &output_ctx,
                           NULL, NULL);
    
    // Free the compression handle
    elzma_compress_free(&handle);
    
    // Free input buffer as we don't need it anymore
    free(input_buffer);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Compression failed with error code: %d\n", ret);
        return LZMA_ERROR_CORRUPT;
    }

    // Write compressed data to output file
    FILE *out = fopen(output_path, "wb");
    if (!out) {
        free(compressed_data);
        perror("Failed to open output file");
        return LZMA_ERROR_OUTPUT;
    }

    size_t bytes_written = fwrite(compressed_data, 1, compressed_size, out);
    fclose(out);
    if (bytes_written != compressed_size) {
        free(compressed_data);
        fprintf(stderr, "Failed to write entire compressed data\n");
        return LZMA_ERROR_OUTPUT;
    }

    printf("Compressed %zu bytes to %zu bytes (%.2f%%)\n",
           input_size, compressed_size, (float)compressed_size * 100 / input_size);
    
    // Free compressed data
    free(compressed_data);
    return LZMA_SUCCESS;
}

int compress_buffer(const uint8_t *input_buffer, size_t input_size, 
                   uint8_t *output_buffer, size_t *output_size) {
    if (input_size == 0) {
        return LZMA_ERROR_INPUT;
    }

    // Use EasyLZMA to compress the data
    unsigned char *compressed_data = NULL;
    size_t compressed_size = 0;
    
    // Create compression handle
    elzma_compress_handle handle;
    handle = elzma_compress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate compression handle\n");
        return LZMA_ERROR_MEMORY;
    }

    // Configure compression parameters with the correct number of arguments
    int ret = elzma_compress_config(handle,
        ELZMA_LC_DEFAULT,      // lc (literal context bits)
        ELZMA_LP_DEFAULT,      // lp (literal position bits)
        ELZMA_PB_DEFAULT,      // pb (position bits)
        9,                     // level (highest compression level)
        ELZMA_DICT_SIZE_DEFAULT_MAX, // dictionarySize
        ELZMA_lzma,            // format
        input_size);           // uncompressedSize
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Failed to configure compression: %d\n", ret);
        elzma_compress_free(&handle);
        return LZMA_ERROR_CORRUPT;
    }

    // Set up input context
    read_buffer_context input_ctx = {
        .data = input_buffer,
        .size = input_size,
        .position = 0
    };
    
    // Set up output context for temporary buffer
    write_buffer_context output_ctx = {
        .data = &compressed_data,
        .size = &compressed_size
    };
    
    // Perform compression with the correct number of arguments
    ret = elzma_compress_run(handle, 
                           buffer_read_callback, &input_ctx,
                           buffer_write_callback, &output_ctx,
                           NULL, NULL);
    
    // Free the compression handle
    elzma_compress_free(&handle);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Compression failed with error code: %d\n", ret);
        return LZMA_ERROR_CORRUPT;
    }

    // Check if output buffer is large enough
    if (*output_size < compressed_size) {
        free(compressed_data);
        fprintf(stderr, "Output buffer too small (%zu needed, %zu available)\n", 
                compressed_size, *output_size);
        return LZMA_ERROR_OUTPUT;
    }

    // Copy compressed data to output buffer
    memcpy(output_buffer, compressed_data, compressed_size);
    *output_size = compressed_size;
    
    // Free temporary compressed data
    free(compressed_data);
    return LZMA_SUCCESS;
}
