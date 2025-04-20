#ifndef LZMA_COMMON_H
#define LZMA_COMMON_H

#include <stdint.h>
#include <stdlib.h>

/* Define LZMA algorithm constants */
#define LZMA_HEADER_SIZE 13  /* 5 bytes props + 8 bytes size */
#define LZMA_MAX_DICT_SIZE (1 << 24)  /* 16MB dictionary */

/* Custom memory allocation functions for LZMA */
void* lzma_alloc(void* p, size_t size);
void lzma_free(void* p, void* address);

/* Error codes */
typedef enum {
    LZMA_SUCCESS = 0,
    LZMA_ERROR_MEMORY = 1,
    LZMA_ERROR_INPUT = 2,
    LZMA_ERROR_OUTPUT = 3,
    LZMA_ERROR_CORRUPT = 4
} lzma_status;

#endif /* LZMA_COMMON_H */
