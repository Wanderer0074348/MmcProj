#include "decompression.h"
#include "lzma_common.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../easylzma/src/easylzma/decompress.h"

char* decompress_file(const char *input_path, size_t *out_size) {
    FILE *in = fopen(input_path, "rb");
    if (!in) {
        perror("Failed to open input file");
        return NULL;
    }

    // Get input file size
    fseek(in, 0, SEEK_END);
    size_t input_size = ftell(in);
    fseek(in, 0, SEEK_SET);

    if (input_size == 0) {
        fprintf(stderr, "Input file is empty\n");
        fclose(in);
        return NULL;
    }

    // Read input file into buffer
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

    // Use EasyLZMA to decompress the data
    unsigned char *output_buffer = NULL;
    size_t output_size = 0;
    
    // Create decompression handle
    elzma_decompress_handle handle;
    handle = elzma_decompress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate decompression handle\n");
        free(input_buffer);
        return NULL;
    }
    
    // Perform decompression (auto-detect format)
    int ret = elzma_decompress(handle, input_buffer, input_size, 
                              &output_buffer, &output_size);
    
    // Free the decompression handle
    elzma_decompress_free(&handle);
    
    // Free input buffer as we don't need it anymore
    free(input_buffer);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Decompression failed with error code: %d\n", ret);
        return NULL;
    }
    
    // Safety check for decompression bombs
    if (output_size > (100 * 1024 * 1024)) {  // 100MB safety limit
        fprintf(stderr, "Decompressed size is too large: %zu bytes\n", output_size);
        free(output_buffer);
        return NULL;
    }

    *out_size = output_size;
    return (char*)output_buffer;
}

int decompress_buffer(const uint8_t *input_buffer, size_t input_size,
                     uint8_t *output_buffer, size_t *output_size) {
    if (input_size == 0) {
        return LZMA_ERROR_INPUT;
    }
    
    // Use EasyLZMA to decompress the data
    unsigned char *decompressed_data = NULL;
    size_t decompressed_size = 0;
    
    // Create decompression handle
    elzma_decompress_handle handle;
    handle = elzma_decompress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate decompression handle\n");
        return LZMA_ERROR_MEMORY;
    }
    
    // Perform decompression (auto-detect format)
    int ret = elzma_decompress(handle, input_buffer, input_size, 
                              &decompressed_data, &decompressed_size);
    
    // Free the decompression handle
    elzma_decompress_free(&handle);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Decompression failed with error code: %d\n", ret);
        return LZMA_ERROR_CORRUPT;
    }
    
    // Check if output buffer is large enough
    if (*output_size < decompressed_size) {
        free(decompressed_data);
        fprintf(stderr, "Output buffer too small (%zu needed, %zu available)\n", 
                decompressed_size, *output_size);
        return LZMA_ERROR_OUTPUT;
    }
    
    // Copy decompressed data to output buffer
    memcpy(output_buffer, decompressed_data, decompressed_size);
    *output_size = decompressed_size;
    
    // Free temporary decompressed data
    free(decompressed_data);
    
    return LZMA_SUCCESS;
}
