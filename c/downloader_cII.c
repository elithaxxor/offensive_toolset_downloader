#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <libxml/HTMLparser.h>
#include <libxml/xpath.h>
#include <sys/stat.h>

#define TARGET_URL "https://inventory.raw.pm/tools.html"
#define OUTPUT_FILE "github_links.txt"
#define REPO_DIR "repos"

typedef struct {
    char **items;
    size_t count;
    size_t capacity;
} StringList;

typedef struct {
    char *data;
    size_t size;
} MemoryBuffer;

// Callback for libcurl to write data to memory
size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    MemoryBuffer *mem = (MemoryBuffer *)userp;
    
    char *ptr = realloc(mem->data, mem->size + realsize + 1);
    if(!ptr) return 0;
    
    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->data[mem->size] = 0;
    
    return realsize;
}

// Initialize string list
void string_list_init(StringList *list) {
    list->count = 0;
    list->capacity = 10;
    list->items = malloc(sizeof(char*) * list->capacity);
}

// Add string to list
void string_list_add(StringList *list, const char *str) {
    if(list->count >= list->capacity) {
        list->capacity *= 2;
        list->items = realloc(list->items, sizeof(char*) * list->capacity);
    }
    list->items[list->count++] = strdup(str);
}

// Free string list memory
void string_list_free(StringList *list) {
    for(size_t i = 0; i < list->count; i++) {
        free(list->items[i]);
    }
    free(list->items);
}

// Fetch HTML content using libcurl
int fetch_html(const char *url, MemoryBuffer *buf) {
    CURL *curl = curl_easy_init();
    if(!curl) return 1;

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, buf);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "libcurl-agent/1.0");
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);

    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    
    return res != CURLE_OK;
}

// Parse HTML and extract GitHub links
void parse_html(MemoryBuffer *buf, StringList *links) {
    htmlDocPtr doc = htmlReadMemory(buf->data, buf->size, NULL, NULL, HTML_PARSE_NOERROR | HTML_PARSE_NOWARNING);
    if(!doc) return;

    xmlXPathContextPtr context = xmlXPathNewContext(doc);
    xmlXPathObjectPtr result = xmlXPathEvalExpression((xmlChar*)"//a/@href", context);

    if(result && result->nodesetval) {
        for(int i = 0; i < result->nodesetval->nodeNr; i++) {
            xmlNodePtr node = result->nodesetval->nodeTab[i];
            char *href = (char*)xmlNodeGetContent(node);
            if(strstr(href, "github.com")) {
                string_list_add(links, href);
            }
            xmlFree(href);
        }
    }

    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    xmlFreeDoc(doc);
}

// Process links to ensure .git suffix
void process_links(StringList *links) {
    for(size_t i = 0; i < links->count; i++) {
        char *link = links->items[i];
        size_t len = strlen(link);
        if(len < 4 || strcmp(link + len - 4, ".git") != 0) {
            char *new_link = malloc(len + 5);
            strcpy(new_link, link);
            strcat(new_link, ".git");
            free(link);
            links->items[i] = new_link;
        }
    }
}

// Write links to file
void write_links(StringList *links) {
    FILE *fp = fopen(OUTPUT_FILE, "w");
    if(!fp) {
        perror("Failed to open output file");
        return;
    }

    for(size_t i = 0; i < links->count; i++) {
        fprintf(fp, "%s\n", links->items[i]);
    }
    fclose(fp);
}

// Create directory if not exists
void create_directory(const char *path) {
    struct stat st = {0};
    if(stat(path, &st) == -1) {
        mkdir(path, 0700);
    }
}

// Clone repositories using system git
void clone_repos(StringList *links) {
    printf("Starting to clone GitHub repositories into '%s/'...\n", REPO_DIR);
    
    for(size_t i = 0; i < links->count; i++) {
        char cmd[1024];
        snprintf(cmd, sizeof(cmd), "git -C %s clone %s", REPO_DIR, links->items[i]);
        
        int status = system(cmd);
        if(status != 0) {
            fprintf(stderr, "Failed to clone %s\n", links->items[i]);
        } else {
            printf("Successfully cloned %s\n", links->items[i]);
        }
    }
}

int main() {
    MemoryBuffer html_buf = {0};
    StringList links;
    string_list_init(&links);

    // Fetch HTML
    if(fetch_html(TARGET_URL, &html_buf)) {
        fprintf(stderr, "Failed to fetch webpage\n");
        goto cleanup;
    }

    // Parse HTML
    parse_html(&html_buf, &links);
    if(links.count == 0) {
        printf("Warning: No GitHub links found on the page.\n");
    }

    // Process links
    process_links(&links);

    // Write to file
    write_links(&links);

    // Create repo directory
    create_directory(REPO_DIR);

    // Clone repositories
    clone_repos(&links);

cleanup:
    free(html_buf.data);
    string_list_free(&links);
    return 0;
}
