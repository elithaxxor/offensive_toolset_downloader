
### Code Explanation

The file `downloader_01.c` is a C program that performs the following tasks:

1. **Download HTML Content**:
    - The program uses `libcurl` to fetch HTML content from a specified URL.

2. **Parse HTML Content**:
    - It uses `libxml2` to parse the downloaded HTML content and extract all anchor (`<a>`) elements with `href` attributes.

3. **Filter GitHub Links**:
    - The program identifies links that point to GitHub repositories and ensures they end with `.git`.

4. **Log GitHub Links**:
    - It saves the identified GitHub links to a file named `github_links.txt`.

5. **Clone Repositories**:
    - The program creates a directory named `repos` and clones each identified GitHub repository into this directory.

#### Detailed Code Breakdown

1. **Include Necessary Headers**:
    - The program includes standard libraries (`stdio.h`, `stdlib.h`, `string.h`) and specialized libraries (`curl/curl.h`, `libxml/HTMLparser.h`, `libxml/xpath.h`, `sys/stat.h`, `unistd.h`).

    ```c
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <curl/curl.h>
    #include <libxml/HTMLparser.h>
    #include <libxml/xpath.h>
    #include <sys/stat.h>
    #include <unistd.h>
    ```

2. **Define Constants**:
    - The program defines constants for maximum links, maximum link length, and the URL to fetch.

    ```c
    #define MAX_LINKS 1000
    #define MAX_LINK_LENGTH 256
    #define URL "https://inventory.raw.pm/tools.html"
    ```

3. **Define MemoryStruct**:
    - A structure to hold the downloaded HTML content in memory.

    ```c
    struct MemoryStruct {
        char *memory;
        size_t size;
    };
    ```

4. **WriteMemoryCallback Function**:
    - A callback function for `libcurl` that writes the downloaded data into the `MemoryStruct`.

    ```c
    static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
        size_t realsize = size * nmemb;
        struct MemoryStruct *mem = (struct MemoryStruct *)userp;

        char *ptr = realloc(mem->memory, mem->size + realsize + 1);
        if (!ptr) return 0;

        mem->memory = ptr;
        memcpy(&(mem->memory[mem->size]), contents, realsize);
        mem->size += realsize;
        mem->memory[mem->size] = 0;

        return realsize;
    }
    ```

5. **clone_repository Function**:
    - Clones a given GitHub repository link into the `repos` directory.

    ```c
    void clone_repository(const char *link) {
        char command[512];
        snprintf(command, sizeof(command), "git clone %s repos/%s", link, strrchr(link, '/') + 1);
        int result = system(command);
        if (result == 0) {
            printf("Successfully cloned %s\n", link);
        } else {
            printf("Failed to clone %s\n", link);
        }
    }
    ```

6. **main Function**:
    - Initializes `libcurl`, downloads the HTML content, parses it using `libxml2`, extracts GitHub links, logs them to a file, and attempts to clone them.

    ```c
    int main(void) {
        CURL *curl_handle;
        CURLcode res;
        struct MemoryStruct chunk;
        chunk.memory = malloc(1);
        chunk.size = 0;

        curl_global_init(CURL_GLOBAL_ALL);
        curl_handle = curl_easy_init();

        curl_easy_setopt(curl_handle, CURLOPT_URL, URL);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, (void *)&chunk);
        curl_easy_setopt(curl_handle, CURLOPT_USERAGENT, "libcurl-agent/1.0");

        res = curl_easy_perform(curl_handle);

        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            htmlDocPtr doc = htmlReadMemory(chunk.memory, chunk.size, URL, NULL, 0);
            if (doc == NULL) {
                fprintf(stderr, "Failed to parse HTML\n");
                return 1;
            }

            xmlXPathContextPtr context = xmlXPathNewContext(doc);
            xmlXPathObjectPtr result = xmlXPathEvalExpression((xmlChar*)"//a[@href]", context);

            if (result == NULL) {
                fprintf(stderr, "Failed to evaluate XPath expression\n");
                return 1;
            }

            char github_links[MAX_LINKS][MAX_LINK_LENGTH];
            int link_count = 0;

            for (int i = 0; i < result->nodesetval->nodeNr && link_count < MAX_LINKS; i++) {
                xmlNodePtr node = result->nodesetval->nodeTab[i];
                xmlChar* href = xmlGetProp(node, (xmlChar*)"href");
                if (strstr((char*)href, "github.com")) {
                    strncpy(github_links[link_count], (char*)href, MAX_LINK_LENGTH - 1);
                    github_links[link_count][MAX_LINK_LENGTH - 1] = '\0';
                    if (strstr(github_links[link_count], ".git") == NULL) {
                        strncat(github_links[link_count], ".git", MAX_LINK_LENGTH - strlen(github_links[link_count]) - 1);
                    }
                    link_count++;
                }
                xmlFree(href);
            }

            xmlXPathFreeObject(result);
            xmlXPathFreeContext(context);
            xmlFreeDoc(doc);

            if (link_count == 0) {
                printf("Warning: No GitHub links found on the page.\n");
            } else {
                FILE *file = fopen("github_links.txt", "w");
                if (file == NULL) {
                    fprintf(stderr, "Failed to open file for writing\n");
                    return 1;
                }

                mkdir("repos", 0777);

                for (int i = 0; link_count; i++) {
                    fprintf(file, "%s\n", github_links[i]);
                    clone_repository(github_links[i]);
                }

                fclose(file);
                printf("GitHub links have been saved to github_links.txt and cloning attempted.\n");
            }
        }

        curl_easy_cleanup(curl_handle);
        free(chunk.memory);
        curl_global_cleanup();

        return 0;
    }
    ```

### README.md

```markdown
# Offensive Toolset Downloader

This repository contains a C program (`downloader_01.c`) designed to download, parse, and process HTML content to extract and clone GitHub repositories. The program fetches a list of GitHub repository links from a specified URL, saves the links to a file, and attempts to clone each repository into a local directory.

## Features

- **Download HTML Content**: Fetches HTML content from a specified URL using `libcurl`.
- **Parse HTML Content**: Uses `libxml2` to parse the downloaded HTML and extract anchor (`<a>`) elements with `href` attributes.
- **Filter GitHub Links**: Identifies GitHub repository links and ensures they end with `.git`.
- **Log GitHub Links**: Saves the identified GitHub links to a file named `github_links.txt`.
- **Clone Repositories**: Creates a directory named `repos` and clones each identified GitHub repository into this directory.

## Requirements

- **libcurl**: A free and easy-to-use client-side URL transfer library.
- **libxml2**: The XML C parser and toolkit developed for the Gnome project.
- **Git**: A version control system to clone repositories.

## Installation

### Install Dependencies

On Debian-based systems, you can install the required libraries using `apt`:

```bash
sudo apt-get update
sudo apt-get install -y libcurl4-openssl-dev libxml2-dev git
```

### Compile the Program

To compile the program, use `gcc`:

```bash
gcc -o downloader_01 downloader_01.c -lcurl -lxml2
```

## Usage

Run the compiled program:

```bash
./downloader_01
```

## Code Explanation

### Include Necessary Headers

The program includes standard libraries (`stdio.h`, `stdlib.h`, `string.h`) and specialized libraries (`curl/curl.h`, `libxml/HTMLparser.h`, `libxml/xpath.h`, `sys/stat.h`, `unistd.h`).

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <libxml/HTMLparser.h>
#include <libxml/xpath.h>
#include <sys/stat.h>
#include <unistd.h>
```

### Define Constants

The program defines constants for maximum links, maximum link length, and the URL to fetch.

```c
#define MAX_LINKS 1000
#define MAX_LINK_LENGTH 256
#define URL "https://inventory.raw.pm/tools.html"
```

### Define MemoryStruct

A structure to hold the downloaded HTML content in memory.

```c
struct MemoryStruct {
    char *memory;
    size_t size;
};
```

### WriteMemoryCallback Function

A callback function for `libcurl` that writes the downloaded data into the `MemoryStruct`.

```c
static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if (!ptr) return 0;

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}
```

### clone_repository Function

Clones a given GitHub repository link into the `repos` directory.

```c
void clone_repository(const char *link) {
    char command[512];
    snprintf(command, sizeof(command), "git clone %s repos/%s", link, strrchr(link, '/') + 1);
    int result = system(command);
    if (result == 0) {
        printf("Successfully cloned %s\n", link);
    } else {
        printf("Failed to clone %s\n", link);
    }
}
```

### main Function

Initializes `libcurl`, downloads the HTML content, parses it using `libxml2`, extracts GitHub links, logs them to a file, and attempts to clone them.

```c
int main(void) {
    CURL *curl_handle;
    CURLcode res;
    struct MemoryStruct chunk;
    chunk.memory = malloc(1);
    chunk.size = 0;

    curl_global_init(CURL_GLOBAL_ALL);
    curl_handle = curl_easy_init();

    curl_easy_setopt(curl_handle, CURLOPT_URL, URL);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl_handle, CURLOPT_USERAGENT, "libcurl-agent/1.0");

    res = curl_easy_perform(curl_handle);

    if (res != CURLE_OK) {
        fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
    } else {
        htmlDocPtr doc = htmlReadMemory(chunk.memory, chunk.size, URL, NULL, 0);
        if (doc == NULL) {
            fprintf(stderr, "Failed to parse HTML\n");
            return 1;
        }

        xmlXPathContextPtr context = xmlXPathNewContext(doc);
        xmlXPathObjectPtr result = xmlXPathEvalExpression((xmlChar*)"//a[@href]", context);

        if (result == NULL) {
            fprintf(stderr, "Failed to evaluate XPath expression\n");
            return 1;
        }

        char github_links[MAX_LINKS][MAX_LINK_LENGTH];
        int link_count = 0;

        for (int i = 0; i < result->nodesetval->nodeNr && link_count < MAX_LINKS; i++) {
            xmlNodePtr node = result->nodesetval->nodeTab[i];
            xmlChar* href = xmlGetProp(node, (xmlChar*)"href");
            if (strstr((char*)href, "github.com")) {
                strncpy(github_links[link_count], (char*)href, MAX_LINK_LENGTH - 1);
                github_links[link_count][MAX_LINK_LENGTH - 1] = '\0';
                if (strstr(github_links[link_count], ".git") == NULL) {
                    strncat(github_links[link_count], ".git", MAX_LINK_LENGTH - strlen(github_links[link_count]) - 1);
                }
                link_count++;
            }
            xmlFree(href);
        }

        xmlXPathFreeObject(result);
        xmlXPathFreeContext(context);
        xmlFreeDoc(doc);

        if (link_count == 0) {
            printf("Warning: No GitHub links found on the page.\n");
        } else {
            FILE *file = fopen("github_links.txt", "w");
            if (file == NULL) {
                fprintf(stderr, "Failed to open file for writing\n");
                return 1;
            }

            mkdir("repos", 0777);

            for (int i = 0; i < link_count; i++) {
                fprintf(file, "%s\n", github_links[i]);
                clone_repository(github_links[i]);
            }

            fclose(file);
            printf("GitHub links have been saved to github_links.txt and cloning attempted.\n");
        }
    }

    curl_easy_cleanup(curl_handle);
    free(chunk.memory);
    curl_global_cleanup();

    return 0;
}
```
